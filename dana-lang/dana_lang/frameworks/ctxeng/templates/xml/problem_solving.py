"""
XML Problem Solving Template for the Context Engineering Framework.
"""

from typing import Any

from ..base import XMLTemplate


class XMLProblemSolvingTemplate(XMLTemplate):
    """Template for problem-solving prompts with rich context.

    This template is optimized for complex problem solving, planning, and execution tasks.
    It provides comprehensive context including problem state, workflow status, and execution history.
    """

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble problem-solving prompt in XML format.

        Args:
            query: The problem to be solved
            context: Dictionary containing problem-solving context data
            options: Additional configuration options (unused in problem-solving template)

        Context Dictionary Expected Keys:
            query: The problem statement (required)

            Problem Context (optional):
            - problem_statement: Detailed problem description
            - objective: What needs to be accomplished
            - current_depth: Current recursion depth (for recursive strategies)
            - constraints: Dictionary of problem constraints
            - assumptions: List of assumptions about the problem

            Workflow Context (optional):
            - workflow_current_workflow: Name/ID of current workflow
            - workflow_workflow_state: Current state of the workflow

            Execution Context (optional):
            - conversation_history: Summary of previous conversation turns
            - recent_events: List of recent execution events
            - additional_context: Any other relevant context data

        Context Usage:
            - problem_statement: Triggers detailed problem context section
            - current_depth: Important for recursive strategies to prevent infinite loops
            - constraints: Provides boundaries and limitations for the solution
            - workflow_context: Shows current execution state and progress
            - conversation_history: Maintains context across multiple interactions
            - recent_events: Provides execution timeline and learning opportunities

        Returns:
            XML-formatted prompt string with comprehensive problem-solving context
        """
        xml_parts = ["<context>"]

        # Query
        xml_parts.append(self._build_xml_element("query", query))

        # Problem context
        if "problem_statement" in context:
            xml_parts.append("<problem_context>")
            xml_parts.append(self._build_xml_element("objective", context.get("objective", "")))
            xml_parts.append(self._build_xml_element("current_depth", str(context.get("current_depth", 0))))

            # Constraints
            if context.get("constraints"):
                xml_parts.append("<constraints>")
                for key, value in context["constraints"].items():
                    xml_parts.append(self._build_xml_element("constraint", str(value), {"type": key}))
                xml_parts.append("</constraints>")

            # Assumptions
            if context.get("assumptions"):
                xml_parts.append("<assumptions>")
                for assumption in context["assumptions"]:
                    xml_parts.append(self._build_xml_element("assumption", assumption))
                xml_parts.append("</assumptions>")

            xml_parts.append("</problem_context>")

        # Workflow context
        if "workflow_current_workflow" in context:
            xml_parts.append("<workflow_context>")
            xml_parts.append(self._build_xml_element("current_workflow", context["workflow_current_workflow"]))
            xml_parts.append(self._build_xml_element("workflow_state", context.get("workflow_workflow_state", "")))
            xml_parts.append("</workflow_context>")

        # Conversation history
        if context.get("conversation_history"):
            xml_parts.append("<conversation_history>")
            xml_parts.append(self._build_xml_element("summary", context["conversation_history"]))
            xml_parts.append("</conversation_history>")

        # Recent events
        if context.get("recent_events"):
            xml_parts.append("<recent_events>")
            for event in context["recent_events"]:
                xml_parts.append(self._build_xml_element("event", event))
            xml_parts.append("</recent_events>")

        # Additional context
        if context.get("additional_context"):
            xml_parts.append("<additional_context>")
            for key, value in context["additional_context"].items():
                xml_parts.append(self._build_xml_element(key, str(value)))
            xml_parts.append("</additional_context>")

        xml_parts.append("</context>")

        return "".join(xml_parts)

    def get_required_context(self) -> list[str]:
        """Get list of required context keys for this template.

        Returns:
            List of context keys that must be present for the template to work
        """
        return ["query"]

    def get_optional_context(self) -> list[str]:
        """Get list of optional context keys for this template.

        Returns:
            List of context keys that enhance problem solving but aren't required.
            This template can work with minimal context but provides richer prompts
            when more context is available.
        """
        return [
            "problem_statement",
            "objective",
            "current_depth",
            "constraints",
            "assumptions",
            "workflow_current_workflow",
            "workflow_workflow_state",
            "conversation_history",
            "recent_events",
            "additional_context",
        ]
