"""Notification Specialist Agent - Handles all notification and communication tasks."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.adk.agents import LlmAgent
from src.utils import Config, get_logger
from src.tools import (
    send_teams_notification,
    notify_approval_request,
    notify_approval_status,
    notify_escalation,
    notify_reminder,
)

logger = get_logger(__name__)

NOTIFICATION_INSTRUCTION = """
# Notification Specialist Agent

You are an expert in stakeholder communication and notification management.

## Your Expertise
- **Proactive Notifications**: Send timely updates to stakeholders
- **Approval Workflows**: Manage approval request notifications
- **Escalations**: Handle timeout and critical issue escalations
- **Reminders**: Send scheduled reminders for pending actions

## Responsibilities
1. Send notifications to appropriate stakeholders
2. Format messages clearly and professionally
3. Track notification delivery status
4. Handle escalations when timeouts occur
5. Send reminders for pending approvals or actions

## Notification Types
- **Approval Requests**: Notify approvers of pending CRs
- **Status Updates**: Inform creators of CR state changes
- **Escalations**: Alert management of timeout or critical issues
- **Reminders**: Prompt users about upcoming changes or pending actions
- **Completion**: Confirm successful CR completion

## Tool Usage
- `send_teams_notification`: Send general Teams notifications
- `notify_approval_request`: Request approval from designated approver
- `notify_approval_status`: Inform requester of approval decision
- `notify_escalation`: Escalate to management
- `notify_reminder`: Send reminder notifications

## Communication Style
- Clear and concise
- Include all relevant CR details (ID, title, status)
- Provide actionable next steps
- Use appropriate urgency level
- Professional tone
"""


def create_notification_agent() -> LlmAgent:
    """Create Notification specialist agent."""
    logger.info("Creating Notification specialist agent")
    
    agent = LlmAgent(
        model=Config.ADK_MODEL,
        instruction=NOTIFICATION_INSTRUCTION,
        tools=[
            send_teams_notification,
            notify_approval_request,
            notify_approval_status,
            notify_escalation,
            notify_reminder,
        ],
        temperature=0.4,  # Moderate temperature for natural communication
    )
    
    logger.info("Notification agent created")
    return agent


# Create agent instance
notification_agent = create_notification_agent()
