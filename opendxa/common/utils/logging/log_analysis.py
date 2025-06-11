"""Log analysis utilities for the DXA system.

This module provides tools for analyzing LLM interaction logs, including:
- Loading and parsing interaction logs
- Finding similar prompts using fuzzy matching
- Analyzing interaction patterns and trends

Basic Usage:
    # Create analyzer
    analyzer = LLMInteractionAnalyzer("path/to/logs")

    # Find similar prompts
    similar = analyzer.find_similar_prompts(
        "How do I implement a binary search?",
        threshold=0.8
    )

    # Load all interactions
    df = analyzer.load_interactions()

Note: This module requires pandas for data manipulation.
"""

import json
import logging
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class LLMInteractionAnalyzer:
    """Analyze LLM interactions from logs.

    This class provides methods to analyze LLM interaction logs, including
    loading log data, finding similar prompts, and extracting patterns.

    Attributes:
        log_dir (Path): Directory containing log files
        log_file (Path): Path to the main log file

    Example:
        >>> analyzer = LLMInteractionAnalyzer("logs")
        >>> similar = analyzer.find_similar_prompts("How to sort a list?")
        >>> for match in similar:
        ...     print(f"{match['similarity']:.2f}: {match['prompt']}")
    """

    def __init__(self, log_dir: str):
        """Initialize analyzer with log directory.

        Args:
            log_dir: Path to directory containing log files
        """
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "dxa.log"

    def load_interactions(self) -> pd.DataFrame:
        """Load interactions from log file into a pandas DataFrame.

        Reads the log file and parses each line as a JSON object containing
        interaction data. Invalid or malformed entries are skipped.

        Returns:
            DataFrame containing interaction data with columns:
            - timestamp: Interaction timestamp
            - interaction_type: Type of interaction (e.g., completion, error)
            - prompt: User prompt/input
            - response: AI response content and metadata
            - metadata: Additional interaction metadata
            - success: Whether interaction was successful

        Example:
            >>> df = analyzer.load_interactions()
            >>> print(f"Total interactions: {len(df)}")
            >>> print(f"Success rate: {df['success'].mean():.2%}")
        """
        if not self.log_file.exists():
            logger.warning("Log file not found: %s", self.log_file)
            return pd.DataFrame()

        interactions = []
        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # Extract interaction data from log entry
                    interaction = {
                        "timestamp": datetime.fromisoformat(data.get("timestamp", "")),
                        "interaction_type": data.get("interaction_type"),
                        "prompt": data.get("content"),
                        "response": data.get("response", {}),
                        "metadata": data.get("metadata", {}),
                        "success": data.get("success", True),
                    }
                    interactions.append(interaction)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug("Skipping malformed log entry: %s", e)
                    continue

        return pd.DataFrame(interactions)

    def find_similar_prompts(self, prompt: str, threshold: float = 0.8) -> list[dict]:
        """Find similar prompts in the logs using fuzzy matching.

        Uses sequence matching to find prompts that are similar to the input prompt.
        Similarity is calculated using difflib's SequenceMatcher and ranges from 0 to 1,
        where 1 indicates an exact match.

        Args:
            prompt: The prompt to find matches for
            threshold: Minimum similarity score (0-1) for matches, defaults to 0.8

        Returns:
            List of dictionaries containing similar prompts, sorted by similarity:
            - timestamp: When the similar prompt was used
            - prompt: The similar prompt text
            - similarity: Similarity score (0-1)
            - response: The AI's response to that prompt

        Example:
            >>> matches = analyzer.find_similar_prompts(
            ...     "How do I sort a list?",
            ...     threshold=0.7
            ... )
            >>> for match in matches:
            ...     print(f"{match['similarity']:.2f}: {match['prompt']}")
        """
        df = self.load_interactions()
        similar_prompts = []

        for _, row in df.iterrows():
            if "prompt" in row:
                similarity = SequenceMatcher(None, prompt.lower(), row["prompt"].lower()).ratio()

                if similarity >= threshold:
                    similar_prompts.append(
                        {
                            "timestamp": row["timestamp"],
                            "prompt": row["prompt"],
                            "similarity": similarity,
                            "response": row.get("response", {}).get("content"),
                        }
                    )

        return sorted(similar_prompts, key=lambda x: x["similarity"], reverse=True)

    def get_token_usage_over_time(self) -> pd.DataFrame:
        """Get token usage over time."""
        df = self.load_interactions()
        return df.groupby("timestamp").sum()


class LogAnalyzer:
    """Analyze log content."""

    def analyze_logs(self, logs: list[str]) -> dict[str, Any]:
        """Analyze log content."""
        return {"total_lines": len(logs), "error_count": sum(1 for log in logs if "ERROR" in log)}
