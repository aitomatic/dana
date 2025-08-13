from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
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
                        name="question",
                        type="string",
                        description="The main question to ask the user. For approvals, phrase as 'Do you approve...?' or 'Should I proceed with...?'. For information gathering, ask directly what you need to know.",
                        example="How would you like to proceed with Smart Contracts?",
                    ),
                    BaseArgument(
                        name="context",
                        type="string",
                        description="Current state information - what was found, current tree state, or relevant background information the user needs to make an informed decision.",
                        example="Found 'Smart Contracts' under 'Blockchain Fundamentals' in your knowledge tree",
                    ),
                    BaseArgument(
                        name="decision_logic",
                        type="string",
                        description="Explanation of why specific options are being offered - the reasoning behind the current question and available choices.",
                        example="Since this topic already exists, I can offer knowledge generation options",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="Optional array of 2-5 options for the user to choose from. Each option should be a string describing a possible answer. You may not always need to provide options, but it may be helpful in many cases where it can save the user from having to type out a response manually. IMPORTANT NOTE: Do not include Yes/No options",
                        example='["Generate knowledge for Smart Contracts", "Generate for all subtopics", "Cancel generation"]',
                    ),
                    BaseArgument(
                        name="workflow_phase",
                        type="string",
                        description="Optional current workflow phase to provide context about where we are in the process (exploration, structure planning, generation, etc.).",
                        example="knowledge generation planning",
                    ),
                ],
                required=["question"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, question: str, context: str = "", decision_logic: str = "", options: list[str] = None, workflow_phase: str = "") -> ToolResult:
        """
        Execute sophisticated question with context, decision logic, and formatted options.
        """
        # Build sophisticated, context-rich response
        content = self._build_sophisticated_response(question, context, decision_logic, options, workflow_phase)
        
        return ToolResult(name="ask_question", result=content, require_user=True)

    def _build_sophisticated_response(self, question: str, context: str = "", decision_logic: str = "", options: list[str] = None, workflow_phase: str = "") -> str:
        """
        Build a sophisticated, context-rich response with clear sections and visual indicators.
        """
        response_parts = []
        
        # Add workflow phase if provided
        if workflow_phase:
            response_parts.append(f"{workflow_phase}")
            response_parts.append("")  # Empty line for spacing
        
        # Add current state section if context provided
        if context:
            response_parts.append(f"{context}")
            response_parts.append("")  # Empty line for spacing
        
        # Add decision logic section if provided
        if decision_logic:
            response_parts.append(f"{decision_logic}")
            response_parts.append("")  # Empty line for spacing
        
        # Add the main question
        response_parts.append(f"{question}")
        response_parts.append("")  # Empty line for spacing
        
        # Add options if provided
        if options and len(options) > 0:
          
            for i, option in enumerate(options, 1):
                response_parts.append(f"• {option}")
        
        # Join all parts with proper spacing
        return "\n".join(response_parts)
