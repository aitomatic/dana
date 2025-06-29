"""
Agent System for Dana Language (Struct-like Refactor)

This module implements the agent type system using the same pattern as struct_system.py.
Agents are pure data containers; all method logic is handled externally and bound via a registry.
"""

from dataclasses import dataclass
from typing import Any
from opendxa.dana.sandbox.sandbox_context import SandboxContext
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function

# --- Default Method Implementations ---
def default_plan_method(context: SandboxContext, agent_instance: "AgentInstance", task: str) -> Any:
    """Default plan method that uses AI reasoning with type hint adaptation."""
    agent_fields = ", ".join(f"{k}: {v}" for k, v in agent_instance.to_dict().items())
    prompt = f"""You are {agent_instance.agent_type.name}, a specialized AI agent.
Agent configuration: {agent_fields}

Task: {task}

Create a detailed plan to accomplish this task. Consider your specialized knowledge and capabilities."""
    
    return reason_function(context, prompt)


def default_solve_method(context: SandboxContext, agent_instance: "AgentInstance", problem: str) -> Any:
    """Default solve method that uses AI reasoning with type hint adaptation."""
    agent_fields = ", ".join(f"{k}: {v}" for k, v in agent_instance.to_dict().items())
    prompt = f"""You are {agent_instance.agent_type.name}, a specialized AI agent.
Agent configuration: {agent_fields}

Problem: {problem}

Analyze and solve this problem using your specialized knowledge and capabilities. Provide a comprehensive solution."""
    
    return reason_function(context, prompt)

# --- AgentType: Like StructType ---
@dataclass
class AgentType:
    name: str
    fields: dict[str, str]  # field name -> type name
    field_order: list[str]
    defaults: dict[str, Any] = None
    _custom_methods: dict[str, Any] = None

    def __post_init__(self):
        if self._custom_methods is None:
            self._custom_methods = {}
        if self.defaults is None:
            self.defaults = {}

    def add_method(self, method_name: str, method_func: Any) -> None:
        self._custom_methods[method_name] = method_func

    def get_method(self, method_name: str) -> Any | None:
        if method_name in self._custom_methods:
            return self._custom_methods[method_name]
        if method_name == "plan":
            return default_plan_method
        elif method_name == "solve":
            return default_solve_method
        return None

    def has_method(self, method_name: str) -> bool:
        return method_name in self._custom_methods or method_name in ["plan", "solve"]

# --- AgentInstance: Like StructInstance ---
class AgentInstance:
    def __init__(self, agent_type: AgentType, values: dict[str, Any], context: SandboxContext):
        # Apply defaults, then provided values
        final_values = agent_type.defaults.copy()
        final_values.update(values)
        
        # Simple validation
        missing_fields = set(agent_type.fields.keys()) - set(final_values.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields for agent '{agent_type.name}': {sorted(missing_fields)}")
        
        self._type = agent_type
        self._values = final_values
        self._context = context

    @property
    def agent_type(self) -> AgentType:
        return self._type

    def _call_method(self, method, *args, **kwargs):
        """Helper to call method with correct parameters."""
        from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction
        if isinstance(method, DanaFunction):
            return method.execute(self._context, self, *args, **kwargs)
        else:
            return method(self._context, self, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        if name in self._type.fields:
            return self._values.get(name)
        if self._type.has_method(name):
            method = self._type.get_method(name)
            if method is not None:
                return lambda *args, **kwargs: self._call_method(method, *args, **kwargs)
        raise AttributeError(f"Agent '{self._type.name}' has no field or method '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        if hasattr(self, "_type") and name in self._type.fields:
            self._values[name] = value
        else:
            super().__setattr__(name, value)

    def call_method(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        if self._type.has_method(method_name):
            method = self._type.get_method(method_name)
            if method is not None:
                return self._call_method(method, *args, **kwargs)
        raise AttributeError(f"Agent '{self._type.name}' has no method '{method_name}'")

    def to_dict(self) -> dict[str, Any]:
        return self._values.copy()

    def __repr__(self) -> str:
        field_strs = [f"{name}={repr(self._values.get(name))}" for name in self._type.field_order]
        return f"{self._type.name}({', '.join(field_strs)})"

# --- AgentTypeRegistry: Like StructTypeRegistry ---
class AgentTypeRegistry:
    _types: dict[str, AgentType] = {}

    @classmethod
    def register(cls, agent_type: AgentType) -> None:
        cls._types[agent_type.name] = agent_type

    @classmethod
    def get(cls, agent_name: str) -> AgentType | None:
        return cls._types.get(agent_name)

    @classmethod
    def exists(cls, agent_name: str) -> bool:
        return agent_name in cls._types

    @classmethod
    def list_types(cls) -> list[str]:
        return sorted(cls._types.keys())

    @classmethod
    def clear(cls) -> None:
        cls._types.clear()

    @classmethod
    def create_instance(cls, agent_name: str, values: dict[str, Any], context: SandboxContext) -> AgentInstance:
        agent_type = cls.get(agent_name)
        if agent_type is None:
            raise ValueError(f"Unknown agent type '{agent_name}'")
        return AgentInstance(agent_type, values, context=context)

# --- Helper for AST-based registration (mirroring struct_system) ---
def create_agent_type_from_ast(agent_def) -> AgentType:
    fields = {}
    field_order = []
    defaults = {}
    
    for field in agent_def.fields:
        fields[field.name] = field.type_hint.name
        field_order.append(field.name)
        
        # Simple default value extraction
        if hasattr(field, 'default_value') and field.default_value is not None:
            if hasattr(field.default_value, 'value'):
                defaults[field.name] = field.default_value.value
    
    return AgentType(name=agent_def.name, fields=fields, field_order=field_order, defaults=defaults)

def register_agent_from_ast(agent_def) -> AgentType:
    agent_type = create_agent_type_from_ast(agent_def)
    AgentTypeRegistry.register(agent_type)
    return agent_type

def create_agent_instance(agent_name: str, context: SandboxContext, **kwargs) -> AgentInstance:
    return AgentTypeRegistry.create_instance(agent_name, kwargs, context=context)

def register_agent_method_from_function_def(node, dana_func):
    """Register function as agent method if first parameter is an agent type."""
    if not hasattr(node, 'parameters') or not node.parameters:
        return
    first_param = node.parameters[0]
    if hasattr(first_param, 'type_hint') and first_param.type_hint and hasattr(first_param.type_hint, 'name'):
        agent_type_name = first_param.type_hint.name
        agent_type = AgentTypeRegistry.get(agent_type_name)
        if agent_type is not None:
            method_name = node.name.name if hasattr(node.name, 'name') else str(node.name)
            agent_type.add_method(method_name, dana_func)
