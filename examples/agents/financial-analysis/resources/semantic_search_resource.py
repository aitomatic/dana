"""
Semantic Search Resource for Financial Analysis Agent.

Provides semantic code search capabilities using RAGResourceV2.
"""

from pathlib import Path
from typing import Optional

from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2, CACHE_DIR
from dana.core.resource.base_resource import BaseResource
from dana.lang.common.utils.misc import Misc
from llama_index.core.schema import MetadataMode
from dana.common.protocols.war import tool_use


class SemanticSearchResource(BaseResource):
    """
    Semantic search resource for finding relevant documents in the workspace.
    
    Uses RAGResourceV2 for vector-based semantic search across the workspace.
    Returns results without line number information (RAG works on document chunks).
    """

    def __init__(
        self,
        workspace_root: str,
        name: str = "semantic_search",
        description: Optional[str] = None,
        debug: bool = False,
        chunk_size: int = 1024,
        chunk_overlap: int = 256,
        **kwargs
    ):
        """
        Initialize SemanticSearchResource.
        
        Args:
            workspace_root: Root directory to index and search
            name: Resource name
            description: Resource description
            debug: Enable debug logging
            chunk_size: Size of text chunks for indexing
            chunk_overlap: Overlap between chunks
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(name=name, description=description, **kwargs)
        
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.debug = debug
        
        if self.debug:
            print(f"SemanticSearchResource initialized with workspace_root: {self.workspace_root}")
        
        # Initialize RAGResourceV2 for semantic search
        self._rag = RAGResourceV2(
            sources=[str(self.workspace_root)],
            name=f"{name}_rag",
            return_raw=True,  # Return raw NodeWithScore objects
            debug=debug,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            reranking=False,  # Disable reranking for faster results
        )

    @tool_use
    def search(self, query: str, top_k: int = 10) -> dict:
        """
        Perform semantic search across the workspace.
        
        Args:
            query: Natural language search query
            top_k: Maximum number of results to return
            
        Returns:
            Dictionary with format:
            {
                "results": [
                    {
                        "file_path": str,  # Path to file
                        "content": str,    # Matching content
                        "score": float     # Similarity score
                    }
                ]
            }
            
            Or on error:
            {
                "results": [],
                "error": str
            }
        """
        try:
            if self.debug:
                print(f"Semantic search query: '{query}' (top_k={top_k})")
            
            # Call RAG query (handles async internally)
            results = Misc.safe_asyncio_run(self._rag.query, query, num_results=top_k)
            
            # Check if RAG is available
            if not self._rag.is_available:
                if self.debug:
                    print("RAG index is not available or empty")
                return {
                    "results": [],
                    "error": "Semantic search index is not available"
                }
            
            # Transform results to expected format
            formatted_results = []
            
            # Handle case where results might be a string (no results)
            if isinstance(results, str):
                if self.debug:
                    print(f"RAG returned string: {results}")
                return {"results": []}
            
            # Process results
            for result in results:
                try:
                    # Extract metadata
                    metadata = result.node.metadata
                    file_path = metadata.get('file_path') or metadata.get('source', 'unknown')
                    
                    # Get content without metadata
                    content = result.node.get_content(MetadataMode.NONE)
                    
                    # Get score
                    score = result.score if hasattr(result, 'score') else 0.0
                    
                    formatted_results.append({
                        "file_path": file_path,
                        "content": content,
                        "score": float(score)
                    })
                except Exception as e:
                    if self.debug:
                        print(f"Error processing result: {e}")
                    continue
            
            if self.debug:
                print(f"Semantic search found {len(formatted_results)} results")
            
            return {"results": formatted_results}
            
        except Exception as e:
            error_msg = f"Semantic search failed: {str(e)}"
            if self.debug:
                print(error_msg)
                import traceback
                traceback.print_exc()
            return {
                "results": [],
                "error": error_msg
            }

    @property
    def is_available(self) -> bool:
        """Check if semantic search is available."""
        try:
            return self._rag.is_available
        except Exception:
            return False


if __name__ == "__main__":
    """
    Demo usage of SemanticSearchResource.
    
    Run this script to test semantic search functionality.
    """
    import sys
    
    # Get workspace root from command line or use current directory
    workspace_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print("=" * 80)
    print("SemanticSearchResource Demo")
    print("=" * 80)
    print()
    
    # Initialize resource
    print(f"Initializing semantic search for: {workspace_root}")
    resource = SemanticSearchResource(
        workspace_root="examples/agents/financial-analysis/data",
        debug=True
    )
    
    print(f"Is available: {resource.is_available}")
    print()
    
    # Test search
    test_query = "financial analysis calculations ratios"
    print(f"Searching for: '{test_query}'")
    print("-" * 80)
    
    results = resource.search(test_query, top_k=5)
    
    if results.get("error"):
        print(f"Error: {results['error']}")
    else:
        print(f"Found {len(results['results'])} results:\n")
        for i, result in enumerate(results["results"], 1):
            print(f"Result {i}:")
            print(f"  File: {result['file_path']}")
            print(f"  Score: {result['score']:.4f}")
            print(f"  Content preview: {result['content'][:150]}...")
            print()
