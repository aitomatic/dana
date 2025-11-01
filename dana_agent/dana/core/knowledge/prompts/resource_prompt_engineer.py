import inspect
from typing import TYPE_CHECKING, override

from dana.common.storage import AbstractStorage
from dana.common.utils.misc import Misc

from .base_prompt_engineer import BasePromptEngineer
from .codecs import AbstractCodec


if TYPE_CHECKING:
    from dana.core.resource.base_resource import BaseResource


class ResourcePromptEngineer(BasePromptEngineer):
    """
    Prompt engineer for resources that formats @tool_use decorated methods.
    
    Uses the configured codec (CSXMLCodec or KLXMLCodec) to format each
    @tool_use method into the appropriate XML format.
    """

    def __init__(
        self,
        component: "BaseResource",
        storage: AbstractStorage | None = None,
        codec: type[AbstractCodec] | None = None,
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs
    ):
        """
        Initialize the ResourcePromptEngineer.
        
        Args:
            component: The resource component to generate prompts for
            storage: Storage instance (optional)
            codec: Codec class to use (optional, defaults to CSXMLCodec)
            force_generate: Whether to force regeneration
            check_conflicts: Whether to check for conflicts
        """
        # Default to CSXMLCodec if not provided
        super().__init__(component, storage, codec, force_generate, check_conflicts)

    @override
    def construct_prompt(self) -> str:
        """
        Construct the prompt for the resource by formatting all @tool_use methods.
        
        Returns:
            Formatted prompt string with all resource methods using the configured codec
        """
        # Extract resource description from docstring
        resource_class = self._component.__class__
        resource_description = self._extract_resource_description(resource_class)
        
        # Find all @tool_use decorated methods
        tool_methods = Misc.extract_tool_use_methods(resource_class)
        
        if not tool_methods:
            # No tool methods found - return just the description
            return resource_description or ""
        
        # Format each method using the codec
        formatted_methods = []
        for _, method in tool_methods:
            # Parse method signature
            signature = Misc.parse_method_signature(method)
            
            # Use codec to format the method signature
            formatted = self._codec.construct(signature)
            formatted_methods.append(formatted)
        
        # Combine resource description and all formatted methods
        prompt_parts = []
        if resource_description:
            prompt_parts.append(resource_description)
            prompt_parts.append("")  # Empty line separator
        
        prompt_parts.extend(formatted_methods)
        
        return "\n".join(prompt_parts)
    
    def _extract_resource_description(self, resource_class) -> str:
        """
        Extract resource description from class docstring.
        
        Args:
            resource_class: The resource class
            
        Returns:
            Resource description string
        """
        docstring = inspect.getdoc(resource_class)
        if not docstring:
            return f"{resource_class.__name__} resource."
        
        # Parse docstring sections
        sections = Misc.parse_docstring_sections(docstring)
        description = sections.get('description', '')
        
        if description:
            # Get first paragraph
            first_para = description.split('\n\n')[0].strip()
            return first_para
        
        return f"{resource_class.__name__} resource."

    @override
    def check_conflicts(self) -> bool:
        """
        Check for conflicts in the resource prompt.
        
        Currently checks for:
        - Duplicate method names (should not happen in same class)
        
        Returns:
            True if conflicts found, False otherwise
        """
        tool_methods = Misc.extract_tool_use_methods(self._component.__class__)
        method_names = [name for name, _ in tool_methods]
        
        # Check for duplicate method names
        if len(method_names) != len(set(method_names)):
            return True
        
        return False