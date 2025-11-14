"""
ReadDocumentsTool for querying documents in a knowledge pack using RAG.
"""

import os
import logging
from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)
from dana.studio.api.repositories.document_repo import SQLDocumentRepo

logger = logging.getLogger(__name__)


class ReadDocumentsTool(BaseTool):
    """
    Tool for querying documents in a knowledge pack using RAG.

    Always requires a query. Optionally filter by document_id.
    """

    def __init__(self, kp_id: int, rag_docs=None):
        self.kp_id = kp_id
        self.rag_docs = rag_docs

        tool_info = BaseToolInformation(
            name="read_documents",
            description="Query documents in the knowledge pack using natural language. Search for specific information, answer questions, or find content across documents. Optionally filter to a specific document by providing document_id.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="query",
                        type="string",
                        description="The question or search query to find information in documents. This is required - always provide a specific question or search term.",
                        example="What safety procedures are mentioned?",
                    ),
                    BaseArgument(
                        name="document_id",
                        type="integer",
                        description="Optional: Limit search to a specific document. If omitted, searches across all documents in the knowledge pack.",
                        example="98",
                    ),
                ],
                required=["query"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, **kwargs) -> ToolResult:
        """
        Query documents using RAG.

        Args from kwargs:
            query: Required search query or question
            document_id: Optional document ID to filter search to specific document
            db: Database session (injected by handler)
        """
        try:
            # Extract parameters from kwargs
            query = kwargs.get("query")
            document_id = kwargs.get("document_id")
            db = kwargs.get("db")

            if not query:
                return ToolResult(
                    name="read_documents",
                    result="❌ Query parameter is required",
                    require_user=False,
                )

            if not db:
                return ToolResult(
                    name="read_documents",
                    result="❌ Database session not available",
                    require_user=False,
                )

            # Check RAG availability
            if not self.rag_docs:
                return ToolResult(
                    name="read_documents",
                    result="❌ RAG is not configured for this knowledge pack. Cannot query documents.",
                    require_user=False,
                )

            # Execute query
            return await self._query_documents(query, document_id, db)

        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return ToolResult(
                name="read_documents",
                result=f"❌ Error querying documents: {str(e)}",
                require_user=False,
            )

    def _resolve_file_path(self, file_path: str) -> str | None:
        """
        Resolve file path to absolute path.

        Handles:
        - "File " prefix removal
        - Relative path resolution
        - Filename-only paths (checks uploads directory)

        Returns:
            Absolute file path or None if file not found
        """
        if not file_path:
            return None

        # Remove "File " prefix if present
        if file_path.startswith("File "):
            logger.warning(f"File path has 'File' prefix, removing it: '{file_path}'")
            file_path = file_path[5:]
            logger.info(f"Corrected file path: '{file_path}'")

        # Resolve to absolute path if it's relative
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
            logger.debug(f"Resolved to absolute path: '{file_path}'")

        # If the file path is just a filename, try to find it in the uploads directory
        if os.path.basename(file_path) == file_path:
            logger.warning(f"File path is just a filename, looking in uploads directory: '{file_path}'")
            uploads_path = os.path.join("uploads", file_path)
            if os.path.exists(uploads_path):
                file_path = os.path.abspath(uploads_path)
                logger.info(f"Found file in uploads directory: '{file_path}'")
            else:
                logger.error(f"File not found in uploads directory: '{uploads_path}'")
                return None

        # Verify file exists
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: '{file_path}'")
            return None

        return file_path

    def _calculate_file_hash(self, file_path: str) -> str | None:
        """
        Calculate SHA-256 file hash from absolute file path.

        Args:
            file_path: Absolute path to the file

        Returns:
            File hash string or None if calculation fails
        """
        try:
            from aicapture.cache import HashUtils

            file_hash = HashUtils.calculate_file_hash(file_path)
            logger.debug(f"Calculated file hash for: {file_path}")
            return file_hash
        except ImportError:
            logger.error("aicapture.cache.HashUtils not available - cannot calculate file hash")
            return None
        except (OSError, FileNotFoundError) as e:
            logger.error(f"Error calculating file hash for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calculating file hash: {e}")
            return None

    async def _query_documents(self, query: str, document_id: int | None, db) -> ToolResult:
        """Query documents using RAG and format results."""
        # Query RAG (rag_docs is already checked in _execute)
        if not self.rag_docs:
            return ToolResult(
                name="read_documents",
                result="❌ RAG is not configured for this knowledge pack.",
                require_user=False,
            )

        # Get document context and prepare hash filtering if document_id provided
        doc_name = None
        original_hashes = None
        file_hash = None

        if document_id:
            documents = await SQLDocumentRepo.get_document_by_ids(document_ids=[document_id], db=db)
            if not documents:
                return ToolResult(
                    name="read_documents",
                    result=f"❌ Document with ID {document_id} not found.",
                    require_user=False,
                )

            doc = documents[0]
            doc_name = doc.original_filename

            # Resolve file path and calculate hash for filtering
            if not doc.file_path:
                logger.warning(f"Document {document_id} has no file_path, cannot filter by document")
            else:
                resolved_path = self._resolve_file_path(doc.file_path)
                if resolved_path:
                    file_hash = self._calculate_file_hash(resolved_path)
                    if file_hash:
                        # Store original hashes and replace with single document hash
                        original_hashes = self.rag_docs.hashes.copy() if hasattr(self.rag_docs, "hashes") and self.rag_docs.hashes else []
                        self.rag_docs.hashes = [file_hash]
                        logger.debug(f"Temporarily replaced hashes with [{file_hash}] for document {document_id}")
                    else:
                        logger.warning(f"Could not calculate file hash for document {document_id}, querying all documents")
                else:
                    logger.warning(f"Could not resolve file path for document {document_id}, querying all documents")

        try:
            # Query RAG (will use filtered hashes if document_id was provided and hash was calculated)
            results = await self.rag_docs.query(query, num_results=10)

            # Handle different return types from RAG
            # When return_raw=False (default), RAG returns formatted string
            # When return_raw=True, RAG returns list of NodeWithScore objects
            if isinstance(results, str):
                # Already formatted string
                content_text = results
            elif isinstance(results, list):
                # List of result objects - extract content
                content_text = "\n\n".join(
                    [
                        result.node.get_content()
                        if hasattr(result, "node") and hasattr(result.node, "get_content")
                        else (result.text if hasattr(result, "text") else str(result))
                        for result in results[:10]
                    ]
                )
            else:
                content_text = str(results)

            # Format results
            content = self._format_query_results(query, content_text, doc_name, document_id)

            return ToolResult(
                name="read_documents",
                result=content,
                require_user=False,
            )

        except Exception as e:
            logger.error(f"Error in _query_documents: {e}")
            return ToolResult(
                name="read_documents",
                result=f"❌ Error querying documents: {str(e)}",
                require_user=False,
            )
        finally:
            # Always restore original hashes if they were replaced
            if original_hashes is not None and hasattr(self.rag_docs, "hashes"):
                self.rag_docs.hashes = original_hashes
                logger.debug(f"Restored original hashes: {original_hashes}")

    def _format_query_results(self, query: str, content_text: str, doc_name: str | None, document_id: int | None) -> str:
        """Format query results for display."""
        content_parts = []

        # Header
        if document_id and doc_name:
            content_parts.append(f"## Query Results from: {doc_name}")
        elif document_id:
            content_parts.append(f"## Query Results (Document ID {document_id})")
        else:
            content_parts.append("## Query Results")

        content_parts.append("")
        content_parts.append(f"**Query**: {query}")
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

        # Content
        if content_text and content_text.strip():
            content_parts.append("### Relevant Content")
            content_parts.append("")
            content_parts.append(content_text)
        else:
            content_parts.append("### No Relevant Content Found")
            content_parts.append("")
            content_parts.append("*No content matching your query was found in the documents.*")

        return "\n".join(content_parts)


if __name__ == "__main__":
    import asyncio

    async def test_read_documents():
        """Test the ReadDocumentsTool with mock data."""
        print("🧪 Testing ReadDocumentsTool")
        print("=" * 40)

        # Create tool
        tool = ReadDocumentsTool(kp_id=8, rag_docs=None)

        print(f"✅ Tool created: {tool.tool_information.name}")
        print(f"   Description: {tool.tool_information.description}")
        print()
        print("Note: Actual execution requires database session and RAG")
        print("      Use this tool within the template handler context")

    asyncio.run(test_read_documents())
