"""Tool dispatcher for routing and executing tool calls."""

import json
from dataclasses import dataclass
from typing import Any

from ..utils.exceptions import ToolExecutionError, ToolNotFoundError
from ..utils.logger import get_logger
from .base import ToolResult, tool_registry

# Import tools to register them
from . import calculator  # noqa: F401
from . import file_ops  # noqa: F401
from . import weather  # noqa: F401
from . import web_search  # noqa: F401
from . import system_info  # noqa: F401

logger = get_logger(__name__)


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""

    name: str
    arguments: dict[str, Any]
    id: str | None = None

    @classmethod
    def from_ollama_response(cls, tool_call: dict) -> "ToolCall":
        """Create ToolCall from Ollama's response format."""
        function = tool_call.get("function", {})
        return cls(
            name=function.get("name", ""),
            arguments=function.get("arguments", {}),
            id=tool_call.get("id"),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ToolCall":
        """Create ToolCall from a dictionary."""
        # Handle both direct format and nested function format
        if "function" in data:
            return cls.from_ollama_response(data)
        return cls(
            name=data.get("name", ""),
            arguments=data.get("arguments", {}),
            id=data.get("id"),
        )


class ToolDispatcher:
    """Dispatches tool calls to the appropriate tool handlers."""

    def __init__(self) -> None:
        self.registry = tool_registry

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return self.registry.list_tools()

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get all tool schemas in Ollama format."""
        return self.registry.get_all_schemas()

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: The tool call to execute

        Returns:
            ToolResult with success/failure and data/error

        Raises:
            ToolNotFoundError: If the tool doesn't exist
            ToolExecutionError: If execution fails unexpectedly
        """
        tool_name = tool_call.name
        arguments = tool_call.arguments

        logger.debug(f"Executing tool: {tool_name} with args: {arguments}")

        # Get the tool
        tool = self.registry.get(tool_name)
        if tool is None:
            available = ", ".join(self.get_available_tools())
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found. Available tools: {available}"
            )

        try:
            # Handle arguments that might be a JSON string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    pass

            # Execute the tool
            result = await tool.execute(**arguments)
            logger.debug(f"Tool {tool_name} result: success={result.success}")
            return result

        except Exception as e:
            logger.error(f"Tool {tool_name} execution error: {e}")
            raise ToolExecutionError(tool_name, str(e))

    async def execute_multiple(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """
        Execute multiple tool calls in sequence.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of results in the same order as the calls
        """
        results = []
        for tool_call in tool_calls:
            try:
                result = await self.execute(tool_call)
                results.append(result)
            except (ToolNotFoundError, ToolExecutionError) as e:
                results.append(ToolResult(success=False, error=str(e)))
        return results
