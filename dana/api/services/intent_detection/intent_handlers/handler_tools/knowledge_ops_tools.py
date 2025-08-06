from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
)
from dana.api.core.schemas import MessageData, DomainKnowledgeTree
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
import logging

logger = logging.getLogger(__name__)


class AskFollowUpQuestionTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="ask_follow_up_question",
            description="Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="question",
                        type="string",
                        description="The question to ask the user. This should be a clear, specific question that addresses the information you need.",
                        example="Your question here",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="An array of 2-5 options for the user to choose from. Each option should be a string describing a possible answer. You may not always need to provide options, but it may be helpful in many cases where it can save the user from having to type out a response manually. IMPORTANT: NEVER include an option to toggle to Act mode, as this would be something you need to direct the user to do manually themselves if needed.",
                        example='Array of options here (optional), e.g. ["Option 1", "Option 2", "Option 3"]',
                    ),
                ],
                required=["question"],
            ),
        )
        super().__init__(tool_info)

    def _execute(self, question: str, options: list[str] = None) -> MessageData:
        options_str = "\n".join([f"- {option}" for option in options]) if options else ""
        return MessageData(
            role="user",
            content=f"""
{question}
{options_str}
""",
            require_user=True,
        )


class NavigateTreeTool(BaseTool):
    def __init__(self, llm: LLMResource | None = None, tree_structure: DomainKnowledgeTree | None = None):
        tool_info = BaseToolInformation(
            name="navigate_tree",
            description="Navigate the knowledge tree to find or create the target location for storing knowledge. Extracts the topic hierarchy from the user request and determines the appropriate path in the tree structure.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="user_message",
                        type="string",
                        description="The original user request to extract topic hierarchy from",
                        example="Add knowledge about current ratio analysis for financial analysts",
                    ),
                    BaseArgument(
                        name="context",
                        type="string",
                        description="Any relevant context from the conversation to help determine the correct path",
                        example="User is building a financial analysis agent",
                    ),
                ],
                required=["user_message"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()
        self.tree_structure = tree_structure

    def _execute(self, user_message: str, context: str = "") -> MessageData:
        """
        Navigate knowledge tree to target location by extracting topic from user request.

        Returns: MessageData with navigation results
        """
        try:
            # Use LLM to extract hierarchical topic structure
            from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import TREE_NAVIGATION_PROMPT

            # Format tree structure if available
            tree_context = self._format_tree_structure()

            prompt = TREE_NAVIGATION_PROMPT.format(user_message=user_message, tree_context=tree_context)
            if context:
                prompt += f"\n\nAdditional context: {context}"

            llm_request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": 200})

            # Run synchronously using Misc.safe_asyncio_run
            response = Misc.safe_asyncio_run(self.llm.query, llm_request)
            result = Misc.text_to_dict(Misc.get_response_content(response))

            path = result.get("path", ["General", "Unknown", "Topic"])
            reasoning = result.get("reasoning", "")
            existing_node = result.get("existing_node", False)

            # TODO: In real implementation, would check/create nodes in actual tree structure
            # For now, use the LLM's determination
            path_str = " > ".join(path)
            status = "existing" if existing_node else "new"

            content = f"""Tree Navigation Complete:
Path: {path_str}
Status: {status} node
Reasoning: {reasoning}

Ready to proceed with knowledge generation at this location."""

            return MessageData(role="user", content=content, require_user=False)

        except Exception as e:
            logger.error(f"Failed to navigate tree: {e}")
            # Fallback navigation
            fallback_path = f"General > Knowledge > {user_message[:50]}"
            content = f"""Tree Navigation Complete:
Path: {fallback_path}
Status: new node (fallback)
Error: {str(e)}

Using fallback navigation. Ready to proceed with knowledge generation."""

            return MessageData(role="user", content=content, require_user=False)

    def _format_tree_structure(self) -> str:
        """
        Format the domain knowledge tree for inclusion in the prompt.
        Returns a string representation of the tree structure.
        """
        if not self.tree_structure or not self.tree_structure.root:
            return "Current domain knowledge tree is empty."

        def format_node(node, level=0):
            """Recursively format tree nodes with indentation"""
            indent = "  " * level
            lines = [f"{indent}- {node.topic}"]
            for child in node.children:
                lines.extend(format_node(child, level + 1))
            return lines

        tree_lines = ["Current domain knowledge tree structure:"]
        tree_lines.extend(format_node(self.tree_structure.root))

        return "\n".join(tree_lines)


if __name__ == "__main__":
    # Test AskFollowUpQuestionTool
    tool = AskFollowUpQuestionTool()
    print("AskFollowUpQuestionTool:")
    print(tool)
    print("\n" + "=" * 60 + "\n")

    # Test NavigateTreeTool
    nav_tool = NavigateTreeTool()
    print("NavigateTreeTool:")
    print(nav_tool)
