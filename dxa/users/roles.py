"""User roles and permissions for the DXA system."""

from dataclasses import dataclass
from typing import List

@dataclass
class User:
    """Represents a human user with a specific role in the problem-solving process."""
    role: str
    name: str
    description: str
    permissions: List[str]  # e.g., ['specify_problem', 'clarify', 'validate', 'modify']

    def get_role_description(self) -> str:
        """Get a description of this user's role for the agent."""
        return f"""Role: {self.role}
        Name: {self.name}
        Description: {self.description}
        Permissions: {', '.join(self.permissions)}"""

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def validate_permissions(self, required_permissions: List[str]) -> bool:
        """Check if user has all required permissions."""
        return all(self.has_permission(perm) for perm in required_permissions)
