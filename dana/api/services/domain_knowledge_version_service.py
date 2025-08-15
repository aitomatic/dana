"""Domain Knowledge Version Control Service - File-based implementation."""

import json
import logging
from datetime import datetime, UTC
from pathlib import Path

from dana.api.core.schemas import DomainKnowledgeTree

logger = logging.getLogger(__name__)


class DomainKnowledgeVersionMetadata:
    """Metadata for a domain knowledge version."""

    def __init__(self, version: int, change_summary: str, change_type: str, created_at: str):
        self.version = version
        self.change_summary = change_summary
        self.change_type = change_type
        self.created_at = created_at

    def to_dict(self):
        return {
            "version": self.version,
            "change_summary": self.change_summary,
            "change_type": self.change_type,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            version=data["version"], change_summary=data["change_summary"], change_type=data["change_type"], created_at=data["created_at"]
        )


class DomainKnowledgeVersionService:
    """Service for managing domain knowledge versions using JSON files."""

    def __init__(self):
        self.versions_base_dir = Path("agents") / "versions"
        self.versions_base_dir.mkdir(parents=True, exist_ok=True)

    def get_agent_versions_dir(self, agent_id: int) -> Path:
        """Get the versions directory for a specific agent."""
        agent_dir = self.versions_base_dir / f"agent_{agent_id}"
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    def save_version(self, agent_id: int, tree: DomainKnowledgeTree, change_summary: str, change_type: str) -> bool:
        """Save a new version of the domain knowledge tree."""
        try:
            versions_dir = self.get_agent_versions_dir(agent_id)

            # Create version metadata
            metadata = DomainKnowledgeVersionMetadata(
                version=tree.version,
                change_summary=change_summary,
                change_type=change_type,
                created_at=datetime.now(UTC).isoformat(),
            )

            # Save the tree data
            tree_file = versions_dir / f"v{tree.version}_tree.json"
            with open(tree_file, "w", encoding="utf-8") as f:
                json.dump(tree.model_dump(), f, indent=2, default=str)

            # Save the metadata
            metadata_file = versions_dir / f"v{tree.version}_metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, indent=2)

            # Update versions index
            self._update_versions_index(agent_id, metadata)

            logger.info(f"Saved domain knowledge version {tree.version} for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving domain knowledge version: {e}")
            return False

    def _update_versions_index(self, agent_id: int, metadata: DomainKnowledgeVersionMetadata):
        """Update the versions index file."""
        versions_dir = self.get_agent_versions_dir(agent_id)
        index_file = versions_dir / "versions_index.json"

        # Load existing index
        versions_list = []
        if index_file.exists():
            try:
                with open(index_file, encoding="utf-8") as f:
                    versions_list = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load versions index: {e}")
                versions_list = []

        # Add new version (avoid duplicates)
        versions_list = [v for v in versions_list if v.get("version") != metadata.version]
        versions_list.append(metadata.to_dict())

        # Sort by version descending
        versions_list.sort(key=lambda x: x["version"], reverse=True)

        # Save updated index
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(versions_list, f, indent=2)

    def get_versions(self, agent_id: int) -> list[dict]:
        """Get all versions for an agent, ordered by version number descending."""
        try:
            versions_dir = self.get_agent_versions_dir(agent_id)
            index_file = versions_dir / "versions_index.json"

            if not index_file.exists():
                return []

            with open(index_file, encoding="utf-8") as f:
                versions_list = json.load(f)

            return versions_list

        except Exception as e:
            logger.error(f"Error getting domain knowledge versions: {e}")
            return []

    def get_version_with_tree(self, agent_id: int, version: int) -> DomainKnowledgeTree | None:
        """Get a specific version with its tree data."""
        try:
            versions_dir = self.get_agent_versions_dir(agent_id)
            tree_file = versions_dir / f"v{version}_tree.json"

            if not tree_file.exists():
                return None

            with open(tree_file, encoding="utf-8") as f:
                tree_data = json.load(f)

            return DomainKnowledgeTree.model_validate(tree_data)

        except Exception as e:
            logger.error(f"Error getting domain knowledge version {version}: {e}")
            return None

    def revert_to_version(self, agent_id: int, target_version: int) -> DomainKnowledgeTree | None:
        """Revert domain knowledge to a specific version."""
        try:
            # Get the target version tree
            reverted_tree = self.get_version_with_tree(agent_id, target_version)
            if not reverted_tree:
                logger.error(f"Version {target_version} not found for agent {agent_id}")
                return None

            # Get the current highest version number and increment for the revert
            versions = self.get_versions(agent_id)
            latest_version_num = max([v["version"] for v in versions]) if versions else 0

            new_version = latest_version_num + 1
            reverted_tree.version = new_version
            reverted_tree.last_updated = datetime.now(UTC)

            # Save the revert as a new version
            self.save_version(
                agent_id=agent_id, tree=reverted_tree, change_summary=f"Reverted to version {target_version}", change_type="revert"
            )

            logger.info(f"Reverted agent {agent_id} to version {target_version}")
            return reverted_tree

        except Exception as e:
            logger.error(f"Error reverting to version {target_version}: {e}")
            return None

    def cleanup_old_versions(self, agent_id: int, keep_count: int = 10) -> int:
        """Clean up old versions, keeping only the most recent ones."""
        try:
            versions = self.get_versions(agent_id)

            if len(versions) <= keep_count:
                return 0

            # Delete old versions beyond the keep_count
            versions_to_delete = versions[keep_count:]
            deleted_count = 0
            versions_dir = self.get_agent_versions_dir(agent_id)

            for version_info in versions_to_delete:
                version_num = version_info["version"]

                # Delete tree and metadata files
                tree_file = versions_dir / f"v{version_num}_tree.json"
                metadata_file = versions_dir / f"v{version_num}_metadata.json"

                if tree_file.exists():
                    tree_file.unlink()
                if metadata_file.exists():
                    metadata_file.unlink()

                deleted_count += 1

            # Update the index to remove deleted versions
            kept_versions = versions[:keep_count]
            index_file = versions_dir / "versions_index.json"
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(kept_versions, f, indent=2)

            logger.info(f"Cleaned up {deleted_count} old versions for agent {agent_id}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old versions: {e}")
            return 0


def get_domain_knowledge_version_service() -> DomainKnowledgeVersionService:
    """Dependency injection for domain knowledge version service."""
    return DomainKnowledgeVersionService()
