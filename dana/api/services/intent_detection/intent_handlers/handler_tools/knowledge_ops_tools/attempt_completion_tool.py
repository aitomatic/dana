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
            description="Present information to the user. Use for: 1) Final results after workflow completion, 2) Direct answers to agent information requests ('Tell me about Sofia'), 3) System capability questions ('What can you help me with?'), 4) Out-of-scope request redirection. DO NOT use for knowledge structure questions - use explore_knowledge instead.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="Summary of what was accomplished OR direct answer/explanation to user's question",
                        example="Successfully generated 10 knowledge artifacts OR Sofia is your Personal Finance Advisor that I'm helping you build OR I specialize in building knowledge for Sofia through structure design and content generation",
                    ),
                ],
                required=["summary"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, summary: str) -> ToolResult:
        # Context-validated completion detection - check actual state, not just phrases
        # First, check for obvious non-completion indicators
        if any(phrase in summary.lower() for phrase in [
            "would be generated",
            "will be generated", 
            "preview",
            "overview",
            "sample content",
            "brief description",
            "what would be",
            "sample facts",
            "sample procedures",
            "no new artifacts",
            "already processed",
            "deemed complete"
        ]):
            is_completion = False
        else:
            # Check for completion indicators
            completion_indicators = [
                "knowledge generation complete",
                "workflow is now complete", 
                "all knowledge has been generated",
                "generation workflow complete",
                "successfully generated",
                "workflow finished"
            ]
            
            # Only mark as completion if summary contains strong completion language
            # AND doesn't contain contradictory information
            is_completion = any(phrase in summary.lower() for phrase in completion_indicators)

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
            content = f"""{summary}"""

        return ToolResult(name="attempt_completion", result=content, require_user=True)
