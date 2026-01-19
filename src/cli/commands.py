"""CLI command handlers."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Awaitable

from ..agent.history import HistoryManager
from ..agent.memory import ConversationMemory
from ..tools.dispatcher import ToolDispatcher
from .interface import CLIInterface


class CommandType(Enum):
    """Types of CLI commands."""

    HELP = auto()
    TOOLS = auto()
    CLEAR = auto()
    HISTORY = auto()
    SAVE = auto()
    LOAD = auto()
    EXIT = auto()
    UNKNOWN = auto()
    NOT_COMMAND = auto()


@dataclass
class CommandResult:
    """Result of command processing."""

    command_type: CommandType
    should_exit: bool = False
    args: list[str] | None = None


class CommandHandler:
    """Handles CLI slash commands."""

    COMMANDS = {
        "/help": CommandType.HELP,
        "/h": CommandType.HELP,
        "/?": CommandType.HELP,
        "/tools": CommandType.TOOLS,
        "/clear": CommandType.CLEAR,
        "/history": CommandType.HISTORY,
        "/save": CommandType.SAVE,
        "/load": CommandType.LOAD,
        "/exit": CommandType.EXIT,
        "/quit": CommandType.EXIT,
        "/q": CommandType.EXIT,
    }

    def __init__(
        self,
        cli: CLIInterface,
        dispatcher: ToolDispatcher,
        history_manager: HistoryManager,
    ) -> None:
        """
        Initialize the command handler.

        Args:
            cli: CLI interface for output
            dispatcher: Tool dispatcher for tool info
            history_manager: History manager for session operations
        """
        self.cli = cli
        self.dispatcher = dispatcher
        self.history_manager = history_manager

    def parse_command(self, input_text: str) -> CommandResult:
        """
        Parse user input and identify if it's a command.

        Args:
            input_text: Raw user input

        Returns:
            CommandResult with command type and args
        """
        stripped = input_text.strip()

        if not stripped.startswith("/"):
            return CommandResult(command_type=CommandType.NOT_COMMAND)

        parts = stripped.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []

        command_type = self.COMMANDS.get(command, CommandType.UNKNOWN)

        return CommandResult(
            command_type=command_type,
            should_exit=(command_type == CommandType.EXIT),
            args=args if args else None,
        )

    async def handle(
        self,
        command_result: CommandResult,
        memory: ConversationMemory,
        session_id: str | None = None,
    ) -> tuple[ConversationMemory, str | None]:
        """
        Handle a parsed command.

        Args:
            command_result: Parsed command result
            memory: Current conversation memory
            session_id: Current session ID (if any)

        Returns:
            Tuple of (possibly updated memory, possibly updated session_id)
        """
        match command_result.command_type:
            case CommandType.HELP:
                self._handle_help()

            case CommandType.TOOLS:
                self._handle_tools()

            case CommandType.CLEAR:
                memory = self._handle_clear(memory)

            case CommandType.HISTORY:
                await self._handle_history()

            case CommandType.SAVE:
                session_id = await self._handle_save(memory, session_id)

            case CommandType.LOAD:
                if command_result.args:
                    loaded_memory = await self._handle_load(command_result.args[0])
                    if loaded_memory:
                        memory = loaded_memory
                        session_id = command_result.args[0]
                else:
                    self.cli.print_error("Usage: /load <session_id>")

            case CommandType.EXIT:
                pass  # Handled by should_exit flag

            case CommandType.UNKNOWN:
                self.cli.print_error(
                    f"Unknown command. Type /help for available commands."
                )

        return memory, session_id

    def _handle_help(self) -> None:
        """Display help information."""
        self.cli.print_welcome()

    def _handle_tools(self) -> None:
        """Display available tools."""
        tools = self.dispatcher.get_available_tools()
        self.cli.print_tools_list(tools)

    def _handle_clear(self, memory: ConversationMemory) -> ConversationMemory:
        """Clear conversation memory."""
        memory.clear()
        self.cli.print_message("system", "Conversation cleared.")
        return memory

    async def _handle_history(self) -> None:
        """Display conversation history."""
        sessions = await self.history_manager.list_sessions()
        self.cli.print_history_list(sessions)

    async def _handle_save(
        self,
        memory: ConversationMemory,
        session_id: str | None,
    ) -> str:
        """
        Save current conversation.

        Returns:
            Session ID
        """
        if not memory.messages:
            self.cli.print_error("Nothing to save - conversation is empty.")
            return session_id or ""

        if session_id:
            await self.history_manager.save_session(session_id, memory)
            self.cli.print_message("system", f"Conversation saved: {session_id}")
        else:
            session_id = await self.history_manager.create_session(memory)
            self.cli.print_message("system", f"Conversation saved as: {session_id}")

        return session_id

    async def _handle_load(self, session_id: str) -> ConversationMemory | None:
        """
        Load a conversation.

        Returns:
            Loaded memory or None if failed
        """
        try:
            memory = await self.history_manager.load_session(session_id)
            self.cli.print_message("system", f"Loaded conversation: {session_id}")

            # Show conversation summary
            user_msgs = [m for m in memory.messages if m.role.value == "user"]
            self.cli.print_message(
                "system",
                f"  ({len(user_msgs)} user messages)",
            )

            return memory
        except Exception as e:
            self.cli.print_error(f"Failed to load session: {e}")
            return None
