"""
UpdateInterviewApproachTool for modifying the Interview Approach section.
"""

from dana.lang.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)
from ..utils import parse_template, write_template


class UpdateInterviewApproachTool(BaseTool):
    """
    Tool for updating the Interview Approach section.
    """

    def __init__(self, template_path: str):
        self.template_path = template_path
        tool_info = BaseToolInformation(
            name="update_interview_approach",
            description="Modify the Interview Approach section (goal, style, duration, topics covered). Updates metadata about the interview process.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="field",
                        type="string",
                        description="Which field to update: 'goal', 'style', 'duration', 'topics_covered', 'all'",
                        example="duration",
                    ),
                    BaseArgument(
                        name="new_value",
                        type="string",
                        description="New value for the field",
                        example="90-120 minutes total, with breaks every 30 minutes",
                    ),
                ],
                required=["field", "new_value"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, field: str, new_value: str, **kwargs) -> ToolResult:
        """
        Update interview approach field.
        """
        try:
            # Parse template
            template_data = parse_template(self.template_path)
            approach = template_data["approach"]

            # Validate field
            valid_fields = ["goal", "style", "duration", "topics_covered"]
            if field not in valid_fields and field != "all":
                return ToolResult(
                    name="update_interview_approach",
                    result=f"❌ Invalid field '{field}'. Valid fields: {', '.join(valid_fields)}, 'all'",
                    require_user=False,
                )

            # Create preview of changes
            preview = self._create_preview(approach, field, new_value)

            return ToolResult(
                name="update_interview_approach",
                result=preview,
                require_user=True,  # Require user approval
            )

        except Exception as e:
            return ToolResult(
                name="update_interview_approach",
                result=f"❌ Error updating interview approach: {str(e)}",
                require_user=False,
            )

    def _create_preview(self, approach: dict, field: str, new_value: str) -> str:
        """Create preview of changes to interview approach."""
        content_parts = []

        content_parts.append("## Interview Approach Changes")
        content_parts.append("")

        if field == "all":
            content_parts.append("**New Interview Approach:**")
            content_parts.append(new_value)
        else:
            content_parts.append(f"**Updating field: {field}**")
            content_parts.append("")

            # Show current value
            current_value = approach.get(field, "Not set")
            content_parts.append(f"**Current {field}**: {current_value}")
            content_parts.append("")

            # Show new value
            content_parts.append(f"**New {field}**: {new_value}")

        content_parts.append("")
        content_parts.append("**Would you like to apply these changes?**")

        return "\n".join(content_parts)

    async def apply_changes(self, field: str, new_value: str, **kwargs) -> ToolResult:
        """Apply the changes to the template."""
        try:
            # Parse template
            template_data = parse_template(self.template_path)

            # Update the approach section
            if field == "all":
                # Replace entire approach section
                template_data["approach"]["raw_text"] = new_value
            else:
                # Update specific field
                template_data["approach"][field] = new_value

                # Reconstruct the raw text
                template_data["approach"]["raw_text"] = self._reconstruct_approach_text(template_data["approach"])

            # Reconstruct template content
            new_content = self._reconstruct_template(template_data)

            # Write updated template
            write_template(self.template_path, new_content)

            return ToolResult(
                name="update_interview_approach",
                result=f"✅ Successfully updated interview approach field: {field}",
                require_user=False,
            )

        except Exception as e:
            return ToolResult(
                name="update_interview_approach",
                result=f"❌ Error applying changes: {str(e)}",
                require_user=False,
            )

    def _reconstruct_approach_text(self, approach: dict) -> str:
        """Reconstruct the approach section text."""
        content_parts = []

        if approach.get("goal"):
            content_parts.append(f"- **Goal**: {approach['goal']}")
        if approach.get("style"):
            content_parts.append(f"- **Style**: {approach['style']}")
        if approach.get("duration"):
            content_parts.append(f"- **Duration**: {approach['duration']}")
        if approach.get("topics_covered"):
            content_parts.append(f"- **Topics Covered**: {approach['topics_covered']}")

        return "\n".join(content_parts)

    def _reconstruct_template(self, template_data: dict) -> str:
        """Reconstruct template from parsed data."""
        content_parts = []

        # Header
        content_parts.append("# Master Interview Template: Food Manufacturing - Process Operator")
        content_parts.append("")

        # Approach section
        if template_data["approach"].get("raw_text"):
            content_parts.append("## Interview Approach")
            content_parts.append(template_data["approach"]["raw_text"])
            content_parts.append("")
            content_parts.append("---")
            content_parts.append("")

        # Topics section
        content_parts.append("## Topic Opening Questions")
        content_parts.append("")

        for topic in template_data["topics"]:
            content_parts.append(f"### {topic['name']}")
            if topic["background"]:
                content_parts.append(f"**Background**: {topic['background']}")
            if topic["questions"]:
                content_parts.append("**Opening Questions**:")
                for i, question in enumerate(topic["questions"], 1):
                    content_parts.append(f"{i}. {question}")
            if topic["connections"]:
                content_parts.append(f"**Listen for connections to**: {topic['connections']}")
            content_parts.append("")
            content_parts.append("---")
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
                content_parts.append(f'- "{question}"')
            content_parts.append("")

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
**Listen for connections to**: Emergency Response

---

## Follow-up Framework
- "Can you tell me more about that?"
"""

    async def test_update_approach():
        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(test_template)
            temp_path = f.name

        try:
            tool = UpdateInterviewApproachTool()

            print("📋 Testing UpdateInterviewApproachTool")
            print("=" * 40)

            # Test updating duration
            result = await tool._execute(
                field="duration", new_value="90-120 minutes total, with breaks every 30 minutes", template_path=temp_path
            )

            print("⏱️ Duration Update Preview:")
            print(result.result)
            print()
            print("✅ Tool shows preview requiring user approval")

        finally:
            os.unlink(temp_path)

    asyncio.run(test_update_approach())
