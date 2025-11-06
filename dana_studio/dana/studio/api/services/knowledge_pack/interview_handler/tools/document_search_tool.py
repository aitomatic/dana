"""
DocumentSearchTool for searching relevant documents using RAGResourceV2.
"""

from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2


class DocumentSearchTool(BaseTool):
    """
    Tool for searching relevant documents using RAGResourceV2.
    """

    def __init__(self, rag_resource: RAGResourceV2):
        self.rag_resource = rag_resource
        tool_info = BaseToolInformation(
            name="document_search",
            description="Search relevant documents for the given query using the knowledge base.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="query",
                        type="string",
                        description="Search query to find relevant documents",
                        example="safety procedures for lockout tagout",
                    ),
                ],
                required=["query"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, query: str = "", **kwargs) -> ToolResult:
        """
        Search documents using RAGResourceV2.
        """
        try:
            # Call RAGResourceV2 query method
            results = await self.rag_resource.query(query)

            # Format results as string
            if isinstance(results, str):
                formatted_content = results
            elif isinstance(results, list):
                # Handle raw chunks format
                formatted_content = "\n\n".join(
                    [f"**Source**: {chunk.get('source', 'Unknown')}\n**Content**: {chunk.get('content', '')}" for chunk in results]
                )
            else:
                formatted_content = str(results)

            return ToolResult(
                name="document_search",
                result=formatted_content,
                require_user=False,
            )

        except Exception as e:
            return ToolResult(
                name="document_search",
                result=f"❌ Error searching documents: {str(e)}",
                require_user=False,
            )


if __name__ == "__main__":
    import asyncio
    from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2

    async def test_document_search():
        # Initialize RAG resource with test sources
        rag = RAGResourceV2(
            sources=["/Users/lam/Desktop/repos/opendxa/docs"],
            name="test_rag",
            debug=True,
        )

        # Create tool
        tool = DocumentSearchTool(rag)

        print("🔍 Testing DocumentSearchTool")
        print("=" * 40)

        # Test search
        result = await tool._execute(query="safety procedures")
        print("📄 Search Results:")
        print(result.result[:200] + "..." if len(result.result) > 200 else result.result)
        print()
        print(f"✅ Tool executed successfully: {result.name}")

    asyncio.run(test_document_search())
