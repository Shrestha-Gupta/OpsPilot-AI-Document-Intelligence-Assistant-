"""
Conversation and message management service using Supabase PostgreSQL.
Handles conversation threads, persistent chat history, and sources attribution.
"""
import logging
from typing import List, Dict, Any, Optional

from app.db.supabase import get_supabase
from app.core.exceptions import AppError

logger = logging.getLogger("opspilot.conversation")


class ConversationService:
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations ordered by updated_at descending."""
        supabase = get_supabase()
        try:
            res = (
                supabase.table("conversations")
                .select("*")
                .order("updated_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            raise AppError(
                message="Failed to retrieve conversations",
                status_code=500,
                error_code="DB_QUERY_FAILED",
            )

    def create_conversation(self, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new conversation thread."""
        supabase = get_supabase()
        payload = {}
        if title:
            payload["title"] = title

        try:
            res = supabase.table("conversations").insert(payload).execute()
            if not res.data:
                raise RuntimeError("No data returned from conversation creation")
            return res.data[0]
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise AppError(
                message="Failed to create conversation",
                status_code=500,
                error_code="DB_INSERT_FAILED",
            )

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation record by ID."""
        supabase = get_supabase()
        try:
            res = (
                supabase.table("conversations")
                .select("*")
                .eq("id", conv_id)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Failed to get conversation {conv_id}: {e}")
            raise AppError(
                message="Failed to retrieve conversation",
                status_code=500,
                error_code="DB_QUERY_FAILED",
            )

    def get_conversation_with_messages(self, conv_id: str) -> Dict[str, Any]:
        """Get conversation and all its messages in chronological order."""
        conv = self.get_conversation(conv_id)
        if not conv:
            raise AppError(
                message=f"Conversation {conv_id} not found",
                status_code=404,
                error_code="CONVERSATION_NOT_FOUND",
            )

        supabase = get_supabase()
        try:
            res = (
                supabase.table("messages")
                .select("*")
                .eq("conversation_id", conv_id)
                .order("created_at", desc=False)
                .execute()
            )
            conv["messages"] = res.data or []
            return conv
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conv_id}: {e}")
            raise AppError(
                message="Failed to retrieve conversation messages",
                status_code=500,
                error_code="DB_QUERY_FAILED",
            )

    def delete_conversation(self, conv_id: str) -> None:
        """Delete conversation and its cascade-deleted messages."""
        conv = self.get_conversation(conv_id)
        if not conv:
            raise AppError(
                message=f"Conversation {conv_id} not found",
                status_code=404,
                error_code="CONVERSATION_NOT_FOUND",
            )

        supabase = get_supabase()
        try:
            supabase.table("conversations").delete().eq("id", conv_id).execute()
            logger.info(f"Deleted conversation {conv_id}")
        except Exception as e:
            logger.error(f"Failed to delete conversation {conv_id}: {e}")
            raise AppError(
                message="Failed to delete conversation",
                status_code=500,
                error_code="DB_DELETE_FAILED",
            )

    def clear_messages(self, conv_id: str) -> None:
        """Delete all messages inside a conversation without deleting the conversation."""
        supabase = get_supabase()
        try:
            supabase.table("messages").delete().eq("conversation_id", conv_id).execute()
            logger.info(f"Cleared messages in conversation {conv_id}")
        except Exception as e:
            logger.error(f"Failed to clear messages in conversation {conv_id}: {e}")
            raise AppError(
                message="Failed to clear messages",
                status_code=500,
                error_code="DB_DELETE_FAILED",
            )

    def add_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Insert a message (user or assistant) into the conversation."""
        supabase = get_supabase()
        payload: Dict[str, Any] = {
            "conversation_id": conv_id,
            "role": role,
            "content": content,
            "sources": sources,
        }

        try:
            res = supabase.table("messages").insert(payload).execute()
            if not res.data:
                raise RuntimeError("No data returned from message insert")
            return res.data[0]
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conv_id}: {e}")
            raise AppError(
                message="Failed to save message",
                status_code=500,
                error_code="DB_INSERT_FAILED",
            )

    def update_title_if_default(self, conv_id: str, new_title: str) -> None:
        """Update conversation title if it is currently None or default."""
        conv = self.get_conversation(conv_id)
        if conv and not conv.get("title"):
            truncated = (new_title[:45] + "...") if len(new_title) > 45 else new_title
            supabase = get_supabase()
            try:
                supabase.table("conversations").update({"title": truncated}).eq("id", conv_id).execute()
            except Exception as e:
                logger.error(f"Failed to update conversation title: {e}")

    def get_recent_messages(self, conv_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent N messages for LLM context."""
        supabase = get_supabase()
        try:
            res = (
                supabase.table("messages")
                .select("role, content")
                .eq("conversation_id", conv_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            # Reverse so they are in chronological order
            data = res.data or []
            data.reverse()
            return data
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []


_conversation_service: ConversationService | None = None


def get_conversation_service() -> ConversationService:
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
