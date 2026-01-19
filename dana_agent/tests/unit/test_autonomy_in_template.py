"""Test that autonomy instructions are properly placed in the system prompt template."""

import pytest

from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec, KLXMLCodec
from dana.core.knowledge.prompts.prompt_api import TEMPLATE_SYSTEM_PROMPT


class TestAutonomyInTemplate:
    """Test that autonomy is in the template, not the codec."""

    def test_template_contains_autonomous_operation_section(self):
        """Verify the template has the <output_format> section."""
        assert "<output_format>" in TEMPLATE_SYSTEM_PROMPT
        assert "</output_format>" in TEMPLATE_SYSTEM_PROMPT

    def test_template_contains_key_autonomy_rules(self):
        """Verify the template contains key autonomy rules."""
        # Check for critical autonomy instructions
        assert "STRICT OUTPUT FORMAT" in TEMPLATE_SYSTEM_PROMPT
        assert "<done>" in TEMPLATE_SYSTEM_PROMPT
        assert "<function_call>" in TEMPLATE_SYSTEM_PROMPT
        assert "<response>" in TEMPLATE_SYSTEM_PROMPT

    def test_template_no_todo_resource_reference(self):
        """Verify the template no longer mentions the todo-resource."""
        assert "todo-resource" not in TEMPLATE_SYSTEM_PROMPT

    def test_csxml_codec_has_no_autonomy(self):
        """Verify CSXMLCodec only has format rules, no autonomy."""
        instructions = CSXMLCodec.get_instruction()

        # Should NOT contain autonomy-related phrases
        assert "AUTONOMOUS" not in instructions
        assert "multi-step" not in instructions.lower()
        assert "After EACH tool result" not in instructions

        # Should contain format-related phrases
        assert "<thinking>" in instructions
        assert "<response>" in instructions
        assert "<function_call>" in instructions
        assert "FORMAT RULES" in instructions

    def test_klxml_codec_has_no_autonomy(self):
        """Verify KLXMLCodec only has format rules, no autonomy."""
        instructions = KLXMLCodec.get_instruction()

        # Should NOT contain autonomy-related phrases
        assert "AUTONOMOUS" not in instructions
        assert "multi-step" not in instructions.lower()
        assert "After EACH tool result" not in instructions

        # Should contain format-related phrases
        assert "<thinking>" in instructions
        assert "<response>" in instructions
        assert "FORMAT RULES" in instructions


class TestAgentSystemPromptIncludesAutonomy:
    """Test that actual agent system prompts include autonomy (JSON format via DefaultRuntime)."""

    def test_star_agent_system_prompt_has_autonomy(self):
        """Verify STARAgent system prompt includes autonomy instructions."""

        class TestAgent(STARAgent):
            """A test agent for verification."""

            def __init__(self):
                super().__init__(
                    agent_type="test",
                    agent_id="test-001",
                    auto_register=False,
                    enable_web_search=False,
                    enable_skills=False,
                    enable_code_execution=False,
                )

        agent = TestAgent()
        system_prompt = agent.system_prompt

        # Check JSON-based autonomy section is present (DefaultRuntime format)
        assert "## Output Format" in system_prompt
        assert '"done"' in system_prompt
        assert "JSON" in system_prompt

    def test_star_agent_subclass_inherits_autonomy(self):
        """Verify subclasses of STARAgent inherit autonomy instructions."""

        class CustomAgent(STARAgent):
            """A custom agent that extends STARAgent."""

            def __init__(self):
                super().__init__(
                    agent_type="custom",
                    agent_id="custom-001",
                    auto_register=False,
                    enable_web_search=False,
                    enable_skills=False,
                    enable_code_execution=False,
                )

        agent = CustomAgent()
        system_prompt = agent.system_prompt

        # Subclass should also have JSON-based autonomy (DefaultRuntime format)
        assert "## Output Format" in system_prompt
        assert '"done"' in system_prompt
