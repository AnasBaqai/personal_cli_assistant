"""Configuration management for the CLI assistant."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Weather API
    openweathermap_api_key: str | None = None

    # History settings
    history_dir: Path = field(default_factory=lambda: Path.home() / ".assistant_history")
    max_history_sessions: int = 50

    # Agent settings
    max_tool_iterations: int = 10
    request_timeout: float = 60.0

    def __post_init__(self) -> None:
        """Load configuration from environment variables."""
        load_dotenv(override=False)  # Don't override existing env vars (e.g., from Docker)

        self.ollama_host = os.getenv("OLLAMA_HOST", self.ollama_host)
        self.ollama_model = os.getenv("OLLAMA_MODEL", self.ollama_model)
        self.openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")

        history_dir = os.getenv("HISTORY_DIR")
        if history_dir:
            self.history_dir = Path(history_dir)

        max_sessions = os.getenv("MAX_HISTORY_SESSIONS")
        if max_sessions:
            self.max_history_sessions = int(max_sessions)

    def ensure_history_dir(self) -> Path:
        """Create history directory if it doesn't exist."""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        return self.history_dir


# Global configuration instance
config = Config()
