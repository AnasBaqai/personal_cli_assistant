"""Ollama LLM provider implementation."""

from typing import Any, AsyncIterator

import ollama
from ollama import AsyncClient

from ..utils.config import config
from ..utils.exceptions import LLMConnectionError, LLMResponseError
from ..utils.logger import get_logger
from .base import LLMProvider, LLMResponse, Message

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama LLM provider with function calling support."""

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
    ) -> None:
        """
        Initialize the Ollama provider.

        Args:
            model: Model name to use (default from config)
            host: Ollama host URL (default from config)
        """
        self.model = model or config.ollama_model
        self.host = host or config.ollama_host
        self._client: AsyncClient | None = None

    @property
    def client(self) -> AsyncClient:
        """Get or create the async client."""
        if self._client is None:
            self._client = AsyncClient(host=self.host)
        return self._client

    async def close(self) -> None:
        """Close the async client to prevent resource warnings."""
        if self._client is not None:
            # Clear reference to allow garbage collection
            self._client = None

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """
        Send a chat request to Ollama.

        Args:
            messages: Conversation history
            tools: Optional list of tool schemas

        Returns:
            LLMResponse with content and optional tool calls
        """
        try:
            # Convert messages to Ollama format
            ollama_messages = [msg.to_dict() for msg in messages]

            # Make the request
            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": ollama_messages,
            }

            if tools:
                kwargs["tools"] = tools

            logger.debug(f"Sending chat request to Ollama: model={self.model}")
            response = await self.client.chat(**kwargs)

            # Parse response - handle both dict and object formats
            if hasattr(response, 'message'):
                # New object format
                message = response.message
                content = message.content if message.content else ""
                tool_calls = message.tool_calls if hasattr(message, 'tool_calls') and message.tool_calls else []
                finish_reason = response.done_reason if hasattr(response, 'done_reason') else None
            else:
                # Old dict format
                message = response.get("message", {})
                content = message.get("content", "") or ""
                tool_calls = message.get("tool_calls", []) or []
                finish_reason = response.get("done_reason")

            logger.debug(
                f"Received response: content_len={len(content)}, "
                f"tool_calls={len(tool_calls)}"
            )

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
            )

        except ollama.ResponseError as e:
            logger.error(f"Ollama response error: {e}")
            raise LLMResponseError(f"Ollama error: {e}")
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            raise LLMConnectionError(f"Failed to connect to Ollama: {e}")

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream a chat response from Ollama.

        Args:
            messages: Conversation history
            tools: Optional list of tool schemas

        Yields:
            Response chunks as they arrive
        """
        try:
            ollama_messages = [msg.to_dict() for msg in messages]

            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": True,
            }

            if tools:
                kwargs["tools"] = tools

            logger.debug(f"Starting streaming chat with Ollama: model={self.model}")

            async for chunk in await self.client.chat(**kwargs):
                message = chunk.get("message", {})
                content = message.get("content", "")
                if content:
                    yield content

        except ollama.ResponseError as e:
            logger.error(f"Ollama streaming error: {e}")
            raise LLMResponseError(f"Ollama streaming error: {e}")
        except Exception as e:
            logger.error(f"Ollama connection error during streaming: {e}")
            raise LLMConnectionError(f"Failed to stream from Ollama: {e}")

    async def is_available(self) -> bool:
        """Check if Ollama is available and the model is loaded."""
        try:
            # Try to list models to verify connection
            response = await self.client.list()

            # Handle both old dict format and new object format
            if hasattr(response, 'models'):
                # New format: response.models is a list of model objects
                model_names = [m.model.split(":")[0] for m in response.models]
            else:
                # Old dict format
                model_names = [m.get("name", "").split(":")[0] for m in response.get("models", [])]

            # Check if our model is available
            model_base = self.model.split(":")[0]
            if model_base not in model_names:
                logger.warning(
                    f"Model '{self.model}' not found. Available: {model_names}"
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Ollama availability check failed: {e}")
            return False

    async def pull_model(self) -> bool:
        """Pull the configured model if not available."""
        try:
            logger.info(f"Pulling model: {self.model}")
            await self.client.pull(self.model)
            return True
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False
