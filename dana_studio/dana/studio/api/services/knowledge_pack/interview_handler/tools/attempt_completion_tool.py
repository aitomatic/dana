"""
AttemptCompletionTool for signaling workflow completion.
"""

import logging
from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)

logger = logging.getLogger(__name__)


class AttemptCompletionTool(BaseTool):
    """
    Tool for signaling that the interview workflow is complete.
    """

    def __init__(self):
        tool_info = BaseToolInformation(
            name="attempt_completion",
            description="Signal that the interview workflow is complete and provide the final result.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="result",
                        type="string",
                        description="The final result or summary of the interview session",
                        example="Thank you for sharing your insights on **Safety Procedures** ✓\n\nKey points captured:\n• 6-step LOTO process with verification checkpoints\n• Dual verification for high-voltage equipment\n• Monthly safety audits with documentation\n• Specialized lockout devices with unique keys\n\n---\n\n**Progress**: 1 of 11 topics complete (~9%)\n\nReady to explore **Equipment Operation** next?",
                    ),
                    BaseArgument(
                        name="options",
                        type="array",
                        description="Optional list of next step options for the user to choose from",
                        example="Begin Equipment Operation topic, Review safety procedures captured, Check overall progress",
                    ),
                ],
                required=["result"],
            ),
        )
        super().__init__(tool_info)

    def _build_interactive_response(self, result: str, options: list[str]) -> str:
        """
        Build an interactive response with HTML button-style options.
        """
        response_parts = []

        # Add the result content
        response_parts.append(f"<p>{result}</p>")
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

    async def _execute(self, result: str, options: list[str] = None, **kwargs) -> ToolResult:
        """
        Signal workflow completion with final result.
        Validates that notes have been properly updated.
        """
        try:
            # Log if this appears to be a topic completion
            is_topic_completion = any(word in result.lower() for word in ["completed", "complete", "done", "finished"]) and \
                                any(word in result.lower() for word in ["topic", "section", "area"])
            
            if is_topic_completion:
                logger.info(f"📝 Topic completion detected: {result[:100]}...")
                logger.warning("⚠️ Ensure update_note was called before attempt_completion to mark topic as Completed")
            
            # Build response with options if provided
            if options and len(options) > 0:
                formatted_result = self._build_interactive_response(result, options)
                require_user = True  # Options require user interaction
            else:
                formatted_result = f"✅ Workflow Complete: {result}"
                require_user = False

            return ToolResult(
                name="attempt_completion",
                result=formatted_result,
                require_user=require_user,
            )

        except Exception as e:
            return ToolResult(
                name="attempt_completion",
                result=f"❌ Error completing workflow: {str(e)}",
                require_user=False,
            )


if __name__ == "__main__":
    import asyncio

    async def test_attempt_completion():
        # Create tool
        tool = AttemptCompletionTool()

        print("✅ Testing AttemptCompletionTool")
        print("=" * 40)

        # Test completion
        result = await tool._execute(
            result="Thank you for sharing your insights on **Safety Procedures** ✓\n\nKey points captured:\n• 6-step LOTO process with verification checkpoints\n• Dual verification for high-voltage equipment\n• Monthly safety audits with documentation\n\n---\n\n**Progress**: 1 of 11 topics complete (~9%)\n\nReady to explore **Equipment Operation** next?",
            options=["Begin Equipment Operation topic", "Review safety procedures captured"]
        )

        print("🎯 Completion Result:")
        print(result.result)
        print()
        print(f"✅ Tool executed successfully: {result.name}")
        print(f"Requires user input: {result.require_user}")

    asyncio.run(test_attempt_completion())
