"""
Knowledge Resource

Provides structured knowledge operations for Dana agents.
Migrated from core to stdlib as a plugin.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import json

from dana.core.resource import BaseResource, ResourceState


@dataclass
class KnowledgeResource(BaseResource):
    """Knowledge resource for structured knowledge operations."""

    kind: str = "knowledge"
    sources: List[str] = field(default_factory=list)
    domain: str = "general"

    # Knowledge storage
    _facts: Dict[str, List[str]] = field(default_factory=dict, init=False)
    _plans: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)
    _heuristics: Dict[str, List[str]] = field(default_factory=dict, init=False)

    def initialize(self) -> bool:
        """Initialize knowledge resource."""
        print(f"Initializing knowledge resource '{self.name}' for domain '{self.domain}'")

        # Load knowledge from sources if provided
        for source in self.sources:
            self._load_knowledge_source(source)

        # Add some default knowledge
        self._initialize_default_knowledge()

        self.state = ResourceState.RUNNING
        self.capabilities = ["get_facts", "get_plan", "get_heuristics", "add_knowledge"]
        return True

    def _load_knowledge_source(self, source: str):
        """Load knowledge from a source file."""
        try:
            with open(source, "r") as f:
                data = json.load(f)
                if "facts" in data:
                    self._facts.update(data["facts"])
                if "plans" in data:
                    self._plans.update(data["plans"])
                if "heuristics" in data:
                    self._heuristics.update(data["heuristics"])
            print(f"Loaded knowledge from {source}")
        except Exception as e:
            print(f"Could not load knowledge from {source}: {e}")

    def _initialize_default_knowledge(self):
        """Initialize with default knowledge base."""
        # Default facts
        self._facts["general"] = [
            "Knowledge can be facts, plans, or heuristics",
            "Agents use knowledge to make decisions",
            "Knowledge can be domain-specific",
        ]

        # Default plans
        self._plans["problem_solving"] = {
            "steps": [
                "Understand the problem",
                "Gather relevant information",
                "Generate possible solutions",
                "Evaluate solutions",
                "Implement chosen solution",
                "Verify results",
            ],
            "estimated_time": "varies",
        }

        # Default heuristics
        self._heuristics["general"] = [
            "Start with the simplest solution",
            "Break complex problems into smaller parts",
            "Consider edge cases",
            "Test assumptions early",
        ]

    def cleanup(self) -> bool:
        """Clean up knowledge resource."""
        self._facts.clear()
        self._plans.clear()
        self._heuristics.clear()
        self.state = ResourceState.TERMINATED
        return True

    def query(self, request: Any) -> Any:
        """Standard query interface."""
        if not self.is_running():
            return {"error": f"Knowledge resource {self.name} not running"}

        # Parse request
        if isinstance(request, str):
            # Treat as topic for facts
            return self.get_facts(request)
        elif isinstance(request, dict):
            operation = request.get("operation", "get_facts")
            if operation == "get_facts":
                return self.get_facts(request.get("topic", "general"))
            elif operation == "get_plan":
                return self.get_plan(request.get("goal", ""))
            elif operation == "get_heuristics":
                return self.get_heuristics(request.get("task", "general"))
            elif operation == "add_knowledge":
                return self.add_knowledge(request.get("type", "fact"), request.get("topic", "general"), request.get("content", ""))

        return {"error": "Invalid request format"}

    def get_facts(self, topic: str) -> Dict[str, Any]:
        """Extract facts about a topic."""
        if not self.is_running():
            return {"error": f"Knowledge resource {self.name} not running"}

        # Look for exact match first
        if topic in self._facts:
            facts = self._facts[topic]
        else:
            # Look for related topics
            facts = []
            for key, values in self._facts.items():
                if topic.lower() in key.lower() or key.lower() in topic.lower():
                    facts.extend(values)

            # If still no facts, return general facts
            if not facts:
                facts = self._facts.get("general", ["No specific facts available"])

        return {"topic": topic, "facts": facts, "confidence": 0.85 if facts else 0.3, "domain": self.domain}

    def get_plan(self, goal: str) -> Dict[str, Any]:
        """Generate plan for achieving a goal."""
        if not self.is_running():
            return {"error": f"Knowledge resource {self.name} not running"}

        # Look for specific plan
        if goal in self._plans:
            plan = self._plans[goal]
        else:
            # Look for related plans
            for key, value in self._plans.items():
                if goal.lower() in key.lower() or key.lower() in goal.lower():
                    plan = value
                    break
            else:
                # Use default problem-solving plan
                plan = self._plans.get(
                    "problem_solving", {"steps": ["Analyze goal", "Create plan", "Execute"], "estimated_time": "unknown"}
                )

        return {"goal": goal, "plan": plan, "domain": self.domain}

    def get_heuristics(self, task: str) -> Dict[str, Any]:
        """Provide heuristics for a task."""
        if not self.is_running():
            return {"error": f"Knowledge resource {self.name} not running"}

        # Look for specific heuristics
        if task in self._heuristics:
            heuristics = self._heuristics[task]
        else:
            # Look for related heuristics
            heuristics = []
            for key, values in self._heuristics.items():
                if task.lower() in key.lower() or key.lower() in task.lower():
                    heuristics.extend(values)

            # Add general heuristics
            heuristics.extend(self._heuristics.get("general", []))

        return {
            "task": task,
            "heuristics": heuristics[:5],  # Limit to top 5
            "applicability": 0.9 if heuristics else 0.5,
            "domain": self.domain,
        }

    def add_knowledge(self, knowledge_type: str, topic: str, content: Any) -> Dict[str, Any]:
        """Add new knowledge to the resource."""
        if not self.is_running():
            return {"error": f"Knowledge resource {self.name} not running"}

        if knowledge_type == "fact":
            if topic not in self._facts:
                self._facts[topic] = []
            if isinstance(content, list):
                self._facts[topic].extend(content)
            else:
                self._facts[topic].append(str(content))
            return {"success": True, "added": f"Facts for {topic}"}

        elif knowledge_type == "plan":
            self._plans[topic] = content if isinstance(content, dict) else {"steps": [str(content)]}
            return {"success": True, "added": f"Plan for {topic}"}

        elif knowledge_type == "heuristic":
            if topic not in self._heuristics:
                self._heuristics[topic] = []
            if isinstance(content, list):
                self._heuristics[topic].extend(content)
            else:
                self._heuristics[topic].append(str(content))
            return {"success": True, "added": f"Heuristics for {topic}"}

        else:
            return {"error": f"Unknown knowledge type: {knowledge_type}"}

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge resource statistics."""
        return {
            "name": self.name,
            "kind": self.kind,
            "domain": self.domain,
            "state": self.state.value,
            "fact_topics": len(self._facts),
            "total_facts": sum(len(facts) for facts in self._facts.values()),
            "plan_count": len(self._plans),
            "heuristic_topics": len(self._heuristics),
            "total_heuristics": sum(len(h) for h in self._heuristics.values()),
            "capabilities": self.capabilities,
        }
