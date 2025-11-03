"""Notification tools for sending proactive messages via Teams bot and Email."""

import sys
import os
import requests
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils import Config, get_logger

logger = get_logger(__name__)

# Import email service (lazy import to avoid circular dependency)
_email_service = None

def get_email_service():
    """Get email service instance (lazy loading)."""
    global _email_service
    if _email_service is None:
        from src.utils.email_service import email_service
        _email_service = email_service
    return _email_service


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


def notify_pir_request(
    reviewer_email: str, cr_id: str, cr_title: str, requester: str
) -> Dict[str, Any]:
    """
    Send a PIR request notification to a reviewer via Email and Teams.

    Args:
        reviewer_email: Email of the PIR reviewer.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        requester: Name/email of the requester.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending PIR request notification",
        reviewer=reviewer_email,
        cr_id=cr_id,
    )

    # Send via Email
    email_service = get_email_service()
    email_result = email_service.send_pir_request_email(
        reviewer_email=reviewer_email,
        cr_id=cr_id,
        cr_title=cr_title,
        requester=requester,
    )
    
    # Also send via Teams if available
    message = (
        f"📋 **PIR Required**\n\n"
        f"**Change Request:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Requested by:** {requester}\n\n"
        f"Please complete the Post Implementation Review for this change.\n\n"
        f"To complete, respond with:\n"
        f"- `complete pir {cr_id}` with your review comments\n\n"
        f"⏰ This PIR will be escalated if not completed within 48 hours."
    )

    # TODO: Retrieve conversation reference for reviewer
    conversation_reference = {}
    teams_result = send_teams_notification(conversation_reference, message)
    
    # Return email result as primary
    return email_result


def notify_pir_reminder(
    reviewer_email: str, cr_id: str, cr_title: str, hours_pending: int
) -> Dict[str, Any]:
    """
    Send a PIR reminder notification to a reviewer via Email and Teams.

    Args:
        reviewer_email: Email of the PIR reviewer.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        hours_pending: Number of hours the PIR has been pending.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending PIR reminder notification",
        reviewer=reviewer_email,
        cr_id=cr_id,
        hours_pending=hours_pending,
    )

    # Send via Email
    email_service = get_email_service()
    email_result = email_service.send_pir_reminder_email(
        reviewer_email=reviewer_email,
        cr_id=cr_id,
        cr_title=cr_title,
        hours_pending=hours_pending,
    )

    # Also send via Teams if available
    message = (
        f"⏰ **PIR Reminder**\n\n"
        f"**Change Request:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Pending for:** {hours_pending} hours\n\n"
        f"This PIR is still awaiting your review. Please complete it as soon as possible.\n\n"
        f"To complete, respond with:\n"
        f"- `complete pir {cr_id}` with your review comments\n\n"
        f"⚠️ This will be escalated to management if not completed within 24 hours."
    )

    # TODO: Retrieve conversation reference for reviewer
    conversation_reference = {}
    teams_result = send_teams_notification(conversation_reference, message)

    return email_result


def notify_pir_escalation(
    manager_email: str, cr_id: str, cr_title: str, requester: str, hours_overdue: int
) -> Dict[str, Any]:
    """
    Send a PIR escalation notification to the Change Manager via Email and Teams.

    Args:
        manager_email: Email of the Change Manager.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        requester: Name/email of the requester.
        hours_overdue: Number of hours the PIR is overdue.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending PIR escalation notification",
        manager=manager_email,
        cr_id=cr_id,
        hours_overdue=hours_overdue,
    )

    # Send via Email
    email_service = get_email_service()
    email_result = email_service.send_pir_escalation_email(
        manager_email=manager_email,
        cr_id=cr_id,
        cr_title=cr_title,
        requester=requester,
        hours_overdue=hours_overdue,
    )

    # Also send via Teams if available
    message = (
        f"🚨 **PIR Escalation Required**\n\n"
        f"**Change Request:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Requested by:** {requester}\n"
        f"**Overdue by:** {hours_overdue} hours\n\n"
        f"This PIR has not been completed within the SLA timeframe and requires your attention.\n\n"
        f"Please follow up with the assigned reviewers or complete the PIR yourself."
    )

    # TODO: Retrieve conversation reference for manager
    conversation_reference = {}
    teams_result = send_teams_notification(conversation_reference, message)

    return email_result


def notify_pir_completion(
    requester_email: str, cr_id: str, cr_title: str, reviewer: str, comments: str = ""
) -> Dict[str, Any]:
    """
    Notify the requester that their PIR has been completed via Email and Teams.

    Args:
        requester_email: Email of the requester.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        reviewer: Name/email of the reviewer who completed the PIR.
        comments: Optional PIR comments.

    Returns:
        Dictionary indicating success or failure.
    """
    logger.info(
        "Sending PIR completion notification",
        requester=requester_email,
        cr_id=cr_id,
    )

    # Send via Email
    email_service = get_email_service()
    email_result = email_service.send_pir_completion_email(
        requester_email=requester_email,
        cr_id=cr_id,
        cr_title=cr_title,
        reviewer=reviewer,
        comments=comments,
    )

    # Also send via Teams if available
    message = (
        f"✅ **PIR Completed**\n\n"
        f"**Change Request:** {cr_id}\n"
        f"**Title:** {cr_title}\n"
        f"**Reviewed by:** {reviewer}\n"
    )

    if comments:
        message += f"**Comments:** {comments}\n"

    message += f"\nYour change request has been closed."

    # TODO: Retrieve conversation reference for requester
    conversation_reference = {}
    teams_result = send_teams_notification(conversation_reference, message)

    return email_result
