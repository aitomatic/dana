"""Tests for ephemeral runtime context in Timeline."""

from dana.core.timeline.timeline import Timeline, TimelineEntry, TimelineEntryType
from dana.core.runtime.base import AgentRuntime
from dana.core.runtime.default import DefaultRuntime


class TestTimelineContext:
    """Tests for Timeline.set_context and ephemeral entries."""

    def test_set_context_adds_context_entry(self):
        """Context entry is added to timeline."""
        timeline = Timeline()

        timeline.set_context(
            {
                "timestamp": "2024-01-15 10:30:00",
                "timezone": "PST",
                "user": "testuser",
            }
        )

        assert len(timeline.timeline) == 1
        entry = timeline.timeline[0]
        assert entry.entry_type == TimelineEntryType.CONTEXT
        assert entry.ephemeral is True
        # timestamp is excluded from content for prompt caching
        assert "PST" in entry.content
        assert "testuser" in entry.content

    def test_set_context_replaces_existing_context(self):
        """Calling set_context again replaces the previous context entry."""
        timeline = Timeline()

        timeline.set_context({"timestamp": "first", "user": "user1"})
        timeline.set_context({"timestamp": "second", "user": "user2"})

        # Should still have only one CONTEXT entry
        context_entries = [e for e in timeline.timeline if e.entry_type == TimelineEntryType.CONTEXT]
        assert len(context_entries) == 1
        # timestamp excluded from content; verify latest user is present
        assert "user2" in context_entries[0].content

    def test_set_context_does_not_remove_other_entries(self):
        """set_context only removes CONTEXT entries, not others."""
        timeline = Timeline()

        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Hello",
            )
        )
        timeline.set_context({"timestamp": "now", "user": "test"})
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.AGENT_RESPONSE,
                content="Hi there",
            )
        )

        assert len(timeline.timeline) == 3
        assert timeline.timeline[0].entry_type == TimelineEntryType.CONTEXT
        assert timeline.timeline[1].entry_type == TimelineEntryType.USER_MESSAGE
        assert timeline.timeline[2].entry_type == TimelineEntryType.AGENT_RESPONSE

    def test_context_entry_is_inserted_at_beginning(self):
        """Context entry is always at the beginning of the timeline."""
        timeline = Timeline()

        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="First message",
            )
        )
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Second message",
            )
        )
        timeline.set_context({"timestamp": "now"})

        assert timeline.timeline[0].entry_type == TimelineEntryType.CONTEXT

    def test_context_entry_has_system_role(self):
        """Context entry maps to system role in LLM messages."""
        timeline = Timeline()
        timeline.set_context({"timestamp": "now", "user": "test"})

        messages = timeline.to_llm_messages()

        assert len(messages) == 1
        assert messages[0].role == "system"


class TestEphemeralEntries:
    """Tests for ephemeral entry persistence behavior."""

    def test_ephemeral_entries_excluded_from_save(self):
        """Ephemeral entries are not included when saving."""
        # Create a mock repository to capture save calls
        saved_entries = []

        class MockRepository:
            def save(self, session_id, entries):
                saved_entries.extend(entries)

        timeline = Timeline()
        timeline._repository = MockRepository()

        # Add regular and ephemeral entries
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Regular message",
            )
        )
        timeline.set_context({"timestamp": "now"})
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.AGENT_RESPONSE,
                content="Response",
            )
        )

        timeline.save("test-session")

        # Only non-ephemeral entries should be saved
        assert len(saved_entries) == 2
        entry_types = [e.entry_type for e in saved_entries]
        assert TimelineEntryType.CONTEXT not in entry_types
        assert TimelineEntryType.USER_MESSAGE in entry_types
        assert TimelineEntryType.AGENT_RESPONSE in entry_types


class TestDefaultRuntimeContext:
    """Tests for DefaultRuntime context injection."""

    def test_get_runtime_context_returns_expected_keys(self):
        """_get_runtime_context returns date, timezone, and user."""
        runtime = DefaultRuntime()

        context = runtime._get_runtime_context()

        assert "date" in context
        assert "timezone" in context
        assert "user" in context

    def test_get_runtime_context_date_format(self):
        """Date is in expected format (date-only for prompt caching)."""
        runtime = DefaultRuntime()

        context = runtime._get_runtime_context()

        # Should be YYYY-MM-DD format (date-only for prompt caching)
        import re

        assert re.match(r"\d{4}-\d{2}-\d{2}$", context["date"])

    def test_build_prompt_injects_context(self):
        """build_prompt injects runtime context into timeline."""
        from dana.core.agent.star_agent import STARAgent

        class MockLLM:
            pass

        agent = STARAgent(
            agent_type="test",
            auto_register=False,
            enable_web_search=False,
            enable_skills=False,
            enable_code_execution=False,
        )
        runtime = DefaultRuntime(llm=MockLLM())  # Pass mock LLM to avoid API key requirement
        timeline = Timeline(agent=agent)
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Hello",
                is_latest_user_message=True,
            )
        )

        runtime.build_prompt(agent, timeline)

        # Timeline should now have a CONTEXT entry
        context_entries = [e for e in timeline.timeline if e.entry_type == TimelineEntryType.CONTEXT]
        assert len(context_entries) == 1
        assert context_entries[0].ephemeral is True

    def test_ip_location_is_cached(self):
        """IP geolocation result is cached at class level."""

        class MockLLM:
            pass

        # Reset cache
        AgentRuntime._cached_location = None

        runtime1 = DefaultRuntime(llm=MockLLM())  # Pass mock LLM to avoid API key requirement
        runtime2 = DefaultRuntime(llm=MockLLM())  # Pass mock LLM to avoid API key requirement

        # First call populates cache
        loc1 = runtime1._get_ip_location()

        # Second call (even from different instance) uses cache
        loc2 = runtime2._get_ip_location()

        assert loc1 == loc2
        assert AgentRuntime._cached_location is not None

    def test_context_includes_location_when_available(self):
        """Context includes location field when IP geolocation succeeds."""
        # Set a mock cached location
        AgentRuntime._cached_location = {"location": "Test City, Test State, Test Country"}

        runtime = DefaultRuntime()
        context = runtime._get_runtime_context()

        assert "location" in context
        assert context["location"] == "Test City, Test State, Test Country"

    def test_context_formats_location(self):
        """Timeline formats location in context display."""
        timeline = Timeline()
        timeline.set_context(
            {
                "timestamp": "2024-01-15 10:00:00",
                "timezone": "PST",
                "location": "San Francisco, California, US",
                "user": "testuser",
            }
        )

        content = timeline.timeline[0].content
        assert "Location: San Francisco, California, US" in content
