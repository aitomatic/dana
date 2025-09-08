from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)


class AskQuestionTool(BaseTool):
    """
    Enhanced unified tool for user interactions with sophisticated context integration.
    Provides current state, decision logic, and clear options to users.
    """

    def __init__(self):
        tool_info = BaseToolInformation(
            name="ask_question",
            description="Provide current state to the user and decision logic. Then ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="user_message",
                        type="string",
                        description="A comprehensive message that acknowledges the user's original request, explains your findings in the context of their goals, and addresses their specific concerns or needs. This should make the user feel heard and informed about how your discoveries relate to what they're trying to accomplish.",
                        example="I can see you need Sofia to help with small business loan decisions. I explored her financial knowledge and found strong expertise in investment analysis and market evaluation, but she currently lacks specific small business lending knowledge that would be essential for making loan recommendations.",
                    ),
                    BaseArgument(
                        name="question",
                        type="string",
                        description="The main question to ask the user, directly related to their goals. For approvals, phrase as 'Would you like me to...?' or 'Should I proceed with...?'. For information gathering, ask specifically what you need to know to help them achieve their objective. Make it clear and actionable.",
                        example="Would you like me to create a comprehensive small business loan advisory knowledge structure for Sofia?",
                    ),
                    BaseArgument(
                        name="context",
                        type="string",
                        description="Factual information about the current state - what was discovered during exploration, current tree structure, existing knowledge status, or relevant technical details. This provides the objective foundation for the user's decision-making.",
                        example="I explored Sofia's financial knowledge tree and found 41 knowledge areas covering investment analysis, market analysis, and financial analysis, but no specific expertise in small business lending, credit assessment, or loan decision criteria.",
                    ),
                    BaseArgument(
                        name="decision_logic",
                        type="string",
                        description="Clear explanation of why you're asking this specific question and why the provided options make sense. Help the user understand how each choice would advance their goals and what the implications are.",
                        example="Adding specialized small business loan knowledge would give Sofia the specific expertise needed to properly evaluate loan applications, assess credit risk, and provide informed lending recommendations to small business owners.",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="Array of 1-2 specific, actionable options that directly address the user's situation. Avoid withrawn options like 'Cancel/No' options. Each option should be a clear choice that moves toward their goal. Avoid generic Yes/No options - instead use descriptive actions like 'Create comprehensive loan knowledge structure', 'Add basic loan topics only', 'Explore existing knowledge first'. Options should be mutually exclusive and cover the most logical paths forward.",
                        example='["Create comprehensive small business loan knowledge structure", "Add basic loan evaluation topics to existing financial analysis", "Show me Sofia\'s current financial knowledge first", "Get strategic advice on loan advisory capabilities"]',
                    ),
                    BaseArgument(
                        name="workflow_phase",
                        type="string",
                        description="Current phase in the knowledge operations workflow to help user understand the process stage. Use clear, user-friendly terms like 'Knowledge Gap Analysis', 'Structure Planning', 'Content Generation Planning', 'Implementation Ready', 'Intent Clarification', etc.",
                        example="Knowledge Gap Analysis",
                    ),
                ],
                required=["question"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(
        self,
        question: str,
        user_message: str = "",
        context: str = "",
        decision_logic: str = "",
        options: list[str] = None,
        workflow_phase: str = "",
    ) -> ToolResult:
        """
        Execute sophisticated question with context, decision logic, and formatted options.
        """
        content = self._build_sophisticated_response(user_message, question, context, decision_logic, options, workflow_phase)

        return ToolResult(name="ask_question", result=content, require_user=True)

    def _build_sophisticated_response(
        self,
        user_message: str,
        question: str,
        context: str = "",
        decision_logic: str = "",
        options: list[str] = None,
        workflow_phase: str = "",
    ) -> str:
        """
        Build a sophisticated, context-rich response with HTML button-style options.
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
                response_parts.append(f"<button class='option-button' data-option='{i}'>{i}. {option}</button>")
            response_parts.append("</div>")
            response_parts.append("")  # Empty line for spacing
        # Join all parts with proper spacing
        return "\n".join(response_parts)
