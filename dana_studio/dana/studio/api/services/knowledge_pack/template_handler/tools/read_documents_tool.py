"""
ReadDocumentsTool for browsing and reading documents in a knowledge pack.
"""

from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)
from dana.studio.api.repositories.domain_knowledge_repo import SQLDomainKnowledgeRepo
from dana.studio.api.repositories.document_repo import SQLDocumentRepo
from datetime import datetime


class ReadDocumentsTool(BaseTool):
    """
    Tool for browsing and reading documents in a knowledge pack.
    
    Two modes:
    1. List Mode (no document_id): Shows all documents with metadata
    2. Read Mode (with document_id): Previews document content using RAG
    """

    def __init__(self, kp_id: int, rag_docs=None):
        self.kp_id = kp_id
        self.rag_docs = rag_docs

        tool_info = BaseToolInformation(
            name="read_documents",
            description="Browse and read documents in the knowledge pack. Without document_id, lists all documents. With document_id, reads and previews document content using RAG.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="document_id",
                        type="integer",
                        description="Optional: Specific document ID to read/preview content from",
                        example="98",
                    ),
                ],
                required=[],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, document_id: int = None, **kwargs) -> ToolResult:
        """
        List or read documents from the knowledge pack.
        
        Args:
            document_id: Optional document ID. If None, lists all documents. If provided, reads that document.
        """
        try:
            # Get database session from kwargs
            db = kwargs.get("db")
            if not db:
                return ToolResult(
                    name="read_documents",
                    result="❌ Database session not available",
                    require_user=False,
                )

            # Mode 1: List all documents (no document_id provided)
            if document_id is None:
                return await self._list_all_documents(db)
            
            # Mode 2: Read specific document (document_id provided)
            else:
                return await self._read_document_content(document_id, db)

        except Exception as e:
            return ToolResult(
                name="read_documents",
                result=f"❌ Error accessing documents: {str(e)}",
                require_user=False,
            )

    async def _list_all_documents(self, db) -> ToolResult:
        """List all documents in the knowledge pack."""
        # Get associated document IDs
        doc_ids = await SQLDomainKnowledgeRepo.get_kp_associated_documents(
            kp_id=self.kp_id, db=db
        )

        if not doc_ids:
            return ToolResult(
                name="read_documents",
                result="📄 No documents are currently associated with this knowledge pack.\n\nTo add documents, upload them through the document management interface.",
                require_user=False,
            )

        # Fetch document details
        documents = await SQLDocumentRepo.get_document_by_ids(
            document_ids=doc_ids, db=db
        )

        if not documents:
            return ToolResult(
                name="read_documents",
                result="📄 Document IDs found but documents could not be retrieved.",
                require_user=False,
            )

        # Format document list
        content = self._format_documents_list(documents)

        return ToolResult(
            name="read_documents",
            result=content,
            require_user=False,
        )

    async def _read_document_content(self, document_id: int, db) -> ToolResult:
        """Read and preview content from a specific document using RAG."""
        # Get document details
        documents = await SQLDocumentRepo.get_document_by_ids(
            document_ids=[document_id], db=db
        )

        if not documents:
            return ToolResult(
                name="read_documents",
                result=f"❌ Document with ID {document_id} not found.",
                require_user=False,
            )

        doc = documents[0]

        # Use RAG to get content overview if available
        content_preview = None
        if self.rag_docs:
            try:
                query = f"Provide a brief overview and summary of the key content in the document titled: {doc.original_filename}"
                results = await self.rag_docs.query(query)
                
                if results:
                    # Get top 5 most relevant chunks
                    content_preview = "\n\n".join([r.text for r in results[:5]])
            except Exception as e:
                print(f"Warning: Could not retrieve document content via RAG: {e}")

        # Format document preview
        content = self._format_document_preview(doc, content_preview)

        return ToolResult(
            name="read_documents",
            result=content,
            require_user=False,
        )

    def _format_documents_list(self, documents: list) -> str:
        """Format list of all documents for display."""
        content_parts = []

        content_parts.append(f"## Documents in Knowledge Pack (ID: {self.kp_id})")
        content_parts.append("")
        content_parts.append(f"**Total Documents**: {len(documents)}")
        content_parts.append("")

        for i, doc in enumerate(documents, 1):
            content_parts.append(f"### {i}. {doc.original_filename}")
            content_parts.append(f"- **Document ID**: {doc.id}")
            content_parts.append(f"- **File Type**: {doc.mime_type}")
            
            # Format file size
            if doc.file_size:
                file_size_mb = doc.file_size / (1024 * 1024)
                if file_size_mb < 1:
                    file_size_kb = doc.file_size / 1024
                    content_parts.append(f"- **File Size**: {file_size_kb:.1f} KB")
                else:
                    content_parts.append(f"- **File Size**: {file_size_mb:.2f} MB")
            
            # Format upload date
            if doc.created_at:
                upload_date = doc.created_at.strftime("%Y-%m-%d %H:%M")
                content_parts.append(f"- **Uploaded**: {upload_date}")
            
            content_parts.append("")

        content_parts.append("---")
        content_parts.append("")
        content_parts.append("💡 **Tip**: To read a document's content, use `read_documents` with the document ID. To generate questions from a document, use `generate_additional_questions` with document IDs.")

        return "\n".join(content_parts)

    def _format_document_preview(self, doc, content_preview: str = None) -> str:
        """Format document preview with content for display."""
        content_parts = []

        content_parts.append(f"## Document Preview: {doc.original_filename}")
        content_parts.append("")
        content_parts.append(f"**Document ID**: {doc.id}")
        content_parts.append(f"**File Type**: {doc.mime_type}")
        
        # Format file size
        if doc.file_size:
            file_size_mb = doc.file_size / (1024 * 1024)
            if file_size_mb < 1:
                file_size_kb = doc.file_size / 1024
                content_parts.append(f"**File Size**: {file_size_kb:.1f} KB")
            else:
                content_parts.append(f"**File Size**: {file_size_mb:.2f} MB")
        
        # Format upload date
        if doc.created_at:
            upload_date = doc.created_at.strftime("%Y-%m-%d %H:%M")
            content_parts.append(f"**Uploaded**: {upload_date}")
        
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

        # Add content preview if available
        if content_preview:
            content_parts.append("### Content Overview")
            content_parts.append("")
            content_parts.append(content_preview)
        else:
            content_parts.append("### Content Overview")
            content_parts.append("")
            content_parts.append("*Document content preview is not available. The document may not be indexed yet, or RAG is not configured for this knowledge pack.*")
        
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")
        content_parts.append("💡 **Next Steps**: You can generate interview questions from this document using `generate_additional_questions` with this document ID.")

        return "\n".join(content_parts)


if __name__ == "__main__":
    import asyncio

    async def test_read_documents():
        """Test the ReadDocumentsTool with mock data."""
        print("🧪 Testing ReadDocumentsTool")
        print("=" * 40)

        # Create tool
        tool = ReadDocumentsTool(kp_id=8, rag_docs=None)

        print(f"✅ Tool created: {tool.info.name}")
        print(f"   Description: {tool.info.description}")
        print()
        print("Note: Actual execution requires database session and RAG")
        print("      Use this tool within the template handler context")

    asyncio.run(test_read_documents())

