"""Multi-turn dialog for creating change requests."""

import sys
import os
from typing import Dict, Any
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.utils import get_logger
from src.bot.state import conversation_state_manager

logger = get_logger(__name__)


class CreateCRDialog:
    """
    Multi-turn dialog for gathering information to create a change request.
    
    This implements a waterfall-style dialog without the Bot Framework's
    WaterfallDialog for simplicity. In production, consider using the
    official dialog system.
    """

    STEPS = [
        "title",
        "description",
        "scheduled_time",
        "duration",
        "confirmation",
    ]

    def __init__(self):
        """Initialize the create CR dialog."""
        logger.info("CreateCRDialog initialized")

    async def start_dialog(self, conversation_id: str, user_message: str) -> str:
        """
        Start the create CR dialog.

        Args:
            conversation_id: Unique conversation identifier.
            user_message: Initial user message that triggered the dialog.

        Returns:
            Response message to send to the user.
        """
        logger.info("Starting create CR dialog", conversation_id=conversation_id)

        # Initialize dialog state
        conversation_state_manager.set_pending_request(
            conversation_id,
            "create_cr",
            {
                "step": "title",
                "collected_data": {},
                "initial_message": user_message,
            },
        )

        return (
            "📝 **Let's create a new Change Request**\n\n"
            "I'll need some information from you.\n\n"
            "**Step 1/4:** What is the title of this change request?\n"
            "Example: 'Database migration for customer portal'"
        )

    async def process_step(
        self, conversation_id: str, user_message: str
    ) -> Dict[str, Any]:
        """
        Process a step in the dialog.

        Args:
            conversation_id: Unique conversation identifier.
            user_message: User's response to the current step.

        Returns:
            Dictionary with 'response' message and 'complete' flag.
        """
        pending = conversation_state_manager.get_pending_request(conversation_id)

        if not pending or pending["type"] != "create_cr":
            return {
                "response": "No active create CR dialog found. Type 'create' to start.",
                "complete": True,
            }

        current_step = pending["data"]["step"]
        collected_data = pending["data"]["collected_data"]

        logger.info(
            "Processing dialog step",
            conversation_id=conversation_id,
            step=current_step,
        )

        # Process based on current step
        if current_step == "title":
            return await self._process_title(
                conversation_id, user_message, collected_data
            )
        elif current_step == "description":
            return await self._process_description(
                conversation_id, user_message, collected_data
            )
        elif current_step == "scheduled_time":
            return await self._process_scheduled_time(
                conversation_id, user_message, collected_data
            )
        elif current_step == "duration":
            return await self._process_duration(
                conversation_id, user_message, collected_data
            )
        elif current_step == "confirmation":
            return await self._process_confirmation(
                conversation_id, user_message, collected_data
            )

        return {
            "response": "Unknown step in dialog. Please start over.",
            "complete": True,
        }

    async def _process_title(
        self, conversation_id: str, user_message: str, collected_data: Dict
    ) -> Dict[str, Any]:
        """Process the title step."""
        collected_data["title"] = user_message

        # Move to next step
        conversation_state_manager.update_state(
            conversation_id,
            {
                "pending_requests": [
                    {
                        "type": "create_cr",
                        "data": {
                            "step": "description",
                            "collected_data": collected_data,
                        },
                    }
                ]
            },
        )

        return {
            "response": (
                f"✅ Title: **{user_message}**\n\n"
                "**Step 2/4:** Please provide a detailed description of the change.\n"
                "Include what will be changed, why, and any potential impacts."
            ),
            "complete": False,
        }

    async def _process_description(
        self, conversation_id: str, user_message: str, collected_data: Dict
    ) -> Dict[str, Any]:
        """Process the description step."""
        collected_data["description"] = user_message

        # Move to next step
        conversation_state_manager.update_state(
            conversation_id,
            {
                "pending_requests": [
                    {
                        "type": "create_cr",
                        "data": {
                            "step": "scheduled_time",
                            "collected_data": collected_data,
                        },
                    }
                ]
            },
        )

        return {
            "response": (
                "✅ Description saved.\n\n"
                "**Step 3/4:** When should this change be scheduled?\n"
                "Please provide in format: `YYYY-MM-DD HH:MM` (24-hour format)\n"
                "Example: `2025-10-25 18:00`"
            ),
            "complete": False,
        }

    async def _process_scheduled_time(
        self, conversation_id: str, user_message: str, collected_data: Dict
    ) -> Dict[str, Any]:
        """Process the scheduled time step."""
        # Parse the time
        try:
            # Try to parse the user's input
            scheduled_dt = datetime.strptime(user_message.strip(), "%Y-%m-%d %H:%M")

            # Check if it's in the future
            if scheduled_dt < datetime.now():
                return {
                    "response": (
                        "⚠️ The scheduled time must be in the future.\n"
                        "Please provide a valid future date and time.\n"
                        "Format: `YYYY-MM-DD HH:MM`"
                    ),
                    "complete": False,
                }

            collected_data["scheduled_time"] = scheduled_dt.isoformat()

            # Move to next step
            conversation_state_manager.update_state(
                conversation_id,
                {
                    "pending_requests": [
                        {
                            "type": "create_cr",
                            "data": {
                                "step": "duration",
                                "collected_data": collected_data,
                            },
                        }
                    ]
                },
            )

            return {
                "response": (
                    f"✅ Scheduled for: **{scheduled_dt.strftime('%Y-%m-%d at %H:%M')}**\n\n"
                    "**Step 4/4:** How long will this change take?\n"
                    "Please provide duration in hours (e.g., `2` for 2 hours, `0.5` for 30 minutes)"
                ),
                "complete": False,
            }

        except ValueError:
            return {
                "response": (
                    "⚠️ Invalid date/time format.\n"
                    "Please use format: `YYYY-MM-DD HH:MM`\n"
                    "Example: `2025-10-25 18:00`"
                ),
                "complete": False,
            }

    async def _process_duration(
        self, conversation_id: str, user_message: str, collected_data: Dict
    ) -> Dict[str, Any]:
        """Process the duration step."""
        try:
            duration = float(user_message.strip())

            if duration <= 0:
                return {
                    "response": "⚠️ Duration must be greater than 0. Please try again.",
                    "complete": False,
                }

            collected_data["duration_hours"] = duration

            # Move to confirmation step
            conversation_state_manager.update_state(
                conversation_id,
                {
                    "pending_requests": [
                        {
                            "type": "create_cr",
                            "data": {
                                "step": "confirmation",
                                "collected_data": collected_data,
                            },
                        }
                    ]
                },
            )

            # Format scheduled time for display
            scheduled_dt = datetime.fromisoformat(collected_data["scheduled_time"])

            return {
                "response": (
                    "📋 **Please review your Change Request:**\n\n"
                    f"**Title:** {collected_data['title']}\n"
                    f"**Description:** {collected_data['description']}\n"
                    f"**Scheduled:** {scheduled_dt.strftime('%Y-%m-%d at %H:%M')}\n"
                    f"**Duration:** {duration} hour(s)\n\n"
                    "Type **confirm** to create this CR, or **cancel** to abort."
                ),
                "complete": False,
            }

        except ValueError:
            return {
                "response": (
                    "⚠️ Invalid duration. Please provide a number.\n"
                    "Example: `2` for 2 hours, `0.5` for 30 minutes"
                ),
                "complete": False,
            }

    async def _process_confirmation(
        self, conversation_id: str, user_message: str, collected_data: Dict
    ) -> Dict[str, Any]:
        """Process the confirmation step."""
        user_response = user_message.strip().lower()

        if user_response == "confirm":
            # Clear the dialog
            conversation_state_manager.clear_pending_request(conversation_id)

            # Get user context
            user_context = conversation_state_manager.get_user_context(conversation_id)

            # TODO: Call ADK agent to create the CR
            # For now, return success message
            return {
                "response": (
                    "✅ **Change Request Created Successfully!**\n\n"
                    f"**CR ID:** CR12345 (placeholder)\n"
                    f"**Title:** {collected_data['title']}\n"
                    f"**Status:** Proposed\n\n"
                    "The request has been submitted for validation and approval.\n"
                    "You will be notified of any updates."
                ),
                "complete": True,
                "cr_data": collected_data,
            }

        elif user_response == "cancel":
            # Clear the dialog
            conversation_state_manager.clear_pending_request(conversation_id)

            return {
                "response": "❌ Change Request creation cancelled.",
                "complete": True,
            }

        else:
            return {
                "response": (
                    "Please type **confirm** to create the CR, or **cancel** to abort."
                ),
                "complete": False,
            }


# Singleton instance
create_cr_dialog = CreateCRDialog()
