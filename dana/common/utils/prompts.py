"""Utility for managing and formatting prompts."""

from pathlib import Path

from dana.common.utils.misc import Misc


class Prompts:
    """Generic prompt management utility."""

    @classmethod
    def load_from_yaml(cls, yaml_data: str | dict | Path) -> dict[str, str]:
        """Load prompts from YAML configuration."""
        # Handle different input types
        if isinstance(yaml_data, str | Path):
            data = Misc.load_yaml_config(yaml_data)
        else:
            data = yaml_data

        return data.get("prompts", {})

    @classmethod
    def format_prompt(cls, template: str, **kwargs) -> str:
        """Format a prompt template with provided variables."""
        # First, handle standard Python format string replacements
        formatted = template.format(**kwargs)

        # Then handle any custom placeholder patterns like <variable_name>
        for key, value in kwargs.items():
            placeholder = f"<{key}>"
            if placeholder in formatted:
                formatted = formatted.replace(placeholder, str(value))

        return formatted

    @classmethod
    def get_prompt(cls, prompt_type: str, prompt_templates: dict[str, str], **kwargs) -> str:
        """Get and format a prompt by type."""
        if prompt_type not in prompt_templates:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        template = prompt_templates[prompt_type]
        return cls.format_prompt(template, **kwargs)
