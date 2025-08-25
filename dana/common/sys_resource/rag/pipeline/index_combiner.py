"""
Index Combining Module

This module handles the combination of multiple vector indices into a unified index
while preserving embedding optimizations. It implements efficient merging of indices
without recomputing embeddings.

The IndexCombiner class is responsible for:
- Creating combined indices from existing indices without recomputing embeddings
- Optimizing embedding reuse during index combination
- Providing fallback mechanisms for robust index combination
"""

import asyncio
import json
from typing import cast

from llama_index.core import VectorStoreIndex, load_index_from_storage
from llama_index.core.data_structs import IndexDict
from llama_index.core.schema import Document
from llama_index.core.storage.storage_context import StorageContext
from dana.common.sys_resource.embedding import get_default_embedding_model
from dana.common.sys_resource.rag.pipeline.base_stage import BaseStage


class IndexCombiner(BaseStage):
    """Handles vector index combination only."""

    _NAME = "index_combiner"

    def __init__(self, **kwargs):
        """Initialize IndexCombiner.

        Args:
            **kwargs: Additional arguments passed to BaseStage
        """
        super().__init__(**kwargs)

    async def combine_indices(
        self, individual_indices: dict[str, VectorStoreIndex], docs_by_source: dict[str, list[Document]], embed_model: str | None = None
    ) -> VectorStoreIndex:
        """Create a combined index from individual indices without recomputing embeddings.

        This method extracts all nodes from individual indices and creates a new
        combined index that reuses the existing embeddings, providing significant
        performance benefits over recreating embeddings from scratch.

        Args:
            individual_indices: Dictionary of individual source indices
            docs_by_source: Original documents by source (fallback if node extraction fails)

        Returns:
            VectorStoreIndex that combines all individual indices with preserved embeddings

        Note:
            Falls back to document-based creation if node extraction fails,
            ensuring robustness while maintaining performance when possible.
        """
        combined_index = await self._create_combined_vector_store_index(individual_indices, embed_model=embed_model)

        if not combined_index:
            self.debug("Warning: No nodes collected, falling back to document-based approach")
            # Fallback: create from documents if node extraction fails
            all_documents = []
            for _source_key, documents in docs_by_source.items():
                all_documents.extend(documents)
            # Run the fallback index creation in a thread
            combined_index = await asyncio.to_thread(VectorStoreIndex.from_documents, all_documents, embed_model=embed_model)

        return combined_index

    async def _create_combined_vector_store_index(self, individual_indices: dict[str, VectorStoreIndex], embed_model: str | None = None) -> VectorStoreIndex | None:
        """Create combined vector store by merging existing vector stores."""

        def _recursive_update_inplace(dict1: dict, dict2: dict):
            for k, v in dict2.items():
                if k in dict1:
                    if isinstance(dict1[k], dict) and isinstance(v, dict):
                        _recursive_update_inplace(dict1[k], v)
                    else:
                        dict1[k] = v
                else:
                    dict1[k] = v

        combined_storage_context_dict = {}
        storage_context_cls = None
        combined_index_struct_dict = {}
        index_struct_cls = None

        for source_key, index in individual_indices.items():
            try:
                if storage_context_cls is None:
                    storage_context_cls = type(index.storage_context)
                storage_context_dict = index.storage_context.to_dict()
                _recursive_update_inplace(combined_storage_context_dict, storage_context_dict)
                if index_struct_cls is None:
                    index_struct_cls = type(index.index_struct)
                index_struct_dict = index.index_struct.to_dict()
                _recursive_update_inplace(combined_index_struct_dict, index_struct_dict)
            except Exception as e:
                self.debug(f"Error extracting nodes from source {source_key}: {str(e)}")
                continue

        # Merge multiple index stores into a single index store
        all_index_store_data = combined_storage_context_dict.get("index_store", {}).get("index_store/data", {})
        combined_index_store_data = {}
        combined_index_id = None
        for index_store_id, index_store_data in all_index_store_data.items():
            if not combined_index_id:
                combined_index_store_data[index_store_id] = index_store_data
                combined_index_id = index_store_id
            else:
                combined_data = json.loads(combined_index_store_data[combined_index_id]["__data__"])
                index_store_nodes_dict = json.loads(index_store_data["__data__"])["nodes_dict"]
                combined_data["nodes_dict"].update(index_store_nodes_dict)
                combined_index_store_data[combined_index_id]["__data__"] = json.dumps(combined_data)

        if combined_index_store_data:
            combined_storage_context_dict["index_store"]["index_store/data"] = combined_index_store_data

        if storage_context_cls is None:
            storage_context_cls = StorageContext

        if index_struct_cls is None:
            index_struct_cls = IndexDict

        return cast(VectorStoreIndex, load_index_from_storage(storage_context_cls.from_dict(combined_storage_context_dict), embed_model=embed_model))
