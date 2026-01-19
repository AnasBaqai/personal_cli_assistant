"""Base tool class and registry for the CLI assistant."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from a tool execution."""

    success: bool
    data: Any = None
    error: str | None = None

    def to_message(self) -> str:
        """Convert result to a message string for the LLM."""
        if self.success:
            return str(self.data) if self.data is not None else "Operation completed successfully."
        return f"Error: {self.error}"


@dataclass
class ToolSchema:
    """JSON Schema definition for a tool."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_ollama_format(self) -> dict[str, Any]:
        """Convert to Ollama's tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Tool(ABC):
    """Abstract base class for all tools."""

    name: str
    description: str

    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """Return the JSON schema for this tool."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given parameters."""
        pass


@dataclass
class ToolRegistry:
    """Registry for managing available tools."""

    _tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_all_schemas(self) -> list[dict[str, Any]]:
        """Get schemas for all registered tools in Ollama format."""
        return [tool.get_schema().to_ollama_format() for tool in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


# Global tool registry instance
tool_registry = ToolRegistry()
