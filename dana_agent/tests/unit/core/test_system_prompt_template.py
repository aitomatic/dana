"""Tests for native system_prompt_template support.

Covers:
- AgentRuntime base no-op
- DefaultRuntime stores template
- CodecRuntimeBase deferred and immediate application
- STARAgent constructor forwarding
- Legacy _get_prompt_api path still works
"""

from unittest.mock import MagicMock

from dana.core.runtime.base import AgentRuntime
from dana.core.runtime.default import DefaultRuntime


class TestSetSystemPromptTemplateBase:
    """Test set_system_prompt_template on AgentRuntime hierarchy."""

    def test_base_runtime_noop(self):
        """AgentRuntime base method is a no-op (doesn't raise)."""
        rt = AgentRuntime.__new__(AgentRuntime)
        rt.set_system_prompt_template("anything")  # should not raise

    def test_default_runtime_noop(self):
        """DefaultRuntime inherits base no-op (doesn't raise)."""
        rt = DefaultRuntime()
        rt.set_system_prompt_template("custom template")  # should not raise


class TestCodecRuntimeSetTemplate:
    """Test set_system_prompt_template on CodecRuntimeBase."""

    def _make_codec_runtime(self):
        # CodecRuntimeBase is abstract; use AnthropicRuntime as concrete subclass
        from dana.core.runtime.anthropic import AnthropicRuntime

        return AnthropicRuntime()

    def test_set_before_prompt_api_created(self):
        """Template stored for deferred application when _get_prompt_api called later."""
        rt = self._make_codec_runtime()
        assert rt._prompt_api is None

        rt.set_system_prompt_template("CUSTOM")
        assert rt._system_prompt_template_override == "CUSTOM"
        assert rt._prompt_api is None  # not created yet

    def test_deferred_application_on_get_prompt_api(self):
        """Stored template applied when _get_prompt_api is first called."""
        rt = self._make_codec_runtime()
        rt.set_system_prompt_template("DEFERRED_TEMPLATE")

        # Create a minimal mock agent
        agent = MagicMock()
        agent.object_id = "test-agent"
        agent._identity_override = None
        agent.__class__.__doc__ = "Test agent"
        agent._resources = []
        agent._workflows = []
        agent._agents = []

        prompt_api = rt._get_prompt_api(agent)
        assert prompt_api._template_system_prompt == "DEFERRED_TEMPLATE"

    def test_set_after_prompt_api_created_invalidates_cache(self):
        """Template applied immediately and cache invalidated on existing prompt_api."""
        rt = self._make_codec_runtime()

        agent = MagicMock()
        agent.object_id = "test-agent"
        agent._identity_override = None
        agent.__class__.__doc__ = "Test agent"
        agent._resources = []
        agent._workflows = []
        agent._agents = []

        # Create prompt_api first
        prompt_api = rt._get_prompt_api(agent)
        # Access system_prompt to populate cache
        _ = prompt_api.system_prompt
        assert prompt_api._system_prompt is not None

        # Now override — should invalidate cache
        rt.set_system_prompt_template("NEW_TEMPLATE")
        assert prompt_api._template_system_prompt == "NEW_TEMPLATE"
        assert prompt_api._system_prompt is None  # cache cleared


class TestLocalPromptAPISetTemplate:
    """Test LocalPromptAPI.set_system_prompt_template directly."""

    def test_sets_template_and_clears_cache(self):
        from dana.core.knowledge.prompts.codecs import CSXMLCodec
        from dana.core.prompt.prompt_api import LocalPromptAPI

        agent = MagicMock()
        agent.object_id = "test"
        agent._identity_override = None
        agent.__class__.__doc__ = "Test"
        agent._resources = []
        agent._workflows = []
        agent._agents = []

        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, provider="anthropic")
        # Populate cache
        _ = api.system_prompt
        assert api._system_prompt is not None

        api.set_system_prompt_template("REPLACED")
        assert api._template_system_prompt == "REPLACED"
        assert api._system_prompt is None
        assert api._template is None


class TestSystemPromptTemplateViaConstructor:
    """Test system_prompt_template param flows through STARAgent."""

    def test_star_agent_forwards_template_to_runtime(self):
        """STARAgent passes system_prompt_template to runtime.set_system_prompt_template."""
        mock_runtime = MagicMock()
        from dana.core.agent.star_agent import STARAgent

        STARAgent(
            agent_type="test",
            runtime=mock_runtime,
            system_prompt_template="MY_TEMPLATE",
            auto_register=False,
            enable_skills=False,
            enable_web_search=False,
            enable_code_execution=False,
            enable_assistant=False,
        )
        mock_runtime.set_system_prompt_template.assert_called_once_with("MY_TEMPLATE")

    def test_star_agent_none_template_no_call(self):
        """STARAgent with None template doesn't call set_system_prompt_template."""
        mock_runtime = MagicMock()
        from dana.core.agent.star_agent import STARAgent

        STARAgent(
            agent_type="test",
            runtime=mock_runtime,
            auto_register=False,
            enable_skills=False,
            enable_web_search=False,
            enable_code_execution=False,
            enable_assistant=False,
        )
        mock_runtime.set_system_prompt_template.assert_not_called()

    def test_identity_override_and_template_are_independent(self):
        """Both can be set independently without conflict."""
        mock_runtime = MagicMock()
        from dana.core.agent.star_agent import STARAgent

        agent = STARAgent(
            agent_type="test",
            runtime=mock_runtime,
            identity_override="IDENTITY",
            system_prompt_template="TEMPLATE",
            auto_register=False,
            enable_skills=False,
            enable_web_search=False,
            enable_code_execution=False,
            enable_assistant=False,
        )
        assert agent._identity_override == "IDENTITY"
        assert agent._system_prompt_template == "TEMPLATE"
        mock_runtime.set_system_prompt_template.assert_called_once_with("TEMPLATE")


class TestLegacyTemplatePath:
    """Verify old _get_prompt_api()._template_system_prompt still works."""

    def test_direct_prompt_api_mutation_still_works(self):
        """Old pattern: runtime._get_prompt_api(agent)._template_system_prompt = X"""
        from dana.core.runtime.anthropic import AnthropicRuntime

        rt = AnthropicRuntime()
        agent = MagicMock()
        agent.object_id = "test"
        agent._identity_override = None
        agent.__class__.__doc__ = "Test"
        agent._resources = []
        agent._workflows = []
        agent._agents = []

        prompt_api = rt._get_prompt_api(agent)
        prompt_api._template_system_prompt = "LEGACY_TEMPLATE"
        assert prompt_api._template_system_prompt == "LEGACY_TEMPLATE"
