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
            description="Present information to the user. Use for: 1) Final results after workflow completion, 2) Direct answers to agent information requests ('Tell me about Sofia'), 3) System capability questions ('What can you help me with?'), 4) Out-of-scope request redirection. DO NOT use for knowledge structure questions - use explore_knowledge instead.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="Summary of what was accomplished, highlight the key points using bold markdown (e.g. **key points**). OR direct answer/explanation to user's question",
                        example="✅ Successfully generated 10 knowledge artifacts OR Sofia is your Personal Finance Advisor that I'm helping you build OR I specialize in building knowledge for Sofia through structure design and content generation",
                    ),
                ],
                required=["summary"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, summary: str) -> ToolResult:
        return ToolResult(name="attempt_completion", result=summary, require_user=True)
