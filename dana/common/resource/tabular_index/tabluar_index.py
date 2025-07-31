from typing import Any
from collections.abc import Callable
import os
from pathlib import Path


class TabularIndexConfig:
    def __init__(
        self,
        cache_dir: str = ".cache/tabular_index",
        force_reload: bool = False,
        source: str = "",
        table_name: str = "my_tabular_index",
        embedding_field_constructor: Callable | None = None,
        metadata_constructor: Callable | None = None,
    ):
        self.cache_dir: str = cache_dir
        self.source: str = source
        danapath = os.environ.get("DANAPATH")
        if danapath:
            self.cache_dir = os.path.join(danapath, self.cache_dir)
            self.source = os.path.join(danapath, self.source)
        self.force_reload: bool = force_reload
        self.table_name: str = table_name
        self.metadata_constructor: Callable | None = metadata_constructor
        self.embedding_field_constructor: Callable | None = embedding_field_constructor
        # Validate source file extension
        self._validate_source()

    def _validate_source(self) -> None:
        """Validate that the source file is a CSV or Parquet file."""
        if not self.source:
            raise ValueError("Source file path cannot be empty")

        source_path = Path(self.source)
        valid_extensions = {".csv", ".parquet"}

        if source_path.suffix.lower() not in valid_extensions:
            raise ValueError(
                f"Source file must be a CSV or Parquet file. "
                f"Got '{source_path.suffix}' but expected one of: {', '.join(valid_extensions)}"
            )


class TabularIndex:
    def __init__(self, tabular_index_config: TabularIndexConfig):
        self.tabular_index_config: TabularIndexConfig = tabular_index_config

    async def load_tabular_index(self):
        print("loading tabular index")
        pass

    async def retrieve(self, query: str, num_results: int = 10) -> list[dict[str, Any]]:
        print("retrieving tabular index")
        return [{"a": 123}]
