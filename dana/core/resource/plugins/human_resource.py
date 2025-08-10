"""
Human Resource

Provides human-in-the-loop interaction capabilities.
Migrated from core to stdlib as a plugin.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import datetime

from dana.core.resource import BaseResource, ResourceState


@dataclass
class HumanResource(BaseResource):
    """Human interaction resource."""

    kind: str = "human"
    interface_type: str = "console"  # console, web, api
    timeout: int = 300  # 5 minutes default
    prompt_template: str = "{question}"
    require_confirmation: bool = True

    # Interaction history
    _interaction_history: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _pending_responses: Dict[str, Any] = field(default_factory=dict, init=False)

    def initialize(self) -> bool:
        """Initialize human interaction interface."""
        print(f"Initializing human interface '{self.name}' via {self.interface_type}")

        self.state = ResourceState.RUNNING
        self.capabilities = ["ask", "get_feedback", "confirm", "choose"]
        return True

    def cleanup(self) -> bool:
        """Clean up human interface."""
        self._interaction_history.clear()
        self._pending_responses.clear()
        self.state = ResourceState.TERMINATED
        return True

    def query(self, request: Any) -> Any:
        """Standard query interface."""
        if not self.is_running():
            return {"error": f"Human resource {self.name} not available"}

        # Parse request
        if isinstance(request, str):
            # Treat as question to ask
            return self.ask(request)
        elif isinstance(request, dict):
            operation = request.get("operation", "ask")
            if operation == "ask":
                return self.ask(request.get("question", ""))
            elif operation == "get_feedback":
                return self.get_feedback(request.get("content", ""))
            elif operation == "confirm":
                return self.confirm(request.get("action", ""))
            elif operation == "choose":
                return self.choose(request.get("question", ""), request.get("options", []))

        return {"error": "Invalid request format"}

    def ask(self, question: str) -> Dict[str, Any]:
        """Ask human a question."""
        if not self.is_running():
            return {"error": f"Human resource {self.name} not available"}

        formatted_question = self.prompt_template.format(question=question)

        # Record interaction
        interaction = {
            "type": "question",
            "question": question,
            "formatted": formatted_question,
            "timestamp": datetime.datetime.now().isoformat(),
            "interface": self.interface_type,
        }

        # Simulate human response based on interface type
        if self.interface_type == "console":
            # In real implementation, would read from console
            response = f"[Simulated console response to: {question[:50]}...]"
        elif self.interface_type == "web":
            # In real implementation, would wait for web response
            response = f"[Simulated web response to: {question[:50]}...]"
        else:
            response = f"[Simulated API response to: {question[:50]}...]"

        interaction["response"] = response
        interaction["response_time"] = datetime.datetime.now().isoformat()
        self._interaction_history.append(interaction)

        return {"success": True, "question": question, "response": response, "interface": self.interface_type, "timeout": self.timeout}

    def get_feedback(self, content: str) -> Dict[str, Any]:
        """Get human feedback on content."""
        if not self.is_running():
            return {"error": f"Human resource {self.name} not available"}

        # Record interaction
        interaction = {
            "type": "feedback",
            "content": content[:200],  # Store truncated version
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Simulate feedback
        feedback = {
            "content": content[:100] + "..." if len(content) > 100 else content,
            "rating": 7,  # Simulated rating out of 10
            "suggestions": ["Consider adding more detail", "Good structure overall", "Check for accuracy"],
            "approved": True,
            "comments": "Looks good with minor suggestions",
        }

        interaction["feedback"] = feedback
        self._interaction_history.append(interaction)

        return {"success": True, "feedback": feedback, "interface": self.interface_type}

    def confirm(self, action: str) -> Dict[str, Any]:
        """Get human confirmation for an action."""
        if not self.is_running():
            return {"error": f"Human resource {self.name} not available"}

        if not self.require_confirmation:
            # Auto-approve if confirmation not required
            return {"success": True, "action": action, "confirmed": True, "auto_approved": True}

        # Record interaction
        interaction = {"type": "confirmation", "action": action, "timestamp": datetime.datetime.now().isoformat()}

        # Simulate confirmation (in real implementation, would wait for human)
        import random

        confirmed = random.choice([True, True, True, False])  # 75% approval rate

        interaction["confirmed"] = confirmed
        interaction["response_time"] = datetime.datetime.now().isoformat()
        self._interaction_history.append(interaction)

        return {
            "success": True,
            "action": action,
            "confirmed": confirmed,
            "reason": "User approved" if confirmed else "User declined",
            "interface": self.interface_type,
        }

    def choose(self, question: str, options: List[str]) -> Dict[str, Any]:
        """Ask human to choose from options."""
        if not self.is_running():
            return {"error": f"Human resource {self.name} not available"}

        if not options:
            return {"error": "No options provided"}

        # Record interaction
        interaction = {"type": "choice", "question": question, "options": options, "timestamp": datetime.datetime.now().isoformat()}

        # Simulate choice (in real implementation, would wait for human)
        import random

        chosen_index = random.randint(0, len(options) - 1)
        chosen = options[chosen_index]

        interaction["chosen"] = chosen
        interaction["chosen_index"] = chosen_index
        interaction["response_time"] = datetime.datetime.now().isoformat()
        self._interaction_history.append(interaction)

        return {
            "success": True,
            "question": question,
            "options": options,
            "chosen": chosen,
            "chosen_index": chosen_index,
            "interface": self.interface_type,
        }

    def get_history(self) -> List[Dict[str, Any]]:
        """Get interaction history."""
        return self._interaction_history.copy()

    def clear_history(self):
        """Clear interaction history."""
        self._interaction_history.clear()
        return {"success": True, "message": "History cleared"}

    def get_stats(self) -> Dict[str, Any]:
        """Get human resource statistics."""
        # Calculate interaction statistics
        interaction_types = {}
        for interaction in self._interaction_history:
            itype = interaction.get("type", "unknown")
            interaction_types[itype] = interaction_types.get(itype, 0) + 1

        return {
            "name": self.name,
            "kind": self.kind,
            "interface_type": self.interface_type,
            "state": self.state.value,
            "timeout": self.timeout,
            "require_confirmation": self.require_confirmation,
            "total_interactions": len(self._interaction_history),
            "interaction_types": interaction_types,
            "capabilities": self.capabilities,
        }
