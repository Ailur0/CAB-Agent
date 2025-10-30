"""Event processor for handling CR changes and triggering notifications."""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_session, UserConversationReference, CRNotificationSent
from src.utils import get_logger, Config
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings

logger = get_logger(__name__)

# Event rules - define which state transitions trigger notifications
EVENT_RULES = {
    "state_transitions": [
        {"from": "Pending CAB", "to": "Approved", "notify": "creator"},
        {"from": "Pending CAB", "to": "Rejected", "notify": "creator"},
        {"from": "Draft", "to": "Pending CAB", "notify": "cab_members"},
        {"from": "Approved", "to": "In Progress", "notify": "creator"},
        {"from": "In Progress", "to": "Closed", "notify": "creator"},
    ],
}


async def process_cr_changes(cr_id, changes, cr_details):
    """
    Process CR changes and trigger appropriate notifications.
    
    Args:
        cr_id: CR ID
        changes: List of changes (field, old_value, new_value)
        cr_details: Full CR details from Azure DevOps
    """
    logger.info(f"Processing changes for CR {cr_id}", changes=changes)
    
    for change in changes:
        if change["field"] == "state":
            await handle_state_change(
                cr_id,
                change["old_value"],
                change["new_value"],
                cr_details,
            )


async def handle_state_change(cr_id, from_state, to_state, cr_details):
    """Handle state transition and send notifications."""
    logger.info(f"CR {cr_id} state changed: {from_state} -> {to_state}")
    
    # Check if this transition matches any rules
    for rule in EVENT_RULES["state_transitions"]:
        if rule["from"] == from_state and rule["to"] == to_state:
            logger.info(f"Rule matched for CR {cr_id}", rule=rule)
            
            if rule["notify"] == "creator":
                await notify_creator(cr_id, from_state, to_state, cr_details)
            elif rule["notify"] == "cab_members":
                # TODO: Implement CAB member notification
                logger.info("CAB member notification not yet implemented")


async def notify_creator(cr_id, from_state, to_state, cr_details):
    """Send notification to CR creator."""
    creator_email = cr_details.get("created_by_unique_name")
    
    if not creator_email:
        logger.warning(f"No creator email for CR {cr_id}")
        return
    
    logger.info(f"Notifying creator {creator_email} about CR {cr_id}")
    
    session = get_session()
    
    try:
        # Check if notification already sent
        event_type = f"state_change_{from_state}_to_{to_state}".replace(" ", "_").lower()
        
        existing = (
            session.query(CRNotificationSent)
            .filter_by(cr_id=cr_id, event_type=event_type, recipient_email=creator_email)
            .first()
        )
        
        if existing:
            logger.info(f"Notification already sent to {creator_email} for CR {cr_id}")
            return
        
        # Get conversation reference
        user_ref = (
            session.query(UserConversationReference)
            .filter_by(email=creator_email)
            .first()
        )
        
        if not user_ref:
            logger.warning(f"No conversation reference for {creator_email}")
            # TODO: Fallback to email
            return
        
        # Parse conversation reference from JSON string
        conversation_reference = json.loads(user_ref.conversation_reference)
        
        # Send Teams message
        message = format_notification_message(cr_id, from_state, to_state, cr_details)
        
        await send_proactive_message(conversation_reference, message)
        
        # Log notification
        notification = CRNotificationSent(
            cr_id=cr_id,
            event_type=event_type,
            recipient_email=creator_email,
        )
        session.add(notification)
        session.commit()
        
        logger.info(f"Notification sent to {creator_email} for CR {cr_id}")
        
    except Exception as e:
        logger.error(f"Failed to notify creator", error=str(e))
        session.rollback()
    finally:
        session.close()


def format_notification_message(cr_id, from_state, to_state, cr_details):
    """Format notification message for Teams."""
    title = cr_details.get("title", "")
    
    if to_state == "Approved":
        emoji = "✅"
        status = "Approved"
    elif to_state == "Rejected":
        emoji = "❌"
        status = "Rejected"
    elif to_state == "In Progress":
        emoji = "🚀"
        status = "In Progress"
    elif to_state == "Closed":
        emoji = "✔️"
        status = "Closed"
    else:
        emoji = "🔔"
        status = to_state
    
    message = f"""{emoji} **CR Status Update**

**CR ID:** {cr_id}
**Title:** {title}
**Status:** {from_state} → {status}

Your change request has been updated."""
    
    return message


async def send_proactive_message(conversation_reference, message):
    """Send proactive message via Teams bot."""
    # Create adapter
    settings = BotFrameworkAdapterSettings(
        app_id=Config.MICROSOFT_APP_ID,
        app_password=Config.MICROSOFT_APP_PASSWORD,
    )
    adapter = BotFrameworkAdapter(settings)
    
    # Send message
    async def callback(turn_context):
        await turn_context.send_activity(message)
    
    await adapter.continue_conversation(
        conversation_reference,
        callback,
        Config.MICROSOFT_APP_ID,
    )
