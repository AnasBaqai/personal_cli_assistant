"""Custom exceptions for the CLI assistant."""


class AssistantError(Exception):
    """Base exception for all assistant errors."""

    pass


class LLMError(AssistantError):
    """Error related to LLM operations."""

    pass


class LLMConnectionError(LLMError):
    """Failed to connect to the LLM provider."""

    pass


class LLMResponseError(LLMError):
    """Invalid or unexpected response from LLM."""

    pass


class ToolError(AssistantError):
    """Base error for tool-related issues."""

    pass


class ToolNotFoundError(ToolError):
    """Requested tool does not exist."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool not found: {tool_name}")


class ToolExecutionError(ToolError):
    """Error during tool execution."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Error executing {tool_name}: {message}")


class ToolValidationError(ToolError):
    """Invalid parameters passed to tool."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Validation error for {tool_name}: {message}")


class HistoryError(AssistantError):
    """Error related to history operations."""

    pass
