"""Comprehensive CR reminder service with multi-state workflows."""

import sys
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_session, ChangeRequest, CRNotificationSent
from src.utils import get_logger, Config
import requests

logger = get_logger(__name__)


async def check_approved_state_reminders():
    """Flow 1: Approved state - 20min before start + at start if not In Progress."""
    logger.info("Checking Approved state reminders")
    session = get_session()
    
    try:
        now = datetime.utcnow()
        
        # Part 1: 20 minutes before start
        window_start = now
        window_end = now + timedelta(minutes=20)
        
        approved_crs = (
            session.query(ChangeRequest)
            .filter(
                ChangeRequest.scheduled_start_date.isnot(None),
                ChangeRequest.scheduled_start_date >= window_start,
                ChangeRequest.scheduled_start_date <= window_end,
                ChangeRequest.state == "Approved"
            )
            .all()
        )
        
        sent_count = 0
        for cr in approved_crs:
            event_type = "approved_20min_before_start"
            if not _notification_exists(session, cr.cr_id, event_type, cr.created_by_email):
                if send_power_automate_notification(
                    user_email=cr.created_by_email,
                    cr_id=cr.cr_id,
                    title=cr.title,
                    notification_type=event_type,
                    scheduled_time=cr.scheduled_start_date,
                    current_state=cr.state,
                    message="Your CR is starting in 20 minutes. Please transition to 'In Progress' when you begin."
                ):
                    _log_notification(session, cr.cr_id, event_type, cr.created_by_email)
                    sent_count += 1
        
        # Part 2: At start time if still Approved
        overdue_crs = (
            session.query(ChangeRequest)
            .filter(
                ChangeRequest.scheduled_start_date.isnot(None),
                ChangeRequest.scheduled_start_date <= now,
                ChangeRequest.scheduled_start_date >= now - timedelta(minutes=5),
                ChangeRequest.state == "Approved"
            )
            .all()
        )
        
        for cr in overdue_crs:
            event_type = "approved_at_start_not_in_progress"
            if not _notification_exists(session, cr.cr_id, event_type, cr.created_by_email):
                if send_power_automate_notification(
                    user_email=cr.created_by_email,
                    cr_id=cr.cr_id,
                    title=cr.title,
                    notification_type=event_type,
                    scheduled_time=cr.scheduled_start_date,
                    current_state=cr.state,
                    message="Your CR scheduled start time has arrived. Please update status to 'In Progress' immediately."
                ):
                    _log_notification(session, cr.cr_id, event_type, cr.created_by_email)
                    sent_count += 1
        
        logger.info(f"Approved state reminders: {sent_count} sent")
        
    except Exception as e:
        logger.error("Approved state reminder check failed", error=str(e))
    finally:
        session.close()


async def check_in_progress_reminders():
    """Flow 2: In Progress state - 20min before end + follow-up at end."""
    logger.info("Checking In Progress state reminders")
    session = get_session()
    
    try:
        now = datetime.utcnow()
        
        # Part 1: 20 minutes before end
        window_start = now
        window_end = now + timedelta(minutes=20)
        
        in_progress_crs = (
            session.query(ChangeRequest)
            .filter(
                ChangeRequest.scheduled_end_date.isnot(None),
                ChangeRequest.scheduled_end_date >= window_start,
                ChangeRequest.scheduled_end_date <= window_end,
                ChangeRequest.state == "In Progress"
            )
            .all()
        )
        
        sent_count = 0
        for cr in in_progress_crs:
            event_type = "in_progress_20min_before_end"
            if not _notification_exists(session, cr.cr_id, event_type, cr.created_by_email):
                if send_power_automate_notification(
                    user_email=cr.created_by_email,
                    cr_id=cr.cr_id,
                    title=cr.title,
                    notification_type=event_type,
                    scheduled_time=cr.scheduled_end_date,
                    current_state=cr.state,
                    message="Your CR is ending in 20 minutes. Please fill in results and update status."
                ):
                    _log_notification(session, cr.cr_id, event_type, cr.created_by_email)
                    sent_count += 1
        
        # Part 2: At end time if results not filled
        overdue_crs = (
            session.query(ChangeRequest)
            .filter(
                ChangeRequest.scheduled_end_date.isnot(None),
                ChangeRequest.scheduled_end_date <= now,
                ChangeRequest.scheduled_end_date >= now - timedelta(minutes=5),
                ChangeRequest.state == "In Progress"
            )
            .all()
        )
        
        for cr in overdue_crs:
            event_type = "in_progress_at_end_no_results"
            if not _notification_exists(session, cr.cr_id, event_type, cr.created_by_email):
                if send_power_automate_notification(
                    user_email=cr.created_by_email,
                    cr_id=cr.cr_id,
                    title=cr.title,
                    notification_type=event_type,
                    scheduled_time=cr.scheduled_end_date,
                    current_state=cr.state,
                    message="Your CR scheduled end time has passed. Please provide completion status and results. Do you need an extension?",
                    requires_response=True
                ):
                    _log_notification(session, cr.cr_id, event_type, cr.created_by_email)
                    sent_count += 1
        
        logger.info(f"In Progress state reminders: {sent_count} sent")
        
    except Exception as e:
        logger.error("In Progress reminder check failed", error=str(e))
    finally:
        session.close()


async def check_awaiting_pir_reminders():
    """Flow 3: Awaiting PIR state - periodic reminders to complete PIR."""
    logger.info("Checking Awaiting PIR reminders")
    session = get_session()
    
    try:
        # Find all CRs in Awaiting PIR state
        awaiting_pir_crs = (
            session.query(ChangeRequest)
            .filter(ChangeRequest.state == "Awaiting PIR")
            .all()
        )
        
        sent_count = 0
        for cr in awaiting_pir_crs:
            # Send daily reminder if not already sent today
            event_type = f"awaiting_pir_reminder_{datetime.utcnow().strftime('%Y%m%d')}"
            
            if not _notification_exists(session, cr.cr_id, event_type, cr.assigned_to or cr.created_by_email):
                recipient = cr.assigned_to or cr.created_by_email
                if send_power_automate_notification(
                    user_email=recipient,
                    cr_id=cr.cr_id,
                    title=cr.title,
                    notification_type="awaiting_pir_reminder",
                    current_state=cr.state,
                    message="Formal reminder: Please complete and submit the Post-Implementation Review (PIR) for this CR."
                ):
                    _log_notification(session, cr.cr_id, event_type, recipient)
                    sent_count += 1
        
        logger.info(f"Awaiting PIR reminders: {sent_count} sent")
        
    except Exception as e:
        logger.error("Awaiting PIR reminder check failed", error=str(e))
    finally:
        session.close()


def _notification_exists(session, cr_id, event_type, recipient_email):
    """Check if notification already sent."""
    return session.query(CRNotificationSent).filter_by(
        cr_id=cr_id,
        event_type=event_type,
        recipient_email=recipient_email
    ).first() is not None


def _log_notification(session, cr_id, event_type, recipient_email):
    """Log sent notification to database."""
    notification = CRNotificationSent(
        cr_id=cr_id,
        event_type=event_type,
        recipient_email=recipient_email,
    )
    session.add(notification)
    session.commit()


def send_power_automate_notification(
    user_email,
    cr_id,
    title,
    notification_type,
    current_state,
    message=None,
    scheduled_time=None,
    requires_response=False
):
    """
    Send notification via Power Automate flow.
    
    Args:
        user_email: Recipient email
        cr_id: Change Request ID
        title: CR title
        notification_type: Type of notification (for flow routing)
        current_state: Current CR state
        message: Custom message text
        scheduled_time: Scheduled datetime (optional)
        requires_response: Whether user response is needed
    
    Returns:
        bool: True if notification sent successfully
    """
    flow_url = Config.POWER_AUTOMATE_URL
    
    if not flow_url:
        logger.warning("POWER_AUTOMATE_URL not configured, skipping notification")
        return False
    
    if not user_email:
        logger.warning(f"No email for CR {cr_id}, cannot send notification")
        return False
    
    # Generate CR link
    cr_link = Config.get_work_item_url(cr_id.replace("CR", ""))
    
    # Format scheduled time if provided
    scheduled_time_str = None
    if scheduled_time and isinstance(scheduled_time, datetime):
        scheduled_time_str = scheduled_time.strftime("%Y-%m-%d %H:%M UTC")
    elif scheduled_time:
        scheduled_time_str = str(scheduled_time)
    
    payload = {
        "user_email": user_email,
        "cr_id": cr_id,
        "title": title,
        "current_state": current_state,
        "cr_link": cr_link,
        "notification_type": notification_type,
        "message": message,
        "scheduled_time": scheduled_time_str,
        "requires_response": requires_response
    }
    
    try:
        response = requests.post(flow_url, json=payload, timeout=10)
        
        if response.status_code == 202:  # Power Automate returns 202 Accepted
            logger.info("Notification sent via Power Automate", 
                       cr_id=cr_id, 
                       user=user_email, 
                       type=notification_type)
            return True
        else:
            logger.error(
                "Failed to send notification",
                cr_id=cr_id,
                type=notification_type,
                status=response.status_code,
                response=response.text
            )
            return False
            
    except Exception as e:
        logger.error("Error sending notification", 
                    cr_id=cr_id, 
                    type=notification_type, 
                    error=str(e))
        return False


def start_reminder_service(check_interval_minutes=5):
    """
    Start comprehensive reminder service with all three flows.
    
    Args:
        check_interval_minutes: How often to check for reminders (default: 5)
    """
    logger.info(f"Starting comprehensive reminder service (check interval: {check_interval_minutes} minutes)")
    
    scheduler = AsyncIOScheduler()
    
    # Flow 1: Approved state reminders
    scheduler.add_job(
        check_approved_state_reminders,
        trigger=IntervalTrigger(minutes=check_interval_minutes),
        id="check_approved_reminders",
        name="Check Approved state reminders (20min before + at start)",
        replace_existing=True,
    )
    
    # Flow 2: In Progress state reminders
    scheduler.add_job(
        check_in_progress_reminders,
        trigger=IntervalTrigger(minutes=check_interval_minutes),
        id="check_in_progress_reminders",
        name="Check In Progress state reminders (20min before end + follow-up)",
        replace_existing=True,
    )
    
    # Flow 3: Awaiting PIR reminders (check every hour)
    scheduler.add_job(
        check_awaiting_pir_reminders,
        trigger=IntervalTrigger(hours=1),
        id="check_awaiting_pir_reminders",
        name="Check Awaiting PIR reminders (daily)",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Comprehensive reminder service started with 3 flows")
    
    return scheduler
