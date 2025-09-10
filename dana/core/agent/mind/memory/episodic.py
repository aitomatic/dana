"""
Episodic memory for storing and recalling experiences.
"""

from datetime import datetime
from typing import Any
import json
from pathlib import Path


class EpisodicMemory:
    """Episodic memory for past experiences and problem-solving episodes."""

    def __init__(self, storage_dir: str | None = None):
        """Initialize episodic memory.

        Args:
            storage_dir: Directory for persistent storage
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path("~/.dana/memory/episodic").expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._episodes: list[dict[str, Any]] = []
        self._index: dict[str, list[int]] = {}  # Tag/category to episode indices
        self._load_episodes()

    def store_experience(self, identifier: str, experience: Any, **metadata) -> None:
        """Store a new experience/episode.

        Args:
            identifier: Experience identifier
            experience: The experience data
            **metadata: Additional metadata (tags, context, outcome, etc.)
        """
        episode = {
            "id": identifier,
            "timestamp": datetime.now().isoformat(),
            "experience": experience,
            "metadata": metadata,
        }

        self._episodes.append(episode)
        episode_idx = len(self._episodes) - 1

        # Update indices
        if "tags" in metadata:
            for tag in metadata["tags"]:
                if tag not in self._index:
                    self._index[tag] = []
                self._index[tag].append(episode_idx)

        # Persist if we've accumulated enough episodes
        if len(self._episodes) % 10 == 0:
            self._save_episodes()

    def recall_similar(self, query: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Recall similar experiences based on query and context.

        Args:
            query: Query string
            context: Current context for similarity matching

        Returns:
            List of similar experiences
        """
        similar = []
        query_lower = query.lower()

        # Simple similarity based on tags and metadata
        for episode in self._episodes:
            score = 0.0

            # Check if query appears in experience
            if query_lower in str(episode["experience"]).lower():
                score += 0.5

            # Check metadata matches
            metadata = episode["metadata"]
            if "problem_type" in metadata and "problem_type" in context:
                if metadata["problem_type"] == context["problem_type"]:
                    score += 0.3

            if "tags" in metadata:
                for tag in metadata["tags"]:
                    if query_lower in tag.lower():
                        score += 0.2
                        break

            # Include if score is high enough
            if score > 0.3:
                similar.append(
                    {
                        "experience": episode["experience"],
                        "metadata": metadata,
                        "similarity_score": score,
                    }
                )

        # Sort by similarity score
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar[:5]  # Return top 5

    def has_similar(self, query: str, context: dict[str, Any]) -> bool:
        """Check if there are similar experiences.

        Args:
            query: Query string
            context: Current context

        Returns:
            True if similar experiences exist
        """
        return len(self.recall_similar(query, context)) > 0

    def get_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Get episodes by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of episodes with that tag
        """
        if tag not in self._index:
            return []

        episodes = []
        for idx in self._index[tag]:
            if idx < len(self._episodes):
                episodes.append(self._episodes[idx])

        return episodes

    def get_recent(self, n: int = 10) -> list[dict[str, Any]]:
        """Get recent episodes.

        Args:
            n: Number of episodes to retrieve

        Returns:
            List of recent episodes
        """
        return self._episodes[-n:] if self._episodes else []

    def count(self) -> int:
        """Get number of stored episodes.

        Returns:
            Number of episodes
        """
        return len(self._episodes)

    def _save_episodes(self) -> None:
        """Save episodes to persistent storage."""
        episodes_file = self.storage_dir / "episodes.json"

        try:
            with open(episodes_file, "w") as f:
                json.dump(
                    {
                        "episodes": self._episodes,
                        "index": self._index,
                    },
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            print(f"Error saving episodic memory: {e}")

    def _load_episodes(self) -> None:
        """Load episodes from persistent storage."""
        episodes_file = self.storage_dir / "episodes.json"

        if episodes_file.exists():
            try:
                with open(episodes_file) as f:
                    data = json.load(f)
                    self._episodes = data.get("episodes", [])
                    self._index = data.get("index", {})
            except Exception as e:
                print(f"Error loading episodic memory: {e}")
                self._episodes = []
                self._index = {}
