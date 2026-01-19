"""
AssistantAgent - Lightweight agent for executing focused subtasks.

A pre-configured STARAgent designed to be used as a sub-agent for delegation.
Comes with built-in resources (web search, code execution) and returns
concise, focused results.

Usage
-----

.. code-block:: python

    from dana.core.agent import STARAgent, AssistantAgent

    # Create a ready-to-use assistant
    assistant = AssistantAgent()

    # Add it to your main agent
    agent = STARAgent(agent_type="coordinator").with_agents(assistant)

    # The LLM can now delegate tasks:
    # assistant__query(message="Get the current temperature in NYC")
    # Returns: "28°F"

Customization
-------------

.. code-block:: python

    # Research-focused assistant (web search only)
    researcher = AssistantAgent(
        agent_type="researcher",
        resources=["web_search"],
    )

    # Coding assistant (code execution only)
    coder = AssistantAgent(
        agent_type="coder",
        resources=["code_execution"],
    )

    # Custom assistant with no built-in resources
    custom = AssistantAgent(
        agent_type="custom",
        resources=[],
    ).with_resources(MyCustomResource())
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dana.core.agent.star_agent import STARAgent


if TYPE_CHECKING:
    from dana.common.protocols import ResourceProtocol  # noqa: F401


# Available built-in resources
RESOURCE_WEB_SEARCH = "web_search"
RESOURCE_CODE_EXECUTION = "code_execution"

DEFAULT_RESOURCES = [RESOURCE_WEB_SEARCH, RESOURCE_CODE_EXECUTION]


class AssistantAgent(STARAgent):
    """
    Lightweight agent for executing focused subtasks.

    Pre-configured with web search and code execution resources.
    Designed to be used as a sub-agent that returns concise results.

    Key features:
    - Built-in web search and code execution
    - Uses fast/cheap model by default (gpt-4o-mini)
    - Minimal system prompt focused on task execution
    - Returns concise, focused results

    Args:
        agent_type: Identifier for this assistant (default: "assistant")
        resources: List of built-in resources to enable.
                   Options: "web_search", "code_execution"
                   Default: ["web_search", "code_execution"]
        model: LLM model to use (default: None)
        max_steps: Maximum STAR loop iterations (default: 10)
        **kwargs: Additional arguments passed to STARAgent
    """

    def __init__(
        self,
        agent_type: str = "assistant",
        resources: list[str] | None = None,
        model: str | None = None,
        max_steps: int = 10,
        **kwargs,
    ):
        # Use defaults if not specified
        if resources is None:
            resources = DEFAULT_RESOURCES.copy()

        self._builtin_resources = resources

        # Disable STARAgent's default resources and assistant - we add our own
        kwargs.setdefault("enable_web_search", False)
        kwargs.setdefault("enable_skills", False)
        kwargs.setdefault("enable_assistant", False)  # Prevent infinite recursion

        # Initialize base STARAgent with lightweight defaults
        super().__init__(
            agent_type=agent_type,
            model=model,
            max_steps=max_steps,
            **kwargs,
        )

        # Add built-in resources
        self._add_builtin_resources()

    def _add_builtin_resources(self) -> None:
        """Add resources based on configuration."""
        resource_instances: list[ResourceProtocol] = []

        if RESOURCE_WEB_SEARCH in self._builtin_resources:
            try:
                from dana.core.resource.simple_search import SimpleWebSearch

                resource_instances.append(SimpleWebSearch())
            except ImportError:
                pass  # Web search not available

        if RESOURCE_CODE_EXECUTION in self._builtin_resources:
            try:
                from dana.common.resource.code_execution_resource import CodeExecutionResource

                resource_instances.append(CodeExecutionResource())
            except ImportError:
                pass  # Code execution not available

        if resource_instances:
            self.with_resources(*resource_instances)

    @property
    def public_description(self) -> str:
        """Description shown to parent agent for tool discovery."""
        resource_descriptions = []

        if RESOURCE_WEB_SEARCH in self._builtin_resources:
            resource_descriptions.append("search the web")

        if RESOURCE_CODE_EXECUTION in self._builtin_resources:
            resource_descriptions.append("run Python code")

        if resource_descriptions:
            caps = " and ".join(resource_descriptions)
            return (
                f"PREFERRED for multi-step tasks. Delegate to this assistant to {caps}. "
                "It works in its own context and returns only the final result, saving your context window. "
                "Use for: research requiring multiple searches, calculations, data gathering. "
                "Example: 'Get current temperatures in 5 US cities' → 'NYC: 42°F, LA: 65°F, Chicago: 35°F, Houston: 58°F, Phoenix: 70°F'"
            )
        else:
            return (
                "PREFERRED for multi-step tasks. Delegate subtasks to this assistant. "
                "It works in its own context and returns only the final result, saving your context window."
            )

    @property
    def system_prompt(self) -> str:
        """Minimal prompt focused on task execution."""
        return """You are a task execution assistant.

Your job is to:
1. Execute the given task using your available tools
2. Return ONLY the requested information - be concise

Guidelines:
- Focus on the specific task given
- Use tools efficiently (minimize unnecessary calls)
- Return just the answer, not explanations unless asked
- If you can't complete the task, explain briefly why

Example good responses:
- Task: "What is the current temperature in NYC?" → "42°F"
- Task: "Calculate 2^100" → "1267650600228229401496703205376"
- Task: "Find the CEO of Apple" → "Tim Cook"
"""

    def query(self, **kwargs) -> str:
        """Execute a task and return only the response string.

        Unlike STARAgent.query() which returns a full trace dict,
        AssistantAgent returns just the answer - keeping the parent's
        context clean.

        Args:
            **kwargs: Arguments passed to the query (must include 'message')

        Returns:
            The response string, or an error message if the query failed
        """
        result = super().query(**kwargs)
        return self._extract_response(result)

    async def aquery(self, **kwargs) -> str:
        """Async version of query - returns only the response string."""
        result = await super().aquery(**kwargs)
        return self._extract_response(result)

    def _extract_response(self, result) -> str:
        """Extract just the response string from query result."""
        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            return result.get("response", "No response generated")
        return str(result)
