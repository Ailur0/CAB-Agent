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
    Manages conversation references for proactive messaging using SQL Server database.
    """

    def __init__(self):
        """Initialize the conversation reference manager."""
        logger.info("ConversationReferenceManager initialized (using database)")

    def save_reference(
        self, user_id: str, conversation_reference: Dict[str, Any]
    ) -> None:
        """
        Save a conversation reference for a user to database.

        Args:
            user_id: Unique user identifier.
            conversation_reference: Bot Framework conversation reference.
        """
        try:
            from src.database import get_session, UserConversationReference
            import json
            
            session = get_session()
            
            # Extract user info from conversation reference
            user_info = conversation_reference.get("user", {})
            email = user_info.get("email") or user_info.get("userPrincipalName")
            aad_object_id = user_info.get("aadObjectId")
            name = user_info.get("name")
            
            # Check if reference exists
            existing = session.query(UserConversationReference).filter_by(user_id=user_id).first()
            
            if existing:
                # Update existing
                existing.conversation_reference = json.dumps(conversation_reference)
                existing.updated_at = datetime.utcnow()
                existing.last_interaction_at = datetime.utcnow()
                if email:
                    existing.email = email
                if aad_object_id:
                    existing.aad_object_id = aad_object_id
                if name:
                    existing.name = name
            else:
                # Create new
                new_ref = UserConversationReference(
                    user_id=user_id,
                    email=email,
                    aad_object_id=aad_object_id,
                    name=name,
                    conversation_reference=json.dumps(conversation_reference),
                )
                session.add(new_ref)
            
            session.commit()
            session.close()
            
            logger.info("Saved conversation reference to database", user_id=user_id, email=email)
            
        except Exception as e:
            logger.error("Failed to save conversation reference", error=str(e))

    def get_reference(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the conversation reference for a user from database.

        Args:
            user_id: Unique user identifier.

        Returns:
            Conversation reference dictionary or None if not found.
        """
        try:
            from src.database import get_session, UserConversationReference
            import json
            
            session = get_session()
            user_ref = session.query(UserConversationReference).filter_by(user_id=user_id).first()
            session.close()
            
            if user_ref:
                logger.info("Retrieved conversation reference from database", user_id=user_id)
                return json.loads(user_ref.conversation_reference)
            
            logger.warning("Conversation reference not found in database", user_id=user_id)
            return None
            
        except Exception as e:
            logger.error("Failed to get conversation reference", error=str(e))
            return None

    def delete_reference(self, user_id: str) -> bool:
        """
        Delete a conversation reference from database.

        Args:
            user_id: Unique user identifier.

        Returns:
            True if deleted, False if not found.
        """
        try:
            from src.database import get_session, UserConversationReference
            
            session = get_session()
            user_ref = session.query(UserConversationReference).filter_by(user_id=user_id).first()
            
            if user_ref:
                session.delete(user_ref)
                session.commit()
                session.close()
                logger.info("Deleted conversation reference from database", user_id=user_id)
                return True
            
            session.close()
            return False
            
        except Exception as e:
            logger.error("Failed to delete conversation reference", error=str(e))
            return False

    def cleanup_old_references(self, max_age_days: int = 30) -> int:
        """
        Clean up conversation references older than specified days from database.

        Args:
            max_age_days: Maximum age in days before cleanup.

        Returns:
            Number of references cleaned up.
        """
        try:
            from src.database import get_session, UserConversationReference
            
            cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
            
            session = get_session()
            old_refs = session.query(UserConversationReference).filter(
                UserConversationReference.last_interaction_at < cutoff_time
            ).all()
            
            count = len(old_refs)
            
            for ref in old_refs:
                session.delete(ref)
            
            session.commit()
            session.close()
            
            logger.info("Cleaned up old references from database", count=count)
            return count
            
        except Exception as e:
            logger.error("Failed to cleanup old references", error=str(e))
            return 0


# Singleton instances
conversation_state_manager = ConversationStateManager()
conversation_reference_manager = ConversationReferenceManager()
