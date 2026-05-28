"""
Ensure all SQLAlchemy models are imported so relationship() targets resolve
before the first mapper configuration or metadata initialization.
"""

from app.models.db_chat_message import ChatMessage
from app.models.db_chat_session import ChatSession
from app.models.db_parent_chunk import ParentChunk
from app.models.db_user import User

__all__ = ["User", "ChatSession", "ChatMessage", "ParentChunk"]
