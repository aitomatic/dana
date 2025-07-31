from typing import Any
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.tabular_index.tabluar_index import TabularIndex, TabularIndexConfig


class TabularIndexResource(BaseResource):
    """RAG resource for document retrieval."""

    def __init__(
        self,
        tabular_index_config: dict[str, Any],
        name: str = "tabular_index",
        description: str | None = None,
    ):
        super().__init__(name, description)

        self._tabular_index = TabularIndex(tabular_index_config=TabularIndexConfig(**tabular_index_config))
        self._is_ready = False

    async def initialize(self) -> None:
        """Initialize and preprocess sources."""
        await super().initialize()
        await self._tabular_index.load_tabular_index()
        self._is_ready = True

    async def retrieve(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Retrieve relevant documents."""
        if not self._is_ready:
            await self.initialize()

        return await self._tabular_index.retrieve(query, top_k)
