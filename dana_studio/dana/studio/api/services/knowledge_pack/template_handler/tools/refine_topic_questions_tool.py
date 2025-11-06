"""
RefineTopicQuestionsTool for modifying opening questions for a topic.
"""

from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from ..utils import parse_template, find_topic_by_name, find_topic_fuzzy, write_template
from ..prompts import QUESTION_REFINEMENT_PROMPT
import re


class RefineTopicQuestionsTool(BaseTool):
    """
    Tool for refining opening questions for a specific topic.
    """

    def __init__(self, template_path: str, domain: str = "General", role: str = "Domain Expert", llm: LLMResource = None):
        self.template_path = template_path
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()

        tool_info = BaseToolInformation(
            name="refine_topic_questions",
            description="Modify opening questions for a specific topic based on user instructions. Generates refined questions using LLM and requires user approval before applying changes.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="topic_name",
                        type="string",
                        description="Name of the topic to refine questions for",
                        example="Lockout/Tagout (LOTO) Procedures",
                    ),
                    BaseArgument(
                        name="refinement_instruction",
                        type="string",
                        description="How to modify the questions - specific instructions for refinement",
                        example="Add questions about digital LOTO systems and how they integrate with legacy procedures",
                    ),
                    BaseArgument(
                        name="preserve_existing",
                        type="boolean",
                        description="Whether to keep existing questions and add new ones (true) or replace them (false)",
                        example="true",
                    ),
                ],
                required=["topic_name", "refinement_instruction"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, topic_name: str, refinement_instruction: str, preserve_existing: bool = True, **kwargs) -> ToolResult:
        """
        Refine questions for a specific topic.
        """
        try:
            # Parse template
            template_data = parse_template(self.template_path)

            # Find the topic with fuzzy matching
            topic, message = find_topic_fuzzy(template_data["topics"], topic_name)
            if not topic:
                return ToolResult(
                    name="refine_topic_questions",
                    result=message,  # Use detailed error message with suggestions
                    require_user=False,
                )

            # Generate refined questions using LLM
            refined_questions = await self._generate_refined_questions(
                topic_name, topic["questions"], refinement_instruction, self.domain, self.role
            )

            if not refined_questions:
                return ToolResult(
                    name="refine_topic_questions",
                    result="❌ Failed to generate refined questions",
                    require_user=False,
                )

            # Format preview
            preview = self._format_questions_preview(topic_name, topic["questions"], refined_questions, preserve_existing)

            return ToolResult(
                name="refine_topic_questions",
                result=preview,
                require_user=True,  # Require user approval
            )

        except Exception as e:
            return ToolResult(
                name="refine_topic_questions",
                result=f"❌ Error refining questions: {str(e)}",
                require_user=False,
            )

    async def _generate_refined_questions(
        self, topic_name: str, existing_questions: list, instruction: str, domain: str, role: str
    ) -> list[str]:
        """Generate refined questions using LLM."""
        try:
            # Format existing questions
            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(existing_questions)])

            # Create prompt
            prompt = QUESTION_REFINEMENT_PROMPT.format(
                role=role, domain=domain, topic_name=topic_name, existing_questions=questions_text, refinement_instruction=instruction
            )

            # Query LLM
            request = BaseRequest(
                arguments={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }
            )

            response = await self.llm.query(request)
            content = Misc.get_response_content(response).strip()

            # Parse questions from response
            questions = self._parse_questions_from_response(content)
            return questions

        except Exception as e:
            print(f"Error generating refined questions: {e}")
            return []

    def _parse_questions_from_response(self, content: str) -> list[str]:
        """Parse questions from LLM response."""
        questions = []

        # Look for numbered questions
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            # Match patterns like "1. Question text" or "1) Question text"
            match = re.match(r"^\d+[.)]\s*(.+)$", line)
            if match:
                questions.append(match.group(1).strip())

        return questions

    def _format_questions_preview(self, topic_name: str, existing_questions: list, refined_questions: list, preserve_existing: bool) -> str:
        """Format preview of refined questions."""
        content_parts = []

        content_parts.append(f"## Refined Questions for: {topic_name}")
        content_parts.append("")

        if preserve_existing:
            content_parts.append("**Current Questions (to be preserved):**")
            for i, question in enumerate(existing_questions, 1):
                content_parts.append(f"{i}. {question}")
            content_parts.append("")
            content_parts.append("**New Refined Questions:**")
            for i, question in enumerate(refined_questions, len(existing_questions) + 1):
                content_parts.append(f"{i}. {question}")
        else:
            content_parts.append("**New Refined Questions (replacing existing):**")
            for i, question in enumerate(refined_questions, 1):
                content_parts.append(f"{i}. {question}")

        content_parts.append("")
        content_parts.append("**Would you like to apply these changes?**")

        return "\n".join(content_parts)

    async def apply_changes(self, topic_name: str, refined_questions: list, preserve_existing: bool, **kwargs) -> ToolResult:
        """Apply the refined questions to the template."""
        try:
            # Parse template
            template_data = parse_template(self.template_path)

            # Find and update the topic
            for topic in template_data["topics"]:
                if topic["name"] == topic_name:
                    if preserve_existing:
                        topic["questions"].extend(refined_questions)
                    else:
                        topic["questions"] = refined_questions
                    break

            # Reconstruct template content
            new_content = self._reconstruct_template(template_data)

            # Write updated template
            write_template(self.template_path, new_content)

            return ToolResult(
                name="refine_topic_questions",
                result=f"✅ Successfully updated questions for '{topic_name}'",
                require_user=False,
            )

        except Exception as e:
            return ToolResult(
                name="refine_topic_questions",
                result=f"❌ Error applying changes: {str(e)}",
                require_user=False,
            )

    def _reconstruct_template(self, template_data: dict) -> str:
        """Reconstruct template from parsed data."""
        content_parts = []

        # Header
        content_parts.append("# Knowledge Capture Template: {domain}")
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
                # if topic["connections"]:
                #     content_parts.append(f"**Listen for connections to**: {topic['connections']}")
            else:
                content_parts.append("*(No questions defined for this topic yet)*")
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

---

## Topic Opening Questions

### Safety Procedures
**Background**: Focuses on safety protocols
**Opening Questions**:
1. How do you approach safety?
2. What safety procedures are important?

---

## Relationship Exploration Prompts
- When expert mentions safety, explore connection to quality

## Follow-up Framework
- "Can you tell me more about that?"
"""

    async def test_refine_questions():
        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(test_template)
            temp_path = f.name

        try:
            tool = RefineTopicQuestionsTool()

            print("🔧 Testing RefineTopicQuestionsTool")
            print("=" * 40)

            # Test refining questions
            result = await tool._execute(
                topic_name="Safety Procedures",
                refinement_instruction="Add questions about digital safety tools and automation",
                preserve_existing=True,
                template_path=temp_path,
                domain="Manufacturing",
                role="Safety Expert",
            )

            print("📝 Refined Questions Preview:")
            print(result.result)
            print()
            print("✅ Tool shows preview requiring user approval")

        finally:
            os.unlink(temp_path)

    asyncio.run(test_refine_questions())
