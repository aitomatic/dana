"""Workflow YAML schema definition."""

from typing import Dict, Any
from jsonschema import validate, ValidationError

WORKFLOW_SCHEMA = {
    "type": "object",
    "required": ["nodes", "edges"],
    "properties": {
        "name": {"type": "string"},
        "objective": {"type": "string"},
        "version": {"type": "string"},
        "nodes": {
            "type": "object",
            "patternProperties": {
                ".*": {  # Node ID pattern
                    "type": "object",
                    "required": ["type", "description"],
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["START", "END", "TASK", "DECISION"]
                        },
                        "description": {"type": "string"},
                        "requires": {
                            "type": "object",
                            "additionalProperties": {"type": "string"}
                        },
                        "provides": {
                            "type": "object",
                            "additionalProperties": {"type": "string"}
                        },
                        "metadata": {
                            "type": "object",
                            "additionalProperties": True
                        }
                    }
                }
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["from", "to"],
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "condition": {"type": "string"},
                    "state_updates": {
                        "type": "object",
                        "additionalProperties": True
                    },
                    "metadata": {
                        "type": "object",
                        "additionalProperties": True
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "author": {"type": "string"},
                "created": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
}

def validate_workflow_yaml(data: Dict[str, Any]) -> bool:
    """Validate workflow YAML against schema."""
    try:
        validate(instance=data, schema=WORKFLOW_SCHEMA)
        return True
    except ValidationError as e:
        raise ValueError(f"Invalid workflow YAML: {e}") from e 