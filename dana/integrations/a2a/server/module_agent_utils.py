"""
Module validation for Dana module agents.

This module provides validation logic to determine if a Dana module can be used as an agent.
"""

from typing import Any

from dana.common.utils.logging import DANA_LOGGER


class ModuleAgentError(Exception):
    """Base exception for module agent errors."""

    pass


class InvalidModuleError(ModuleAgentError):
    """Module cannot be used as agent."""

    pass


class ModuleExecutionError(ModuleAgentError):
    """Error during module agent execution."""

    pass


def validate_module_as_agent(module: Any) -> bool:
    """
    Validate if a Dana module can be used as an agent.

    Requirements for a module to be an agent:
    1. Must have system:agent_name
    2. Must have system:agent_description
    3. Must have a solve function

    Args:
        module: The Dana module to validate

    Returns:
        True if module can be used as agent

    Raises:
        InvalidModuleError: If module doesn't meet agent requirements
    """
    logger = DANA_LOGGER.getLogger("dana.module_validator")

    try:
        # Check if module has the required attributes
        if not hasattr(module, "__dict__"):
            raise InvalidModuleError("Module must be a Dana module with attributes")

        module_dict = module.__dict__

        # Debug: Print all module attributes to understand structure
        logger.debug(f"Module attributes: {list(module_dict.keys())}")
        logger.debug(f"Module type: {type(module)}")

        # Check for system:agent_name (might be stored differently)
        agent_name = None
        agent_description = None

        # Try different possible keys for system variables
        possible_name_keys = ["system:agent_name", "agent_name", "system_agent_name"]
        possible_desc_keys = ["system:agent_description", "agent_description", "system_agent_description"]

        for key in possible_name_keys:
            if key in module_dict:
                agent_name = module_dict[key]
                logger.debug(f"Found agent name with key '{key}': {agent_name}")
                break

        for key in possible_desc_keys:
            if key in module_dict:
                agent_description = module_dict[key]
                logger.debug(f"Found agent description with key '{key}': {agent_description}")
                break

        # Check if we found agent name
        if agent_name is None:
            # Log all keys for debugging
            logger.error(f"Available module keys: {list(module_dict.keys())}")
            raise InvalidModuleError(
                "Module must have 'system:agent_name' to be used as agent. Add: system:agent_name = \"Your Agent Name\""
            )

        # Check if we found agent description
        if agent_description is None:
            logger.error(f"Available module keys: {list(module_dict.keys())}")
            raise InvalidModuleError(
                "Module must have 'system:agent_description' to be used as agent. "
                'Add: system:agent_description = "Your agent description"'
            )

        # Check for solve function
        if "solve" not in module_dict:
            logger.error(f"Available module keys: {list(module_dict.keys())}")
            raise InvalidModuleError("Module must have a 'solve' function to be used as agent. Add: def solve(task: str) -> str: ...")

        # Verify solve is callable
        solve_func = module_dict["solve"]
        if not callable(solve_func):
            raise InvalidModuleError("Module 'solve' must be a callable function")

        logger.debug(f"Module validated as agent: {agent_name} - {agent_description}")
        return True

    except InvalidModuleError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error validating module as agent: {e}")
        raise InvalidModuleError(f"Failed to validate module: {e}") from e


def get_module_agent_info(module: Any) -> dict[str, str]:
    """
    Extract agent information from a validated module.

    Args:
        module: The validated Dana module

    Returns:
        Dictionary with agent_name and agent_description

    Raises:
        InvalidModuleError: If module is not valid
    """
    # Validate first
    validate_module_as_agent(module)

    module_dict = module.__dict__

    # Try different possible keys for system variables
    agent_name = None
    agent_description = None

    possible_name_keys = ["system:agent_name", "agent_name", "system_agent_name"]
    possible_desc_keys = ["system:agent_description", "agent_description", "system_agent_description"]

    for key in possible_name_keys:
        if key in module_dict:
            agent_name = module_dict[key]
            break

    for key in possible_desc_keys:
        if key in module_dict:
            agent_description = module_dict[key]
            break

    # Ensure we have valid strings (validation should have caught None values)
    if agent_name is None or agent_description is None:
        raise InvalidModuleError("Module validation passed but agent info is missing")

    return {"agent_name": str(agent_name), "agent_description": str(agent_description)}
