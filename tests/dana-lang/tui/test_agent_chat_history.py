"""
Agent Chat History Test Example.

This demonstrates how to properly backup and restore agent chat history
during tests to avoid affecting the user's actual agent chat history.
"""

import pytest

from dana.apps.tui import DanaTUI
from dana.apps.tui.ui.prompt_textarea import PromptStyleTextArea

from .history_test_utils import (
    AgentChatHistoryBackup,
    HistoryBackup,
    clear_agent_chat_history_for_test,
    clear_tui_history_for_test,
    delete_agent_chat_history,
)


@pytest.mark.asyncio
async def test_agent_chat_with_history_backup():
    """Test agent chat functionality with proper history backup/restore."""
    # Use an esoteric agent name to avoid conflicts
    test_agent_name = "test_agent_xkcd_42_esoteric"

    # Backup both TUI history and agent chat history
    with HistoryBackup(), AgentChatHistoryBackup(test_agent_name):
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear TUI history for testing
            clear_tui_history_for_test()
            prompt_widget._load_history()

            # Clear agent chat history for testing
            clear_agent_chat_history_for_test(test_agent_name)

            # Add some test commands to TUI history
            test_commands = [f"agent {test_agent_name}", "Hello, this is a test message", "What is 2 + 2?", "Thank you for your help"]

            for command in test_commands:
                prompt_widget.add_to_history(command)

            # Test that TUI history works correctly
            # Verify the history was loaded correctly
            assert len(prompt_widget._history) == 4
            assert prompt_widget._history[-1] == "Thank you for your help"
            assert prompt_widget._history[0] == f"agent {test_agent_name}"

            # Test that we can find agent commands in history
            agent_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("agent")]
            assert len(agent_commands) == 1
            assert agent_commands[0] == f"agent {test_agent_name}"

        # After the test, the history files will be automatically restored
        # and the test agent's chat history will be cleaned up

    # Clean up the test agent completely
    delete_agent_chat_history(test_agent_name)


@pytest.mark.asyncio
async def test_multiple_agents_with_history_backup():
    """Test multiple agents with proper history backup/restore."""
    # Use multiple esoteric agent names
    test_agents = ["test_agent_alpha_12345", "test_agent_beta_67890", "test_agent_gamma_abcdef"]

    # Create backup contexts for all agents
    backup_contexts = [AgentChatHistoryBackup(agent_name) for agent_name in test_agents]

    # Use contextlib.ExitStack to manage multiple contexts
    from contextlib import ExitStack

    with HistoryBackup(), ExitStack() as stack:
        # Enter all agent backup contexts
        for context in backup_contexts:
            stack.enter_context(context)

        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear TUI history for testing
            clear_tui_history_for_test()
            prompt_widget._load_history()

            # Clear all agent chat histories for testing
            for agent_name in test_agents:
                clear_agent_chat_history_for_test(agent_name)

            # Test switching between agents
            for agent_name in test_agents:
                # Add agent command to history
                agent_command = f"agent {agent_name}"
                prompt_widget.add_to_history(agent_command)

                # Verify the agent command was added to history
                assert agent_command in prompt_widget._history

        # All histories will be automatically restored

    # Clean up all test agents
    for agent_name in test_agents:
        delete_agent_chat_history(agent_name)


if __name__ == "__main__":
    # Run the tests directly
    import asyncio

    async def run_agent_tests():
        print("Testing agent chat history backup/restore...")
        await test_agent_chat_with_history_backup()
        print("✓ Single agent test passed")

        print("\nTesting multiple agents with history backup...")
        await test_multiple_agents_with_history_backup()
        print("✓ Multiple agents test passed")

        print("\n🎉 All agent chat history tests completed successfully!")

    asyncio.run(run_agent_tests())
