"""
Agent System for Dana Language (Struct-like Refactor)

This module implements the agent type system using the same pattern as struct_system.py.
Agents are pure data containers; all method logic is handled externally and bound via a registry.
"""

from dataclasses import dataclass
from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.stdlib.core.reason_function import reason_function

from .abstract_dana_agent import AbstractDanaAgent


# --- Default Method Implementations ---
def default_plan_method(context: SandboxContext, agent_instance: "AgentInstance", task: str, user_context: dict | None = None) -> Any:
    """Default plan method that uses AI reasoning with type hint adaptation."""
    agent_fields = ", ".join(f"{k}: {v}" for k, v in agent_instance.to_dict().items())
    
    # Include user context in the prompt if provided
    context_info = ""
    if user_context:
        context_info = f"\nAdditional context: {user_context}"
    

    # Use a simple, clear prompt - let the POET-enhanced reason_function handle type-specific enhancements
    # The type hint information is already set by AssignmentHandler when processing typed assignments
    prompt = f"""You are {agent_instance.agent_type.name}, a specialized AI agent.
Agent configuration: {agent_fields}{context_info}

Task: {task}

Create a detailed plan to accomplish this task. Consider your specialized knowledge and capabilities."""
    
    return reason_function(context, prompt)


def default_solve_method(context: SandboxContext, agent_instance: "AgentInstance", problem: str, user_context: dict | None = None) -> Any:
    """Default solve method that uses AI reasoning with type hint adaptation."""
    agent_fields = ", ".join(f"{k}: {v}" for k, v in agent_instance.to_dict().items())
    
    # Include user context in the prompt if provided
    context_info = ""
    if user_context:
        context_info = f"\nAdditional context: {user_context}"
    
    # Use a simple, clear prompt - let the POET-enhanced reason_function handle type-specific enhancements
    # The type hint information is already set by AssignmentHandler when processing typed assignments
    prompt = f"""You are {agent_instance.agent_type.name}, a specialized AI agent.
Agent configuration: {agent_fields}{context_info}

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
class AgentInstance(AbstractDanaAgent):
    def __init__(self, agent_type: AgentType, values: dict[str, Any], context: SandboxContext):
        # Apply defaults, evaluating complex expressions if needed
        final_values = {}
        for field_name, default_value in agent_type.defaults.items():
            if isinstance(default_value, (str, int, float, bool, list, dict)):
                # Already evaluated simple value
                final_values[field_name] = default_value
            else:
                # AST node that needs evaluation
                try:
                    if hasattr(context, '_interpreter') and context._interpreter:
                        evaluated_value = context._interpreter.execute_statement(default_value, context)
                        final_values[field_name] = evaluated_value
                    else:
                        # No interpreter available - this shouldn't happen in normal execution
                        raise ValueError(f"Cannot evaluate default value for field '{field_name}': no interpreter available")
                except Exception as e:
                    # If evaluation fails, provide more specific error
                    raise ValueError(f"Failed to evaluate default value for field '{field_name}': {e}")
        
        # Apply provided values (overriding defaults)
        final_values.update(values)
        
        # Simple validation
        missing_fields = set(agent_type.fields.keys()) - set(final_values.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields for agent '{agent_type.name}': {sorted(missing_fields)}")
        
        self._type = agent_type
        self._values = final_values
        self._context = context

    @property
    def agent_card(self) -> dict[str, Any]:
        resources = self._values.get("resources", [])
        tools = []
        for resource in resources:
            tools.extend(resource.list_tools())
        skills = []
        for tool in tools:
            if "function" in tool:
                function = tool["function"]
                skills.append({"name": function.get("name", ""), "description": function.get("description", "")})
        return {
            "name": self._values.get("name", "General Purpose Agent"),
            "description": self._values.get("description", "General Purpose Agent"),
            "skills": skills
        }
    
    @property
    def skills(self) -> list[dict[str, Any]]:
        return self.agent_card.get("skills", [])

    @property
    def agent_type(self) -> AgentType:
        return self._type
    
    async def solve(self, task: str) -> str:
        """Solve a problem by delegating to the agent."""
        # Use the internal method resolution to avoid recursion
        method = self._type.get_method("solve")
        if method is not None:
            result = self._call_method(method, task)
            return str(result)
        return "No solve method available"

    def plan(self, task: str, user_context: dict | None = None) -> Any:
        return self.__getattr__("plan")(task, user_context)

    def _call_method(self, method, *args, **kwargs):
        """Helper to call method with correct parameters."""
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction
        
        # Handle 'context' kwarg conflict for both DanaFunction and Python functions
        context_value = None
        if 'context' in kwargs:
            context_value = kwargs.pop('context')
        
        if isinstance(method, DanaFunction):
            # For DanaFunction, handle parameter mapping
            if context_value is not None:
                # Check if the function actually has a 'context' parameter
                if hasattr(method, 'parameters') and 'context' in method.parameters:
                    # The function expects 'context', so we need to pass it correctly
                    # We'll add it to args in the right position
                    param_index = method.parameters.index('context')
                    # Adjust for the agent instance parameter (first param after execution context)
                    user_param_index = param_index - 1  # -1 because agent instance is first user param
                    
                    if user_param_index == len(args):
                        # Context should be the next positional argument
                        args = list(args) + [context_value]
                    elif user_param_index < len(args):
                        # Insert context at the right position
                        args = list(args)
                        args.insert(user_param_index, context_value)
            
            return method.execute(self._context, self, *args, **kwargs)
        else:
            # For Python functions (default methods), pass context_value as user_context kwarg
            if context_value is not None:
                kwargs['user_context'] = context_value
            
            return method(self._context, self, *args, **kwargs)
    
    def _call_method_with_current_context(self, method, *args, **kwargs):
        """Execute a method using the current execution context if available."""
        # Try to get the current execution context
        current_context = self._get_current_execution_context()
        if current_context:

            # We have current context with type hint info, but we need resources from stored context
            # Copy type hint information from current context to stored context
            type_hint = current_context.get("system:__current_assignment_type")
            if type_hint is not None:

                self._context.set("system:__current_assignment_type", type_hint)
            
            try:
                # Use the stored context (which has resources) now with type hint information
                if hasattr(method, 'execute'):
                    return method.execute(self._context, self, *args, **kwargs)
                else:
                    return method(self._context, self, *args, **kwargs)
            finally:
                # Clean up the type hint from stored context to avoid contamination
                if type_hint is not None:
                    self._context.set("system:__current_assignment_type", None)
        else:

            # Fallback to the original method
            return self._call_method(method, *args, **kwargs)
    
    def _get_current_execution_context(self):
        """Try to get the current execution context from the interpreter."""
        try:
            # Access the current interpreter and context through thread-local storage or similar
            # This is a bit of a hack, but necessary since agent methods need current context
            import threading
            current_thread = threading.current_thread()
            if hasattr(current_thread, 'dana_context'):
                return current_thread.dana_context
        except Exception:
            pass
        return None

    def __getattr__(self, name: str) -> Any:
        if name in self._type.fields:
            return self._values.get(name)
        if self._type.has_method(name):
            method = self._type.get_method(name)
            if method is not None:
                return lambda *args, **kwargs: self._call_method_with_current_context(method, *args, **kwargs)
        
        # NEW: Type-based fallback to global function registry
        fallback_method = self._try_global_function_fallback(name)
        if fallback_method is not None:
            return fallback_method
        
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

    def _try_global_function_fallback(self, method_name: str) -> Any | None:
        """Try to find a global function that matches the agent type."""
        
        # Get the function registry from the context
        function_registry = self._get_function_registry()
        if not function_registry:
            return None
        
        # Check if a function with this name exists in the registry
        if not function_registry.has(method_name):
            return None
        
        try:
            # Get the function from the registry
            func, func_type, metadata = function_registry.resolve(method_name)
            
            # Check if the function's first parameter type matches this agent's type
            if self._function_matches_agent_type(func, self._type.name):
                # Create a wrapper that calls the function with the agent as first argument
                def agent_method_wrapper(*args, **kwargs):
                    return function_registry.call(method_name, self._context, None, self, *args, **kwargs)
                
                return agent_method_wrapper
        
        except Exception:
            # If anything goes wrong, return None to fall back to normal error handling
            pass
        
        return None

    def _function_matches_agent_type(self, func: Any, agent_type_name: str) -> bool:
        """Check if a function's first parameter type hint matches the agent type."""
        
        try:
            # For Dana functions, we need to check the signature differently
            if hasattr(func, 'parameters') and func.parameters:
                first_param = func.parameters[0]
                if hasattr(first_param, 'type_hint') and first_param.type_hint:
                    return first_param.type_hint.name == agent_type_name
            
            # For Python functions, use inspect
            if hasattr(func, 'func') and callable(func.func):
                import inspect
                sig = inspect.signature(func.func)
                params = list(sig.parameters.values())
                
                if params:
                    first_param = params[0]
                    if first_param.annotation != inspect.Parameter.empty:
                        # Check if the annotation matches the agent type name
                        annotation_name = getattr(first_param.annotation, '__name__', str(first_param.annotation))
                        return annotation_name == agent_type_name
            
            # For other callable types, try to get signature info
            if callable(func):
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.values())
                
                if params:
                    first_param = params[0]
                    if first_param.annotation != inspect.Parameter.empty:
                        annotation_name = getattr(first_param.annotation, '__name__', str(first_param.annotation))
                        return annotation_name == agent_type_name
        
        except Exception:
            # If we can't determine the type, don't match
            pass
        
        return False

    def _get_function_registry(self):
        """Get the function registry from the context."""
        try:
            # Try to get the function registry from the context
            if hasattr(self._context, '_interpreter') and self._context._interpreter:
                return getattr(self._context._interpreter, 'function_registry', None)
            
            # Alternative: try to get it from thread-local storage
            import threading
            current_thread = threading.current_thread()
            if hasattr(current_thread, 'dana_function_registry'):
                return current_thread.dana_function_registry
        
        except Exception:
            pass
        
        return None

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
        
        # Extract default value if present
        if hasattr(field, 'default_value') and field.default_value is not None:
            if hasattr(field.default_value, 'value'):
                # Simple literal value (StringLiteral, NumberLiteral, etc.)
                defaults[field.name] = field.default_value.value
            else:
                # Complex expression - store AST node for later evaluation
                defaults[field.name] = field.default_value
    
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
