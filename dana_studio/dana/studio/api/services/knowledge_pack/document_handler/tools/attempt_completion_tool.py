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
            description="Present document exploration results, findings, or answers to the user. Use this tool when: 1) Document exploration workflow is complete and you have findings to share, 2) User's questions about documents have been answered, 3) User asks about document status, structure, or content ('What documents are available?', 'What's in document X?'), 4) You've discovered insights from documents that should be summarized, 5) Workflow has reached a natural conclusion. This tool presents information in a user-friendly format and can optionally provide interactive next-step options. DO NOT use this tool for asking questions - use ask_question instead.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="answer",
                        type="string",
                        description="MUST BE IN markdown format. The response content to present to the user. This can be: 1) A summary of document exploration findings with key insights highlighted using bold markdown (e.g. **key points**), 2) A direct answer to the user's question about documents, 3) A status update about available documents or their content, 4) Insights discovered from document analysis. Format the content clearly with proper markdown formatting for readability.",
                        example="**Document Exploration Complete**\n\nI've reviewed the safety procedures documents in this knowledge pack. Here are the key findings:\n\n• **LOTO Procedures**: Found 3 documents covering lockout/tagout procedures with detailed step-by-step instructions\n• **PPE Requirements**: 2 documents specify personal protective equipment requirements for different work areas\n• **Emergency Response**: 1 document outlines emergency evacuation procedures\n\nWould you like me to read any specific document in detail, or help you refine interview questions based on these findings?",
                    ),
                ],
                required=["answer"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, answer: str, **kwargs) -> ToolResult:
        """
        Execute completion.
        """
        content = answer

        return ToolResult(name="attempt_completion", result=content, require_user=True)
