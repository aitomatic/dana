"""
Text Problem Solving Template for the Context Engineering Framework.
"""

from typing import Any

from ..base import TextTemplate


class TextProblemSolvingTemplate(TextTemplate):
    """Template for problem-solving prompts in text format."""

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble problem-solving prompt in text format."""
        text_parts = []

        # Query
        text_parts.append(f"PROBLEM: {query}\n")

        # Problem context
        if "problem_statement" in context:
            text_parts.append(f"OBJECTIVE: {context.get('objective', '')}\n")
            text_parts.append(f"DEPTH: {context.get('current_depth', 0)}\n")

            # Constraints
            if context.get("constraints"):
                text_parts.append("CONSTRAINTS:\n")
                for key, value in context["constraints"].items():
                    text_parts.append(f"  - {key}: {value}\n")

            # Assumptions
            if context.get("assumptions"):
                text_parts.append("ASSUMPTIONS:\n")
                for assumption in context["assumptions"]:
                    text_parts.append(f"  - {assumption}\n")

        # Workflow context
        if "workflow_current_workflow" in context:
            text_parts.append(f"CURRENT WORKFLOW: {context['workflow_current_workflow']}\n")
            text_parts.append(f"WORKFLOW STATE: {context.get('workflow_workflow_state', '')}\n")

        # Conversation history
        if context.get("conversation_history"):
            text_parts.append("CONVERSATION HISTORY:\n")
            text_parts.append(f"{context['conversation_history']}\n")

        # Recent events
        if context.get("recent_events"):
            text_parts.append("RECENT EVENTS:\n")
            for event in context["recent_events"]:
                text_parts.append(f"  - {event}\n")

        return "".join(text_parts)

    def get_required_context(self) -> list[str]:
        return ["query"]

    def get_optional_context(self) -> list[str]:
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
        ]
