"""
Langfuse-based prompt repository implementation.

Stores and retrieves prompts via Langfuse API, following the PromptRepositoryProtocol
interface and reusing LocalRepositoryMixin for codec/path utilities.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from langfuse import Langfuse
from structlog import get_logger

from dana.common.base_war import BaseWAR
from dana.common.protocols.war import AgentProtocol, ResourceProtocol, WorkflowProtocol
from dana.common.schemas import PromptVersionSnapshot
from dana.config.storage_config import LangfuseStorageConfig, StorageConfig
from dana.core.agent.base_agent import BaseAgent

from .local_file_repository import LocalRepositoryMixin
from .repository_protocol import PromptRepositoryProtocol


if TYPE_CHECKING:
    pass

logger = get_logger()


def _get_langfuse_client(storage_config: LangfuseStorageConfig) -> Langfuse:
    """
    Get Langfuse client from storage config.

    Args:
        storage_config: LangfuseStorageConfig with credentials

    Returns:
        Initialized Langfuse client instance

    Raises:
        ValueError: If credentials are not provided in config or env vars
    """
    public_key = storage_config.public_key
    secret_key = storage_config.secret_key
    host = storage_config.host or "https://cloud.langfuse.com"

    if not public_key or not secret_key:
        raise ValueError(
            "Langfuse credentials not provided. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables, "
            "or provide them in LangfuseStorageConfig."
        )

    return Langfuse(public_key=public_key, secret_key=secret_key, host=host)


class LangfusePromptRepository(PromptRepositoryProtocol, LocalRepositoryMixin):
    """
    Langfuse-based prompt repository that stores prompts via Langfuse API.

    Reuses LocalRepositoryMixin for:
    - Codec extraction and prefix computation
    - Agent path computation
    - Component type detection
    """

    # Metadata key for tracking active version in Langfuse
    ACTIVE_VERSION_KEY = "dana_active_version"

    @classmethod
    def instantiate(cls, storage_config: StorageConfig, agent: BaseAgent, component: BaseWAR | None = None) -> LangfusePromptRepository:
        """
        Instantiate LangfusePromptRepository (required by PromptRepositoryProtocol).

        Args:
            storage_config: StorageConfig (should be LangfuseStorageConfig)
            agent: Agent instance
            component: Optional component (agent/resource/workflow) for component prompts

        Returns:
            LangfusePromptRepository instance
        """
        if not isinstance(storage_config, LangfuseStorageConfig):
            raise ValueError(f"Expected LangfuseStorageConfig, got {type(storage_config)}")
        return cls(storage_config, agent, component)

    def __init__(self, storage_config: LangfuseStorageConfig, agent: BaseAgent, component: BaseWAR | None = None):
        """
        Initialize Langfuse prompt repository.

        Args:
            storage_config: LangfuseStorageConfig with credentials
            agent: Agent instance
            component: Optional component (agent/resource/workflow) for component prompts
        """
        self.storage_config = storage_config
        self._agent = agent
        self._component = component

        # Initialize Langfuse client from storage config
        self._langfuse = _get_langfuse_client(storage_config)

        # Compute and cache prompt name using mixin methods
        self._prompt_name = self._get_langfuse_prompt_name()
        self._active_version_cache: str | None = None

    def _get_langfuse_prompt_name(self) -> str:
        """
        Generate Langfuse prompt name using LocalRepositoryMixin utilities.

        Format: {codec}/{agent_class}__{filename}/{component_type}/{component_name}
        or: {codec}/{agent_class}__{filename}/system_prompt_template

        Note: _get_relative_storage_path() already includes the codec prefix,
        so we don't need to add it again.

        Returns:
            Prompt name string for Langfuse
        """
        # Reuse mixin method - it already includes codec prefix in the path
        base_path = self._get_relative_storage_path(self._agent)

        if self._component is None:
            # System prompt template
            return f"{base_path}/system_prompt_template"
        else:
            # Component prompt - reuse component type detection from LocalPromptRepository
            if isinstance(self._component, AgentProtocol):
                subfolder = "agents"
            elif isinstance(self._component, ResourceProtocol):
                subfolder = "resources"
            elif isinstance(self._component, WorkflowProtocol):
                subfolder = "workflows"
            else:
                raise ValueError(
                    f"Invalid component type: {type(self._component)}. "
                    f"Only accepts instance of subclasses of {ResourceProtocol.__name__}, "
                    f"{AgentProtocol.__name__}, {WorkflowProtocol.__name__}"
                )

            return f"{base_path}/{subfolder}/{str(self._component.object_id)}"

    def has_any_versions(self) -> bool:
        """Check if any versions exist for this prompt."""
        return len(self.list_versions()) > 0

    def get_active(self, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        """
        Get active version snapshot.

        Args:
            error_if_not_found: If True, raise error when no active version found

        Returns:
            PromptVersionSnapshot of active version, or None if not found and error_if_not_found=False
        """
        if not error_if_not_found and not self.has_any_versions():
            return None

        try:
            # Get active version from cache or Langfuse metadata
            active_version = self._get_active_version_from_langfuse()
            if active_version:
                return self.load_snapshot(active_version, error_if_not_found)

            # Fallback to latest version if no active version set
            versions = self.list_versions()
            if versions:
                return self.load_snapshot(versions[-1], error_if_not_found)

            if error_if_not_found:
                raise ValueError("No active version found")
            return None
        except Exception as e:
            if error_if_not_found:
                raise
            logger.warning(f"Failed to get active version: {e}")
            return None

    def list_versions(self) -> list[str]:
        """
        List all versions for this prompt.

        Returns:
            Sorted list of version strings (v1, v2, etc.)
        """
        try:
            # Get prompt from Langfuse to extract version list from config
            # We track versions in config since Langfuse doesn't provide direct version listing
            prompt = self._langfuse.get_prompt(name=self._prompt_name)

            if not prompt:
                return []

            # Extract versions from config (metadata is stored in config)
            config = getattr(prompt, "config", {}) or {}
            versions_list = config.get("dana_versions", [])

            # If no versions in config, check if there's at least one version
            # by trying to get the prompt with a default label
            if not versions_list:
                # Try to get prompt with default label to see if any version exists
                # This is a fallback - ideally versions should be tracked in config
                return []

            # Filter and sort versions
            valid_versions = [v for v in versions_list if isinstance(v, str) and v.startswith("v") and v[1:].isdigit()]
            return sorted(valid_versions, key=lambda x: int(x.split("v")[1]))
        except Exception as e:
            logger.warning(f"Failed to list versions from Langfuse: {e}")
            return []

    def load_snapshot(self, version: str, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        """
        Load prompt snapshot for a specific version.

        Args:
            version: Version string (e.g., "v1", "v2")
            error_if_not_found: If True, raise error when version not found

        Returns:
            PromptVersionSnapshot or None if not found and error_if_not_found=False
        """
        try:
            # Get prompt from Langfuse with specific version/label
            prompt = self._langfuse.get_prompt(name=self._prompt_name, label=version)

            if not prompt:
                if error_if_not_found:
                    raise ValueError(f"Version {version} not found for prompt {self._prompt_name}")
                return None

            # Extract data from Langfuse prompt object
            # Map Langfuse prompt structure to PromptVersionSnapshot
            content = getattr(prompt, "prompt", "") or getattr(prompt, "content", "")
            config = getattr(prompt, "config", {}) or {}

            # Extract provenance and metrics from config (metadata is stored in config)
            provenance = config.get("provenance", {})
            metrics = config.get("metrics", {})

            # Extract timestamps - Langfuse prompt objects may not have these directly
            # Use current time as fallback
            created_at = getattr(prompt, "created_at", None) or datetime.now(UTC)
            updated_at = getattr(prompt, "updated_at", None) or datetime.now(UTC)

            # Convert to datetime if needed
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

            return PromptVersionSnapshot(
                version=version,
                content=content,
                created_at=created_at,
                updated_at=updated_at,
                provenance=provenance,
                metrics=metrics,
            )
        except Exception as e:
            if error_if_not_found:
                raise ValueError(f"Failed to load version {version}: {e}") from e
            logger.warning(f"Failed to load snapshot {version}: {e}")
            return None

    def set_active_version(self, version: str) -> None:
        """
        Set active version for this prompt.

        Args:
            version: Version string to set as active
        """
        try:
            # Get the prompt with the specified version to verify it exists
            prompt = self._langfuse.get_prompt(name=self._prompt_name, label=version)

            if not prompt:
                raise ValueError(f"Version {version} not found for prompt {self._prompt_name}")

            # Get existing config
            config = getattr(prompt, "config", {}) or {}
            config[self.ACTIVE_VERSION_KEY] = version

            # Also update the base prompt (without label) to track active version
            # This allows quick lookup of active version
            try:
                base_prompt = self._langfuse.get_prompt(name=self._prompt_name)
                if base_prompt:
                    base_config = getattr(base_prompt, "config", {}) or {}
                    base_config[self.ACTIVE_VERSION_KEY] = version

                    # Update base prompt with active version in config
                    # Get the version's content to update base prompt
                    version_prompt = self._langfuse.get_prompt(name=self._prompt_name, label=version)
                    if version_prompt:
                        content = getattr(version_prompt, "prompt", "") or getattr(version_prompt, "content", "")
                        # Create/update base prompt with active version tracking
                        self._langfuse.create_prompt(name=self._prompt_name, prompt=content, config=base_config)
            except Exception:
                # If base prompt doesn't exist, that's okay - we'll track active version in version-specific prompt
                pass

            # Cache active version
            self._active_version_cache = version
            logger.info(f"Set active version {version} for prompt {self._prompt_name}")
        except Exception as e:
            logger.warning(f"Failed to set active version {version}: {e}")
            raise

    def set_active(self, version: str) -> None:
        """Alias for set_active_version for backward compatibility."""
        self.set_active_version(version)

    def create_snapshot(self, content: str, provenance: dict, metrics: dict) -> PromptVersionSnapshot:
        """
        Create a new prompt snapshot in Langfuse.

        Args:
            content: Prompt content
            provenance: Provenance metadata
            metrics: Metrics metadata

        Returns:
            PromptVersionSnapshot with new version
        """
        try:
            # Determine next version number
            versions = self.list_versions()
            if versions:
                latest_version = versions[-1]
                version_number = int(latest_version.split("v")[1]) + 1
            else:
                version_number = 1

            version = f"v{version_number}"

            # Get existing config to preserve version list
            existing_config = {}
            try:
                existing_prompt = self._langfuse.get_prompt(name=self._prompt_name)
                if existing_prompt:
                    existing_config = getattr(existing_prompt, "config", {}) or {}
            except Exception:
                pass  # No existing prompt, start fresh

            # Update version list in config
            versions_list = existing_config.get("dana_versions", [])
            if version not in versions_list:
                versions_list.append(version)

            # Prepare config for Langfuse (metadata is stored in config)
            config = {
                "provenance": provenance,
                "metrics": metrics,
                "dana_versions": versions_list,  # Track all versions
            }

            # Create/update prompt in Langfuse with version label
            # Langfuse SDK uses create_prompt() method with name, prompt content, labels (list), and config
            self._langfuse.create_prompt(
                name=self._prompt_name,
                prompt=content,
                labels=[version],  # Use labels as list
                config=config,  # Use config for metadata
            )

            # Flush to ensure prompt is saved
            self._langfuse.flush()

            # Create snapshot object
            now = datetime.now(UTC)
            snapshot = PromptVersionSnapshot(
                version=version,
                content=content,
                created_at=now,
                updated_at=now,
                provenance=provenance,
                metrics=metrics,
            )

            logger.info(f"Created prompt snapshot {version} for {self._prompt_name} in Langfuse")

            return snapshot
        except Exception as e:
            logger.error(f"Failed to create snapshot in Langfuse: {e}")
            raise ValueError(f"Failed to create prompt snapshot: {e}") from e

    def _get_active_version_from_langfuse(self) -> str | None:
        """
        Get active version from Langfuse config.

        Returns:
            Active version string or None if not set
        """
        try:
            # Check cache first
            if self._active_version_cache:
                return self._active_version_cache

            # Get prompt from Langfuse
            prompt = self._langfuse.get_prompt(name=self._prompt_name)

            if prompt:
                config = getattr(prompt, "config", {}) or {}
                active_version = config.get(self.ACTIVE_VERSION_KEY)
                if active_version:
                    self._active_version_cache = active_version
                    return active_version

            return None
        except Exception as e:
            logger.warning(f"Failed to get active version from Langfuse: {e}")
            return None
