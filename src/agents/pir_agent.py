"""PIR (Post Implementation Review) agent for automated follow-ups and tracking."""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.adk.agents import LlmAgent
from src.utils import Config, get_logger
from src.database import get_session, PIRTracking, CRNotificationSent
from src.tools import (
    get_change_request,
    update_change_request,
    notify_pir_request,
    notify_pir_reminder,
    notify_pir_escalation,
    notify_pir_completion,
)

logger = get_logger(__name__)


def identify_pir_reviewers(cr_id: str) -> Dict[str, Any]:
    """
    Identify PIR reviewers for a change request.
    
    Args:
        cr_id: Change Request ID
        
    Returns:
        Dictionary with reviewer information
    """
    logger.info("Identifying PIR reviewers", cr_id=cr_id)
    
    try:
        # Get CR details
        cr_details = get_change_request(cr_id)
        
        if cr_details.get("status") != "success":
            return {
                "status": "error",
                "message": "Failed to retrieve CR details",
            }
        
        reviewers = []
        
        # Get assigned to (primary reviewer)
        assigned_to = cr_details.get("assigned_to")
        if assigned_to:
            reviewers.append({
                "name": assigned_to,
                "role": "primary",
                "email": cr_details.get("assigned_to_email"),
            })
        
        # Get created by (requester - should also review)
        created_by = cr_details.get("created_by")
        created_by_email = cr_details.get("created_by_unique_name")
        if created_by:
            reviewers.append({
                "name": created_by if isinstance(created_by, str) else created_by.get("displayName"),
                "role": "requester",
                "email": created_by_email if isinstance(created_by_email, str) else created_by.get("uniqueName") if isinstance(created_by, dict) else None,
            })
        
        # TODO: Add CAB members or designated PIR reviewers from Azure DevOps custom fields
        # This would require custom fields like "Custom.PIRReviewers"
        
        logger.info("Identified PIR reviewers", cr_id=cr_id, count=len(reviewers))
        
        return {
            "status": "success",
            "cr_id": cr_id,
            "reviewers": reviewers,
            "count": len(reviewers),
        }
        
    except Exception as e:
        logger.error("Failed to identify PIR reviewers", cr_id=cr_id, error=str(e))
        return {
            "status": "error",
            "message": str(e),
        }


def initiate_pir_tracking(cr_id: str, cr_title: str, requester_email: str) -> Dict[str, Any]:
    """
    Initiate PIR tracking for a change request that moved to "Awaiting PIR" state.
    
    Args:
        cr_id: Change Request ID
        cr_title: CR title
        requester_email: Email of the requester
        
    Returns:
        Dictionary with tracking status
    """
    logger.info("Initiating PIR tracking", cr_id=cr_id)
    
    session = get_session()
    
    try:
        # Check if PIR tracking already exists
        existing = session.query(PIRTracking).filter_by(cr_id=cr_id).first()
        
        if existing:
            logger.info("PIR tracking already exists", cr_id=cr_id)
            return {
                "status": "success",
                "message": "PIR tracking already active",
                "pir_id": existing.id,
            }
        
        # Identify reviewers
        reviewer_info = identify_pir_reviewers(cr_id)
        
        if reviewer_info.get("status") != "success":
            return reviewer_info
        
        reviewers = reviewer_info.get("reviewers", [])
        
        # Create PIR tracking record
        now = datetime.utcnow()
        pir_tracking = PIRTracking(
            cr_id=cr_id,
            cr_title=cr_title,
            requester_email=requester_email,
            status="pending",
            initiated_at=now,
            reminder_due_at=now + timedelta(hours=Config.PIR_REMINDER_HOURS),
            escalation_due_at=now + timedelta(hours=Config.PIR_ESCALATION_HOURS),
            reviewer_count=len(reviewers),
        )
        
        session.add(pir_tracking)
        session.commit()
        
        # Send initial notifications to all reviewers
        for reviewer in reviewers:
            if reviewer.get("email"):
                notify_pir_request(
                    reviewer_email=reviewer["email"],
                    cr_id=cr_id,
                    cr_title=cr_title,
                    requester=requester_email,
                )
        
        logger.info("PIR tracking initiated", cr_id=cr_id, pir_id=pir_tracking.id)
        
        return {
            "status": "success",
            "cr_id": cr_id,
            "pir_id": pir_tracking.id,
            "reviewers_notified": len(reviewers),
            "reminder_due_at": pir_tracking.reminder_due_at.isoformat(),
            "escalation_due_at": pir_tracking.escalation_due_at.isoformat(),
        }
        
    except Exception as e:
        logger.error("Failed to initiate PIR tracking", cr_id=cr_id, error=str(e))
        session.rollback()
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        session.close()


def check_pir_reminders() -> Dict[str, Any]:
    """
    Check for PIRs that need reminders and send them.
    
    Returns:
        Dictionary with reminder status
    """
    logger.info("Checking for PIR reminders")
    
    session = get_session()
    
    try:
        now = datetime.utcnow()
        
        # Find PIRs that need reminders
        pirs_needing_reminders = (
            session.query(PIRTracking)
            .filter(
                PIRTracking.status == "pending",
                PIRTracking.reminder_due_at <= now,
                PIRTracking.reminder_sent == False,
            )
            .all()
        )
        
        reminders_sent = 0
        
        for pir in pirs_needing_reminders:
            # Get reviewers
            reviewer_info = identify_pir_reviewers(pir.cr_id)
            
            if reviewer_info.get("status") == "success":
                reviewers = reviewer_info.get("reviewers", [])
                
                # Send reminders
                for reviewer in reviewers:
                    if reviewer.get("email"):
                        notify_pir_reminder(
                            reviewer_email=reviewer["email"],
                            cr_id=pir.cr_id,
                            cr_title=pir.cr_title,
                            hours_pending=Config.PIR_REMINDER_HOURS,
                        )
                
                # Mark reminder as sent
                pir.reminder_sent = True
                pir.reminder_sent_at = now
                reminders_sent += 1
        
        session.commit()
        
        logger.info("PIR reminders processed", count=reminders_sent)
        
        return {
            "status": "success",
            "reminders_sent": reminders_sent,
        }
        
    except Exception as e:
        logger.error("Failed to check PIR reminders", error=str(e))
        session.rollback()
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        session.close()


def check_pir_escalations() -> Dict[str, Any]:
    """
    Check for PIRs that need escalation and escalate them.
    
    Returns:
        Dictionary with escalation status
    """
    logger.info("Checking for PIR escalations")
    
    session = get_session()
    
    try:
        now = datetime.utcnow()
        
        # Find PIRs that need escalation
        pirs_needing_escalation = (
            session.query(PIRTracking)
            .filter(
                PIRTracking.status == "pending",
                PIRTracking.escalation_due_at <= now,
                PIRTracking.escalation_sent == False,
            )
            .all()
        )
        
        escalations_sent = 0
        
        for pir in pirs_needing_escalation:
            # Send escalation to Change Manager
            notify_pir_escalation(
                manager_email=Config.CHANGE_MANAGER_EMAIL,
                cr_id=pir.cr_id,
                cr_title=pir.cr_title,
                requester=pir.requester_email,
                hours_overdue=Config.PIR_ESCALATION_HOURS,
            )
            
            # Mark escalation as sent
            pir.escalation_sent = True
            pir.escalation_sent_at = now
            pir.status = "escalated"
            escalations_sent += 1
        
        session.commit()
        
        logger.info("PIR escalations processed", count=escalations_sent)
        
        return {
            "status": "success",
            "escalations_sent": escalations_sent,
        }
        
    except Exception as e:
        logger.error("Failed to check PIR escalations", error=str(e))
        session.rollback()
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        session.close()


def complete_pir(cr_id: str, reviewer_email: str, comments: str = "") -> Dict[str, Any]:
    """
    Mark a PIR as completed.
    
    Args:
        cr_id: Change Request ID
        reviewer_email: Email of the reviewer completing the PIR
        comments: Optional PIR comments
        
    Returns:
        Dictionary with completion status
    """
    logger.info("Completing PIR", cr_id=cr_id, reviewer=reviewer_email)
    
    session = get_session()
    
    try:
        # Get PIR tracking record
        pir = session.query(PIRTracking).filter_by(cr_id=cr_id).first()
        
        if not pir:
            return {
                "status": "error",
                "message": "PIR tracking not found",
            }
        
        if pir.status == "completed":
            return {
                "status": "success",
                "message": "PIR already completed",
            }
        
        # Update PIR status
        now = datetime.utcnow()
        pir.status = "completed"
        pir.completed_at = now
        pir.completed_by = reviewer_email
        pir.pir_comments = comments
        
        # Calculate completion time
        time_to_complete = (now - pir.initiated_at).total_seconds() / 3600  # hours
        pir.completion_time_hours = time_to_complete
        
        session.commit()
        
        # Update CR state in Azure DevOps
        update_change_request(
            cr_id=cr_id,
            field_updates={
                "state": "Closed",
                "comments": f"PIR completed by {reviewer_email}. {comments}",
            }
        )
        
        # Notify requester
        notify_pir_completion(
            requester_email=pir.requester_email,
            cr_id=cr_id,
            cr_title=pir.cr_title,
            reviewer=reviewer_email,
            comments=comments,
        )
        
        logger.info(
            "PIR completed",
            cr_id=cr_id,
            completion_time_hours=time_to_complete,
        )
        
        return {
            "status": "success",
            "cr_id": cr_id,
            "completed_by": reviewer_email,
            "completion_time_hours": round(time_to_complete, 2),
        }
        
    except Exception as e:
        logger.error("Failed to complete PIR", cr_id=cr_id, error=str(e))
        session.rollback()
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        session.close()


def get_pir_analytics(days: int = 30) -> Dict[str, Any]:
    """
    Get PIR analytics for the specified time period.
    
    Args:
        days: Number of days to analyze (default: 30)
        
    Returns:
        Dictionary with PIR analytics
    """
    logger.info("Getting PIR analytics", days=days)
    
    session = get_session()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all PIRs in the time period
        pirs = (
            session.query(PIRTracking)
            .filter(PIRTracking.initiated_at >= cutoff_date)
            .all()
        )
        
        total_pirs = len(pirs)
        completed_pirs = [p for p in pirs if p.status == "completed"]
        pending_pirs = [p for p in pirs if p.status == "pending"]
        escalated_pirs = [p for p in pirs if p.status == "escalated"]
        
        # Calculate metrics
        completion_rate = (len(completed_pirs) / total_pirs * 100) if total_pirs > 0 else 0
        
        avg_completion_time = 0
        if completed_pirs:
            completion_times = [p.completion_time_hours for p in completed_pirs if p.completion_time_hours]
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # PIRs completed within SLA (24 hours)
        within_sla = [p for p in completed_pirs if p.completion_time_hours and p.completion_time_hours <= 24]
        sla_compliance_rate = (len(within_sla) / len(completed_pirs) * 100) if completed_pirs else 0
        
        analytics = {
            "status": "success",
            "period_days": days,
            "total_pirs": total_pirs,
            "completed": len(completed_pirs),
            "pending": len(pending_pirs),
            "escalated": len(escalated_pirs),
            "completion_rate": round(completion_rate, 2),
            "avg_completion_time_hours": round(avg_completion_time, 2),
            "sla_compliance_rate": round(sla_compliance_rate, 2),
            "within_sla_count": len(within_sla),
        }
        
        logger.info("PIR analytics generated", **analytics)
        
        return analytics
        
    except Exception as e:
        logger.error("Failed to get PIR analytics", error=str(e))
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        session.close()


def get_pending_pirs() -> Dict[str, Any]:
    """
    Get all pending PIRs with their status.
    
    Returns:
        Dictionary with pending PIR list
    """
    logger.info("Getting pending PIRs")
    
    session = get_session()
    
    try:
        now = datetime.utcnow()
        
        pending_pirs = (
            session.query(PIRTracking)
            .filter(PIRTracking.status.in_(["pending", "escalated"]))
            .order_by(PIRTracking.initiated_at)
            .all()
        )
        
        pir_list = []
        for pir in pending_pirs:
            hours_pending = (now - pir.initiated_at).total_seconds() / 3600
            
            pir_list.append({
                "cr_id": pir.cr_id,
                "cr_title": pir.cr_title,
                "requester": pir.requester_email,
                "status": pir.status,
                "initiated_at": pir.initiated_at.isoformat(),
                "hours_pending": round(hours_pending, 2),
                "reminder_sent": pir.reminder_sent,
                "escalation_sent": pir.escalation_sent,
            })
        
        logger.info("Retrieved pending PIRs", count=len(pir_list))
        
        return {
            "status": "success",
            "count": len(pir_list),
            "pending_pirs": pir_list,
        }
        
    except Exception as e:
        logger.error("Failed to get pending PIRs", error=str(e))
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        session.close()


# Define PIR agent instruction
PIR_AGENT_INSTRUCTION = """
# PIR (Post Implementation Review) Agent

You manage the automated PIR follow-up process for change requests.

## Your Responsibilities

1. **Initiate PIR Tracking**: When a CR moves to "Awaiting PIR", start tracking
2. **Identify Reviewers**: Determine who should complete the PIR
3. **Send Notifications**: Notify reviewers immediately when PIR is needed
4. **Monitor Progress**: Track PIR completion status
5. **Send Reminders**: After {reminder_hours} hours, send reminder notifications
6. **Escalate**: After {escalation_hours} hours, escalate to Change Manager
7. **Track Completion**: Record when PIR is completed and notify requester
8. **Provide Analytics**: Generate PIR completion metrics and insights

## Workflow

1. CR status changes to "Awaiting PIR" → `initiate_pir_tracking()`
2. Identify reviewers → `identify_pir_reviewers()`
3. Send initial notifications to all reviewers
4. Monitor for completion
5. After {reminder_hours}h → `check_pir_reminders()` sends reminders
6. After {escalation_hours}h → `check_pir_escalations()` escalates
7. When completed → `complete_pir()` updates status and notifies requester

## Tools Available

- `initiate_pir_tracking`: Start PIR tracking for a CR
- `identify_pir_reviewers`: Find who should review the PIR
- `check_pir_reminders`: Check and send reminder notifications
- `check_pir_escalations`: Check and send escalation notifications
- `complete_pir`: Mark PIR as completed
- `get_pir_analytics`: Get PIR completion metrics
- `get_pending_pirs`: List all pending PIRs

## Success Metrics

- 100% of PIR reviewers receive automated notifications
- PIR completion time reduced by 60%
- Zero manual follow-ups required
- Complete visibility into PIR status
"""


def create_pir_agent() -> LlmAgent:
    """
    Create and configure the PIR agent.
    
    Returns:
        Configured LlmAgent instance
    """
    logger.info("Creating PIR agent")
    
    agent = LlmAgent(
        model=Config.ADK_MODEL,
        instruction=PIR_AGENT_INSTRUCTION.format(
            reminder_hours=Config.PIR_REMINDER_HOURS,
            escalation_hours=Config.PIR_ESCALATION_HOURS,
        ),
        tools=[
            initiate_pir_tracking,
            identify_pir_reviewers,
            check_pir_reminders,
            check_pir_escalations,
            complete_pir,
            get_pir_analytics,
            get_pending_pirs,
        ],
        temperature=0.3,
    )
    
    logger.info("PIR agent created successfully")
    return agent


# Create agent instance
pir_agent = create_pir_agent()


if __name__ == "__main__":
    print("\n📋 PIR (Post Implementation Review) Agent")
    print("=" * 50)
    print("\nAgent is ready for testing!")
    print(f"\nConfiguration:")
    print(f"  Reminder after: {Config.PIR_REMINDER_HOURS} hours")
    print(f"  Escalation after: {Config.PIR_ESCALATION_HOURS} hours")
    print(f"  Change Manager: {Config.CHANGE_MANAGER_EMAIL}")
    print("\nExample commands:")
    print('  - initiate_pir_tracking("CR12345", "DB Migration", "user@example.com")')
    print('  - check_pir_reminders()')
    print('  - check_pir_escalations()')
    print('  - complete_pir("CR12345", "reviewer@example.com", "All tests passed")')
    print('  - get_pir_analytics(30)')
    print()
