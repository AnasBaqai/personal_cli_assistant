# Personal CLI Assistant

A powerful command-line AI assistant with function calling capabilities. Built with Python, Ollama (local LLM), and Rich for beautiful terminal output.

## Features

- **Function Calling / Tool Use** - AI executes real tools to perform actions
- **5 Built-in Tools**:
  - `calculator` - Math operations (arithmetic, trigonometry, logarithms)
  - `file_ops` - File system operations (list, read, get info)
  - `weather` - Real-time weather data (OpenWeatherMap API)
  - `web_search` - Web search via DuckDuckGo
  - `system_info` - System metrics (CPU, memory, disk, datetime)
- **Tool Chaining** - AI chains multiple tools to answer complex questions
- **Conversation History** - Save and load conversation sessions
- **Beautiful CLI** - Rich terminal output with markdown rendering
- **Fully Async** - Modern async/await architecture
- **Docker Support** - Run anywhere with Docker

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/personal_cli_assistant.git
cd personal_cli_assistant

# Start Ollama on your machine (must be running)
OLLAMA_HOST=0.0.0.0 ollama serve

# Pull the model (in another terminal)
ollama pull llama3.1

# Run with Docker
docker-compose run --rm assistant
```

### Option 2: Local Installation

```bash
# Clone and install
git clone https://github.com/yourusername/personal_cli_assistant.git
cd personal_cli_assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .

# Start Ollama
ollama serve

# Pull the model (in another terminal)
ollama pull llama3.1

# Run the assistant
assistant
# Or: python -m src.main
```

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Required for local installation |
| Ollama | Latest | Local LLM runtime |
| Docker | Latest | Optional, for containerized deployment |

### Installing Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

## Usage Examples

### Basic Conversation

```
You: What's 15% of 250?
Assistant: ⚡ Using tool: calculator
✓ calculator: 37.5
The result is 37.5

You: What's the weather like in London?
Assistant: ⚡ Using tool: weather
✓ weather: London: 12°C, partly cloudy...
The current weather in London is 12°C with partly cloudy skies.
```

### Tool Chaining

```
You: What's the square root of the current temperature in Paris?
Assistant: ⚡ Using tool: weather
✓ weather: Paris: 18°C, clear sky...
⚡ Using tool: calculator
✓ calculator: 4.24264...
The temperature in Paris is 18°C, and its square root is approximately 4.24.
```

### File Operations

```
You: List the files in my current directory
Assistant: ⚡ Using tool: file_ops
✓ file_ops: Found 12 files...
Here are the files in your current directory:
- README.md
- pyproject.toml
- src/
...
```

## CLI Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `/help` | `/h`, `/?` | Show help and available tools |
| `/tools` | - | List all available tools with descriptions |
| `/clear` | - | Clear conversation memory |
| `/history` | - | View saved conversation sessions |
| `/save` | - | Save current conversation |
| `/load <id>` | - | Load a previous conversation |
| `/exit` | `/quit`, `/q` | Exit the assistant |

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Weather API (optional - get free key at openweathermap.org)
OPENWEATHERMAP_API_KEY=your_api_key_here

# History Settings
HISTORY_DIR=~/.assistant_history
MAX_HISTORY_SESSIONS=50
```

### Docker Configuration

The `docker-compose.yml` automatically configures:
- Connection to host Ollama via `host.docker.internal`
- Persistent conversation history via Docker volume
- Environment variable passthrough from `.env`

## Project Structure

```
personal_cli_assistant/
├── src/
│   ├── agent/
│   │   ├── core.py       # Main agent loop
│   │   ├── memory.py     # Conversation memory
│   │   ├── history.py    # Session persistence
│   │   └── prompt.py     # System prompts
│   ├── llm/
│   │   ├── base.py       # LLM provider interface
│   │   └── ollama.py     # Ollama implementation
│   ├── tools/
│   │   ├── base.py       # Tool base class & registry
│   │   ├── schemas.py    # JSON schemas for tools
│   │   ├── dispatcher.py # Tool execution dispatcher
│   │   ├── calculator.py # Calculator tool
│   │   ├── file_ops.py   # File operations tool
│   │   ├── weather.py    # Weather tool
│   │   ├── web_search.py # Web search tool
│   │   └── system_info.py# System info tool
│   ├── cli/
│   │   ├── interface.py  # Rich CLI interface
│   │   ├── commands.py   # Slash command handlers
│   │   └── themes.py     # Color themes
│   ├── utils/
│   │   ├── config.py     # Configuration management
│   │   ├── logger.py     # Logging setup
│   │   └── exceptions.py # Custom exceptions
│   └── main.py           # Entry point
├── tests/                # Test files
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose config
├── pyproject.toml        # Python project config
└── README.md
```

## Architecture

### Agent Loop

The assistant follows a reasoning loop:

```
User Input
    ↓
┌─────────────────────────────────────┐
│           Agent Loop                │
│  ┌─────────────────────────────┐    │
│  │ 1. Send to LLM              │    │
│  │ 2. Check for tool calls     │←───┤
│  │ 3. Execute tools            │    │
│  │ 4. Add results to context   │────┘
│  │ 5. Repeat until done        │
│  └─────────────────────────────┘
└─────────────────────────────────────┘
    ↓
Final Response
```

### Tool Schema Example

Tools are defined with JSON schemas:

```python
CALCULATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate"
        }
    },
    "required": ["expression"]
}
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Adding New Tools

1. Create a new file in `src/tools/`
2. Define the JSON schema in `src/tools/schemas.py`
3. Implement the `Tool` class with `get_schema()` and `execute()` methods
4. Register the tool with `tool_registry.register()`

Example:

```python
# src/tools/my_tool.py
from .base import Tool, ToolResult, ToolSchema, tool_registry
from .schemas import MY_TOOL_SCHEMA

class MyTool(Tool):
    name = "my_tool"
    description = "Description of what my tool does"

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=MY_TOOL_SCHEMA,
        )

    async def execute(self, **kwargs) -> ToolResult:
        # Tool implementation
        return ToolResult(success=True, data="Result")

tool_registry.register(MyTool())
```

## Troubleshooting

### "Could not connect to Ollama"

```bash
# Make sure Ollama is running
ollama serve

# For Docker, Ollama must listen on all interfaces
OLLAMA_HOST=0.0.0.0 ollama serve
```

### "Model not found"

```bash
# Pull the required model
ollama pull llama3.1

# List available models
ollama list
```

### "No results found" (Web Search)

DuckDuckGo may rate-limit requests. The tool automatically retries 3 times. If issues persist, try again after a few seconds.

### Docker can't connect to Ollama

Ensure Ollama is running with:
```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

The Docker container connects via `host.docker.internal:11434`.

## Key Concepts Demonstrated

This project showcases modern AI engineering patterns:

1. **Function/Tool Calling** - Structured JSON schemas for LLM tool use
2. **Agentic Loops** - Iterative reasoning with tool execution
3. **Error Recovery** - Graceful handling of failures in agentic workflows
4. **Async Python** - Modern async/await patterns throughout
5. **Clean Architecture** - Separation of concerns (LLM, Tools, CLI, Agent)
6. **Docker Deployment** - Containerized application with proper networking

## License

MIT License - feel free to use this project for learning and building your own AI assistants.

---

Built with Python, Ollama, and Rich
