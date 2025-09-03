from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import (
    MetadataFilters,
)
from dana.common.sys_resource.embedding import get_default_embedding_model


class Retriever:
    def __init__(self, index: VectorStoreIndex, embed_model = None, **kwargs) -> None:
        self._index = index
        self._embedding_model = embed_model if embed_model else get_default_embedding_model()


    @classmethod
    def from_index(cls, index: VectorStoreIndex, embed_model: str | None = None, **kwargs) -> "Retriever":
        return cls(index, embed_model=embed_model, **kwargs)

    def retrieve(self, query: str, num_results: int = 10) -> list[NodeWithScore]:
        return self._index.as_retriever(similarity_top_k=num_results, embed_model=self._embedding_model).retrieve(query)

    async def aretrieve(self, query: str, num_results: int = 10) -> list[NodeWithScore]:
        return await self._index.as_retriever(similarity_top_k=num_results, embed_model=self._embedding_model).aretrieve(query)

    async def aretrieve_with_filters(
        self, query: str, num_results: int = 10, filters: MetadataFilters | None = None
    ) -> list[NodeWithScore]:
        if filters is None:
            return await self.aretrieve(query, num_results)
        return await self._index.as_retriever(similarity_top_k=num_results, filters=filters, embed_model=self._embedding_model).aretrieve(query)

    def get_all_filenames(self) -> list[str]:
        """Get all filenames from the index.

        Returns:
            List of unique filenames found in the index.
        """
        filenames = set()

        try:
            # Access the document store to get all nodes
            docstore = self._index.storage_context.docstore

            # Get all node IDs from the index structure
            node_ids = list(self._index.index_struct.nodes_dict.keys())

            # Extract filenames from node metadata
            for node_id in node_ids:
                node = docstore.get_node(node_id)
                if node and node.metadata:
                    # Check for common filename metadata keys
                    filename = (
                        node.metadata.get("filename")
                        or node.metadata.get("file_name")
                        or node.metadata.get("source")
                        or node.metadata.get("file_path")
                    )
                    if filename:
                        filenames.add(filename)

            return sorted(list(filenames))

        except Exception:
            # If we can't access the document store, try alternative approach
            try:
                # Use a broad query to get all nodes and extract filenames
                all_nodes = self._index.as_retriever(similarity_top_k=1000, embed_model=self._embedding_model).retrieve("")
                filenames = set()

                for node in all_nodes:
                    if node.metadata:
                        filename = (
                            node.metadata.get("filename")
                            or node.metadata.get("file_name")
                            or node.metadata.get("source")
                            or node.metadata.get("file_path")
                        )
                        if filename:
                            filenames.add(filename)

                return sorted(list(filenames))

            except Exception:
                # If all else fails, return empty list
                return []
