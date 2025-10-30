"""Miscellaneous utilities."""

# Configure asyncio to only warn about tasks taking longer than 30 seconds
# (LLM operations typically take 1-10 seconds, so this avoids false warnings)
import inspect
import re
from typing import Any, get_type_hints

from pydantic import BaseModel

from dana.common.protocols.war import IS_TOOL_USE


class ParsedArgKwargsResults(BaseModel):
    matched_args: list[Any]
    matched_kwargs: dict[str, Any]
    varargs: list[Any]
    varkwargs: dict[str, Any]
    unmatched_args: list[Any]
    unmatched_kwargs: dict[str, Any]


class Misc:
    """A collection of miscellaneous utility methods."""

    @staticmethod
    def parse_args_kwargs(func, *args, **kwargs) -> ParsedArgKwargsResults:

        """
        Bind (args, kwargs) to `func`'s signature, returning a dict with:
        - matched_args:      positional args that were bound to named parameters
        - matched_kwargs:    keyword args that were bound to named or kw-only parameters
        - varargs:           values that ended up in func's *args (if it has one)
        - varkwargs:         values that ended up in func's **kwargs (if it has one)
        - unmatched_args:    positional args that couldn't be bound (and no *args present)
        - unmatched_kwargs:  keyword args that couldn't be bound (and no **kwargs present)
        """
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        matched_args = []
        matched_kwargs = {}
        varargs = []
        varkwargs = {}
        unmatched_args = []
        unmatched_kwargs = {}

        # Separate out which parameters are "named positional" (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD)
        pos_params = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        # Which are keyword-only
        kwonly_params = [p for p in params if p.kind == p.KEYWORD_ONLY]

        # Check if func has *args or **kwargs
        has_var_pos = any(p.kind == p.VAR_POSITIONAL for p in params)
        has_var_kw = any(p.kind == p.VAR_KEYWORD for p in params)

        # 1) Assign positional arguments
        for index, value in enumerate(args):
            if index < len(pos_params):
                # Still within the "named positional" slots
                matched_args.append(value)
            else:
                # No more named positional slots left
                if has_var_pos:
                    varargs.append(value)
                else:
                    unmatched_args.append(value)

        # 2) Assign keyword arguments
        #    If the key matches one of the named parameters (positional or kw-only), consume it.
        named_param_names = {p.name for p in (pos_params + kwonly_params)}
        for key, value in kwargs.items():
            if key in named_param_names:
                matched_kwargs[key] = value
            else:
                if has_var_kw:
                    varkwargs[key] = value
                else:
                    unmatched_kwargs[key] = value

        return ParsedArgKwargsResults(
            matched_args=matched_args,
            matched_kwargs=matched_kwargs,
            varargs=varargs,
            varkwargs=varkwargs,
            unmatched_args=unmatched_args,
            unmatched_kwargs=unmatched_kwargs,
        )

    @staticmethod
    def extract_tool_use_methods(resource_class) -> list[tuple[str, callable]]:
        """
        Find all methods decorated with @tool_use.
        
        Args:
            resource_class: The class to inspect for tool_use decorated methods
            
        Returns:
            List of (method_name, method) tuples for methods decorated with @tool_use
        """
        tool_methods = []
        
        for name, method in inspect.getmembers(resource_class, predicate=inspect.isfunction):
            # Check if method has @tool_use decorator (IS_TOOL_USE attribute)
            if hasattr(method, IS_TOOL_USE) and getattr(method, IS_TOOL_USE):
                tool_methods.append((name, method))
        
        return tool_methods

    @staticmethod
    def parse_docstring_sections(docstring: str) -> dict[str, str]:
        """
        Parse docstring into sections (description, Args, Returns, etc.).
        
        Args:
            docstring: The docstring to parse
            
        Returns:
            Dict with sections: {'description', 'args', 'returns', 'raises', etc.}
        """
        if not docstring:
            return {'description': ''}
        
        sections = {}
        
        # Extract description (everything before first section header)
        desc_match = re.split(r'\n\s*(Args|Returns|Raises|Examples?|Notes?):', docstring, maxsplit=1)
        sections['description'] = desc_match[0].strip()
        
        # Extract Args section
        args_match = re.search(r'Args:(.*?)(?=\n\s*(?:Returns|Raises|Examples?|Notes?):|\Z)', docstring, re.DOTALL)
        sections['args'] = args_match.group(1).strip() if args_match else ''
        
        # Extract Returns section
        returns_match = re.search(r'Returns:(.*?)(?=\n\s*(?:Args|Raises|Examples?|Notes?):|\Z)', docstring, re.DOTALL)
        sections['returns'] = returns_match.group(1).strip() if returns_match else ''
        
        # Extract Raises section
        raises_match = re.search(r'Raises:(.*?)(?=\n\s*(?:Args|Returns|Examples?|Notes?):|\Z)', docstring, re.DOTALL)
        sections['raises'] = raises_match.group(1).strip() if raises_match else ''
        
        return sections

    @staticmethod
    def parse_method_signature(method: callable) -> dict[str, Any]:
        """
        Parse method signature and return structured parameter info.
        
        Args:
            method: The method to parse
            
        Returns:
            Dict with structure:
            {
                'name': str,
                'description': str,
                'parameters': [
                    {
                        'name': str,
                        'type': str,
                        'description': str,
                        'default': Any (optional),
                        'has_default': bool,
                        'example': str (optional)
                    }
                ]
            }
        """
        sig = inspect.signature(method)
        docstring = inspect.getdoc(method) or ""
        
        # Parse docstring sections
        sections = Misc.parse_docstring_sections(docstring)
        method_description = sections['description']
        
        # Extract parameter descriptions from Args section
        param_descriptions = Misc._parse_param_descriptions(sections['args'])
        
        # Get type hints
        try:
            type_hints = get_type_hints(method)
        except Exception:
            type_hints = {}
        
        # Build parameter list
        parameters = []
        for param_name, param in sig.parameters.items():
            # Skip 'self' and '**kwargs'
            if param_name in ('self', 'kwargs'):
                continue
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                continue
            
            # Get parameter type
            param_type = Misc._format_type_annotation(param, type_hints.get(param_name))
            
            # Get parameter description
            param_desc = param_descriptions.get(param_name, f"Parameter {param_name}")
            
            # Check for default value
            has_default = param.default != inspect.Parameter.empty
            default_value = param.default if has_default else None
            
            # Extract example from description or docstring
            example = Misc._extract_example_from_text(param_name, docstring)
            
            param_info = {
                'name': param_name,
                'type': param_type,
                'description': param_desc,
                'has_default': has_default,
            }
            
            if has_default and default_value is not None:
                param_info['default'] = default_value
            
            if example:
                param_info['example'] = example
            
            parameters.append(param_info)
        
        return {
            'name': method.__name__,
            'description': method_description,
            'parameters': parameters
        }

    @staticmethod
    def _parse_param_descriptions(args_section: str) -> dict[str, str]:
        """
        Parse parameter descriptions from Args section of docstring.
        
        Args:
            args_section: The Args section text from docstring
            
        Returns:
            Dict mapping parameter names to descriptions
        """
        descriptions = {}
        
        if not args_section:
            return descriptions
        
        # Parse parameter lines (format: "param_name: description" or "param_name (type): description")
        # This regex handles multi-line descriptions and special params like **kwargs, *args
        param_pattern = r'^\s*(\*{0,2}\w+)(?:\s*\([^)]+\))?\s*:\s*(.+?)(?=^\s*\*{0,2}\w+\s*(?:\([^)]+\))?\s*:|\Z)'
        matches = re.finditer(param_pattern, args_section, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            param_name = match.group(1)
            # Remove * from param names like **kwargs and *args
            clean_param_name = param_name.lstrip('*')
            param_desc = match.group(2).strip()
            # Clean up description (collapse multiple whitespace)
            param_desc = ' '.join(param_desc.split())
            descriptions[clean_param_name] = param_desc
        
        return descriptions

    @staticmethod
    def _format_type_annotation(param: inspect.Parameter, type_hint: Any) -> str:
        """
        Format parameter type annotation as string.
        
        Args:
            param: The parameter object from signature
            type_hint: Type hint from get_type_hints()
            
        Returns:
            Formatted type string
        """
        if type_hint:
            # Handle typing module types
            type_str = str(type_hint)
            # Clean up typing module notation
            type_str = type_str.replace('typing.', '')
            type_str = type_str.replace('<class \'', '').replace('\'>', '')
            # Clean up common patterns
            type_str = type_str.replace('builtins.', '')
            return type_str
        
        if param.annotation != inspect.Parameter.empty:
            ann_str = str(param.annotation)
            ann_str = ann_str.replace('<class \'', '').replace('\'>', '')
            ann_str = ann_str.replace('builtins.', '')
            return ann_str
        
        return "Any"

    @staticmethod
    def _extract_example_from_text(param_name: str, text: str) -> str | None:
        """
        Extract example value for parameter from text.
        
        Looks for patterns like:
        - Example: value
        - (example: value)
        - EXAMPLE tag in XML-like format
        
        Args:
            param_name: Name of the parameter to find example for
            text: Text to search for examples
            
        Returns:
            Example string if found, None otherwise
        """
        # Look for examples in parameter description
        # Pattern 1: "param_name: description Example: value"
        pattern1 = rf'{param_name}[^:]*:.*?[Ee]xample[:\s]+([^\n\)]+)'
        match = re.search(pattern1, text)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "(example: value)" near parameter
        pattern2 = rf'{param_name}[^:]*:.*?\([Ee]xample:\s*([^\)]+)\)'
        match = re.search(pattern2, text)
        if match:
            return match.group(1).strip()
        
        return None