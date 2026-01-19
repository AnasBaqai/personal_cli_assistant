"""In-memory conversation history management."""

from dataclasses import dataclass, field
from typing import Any

from ..llm.base import Message, MessageRole


@dataclass
class ConversationMemory:
    """Manages conversation history in memory."""

    messages: list[Message] = field(default_factory=list)
    system_prompt: str | None = None
    max_messages: int = 100  # Prevent unbounded growth

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt for the conversation."""
        self.system_prompt = prompt

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.messages.append(Message.user(content))
        self._trim_if_needed()

    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add an assistant message to the conversation."""
        self.messages.append(Message.assistant(content, tool_calls))
        self._trim_if_needed()

    def add_tool_result(self, content: str, tool_call_id: str) -> None:
        """Add a tool result to the conversation."""
        self.messages.append(Message.tool_result(content, tool_call_id))
        self._trim_if_needed()

    def get_messages(self) -> list[Message]:
        """Get all messages including system prompt."""
        messages = []
        if self.system_prompt:
            messages.append(Message.system(self.system_prompt))
        messages.extend(self.messages)
        return messages

    def get_last_message(self) -> Message | None:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None

    def clear(self) -> None:
        """Clear all messages (keeps system prompt)."""
        self.messages.clear()

    def _trim_if_needed(self) -> None:
        """Remove oldest messages if we exceed max_messages."""
        if len(self.messages) > self.max_messages:
            # Keep the most recent messages
            excess = len(self.messages) - self.max_messages
            self.messages = self.messages[excess:]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "system_prompt": self.system_prompt,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "tool_calls": self._serialize_tool_calls(msg.tool_calls),
                    "tool_call_id": msg.tool_call_id,
                }
                for msg in self.messages
            ],
        }

    @staticmethod
    def _serialize_tool_calls(tool_calls: list | None) -> list | None:
        """Convert tool_calls to JSON-serializable format."""
        if not tool_calls:
            return None
        serialized = []
        for tc in tool_calls:
            if hasattr(tc, 'function'):
                # Ollama object format
                serialized.append({
                    "function": {
                        "name": tc.function.name if hasattr(tc.function, 'name') else tc.function.get("name", ""),
                        "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else tc.function.get("arguments", {}),
                    }
                })
            elif isinstance(tc, dict):
                # Already a dict
                serialized.append(tc)
            else:
                # Unknown format, try to convert
                serialized.append({"raw": str(tc)})
        return serialized

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationMemory":
        """Create from dictionary."""
        memory = cls()
        memory.system_prompt = data.get("system_prompt")
        for msg_data in data.get("messages", []):
            role = MessageRole(msg_data["role"])
            memory.messages.append(
                Message(
                    role=role,
                    content=msg_data["content"],
                    tool_calls=msg_data.get("tool_calls"),
                    tool_call_id=msg_data.get("tool_call_id"),
                )
            )
        return memory

    def __len__(self) -> int:
        return len(self.messages)
