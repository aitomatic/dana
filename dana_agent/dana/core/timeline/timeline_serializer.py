"""
Timeline serializer mixin for CompressedTimeline.

Provides TimelineSerializerMixin with all persistence-related methods:
read_since, save, load_from_entries, and supporting private helpers.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from structlog import get_logger

from dana.core.timeline.native_message import (
    COMPRESSED_CONTEXT_KEY,
    NativeMessage,
)
from dana.core.timeline.timeline import TimelineEntry


if TYPE_CHECKING:
    from dana.core.timeline.compressed_timeline import CompressedTimeline

logger = get_logger()


class TimelineSerializerMixin:
    """
    Mixin providing persistence logic for CompressedTimeline.

    Expects the following attributes on self (provided by CompressedTimeline):
        _repository: repository instance or None
        _agent: BaseAgent or None
        _native_messages: list[NativeMessage]
        timeline: list[TimelineEntry]
        _timeline_entry_to_native_message: callable
        _native_message_to_timeline_entry: callable
    """

    def read_since(self: CompressedTimeline, checkpoint: int) -> Iterator[TimelineEntry]:
        """
        Read timeline entries since checkpoint, with compression-aware loading.

        This override ensures that when loading from repository, we leverage
        compressed context metadata to avoid loading unnecessary old entries.
        It also rebuilds _native_messages so that to_llm_messages() works
        correctly after loading a saved session.

        Args:
            checkpoint: Starting index for reading entries

        Yields:
            TimelineEntry objects since checkpoint
        """
        # First, get all entries using parent method
        all_entries = list(super().read_since(checkpoint))  # type: ignore[misc]

        # Find the first entry with compressed context (from the end)
        cutoff_idx = 0
        for i, entry in enumerate(reversed(all_entries)):
            if COMPRESSED_CONTEXT_KEY in entry.metadata:
                cutoff_idx = len(all_entries) - i - 1
                break

        # Get the entries we'll actually use
        result_entries = all_entries[cutoff_idx:]

        # Also try to load saved native_messages from the JSON file
        native_messages_loaded = self._try_load_native_messages_from_repository()

        if not native_messages_loaded:
            # No saved native_messages found — rebuild from entries
            self._native_messages = [self._timeline_entry_to_native_message(entry) for entry in result_entries]

        # Yield entries from the cutoff point
        for entry in result_entries:
            yield entry

    def _try_load_native_messages_from_repository(self: CompressedTimeline) -> bool:
        """
        Try to load saved native_messages from the repository JSON file.

        Returns:
            True if native_messages were loaded, False otherwise.
        """
        if self._repository is None or self._agent is None:
            return False

        session_id = getattr(self._agent, "_session_id", None)
        if session_id is None:
            return False

        if not hasattr(self._repository, "_events_path"):
            return False

        import json
        from pathlib import Path

        events_path = self._repository._events_path
        session_folder = Path(events_path) / session_id
        timeline_file = session_folder / "timeline.json"

        if not timeline_file.exists():
            return False

        try:
            with open(timeline_file) as f:
                timeline_data = json.load(f)

            native_data = timeline_data.get("native_messages")
            if not native_data:
                return False

            self._native_messages = [NativeMessage.from_dict(msg) for msg in native_data]
            logger.info(f"Loaded {len(self._native_messages)} native messages from repository")
            return True
        except Exception as e:
            logger.warning(f"Failed to load native messages from repository: {e}")
            return False

    def save(self: CompressedTimeline, session_id: str) -> None:
        """
        Save timeline for a session, including native messages.

        This override extends the parent save to also persist the native messages
        in the same JSON file. The native messages are stored in a separate
        "native_messages" key for backward compatibility.

        Ephemeral entries (like CONTEXT) are excluded from persistence.

        Args:
            session_id: Session identifier
        """
        if self._repository is None:
            raise ValueError("Cannot save timeline: repository is None. Initialize Timeline with repository or agent.")

        # Filter out ephemeral entries before saving
        persistent_entries = [e for e in self.timeline if not e.ephemeral]

        # Filter out ephemeral native messages (those corresponding to CONTEXT entries)
        persistent_native_messages = [
            msg for msg in self._native_messages if not (msg.role == "system" and msg.metadata.get("ephemeral", False))
        ]

        # Use the repository's save method for TimelineEntry
        self._repository.save(session_id, persistent_entries)

        # Now also save native messages to the same file
        # We need to access the repository's internal path to update the JSON
        if hasattr(self._repository, "_events_path"):
            import json
            from pathlib import Path

            events_path = self._repository._events_path
            session_folder = Path(events_path) / session_id
            timeline_file = session_folder / "timeline.json"

            if timeline_file.exists():
                # Read existing data and add native_messages
                with open(timeline_file) as f:
                    timeline_data = json.load(f)

                # Add native messages to the saved data
                timeline_data["native_messages"] = [msg.to_dict() for msg in persistent_native_messages]

                # Write back
                with open(timeline_file, "w") as f:
                    json.dump(timeline_data, f, indent=2)

        logger.info(
            f"Saved compressed timeline with {len(persistent_entries)} entries "
            f"and {len(persistent_native_messages)} native messages for session {session_id}"
        )

    def load_from_entries(
        self: CompressedTimeline,
        entries: list[TimelineEntry] | list[dict[str, Any]],
        native_messages: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Load timeline from entries, supporting both legacy and native message formats.

        This method handles loading from:
        1. Legacy format: list[TimelineEntry] - converted to native on load
        2. Native format: list[dict] with 'role' field - loaded as NativeMessage
        3. Mixed format: entries + optional native_messages list

        Format detection is via presence of 'role' field (native) vs 'type' field (legacy).

        Args:
            entries: List of TimelineEntry objects or dicts (legacy format)
            native_messages: Optional list of native message dicts (new format)
        """
        if not entries and not native_messages:
            self.timeline = []
            self._native_messages = []
            return

        # Check if entries are in native format (dicts with 'role' key) or legacy format (dicts with 'type' key)
        first_entry = entries[0] if entries else None

        if isinstance(first_entry, dict):
            # Check for native format indicator
            if "role" in first_entry and "type" not in first_entry:
                # Native format - load as NativeMessage directly
                self._load_from_native_format(entries)  # type: ignore[arg-type]
                return

        # Legacy format or TimelineEntry objects - use original loading logic
        # Convert dicts to TimelineEntry if needed
        timeline_entries: list[TimelineEntry] = []
        for entry in entries:
            if isinstance(entry, dict):
                timeline_entries.append(TimelineEntry.from_dict(entry))
            else:
                timeline_entries.append(entry)  # type: ignore[arg-type]

        # Check if we have native_messages separately provided
        if native_messages:
            # Load timeline entries using legacy logic
            self._load_timeline_entries_legacy(timeline_entries)
            # Load native messages directly
            self._native_messages = [NativeMessage.from_dict(msg) for msg in native_messages]
            logger.info(
                f"Loaded {len(self.timeline)} timeline entries with {len(self._native_messages)} native messages from separate storage"
            )
        else:
            # Pure legacy format - load entries and convert to native
            self._load_timeline_entries_legacy(timeline_entries)
            # Convert each entry to native message
            self._native_messages = [self._timeline_entry_to_native_message(entry) for entry in self.timeline]
            logger.info(f"Loaded and converted {len(self.timeline)} legacy timeline entries to native format")

    def _load_timeline_entries_legacy(self: CompressedTimeline, entries: list[TimelineEntry]) -> None:
        """
        Load timeline entries using the legacy compression-aware logic.

        This implements the original load_from_entries optimization:
        - Iterates through entries from most recent
        - When it finds an entry with compressed context metadata, stops there
        - Uses the compressed context to represent older history

        Args:
            entries: List of TimelineEntry objects to load
        """
        if not entries:
            self.timeline = []
            return

        # Look for entry with compressed context, starting from most recent
        # We want to keep entries from the one with compressed context onwards
        entries_to_load = []
        found_compressed = False

        for entry in reversed(entries):
            entries_to_load.insert(0, entry)
            if COMPRESSED_CONTEXT_KEY in entry.metadata:
                found_compressed = True
                break

        # If we found compressed context, we only need entries from that point
        # Otherwise, load all entries
        if found_compressed:
            self.timeline = entries_to_load
            logger.info(
                f"Loaded {len(entries_to_load)} entries with compressed context "
                f"(skipped {len(entries) - len(entries_to_load)} older entries)"
            )
        else:
            self.timeline = entries
            logger.info(f"Loaded all {len(entries)} entries (no compressed context found)")

    def _load_from_native_format(self: CompressedTimeline, native_data: list[dict[str, Any]]) -> None:
        """
        Load timeline from native message format.

        When loading native format, we:
        1. Load messages directly as NativeMessage
        2. Reconstruct TimelineEntry objects for backward compatibility

        Args:
            native_data: List of native message dicts
        """
        # Load native messages directly
        self._native_messages = []
        entries_to_load: list[NativeMessage] = []
        found_compressed = False

        # Look for message with compressed context, starting from most recent
        for msg_dict in reversed(native_data):
            msg = NativeMessage.from_dict(msg_dict)
            entries_to_load.insert(0, msg)
            if COMPRESSED_CONTEXT_KEY in msg.metadata:
                found_compressed = True
                break

        if found_compressed:
            self._native_messages = entries_to_load
            logger.info(
                f"Loaded {len(entries_to_load)} native messages with compressed context "
                f"(skipped {len(native_data) - len(entries_to_load)} older messages)"
            )
        else:
            self._native_messages = [NativeMessage.from_dict(d) for d in native_data]
            logger.info(f"Loaded all {len(native_data)} native messages (no compressed context found)")

        # Reconstruct TimelineEntry for backward compatibility
        self.timeline = [self._native_message_to_timeline_entry(msg) for msg in self._native_messages]

    def _native_message_to_timeline_entry(self: CompressedTimeline, msg: NativeMessage) -> TimelineEntry:
        """
        Convert a NativeMessage back to TimelineEntry for backward compatibility.

        Args:
            msg: NativeMessage to convert

        Returns:
            TimelineEntry representation
        """
        from dana.core.timeline.timeline import TimelineEntryType

        # Determine entry type from role and content
        entry_type: TimelineEntryType
        tool_calls: list[dict[str, Any]] | None = None
        tool_call_id: str | None = msg.tool_call_id

        if msg.role == "user":
            entry_type = TimelineEntryType.USER_MESSAGE
        elif msg.role == "system":
            # Check if it's a summary or context
            if msg.content.startswith("[SUMMARY]") or COMPRESSED_CONTEXT_KEY in msg.metadata:
                entry_type = TimelineEntryType.TIMELINE_SUMMARY
            else:
                entry_type = TimelineEntryType.CONTEXT
        elif msg.role == "tool":
            entry_type = TimelineEntryType.RESOURCE_RESULT
        elif msg.role == "assistant":
            if msg.tool_calls:
                entry_type = TimelineEntryType.TOOL_CALL
                # Convert NativeToolCall to dict format
                tool_calls = [tc.to_dict() for tc in msg.tool_calls]
            else:
                entry_type = TimelineEntryType.AGENT_RESPONSE
        else:
            entry_type = TimelineEntryType.AGENT_RESPONSE

        return TimelineEntry(
            entry_type=entry_type,
            content=msg.content,
            timestamp=msg.timestamp,
            metadata=msg.metadata.copy(),
            tool_call_id=tool_call_id,
            tool_calls=tool_calls,
        )
