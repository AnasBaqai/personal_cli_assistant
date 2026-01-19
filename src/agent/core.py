"""Core agent implementation with the main agent loop."""

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

from ..llm.base import LLMProvider, LLMResponse
from ..tools.base import ToolResult
from ..tools.dispatcher import ToolCall, ToolDispatcher
from ..utils.config import config
from ..utils.exceptions import LLMError, ToolError
from ..utils.logger import get_logger
from .memory import ConversationMemory
from .prompt import SYSTEM_PROMPT

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    """Response from the agent."""

    content: str
    tool_calls_made: list[str] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


class Agent:
    """
    Main agent that orchestrates the conversation loop.

    The agent loop:
    1. Send user message + history to LLM
    2. Check for tool calls in response
    3. If tool calls: execute tools, add results, loop back to step 1
    4. If no tool calls: return final response
    """

    def __init__(
        self,
        llm: LLMProvider,
        dispatcher: ToolDispatcher | None = None,
        memory: ConversationMemory | None = None,
        max_iterations: int | None = None,
    ) -> None:
        """
        Initialize the agent.

        Args:
            llm: LLM provider to use
            dispatcher: Tool dispatcher (creates default if not provided)
            memory: Conversation memory (creates default if not provided)
            max_iterations: Maximum tool call iterations per request
        """
        self.llm = llm
        self.dispatcher = dispatcher or ToolDispatcher()
        self.memory = memory or ConversationMemory()
        self.max_iterations = max_iterations or config.max_tool_iterations

        # Set system prompt
        self.memory.set_system_prompt(SYSTEM_PROMPT)

        # Callbacks for CLI integration
        self._on_tool_start: Callable[[str], None] | None = None
        self._on_tool_end: Callable[[str, ToolResult], None] | None = None
        self._on_thinking: Callable[[], None] | None = None

    def set_callbacks(
        self,
        on_tool_start: Callable[[str], None] | None = None,
        on_tool_end: Callable[[str, ToolResult], None] | None = None,
        on_thinking: Callable[[], None] | None = None,
    ) -> None:
        """Set callbacks for tool execution events."""
        self._on_tool_start = on_tool_start
        self._on_tool_end = on_tool_end
        self._on_thinking = on_thinking

    async def run(self, user_message: str) -> AgentResponse:
        """
        Process a user message and return the agent's response.

        This implements the main agent loop with tool calling support.

        Args:
            user_message: The user's input message

        Returns:
            AgentResponse with the final response and any tool calls made
        """
        # Add user message to memory
        self.memory.add_user_message(user_message)

        tool_calls_made: list[str] = []
        tool_results: list[ToolResult] = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Agent loop iteration {iteration}")

            if self._on_thinking:
                self._on_thinking()

            try:
                # Get LLM response
                response = await self.llm.chat(
                    messages=self.memory.get_messages(),
                    tools=self.dispatcher.get_tool_schemas(),
                )
            except LLMError as e:
                logger.error(f"LLM error: {e}")
                return AgentResponse(
                    content=f"Sorry, I encountered an error: {e}",
                    tool_calls_made=tool_calls_made,
                    tool_results=tool_results,
                )

            # Check if there are tool calls
            if response.has_tool_calls:
                # Add assistant message with tool calls FIRST (before tool results)
                self.memory.add_assistant_message(
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )

                # Process each tool call
                for tool_call_data in response.tool_calls:
                    tool_call = ToolCall.from_dict(tool_call_data)
                    tool_calls_made.append(tool_call.name)

                    logger.debug(f"Executing tool: {tool_call.name}")

                    if self._on_tool_start:
                        self._on_tool_start(tool_call.name)

                    try:
                        result = await self.dispatcher.execute(tool_call)
                    except ToolError as e:
                        result = ToolResult(success=False, error=str(e))

                    tool_results.append(result)

                    if self._on_tool_end:
                        self._on_tool_end(tool_call.name, result)

                    # Add tool result to memory (after assistant message)
                    tool_call_id = tool_call.id or f"call_{iteration}_{tool_call.name}"
                    self.memory.add_tool_result(
                        content=result.to_message(),
                        tool_call_id=tool_call_id,
                    )

                # Continue the loop to get the next response
                continue

            # No tool calls - we have the final response
            final_content = response.content or "I don't have a response."
            self.memory.add_assistant_message(final_content)

            return AgentResponse(
                content=final_content,
                tool_calls_made=tool_calls_made,
                tool_results=tool_results,
            )

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return AgentResponse(
            content="I apologize, but I've reached the maximum number of tool calls. Please try a simpler request.",
            tool_calls_made=tool_calls_made,
            tool_results=tool_results,
        )

    async def run_stream(
        self,
        user_message: str,
    ) -> AsyncIterator[str]:
        """
        Process a user message and stream the response.

        Note: Tool calls are handled non-streaming, only final response is streamed.

        Args:
            user_message: The user's input message

        Yields:
            Response chunks as they arrive
        """
        # First, handle any tool calls non-streaming
        self.memory.add_user_message(user_message)

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1

            if self._on_thinking:
                self._on_thinking()

            # Check for tool calls first (non-streaming)
            response = await self.llm.chat(
                messages=self.memory.get_messages(),
                tools=self.dispatcher.get_tool_schemas(),
            )

            if response.has_tool_calls:
                # Add assistant message with tool calls FIRST
                self.memory.add_assistant_message(
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )

                # Process tool calls
                for tool_call_data in response.tool_calls:
                    tool_call = ToolCall.from_dict(tool_call_data)

                    if self._on_tool_start:
                        self._on_tool_start(tool_call.name)

                    try:
                        result = await self.dispatcher.execute(tool_call)
                    except ToolError as e:
                        result = ToolResult(success=False, error=str(e))

                    if self._on_tool_end:
                        self._on_tool_end(tool_call.name, result)

                    tool_call_id = tool_call.id or f"call_{iteration}_{tool_call.name}"
                    self.memory.add_tool_result(
                        content=result.to_message(),
                        tool_call_id=tool_call_id,
                    )

                continue

            # No more tool calls - stream the final response
            full_response = ""
            async for chunk in self.llm.chat_stream(
                messages=self.memory.get_messages(),
                tools=None,  # No tools for final streaming response
            ):
                full_response += chunk
                yield chunk

            self.memory.add_assistant_message(full_response or "I don't have a response.")
            return

        yield "I apologize, but I've reached the maximum number of tool calls."

    def clear_memory(self) -> None:
        """Clear conversation memory."""
        self.memory.clear()

    def get_memory(self) -> ConversationMemory:
        """Get the conversation memory."""
        return self.memory

    def set_memory(self, memory: ConversationMemory) -> None:
        """Set the conversation memory (for loading from history)."""
        self.memory = memory
        if not self.memory.system_prompt:
            self.memory.set_system_prompt(SYSTEM_PROMPT)
