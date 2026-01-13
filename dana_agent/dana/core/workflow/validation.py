"""
Validation decorators for workflow inputs and outputs.

Provides @validate_input and @validate_output decorators for declarative
validation of workflow parameters and return values.
"""

from collections.abc import Callable
from functools import wraps

from dana.common.protocols import DictParams


def validate_input(**schema) -> Callable:
    """
    Decorator to validate workflow input parameters.

    Args:
        **schema: Validation rules for each parameter. Each rule can specify:
            - required (bool): Whether the parameter is required (default: False)
            - type (type | tuple): Expected type(s)
            - enum (list): List of allowed values
            - min_value (int/float): Minimum value for numbers
            - max_value (int/float): Maximum value for numbers
            - min_length (int): Minimum length for strings/lists
            - max_length (int): Maximum length for strings/lists
            - validator (callable): Custom validation function
            - default: Default value if not provided

    Example:
        @validate_input(
            query={"required": True, "type": str, "min_length": 1},
            max_results={"type": int, "min_value": 1, "max_value": 100, "default": 10}
        )
        def _do_execute(self, **kwargs) -> DictParams:
            # kwargs are already validated
            pass

    Returns:
        Decorated function that validates inputs before execution.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, **kwargs) -> DictParams:
            # Validate each parameter according to schema
            validated_kwargs = {}

            for param_name, rules in schema.items():
                value = kwargs.get(param_name)

                # Handle defaults
                if value is None and "default" in rules:
                    value = rules["default"]
                    validated_kwargs[param_name] = value

                # Check required
                if rules.get("required", False) and value is None:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Required parameter '{param_name}' is missing",
                        "field": param_name,
                    }

                # If value is None and not required, skip further validation
                if value is None:
                    continue

                # Type validation
                if "type" in rules:
                    expected_type = rules["type"]
                    if not isinstance(value, expected_type):
                        type_name = expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Parameter '{param_name}' must be of type {type_name}, got {type(value).__name__}",
                            "field": param_name,
                        }

                # Enum validation
                if "enum" in rules and value not in rules["enum"]:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Parameter '{param_name}' must be one of {rules['enum']}, got '{value}'",
                        "field": param_name,
                    }

                # Min/max value validation (for numbers)
                if "min_value" in rules and value < rules["min_value"]:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Parameter '{param_name}' must be >= {rules['min_value']}, got {value}",
                        "field": param_name,
                    }

                if "max_value" in rules and value > rules["max_value"]:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Parameter '{param_name}' must be <= {rules['max_value']}, got {value}",
                        "field": param_name,
                    }

                # Min/max length validation (for strings/lists)
                if "min_length" in rules:
                    if not hasattr(value, "__len__"):
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Parameter '{param_name}' must have length, got {type(value).__name__}",
                            "field": param_name,
                        }
                    if len(value) < rules["min_length"]:
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Parameter '{param_name}' must have length >= {rules['min_length']}, got {len(value)}",
                            "field": param_name,
                        }

                if "max_length" in rules:
                    if not hasattr(value, "__len__"):
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Parameter '{param_name}' must have length, got {type(value).__name__}",
                            "field": param_name,
                        }
                    if len(value) > rules["max_length"]:
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Parameter '{param_name}' must have length <= {rules['max_length']}, got {len(value)}",
                            "field": param_name,
                        }

                # Custom validator
                if "validator" in rules:
                    validator = rules["validator"]
                    try:
                        if not validator(value):
                            return {
                                "success": False,
                                "error": "validation_error",
                                "message": f"Parameter '{param_name}' failed custom validation",
                                "field": param_name,
                            }
                    except Exception as e:
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Parameter '{param_name}' validation error: {str(e)}",
                            "field": param_name,
                        }

                validated_kwargs[param_name] = value

            # Merge validated kwargs with original kwargs (keep non-schema params)
            all_kwargs = {**kwargs, **validated_kwargs}

            # Call the original function with validated parameters
            return func(self, **all_kwargs)

        return wrapper

    return decorator


def validate_output(**schema) -> Callable:
    """
    Decorator to validate workflow output.

    Args:
        **schema: Validation rules for output fields. Each rule can specify:
            - required (bool): Whether the field is required (default: False)
            - type (type | tuple): Expected type(s)
            - enum (list): List of allowed values
            - min_value (int/float): Minimum value for numbers
            - max_value (int/float): Maximum value for numbers
            - min_length (int): Minimum length for strings/lists
            - max_length (int): Maximum length for strings/lists
            - validator (callable): Custom validation function

    Example:
        @validate_output(
            success={"required": True, "type": bool},
            results={"required": True, "type": list, "min_length": 0}
        )
        def _do_execute(self, **kwargs) -> DictParams:
            return {"success": True, "results": [...]}

    Returns:
        Decorated function that validates outputs after execution.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, **kwargs) -> DictParams:
            # Execute the function
            result = func(self, **kwargs)

            # Ensure result is a dict
            if not isinstance(result, dict):
                return {
                    "success": False,
                    "error": "validation_error",
                    "message": f"Output must be a dictionary, got {type(result).__name__}",
                }

            # Validate each field according to schema
            for field_name, rules in schema.items():
                value = result.get(field_name)

                # Check required
                if rules.get("required", False) and value is None:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Required output field '{field_name}' is missing",
                        "field": field_name,
                    }

                # If value is None and not required, skip further validation
                if value is None:
                    continue

                # Type validation
                if "type" in rules:
                    expected_type = rules["type"]
                    if not isinstance(value, expected_type):
                        type_name = expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Output field '{field_name}' must be of type {type_name}, got {type(value).__name__}",
                            "field": field_name,
                        }

                # Enum validation
                if "enum" in rules and value not in rules["enum"]:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Output field '{field_name}' must be one of {rules['enum']}, got '{value}'",
                        "field": field_name,
                    }

                # Min/max value validation (for numbers)
                if "min_value" in rules and value < rules["min_value"]:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Output field '{field_name}' must be >= {rules['min_value']}, got {value}",
                        "field": field_name,
                    }

                if "max_value" in rules and value > rules["max_value"]:
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Output field '{field_name}' must be <= {rules['max_value']}, got {value}",
                        "field": field_name,
                    }

                # Min/max length validation (for strings/lists)
                if "min_length" in rules:
                    if not hasattr(value, "__len__"):
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Output field '{field_name}' must have length, got {type(value).__name__}",
                            "field": field_name,
                        }
                    if len(value) < rules["min_length"]:
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Output field '{field_name}' must have length >= {rules['min_length']}, got {len(value)}",
                            "field": field_name,
                        }

                if "max_length" in rules:
                    if not hasattr(value, "__len__"):
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Output field '{field_name}' must have length, got {type(value).__name__}",
                            "field": field_name,
                        }
                    if len(value) > rules["max_length"]:
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Output field '{field_name}' must have length <= {rules['max_length']}, got {len(value)}",
                            "field": field_name,
                        }

                # Custom validator
                if "validator" in rules:
                    validator = rules["validator"]
                    try:
                        if not validator(value):
                            return {
                                "success": False,
                                "error": "validation_error",
                                "message": f"Output field '{field_name}' failed custom validation",
                                "field": field_name,
                            }
                    except Exception as e:
                        return {
                            "success": False,
                            "error": "validation_error",
                            "message": f"Output field '{field_name}' validation error: {str(e)}",
                            "field": field_name,
                        }

            # Return the validated result
            return result

        return wrapper

    return decorator


__all__ = ["validate_input", "validate_output"]
