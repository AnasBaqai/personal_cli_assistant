"""Rich CLI interface for the assistant."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ..tools.base import ToolResult
from .themes import Theme, default_theme


class CLIInterface:
    """Rich-based CLI interface for the assistant."""

    def __init__(self, theme: Theme | None = None) -> None:
        """
        Initialize the CLI interface.

        Args:
            theme: Color theme to use
        """
        self.console = Console()
        self.theme = theme or default_theme

    def print_welcome(self) -> None:
        """Print the welcome message."""
        welcome_text = """
# Personal CLI Assistant

Welcome! I'm your AI assistant with tool-calling capabilities.

**Available Tools:**
- `calculator` - Mathematical calculations
- `file_ops` - File system operations
- `weather` - Weather information
- `web_search` - Web search
- `system_info` - System information

**Commands:**
- `/help` - Show this help
- `/tools` - List available tools
- `/clear` - Clear conversation
- `/history` - View conversation history
- `/save` - Save conversation
- `/load <id>` - Load a conversation
- `/exit` or `/quit` - Exit

Type your message and press Enter to chat!
"""
        self.console.print(Markdown(welcome_text))
        self.console.print()

    def print_message(self, role: str, content: str) -> None:
        """
        Print a chat message.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
        """
        if role == "user":
            self.console.print(
                Text("You: ", style=f"bold {self.theme.user_color}"),
                end="",
            )
            self.console.print(content)
        elif role == "assistant":
            self.console.print(
                Text("Assistant: ", style=f"bold {self.theme.assistant_color}"),
            )
            # Render markdown for assistant responses
            self.console.print(Markdown(content))
        elif role == "system":
            self.console.print(
                Text(content, style=self.theme.system_color),
            )
        self.console.print()

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self.console.print(
            Text(f"Error: {message}", style=self.theme.error_color)
        )

    def print_tool_start(self, tool_name: str) -> None:
        """Print tool execution start."""
        self.console.print(
            Text(f"  ⚡ Using tool: ", style=self.theme.muted_color),
            Text(tool_name, style=f"bold {self.theme.tool_name_color}"),
        )

    def print_tool_result(self, tool_name: str, result: ToolResult) -> None:
        """Print tool execution result."""
        if result.success:
            style = self.theme.tool_success_color
            icon = "✓"
        else:
            style = self.theme.tool_error_color
            icon = "✗"

        self.console.print(
            Text(f"  {icon} {tool_name}: ", style=f"{style}"),
            Text(
                result.to_message()[:100] + ("..." if len(result.to_message()) > 100 else ""),
                style=self.theme.muted_color,
            ),
        )

    def print_tools_list(self, tools: list[str]) -> None:
        """Print list of available tools."""
        table = Table(title="Available Tools")
        table.add_column("Tool", style=self.theme.tool_name_color)
        table.add_column("Description")

        tool_descriptions = {
            "calculator": "Perform mathematical calculations",
            "file_ops": "List, read files and directories",
            "weather": "Get weather information for a city",
            "web_search": "Search the web",
            "system_info": "Get system information",
        }

        for tool in tools:
            desc = tool_descriptions.get(tool, "No description")
            table.add_row(tool, desc)

        self.console.print(table)

    def print_history_list(self, sessions: list) -> None:
        """Print list of saved sessions."""
        if not sessions:
            self.console.print(
                Text("No saved conversations found.", style=self.theme.muted_color)
            )
            return

        table = Table(title="Saved Conversations")
        table.add_column("ID", style=self.theme.tool_name_color)
        table.add_column("Title")
        table.add_column("Messages")
        table.add_column("Last Updated")

        for session in sessions[:10]:  # Show last 10
            table.add_row(
                session.session_id,
                session.title or "(untitled)",
                str(session.message_count),
                session.updated_at.strftime("%Y-%m-%d %H:%M"),
            )

        self.console.print(table)
        self.console.print(
            Text(
                "\nUse /load <id> to load a conversation",
                style=self.theme.muted_color,
            )
        )

    def get_input(self, prompt: str = "You") -> str:
        """
        Get input from the user.

        Args:
            prompt: Prompt text to display

        Returns:
            User input string
        """
        return Prompt.ask(Text(prompt, style=self.theme.prompt_color))

    def create_spinner(self, message: str = "Thinking...") -> Progress:
        """
        Create a spinner for long operations.

        Args:
            message: Message to display with spinner

        Returns:
            Progress context manager
        """
        return Progress(
            SpinnerColumn(self.theme.spinner_style),
            TextColumn(f"[{self.theme.muted_color}]{message}"),
            console=self.console,
            transient=True,
        )

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        self.console.clear()

    def print_panel(self, content: str, title: str = "") -> None:
        """Print content in a panel."""
        self.console.print(
            Panel(
                Markdown(content),
                title=title,
                border_style=self.theme.header_color,
            )
        )

    def confirm(self, message: str) -> bool:
        """
        Ask for confirmation.

        Args:
            message: Confirmation message

        Returns:
            True if confirmed, False otherwise
        """
        response = Prompt.ask(
            Text(f"{message} [y/n]", style=self.theme.prompt_color),
            default="n",
        )
        return response.lower() in ("y", "yes")
