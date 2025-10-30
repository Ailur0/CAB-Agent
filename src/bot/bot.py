"""Microsoft Teams bot implementation for Change Management System."""

from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils import get_logger
from src.bot.state import conversation_state_manager, conversation_reference_manager
from src.bot.dialogs import create_cr_dialog

logger = get_logger(__name__)


class ChangeManagementBot(ActivityHandler):
    """
    Teams bot that handles user interactions for change management workflows.
    
    This bot processes user commands, manages conversation state, and integrates
    with the ADK backend for workflow orchestration.
    """

    def __init__(self):
        """Initialize the Change Management Bot."""
        super().__init__()
        logger.info("ChangeManagementBot initialized")

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming message activities from users.

        Args:
            turn_context: Context object containing information about the incoming activity.
        """
        user_message = turn_context.activity.text.strip()
        user_name = turn_context.activity.from_property.name
        user_id = turn_context.activity.from_property.id
        conversation_id = turn_context.activity.conversation.id
        
        logger.info(
            "Received message",
            user=user_name,
            message=user_message,
            conversation_id=conversation_id,
        )

        # Save conversation reference for proactive messaging
        conversation_ref = TurnContext.get_conversation_reference(turn_context.activity)
        conversation_reference_manager.save_reference(user_id, conversation_ref)

        # Set user context
        conversation_state_manager.set_user_context(
            conversation_id,
            user_email=turn_context.activity.from_property.aad_object_id or user_id,
            user_name=user_name,
        )

        # Check if there's an active dialog
        pending = conversation_state_manager.get_pending_request(conversation_id)
        
        if pending and pending["type"] == "create_cr":
            # Continue the create CR dialog
            result = await create_cr_dialog.process_step(conversation_id, user_message)
            await turn_context.send_activity(MessageFactory.text(result["response"]))
            return

        # Parse command and route to appropriate handler
        if user_message.lower().startswith("create"):
            await self._handle_create_request(turn_context, user_message)
        elif user_message.lower().startswith("extend"):
            await self._handle_extend_request(turn_context, user_message)
        elif user_message.lower().startswith("status"):
            await self._handle_status_request(turn_context, user_message)
        elif user_message.lower() in ["help", "?"]:
            await self._handle_help_request(turn_context)
        else:
            # Default: Process with ADK agent
            await self._process_with_agent(turn_context, user_message)

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        """
        Handle new members being added to the conversation.

        Args:
            members_added: List of members that were added.
            turn_context: Context object for the current turn.
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                logger.info("New member added", member_name=member.name, member_id=member.id)
                
                welcome_message = (
                    f"Welcome to the Change Management System, {member.name}! 👋\n\n"
                    "I can help you with:\n"
                    "- **Create** new change requests\n"
                    "- **Extend** existing change requests\n"
                    "- **Check status** of your requests\n"
                    "- **Approve** or **reject** pending requests\n\n"
                    "Type **help** to see available commands."
                )
                
                await turn_context.send_activity(MessageFactory.text(welcome_message))

    async def on_teams_team_renamed_activity(
        self, team_info: dict, turn_context: TurnContext
    ):
        """
        Handle team rename events.

        Args:
            team_info: Information about the renamed team.
            turn_context: Context object for the current turn.
        """
        logger.info("Team renamed", new_name=team_info.get("name"))
        return await super().on_teams_team_renamed_activity(team_info, turn_context)

    async def _handle_create_request(self, turn_context: TurnContext, message: str):
        """
        Handle create change request command.

        Args:
            turn_context: Context object for the current turn.
            message: User's message text.
        """
        logger.info("Handling create request", message=message)
        
        conversation_id = turn_context.activity.conversation.id
        
        # Start the create CR dialog
        response = await create_cr_dialog.start_dialog(conversation_id, message)
        await turn_context.send_activity(MessageFactory.text(response))

    async def _handle_extend_request(self, turn_context: TurnContext, message: str):
        """
        Handle extend change request command.

        Args:
            turn_context: Context object for the current turn.
            message: User's message text.
        """
        logger.info("Handling extend request", message=message)
        
        response = (
            "⏰ Processing extension request...\n\n"
            "I'll validate the change request and check for conflicts."
        )
        
        await turn_context.send_activity(MessageFactory.text(response))
        
        # TODO: Integrate with ADK agent
        # await self._call_adk_agent("extend_cr", message)

    async def _handle_status_request(self, turn_context: TurnContext, message: str):
        """
        Handle status check command.

        Args:
            turn_context: Context object for the current turn.
            message: User's message text.
        """
        logger.info("Handling status request", message=message)
        
        response = "📊 Checking status of your change requests..."
        
        await turn_context.send_activity(MessageFactory.text(response))
        
        # TODO: Query Azure DevOps for CR status
        # await self._query_cr_status(user_id)

    async def _handle_help_request(self, turn_context: TurnContext):
        """
        Handle help command.

        Args:
            turn_context: Context object for the current turn.
        """
        logger.info("Handling help request")
        
        help_text = (
            "**Change Management Bot - Available Commands**\n\n"
            "**Creating Requests:**\n"
            "- `create CR for database migration on Friday 6pm`\n"
            "- `create change request for server maintenance`\n\n"
            "**Managing Requests:**\n"
            "- `extend CR12345 by 2 hours`\n"
            "- `status of CR12345`\n"
            "- `status` - Show all my requests\n\n"
            "**Approvals:**\n"
            "- `approve CR12345`\n"
            "- `reject CR12345 - conflicts with deployment`\n\n"
            "**General:**\n"
            "- `help` - Show this message\n\n"
            "You can also just describe what you need in natural language, "
            "and I'll understand! 🤖"
        )
        
        await turn_context.send_activity(MessageFactory.text(help_text))

    async def _process_with_agent(self, turn_context: TurnContext, message: str):
        """
        Process message with OpenAI agent for natural language understanding.

        Args:
            turn_context: Context object for the current turn.
            message: User's message text.
        """
        logger.info("Processing with OpenAI", message=message)
        
        # Import OpenAI agent
        from src.bot.gemini_integration import get_openai_agent
        
        try:
            # Get user info
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name
            
            # Process with OpenAI
            agent = get_openai_agent()
            response = await agent.process_message(user_id, message, user_name)
            
            # Send response
            await turn_context.send_activity(MessageFactory.text(response))
            
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}", exc_info=True)
            await turn_context.send_activity(
                MessageFactory.text(
                    f"❌ Sorry, I encountered an error: {str(e)}\n\n"
                    "Please try again or use specific commands like 'help'."
                )
            )

    async def _call_adk_agent(self, agent_type: str, message: str) -> str:
        """
        Call the ADK agent backend for processing.

        Args:
            agent_type: Type of agent to call (orchestrator, validate, etc.).
            message: User message to process.

        Returns:
            Agent response text.
        """
        # TODO: Implement actual ADK agent integration
        # This will be implemented in Phase 3
        logger.info("ADK agent call", agent_type=agent_type, message=message)
        return "Agent response placeholder"
