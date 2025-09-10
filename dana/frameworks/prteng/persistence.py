"""
Persistence layer for the PromptEngineer framework.
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime

from .models import Interaction, TemplateVersion


class PromptEngineerPersistence:
    """Handles filesystem persistence for prompt templates and interaction history."""

    def __init__(self, base_dir: str = "~/.dana/prteng"):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_prompt_dir(self, prompt_id: str) -> Path:
        """Get directory for specific prompt_id."""
        return self.base_dir / prompt_id

    def save_template_version(self, prompt_id: str, template: str, version: int):
        """Save template version to versions/v{version}.json."""
        prompt_dir = self.get_prompt_dir(prompt_id)
        prompt_dir.mkdir(parents=True, exist_ok=True)
        versions_dir = prompt_dir / "versions"
        versions_dir.mkdir(exist_ok=True)

        version_file = versions_dir / f"v{version}.json"
        template_version = TemplateVersion(template=template, version=version, timestamp=datetime.now(), prompt_id=prompt_id)

        with open(version_file, "w") as f:
            json.dump(template_version.to_dict(), f, indent=2)

    def save_interaction(self, prompt_id: str, interaction: Interaction):
        """Save interaction to interactions/ directory."""
        prompt_dir = self.get_prompt_dir(prompt_id)
        prompt_dir.mkdir(parents=True, exist_ok=True)
        interactions_dir = prompt_dir / "interactions"
        interactions_dir.mkdir(exist_ok=True)

        timestamp = interaction.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        interaction_file = interactions_dir / f"{timestamp}.json"

        with open(interaction_file, "w") as f:
            json.dump(interaction.to_dict(), f, indent=2)

    def load_prompt_history(self, prompt_id: str) -> list[Interaction]:
        """Load all interactions for a prompt_id."""
        prompt_dir = self.get_prompt_dir(prompt_id)
        interactions_dir = prompt_dir / "interactions"

        if not interactions_dir.exists():
            return []

        interactions = []
        for file_path in sorted(interactions_dir.glob("*.json")):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    interactions.append(Interaction.from_dict(data))
            except (json.JSONDecodeError, KeyError) as e:
                # Skip corrupted files
                print(f"Warning: Skipping corrupted interaction file {file_path}: {e}")
                continue

        return interactions

    def load_template_versions(self, prompt_id: str) -> list[TemplateVersion]:
        """Load all template versions for a prompt_id."""
        prompt_dir = self.get_prompt_dir(prompt_id)
        versions_dir = prompt_dir / "versions"

        if not versions_dir.exists():
            return []

        versions = []
        for file_path in sorted(versions_dir.glob("v*.json")):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    versions.append(TemplateVersion.from_dict(data))
            except (json.JSONDecodeError, KeyError) as e:
                # Skip corrupted files
                print(f"Warning: Skipping corrupted version file {file_path}: {e}")
                continue

        return sorted(versions, key=lambda v: v.version)

    def get_latest_template(self, prompt_id: str) -> str | None:
        """Get the latest template version for a prompt_id."""
        versions = self.load_template_versions(prompt_id)
        if not versions:
            return None
        return versions[-1].template

    def save_metadata(self, prompt_id: str, metadata: dict[str, Any]):
        """Save prompt metadata to metadata.json."""
        prompt_dir = self.get_prompt_dir(prompt_id)
        prompt_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = prompt_dir / "metadata.json"

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def load_metadata(self, prompt_id: str) -> dict[str, Any]:
        """Load prompt metadata from metadata.json."""
        prompt_dir = self.get_prompt_dir(prompt_id)
        metadata_file = prompt_dir / "metadata.json"

        if not metadata_file.exists():
            return {}

        try:
            with open(metadata_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def list_prompt_ids(self) -> list[str]:
        """List all prompt_ids that have been created."""
        if not self.base_dir.exists():
            return []

        prompt_ids = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                prompt_ids.append(item.name)

        return sorted(prompt_ids)
