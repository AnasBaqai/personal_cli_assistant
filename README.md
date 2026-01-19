# Personal CLI Assistant

A command-line AI assistant with function calling capabilities, built with Python, Ollama, and Rich.

## Features

- **Function Calling**: The AI can execute tools to perform real actions
- **5 Built-in Tools**:
  - `calculator` - Mathematical calculations (basic arithmetic, trigonometry, logarithms)
  - `file_ops` - File system operations (list, read, info, create directories)
  - `weather` - Current weather information (requires OpenWeatherMap API key)
  - `web_search` - Web search via DuckDuckGo
  - `system_info` - System information (CPU, memory, disk, datetime)
- **Tool Chaining**: AI can use multiple tools in sequence to answer complex questions
- **Conversation History**: Save and load conversation sessions
- **Beautiful CLI**: Rich terminal output with markdown rendering and syntax highlighting
- **Async Architecture**: Built with async/await for better performance

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Ollama** - Local LLM runtime

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Set up Ollama
ollama pull llama3.1
ollama serve
```

## Usage

```bash
# Start the assistant
python -m src.main

# Or use the installed command
assistant
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help information |
| `/tools` | List available tools |
| `/clear` | Clear conversation |
| `/history` | View saved conversations |
| `/save` | Save current conversation |
| `/load <id>` | Load a conversation |
| `/exit` | Exit the assistant |

## Project Structure

```
personal_cli_assistant/
├── src/
│   ├── agent/      # Agent core and memory
│   ├── llm/        # LLM providers
│   ├── tools/      # Tool implementations
│   ├── cli/        # CLI interface
│   └── utils/      # Utilities
├── tests/          # Test files
└── pyproject.toml  # Project config
```

## Key Concepts Demonstrated

1. **Function/Tool Calling**: JSON schema definitions for tools, structured outputs
2. **Agent Loop**: reason → call tool → observe → repeat
3. **Error Handling**: Graceful error recovery in agentic workflows
4. **Async Python**: Modern async/await patterns throughout
5. **CLI UX**: Rich library for beautiful terminal interfaces

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model to use | `llama3.1` |
| `OPENWEATHERMAP_API_KEY` | Weather API key | (none) |

## License

MIT
