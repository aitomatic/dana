from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)


class AskQuestionTool(BaseTool):
    """
    Tool for asking questions to users with optional context and button-style options.
    Provides a streamlined interface for interactive problem-solving.
    """

    def __init__(self):
        tool_info = BaseToolInformation(
            name="ask_question",
            description="Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="ack",
                        type="string",
                        description="Optional: A message that acknowledges the user's request and provides context before asking the question. This can include factual information about the current state, decision logic explaining why you're asking, or any other context that helps the user understand the situation. This should make the user feel heard and informed about how your discoveries relate to what they're trying to accomplish. Avoid referring to outputs that are not available, e.g. 'Here is the current structure' but the structure is not available.",
                        example="I've found 5 documents in this knowledge pack. To help you better, I need to know which document you'd like to explore first.",
                    ),
                    BaseArgument(
                        name="question",
                        type="string",
                        description="The main question to ask the user, directly related to their goals. For approvals, phrase as 'Would you like me to...?' or 'Should I proceed with...?'. For information gathering, ask specifically what you need to know to help them achieve their objective. Make it clear and actionable.",
                        example="Would you like me to read a specific document, or explore all documents in this knowledge pack?",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="Optional: List of actionable choices (typically 1-3 options) that directly answer the question. Each option must be a complete user response that makes sense when sent as the next message. Use descriptive phrases, not generic yes/no responses. Omit if the question requires open-ended user input.",
                        example='["Read document 1: Safety Manual", "List all documents first", "Search for specific content"]',
                    ),
                ],
                required=["ack", "question"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(
        self,
        ack: str,
        question: str,
        options: list[str] = None,
    ) -> ToolResult:
        """
        Execute question with optional context message and button-style options.
        """
        content = self._build_sophisticated_response(ack, question, options)

        return ToolResult(name="ask_question", result=content, require_user=True)

    def _build_sophisticated_response(
        self,
        user_message: str,
        question: str,
        options: list[str] = None,
    ) -> str:
        """
        Build a response with optional context message, question, and HTML button-style options.
        """
        response_parts = []

        # Add user message first (acknowledgment and context)
        if user_message:
            response_parts.append(f"<p>{user_message}</p>")
            response_parts.append("")  # Empty line for spacing

        # Add the main question
        response_parts.append(f"<p><strong>{question}</strong></p>")
        response_parts.append("")  # Empty line for spacing

        # Add options if provided
        if options and len(options) > 0:
            response_parts.append("<div class='options-container'>")
            for i, option in enumerate(options, 1):
                # Create clickable button-style options (onclick handled by React)
                response_parts.append(f"<button class='option-button' data-option='{i}'>{option}</button>")
            response_parts.append("</div>")
            response_parts.append("<p><em>Or, just type your own request in the chat</em></p>")
            response_parts.append("")  # Empty line for spacing
        # Join all parts with proper spacing
        return "\n".join(response_parts)
