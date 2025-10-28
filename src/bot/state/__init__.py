"""State management module for the Teams bot."""

from .conversation_state_manager import (
    ConversationStateManager,
    ConversationReferenceManager,
    conversation_state_manager,
    conversation_reference_manager,
)

__all__ = [
    "ConversationStateManager",
    "ConversationReferenceManager",
    "conversation_state_manager",
    "conversation_reference_manager",
]
