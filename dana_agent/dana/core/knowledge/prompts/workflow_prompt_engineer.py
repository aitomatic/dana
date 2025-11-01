import inspect
from typing import TYPE_CHECKING, override

from dana.common.storage import AbstractStorage
from dana.common.utils.misc import Misc

from .base_prompt_engineer import BasePromptEngineer
from .codecs import AbstractCodec, CSXMLCodec


if TYPE_CHECKING:
    from dana.core.workflow.base_workflow import BaseWorkflow


class WorkflowPromptEngineer(BasePromptEngineer):
    """
    Prompt engineer for workflows that formats the execute method.
    
    Uses the configured codec (CSXMLCodec or KLXMLCodec) to format the
    execute method into the appropriate XML format.
    """

    def __init__(
        self,
        component: "BaseWorkflow",
        storage: AbstractStorage | None = None,
        codec: type[AbstractCodec] | None = None,
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs
    ):
        """
        Initialize the WorkflowPromptEngineer.
        
        Args:
            component: The workflow component to generate prompts for
            storage: Storage instance (optional)
            codec: Codec class to use (optional, defaults to CSXMLCodec)
            force_generate: Whether to force regeneration
            check_conflicts: Whether to check for conflicts
        """
        # Default to CSXMLCodec if not provided
        codec = codec if codec is not None else CSXMLCodec
        super().__init__(component, storage, codec, force_generate, check_conflicts)
        # Store codec class for use in construct_prompt
        self._codec = codec

    @override
    def construct_prompt(self) -> str:
        """
        Construct the prompt for the workflow by formatting the execute method.
        
        Returns:
            Formatted prompt string with the execute method using the configured codec
        """
        # Extract workflow description from docstring
        workflow_class = self._component.__class__
        workflow_description = self._extract_workflow_description(workflow_class)
        
        # Find execute method directly (not decorated with @tool_use)
        execute_method = getattr(workflow_class, 'execute', None)
        
        if execute_method is None:
            # No execute method found - return just the description
            return workflow_description or ""
        
        # Parse execute method signature
        signature = Misc.parse_method_signature(execute_method)
        
        # Use codec to format the method signature
        formatted = self._codec.construct(signature)
        
        # Combine workflow description and formatted execute method
        prompt_parts = []
        if workflow_description:
            prompt_parts.append(workflow_description)
            prompt_parts.append("")  # Empty line separator
        
        prompt_parts.append(formatted)
        
        return "\n".join(prompt_parts)
    
    def _extract_workflow_description(self, workflow_class) -> str:
        """
        Extract workflow description from class docstring.
        
        Args:
            workflow_class: The workflow class
            
        Returns:
            Workflow description string
        """
        docstring = inspect.getdoc(workflow_class)
        if not docstring:
            return f"{workflow_class.__name__} workflow."
        
        # Parse docstring sections
        sections = Misc.parse_docstring_sections(docstring)
        description = sections.get('description', '')
        
        if description:
            # Get first paragraph
            first_para = description.split('\n\n')[0].strip()
            return first_para
        
        return f"{workflow_class.__name__} workflow."

    @override
    def check_conflicts(self) -> bool:
        """
        Check for conflicts in the workflow prompt.
        
        Workflows only have one method (execute), so no conflicts are possible.
        
        Returns:
            Always returns False (no conflicts possible)
        """
        return False