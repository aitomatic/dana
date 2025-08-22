from pathlib import Path


class AvatarService:
    """Service for managing agent avatars using file system storage."""

    def __init__(self, avatars_dir: str = "dana/contrib/ui/public/agent-avatar"):
        self.avatars_dir = Path(avatars_dir)

    def get_agent_avatar(self, agent_id: int) -> str:
        """
        Get avatar path for agent ID, fallback to default if not found.

        Args:
            agent_id: The agent ID to get avatar for

        Returns:
            Path to the avatar file relative to public directory
        """
        avatar_filename = f"agent-avatar-{agent_id}.svg"
        default_filename = "agent-avatar-0.svg"

        avatar_path = self.avatars_dir / avatar_filename
        default_path = self.avatars_dir / default_filename

        if avatar_path.exists():
            return f"/agent-avatar/{avatar_filename}"
        elif default_path.exists():
            return f"/agent-avatar/{default_filename}"
        else:
            # Ultimate fallback to existing avatar
            return "/agent-avatar/agent-avatar-1.svg"

    def get_avatar_file_path(self, agent_id: int) -> Path | None:
        """
        Get the actual file path for an agent avatar.

        Args:
            agent_id: The agent ID to get avatar for

        Returns:
            Path object to the avatar file, or None if not found
        """
        avatar_filename = f"agent-avatar-{agent_id}.svg"
        default_filename = "agent-avatar-0.svg"

        avatar_path = self.avatars_dir / avatar_filename
        default_path = self.avatars_dir / default_filename

        if avatar_path.exists():
            return avatar_path
        elif default_path.exists():
            return default_path
        else:
            # Ultimate fallback
            fallback_path = self.avatars_dir / "agent-avatar-1.svg"
            return fallback_path if fallback_path.exists() else None

    def avatar_exists(self, agent_id: int) -> bool:
        """
        Check if a specific avatar exists for an agent ID.

        Args:
            agent_id: The agent ID to check

        Returns:
            True if avatar exists, False otherwise
        """
        avatar_filename = f"agent-avatar-{agent_id}.svg"
        avatar_path = self.avatars_dir / avatar_filename
        return avatar_path.exists()

    def get_available_avatars(self) -> list[int]:
        """
        Get list of available agent IDs that have avatars.

        Returns:
            List of agent IDs that have corresponding avatars
        """
        available_ids = []
        for file_path in self.avatars_dir.glob("agent-avatar-*.svg"):
            filename = file_path.stem  # Remove .svg extension
            if filename.startswith("agent-avatar-"):
                try:
                    agent_id = int(filename.replace("agent-avatar-", ""))
                    available_ids.append(agent_id)
                except ValueError:
                    # Skip files that don't follow the naming convention
                    continue
        return sorted(available_ids)
