"""TaskResource for dispatching tasks to sub-agents with dynamic tool descriptions."""

from typing import Any
import uuid

from dana.common.protocols.war import TOOL_NAME, named_tool
from dana.common.utils.misc import Misc
from dana.core.resource.base_resource import BaseResource


class TaskResource(BaseResource):
    """Resource for launching tasks to sub-agents.

    The TaskResource dispatches tasks to specialized sub-agents, with tool descriptions
    dynamically generated based on the registered agents and their capabilities.
    """

    def __init__(self, resource_id: str, agents: dict[str, Any] | None = None, **kwargs):
        """Initialize the TaskResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            agents: Dictionary mapping agent type names to agent instances.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self._agents: dict[str, Any] = agents or {}
        self._sessions: dict[str, dict[str, Any]] = {}
        self._update_task_docstring()

    def register_agent(self, name: str, agent: Any) -> None:
        """Register an agent for task dispatch.

        Args:
            name: The name to use for this agent type.
            agent: The agent instance.
        """
        self._agents[name] = agent
        self._update_task_docstring()

    def unregister_agent(self, name: str) -> bool:
        """Unregister an agent from task dispatch.

        Args:
            name: The agent type name to remove.

        Returns:
            True if agent was removed, False if not found.
        """
        if name in self._agents:
            del self._agents[name]
            self._update_task_docstring()
            return True
        return False

    def _update_task_docstring(self) -> None:
        """Update the task method docstring with current agent information."""
        self.task.__func__.__doc__ = self._build_task_description()

    def _build_task_description(self) -> str:
        """Build description matching the expected format for dynamic agent documentation."""
        parts = [
            "Launch a new agent to handle complex, multi-step tasks autonomously.",
            "",
            "The Task tool launches specialized agents (subprocesses) that autonomously handle complex tasks. Each agent type has specific capabilities and tools available to it.",
            "",
            "Available agent types and the tools they have access to:",
        ]

        # Add each agent with its full description
        for name, agent in self._agents.items():
            desc = getattr(agent.__class__, "TASK_TOOL_DESCRIPTION", "No description available")
            tools = self._get_agent_tools(agent)
            tools_str = ", ".join(tools) if tools else "None"
            parts.append(f"- {name}: {desc} (Tools: {tools_str})")

        parts.extend(
            [
                "",
                "When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.",
                "",
                "When NOT to use the Task tool:",
                "- If you want to read a specific file path, use the Read or Glob tool instead of the Task tool, to find the match more quickly",
                '- If you are searching for a specific class definition like "class Foo", use the Glob tool instead, to find the match more quickly',
                "- If you are searching for code within a specific file or set of 2-3 files, use the Read tool instead of the Task tool, to find the match more quickly",
                "- Other tasks that are not related to the agent descriptions above",
                "",
                "Usage notes:",
                "- Always include a short description (3-5 words) summarizing what the agent will do",
                "- Provide clear, detailed prompts so the agent can work autonomously and return exactly the information you need",
                "- When the agent is done, it will return a single message back to you along with its session_id. You can use this ID to resume the agent later if needed for follow-up work.",
                "- Agents can be resumed using the `resume` parameter by passing the session_id from a previous invocation. When resumed, the agent continues with its full previous context preserved.",
                "- You can optionally run agents in the background using the run_in_background parameter.",
            ]
        )

        return "\n".join(parts)

    def _get_agent_tools(self, agent: Any) -> list[str]:
        """Extract tool names from an agent's resources.

        Args:
            agent: The agent to extract tools from.

        Returns:
            List of tool names available to the agent.
        """
        tool_names = []
        resources = getattr(agent, "_resources", [])

        for resource in resources:
            for method_name, method in Misc.extract_tool_use_methods(resource):
                # Check for custom tool name from @named_tool decorator
                custom_name = method.__dict__.get(TOOL_NAME) if hasattr(method, "__dict__") else None
                tool_names.append(custom_name or method_name)

        return tool_names

    def _generate_session_id(self) -> str:
        """Generate a unique session ID.

        Returns:
            An 8-character unique session identifier.
        """
        return str(uuid.uuid4())[:8]

    @named_tool(name="Task")
    async def task(
        self,
        description: str,  # noqa: ARG002 - Used for logging/display purposes
        prompt: str,
        subagent_type: str,
        model: str | None = None,  # noqa: ARG002 - Reserved for future model override
        resume: str | None = None,
        run_in_background: bool = False,  # noqa: ARG002 - Reserved for background execution
        max_turns: int = 50,  # noqa: ARG002 - Reserved for turn limiting
    ) -> str:
        """Placeholder docstring - replaced at runtime by _update_task_docstring().

        Args:
            description: A short (3-5 word) description of the task.
            prompt: The task for the agent to perform.
            subagent_type: The type of specialized agent to use for this task.
            model: Optional model to use for this agent.
            resume: Optional session_id to resume from a previous invocation.
            run_in_background: Set to true to run this agent in the background.
            max_turns: Maximum number of agentic turns before stopping.

        Returns:
            The agent's response along with a session_id for resumption.
        """
        _ = (description, model, run_in_background, max_turns)  # Reserved for future use

        # Validate agent type
        if subagent_type not in self._agents:
            available = ", ".join(self._agents.keys()) if self._agents else "none"
            return f"Error: Unknown agent type '{subagent_type}'. Available agents: {available}"

        agent = self._agents[subagent_type]
        session_id = resume or self._generate_session_id()

        # Store session state
        self._sessions[session_id] = {
            "agent": agent,
            "subagent_type": subagent_type,
            "status": "running",
        }

        # Execute the agent query
        result = await agent.aquery(message=prompt, session_id=session_id)

        # Update session state
        self._sessions[session_id]["status"] = "completed"
        self._sessions[session_id]["result"] = result

        # Extract response from result
        response = result.get("response", str(result)) if isinstance(result, dict) else str(result)
        return f"{response}\n\n[session_id: {session_id}]"

    @named_tool(name="TaskOutput")
    async def task_output(self, task_id: str, block: bool = True, timeout: int = 30000) -> str:
        """Retrieve output from a running or completed task.

        Args:
            task_id: The session ID to get output from.
            block: Whether to wait for completion (default: True).
            timeout: Max wait time in milliseconds (default: 30000).

        Returns:
            The task status and output.
        """
        _ = (block, timeout)  # Reserved for async/blocking behavior

        if task_id not in self._sessions:
            return f"Error: Session '{task_id}' not found."

        session = self._sessions[task_id]
        status = session.get("status", "unknown")

        if status == "completed":
            result = session.get("result", {})
            response = result.get("response", str(result)) if isinstance(result, dict) else str(result)
            return f"Status: completed\n\n{response}"

        return f"Status: {status}"
