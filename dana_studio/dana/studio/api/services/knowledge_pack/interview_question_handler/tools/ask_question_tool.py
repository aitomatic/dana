from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
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
            description="Provide current state to the user and decision logic. Then ask the user ONLY ONE question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="preface",
                        type="string",
                        description="A natural introduction that: (1) acknowledges understanding of the user's last response by referencing specific content from their answer, (2) provides relevant context about current state/progress, and (3) sets up the question naturally. Write this as a cohesive paragraph that flows naturally. Use neutral, factual language to paraphrase key points, identify connections, or recognize implications. Match the information density of their response (brief answer = brief preface). This is MANDATORY for every question to prove you understood their input and provide necessary context.",
                        example="So your lockout procedure has six steps, and high-voltage equipment specifically requires two people to verify de-energization - one to test, one to witness. We've covered the standard LOTO procedure, and understanding exception handling will complete the safety protocol picture.",
                    ),
                    BaseArgument(
                        name="question",
                        type="string",
                        description="The main question to ask the user, directly related to their goals. For approvals, phrase as 'Would you like me to...?' or 'Should I proceed with...?'. For information gathering, ask specifically what you need to know to help them achieve their objective. Make it clear and actionable.",
                        example="Walk me through what happens if the equipment doesn't fully de-energize during that verification step.",
                    ),
                    BaseArgument(
                        name="workflow_phase",
                        type="string",
                        description="Current phase in the knowledge operations workflow to help user understand the process stage. Use clear, user-friendly terms like 'Knowledge Gap Analysis', 'Structure Planning', 'Content Generation Planning', 'Implementation Ready', 'Intent Clarification', etc.",
                        example="Knowledge Gap Analysis",
                    ),
                    BaseArgument(
                        name="category",
                        type="string",
                        description="Type of question being asked. Use 'interview_note' for questions directly from the interview template/note, 'followup' for clarification questions when user's answer is ambiguous or unclear, 'normal' for general communication not related to interview content (e.g., meta-questions about the process).",
                        example="interview_note|followup|normal",
                    ),
                ],
                required=["question", "category", "preface"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(
        self,
        question: str,
        category: str,
        preface: str,
        workflow_phase: str = "",
    ) -> ToolResult:
        """
        Execute sophisticated question with preface and formatted options.
        """
        content = self._build_sophisticated_response(preface, question, workflow_phase, category)

        return ToolResult(name="ask_question", result=content, require_user=True)

    def _build_sophisticated_response(
        self,
        preface: str,
        question: str,
        workflow_phase: str = "",
        category: str = "",
    ) -> str:
        """
        Build a sophisticated, context-rich response with HTML formatting.
        """
        response_parts = []

        # Add preface first (combines acknowledgment and context)
        if preface:
            response_parts.append(f"<p>{preface}</p>")
            response_parts.append("")  # Empty line for spacing

        # Add the main question
        response_parts.append(f"<p><strong>{question}</strong></p>")
        response_parts.append("")  # Empty line for spacing

        # Add category as metadata (for frontend/backend tracking)
        if category:
            response_parts.append(f"<p><em>Category: {category}</em></p>")
            response_parts.append("")  # Empty line for spacing

        # Join all parts with proper spacing
        return "\n".join(response_parts)
