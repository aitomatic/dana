from abc import ABC, abstractmethod
import inspect
from typing import TYPE_CHECKING, override

import structlog

from dana.common.base_war import BaseWAR
from dana.common.protocols import Persistable
from dana.common.schemas.tool_call import ParameterInfo
from dana.common.utils.misc import Misc

from ..codecs import AbstractCodec, CSXMLCodec
from dana.repositories.repository_protocol import PromptRepositoryProtocol


if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent
    from dana.core.resource.base_resource import BaseResource
    from dana.core.workflow.base_workflow import BaseWorkflow


logger = structlog.get_logger("prompts")


class BasePromptEngineer(ABC, Persistable):
    def __init__(
        self,
        component: BaseWAR,
        repository: PromptRepositoryProtocol,
        codec: type[AbstractCodec],
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs,
    ):
        self._repository = repository
        self._component = component
        self._codec = codec or CSXMLCodec
        self._force_generate = force_generate
        self._check_conflicts = check_conflicts
        self._prompt = None

    @property
    def prompt(self) -> str:
        if self._prompt is None:
            self._prompt = self._get_prompt()
        return self._prompt

    def _get_prompt(self) -> str:
        """
        Get the prompt for the component.
        """
        prompt = self.load()
        if prompt is None or self._force_generate:
            prompt = self.construct_prompt()
            self._prompt = prompt
            self.persist()
        return prompt

    @abstractmethod
    def construct_prompt(self) -> str:
        """
        Construct the prompt for the component.
        """
        pass

    @abstractmethod
    def check_conflicts(self) -> bool:
        """
        Check for conflicts in the prompt for the component.
        """
        pass


    def persist(self) -> None:
        """
        Persist the prompt for the component.
        """
        if self._prompt is None:
            raise ValueError(f"[{self.__class__.__qualname__}] Prompt for {self._component.__class__.__qualname__} is not generated yet")
        prompt_version = self._repository.create_snapshot(
                            content=self._prompt, 
                            provenance={
                                "source" : "auto-generated",
                                "reasoning" : "auto-generated",
                                "parent_version" : None,
                            }, 
                            metrics={}
                            )
        logger.info(f"Prompt template persisted for {self._component.__class__.__qualname__} and codec {self._codec.__qualname__} with version {prompt_version.version}")
        self._repository.set_active(prompt_version.version)

    def load(self) -> str | None:
        """
        Load the prompt for the component.
        """
        snapshot = self._repository.get_active(error_if_not_found=False)
        if snapshot is None:
            return None
        return snapshot.content

    
class ResourcePromptEngineer(BasePromptEngineer):
    def __init__(
        self,
        component: "BaseResource",
        repository: PromptRepositoryProtocol,
        codec: type[AbstractCodec],
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs,
    ):
        super().__init__(component, repository, codec, force_generate, check_conflicts, **kwargs)

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

class WorkflowPromptEngineer(BasePromptEngineer):
    def __init__(
        self,
        component: "BaseWorkflow",
        repository: PromptRepositoryProtocol,
        codec: type[AbstractCodec],
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs,
    ):
        super().__init__(component, repository, codec, force_generate, check_conflicts, **kwargs)

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


class AgentPromptEngineer(BasePromptEngineer):
    """
    Prompt engineer for agents that formats the query method.
    
    Uses the configured codec (CSXMLCodec or KLXMLCodec) to format the
    query method into the appropriate XML format.
    """

    def __init__(
        self,
        component: "BaseAgent",
        repository: PromptRepositoryProtocol,
        codec: type[AbstractCodec],
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs,
    ):
        super().__init__(component, repository, codec, force_generate, check_conflicts, **kwargs)

    @override
    def construct_prompt(self) -> str:
        """
        Construct the prompt for the agent by formatting the query method.
        
        Returns:
            Formatted prompt string with the query method using the configured codec
        """
        # Extract agent description from docstring
        agent_class = self._component.__class__
        agent_description = self._extract_agent_description(agent_class)
        
        # Find query method directly (not decorated with @tool_use)
        query_method = getattr(agent_class, 'query', None)
        
        if query_method is None:
            # No query method found - return just the description
            return agent_description or ""
        
        # Parse query method signature
        signature = Misc.parse_method_signature(query_method)
        signature.class_name = agent_class.__name__

        if not signature.parameters:
            signature.parameters = [ParameterInfo(name="message", type="str", description="The message to query the agent with", has_default=False, default=None, example=None)]
        
        # Use codec to format the method signature
        formatted = self._codec.construct(signature)
        
        # Combine agent description and formatted query method
        prompt_parts = []
        if agent_description:
            prompt_parts.append(agent_description)
            prompt_parts.append("")  # Empty line separator
        
        prompt_parts.append(formatted)
        
        return "\n".join(prompt_parts)
    
    def _extract_agent_description(self, agent_class) -> str:
        """
        Extract agent description from class docstring.
        
        Args:
            agent_class: The agent class
            
        Returns:
            Agent description string
        """
        docstring = inspect.getdoc(agent_class)
        if not docstring:
            return f"{agent_class.__name__} agent."
        
        # Parse docstring sections
        sections = Misc.parse_docstring_sections(docstring)
        description = sections.get('description', '')
        
        if description:
            return description
        
        return f"{agent_class.__name__} agent."

    @override
    def check_conflicts(self) -> bool:
        """
        Check for conflicts in the agent prompt.
        
        Agents only have one method (query), so no conflicts are possible.
        
        Returns:
            Always returns False (no conflicts possible)
        """
        return False