"""
History Backup/Restore Test.

This test verifies that the history backup and restore functionality works correctly
without requiring the full Textual app context.
"""

from .history_test_utils import (
    AgentChatHistoryBackup,
    HistoryBackup,
    clear_agent_chat_history_for_test,
    clear_tui_history_for_test,
    delete_agent_chat_history,
    get_agent_chat_history_file_path,
    get_tui_history_file_path,
)


def test_tui_history_backup_restore():
    """Test that TUI history backup and restore works correctly."""
    history_file = get_tui_history_file_path()

    # Create some test content
    test_content = "print('hello')\nx = 42\ndef func(): pass"

    # Ensure the directory exists and write test content
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(test_content, encoding="utf-8")

    # Verify the file exists and has content
    assert history_file.exists()
    assert history_file.read_text(encoding="utf-8") == test_content

    # Test backup and restore
    with HistoryBackup():
        # Clear the history
        clear_tui_history_for_test()

        # Verify it's cleared
        assert history_file.read_text(encoding="utf-8") == ""

        # Add some new content
        new_content = "new_command\nanother_command"
        history_file.write_text(new_content, encoding="utf-8")
        assert history_file.read_text(encoding="utf-8") == new_content

    # After the context exits, the original content should be restored
    assert history_file.read_text(encoding="utf-8") == test_content


def test_agent_chat_history_backup_restore():
    """Test that agent chat history backup and restore works correctly."""
    test_agent_name = "test_agent_backup_restore_123"
    history_file = get_agent_chat_history_file_path(test_agent_name)

    # Create some test content
    test_content = "Hello, this is a test message\nWhat is 2 + 2?\nThank you for your help"

    # Ensure the directory exists and write test content
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(test_content, encoding="utf-8")

    # Verify the file exists and has content
    assert history_file.exists()
    assert history_file.read_text(encoding="utf-8") == test_content

    # Test backup and restore
    with AgentChatHistoryBackup(test_agent_name):
        # Clear the history
        clear_agent_chat_history_for_test(test_agent_name)

        # Verify it's cleared
        assert history_file.read_text(encoding="utf-8") == ""

        # Add some new content
        new_content = "new_agent_message\nanother_agent_message"
        history_file.write_text(new_content, encoding="utf-8")
        assert history_file.read_text(encoding="utf-8") == new_content

    # After the context exits, the original content should be restored
    assert history_file.read_text(encoding="utf-8") == test_content

    # Clean up the test agent
    delete_agent_chat_history(test_agent_name)


def test_multiple_agents_backup_restore():
    """Test that multiple agent chat histories can be backed up and restored."""
    test_agents = ["test_agent_alpha_456", "test_agent_beta_789", "test_agent_gamma_abc"]

    # Create test content for each agent
    agent_contents = {}
    for agent_name in test_agents:
        history_file = get_agent_chat_history_file_path(agent_name)
        test_content = f"Test content for {agent_name}\nAnother message for {agent_name}"

        # Ensure the directory exists and write test content
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(test_content, encoding="utf-8")

        # Verify the file exists and has content
        assert history_file.exists()
        assert history_file.read_text(encoding="utf-8") == test_content
        agent_contents[agent_name] = test_content

    # Test backup and restore for all agents
    from contextlib import ExitStack

    with HistoryBackup(), ExitStack() as stack:
        # Enter all agent backup contexts
        for agent_name in test_agents:
            stack.enter_context(AgentChatHistoryBackup(agent_name))

        # Clear all histories
        for agent_name in test_agents:
            clear_agent_chat_history_for_test(agent_name)
            history_file = get_agent_chat_history_file_path(agent_name)
            assert history_file.read_text(encoding="utf-8") == ""

        # Add new content to all agents
        for agent_name in test_agents:
            history_file = get_agent_chat_history_file_path(agent_name)
            new_content = f"New content for {agent_name}"
            history_file.write_text(new_content, encoding="utf-8")
            assert history_file.read_text(encoding="utf-8") == new_content

    # After the context exits, all original content should be restored
    for agent_name in test_agents:
        history_file = get_agent_chat_history_file_path(agent_name)
        assert history_file.read_text(encoding="utf-8") == agent_contents[agent_name]

    # Clean up all test agents
    for agent_name in test_agents:
        delete_agent_chat_history(agent_name)


def test_no_existing_history():
    """Test that backup/restore works when no history files exist."""
    # Test TUI history
    with HistoryBackup():
        # This should work even if no history file exists
        clear_tui_history_for_test()
        history_file = get_tui_history_file_path()
        assert history_file.read_text(encoding="utf-8") == ""

    # Test agent history
    test_agent_name = "test_agent_nonexistent_xyz"
    with AgentChatHistoryBackup(test_agent_name):
        # This should work even if no agent history file exists
        clear_agent_chat_history_for_test(test_agent_name)
        history_file = get_agent_chat_history_file_path(test_agent_name)
        assert history_file.read_text(encoding="utf-8") == ""

    # Clean up
    delete_agent_chat_history(test_agent_name)


if __name__ == "__main__":
    # Run the tests directly
    print("Testing TUI history backup/restore...")
    test_tui_history_backup_restore()
    print("✓ TUI history backup/restore test passed")

    print("\nTesting agent chat history backup/restore...")
    test_agent_chat_history_backup_restore()
    print("✓ Agent chat history backup/restore test passed")

    print("\nTesting multiple agents backup/restore...")
    test_multiple_agents_backup_restore()
    print("✓ Multiple agents backup/restore test passed")

    print("\nTesting no existing history...")
    test_no_existing_history()
    print("✓ No existing history test passed")

    print("\n🎉 All history backup/restore tests completed successfully!")
