"""
History Test Utilities.

Provides utilities for backing up and restoring history files during tests
to ensure tests don't affect the user's actual history.
"""

import shutil
import tempfile
from pathlib import Path


def get_tui_history_file_path() -> Path:
    """Get the path to the Dana TUI history file."""
    dana_dir = Path.home() / ".dana"
    return dana_dir / "history_tui.txt"


def get_repl_history_file_path() -> Path:
    """Get the path to the Dana REPL history file."""
    dana_dir = Path.home() / ".dana"
    return dana_dir / "history_repl.txt"


def get_agent_chat_history_file_path(agent_name: str) -> Path:
    """Get the path to an agent's chat history file."""
    dana_dir = Path.home() / ".dana"
    return dana_dir / "agents" / f"{agent_name}_chat_history.txt"


def backup_tui_history() -> Path | None:
    """
    Backup the current TUI history file to a temporary location.

    Returns:
        Path to the backup file, or None if no history file exists
    """
    history_file = get_tui_history_file_path()

    if not history_file.exists():
        return None

    # Create a temporary backup file
    backup_file = Path(tempfile.mktemp(suffix=".txt"))
    shutil.copy2(history_file, backup_file)

    return backup_file


def restore_tui_history(backup_file: Path | None) -> None:
    """
    Restore the TUI history file from backup.

    Args:
        backup_file: Path to the backup file, or None if no backup was created
    """
    if backup_file is None:
        return

    if not backup_file.exists():
        return

    history_file = get_tui_history_file_path()

    # Ensure the .dana directory exists
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Restore the history file
    shutil.copy2(backup_file, history_file)

    # Clean up the backup file
    backup_file.unlink()


def clear_tui_history_for_test() -> None:
    """Clear the TUI history file for testing purposes."""
    history_file = get_tui_history_file_path()

    # Ensure the .dana directory exists
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Create an empty history file
    history_file.write_text("", encoding="utf-8")


def backup_agent_chat_history(agent_name: str) -> Path | None:
    """
    Backup an agent's chat history file to a temporary location.

    Args:
        agent_name: Name of the agent

    Returns:
        Path to the backup file, or None if no history file exists
    """
    history_file = get_agent_chat_history_file_path(agent_name)

    if not history_file.exists():
        return None

    # Create a temporary backup file
    backup_file = Path(tempfile.mktemp(suffix=".txt"))
    shutil.copy2(history_file, backup_file)

    return backup_file


def restore_agent_chat_history(agent_name: str, backup_file: Path | None) -> None:
    """
    Restore an agent's chat history file from backup.

    Args:
        agent_name: Name of the agent
        backup_file: Path to the backup file, or None if no backup was created
    """
    if backup_file is None:
        return

    if not backup_file.exists():
        return

    history_file = get_agent_chat_history_file_path(agent_name)

    # Ensure the agents directory exists
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Restore the history file
    shutil.copy2(backup_file, history_file)

    # Clean up the backup file
    backup_file.unlink()


def clear_agent_chat_history_for_test(agent_name: str) -> None:
    """Clear an agent's chat history file for testing purposes."""
    history_file = get_agent_chat_history_file_path(agent_name)

    # Ensure the agents directory exists
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Create an empty history file
    history_file.write_text("", encoding="utf-8")


def delete_agent_chat_history(agent_name: str) -> None:
    """Delete an agent's chat history file completely."""
    history_file = get_agent_chat_history_file_path(agent_name)

    if history_file.exists():
        history_file.unlink()


# Legacy function names for backward compatibility
def backup_history() -> Path | None:
    """Legacy function - use backup_tui_history() instead."""
    return backup_tui_history()


def restore_history(backup_file: Path | None) -> None:
    """Legacy function - use restore_tui_history() instead."""
    restore_tui_history(backup_file)


def clear_history_for_test() -> None:
    """Legacy function - use clear_tui_history_for_test() instead."""
    clear_tui_history_for_test()


class HistoryBackup:
    """Context manager for backing up and restoring TUI history during tests."""

    def __init__(self):
        self.backup_file: Path | None = None

    def __enter__(self):
        """Backup TUI history before entering context."""
        self.backup_file = backup_tui_history()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore TUI history when exiting context."""
        restore_tui_history(self.backup_file)


class AgentChatHistoryBackup:
    """Context manager for backing up and restoring agent chat history during tests."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.backup_file: Path | None = None

    def __enter__(self):
        """Backup agent chat history before entering context."""
        self.backup_file = backup_agent_chat_history(self.agent_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore agent chat history when exiting context."""
        restore_agent_chat_history(self.agent_name, self.backup_file)
