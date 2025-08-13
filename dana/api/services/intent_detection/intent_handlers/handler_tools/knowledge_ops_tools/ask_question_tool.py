from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)


class AskQuestionTool(BaseTool):
    """
    Unified tool for user interactions - replaces both AskFollowUpQuestionTool and AskApprovalTool.
    Handles both general questions and approval requests naturally based on the question content.
    """

    def __init__(self):
        tool_info = BaseToolInformation(
            name="ask_question",
            description="Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="question",
                        type="string",
                        description="You need to provide the context of existing tool results and then the follow up question you want to ask the user.",
                        example="Question to ask the user with sufficient context to understand the current situation and the follow up question.",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="Optional An array of 2-5 options for the user to choose from. Each option should be a string describing a possible answer. You may not always need to provide options, but it may be helpful in many cases where it can save the user from having to type out a response manually. IMPORTANT NOTE: Do not include Yes/No options",
                        example='["Option 1", "Option 2", "Option 3"]',
                    ),
                ],
                required=["question"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, question: str, options: list[str] = None) -> ToolResult:
        """
        Execute question based on content - automatically handles approvals vs general questions.
        """
        # Detect if this is an approval question based on common patterns
        content = question

        for option in options:
            content += f"\n- {option}"

        return ToolResult(name="ask_question", result=content, require_user=True)
