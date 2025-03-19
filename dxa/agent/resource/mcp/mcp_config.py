"""Configuration utilities for execution components."""

from pathlib import Path
from typing import Optional, Type, Any
from ....common.utils import get_config_path

class MCPConfig:
    """Centralized configuration management for all execution components."""
    
    @classmethod
    def get_mcp_services_path(cls,
                              path: Optional[str] = None,
                              for_class: Optional[Type[Any]] = None) -> Path:
        """Get path to service code file.

        Arguments:
            path: Considered first. Full path to service file, OR relative
                    to the services directory (e.g., "mcp_echo_service" or
                    "mcp_echo_service/mcp_echo_service.py")

            for_class: Considered second. If provided, we will look
                    here for the "mcp_services" directory first

        Returns:
            Full path to the services .py file
        """

        if not for_class:
            for_class = cls

        return get_config_path(for_class=for_class,
                               path=path,
                               config_dir="mcp_services",
                               default_config_file="mcp_echo_service",
                               file_extension="py")
