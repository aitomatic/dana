from opendxa.contrib.dana_rag.common.resource.storage.rag_store import RAGStore

from opendxa.common.resource import BaseResource
from opendxa.common.mixins.tool_callable import ToolCallable
from typing import Dict, Any, Union, List
from pathlib import Path

class RAGResource(BaseResource):
    """Resource for RAG-based retrieval using both BM25 and VectorStore retrievers."""
    COUNT = 0

    def __init__(
        self,
        doc_paths: List[str] = ['proposal/data/data_for_usecases/semiconductor/mock-docs'],
        output_folder: str = 'proposal/data/dana/storage',
        use_chunking: bool = True,
        enable_print: bool = False,
        force_reload: bool = False,
        **kwargs
    ):
        self.COUNT += 1
        if kwargs.get("name") is None:
            kwargs["name"] = f"rag{self.COUNT}"
        super().__init__(**kwargs)
        self.enable_print = enable_print
        
        # Convert doc_paths to list if it's a string
        self.doc_paths = doc_paths
            
        self.output_folder = output_folder
        self.doc_store = RAGStore(doc_paths=self.doc_paths, output_folder=self.output_folder, use_chunking=use_chunking, enable_print=enable_print, force_reload=force_reload)

    @ToolCallable.tool
    async def retrieve(self, query:str, num_results:int = 10) -> str:
        """Query Documents or any kind of data sources for relevant information"""
        results = await self.doc_store._manual_retrieve(query, num_results=num_results)
        return "\n".join([result for result in results])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given name and arguments, validating arguments first."""
        if not hasattr(self, tool_name):
            raise ValueError(f"Tool {tool_name} not found in {self.__class__.__name__}")
        func = getattr(self, tool_name)
        return await func(**arguments)
    
    async def query(self, query: str) -> None: #NOTE : MUST HAVE. BUT NOT USED.
        pass

    def check_supported_type(self, path: str) -> bool:
        _path = Path(path)
        return _path.suffix in RAGStore.SUPPORTED_TYPES
    
if __name__ == "__main__":
    rag_resource = RAGStore(doc_paths=["https://obc.lbl.gov/specification/cdl.html"], output_folder="proposal/data/dana/storage", use_chunking=True, enable_print=True, force_reload=True)
    import asyncio
    print(asyncio.run(rag_resource.retrieve("CDL specification")))