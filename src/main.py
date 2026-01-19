"""Main entry point for the Personal CLI Assistant."""

import asyncio
import sys

from .agent.core import Agent
from .agent.history import HistoryManager
from .agent.memory import ConversationMemory
from .cli.commands import CommandHandler, CommandType
from .cli.interface import CLIInterface
from .llm.ollama import OllamaProvider
from .tools.dispatcher import ToolDispatcher
from .utils.logger import get_logger

logger = get_logger(__name__)


async def check_ollama_available(llm: OllamaProvider, cli: CLIInterface) -> bool:
    """Check if Ollama is available and the model is ready."""
    with cli.create_spinner("Checking Ollama connection..."):
        if await llm.is_available():
            return True

    cli.print_error(
        "Could not connect to Ollama or model not found.\n"
        "Please ensure:\n"
        "  1. Ollama is installed (https://ollama.ai)\n"
        "  2. Ollama is running (ollama serve)\n"
        "  3. The model is pulled (ollama pull llama3.1)"
    )
    return False


async def run_assistant() -> None:
    """Main async function to run the assistant."""
    # Initialize components
    cli = CLIInterface()
    llm = OllamaProvider()
    dispatcher = ToolDispatcher()
    history_manager = HistoryManager()
    memory = ConversationMemory()

    # Cleanup function
    async def cleanup() -> None:
        await llm.close()

    # Check Ollama availability
    if not await check_ollama_available(llm, cli):
        await cleanup()
        return

    # Initialize agent with callbacks
    agent = Agent(llm=llm, dispatcher=dispatcher, memory=memory)
    agent.set_callbacks(
        on_tool_start=cli.print_tool_start,
        on_tool_end=cli.print_tool_result,
    )

    # Initialize command handler
    command_handler = CommandHandler(
        cli=cli,
        dispatcher=dispatcher,
        history_manager=history_manager,
    )

    # Print welcome message
    cli.print_welcome()

    # Current session tracking
    session_id: str | None = None

    # Main loop
    while True:
        try:
            # Get user input
            user_input = cli.get_input()

            if not user_input.strip():
                continue

            # Check for commands
            command_result = command_handler.parse_command(user_input)

            if command_result.command_type != CommandType.NOT_COMMAND:
                if command_result.should_exit:
                    # Ask to save before exit if there's conversation
                    if memory.messages and cli.confirm("Save conversation before exit?"):
                        await command_handler._handle_save(memory, session_id)
                    cli.print_message("system", "Goodbye!")
                    await cleanup()
                    break

                # Handle the command
                memory, session_id = await command_handler.handle(
                    command_result,
                    memory,
                    session_id,
                )
                # Update agent memory if it changed
                agent.set_memory(memory)
                continue

            # Regular message - process with agent
            with cli.create_spinner("Thinking..."):
                response = await agent.run(user_input)

            # Print response
            cli.print_message("assistant", response.content)

            # Auto-save periodically (every 5 messages)
            if len(memory.messages) % 10 == 0 and len(memory.messages) > 0:
                if session_id:
                    await history_manager.save_session(session_id, memory)
                else:
                    session_id = await history_manager.create_session(memory)

        except KeyboardInterrupt:
            cli.console.print()  # New line after ^C
            if cli.confirm("Exit?"):
                if memory.messages and cli.confirm("Save conversation?"):
                    await command_handler._handle_save(memory, session_id)
                cli.print_message("system", "Goodbye!")
                await cleanup()
                break
        except Exception as e:
            logger.exception("Unexpected error")
            cli.print_error(f"Unexpected error: {e}")


def main() -> None:
    """Entry point for the CLI assistant."""
    try:
        asyncio.run(run_assistant())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
