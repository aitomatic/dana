"""
Long-term persistent memory for knowledge storage and retrieval.

LTMemory stores memories in a markdown file and uses RLM (Recursive Language Model)
pattern to query large memory stores that don't fit in context.
"""

import re
from datetime import datetime
from pathlib import Path

from dana.common.resource.rlm_resource import RLMResource


class LTMemory:
    """Long-term persistent memory.

    Stores memories in a human-readable markdown format and uses RLM
    for semantic querying of large memory stores.
    """

    def __init__(
        self,
        path: str = "./memories/",
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4-20250514",
    ):
        """
        Initialize LTMemory.

        Args:
            path: Directory path for memory storage
            llm_provider: LLM provider for RLM queries
            llm_model: LLM model for RLM queries
        """
        self.path = Path(path)
        self.memories_file = self.path / "memories.md"

        # Create directory if missing
        self.path.mkdir(parents=True, exist_ok=True)

        # Create empty memories file if missing
        if not self.memories_file.exists():
            self.memories_file.write_text("")

        # Initialize RLM for querying
        self._rlm = RLMResource(
            file=str(self.memories_file),
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

    def store(self, memory: dict) -> None:
        """
        Persist a memory to the markdown file.

        Args:
            memory: Dictionary with fields:
                - type: str (lesson, episode, fact, pattern)
                - content: str
                - context: str (optional)
                - timestamp: str (optional, auto-generated if missing)
        """
        # Auto-generate timestamp if not provided
        timestamp = memory.get("timestamp") or datetime.now().isoformat()
        memory_type = memory.get("type", "note")
        context = memory.get("context", "")
        content = memory.get("content", "")

        # Format entry
        entry = f"\n## Memory [{timestamp}]\n"
        entry += f"- **Type**: {memory_type}\n"
        if context:
            entry += f"- **Context**: {context}\n"
        entry += f"- **Content**: {content}\n"
        entry += "\n---\n"

        # Append to file
        with open(self.memories_file, "a") as f:
            f.write(entry)

    def query(self, question: str) -> str:
        """
        Query memories using RLM pattern.

        Args:
            question: Question to answer using stored memories

        Returns:
            Relevant memories as text
        """
        # Check if there are any memories
        if self.count() == 0:
            return "No memories stored yet."

        return self._rlm.query(question)

    def count(self) -> int:
        """
        Count number of stored memories.

        Returns:
            Number of memory entries
        """
        content = self.memories_file.read_text()
        if not content.strip():
            return 0
        # Count ## Memory headers
        return len(re.findall(r"^## Memory \[", content, re.MULTILINE))
