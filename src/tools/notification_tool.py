"""Notification tools for sending proactive messages via Teams bot."""

import sys
import os
import requests
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils import Config, get_logger

logger = get_logger(__name__)


def send_teams_notification(
    conversation_reference: Dict[str, Any], message: str
) -> Dict[str, Any]:
    """
    Send a proactive notification to a Teams user or channel.

    Args:
        conversation_reference: The stored conversation reference for the recipient.
        message: The message text to send.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info("Sending Teams notification", message_preview=message[:50])

    try:
        # Call the bot's /api/notify endpoint
        bot_url = f"http://localhost:{Config.BOT_PORT}/api/notify"

        payload = {
            "conversation_reference": conversation_reference,
            "message": message,
        }

        response = requests.post(bot_url, json=payload, timeout=10)
        response.raise_for_status()

        logger.info("Notification sent successfully")

        return {
            "status": "success",
            "message": "Notification sent",
        }

    except Exception as e:
        logger.error("Failed to send notification", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to send notification: {str(e)}",
        }


def notify_approval_request(
    approver_email: str, cr_id: str, cr_title: str, requester: str
) -> Dict[str, Any]:
    """
    Send an approval request notification to a manager.

    Args:
        approver_email: Email of the approver.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        requester: Name/email of the requester.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending approval request",
        approver=approver_email,
        cr_id=cr_id,
    )

    message = (
        f"🔔 **Approval Required**\n\n"
        f"**Change Request:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Requested by:** {requester}\n\n"
        f"Please review and respond with:\n"
        f"- `approve {cr_id}` to approve\n"
        f"- `reject {cr_id}` to reject\n\n"
        f"This request will auto-escalate if not responded to within "
        f"{Config.APPROVAL_TIMEOUT_MINUTES} minutes."
    )

    # TODO: Retrieve conversation reference for approver from storage
    # For now, this is a placeholder
    conversation_reference = {}

    return send_teams_notification(conversation_reference, message)


def notify_approval_status(
    requester_email: str, cr_id: str, status: str, approver: str, comments: str = ""
) -> Dict[str, Any]:
    """
    Notify the requester about the approval status of their CR.

    Args:
        requester_email: Email of the requester.
        cr_id: Change Request ID.
        status: Approval status ("approved" or "rejected").
        approver: Name/email of the approver.
        comments: Optional comments from the approver.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending approval status notification",
        requester=requester_email,
        cr_id=cr_id,
        status=status,
    )

    emoji = "✅" if status == "approved" else "❌"
    status_text = "Approved" if status == "approved" else "Rejected"

    message = (
        f"{emoji} **Change Request {status_text}**\n\n"
        f"**CR ID:** {cr_id}\n"
        f"**Status:** {status_text}\n"
        f"**Reviewed by:** {approver}\n"
    )

    if comments:
        message += f"**Comments:** {comments}\n"

    # TODO: Retrieve conversation reference for requester from storage
    conversation_reference = {}

    return send_teams_notification(conversation_reference, message)


def notify_escalation(
    escalation_contact: str, cr_id: str, cr_title: str, reason: str
) -> Dict[str, Any]:
    """
    Send an escalation notification when approval times out.

    Args:
        escalation_contact: Email of the escalation contact.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        reason: Reason for escalation.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending escalation notification",
        escalation_contact=escalation_contact,
        cr_id=cr_id,
    )

    message = (
        f"⚠️ **Escalation Required**\n\n"
        f"**Change Request:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Reason:** {reason}\n\n"
        f"This request requires immediate attention."
    )

    # TODO: Retrieve conversation reference for escalation contact
    conversation_reference = {}

    return send_teams_notification(conversation_reference, message)


def notify_reminder(
    user_email: str, cr_id: str, cr_title: str, scheduled_time: str
) -> Dict[str, Any]:
    """
    Send a reminder about an upcoming change.

    Args:
        user_email: Email of the user to notify.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        scheduled_time: Scheduled time of the change.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending reminder notification",
        user=user_email,
        cr_id=cr_id,
    )

    message = (
        f"⏰ **Upcoming Change Reminder**\n\n"
        f"**CR ID:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Scheduled:** {scheduled_time}\n\n"
        f"Please ensure all preparations are complete."
    )

    # TODO: Retrieve conversation reference for user
    conversation_reference = {}

    return send_teams_notification(conversation_reference, message)
