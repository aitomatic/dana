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
import re

logger = logging.getLogger(__name__)


class RefineKnowledgeStructureTool(BaseTool):
    def __init__(
        self,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
    ):
        self.domain = domain
        self.role = role
        tool_info = BaseToolInformation(
            name="refine_knowledge_structure",
            description="Refine and modify proposed knowledge structures based on user feedback. Can add sections, remove sections, reorganize content, or make other modifications while preserving the overall structure quality. Always shows the updated structure to the user for review.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="current_structure",
                        type="string",
                        description="The current proposed knowledge structure to be modified",
                        example="📁 **Cryptocurrency**\n- 📄 Bitcoin\n- 📄 Ethereum",
                    ),
                    BaseArgument(
                        name="modification_request",
                        type="string",
                        description="User's request for how to modify the structure (e.g., 'remove DeFi section', 'add NFT category', 'reorganize sections')",
                        example="remove the DeFi section",
                    ),
                    BaseArgument(
                        name="topic",
                        type="string",
                        description="The main topic domain being refined (for context)",
                        example="cryptocurrency",
                    ),
                ],
                required=["modification_request"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()

    async def _execute(self, current_structure: str = "", modification_request: str = "", topic: str = "") -> ToolResult:
        """
        Refine the knowledge structure based on user feedback.

        Returns: ToolResult with refined structure for user review
        """
        try:
            logger.info(f"Refining knowledge structure for topic: {topic}")
            logger.info(f"Modification request: {modification_request}")

            # Validate modification request
            if not modification_request.strip():
                return ToolResult(name="refine_knowledge_structure", result="❌ Error: No modification request provided", require_user=True)

            # Extract current structure from conversation context if not provided
            if not current_structure.strip():
                logger.info("No current structure provided, will need to be extracted from conversation context")
                return ToolResult(
                    name="refine_knowledge_structure",
                    result="❌ Error: No current structure found in conversation context. Please ensure a structure was proposed first using propose_knowledge_structure.",
                    require_user=True,
                )

            # Extract topic from structure if not provided
            if not topic.strip():
                topic = self._extract_topic_from_structure(current_structure)

            # Apply the modification using LLM
            refined_structure = self._apply_structure_modification(current_structure, modification_request, topic)

            # Validate the refined structure
            if not self._validate_structure_format(refined_structure):
                logger.warning("Refined structure format validation failed, attempting to fix")
                refined_structure = self._fix_structure_format(refined_structure, topic)

            # Format the response for user review
            content = f"""🔄 Refined Knowledge Structure: {topic.title()}

**Applied Modification:** {modification_request}

{refined_structure}

💡 **Review the Updated Structure:**
- Check if the modification was applied correctly
- Identify any additional changes needed
- Consider if the structure still flows logically
- Ensure all important areas are covered

📋 **Next Steps:**
- If satisfied: say "approve" or "looks good" to add this structure to your knowledge tree
- For more changes: describe what else you'd like to modify
- To undo: say "revert" to go back to the previous version

**Ready for your feedback on this refined structure!**"""

            return ToolResult(name="refine_knowledge_structure", result=content, require_user=True)

        except Exception as e:
            logger.error(f"Failed to refine knowledge structure: {e}")
            return ToolResult(
                name="refine_knowledge_structure",
                result=f"❌ Error refining structure: {str(e)}\n\nOriginal structure preserved:\n{current_structure}",
                require_user=True,
            )

    def _apply_structure_modification(self, current_structure: str, modification_request: str, topic: str) -> str:
        """Apply the requested modification to the structure using LLM."""

        modification_prompt = f"""You are a knowledge structure expert. Modify the following knowledge structure based on the user's request.

CURRENT STRUCTURE:
{current_structure}

USER REQUEST: {modification_request}

TOPIC DOMAIN: {topic}

MODIFICATION GUIDELINES:
1. Preserve the hierarchical format with 📁 for categories and 📄 for subtopics
2. Maintain proper indentation for tree structure
3. Keep the overall structure logical and well-organized
4. If removing sections, ensure remaining structure is complete
5. If adding sections, place them in logical positions
6. If reorganizing, maintain natural learning progression
7. Ensure all subtopics are specific enough for knowledge generation

COMMON MODIFICATION TYPES:
- Remove: Delete specified sections completely
- Add: Insert new sections in appropriate locations
- Reorganize: Change order or hierarchy of existing sections
- Rename: Update section names while preserving content intent
- Expand: Add more subtopics to existing sections
- Merge: Combine related sections

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

Apply the requested modification and return ONLY the complete modified structure in the exact same format as the input."""

        try:
            response = Misc.safe_asyncio_run(
                self.llm.query,
                BaseRequest(
                    arguments={
                        "messages": [{"role": "user", "content": modification_prompt}],
                        "temperature": 0.2,  # Lower temperature for more consistent modifications
                        "max_tokens": 1500,
                    }
                ),
            )

            refined_structure = Misc.get_response_content(response).strip()
            logger.info(f"Applied modification successfully: {refined_structure[:200]}...")

            return refined_structure

        except Exception as e:
            logger.error(f"Failed to apply structure modification: {e}")
            # Fallback: try simple text-based modification
            return self._apply_simple_modification(current_structure, modification_request)

    def _apply_simple_modification(self, current_structure: str, modification_request: str) -> str:
        """Fallback method for simple text-based modifications."""

        request_lower = modification_request.lower()

        # Simple removal logic
        if "remove" in request_lower:
            # Extract what to remove
            lines = current_structure.split("\n")
            modified_lines = []

            # Look for section to remove
            skip_section = False
            section_to_remove = None

            # Try to identify what to remove from the request
            for line in lines:
                if line.strip().startswith("📁"):
                    section_name = line.strip().replace("📁", "").strip()
                    if any(term in section_name.lower() for term in request_lower.split() if len(term) > 3):
                        skip_section = True
                        section_to_remove = section_name
                        continue
                    else:
                        skip_section = False

                if not skip_section:
                    modified_lines.append(line)

            result = "\n".join(modified_lines)
            if result.strip() != current_structure.strip():
                logger.info(f"Simple removal applied, removed section containing terms from: {modification_request}")
                return result

        # If no modification could be applied, return original with note
        return f"{current_structure}\n\n⚠️ Note: Could not automatically apply modification '{modification_request}'. Please provide more specific instructions."

    def get_structure_summary(self, structure: str) -> str:
        """Get a brief summary of the structure for logging/debugging."""
        if not structure.strip():
            return "Empty structure"

        lines = [line.strip() for line in structure.split("\n") if line.strip()]
        categories = [line for line in lines if "📁" in line]
        subtopics = [line for line in lines if "📄" in line]

        return f"{len(categories)} categories, {len(subtopics)} subtopics"

    def _extract_topic_from_structure(self, structure: str) -> str:
        """Extract the main topic from a structure string."""
        # Look for patterns like "Knowledge Structure: Topic" or first category
        lines = structure.split("\n")

        for line in lines:
            if "Knowledge Structure:" in line:
                # Extract topic after the colon
                parts = line.split("Knowledge Structure:")
                if len(parts) > 1:
                    topic = parts[1].strip()
                    # Remove any markdown or extra formatting
                    topic = re.sub(r"[#*_]", "", topic).strip()
                    if topic:
                        return topic
            elif line.strip().startswith("📁"):
                # Use first category as fallback
                topic = line.strip().replace("📁", "").strip()
                if topic:
                    return topic

        return "Unknown Topic"
