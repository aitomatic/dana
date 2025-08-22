"""Domain Knowledge Service for managing agent domain expertise trees."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.models import Agent
from dana.api.core.schemas import (
    DomainKnowledgeTree,
    DomainNode,
    DomainKnowledgeUpdateResponse,
)
from dana.api.services.domain_knowledge_version_service import get_domain_knowledge_version_service
from dana.common.mixins.loggable import Loggable

logger = logging.getLogger(__name__)


class DomainKnowledgeService(Loggable):
    """Service for managing agent domain knowledge trees."""

    def __init__(self):
        super().__init__()
        self.domain_knowledge_dir = Path("agents") / "domain_knowledge"
        self.domain_knowledge_dir.mkdir(parents=True, exist_ok=True)

    def get_domain_knowledge_file_path(self, agent_id: int) -> Path:
        """Get the file path for an agent's domain knowledge."""
        return self.domain_knowledge_dir / f"agent_{agent_id}_domain_knowledge.json"

    def get_version_file_path(self, agent_id: int, version: int) -> Path:
        """Get the file path for a specific version of agent's domain knowledge."""
        return self.domain_knowledge_dir / f"agent_{agent_id}_domain_knowledge_v{version}.json"

    def get_version_history_dir(self, agent_id: int) -> Path:
        """Get the directory path for an agent's version history."""
        version_dir = self.domain_knowledge_dir / f"agent_{agent_id}_versions"
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir

    async def get_agent_domain_knowledge(self, agent_id: int, db: Session | None = None) -> DomainKnowledgeTree | None:
        """Retrieve domain knowledge tree for an agent."""
        try:
            if db is None:
                db = next(get_db())

            # Get agent from database
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                self.error(f"Agent {agent_id} not found")
                return None

            # Try to find domain_knowledge.json in order of preference:
            file_path = None

            # 1. First, try the agent's folder (new location)
            folder_path = agent.config.get("folder_path") if agent.config else None
            if folder_path:
                agent_folder_path = Path(folder_path) / "domain_knowledge.json"
                if agent_folder_path.exists():
                    file_path = agent_folder_path
                    self.info(f"Found domain knowledge in agent folder: {file_path}")

            # 2. If not found, check if there's a specific path in config
            if not file_path:
                domain_knowledge_path = agent.config.get("domain_knowledge_path") if agent.config else None
                if domain_knowledge_path:
                    config_path = Path(domain_knowledge_path)
                    if config_path.exists():
                        file_path = config_path
                        self.info(f"Found domain knowledge at config path: {file_path}")

            # 3. Finally, try the old default location
            if not file_path:
                default_path = self.get_domain_knowledge_file_path(agent_id)
                if default_path.exists():
                    file_path = default_path
                    self.info(f"Found domain knowledge at default path: {file_path}")

            if not file_path:
                self.warning(f"Domain knowledge file not found for agent {agent_id}")
                return None

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            return DomainKnowledgeTree(**data)

        except Exception as e:
            self.error(f"Error retrieving domain knowledge for agent {agent_id}: {e}")
            return None

    async def save_agent_domain_knowledge(
        self,
        agent_id: int,
        tree: DomainKnowledgeTree,
        db: Session | None = None,
        agent: Agent | None = None,
    ) -> bool:
        """Save domain knowledge tree for an agent with version history."""
        try:
            if db is None:
                db = next(get_db())

            # Get agent from database or use provided agent
            if agent is None:
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if not agent:
                    self.error(f"Agent {agent_id} not found")
                    return False

            # Get current version if exists
            current_tree = await self.get_agent_domain_knowledge(agent_id, db)

            # Update tree metadata
            tree.last_updated = datetime.now(UTC)
            tree.version = tree.version + 1 if tree.version else 1

            # Save current version to history before overwriting (if it exists)
            if current_tree:
                await self._save_version_to_history(agent_id, current_tree)

            # Determine where to save the file:
            # 1. Prefer the agent's folder if it exists
            # 2. Fall back to the old default location
            file_path = None
            folder_path = agent.config.get("folder_path") if agent.config else None

            if folder_path:
                agent_folder = Path(folder_path)
                if agent_folder.exists():
                    file_path = agent_folder / "domain_knowledge.json"
                    self.info(f"Saving domain knowledge to agent folder: {file_path}")

            # Fall back to old default location
            if not file_path:
                file_path = self.get_domain_knowledge_file_path(agent_id)
                self.info(f"Saving domain knowledge to default location: {file_path}")

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save new version to main file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tree.model_dump(), f, indent=2, default=str)

            # Update agent config with file path if it's not in the agent folder
            # (If it's in agent folder, we don't need to store the path separately)
            config = dict(agent.config) if agent.config else {}
            if folder_path and file_path == Path(folder_path) / "domain_knowledge.json":
                # File is in agent folder - remove explicit path from config if it exists
                config.pop("domain_knowledge_path", None)
            else:
                # File is in default location - store explicit path
                config["domain_knowledge_path"] = str(file_path)
            agent.config = config

            db.commit()

            self.info(f"Saved domain knowledge for agent {agent_id} to {file_path} (version {tree.version})")
            return True

        except Exception as e:
            self.error(f"Error saving domain knowledge for agent {agent_id}: {e}")
            if db:
                db.rollback()
            return False

    async def create_initial_domain_knowledge(
        self,
        agent_id: int,
        agent_name: str,
        agent_description: str,
        db: Session | None = None,
    ) -> DomainKnowledgeTree | None:
        """Create initial domain knowledge tree based on agent description."""
        try:
            # For now, create a basic tree structure
            # In the future, this would use LLM to generate based on description
            root_topic = self._extract_main_topic(agent_name, agent_description)

            root_node = DomainNode(topic=root_topic, children=[])

            tree = DomainKnowledgeTree(root=root_node, last_updated=datetime.now(UTC), version=1)

            # Save the tree
            success = await self.save_agent_domain_knowledge(agent_id, tree, db)
            if success:
                return tree
            return None

        except Exception as e:
            self.error(f"Error creating initial domain knowledge for agent {agent_id}: {e}")
            return None

    def _extract_main_topic(self, agent_name: str, agent_description: str) -> str:
        """Extract the main topic from agent name and description."""
        # Simple heuristic - could be enhanced with NLP
        if "financial" in agent_description.lower() or "finance" in agent_description.lower():
            return "Finance"
        elif "legal" in agent_description.lower() or "law" in agent_description.lower():
            return "Legal"
        elif "medical" in agent_description.lower() or "health" in agent_description.lower():
            return "Healthcare"
        elif "technical" in agent_description.lower() or "engineering" in agent_description.lower():
            return "Engineering"
        elif "research" in agent_description.lower():
            return "Research"
        else:
            return agent_name.replace(" Agent", "").replace(" Assistant", "").strip()

    async def add_knowledge_node(
        self,
        agent_id: int,
        topic: str,
        parent_topic: str | None = None,
        db: Session | None = None,
    ) -> DomainKnowledgeUpdateResponse:
        """Add a new knowledge node to the domain tree."""
        try:
            # Get current tree
            tree = await self.get_agent_domain_knowledge(agent_id, db)
            if not tree:
                return DomainKnowledgeUpdateResponse(success=False, error="No domain knowledge tree found for agent")

            # Find parent node or use root
            parent_node = tree.root
            if parent_topic:
                parent_node = self._find_node(tree.root, parent_topic)
                if not parent_node:
                    return DomainKnowledgeUpdateResponse(
                        success=False,
                        error=f"Parent topic '{parent_topic}' not found in tree",
                    )

            # Check if topic already exists
            if self._find_node(tree.root, topic):
                return DomainKnowledgeUpdateResponse(success=False, error=f"Topic '{topic}' already exists in tree")

            # Add new node
            new_node = DomainNode(topic=topic, children=[])
            parent_node.children.append(new_node)

            # Save updated tree
            success = await self.save_agent_domain_knowledge(agent_id, tree, db)

            return DomainKnowledgeUpdateResponse(
                success=success,
                updated_tree=tree if success else None,
                changes_summary=f"Added '{topic}' under '{parent_node.topic}'" if success else None,
                error=None if success else "Failed to save updated tree",
            )

        except Exception as e:
            self.error(f"Error adding knowledge node: {e}")
            return DomainKnowledgeUpdateResponse(success=False, error=str(e))

    async def refresh_domain_knowledge(self, agent_id: int, context: str = "", db: Session | None = None) -> DomainKnowledgeUpdateResponse:
        """Refresh/regenerate the domain knowledge tree."""
        try:
            if db is None:
                db = next(get_db())

            # Get agent info
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return DomainKnowledgeUpdateResponse(success=False, error="Agent not found")

            # Get current tree
            current_tree = await self.get_agent_domain_knowledge(agent_id, db)

            # For now, create an enhanced version of the current tree
            # In the future, this would use LLM to regenerate based on context
            if current_tree:
                # Add some default enhancements based on context
                enhanced_tree = await self._enhance_tree_with_context(current_tree, context, agent)
                success = await self.save_agent_domain_knowledge(agent_id, enhanced_tree, db)

                return DomainKnowledgeUpdateResponse(
                    success=success,
                    updated_tree=enhanced_tree if success else None,
                    changes_summary="Refreshed domain knowledge tree with new context" if success else None,
                    error=None if success else "Failed to save refreshed tree",
                )
            else:
                # Create new tree
                new_tree = await self.create_initial_domain_knowledge(agent_id, agent.name, agent.description or "", db)

                return DomainKnowledgeUpdateResponse(
                    success=new_tree is not None,
                    updated_tree=new_tree,
                    changes_summary="Created new domain knowledge tree" if new_tree else None,
                    error=None if new_tree else "Failed to create domain knowledge tree",
                )

        except Exception as e:
            self.error(f"Error refreshing domain knowledge: {e}")
            return DomainKnowledgeUpdateResponse(success=False, error=str(e))

    async def _save_version_to_history(
        self, agent_id: int, tree: DomainKnowledgeTree, change_summary: str = "Manual save", change_type: str = "modify"
    ) -> None:
        """Save a version to file history and maintain only last 10 versions."""
        try:
            version_service = get_domain_knowledge_version_service()

            # Save to files
            version_service.save_version(agent_id=agent_id, tree=tree, change_summary=change_summary, change_type=change_type)

            # Clean up old versions (keep only last 10)
            version_service.cleanup_old_versions(agent_id, keep_count=10)

        except Exception as e:
            self.error(f"Error saving version {tree.version} to history: {e}")

    async def _cleanup_old_versions(self, agent_id: int) -> None:
        """Keep only the last 5 versions in history."""
        try:
            version_dir = self.get_version_history_dir(agent_id)
            version_files = list(version_dir.glob("v*.json"))

            # Sort by version number (extract number from filename)
            version_files.sort(key=lambda x: int(x.stem[1:]), reverse=True)

            # Keep only the last 5 versions, remove the rest
            for old_file in version_files[5:]:
                old_file.unlink()
                self.debug(f"Removed old version file: {old_file}")

        except Exception as e:
            self.error(f"Error cleaning up old versions: {e}")

    async def get_version_history(self, agent_id: int) -> list[dict[str, Any]]:
        """Get available versions for an agent."""
        try:
            version_dir = self.get_version_history_dir(agent_id)
            version_files = list(version_dir.glob("v*.json"))

            # Also include current version
            current_tree = await self.get_agent_domain_knowledge(agent_id)
            versions = []

            if current_tree:
                versions.append(
                    {
                        "version": current_tree.version,
                        "last_updated": current_tree.last_updated.isoformat() if current_tree.last_updated else None,
                        "is_current": True,
                    }
                )

            # Add historical versions
            for version_file in version_files:
                try:
                    with open(version_file, encoding="utf-8") as f:
                        data = json.load(f)

                    versions.append(
                        {
                            "version": data.get("version"),
                            "last_updated": data.get("last_updated"),
                            "is_current": False,
                        }
                    )
                except Exception as e:
                    self.warning(f"Error reading version file {version_file}: {e}")

            # Sort by version descending (newest first)
            versions.sort(key=lambda x: x["version"] or 0, reverse=True)
            return versions

        except Exception as e:
            self.error(f"Error getting version history: {e}")
            return []

    async def revert_to_version(self, agent_id: int, target_version: int, db: Session | None = None) -> DomainKnowledgeUpdateResponse:
        """Revert domain knowledge to a specific version."""
        try:
            if db is None:
                db = next(get_db())

            # Check if target version is current
            current_tree = await self.get_agent_domain_knowledge(agent_id, db)
            if current_tree and current_tree.version == target_version:
                return DomainKnowledgeUpdateResponse(
                    success=False,
                    error=f"Version {target_version} is already the current version",
                )

            # Try to load target version from history
            version_dir = self.get_version_history_dir(agent_id)
            version_file = version_dir / f"v{target_version}.json"

            if not version_file.exists():
                return DomainKnowledgeUpdateResponse(
                    success=False,
                    error=f"Version {target_version} not found in history",
                )

            # Load the target version
            with open(version_file, encoding="utf-8") as f:
                data = json.load(f)

            target_tree = DomainKnowledgeTree(**data)

            # Save as new version (this will increment version and save current to history)
            success = await self.save_agent_domain_knowledge(agent_id, target_tree, db)

            return DomainKnowledgeUpdateResponse(
                success=success,
                updated_tree=target_tree if success else None,
                changes_summary=f"Reverted to version {target_version}" if success else None,
                error=None if success else "Failed to revert to target version",
            )

        except Exception as e:
            self.error(f"Error reverting to version {target_version}: {e}")
            return DomainKnowledgeUpdateResponse(success=False, error=str(e))

    def _find_node(self, root: DomainNode, topic: str) -> DomainNode | None:
        """Find a node in the tree by topic."""
        if root.topic.lower() == topic.lower():
            return root

        for child in root.children:
            found = self._find_node(child, topic)
            if found:
                return found

        return None

    async def _enhance_tree_with_context(self, tree: DomainKnowledgeTree, context: str, agent: Agent) -> DomainKnowledgeTree:
        """Enhance existing tree with context (placeholder for LLM enhancement)."""
        # This is a placeholder - in the future, this would use LLM to enhance the tree
        # For now, just return the existing tree with updated timestamp
        tree.last_updated = datetime.now(UTC)
        tree.version += 1
        return tree


def get_domain_knowledge_service() -> DomainKnowledgeService:
    """Dependency injection for domain knowledge service."""
    return DomainKnowledgeService()
