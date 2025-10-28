"""Conversation state management for the Teams bot."""

import sys
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.utils import get_logger

logger = get_logger(__name__)


class ConversationStateManager:
    """
    Manages conversation state for multi-turn dialogs.
    
    In production, this should use Azure Blob Storage or Cosmos DB.
    For now, using in-memory storage for development.
    """

    def __init__(self):
        """Initialize the conversation state manager."""
        self._state_store: Dict[str, Dict[str, Any]] = {}
        logger.info("ConversationStateManager initialized")

    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the state for a conversation.

        Args:
            conversation_id: Unique conversation identifier.

        Returns:
            Dictionary containing conversation state.
        """
        if conversation_id not in self._state_store:
            self._state_store[conversation_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "pending_requests": [],
                "current_dialog": None,
                "user_context": {},
            }
            logger.info("Created new conversation state", conversation_id=conversation_id)

        return self._state_store[conversation_id]

    def update_state(
        self, conversation_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the state for a conversation.

        Args:
            conversation_id: Unique conversation identifier.
            updates: Dictionary of state updates to apply.

        Returns:
            Updated conversation state.
        """
        state = self.get_state(conversation_id)
        state.update(updates)
        state["last_updated"] = datetime.utcnow().isoformat()

        logger.info(
            "Updated conversation state",
            conversation_id=conversation_id,
            updated_keys=list(updates.keys()),
        )

        return state

    def set_pending_request(
        self, conversation_id: str, request_type: str, request_data: Dict[str, Any]
    ) -> None:
        """
        Set a pending request that requires user input.

        Args:
            conversation_id: Unique conversation identifier.
            request_type: Type of request (e.g., "create_cr", "extend_cr").
            request_data: Data associated with the request.
        """
        state = self.get_state(conversation_id)

        pending_request = {
            "type": request_type,
            "data": request_data,
            "created_at": datetime.utcnow().isoformat(),
        }

        state["pending_requests"].append(pending_request)
        state["current_dialog"] = request_type
        state["last_updated"] = datetime.utcnow().isoformat()

        logger.info(
            "Set pending request",
            conversation_id=conversation_id,
            request_type=request_type,
        )

    def get_pending_request(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent pending request.

        Args:
            conversation_id: Unique conversation identifier.

        Returns:
            Pending request dictionary or None if no pending requests.
        """
        state = self.get_state(conversation_id)
        pending_requests = state.get("pending_requests", [])

        if pending_requests:
            return pending_requests[-1]

        return None

    def clear_pending_request(self, conversation_id: str) -> None:
        """
        Clear the most recent pending request.

        Args:
            conversation_id: Unique conversation identifier.
        """
        state = self.get_state(conversation_id)

        if state.get("pending_requests"):
            state["pending_requests"].pop()
            state["current_dialog"] = None
            state["last_updated"] = datetime.utcnow().isoformat()

            logger.info("Cleared pending request", conversation_id=conversation_id)

    def set_user_context(
        self, conversation_id: str, user_email: str, user_name: str
    ) -> None:
        """
        Set user context information.

        Args:
            conversation_id: Unique conversation identifier.
            user_email: User's email address.
            user_name: User's display name.
        """
        state = self.get_state(conversation_id)
        state["user_context"] = {
            "email": user_email,
            "name": user_name,
            "last_interaction": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Set user context",
            conversation_id=conversation_id,
            user_email=user_email,
        )

    def get_user_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get user context information.

        Args:
            conversation_id: Unique conversation identifier.

        Returns:
            User context dictionary.
        """
        state = self.get_state(conversation_id)
        return state.get("user_context", {})

    def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """
        Clean up conversation states older than specified hours.

        Args:
            max_age_hours: Maximum age in hours before cleanup.

        Returns:
            Number of states cleaned up.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        conversations_to_remove = []

        for conv_id, state in self._state_store.items():
            last_updated = datetime.fromisoformat(state["last_updated"])
            if last_updated < cutoff_time:
                conversations_to_remove.append(conv_id)

        for conv_id in conversations_to_remove:
            del self._state_store[conv_id]

        logger.info("Cleaned up old states", count=len(conversations_to_remove))
        return len(conversations_to_remove)


class ConversationReferenceManager:
    """
    Manages conversation references for proactive messaging.
    
    In production, this should use Cosmos DB with TTL.
    For now, using in-memory storage for development.
    """

    def __init__(self):
        """Initialize the conversation reference manager."""
        self._reference_store: Dict[str, Dict[str, Any]] = {}
        logger.info("ConversationReferenceManager initialized")

    def save_reference(
        self, user_id: str, conversation_reference: Dict[str, Any]
    ) -> None:
        """
        Save a conversation reference for a user.

        Args:
            user_id: Unique user identifier.
            conversation_reference: Bot Framework conversation reference.
        """
        self._reference_store[user_id] = {
            "reference": conversation_reference,
            "saved_at": datetime.utcnow().isoformat(),
        }

        logger.info("Saved conversation reference", user_id=user_id)

    def get_reference(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the conversation reference for a user.

        Args:
            user_id: Unique user identifier.

        Returns:
            Conversation reference dictionary or None if not found.
        """
        stored = self._reference_store.get(user_id)

        if stored:
            logger.info("Retrieved conversation reference", user_id=user_id)
            return stored["reference"]

        logger.warning("Conversation reference not found", user_id=user_id)
        return None

    def delete_reference(self, user_id: str) -> bool:
        """
        Delete a conversation reference.

        Args:
            user_id: Unique user identifier.

        Returns:
            True if deleted, False if not found.
        """
        if user_id in self._reference_store:
            del self._reference_store[user_id]
            logger.info("Deleted conversation reference", user_id=user_id)
            return True

        return False

    def cleanup_old_references(self, max_age_days: int = 30) -> int:
        """
        Clean up conversation references older than specified days.

        Args:
            max_age_days: Maximum age in days before cleanup.

        Returns:
            Number of references cleaned up.
        """
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        users_to_remove = []

        for user_id, stored in self._reference_store.items():
            saved_at = datetime.fromisoformat(stored["saved_at"])
            if saved_at < cutoff_time:
                users_to_remove.append(user_id)

        for user_id in users_to_remove:
            del self._reference_store[user_id]

        logger.info("Cleaned up old references", count=len(users_to_remove))
        return len(users_to_remove)


# Singleton instances
conversation_state_manager = ConversationStateManager()
conversation_reference_manager = ConversationReferenceManager()
