"""
Unit tests for LocalPromptStore.

Tests the local file-based prompt version storage functionality.
"""

from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import MagicMock

import pytest


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

# Now import normally
from dana.config.storage_config import FileStorageConfig
from dana.core.knowledge.prompts.stores.local_prompt_store import LocalPromptStore


class TestLocalPromptStoreInitialization:
    """Test LocalPromptStore initialization."""

    def test_initialization_with_valid_config_creates_workspace_folder(self):
        """Test initialization with valid config creates workspace folder."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            assert Path(temp_dir).exists()
            assert Path(temp_dir).is_dir()
            assert store._workspace_folder == Path(temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_with_nested_path_creates_parent_directories(self):
        """Test initialization with nested path creates parent directories."""
        temp_dir = tempfile.mkdtemp()
        try:
            nested_path = Path(temp_dir) / "nested" / "path" / "to" / "workspace"
            config = FileStorageConfig(workspace_folder=str(nested_path))
            store = LocalPromptStore(config)
            
            assert nested_path.exists()
            assert nested_path.is_dir()
            assert store._workspace_folder == nested_path
        finally:
            shutil.rmtree(temp_dir)

    def test_version_is_none_after_initialization(self):
        """Test _version is None after initialization."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            assert store._version is None
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptStoreVersion:
    """Test LocalPromptStore version property."""

    def test_version_property_lazy_loads_when_not_set(self):
        """Test version property lazy loads when not set."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a version file
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            version_file = Path(temp_dir) / "versions" / "v1.prompt"
            version_file.write_text("Test content")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            # Initially _version should be None
            assert store._version is None
            
            # Accessing version property should trigger lazy loading
            version = store.version
            assert version is not None
            assert store._version is not None
        finally:
            shutil.rmtree(temp_dir)

    def test_version_reads_from_version_txt_if_exists(self):
        """Test version reads from version.txt if exists."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create version.txt file
            version_txt = Path(temp_dir) / "version.txt"
            version_txt.write_text("v2")
            
            # Create corresponding version file
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            version_file = versions_dir / "v2.prompt"
            version_file.write_text("Test content")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            assert store.version == "v2"
        finally:
            shutil.rmtree(temp_dir)

    def test_version_falls_back_to_latest_version_if_version_txt_doesnt_exist(self):
        """Test version falls back to latest version if version.txt doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create multiple version files
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            
            # Create v1 and v3 (v2 missing to test sorting)
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "v3.prompt").write_text("Content 3")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            # Should return latest version (v3) when version.txt doesn't exist
            assert store.version == "v3"
        finally:
            shutil.rmtree(temp_dir)

    def test_version_persists_to_version_txt_on_first_access(self):
        """Test version persists to version.txt on first access."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create version file
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Test content")
            
            version_txt = Path(temp_dir) / "version.txt"
            assert not version_txt.exists()
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            # Access version property
            _ = store.version
            
            # version.txt should now exist with the version
            assert version_txt.exists()
            assert version_txt.read_text().strip() == "v1"
        finally:
            shutil.rmtree(temp_dir)

    def test_version_property_returns_cached_value_after_first_access(self):
        """Test version property returns cached value after first access."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create version file
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Test content")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            # First access
            version1 = store.version
            # Second access should return same value (cached)
            version2 = store.version
            
            assert version1 == version2
            assert version1 == "v1"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptStoreCreateSnapshot:
    """Test LocalPromptStore create_snapshot method."""

    def test_create_snapshot_creates_first_version_when_no_versions_exist(self):
        """Test create_snapshot creates first version (v1) when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.create_snapshot(
                content="Test prompt content",
                provenance={"source": "test"},
                metrics={"score": 0.95}
            )
            
            assert snapshot.version == "v1"
            assert snapshot.content == "Test prompt content"
            
            # Verify file was created
            version_file = Path(temp_dir) / "versions" / "v1.prompt"
            assert version_file.exists()
            assert version_file.read_text() == "Test prompt content"
        finally:
            shutil.rmtree(temp_dir)

    def test_create_snapshot_increments_version_number_from_existing_versions(self):
        """Test create_snapshot increments version number from existing versions."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create initial version
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.create_snapshot(
                content="Content 2",
                provenance={"source": "test"},
                metrics={"score": 0.96}
            )
            
            assert snapshot.version == "v2"
            
            # Verify new file was created
            version_file = Path(temp_dir) / "versions" / "v2.prompt"
            assert version_file.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_create_snapshot_writes_content_to_version_file(self):
        """Test create_snapshot writes content to versions/{version}.prompt file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            content = "This is a test prompt content"
            snapshot = store.create_snapshot(
                content=content,
                provenance={},
                metrics={}
            )
            
            version_file = Path(temp_dir) / "versions" / f"{snapshot.version}.prompt"
            assert version_file.exists()
            assert version_file.read_text() == content
        finally:
            shutil.rmtree(temp_dir)

    def test_create_snapshot_saves_provenance_and_metrics_to_json_files(self):
        """Test create_snapshot saves provenance and metrics to JSON files."""
        import json
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            provenance = {"source": "test", "author": "unit_test"}
            metrics_input = {"score": 0.95, "quality": "high"}
            
            snapshot = store.create_snapshot(
                content="Test content",
                provenance=provenance,
                metrics=metrics_input
            )
            
            # Verify provenance.json
            provenance_file = Path(temp_dir) / "provenance.json"
            assert provenance_file.exists()
            provenances = json.loads(provenance_file.read_text())
            assert snapshot.version in provenances
            assert provenances[snapshot.version] == provenance
            
            # Verify metrics.json
            metrics_file = Path(temp_dir) / "metrics.json"
            assert metrics_file.exists()
            metrics_dict = json.loads(metrics_file.read_text())
            assert snapshot.version in metrics_dict
            assert metrics_dict[snapshot.version] == metrics_input
        finally:
            shutil.rmtree(temp_dir)

    def test_create_snapshot_returns_prompt_version_snapshot_with_correct_fields(self):
        """Test create_snapshot returns PromptVersionSnapshot with correct fields."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            provenance = {"source": "test"}
            metrics = {"score": 0.95}
            
            snapshot = store.create_snapshot(
                content="Test content",
                provenance=provenance,
                metrics=metrics
            )
            
            assert snapshot.version == "v1"
            assert snapshot.content == "Test content"
            assert snapshot.provenance == provenance
            assert snapshot.metrics == metrics
            assert snapshot.created_at is not None
            assert snapshot.updated_at is not None
        finally:
            shutil.rmtree(temp_dir)

    def test_create_snapshot_handles_file_creation_timestamps_correctly(self):
        """Test create_snapshot handles file creation timestamps correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.create_snapshot(
                content="Test content",
                provenance={},
                metrics={}
            )
            
            # Verify timestamps are set
            assert snapshot.created_at is not None
            assert snapshot.updated_at is not None
            # Timestamps should be datetime objects
            from datetime import datetime
            assert isinstance(snapshot.created_at, datetime)
            assert isinstance(snapshot.updated_at, datetime)
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptStoreListVersions:
    """Test LocalPromptStore list_versions method."""

    def test_list_versions_returns_empty_list_when_no_versions_exist(self):
        """Test list_versions returns empty list when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            versions = store.list_versions()
            
            assert versions == []
        finally:
            shutil.rmtree(temp_dir)

    def test_list_versions_returns_sorted_list_of_version_strings(self):
        """Test list_versions returns sorted list of version strings."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create version files in non-sorted order
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v3.prompt").write_text("Content 3")
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "v2.prompt").write_text("Content 2")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            versions = store.list_versions()
            
            assert versions == ["v1", "v2", "v3"]
        finally:
            shutil.rmtree(temp_dir)

    def test_list_versions_filters_out_non_version_files(self):
        """Test list_versions filters out non-version files."""
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "invalid.prompt").write_text("Invalid")
            (versions_dir / "v2.prompt").write_text("Content 2")
            (versions_dir / "readme.txt").write_text("Readme")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            versions = store.list_versions()
            
            assert versions == ["v1", "v2"]
            assert "invalid" not in versions
            assert "readme" not in versions
        finally:
            shutil.rmtree(temp_dir)

    def test_list_versions_handles_versions_folder_not_existing(self):
        """Test list_versions handles versions folder not existing."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            versions = store.list_versions()
            
            assert versions == []
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptStoreLoadSnapshot:
    """Test LocalPromptStore load_snapshot method."""

    def test_load_snapshot_loads_content_from_version_file(self):
        """Test load_snapshot loads content from version file."""
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            content = "This is test prompt content"
            (versions_dir / "v1.prompt").write_text(content)
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.load_snapshot("v1")
            
            assert snapshot.version == "v1"
            assert snapshot.content == content
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_includes_provenance_from_json_file(self):
        """Test load_snapshot includes provenance from JSON file."""
        import json
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content")
            
            provenance = {"source": "test", "author": "unit_test"}
            provenance_file = Path(temp_dir) / "provenance.json"
            provenance_file.write_text(json.dumps({"v1": provenance}, indent=4))
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.load_snapshot("v1")
            
            assert snapshot.provenance == provenance
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_includes_metrics_from_json_file(self):
        """Test load_snapshot includes metrics from JSON file."""
        import json
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content")
            
            metrics = {"score": 0.95, "quality": "high"}
            metrics_file = Path(temp_dir) / "metrics.json"
            metrics_file.write_text(json.dumps({"v1": metrics}, indent=4))
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.load_snapshot("v1")
            
            assert snapshot.metrics == metrics
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_uses_file_timestamps_for_created_at_updated_at(self):
        """Test load_snapshot uses file timestamps for created_at/updated_at."""
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            version_file = versions_dir / "v1.prompt"
            version_file.write_text("Content")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.load_snapshot("v1")
            
            assert snapshot.created_at is not None
            assert snapshot.updated_at is not None
            from datetime import datetime
            assert isinstance(snapshot.created_at, datetime)
            assert isinstance(snapshot.updated_at, datetime)
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_handles_missing_provenance_metrics_gracefully(self):
        """Test load_snapshot handles missing provenance/metrics gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.load_snapshot("v1")
            
            assert snapshot.provenance == {}
            assert snapshot.metrics == {}
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptStoreSetActive:
    """Test LocalPromptStore set_active method."""

    def test_set_active_updates_internal_version(self):
        """Test set_active updates internal _version."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            store.set_active("v2")
            
            assert store._version == "v2"
        finally:
            shutil.rmtree(temp_dir)

    def test_set_active_persists_version_to_version_txt_file(self):
        """Test set_active persists version to version.txt file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            store.set_active("v3")
            
            version_file = Path(temp_dir) / "version.txt"
            assert version_file.exists()
            assert version_file.read_text().strip() == "v3"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptStoreGetActive:
    """Test LocalPromptStore get_active method."""

    def test_get_active_returns_snapshot_of_current_version(self):
        """Test get_active returns snapshot of current version."""
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "v2.prompt").write_text("Content 2")
            
            # Set version.txt to v2
            version_file = Path(temp_dir) / "version.txt"
            version_file.write_text("v2")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.get_active()
            
            assert snapshot.version == "v2"
            assert snapshot.content == "Content 2"
        finally:
            shutil.rmtree(temp_dir)

    def test_get_active_uses_version_property_to_determine_active_version(self):
        """Test get_active uses version property to determine active version."""
        temp_dir = tempfile.mkdtemp()
        try:
            versions_dir = Path(temp_dir) / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            snapshot = store.get_active()
            
            # Should use latest version when no version.txt exists
            assert snapshot.version == "v1"
            assert snapshot.content == "Content 1"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptStoreEdgeCases:
    """Test LocalPromptStore edge cases."""

    def test_get_latest_version_raises_value_error_when_no_versions_exist(self):
        """Test _get_latest_version raises ValueError when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            with pytest.raises(ValueError, match="No versions found"):
                store._get_latest_version()
        finally:
            shutil.rmtree(temp_dir)

    def test_version_property_raises_value_error_when_no_versions_and_no_version_txt(self):
        """Test version property raises ValueError when no versions and no version.txt."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            with pytest.raises(ValueError, match="No versions found"):
                _ = store.version
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_raises_error_when_version_file_doesnt_exist(self):
        """Test load_snapshot raises appropriate error when version file doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            store = LocalPromptStore(config)
            
            # Should raise FileNotFoundError when trying to read non-existent file
            with pytest.raises(FileNotFoundError):
                store.load_snapshot("v99")
        finally:
            shutil.rmtree(temp_dir)

