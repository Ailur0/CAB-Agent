"""Event processor for handling CR changes and triggering notifications."""

import sys
import os
import requests
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_session, UserConversationReference, CRNotificationSent
from src.utils import get_logger, Config

logger = get_logger(__name__)

# Event rules - define which state transitions trigger notifications
EVENT_RULES = {
    "state_transitions": [
        {"from": "Pending CAB", "to": "Approved", "notify": "creator"},
        {"from": "Pending CAB", "to": "Rejected", "notify": "creator"},
        {"from": "Draft", "to": "Pending CAB", "notify": "cab_members"},
        {"from": "Approved", "to": "In Progress", "notify": "creator"},
        {"from": "In Progress", "to": "Awaiting PIR", "notify": "creator", "action": "initiate_pir"},
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
            
            # Handle special actions
            if rule.get("action") == "initiate_pir":
                await initiate_pir_workflow(cr_id, cr_details)


async def notify_creator(cr_id, from_state, to_state, cr_details):
    """Send notification to CR creator via Teams webhook."""
    creator_email = cr_details.get("created_by_unique_name")
    title = cr_details.get("title", "")
    
    if not creator_email:
        logger.warning(f"No creator email for CR {cr_id}")
        return
    
    logger.info(f"Notifying about CR {cr_id} via Teams webhook")
    
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
            logger.info(f"Notification already sent for CR {cr_id}")
            return
        
        # Send Teams webhook notification (channel)
        webhook_success = send_teams_webhook_notification(
            cr_id=cr_id,
            title=title,
            creator_email=creator_email,
            from_state=from_state,
            to_state=to_state
        )
        
        # Send Power Automate notification (personal DM)
        power_automate_success = send_power_automate_notification(
            user_email=creator_email,
            cr_id=cr_id,
            title=title,
            from_state=from_state,
            to_state=to_state
        )
        
        if webhook_success or power_automate_success:
            # Log notification
            notification = CRNotificationSent(
                cr_id=cr_id,
                event_type=event_type,
                recipient_email=creator_email,
            )
            session.add(notification)
            session.commit()
            
            logger.info(f"Notification sent for CR {cr_id}", webhook=webhook_success, power_automate=power_automate_success)
        
    except Exception as e:
        logger.error(f"Failed to notify via webhook", error=str(e))
        session.rollback()
    finally:
        session.close()


async def initiate_pir_workflow(cr_id, cr_details):
    """Initiate PIR tracking workflow when CR moves to Awaiting PIR."""
    logger.info(f"Initiating PIR workflow for CR {cr_id}")
    
    try:
        # Import here to avoid circular dependency
        from src.agents.pir_agent import initiate_pir_tracking
        
        title = cr_details.get("title", "")
        creator_email = cr_details.get("created_by_unique_name")
        
        if not creator_email:
            logger.warning(f"No creator email for CR {cr_id}, cannot initiate PIR")
            return
        
        # Initiate PIR tracking
        result = initiate_pir_tracking(
            cr_id=cr_id,
            cr_title=title,
            requester_email=creator_email,
        )
        
        if result.get("status") == "success":
            logger.info(f"PIR workflow initiated for CR {cr_id}", pir_id=result.get("pir_id"))
        else:
            logger.error(f"Failed to initiate PIR workflow for CR {cr_id}", error=result.get("message"))
            
    except Exception as e:
        logger.error(f"Error initiating PIR workflow for CR {cr_id}", error=str(e))


def send_teams_webhook_notification(cr_id, title, creator_email, from_state, to_state):
    """Send notification via Teams webhook."""
    webhook_url = Config.TEAMS_WEBHOOK_URL
    
    if not webhook_url:
        logger.warning("TEAMS_WEBHOOK_URL not configured in .env file")
        return False
    
    # Choose emoji and color based on new state
    if "Approved" in to_state:
        emoji = "✅"
        color = "28A745"  # Green
    elif "Rejected" in to_state:
        emoji = "❌"
        color = "DC3545"  # Red
    elif "Progress" in to_state:
        emoji = "🚀"
        color = "0078D4"  # Blue
    elif "PIR" in to_state:
        emoji = "📋"
        color = "FFC107"  # Yellow
    elif "Closed" in to_state:
        emoji = "✔️"
        color = "6C757D"  # Gray
    else:
        emoji = "🔔"
        color = "FFC107"  # Yellow
    
    # Generate CR link
    cr_link = Config.get_work_item_url(cr_id.replace("CR", ""))
    
    # Build MessageCard payload
    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"CR {cr_id} Status Update",
        "themeColor": color,
        "title": f"{emoji} CR Status Update: {cr_id}",
        "text": "Change request status has changed.",
        "sections": [{
            "facts": [
                {"name": "CR ID", "value": cr_id},
                {"name": "Title", "value": title[:100]},  # Truncate long titles
                {"name": "Creator", "value": creator_email},
                {"name": "Previous Status", "value": from_state},
                {"name": "New Status", "value": to_state}
            ]
        }],
        "potentialAction": [{
            "@type": "OpenUri",
            "name": "View CR in Azure DevOps",
            "targets": [{"os": "default", "uri": cr_link}]
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Teams webhook notification sent", cr_id=cr_id)
            return True
        else:
            logger.error(
                "Failed to send Teams webhook",
                status=response.status_code,
                response=response.text
            )
            return False
            
    except Exception as e:
        logger.error("Error sending Teams webhook", error=str(e))
        return False


def send_power_automate_notification(user_email, cr_id, title, from_state, to_state):
    """Send personal notification via Power Automate flow."""
    flow_url = Config.POWER_AUTOMATE_URL
    
    if not flow_url:
        logger.debug("POWER_AUTOMATE_URL not configured, skipping personal notification")
        return False
    
    # Generate CR link
    cr_link = Config.get_work_item_url(cr_id.replace("CR", ""))
    
    payload = {
        "user_email": user_email,
        "cr_id": cr_id,
        "title": title,
        "from_state": from_state,
        "to_state": to_state,
        "cr_link": cr_link
    }
    
    try:
        response = requests.post(flow_url, json=payload, timeout=10)
        
        if response.status_code == 202:  # Power Automate returns 202 Accepted
            logger.info("Power Automate notification sent", user_email=user_email, cr_id=cr_id)
            return True
        else:
            logger.error(
                "Failed to send Power Automate notification",
                status=response.status_code,
                response=response.text
            )
            return False
            
    except Exception as e:
        logger.error("Error sending Power Automate notification", error=str(e))
        return False
