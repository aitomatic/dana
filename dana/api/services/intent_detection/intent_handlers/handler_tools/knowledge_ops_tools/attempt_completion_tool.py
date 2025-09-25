from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
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
            description="Present information to the user. Use for: 1) Final results after workflow completion, 2) Direct answers to agent information requests ('Tell me about Sofia'), 3) System capability questions ('What can you help me with?'), 4) Out-of-scope request redirection. DO NOT use for knowledge structure questions - use explore_knowledge instead. Optionally provide one option for next step if it is relevant, but if there is option provided, ALWAYS use options parameter and ONLY provided one option.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="Summary of what was accomplished, highlight the key points using bold markdown (e.g. **key points**). OR direct answer/explanation to user's question",
                        example="✅ Successfully generated 10 knowledge artifacts OR Sofia is your Personal Finance Advisor that I'm helping you build OR I specialize in building knowledge for Sofia through structure design and content generation",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="Provide option if there is one relevant next step or choice. Provide only ONE option. Use when presenting option to the user after completing a task or when asking for next action. Option must be a complete user response that makes sense when sent as the next message. If the summary is about added topics successfully, the option must be Generate knowledge for added topics",
                        example='["Add this structure to domain knowledge"]',
                    ),
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
