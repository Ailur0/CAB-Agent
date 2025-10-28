"""Google Cloud Function for handling Azure DevOps webhooks."""

import os
import sys
import json
import hmac
import hashlib
from typing import Dict, Any
import requests
from flask import Request

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.utils import get_logger

logger = get_logger(__name__)


def verify_webhook_signature(request: Request, secret: str) -> bool:
    """
    Verify the webhook signature from Azure DevOps.

    Args:
        request: Flask request object.
        secret: Shared secret for webhook verification.

    Returns:
        True if signature is valid, False otherwise.
    """
    # Get signature from header
    signature = request.headers.get("X-Azure-Signature")

    if not signature:
        logger.warning("No signature in webhook request")
        return False

    # Calculate expected signature
    body = request.get_data()
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    # Compare signatures
    is_valid = hmac.compare_digest(signature, expected_signature)

    if not is_valid:
        logger.warning("Invalid webhook signature")

    return is_valid


def send_pir_notification(user_id: str, cr_id: str, cr_title: str) -> None:
    """
    Send a PIR (Post-Implementation Review) notification.

    Args:
        user_id: User ID to notify.
        cr_id: Change Request ID.
        cr_title: Title of the change request.
    """
    bot_url = os.getenv("BOT_NOTIFY_URL", "http://localhost:3978/api/notify")

    message = (
        f"📋 **Post-Implementation Review Required**\n\n"
        f"**CR ID:** {cr_id}\n"
        f"**Title:** {cr_title}\n\n"
        f"The change request has been completed. "
        f"Please provide a post-implementation review:\n\n"
        f"1. Was the change successful?\n"
        f"2. Were there any issues?\n"
        f"3. Any lessons learned?\n\n"
        f"Reply with your PIR summary."
    )

    payload = {
        "user_id": user_id,
        "message": message,
    }

    try:
        response = requests.post(bot_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("PIR notification sent", user_id=user_id, cr_id=cr_id)
    except Exception as e:
        logger.error("Failed to send PIR notification", error=str(e), user_id=user_id)


def process_work_item_updated(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a work item updated event.

    Args:
        payload: Webhook payload from Azure DevOps.

    Returns:
        Dictionary with processing result.
    """
    logger.info("Processing work item updated event")

    try:
        # Extract work item details
        resource = payload.get("resource", {})
        fields = resource.get("fields", {})

        work_item_id = resource.get("id")
        work_item_type = fields.get("System.WorkItemType")
        state = fields.get("System.State")
        title = fields.get("System.Title")
        created_by = fields.get("System.CreatedBy")

        logger.info(
            "Work item details",
            id=work_item_id,
            type=work_item_type,
            state=state,
        )

        # Check if this is a Change Request that was closed
        if work_item_type == "Change Request" and state == "Closed":
            logger.info("Change Request closed, sending PIR notification", cr_id=work_item_id)

            # Extract user ID from created_by
            user_id = created_by  # In production, extract actual user ID

            send_pir_notification(
                user_id=user_id,
                cr_id=f"CR{work_item_id}",
                cr_title=title,
            )

            return {
                "status": "success",
                "message": "PIR notification sent",
                "cr_id": f"CR{work_item_id}",
            }

        return {
            "status": "success",
            "message": "Event processed, no action needed",
        }

    except Exception as e:
        logger.error("Error processing work item updated event", error=str(e))
        return {
            "status": "error",
            "message": str(e),
        }


def webhook_handler(request: Request) -> tuple:
    """
    Cloud Function entry point for Azure DevOps webhook handling.

    Args:
        request: Flask request object.

    Returns:
        Tuple of (response_body, status_code).
    """
    logger.info("Webhook handler triggered", method=request.method)

    # Only accept POST requests
    if request.method != "POST":
        return {"error": "Method not allowed"}, 405

    # Verify webhook signature (if secret is configured)
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    if webhook_secret:
        if not verify_webhook_signature(request, webhook_secret):
            return {"error": "Invalid signature"}, 401

    try:
        # Parse webhook payload
        payload = request.get_json()

        if not payload:
            logger.warning("Empty webhook payload")
            return {"error": "Empty payload"}, 400

        # Get event type
        event_type = payload.get("eventType")
        logger.info("Webhook event received", event_type=event_type)

        # Route to appropriate handler
        if event_type == "workitem.updated":
            result = process_work_item_updated(payload)
            return result, 200

        # Unknown event type
        logger.warning("Unknown event type", event_type=event_type)
        return {
            "status": "success",
            "message": f"Event type '{event_type}' not handled",
        }, 200

    except Exception as e:
        logger.error("Error in webhook handler", error=str(e))
        return {"error": str(e)}, 500


# For local testing
if __name__ == "__main__":
    print("\n🔗 Webhook Handler Function")
    print("=" * 50)
    print("\nThis function handles Azure DevOps webhooks.")
    print("\nSupported events:")
    print("  - workitem.updated (triggers PIR notifications)")
    print("\nConfigure webhook in Azure DevOps:")
    print("  1. Go to Project Settings > Service Hooks")
    print("  2. Create Web Hook subscription")
    print("  3. Set URL to Cloud Function URL")
    print("  4. Set event filter to 'Work item updated'")
    print()
