"""
Unit tests for LocalPromptRepository.

Tests the local file-based prompt repository with agent/component binding.
"""

from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, Mock

import pytest


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

# Now import normally
from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.core.resource import BaseResource
from dana.core.workflow import BaseWorkflow
from dana.repositories.local_file_repository import LocalPromptRepository


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        # Mock codec
        self._codec = Mock()
        self._codec.__qualname__ = "TestCodec"


class MockResource(BaseResource):
    """Mock resource for testing."""

    def __init__(self, **kwargs):
        super().__init__(resource_type="test_resource", auto_register=False, **kwargs)


class MockWorkflow(BaseWorkflow):
    """Mock workflow for testing."""

    def __init__(self, **kwargs):
        super().__init__(workflow_type="test_workflow", auto_register=False, **kwargs)


class TestLocalPromptRepositoryInitialization:
    """Test LocalPromptRepository initialization."""

    def test_initialization_with_agent_and_component_creates_workspace_folder(self):
        """Test initialization with agent and component creates workspace folder."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            component = MockResource()
            repository = LocalPromptRepository(config, agent, component)

            assert Path(temp_dir).exists()
            assert Path(temp_dir).is_dir()
            assert repository._workspace_folder == Path(temp_dir)
            assert repository._agent == agent
            assert repository._component == component
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_with_agent_only_creates_workspace_folder(self):
        """Test initialization with agent only (component=None) creates workspace folder."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent, component=None)

            assert Path(temp_dir).exists()
            assert Path(temp_dir).is_dir()
            assert repository._workspace_folder == Path(temp_dir)
            assert repository._agent == agent
            assert repository._component is None
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_with_nested_path_creates_parent_directories(self):
        """Test initialization with nested path creates parent directories."""
        temp_dir = tempfile.mkdtemp()
        try:
            nested_path = Path(temp_dir) / "nested" / "path" / "to" / "workspace"
            config = FileStorageConfig(workspace_folder=str(nested_path))
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            assert nested_path.exists()
            assert nested_path.is_dir()
            assert repository._workspace_folder == nested_path
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositoryPathResolution:
    """Test LocalPromptRepository path resolution."""

    def test_path_resolution_for_agent_only_uses_system_prompt_template(self):
        """Test path resolution for agent only uses system_prompt_template path."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent, component=None)

            path = repository._get_relative_prompt_path()

            expected_path = Path(temp_dir) / "TestCodec" / "MockAgent" / "prompts" / "system_prompt_template"
            assert path == expected_path
            assert path.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_path_resolution_for_agent_and_resource(self):
        """Test path resolution for agent and resource."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            component = MockResource()
            repository = LocalPromptRepository(config, agent, component)

            path = repository._get_relative_prompt_path()

            expected_path = Path(temp_dir) / "TestCodec" / "MockAgent" / "prompts" / "resources" / "MockResource"
            assert path == expected_path
            assert path.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_path_resolution_for_agent_and_workflow(self):
        """Test path resolution for agent and workflow."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            component = MockWorkflow()
            repository = LocalPromptRepository(config, agent, component)

            path = repository._get_relative_prompt_path()

            expected_path = Path(temp_dir) / "TestCodec" / "MockAgent" / "prompts" / "workflows" / "MockWorkflow"
            assert path == expected_path
            assert path.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_path_resolution_for_agent_and_nested_agent(self):
        """Test path resolution for agent and nested agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            nested_agent = MockAgent()
            repository = LocalPromptRepository(config, agent, nested_agent)

            path = repository._get_relative_prompt_path()

            expected_path = Path(temp_dir) / "TestCodec" / "MockAgent" / "prompts" / "agents" / "MockAgent"
            assert path == expected_path
            assert path.exists()
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositoryHasAnyVersions:
    """Test LocalPromptRepository has_any_versions method."""

    def test_has_any_versions_returns_false_when_no_versions_exist(self):
        """Test has_any_versions returns False when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            assert repository.has_any_versions() is False
        finally:
            shutil.rmtree(temp_dir)

    def test_has_any_versions_returns_true_when_versions_exist(self):
        """Test has_any_versions returns True when versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            # Create a version file
            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Test content")

            assert repository.has_any_versions() is True
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositoryListVersions:
    """Test LocalPromptRepository list_versions method."""

    def test_list_versions_returns_empty_list_when_no_versions_exist(self):
        """Test list_versions returns empty list when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            versions = repository.list_versions()

            assert versions == []
        finally:
            shutil.rmtree(temp_dir)

    def test_list_versions_returns_sorted_list_of_version_strings(self):
        """Test list_versions returns sorted list of version strings."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            # Create version files in non-sorted order
            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v3.prompt").write_text("Content 3")
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "v2.prompt").write_text("Content 2")

            versions = repository.list_versions()

            assert versions == ["v1", "v2", "v3"]
        finally:
            shutil.rmtree(temp_dir)

    def test_list_versions_filters_out_non_version_files(self):
        """Test list_versions filters out non-version files."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "invalid.prompt").write_text("Invalid")
            (versions_dir / "v2.prompt").write_text("Content 2")
            (versions_dir / "readme.txt").write_text("Readme")

            versions = repository.list_versions()

            assert versions == ["v1", "v2"]
            assert "invalid" not in versions
            assert "readme" not in versions
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositoryCreateSnapshot:
    """Test LocalPromptRepository create_snapshot method."""

    def test_create_snapshot_creates_first_version_when_no_versions_exist(self):
        """Test create_snapshot creates first version (v1) when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            snapshot = repository.create_snapshot(content="Test prompt content", provenance={"source": "test"}, metrics={"score": 0.95})

            assert snapshot.version == "v1"
            assert snapshot.content == "Test prompt content"

            # Verify file was created
            path = repository._get_relative_prompt_path()
            version_file = path / "versions" / "v1.prompt"
            assert version_file.exists()
            assert version_file.read_text() == "Test prompt content"
        finally:
            shutil.rmtree(temp_dir)

    def test_create_snapshot_increments_version_number_from_existing_versions(self):
        """Test create_snapshot increments version number from existing versions."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            # Create initial version
            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")

            snapshot = repository.create_snapshot(content="Content 2", provenance={"source": "test"}, metrics={"score": 0.96})

            assert snapshot.version == "v2"

            # Verify new file was created
            version_file = path / "versions" / "v2.prompt"
            assert version_file.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_create_snapshot_saves_provenance_and_metrics_to_json_files(self):
        """Test create_snapshot saves provenance and metrics to JSON files."""
        import json

        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            provenance = {"source": "test", "author": "unit_test"}
            metrics_input = {"score": 0.95, "quality": "high"}

            snapshot = repository.create_snapshot(content="Test content", provenance=provenance, metrics=metrics_input)

            path = repository._get_relative_prompt_path()

            # Verify provenance.json
            provenance_file = path / "provenance.json"
            assert provenance_file.exists()
            provenances = json.loads(provenance_file.read_text())
            assert snapshot.version in provenances
            assert provenances[snapshot.version] == provenance

            # Verify metrics.json
            metrics_file = path / "metrics.json"
            assert metrics_file.exists()
            metrics_dict = json.loads(metrics_file.read_text())
            assert snapshot.version in metrics_dict
            assert metrics_dict[snapshot.version] == metrics_input
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositoryLoadSnapshot:
    """Test LocalPromptRepository load_snapshot method."""

    def test_load_snapshot_loads_content_from_version_file(self):
        """Test load_snapshot loads content from version file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            content = "This is test prompt content"
            (versions_dir / "v1.prompt").write_text(content)

            snapshot = repository.load_snapshot("v1")

            assert snapshot.version == "v1"
            assert snapshot.content == content
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_includes_provenance_from_json_file(self):
        """Test load_snapshot includes provenance from JSON file."""
        import json

        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content")

            provenance = {"source": "test", "author": "unit_test"}
            provenance_file = path / "provenance.json"
            provenance_file.write_text(json.dumps({"v1": provenance}, indent=4))

            snapshot = repository.load_snapshot("v1")

            assert snapshot.provenance == provenance
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_handles_missing_provenance_metrics_gracefully(self):
        """Test load_snapshot handles missing provenance/metrics gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content")

            snapshot = repository.load_snapshot("v1")

            assert snapshot.provenance == {}
            assert snapshot.metrics == {}
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositoryGetActive:
    """Test LocalPromptRepository get_active method."""

    def test_get_active_returns_snapshot_of_current_version(self):
        """Test get_active returns snapshot of current version."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "v2.prompt").write_text("Content 2")

            # Set version.txt to v2
            version_file = path / "version.txt"
            version_file.write_text("v2")

            snapshot = repository.get_active()

            assert snapshot.version == "v2"
            assert snapshot.content == "Content 2"
        finally:
            shutil.rmtree(temp_dir)

    def test_get_active_uses_latest_version_when_no_version_txt_exists(self):
        """Test get_active uses latest version when no version.txt exists."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")

            snapshot = repository.get_active()

            # Should use latest version when no version.txt exists
            assert snapshot.version == "v1"
            assert snapshot.content == "Content 1"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositorySetActiveVersion:
    """Test LocalPromptRepository set_active_version method."""

    def test_set_active_version_persists_version_to_version_txt_file(self):
        """Test set_active_version persists version to version.txt file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "v2.prompt").write_text("Content 2")

            repository.set_active_version("v2")

            version_file = path / "version.txt"
            assert version_file.exists()
            assert version_file.read_text().strip() == "v2"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptRepositoryCompatibilityMethods:
    """Test LocalPromptRepository compatibility methods for store interface."""

    def test_get_active_with_error_if_not_found_true_raises_when_no_versions(self):
        """Test get_active(error_if_not_found=True) raises error when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            with pytest.raises(ValueError, match="No versions found"):
                repository.get_active(error_if_not_found=True)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_active_with_error_if_not_found_false_returns_none_when_no_versions(self):
        """Test get_active(error_if_not_found=False) returns None when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            result = repository.get_active(error_if_not_found=False)

            assert result is None
        finally:
            shutil.rmtree(temp_dir)

    def test_get_active_with_error_if_not_found_false_returns_snapshot_when_versions_exist(self):
        """Test get_active(error_if_not_found=False) returns snapshot when versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")

            result = repository.get_active(error_if_not_found=False)

            assert result is not None
            assert result.version == "v1"
            assert result.content == "Content 1"
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_with_error_if_not_found_true_raises_when_version_not_found(self):
        """Test load_snapshot(error_if_not_found=True) raises error when version not found."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            with pytest.raises(ValueError, match="Version v99 not found"):
                repository.load_snapshot("v99", error_if_not_found=True)
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_with_error_if_not_found_false_returns_none_when_version_not_found(self):
        """Test load_snapshot(error_if_not_found=False) returns None when version not found."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            result = repository.load_snapshot("v99", error_if_not_found=False)

            assert result is None
        finally:
            shutil.rmtree(temp_dir)

    def test_load_snapshot_with_error_if_not_found_false_returns_snapshot_when_version_exists(self):
        """Test load_snapshot(error_if_not_found=False) returns snapshot when version exists."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")

            result = repository.load_snapshot("v1", error_if_not_found=False)

            assert result is not None
            assert result.version == "v1"
            assert result.content == "Content 1"
        finally:
            shutil.rmtree(temp_dir)

    def test_set_active_alias_calls_set_active_version(self):
        """Test set_active() is an alias for set_active_version()."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            repository = LocalPromptRepository(config, agent)

            path = repository._get_relative_prompt_path()
            versions_dir = path / "versions"
            versions_dir.mkdir(parents=True)
            (versions_dir / "v1.prompt").write_text("Content 1")
            (versions_dir / "v2.prompt").write_text("Content 2")

            repository.set_active("v2")

            version_file = path / "version.txt"
            assert version_file.exists()
            assert version_file.read_text().strip() == "v2"

            # Verify it works the same as set_active_version
            repository.set_active_version("v1")
            assert version_file.read_text().strip() == "v1"
        finally:
            shutil.rmtree(temp_dir)
