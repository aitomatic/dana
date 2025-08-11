from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)


class AttemptCompletionTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="attempt_completion",
            description="Present information to the user. Use for final results after workflow completion OR to directly answer user questions about capabilities, explanations, or informational requests that don't require task execution.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="Summary of what was accomplished OR direct answer/explanation to user's question",
                        example="Successfully generated 10 knowledge artifacts OR I can help you generate financial analysis knowledge, modify knowledge structure, and explore available topics",
                    ),
                ],
                required=["summary"],
            ),
        )
        super().__init__(tool_info)

    def _execute(self, summary: str) -> ToolResult:
        # Detect if this is a completion (mentions artifacts/generation) or information response
        is_completion = any(
            keyword in summary.lower() for keyword in ["generated", "created", "complete", "artifacts", "workflow", "finished"]
        )

        if is_completion:
            # Format as workflow completion
            content = f"""🎉 Knowledge Generation Complete

{summary}

✅ All knowledge has been:
- Generated with high accuracy
- Validated for quality  
- Stored to vector database
- Made available for agent usage

The knowledge generation workflow is now complete. Your agent has been enhanced with new domain expertise!"""
        else:
            # Format as direct information response
            content = f"""ℹ️ {summary}"""

        return ToolResult(name="attempt_completion", result=content, require_user=True)
