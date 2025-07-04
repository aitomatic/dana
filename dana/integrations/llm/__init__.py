"""LLM (Large Language Model) Integration."""

# Import from the common resource location
from ...common.resource.llm_configuration_manager import LLMConfigurationManager
from ...common.resource.llm_resource import LLMResource

__all__ = [
    'LLMResource',
    'LLMConfigurationManager'
]