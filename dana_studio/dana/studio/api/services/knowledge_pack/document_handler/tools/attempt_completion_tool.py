from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)


class AttemptCompletionTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="attempt_completion",
            description="Present template refinement results to the user. Use when: 1) Template refinement is complete, 2) User asks about template status ('What questions are in topic X?'), 3) User asks about template structure. Summarize what template changes were made. NEVER suggest knowledge generation - this tool is only for template refinement.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="MUST BE IN markdown format. Summary of what was accomplished, highlight the key points using bold markdown (e.g. **key points**). OR direct answer/explanation to user's question in ",
                        example="**Key points**: I've reviewed the current questions and they focus on traditional procedures. I can help enhance them to include modern digital safety systems.",
                    )
                ],
                required=["summary"],
            ),
        )
        super().__init__(tool_info)

    def _build_interactive_response(self, summary: str, options: list[str]) -> str:
        """
        Build an interactive response with HTML button-style options.
        """
        response_parts = []

        # Add the summary content
        response_parts.append(f"<p>{summary}</p>")
        response_parts.append("")  # Empty line for spacing

        # Add clickable options
        response_parts.append("<div class='options-container'>")
        for i, option in enumerate(options, 1):
            # Create clickable button-style options (onclick handled by React)
            response_parts.append(f"<button class='option-button' data-option='{i}'>{option}</button>")
        response_parts.append("</div>")
        response_parts.append("<p><em>Or, just type your own request in the chat</em></p>")
        response_parts.append("")  # Empty line for spacing

        # Join all parts with proper spacing
        return "\n".join(response_parts)

    async def _execute(self, summary: str, options: list[str] = None) -> ToolResult:
        """
        Execute completion with optional interactive options.
        """
        if options and len(options) > 0:
            content = self._build_interactive_response(summary, options)
        else:
            content = summary

        return ToolResult(name="attempt_completion", result=content, require_user=True)
