"""Google Cloud Function for scheduled change request reminders."""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
import requests

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.utils import get_logger, azure_devops_auth, Config
from src.tools import notify_reminder

logger = get_logger(__name__)


def send_reminder_notification(user_id: str, cr_id: str, cr_title: str, scheduled_time: str) -> None:
    """
    Send a reminder notification via the bot's notify endpoint.

    Args:
        user_id: User ID to notify.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        scheduled_time: Scheduled time of the change.
    """
    bot_url = os.getenv("BOT_NOTIFY_URL", "http://localhost:3978/api/notify")

    message = (
        f"⏰ **Upcoming Change Reminder**\n\n"
        f"**CR ID:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Scheduled:** {scheduled_time}\n\n"
        f"Please ensure all preparations are complete."
    )

    payload = {
        "user_id": user_id,
        "message": message,
    }

    try:
        response = requests.post(bot_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Reminder sent", user_id=user_id, cr_id=cr_id)
    except Exception as e:
        logger.error("Failed to send reminder", error=str(e), user_id=user_id)


def get_upcoming_changes(hours_ahead: int = 24) -> list:
    """
    Query Azure DevOps for upcoming change requests.

    Args:
        hours_ahead: Number of hours ahead to look for changes.

    Returns:
        List of upcoming change requests.
    """
    logger.info("Querying upcoming changes", hours_ahead=hours_ahead)

    # Calculate time window
    now = datetime.utcnow()
    future_time = now + timedelta(hours=hours_ahead)

    # Build WIQL query
    query = f"""
    SELECT [System.Id], [System.Title], [Custom.ScheduledTime], [System.CreatedBy]
    FROM WorkItems
    WHERE [System.WorkItemType] = 'Change Request'
    AND [System.State] = 'Approved'
    AND [Custom.ScheduledTime] >= '{now.isoformat()}'
    AND [Custom.ScheduledTime] <= '{future_time.isoformat()}'
    """

    try:
        result = azure_devops_auth.call_api(
            endpoint="wit/wiql",
            method="POST",
            data={"query": query},
        )

        work_items = result.get("workItems", [])
        logger.info("Found upcoming changes", count=len(work_items))

        # Fetch details for each work item
        upcoming_changes = []
        for item in work_items:
            work_item_id = item["id"]

            # Get work item details
            details = azure_devops_auth.call_api(
                endpoint=f"wit/workitems/{work_item_id}",
                method="GET",
            )

            fields = details.get("fields", {})
            upcoming_changes.append({
                "cr_id": f"CR{work_item_id}",
                "title": fields.get("System.Title"),
                "scheduled_time": fields.get("Custom.ScheduledTime"),
                "created_by": fields.get("System.CreatedBy"),
            })

        return upcoming_changes

    except Exception as e:
        logger.error("Failed to query upcoming changes", error=str(e))
        return []


def scheduled_reminders(request=None) -> Dict[str, Any]:
    """
    Cloud Function entry point for scheduled reminders.

    This function is triggered by Cloud Scheduler on a cron schedule.

    Args:
        request: HTTP request object (for HTTP-triggered functions).

    Returns:
        Dictionary with execution status.
    """
    logger.info("Scheduled reminders function triggered")

    try:
        # Get upcoming changes
        upcoming_changes = get_upcoming_changes(hours_ahead=24)

        if not upcoming_changes:
            logger.info("No upcoming changes found")
            return {
                "status": "success",
                "message": "No upcoming changes to remind about",
                "count": 0,
            }

        # Send reminders for each change
        reminders_sent = 0
        for change in upcoming_changes:
            # Extract user ID from created_by field
            # Format is typically "Display Name <email@example.com>"
            created_by = change["created_by"]
            user_id = created_by  # In production, extract actual user ID

            send_reminder_notification(
                user_id=user_id,
                cr_id=change["cr_id"],
                cr_title=change["title"],
                scheduled_time=change["scheduled_time"],
            )

            reminders_sent += 1

        logger.info("Reminders sent successfully", count=reminders_sent)

        return {
            "status": "success",
            "message": f"Sent {reminders_sent} reminders",
            "count": reminders_sent,
        }

    except Exception as e:
        logger.error("Error in scheduled reminders function", error=str(e))
        return {
            "status": "error",
            "message": str(e),
        }


# For local testing
if __name__ == "__main__":
    print("\n⏰ Scheduled Reminders Function")
    print("=" * 50)
    result = scheduled_reminders()
    print(f"\nResult: {result}")
