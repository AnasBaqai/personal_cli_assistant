"""Color themes and styling for the CLI interface."""

from dataclasses import dataclass


@dataclass
class Theme:
    """Color theme for the CLI interface."""

    # Message colors
    user_color: str = "cyan"
    assistant_color: str = "green"
    system_color: str = "yellow"
    error_color: str = "red"

    # Tool colors
    tool_name_color: str = "magenta"
    tool_success_color: str = "green"
    tool_error_color: str = "red"

    # UI colors
    prompt_color: str = "bold cyan"
    header_color: str = "bold blue"
    muted_color: str = "dim"

    # Spinner
    spinner_style: str = "dots"


# Default theme
default_theme = Theme()

# Alternative themes
dark_theme = Theme(
    user_color="bright_cyan",
    assistant_color="bright_green",
    system_color="bright_yellow",
    error_color="bright_red",
    tool_name_color="bright_magenta",
)

minimal_theme = Theme(
    user_color="white",
    assistant_color="white",
    system_color="dim white",
    error_color="red",
    tool_name_color="white",
    prompt_color="bold white",
    header_color="bold white",
)
