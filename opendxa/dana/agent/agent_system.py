"""
Agent System for Dana Language

This module implements the core agent type system by extending the existing struct system.
It provides AgentType and AgentInstance classes with built-in intelligence capabilities.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import TYPE_CHECKING, Any, Optional

from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function
from opendxa.dana.sandbox.parser.ast import AgentDefinition, AgentField

if TYPE_CHECKING:
    from opendxa.dana.sandbox.sandbox_context import SandboxContext


class AgentTypeRegistry:
    """Registry for agent types, similar to StructTypeRegistry."""

    def __init__(self):
        self._agent_types: dict[str, AgentType] = {}

    def register(self, agent_type: "AgentType") -> None:
        """Register an agent type."""
        self._agent_types[agent_type.name] = agent_type
        DXA_LOGGER.debug(f"Registered agent type: {agent_type.name}")

    def get(self, name: str) -> Optional["AgentType"]:
        """Get an agent type by name."""
        return self._agent_types.get(name)

    def list_types(self) -> list[str]:
        """List all registered agent type names."""
        return list(self._agent_types.keys())


class AgentType:
    """Agent type definition, extends struct concept with built-in capabilities."""

    def __init__(self, definition: AgentDefinition):
        self.name = definition.name
        self.fields = definition.fields
        self.definition = definition

        # Built-in capabilities will be added here
        self._capabilities = {"memory": True, "knowledge": True, "communication": True, "planning": True}
        
        # Custom methods storage (for method overriding)
        self._custom_methods: dict[str, Any] = {}

        DXA_LOGGER.debug(f"Created agent type: {self.name} with {len(self.fields)} fields")

    def create_instance(self, context: Optional["SandboxContext"] = None, **kwargs) -> "AgentInstance":
        """Create an instance of this agent type."""
        return AgentInstance(self, context=context, **kwargs)

    def get_field(self, name: str) -> AgentField | None:
        """Get a field by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None
    
    def add_method(self, method_name: str, method_func: Any) -> None:
        """Add a custom method to this agent type."""
        self._custom_methods[method_name] = method_func
        DXA_LOGGER.debug(f"Added custom method '{method_name}' to agent type '{self.name}'")
    
    def get_method(self, method_name: str) -> Any | None:
        """Get a custom method by name."""
        return self._custom_methods.get(method_name)
    
    def has_method(self, method_name: str) -> bool:
        """Check if this agent type has a custom method."""
        return method_name in self._custom_methods


class AgentInstance:
    """Instance of an agent with built-in intelligence capabilities."""

    def __init__(self, agent_type: AgentType, context: Optional["SandboxContext"] = None, **kwargs):
        self.agent_type = agent_type
        self.name = agent_type.name
        self.fields = {}
        self.context = context  # Store context for reasoning capabilities

        # Initialize fields with provided values or defaults
        for field in agent_type.fields:
            if field.name in kwargs:
                self.fields[field.name] = kwargs[field.name]
            elif field.default_value is not None:
                # For Phase 1, simple default handling
                self.fields[field.name] = self._evaluate_default(field.default_value)
            else:
                self.fields[field.name] = None

        # Built-in capabilities
        self._memory = {}
        self._conversation_history = []
        self._domain_facts = {}
        self._learned_patterns = []

        DXA_LOGGER.info(f"Created agent instance: {self.name}")

    def _evaluate_default(self, default_value) -> Any:
        """Evaluate default value expression. For Phase 1, handle simple cases."""
        # This is a simplified implementation for Phase 1
        if hasattr(default_value, "value"):
            return default_value.value
        return str(default_value)

    def __getattr__(self, name: str) -> Any:
        # First check if it's a field
        if name in self.fields:
            return self.fields[name]
        # Then check if it's a custom method
        if self.agent_type.has_method(name):
            custom_method = self.agent_type.get_method(name)
            if custom_method is not None:
                def bound_method(*args, **kwargs):
                    return custom_method(self, *args, **kwargs)
                return bound_method
        # If not found, raise AttributeError (do NOT try to resolve built-in methods here)
        available_fields = list(self.fields.keys())
        available_methods = list(self.agent_type._custom_methods.keys()) + ["plan", "solve", "remember", "recall"]
        raise AttributeError(f"Agent '{self.name}' has no field or method '{name}'. Available fields: {available_fields}, Available methods: {available_methods}")

    def plan(self, objective: str, context: dict[str, Any] | None = None) -> Any:
        """Built-in planning capability using AI reasoning with type hint support."""
        # Check if there's a custom plan method first
        if self.agent_type.has_method("plan"):
            custom_plan = self.agent_type.get_method("plan")
            if custom_plan is not None:
                return custom_plan(self, objective, context)
        
        # Otherwise use built-in implementation
        DXA_LOGGER.info(f"Agent {self.name} planning for objective: {objective}")

        # Build context-aware prompt for planning
        context_info = context or {}
        agent_fields = {k: v for k, v in self.fields.items() if v is not None}
        
        # Detect expected return type from calling context
        type_context = None
        expected_type = "list"  # Default to list
        
        if self.context:
            try:
                from opendxa.dana.sandbox.interpreter.context_detection import ContextDetector
                
                context_detector = ContextDetector()
                type_context = context_detector.detect_current_context(self.context)
                
                if type_context and type_context.expected_type:
                    expected_type = type_context.expected_type.lower()
                    DXA_LOGGER.debug(f"Detected expected type for plan(): {expected_type}")
                else:
                    DXA_LOGGER.debug("No type context detected, defaulting to list")
            except Exception as e:
                DXA_LOGGER.debug(f"Type detection failed: {e}, using default list")
        
        # Build type-aware prompt
        if expected_type == "list":
            prompt = f"""As a {self.name} agent, create a step-by-step action plan for this objective: {objective}

Agent Configuration:
{chr(10).join(f"- {k}: {v}" for k, v in agent_fields.items())}

Additional Context:
{chr(10).join(f"- {k}: {v}" for k, v in context_info.items())}

Please provide a clear list of actionable steps that leverage this agent's domain expertise. 
Return ONLY a JSON array of step strings, like: ["Step 1 description", "Step 2 description", ...]
Do not include markdown formatting or explanations."""

        elif expected_type == "dict":
            prompt = f"""As a {self.name} agent, create a detailed plan for this objective: {objective}

Agent Configuration:
{chr(10).join(f"- {k}: {v}" for k, v in agent_fields.items())}

Additional Context:
{chr(10).join(f"- {k}: {v}" for k, v in context_info.items())}

Please provide a structured plan with analysis and steps. 
Return ONLY a JSON object with keys like: {{"objective": "...", "analysis": "...", "steps": [...], "confidence": 0.8}}
Do not include markdown formatting."""

        else:
            # Generic prompt for other types
            prompt = f"""As a {self.name} agent, create a plan for this objective: {objective}

Agent Configuration:
{chr(10).join(f"- {k}: {v}" for k, v in agent_fields.items())}

Additional Context:
{chr(10).join(f"- {k}: {v}" for k, v in context_info.items())}

Please provide a {expected_type} response that represents a plan leveraging this agent's domain expertise."""

        # Use reason function for intelligent planning
        try:
            if self.context:
                reasoning_result = reason_function(context=self.context, prompt=prompt, options={
                    "temperature": 0.7,
                    "format": "json" if expected_type in ["list", "dict"] else "text",
                    "system_message": f"You are an expert {self.name} agent with specialized domain knowledge."
                })
            else:
                reasoning_result = f"Intelligent plan for {objective} using {self.name} domain expertise"
        except Exception as e:
            DXA_LOGGER.warning(f"Reason function failed for agent {self.name}: {e}, using fallback")
            reasoning_result = f"Expert plan for {objective} using {self.name} domain knowledge"

        # Apply semantic coercion to match expected type
        result = reasoning_result
        if type_context and type_context.expected_type and reasoning_result is not None:
            try:
                from opendxa.dana.sandbox.interpreter.enhanced_coercion import SemanticCoercer
                
                semantic_coercer = SemanticCoercer()
                coerced_result = semantic_coercer.coerce_value(
                    reasoning_result, 
                    type_context.expected_type, 
                    context=f"agent_plan_{type_context.expected_type}"
                )
                
                if coerced_result != reasoning_result:
                    DXA_LOGGER.debug(f"Applied semantic coercion: {type(reasoning_result)} → {type(coerced_result)}")
                
                result = coerced_result
            except Exception as coercion_error:
                DXA_LOGGER.debug(f"Semantic coercion failed: {coercion_error}, using original result")

        # If no coercion occurred and we expect a list, provide default structure
        if expected_type == "list" and not isinstance(result, list):
            result = [
                f"Analyze {objective} with {self.name} expertise",
                "Apply domain-specific knowledge and best practices", 
                "Generate optimized solution approach",
                "Execute plan with monitoring and validation"
            ]

        # Store in memory (always store the structured plan for internal use)
        plan_record = {
            "objective": objective,
            "agent": self.name,
            "context": context_info,
            "result": result,
            "result_type": type(result).__name__,
            "steps": result if isinstance(result, list) else [
                f"Analyze {objective} with {self.name} expertise",
                "Apply domain-specific knowledge and best practices",
                "Generate optimized solution approach", 
                "Execute plan with monitoring and validation"
            ],
            "estimated_duration": "varies based on complexity",
            "confidence": 0.8,
        }

        self._memory[f"plan_{len(self._memory)}"] = plan_record
        self._conversation_history.append(
            {
                "type": "plan",
                "objective": objective,
                "timestamp": "now",  # Simplified for Phase 1
                "plan": plan_record,
            }
        )

        return result

    def solve(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Built-in problem-solving capability using AI reasoning."""
        # Check if there's a custom solve method first
        if self.agent_type.has_method("solve"):
            custom_solve = self.agent_type.get_method("solve")
            if custom_solve is not None:
                return custom_solve(self, problem, context)
        
        # Otherwise use built-in implementation
        DXA_LOGGER.info(f"Agent {self.name} solving problem: {problem}")

        # Build context-aware prompt for problem solving
        context_info = context or {}
        agent_fields = {k: v for k, v in self.fields.items() if v is not None}
        
        prompt = f"""As a {self.name} agent, analyze and solve this problem: {problem}

Agent Configuration:
{chr(10).join(f"- {k}: {v}" for k, v in agent_fields.items())}

Additional Context:
{chr(10).join(f"- {k}: {v}" for k, v in context_info.items())}

Please provide a comprehensive solution that:
1. Analyzes the problem with domain expertise
2. Identifies the best approach using specialized knowledge
3. Provides specific recommendations
4. Considers potential risks and mitigation strategies

Format the response as a detailed solution with clear recommendations."""

        # Use reason function for intelligent problem solving
        try:
            if self.context:
                reasoning_result = reason_function(context=self.context, prompt=prompt, options={
                    "temperature": 0.7,
                    "format": "text",
                    "system_message": f"You are an expert {self.name} agent with specialized domain knowledge."
                })
            else:
                reasoning_result = f"Intelligent solution for {problem} using {self.name} domain expertise"
        except Exception as e:
            DXA_LOGGER.warning(f"Reason function failed for agent {self.name}: {e}, using fallback")
            reasoning_result = f"Expert solution for {problem} using {self.name} domain knowledge"

        # Structure the solution response
        solution = {
            "problem": problem,
            "agent": self.name,
            "solution": reasoning_result,
            "recommendations": [
                f"Apply {self.name} domain expertise to analyze the problem",
                "Use specialized knowledge and best practices",
                "Implement solution with monitoring and validation"
            ],
            "confidence": 0.7,
            "estimated_effort": "varies based on complexity",
            "risks": ["Domain-specific risks should be assessed"],
            "mitigation": ["Follow established protocols and best practices"]
        }

        # Store in memory
        self._memory[f"solve_{len(self._memory)}"] = solution
        self._conversation_history.append(
            {
                "type": "solve",
                "problem": problem,
                "timestamp": "now",  # Simplified for Phase 1
                "solution": solution,
            }
        )

        return solution

    def remember(self, key: str, value: Any) -> None:
        """Store information in memory."""
        self._memory[key] = value
        DXA_LOGGER.debug(f"Agent {self.name} remembered: {key}")

    def recall(self, key: str) -> Any:
        """Retrieve information from memory."""
        value = self._memory.get(key)
        if value:
            DXA_LOGGER.debug(f"Agent {self.name} recalled: {key}")
        return value

    def get_field_value(self, field_name: str) -> Any:
        """Get the value of a field."""
        return self.fields.get(field_name)

    def set_field_value(self, field_name: str, value: Any) -> None:
        """Set the value of a field."""
        if self.agent_type.get_field(field_name):
            self.fields[field_name] = value
            DXA_LOGGER.debug(f"Agent {self.name} field {field_name} set to {value}")
        else:
            raise ValueError(f"Unknown field: {field_name}")

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """Get conversation history."""
        return self._conversation_history.copy()

    def get_memory_keys(self) -> list[str]:
        """Get all memory keys."""
        return list(self._memory.keys())

    def __str__(self) -> str:
        return f"{self.name}({', '.join(f'{k}={v}' for k, v in self.fields.items())})"


# Global registry instance
_agent_registry = AgentTypeRegistry()


def register_agent_type(agent_type: AgentType) -> None:
    """Register an agent type globally."""
    _agent_registry.register(agent_type)


def get_agent_type(name: str) -> AgentType | None:
    """Get an agent type by name."""
    return _agent_registry.get(name)


def list_agent_types() -> list[str]:
    """List all registered agent types."""
    return _agent_registry.list_types()
