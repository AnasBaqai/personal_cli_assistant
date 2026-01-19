"""Persistent conversation history management."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

from ..utils.config import config
from ..utils.exceptions import HistoryError
from ..utils.logger import get_logger
from .memory import ConversationMemory

logger = get_logger(__name__)


@dataclass
class SessionMetadata:
    """Metadata for a conversation session."""

    session_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMetadata":
        return cls(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            message_count=data["message_count"],
            title=data.get("title"),
        )


class HistoryManager:
    """Manages persistent conversation history."""

    def __init__(self, history_dir: Path | None = None) -> None:
        """
        Initialize the history manager.

        Args:
            history_dir: Directory to store history files
        """
        self.history_dir = history_dir or config.history_dir
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure the history directory exists."""
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.history_dir / f"{session_id}.json"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    async def create_session(self, memory: ConversationMemory) -> str:
        """
        Create a new session and save it.

        Args:
            memory: The conversation memory to save

        Returns:
            The new session ID
        """
        session_id = self._generate_session_id()
        await self.save_session(session_id, memory)
        return session_id

    async def save_session(
        self,
        session_id: str,
        memory: ConversationMemory,
        title: str | None = None,
    ) -> None:
        """
        Save a conversation session to disk.

        Args:
            session_id: Session identifier
            memory: Conversation memory to save
            title: Optional title for the session
        """
        try:
            # Generate title from first user message if not provided
            if title is None and memory.messages:
                for msg in memory.messages:
                    if msg.role.value == "user":
                        title = msg.content[:50] + ("..." if len(msg.content) > 50 else "")
                        break

            # Check if session exists to get created_at
            session_path = self._session_path(session_id)
            created_at = datetime.now()
            if session_path.exists():
                try:
                    existing = await self._load_file(session_path)
                    created_at = datetime.fromisoformat(
                        existing.get("metadata", {}).get("created_at", created_at.isoformat())
                    )
                except Exception:
                    pass

            metadata = SessionMetadata(
                session_id=session_id,
                created_at=created_at,
                updated_at=datetime.now(),
                message_count=len(memory),
                title=title,
            )

            data = {
                "metadata": metadata.to_dict(),
                "conversation": memory.to_dict(),
            }

            async with aiofiles.open(session_path, "w") as f:
                await f.write(json.dumps(data, indent=2))

            logger.debug(f"Saved session: {session_id}")

        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise HistoryError(f"Failed to save session: {e}")

    async def load_session(self, session_id: str) -> ConversationMemory:
        """
        Load a conversation session from disk.

        Args:
            session_id: Session identifier

        Returns:
            Loaded conversation memory
        """
        session_path = self._session_path(session_id)

        if not session_path.exists():
            raise HistoryError(f"Session not found: {session_id}")

        try:
            data = await self._load_file(session_path)
            return ConversationMemory.from_dict(data.get("conversation", {}))
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            raise HistoryError(f"Failed to load session: {e}")

    async def list_sessions(self) -> list[SessionMetadata]:
        """
        List all saved sessions.

        Returns:
            List of session metadata, sorted by updated_at descending
        """
        sessions = []

        for path in self.history_dir.glob("*.json"):
            try:
                data = await self._load_file(path)
                metadata = SessionMetadata.from_dict(data.get("metadata", {}))
                sessions.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to load session metadata from {path}: {e}")

        # Sort by updated_at, newest first
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return sessions

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        session_path = self._session_path(session_id)

        if not session_path.exists():
            return False

        try:
            await aiofiles.os.remove(session_path)
            logger.debug(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise HistoryError(f"Failed to delete session: {e}")

    async def cleanup_old_sessions(self, max_sessions: int | None = None) -> int:
        """
        Remove old sessions to stay within the limit.

        Args:
            max_sessions: Maximum number of sessions to keep

        Returns:
            Number of sessions deleted
        """
        max_sessions = max_sessions or config.max_history_sessions
        sessions = await self.list_sessions()

        if len(sessions) <= max_sessions:
            return 0

        # Delete oldest sessions
        deleted = 0
        for session in sessions[max_sessions:]:
            if await self.delete_session(session.session_id):
                deleted += 1

        return deleted

    async def _load_file(self, path: Path) -> dict[str, Any]:
        """Load JSON from a file."""
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            return json.loads(content)
