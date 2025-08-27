from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
import logging

logger = logging.getLogger(__name__)


class PreviewKnowledgeTopicTool(BaseTool):
    def __init__(
        self,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
    ):
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        tool_info = BaseToolInformation(
            name="preview_knowledge_topic",
            description="Generate lightweight previews of knowledge content during structure planning. Shows sample facts, procedures, and heuristics for any topic to help users understand what would be generated before adding topics to the knowledge structure. Use for 'brief overview', 'what would be generated', 'show sample content' requests.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="user_message",
                        type="string",
                        description="A comprehensive message that acknowledges the user's request and explains what the preview will show",
                        example="I understand you want to see a preview of what knowledge would be generated for investing. This will help you decide whether to add this topic to Sofia's knowledge structure.",
                    ),
                    BaseArgument(
                        name="topic",
                        type="string",
                        description="The topic to generate a preview for (e.g., 'investing', 'risk management', 'cryptocurrency')",
                        example="investing",
                    ),
                    BaseArgument(
                        name="context",
                        type="string",
                        description="Optional context or specific focus for the preview (e.g., 'for personal finance', 'brief overview', 'investment strategies')",
                        example="personal finance and investment strategy",
                    ),
                ],
                required=["topic"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()

    async def _execute(self, topic: str, user_message: str = "", context: str = "") -> ToolResult:
        """
        Generate a lightweight preview of knowledge content for a topic.

        Returns: ToolResult with sample content preview for user review
        """
        try:
            logger.info(f"Generating knowledge preview for topic: {topic}")

            if not topic.strip():
                return ToolResult(name="preview_knowledge_topic", result="❌ Error: No topic provided for preview", require_user=True)

            # Generate lightweight preview content
            preview_content = self._generate_topic_preview(topic, context)

            # Format the response for user review
            content = self._build_preview_response(user_message, topic, preview_content)

            return ToolResult(name="preview_knowledge_topic", result=content, require_user=True)

        except Exception as e:
            logger.error(f"Failed to generate knowledge preview: {e}")
            return ToolResult(
                name="preview_knowledge_topic", result=f"❌ Error generating preview for '{topic}': {str(e)}", require_user=True
            )

    def _generate_topic_preview(self, topic: str, context: str) -> str:
        """Generate lightweight preview content using LLM."""

        context_info = f" with focus on {context}" if context.strip() else ""

        preview_prompt = f"""Generate a brief knowledge preview for the topic: {topic}{context_info}

CONTEXT:
- Target Agent: {self.role} working in {self.domain}
- Agent Tasks: {", ".join(self.tasks)}
- Purpose: Preview content during knowledge structure planning (NOT full generation)
- Audience: User deciding whether to add this topic to knowledge structure

REQUIREMENTS:
1. Generate 3-4 sample FACTS (definitions, data, key concepts)
2. Generate 2-3 sample PROCEDURES (step-by-step processes)
3. Generate 2-3 sample HEURISTICS (rules of thumb, decision guidelines)
4. Keep each item concise (1-2 sentences max)
5. Focus on practical, actionable knowledge
6. Make content relevant to {self.role} role
7. Use clear, professional language

FORMAT:
📄 Sample Facts:
• [Fact 1]
• [Fact 2]
• [Fact 3]

📋 Sample Procedures:
• [Procedure 1]
• [Procedure 2]

💡 Sample Heuristics:
• [Heuristic 1]
• [Heuristic 2]

Generate the preview content now:"""

        try:
            response = Misc.safe_asyncio_run(
                self.llm.query,
                BaseRequest(
                    arguments={
                        "messages": [{"role": "user", "content": preview_prompt}],
                        "temperature": 0.3,
                        "max_tokens": 800,  # Lightweight preview, not full generation
                    }
                ),
            )

            preview_content = Misc.get_response_content(response).strip()
            logger.info(f"Generated preview content: {preview_content[:200]}...")

            return preview_content

        except Exception as e:
            logger.error(f"Failed to generate topic preview: {e}")
            # Fallback preview
            return f"""📄 Sample Facts:
• {topic.title()} involves key concepts and principles relevant to {self.role}
• Understanding {topic} is important for effective decision-making
• {topic.title()} knowledge includes both theoretical and practical aspects

📋 Sample Procedures:
• Research and analyze {topic}-related information systematically
• Apply {topic} principles to real-world scenarios

💡 Sample Heuristics:
• Consider multiple perspectives when working with {topic}
• Balance theoretical knowledge with practical application

⚠️ Note: This is a basic preview due to generation error. The actual content would be more comprehensive and domain-specific."""

    def _build_preview_response(self, user_message: str, topic: str, preview_content: str) -> str:
        """Build a structured preview response with user message and preview content."""
        response_parts = []

        # Add user message first (acknowledgment and context)
        if user_message:
            response_parts.append(f"{user_message}")
            response_parts.append("")  # Empty line for spacing

        # Add the main preview header
        response_parts.append(f"🔍 **Knowledge Preview:** {topic.title()}")
        response_parts.append("")  # Empty line for spacing

        # Add the preview content
        response_parts.append(preview_content)
        response_parts.append("")  # Empty line for spacing

        # Add explanation and next steps
        response_parts.append(f"""💡 **This is a preview of what would be generated for {topic}.**

During structure planning, this helps you understand what content your agent would learn about {topic}. This is NOT actual knowledge generation - just a preview to help you make informed decisions about your knowledge structure.

**Next Steps:**
• Add this topic to your knowledge structure
• Modify the topic focus or scope  
• Preview a different topic
• Continue with structure planning

**Ready for your decision on this topic preview!**""")

        # Join all parts with proper spacing
        return "\n".join(response_parts)

    def get_topic_summary(self, topic: str) -> str:
        """Get a brief summary of the topic for logging/debugging."""
        return f"Preview for: {topic}"
