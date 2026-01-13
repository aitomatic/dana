"""
ViewTemplateTool for displaying template sections.
"""

from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)
from ..utils import parse_template, find_topic_fuzzy


class ViewTemplateTool(BaseTool):
    """
    Tool for viewing template sections or the entire template.
    """

    def __init__(self, template_path: str):
        self.template_path = template_path
        tool_info = BaseToolInformation(
            name="view_template",
            description="Display the current template or specific sections. Use this to see what exists before making changes.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="section",
                        type="string",
                        description="Which section to view: 'all', 'topic:{topic_name}', 'approach', 'relationship_prompts', 'followup_framework'",
                        example="topic:Lockout/Tagout (LOTO) Procedures",
                    ),
                ],
                required=[],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, section: str = "all", **kwargs) -> ToolResult:
        """
        Display template or specific section.
        """
        try:
            # Parse template
            template_data = parse_template(self.template_path)

            if section == "all":
                content = self._format_full_template(template_data)
            elif section == "approach":
                content = self._format_approach_section(template_data["approach"])
            elif section == "relationship_prompts":
                content = self._format_relationship_prompts(template_data["relationship_prompts"])
            elif section == "followup_framework":
                content = self._format_followup_framework(template_data["followup_framework"])
            elif section.startswith("topic:"):
                topic_name = section.split(":", 1)[1]
                content = self._format_topic_section(template_data["topics"], topic_name)
            else:
                content = f"❌ Unknown section: {section}"

            return ToolResult(
                name="view_template",
                result=content,
                require_user=False,
            )

        except Exception as e:
            return ToolResult(
                name="view_template",
                result=f"❌ Error viewing template: {str(e)}",
                require_user=False,
            )

    def _format_full_template(self, template_data: dict) -> str:
        """Format the complete template for display."""
        content_parts = []

        # Header
        content_parts.append("# Master Interview Template")
        content_parts.append("")

        # Approach section
        if template_data["approach"].get("raw_text"):
            content_parts.append("## Interview Approach")
            content_parts.append(template_data["approach"]["raw_text"])
            content_parts.append("")

        # Topics section
        content_parts.append("## Topic Opening Questions")
        content_parts.append("")

        for topic in template_data["topics"]:
            content_parts.append(f"### {topic['name']}")
            if topic["questions"]:
                if topic["background"]:
                    content_parts.append(f"**Background**: {topic['background']}")
                content_parts.append("**Opening Questions**:")
                for i, question in enumerate(topic["questions"], 1):
                    content_parts.append(f"{i}. {question}")
            else:
                content_parts.append("*(No questions defined for this topic yet)*")
            content_parts.append("")

        # Relationship prompts
        if template_data["relationship_prompts"]:
            content_parts.append("## Relationship Exploration Prompts")
            for prompt in template_data["relationship_prompts"]:
                content_parts.append(f"- {prompt}")
            content_parts.append("")

        # Follow-up framework
        if template_data["followup_framework"]:
            content_parts.append("## Follow-up Framework")
            for question in template_data["followup_framework"]:
                content_parts.append(f"- {question}")
            content_parts.append("")

        return "\n".join(content_parts)

    def _format_approach_section(self, approach: dict) -> str:
        """Format the interview approach section."""
        if not approach.get("raw_text"):
            return "No interview approach section found."

        content_parts = ["## Interview Approach", ""]
        content_parts.append(approach["raw_text"])
        return "\n".join(content_parts)

    def _format_relationship_prompts(self, prompts: list) -> str:
        """Format relationship exploration prompts."""
        if not prompts:
            return "No relationship exploration prompts found."

        content_parts = ["## Relationship Exploration Prompts", ""]
        for prompt in prompts:
            content_parts.append(f"- {prompt}")
        return "\n".join(content_parts)

    def _format_followup_framework(self, framework: list) -> str:
        """Format follow-up framework."""
        if not framework:
            return "No follow-up framework found."

        content_parts = ["## Follow-up Framework", ""]
        for question in framework:
            content_parts.append(f'- "{question}"')
        return "\n".join(content_parts)

    def _format_topic_section(self, topics: list, topic_name: str) -> str:
        """Format a specific topic section."""
        topic, message = find_topic_fuzzy(topics, topic_name)

        if not topic:
            return message  # Error or suggestions

        content_parts = []

        # Add success message if fuzzy match was used
        if "Matched:" in message and "Exact" not in message:
            content_parts.append(f"ℹ️  {message}\n")

        content_parts.append(f"### {topic['name']}")
        content_parts.append("")

        if topic["questions"]:
            if topic["background"]:
                content_parts.append(f"**Background**: {topic['background']}")

            content_parts.append("**Opening Questions**:")
            for i, question in enumerate(topic["questions"], 1):
                content_parts.append(f"{i}. {question}")

        else:
            content_parts.append("*(No questions defined for this topic yet)*")

        return "\n".join(content_parts)


if __name__ == "__main__":
    import asyncio
    import tempfile
    import os

    # Create test template
    test_template = """# Master Interview Template: Test Domain

## Interview Approach
- **Goal**: Capture expert knowledge
- **Style**: Conversational
- **Duration**: 60 minutes
- **Topics Covered**: 2 topics

---

## Topic Opening Questions

### Safety Procedures
**Background**: Focuses on safety protocols
**Opening Questions**:
1. How do you approach safety?
2. What safety procedures are important?

---

### Quality Control
**Background**: Covers quality assurance
**Opening Questions**:
1. How do you ensure quality?
2. What quality metrics do you track?

---

## Relationship Exploration Prompts
- When expert mentions safety, explore connection to quality

## Follow-up Framework
- "Can you tell me more about that?"
- "What's an example of when that happened?"
"""

    async def test_view_template():
        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(test_template)
            temp_path = f.name

        try:
            tool = ViewTemplateTool()

            print("🔍 Testing ViewTemplateTool")
            print("=" * 40)

            # Test viewing all sections
            result = await tool._execute(section="all", template_path=temp_path)
            print("📄 Full Template:")
            print(result.result[:200] + "..." if len(result.result) > 200 else result.result)
            print()

            # Test viewing specific topic
            result = await tool._execute(section="topic:Safety Procedures", template_path=temp_path)
            print("🎯 Safety Procedures Topic:")
            print(result.result)
            print()

            # Test viewing approach
            result = await tool._execute(section="approach", template_path=temp_path)
            print("📋 Interview Approach:")
            print(result.result)

        finally:
            os.unlink(temp_path)

    asyncio.run(test_view_template())
