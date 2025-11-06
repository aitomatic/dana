from datetime import datetime
import json
import os
from pathlib import Path

from dana.common.schemas import PromptVersionSnapshot
from dana.config.storage_config import FileStorageConfig

from .prompt_store_protocol import PromptStoreProtocol


"""
Store prompt for a SINGLE agent, resource, workflow, etc on Local disk.
"""

class LocalPromptStore(PromptStoreProtocol):
    def __init__(self, config : FileStorageConfig):
        self._config = config
        self._workspace_folder = Path(self._config.workspace_folder)
        self._workspace_folder.mkdir(parents=True, exist_ok=True)
        self._version = None

    def version_exists(self) -> bool:
        return len(self.list_versions()) > 0

    @property
    def version(self) -> str:
        if self._version is None:
            self._version = self._get_current_version()
            self._persist_version(self._version)
        return self._version

    def get_active(self, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        if not error_if_not_found:
            if not self.version_exists(): # Because error_if_not_found = False -> We check if version exists to return None instead of raising an error
                return None
        return self.load_snapshot(self.version, error_if_not_found)

    def list_versions(self) -> list[str]:
        def _filter(item: str) -> bool:
            return item.startswith("v") and item[1:].isdigit()
        versions_folder = self._workspace_folder / "versions"
        if not versions_folder.exists():
            return []
        items = [_path.stem for _path in versions_folder.iterdir()]
        return sorted([item for item in items if _filter(item)], key=lambda x: int(x.split("v")[1]))

    def load_snapshot(self, version: str, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        try:
            versions_folder = self._workspace_folder / "versions"
            versions_folder.mkdir(parents=True, exist_ok=True)
            content_file = self._workspace_folder / "versions" / f"{version}.prompt"
            created_at = os.path.getctime(content_file)
            updated_at = os.path.getmtime(content_file)
            content = content_file.read_text()
            return PromptVersionSnapshot(
                version=version,
                content=content,
                created_at=datetime.fromtimestamp(created_at),
                updated_at=datetime.fromtimestamp(updated_at),
                provenance=self._load_provenances().get(version, {}),
                metrics=self._load_metrics().get(version, {}),
            )
        except ValueError:
            if error_if_not_found:
                raise ValueError(f"Version {version} not found")
            return None

    def _load_provenances(self) -> dict:
        provenance_file = self._workspace_folder / "provenance.json"
        if provenance_file.exists():
            return json.loads(provenance_file.read_text())
        return {}

    def _load_metrics(self) -> dict:
        metrics_file = self._workspace_folder / "metrics.json"
        if metrics_file.exists():
            return json.loads(metrics_file.read_text())
        return {}

    def set_active(self, version: str) -> None:
        self._version = version
        self._persist_version(version)

    def create_snapshot(self, content: str, provenance: dict, metrics: dict) -> PromptVersionSnapshot:
        try:
            current_version = self._get_latest_version()
            new_version_number = int(current_version.split("v")[1]) + 1
            version = f"v{new_version_number}"
        except ValueError:
            version = "v1"
        versions_folder = self._workspace_folder / "versions"
        versions_folder.mkdir(parents=True, exist_ok=True)
        content_file = versions_folder / f"{version}.prompt"
        provenances = self._load_provenances()
        provenances[version] = provenance
        metrics_dict = self._load_metrics()
        metrics_dict[version] = metrics
        content_file.write_text(content)
        provenance_file = self._workspace_folder / "provenance.json"
        metrics_file = self._workspace_folder / "metrics.json"
        provenance_file.write_text(json.dumps(provenances, indent=4))
        metrics_file.write_text(json.dumps(metrics_dict, indent=4))
        return PromptVersionSnapshot(
            version=version,
            content=content,
            created_at=datetime.fromtimestamp(os.path.getctime(content_file)),
            updated_at=datetime.fromtimestamp(os.path.getmtime(content_file)),
            provenance=provenance,
            metrics=metrics,
        )
    
    @property
    def _version_file(self) -> Path:
        return self._workspace_folder / "version.txt"

    def _get_current_version(self) -> str:
        if self._version_file.exists():
            return self._version_file.read_text()
        return self._get_latest_version()

    def _get_latest_version(self) -> str:
        versions = self.list_versions()
        if versions:
            return versions[-1]
        raise ValueError("No versions found")

    def _persist_version(self, version: str) -> None:
        self._version_file.write_text(version)
