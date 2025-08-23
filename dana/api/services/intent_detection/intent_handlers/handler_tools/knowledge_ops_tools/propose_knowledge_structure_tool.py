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


class ProposeKnowledgeStructureTool(BaseTool):
    def __init__(
        self,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
    ):
        self.domain = domain
        self.role = role
        tool_info = BaseToolInformation(
            name="propose_knowledge_structure",
            description="Generate a comprehensive hierarchical knowledge structure for a new topic domain. Creates organized topic breakdown with main categories and subtopics to help users visualize and plan knowledge areas before generation. Essential for adding new knowledge domains.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="user_message",
                        type="string",
                        description="A comprehensive message that acknowledges the user's request, explains the approach, and sets context for the knowledge structure proposal",
                        example="I understand you want to add comprehensive knowledge about cryptocurrency to Sofia's expertise. Based on your request, I'll create a structured breakdown covering all essential areas.",
                    ),
                    BaseArgument(
                        name="topic",
                        type="string",
                        description="The main topic or domain to create knowledge structure for (e.g., 'cryptocurrency', 'machine learning', 'financial analysis')",
                        example="cryptocurrency",
                    ),
                    BaseArgument(
                        name="focus_areas",
                        type="string",
                        description="Optional specific areas to emphasize or include in the structure (e.g., 'trading, technical analysis' for crypto)",
                        example="blockchain fundamentals, trading, DeFi",
                    ),
                    BaseArgument(
                        name="depth_level",
                        type="string",
                        description="Structure depth: 'basic' (2-3 levels), 'comprehensive' (3-4 levels), or 'detailed' (4-5 levels)",
                        example="comprehensive",
                    ),
                ],
                required=["topic"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()

    async def _execute(self, topic: str, user_message: str = "", focus_areas: str = "", depth_level: str = "comprehensive") -> ToolResult:
        """
        Generate hierarchical knowledge structure for a new topic domain.

        Returns: ToolResult with proposed structure for user review and refinement
        """
        try:
            logger.info(f"Proposing knowledge structure for topic: {topic}")

            # Generate comprehensive topic structure using LLM
            structure_content = self._generate_topic_structure(topic, focus_areas, depth_level)

            # Format the response for user review
            content = self._build_structured_response(user_message, topic, structure_content)

            return ToolResult(name="propose_knowledge_structure", result=content, require_user=True)

        except Exception as e:
            logger.error(f"Failed to propose knowledge structure: {e}")
            return ToolResult(
                name="propose_knowledge_structure", result=f"❌ Error proposing structure for '{topic}': {str(e)}", require_user=True
            )

    def _generate_topic_structure(self, topic: str, focus_areas: str, depth_level: str) -> str:
        """Generate hierarchical topic structure using LLM."""

        # Determine structure parameters based on depth level
        depth_params = {
            "basic": {"levels": "2-3", "subtopics_per_category": "3-4", "detail": "essential topics only"},
            "comprehensive": {"levels": "3-4", "subtopics_per_category": "4-6", "detail": "comprehensive coverage"},
            "detailed": {"levels": "4-5", "subtopics_per_category": "5-8", "detail": "detailed and specialized topics"},
        }

        params = depth_params.get(depth_level.lower(), depth_params["comprehensive"])

        structure_prompt = f"""You are a domain expert creating a comprehensive knowledge structure for: {topic}

TASK: Create a hierarchical knowledge structure with {params["levels"]} levels of depth.

REQUIREMENTS:
1. Create {params["subtopics_per_category"]} main categories (📁) that cover the domain comprehensively
2. Under each main category, add {params["subtopics_per_category"]} specific subtopics (📄) 
3. Focus on {params["detail"]} - practical, actionable knowledge areas
4. Use clear, descriptive names that indicate what knowledge would be generated
5. Structure should be logical and follow natural learning progression

FOCUS AREAS: {focus_areas if focus_areas else "Cover all essential aspects of the domain"}

DOMAIN CONTEXT:
- Target audience: {self.role} working in {self.domain}
- Purpose: Knowledge base for AI agent training and decision-making
- Emphasis: Practical, actionable knowledge over theoretical concepts

FORMAT REQUIREMENTS:
- Use 📁 for main categories (folders)
- Use 📄 for specific subtopics (knowledge generation targets)
- Use proper indentation for tree structure
- Each subtopic should be specific enough for focused knowledge generation

EXAMPLE FORMAT:
📁 **Category Name**
  - 📄 Specific Subtopic 1
  - 📄 Specific Subtopic 2
  - 📄 Specific Subtopic 3

Generate the complete knowledge structure now:"""

        try:
            response = Misc.safe_asyncio_run(
                self.llm.query,
                BaseRequest(
                    arguments={"messages": [{"role": "user", "content": structure_prompt}], "temperature": 0.3, "max_tokens": 1500}
                ),
            )

            structure_content = Misc.get_response_content(response)
            logger.info(f"Generated structure content: {structure_content[:200]}...")

            return structure_content

        except Exception as e:
            logger.error(f"Failed to generate topic structure: {e}")
            # Fallback structure
            return f"""📁 {topic.title()} Fundamentals


📁 **Application of {topic.title()} **
  - 📄 Specific Subtopic 1
  - 📄 Specific Subtopic 2
  - 📄 Specific Subtopic 3

📁 **Advanced {topic.title()}**
  - 📄 Advanced Subtopic 1
  - 📄 Advanced Subtopic 2
  - 📄 Advanced Subtopic 3

⚠️ Note: This is a fallback structure due to generation error. Please refine as needed."""

    def refine_structure(self, current_structure: str, refinement_request: str) -> str:
        """Refine existing structure based on user feedback."""
        refinement_prompt = f"""Refine this knowledge structure based on user feedback:

CURRENT STRUCTURE:
{current_structure}

USER FEEDBACK/REQUEST:
{refinement_request}

TASK: Modify the structure according to the user's request while maintaining:
1. Proper hierarchical format with 📁 and 📄 symbols
2. Logical organization and flow
3. Specific, actionable subtopic names
4. Appropriate depth and breadth

Generate the refined structure:"""

        try:
            response = Misc.safe_asyncio_run(
                self.llm.query,
                BaseRequest(
                    arguments={"messages": [{"role": "user", "content": refinement_prompt}], "temperature": 0.2, "max_tokens": 1200}
                ),
            )

            return Misc.get_response_content(response)

        except Exception as e:
            logger.error(f"Failed to refine structure: {e}")
            return f"❌ Error refining structure: {str(e)}\n\nOriginal structure:\n{current_structure}"

    def _build_structured_response(self, user_message: str, topic: str, structure_content: str) -> str:
        """Build a structured response with user message and knowledge structure."""
        response_parts = []

        # Add user message first (acknowledgment and context)
        if user_message:
            response_parts.append(f"{user_message}")
            response_parts.append("")  # Empty line for spacing

        # Add the main structure header
        response_parts.append(f"🏗️ **Proposed Knowledge Structure:** {topic.title()}")
        response_parts.append("")  # Empty line for spacing

        # Add the structure content
        response_parts.append(structure_content)
        response_parts.append("")  # Empty line for spacing

        # Add next steps and guidelines
        response_parts.append("""💡 **Next Steps:**
- Review the proposed structure above carefully
- Identify any areas you'd like to modify, expand, or remove  
- Once satisfied, we'll add this structure to your knowledge tree
""")

        # Join all parts with proper spacing
        return "\n".join(response_parts)
