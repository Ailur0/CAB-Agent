"""Scheduled reminder service to notify CR creators 15 minutes before start time."""

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


async def check_upcoming_crs():
    """Check for CRs starting in the next 15 minutes and send reminders."""
    logger.info("Checking for upcoming CRs requiring reminders")
    
    session = get_session()
    
    try:
        # Calculate time window: now to 15 minutes from now
        now = datetime.utcnow()
        reminder_window_start = now
        reminder_window_end = now + timedelta(minutes=15)
        
        # Query CRs with scheduled_start_date in the next 15 minutes
        # Only notify for approved CRs that haven't started yet
        upcoming_crs = (
            session.query(ChangeRequest)
            .filter(
                ChangeRequest.scheduled_start_date.isnot(None),
                ChangeRequest.scheduled_start_date >= reminder_window_start,
                ChangeRequest.scheduled_start_date <= reminder_window_end,
                ChangeRequest.state.in_(["Approved", "Scheduled"])
            )
            .all()
        )
        
        if not upcoming_crs:
            logger.debug("No upcoming CRs found in the next 15 minutes")
            return
        
        logger.info(f"Found {len(upcoming_crs)} CRs starting soon")
        
        sent_count = 0
        skipped_count = 0
        
        for cr in upcoming_crs:
            try:
                # Check if reminder already sent
                event_type = "reminder_15min_before_start"
                existing_notification = (
                    session.query(CRNotificationSent)
                    .filter_by(
                        cr_id=cr.cr_id,
                        event_type=event_type,
                        recipient_email=cr.created_by_email
                    )
                    .first()
                )
                
                if existing_notification:
                    logger.debug(f"Reminder already sent for {cr.cr_id}")
                    skipped_count += 1
                    continue
                
                # Send reminder via Power Automate
                success = send_reminder_notification(
                    user_email=cr.created_by_email,
                    cr_id=cr.cr_id,
                    title=cr.title,
                    scheduled_start=cr.scheduled_start_date,
                    current_state=cr.state
                )
                
                if success:
                    # Log notification
                    notification = CRNotificationSent(
                        cr_id=cr.cr_id,
                        event_type=event_type,
                        recipient_email=cr.created_by_email,
                    )
                    session.add(notification)
                    session.commit()
                    
                    sent_count += 1
                    logger.info(f"Reminder sent for {cr.cr_id}", user=cr.created_by_email)
                
            except Exception as e:
                logger.error(f"Failed to send reminder for {cr.cr_id}", error=str(e))
                session.rollback()
        
        logger.info(
            "Reminder check complete",
            sent=sent_count,
            skipped=skipped_count,
            total=len(upcoming_crs)
        )
        
    except Exception as e:
        logger.error("Reminder check failed", error=str(e))
    finally:
        session.close()


def send_reminder_notification(user_email, cr_id, title, scheduled_start, current_state):
    """
    Send 15-minute reminder via Power Automate flow.
    
    Args:
        user_email: Email of CR creator
        cr_id: Change Request ID
        title: CR title
        scheduled_start: Scheduled start datetime
        current_state: Current CR state
    
    Returns:
        bool: True if notification sent successfully
    """
    flow_url = Config.POWER_AUTOMATE_URL
    
    if not flow_url:
        logger.warning("POWER_AUTOMATE_URL not configured, skipping reminder")
        return False
    
    if not user_email:
        logger.warning(f"No email for CR {cr_id}, cannot send reminder")
        return False
    
    # Generate CR link
    cr_link = Config.get_work_item_url(cr_id.replace("CR", ""))
    
    # Format scheduled time
    if isinstance(scheduled_start, datetime):
        scheduled_time_str = scheduled_start.strftime("%Y-%m-%d %H:%M UTC")
    else:
        scheduled_time_str = str(scheduled_start)
    
    payload = {
        "user_email": user_email,
        "cr_id": cr_id,
        "title": title,
        "scheduled_start": scheduled_time_str,
        "current_state": current_state,
        "cr_link": cr_link,
        "notification_type": "reminder_15min"
    }
    
    try:
        response = requests.post(flow_url, json=payload, timeout=10)
        
        if response.status_code == 202:  # Power Automate returns 202 Accepted
            logger.info("Reminder sent via Power Automate", cr_id=cr_id, user=user_email)
            return True
        else:
            logger.error(
                "Failed to send reminder",
                cr_id=cr_id,
                status=response.status_code,
                response=response.text
            )
            return False
            
    except Exception as e:
        logger.error("Error sending reminder", cr_id=cr_id, error=str(e))
        return False


def start_reminder_service(check_interval_minutes=5):
    """
    Start background reminder service.
    
    Args:
        check_interval_minutes: How often to check for upcoming CRs (default: 5)
    """
    logger.info(f"Starting reminder service (check interval: {check_interval_minutes} minutes)")
    
    scheduler = AsyncIOScheduler()
    
    # Add reminder check job
    scheduler.add_job(
        check_upcoming_crs,
        trigger=IntervalTrigger(minutes=check_interval_minutes),
        id="check_cr_reminders",
        name="Check CR 15-minute reminders",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Reminder service started")
    
    return scheduler
