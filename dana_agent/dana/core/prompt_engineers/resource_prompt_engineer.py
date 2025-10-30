"""
ResourcePromptEngineer - Loads XML prompts for Resource instances.

Can work in two modes:
1. File-based: Loads XML from disk (when XML file exists)
2. Auto-generated: Generates XML from @tool_use decorated methods (when file doesn't exist or force_generate=True)

Architecture:
    ResourcePromptEngineer uses a loader to read/write XML files, and can automatically
    generate XML content from method signatures and docstrings when needed.

Example:
    # Auto-generate from signatures (creates XML file if not exists)
    engineer = ResourcePromptEngineer(resource, loader)
    prompt = engineer.get_prompt()
    
    # Force regenerate XML from signatures (overwrites existing)
    engineer = ResourcePromptEngineer(resource, loader, force_generate=True)
    prompt = engineer.get_prompt()
"""

import re
from typing import override

from dana.common.utils.misc import Misc
from dana.core.prompt_engineers.base_prompt_engineer import BasePromptEngineer
from dana.core.prompt_engineers.loaders.abstract_loader import AbstractLoader
from dana.core.resource.base_resource import BaseResource


class ResourcePromptEngineer(BasePromptEngineer):
    """
    Resource prompt engineer with auto-generation capability.
    
    This class can either load XML from files or auto-generate it from
    @tool_use decorated methods. If XML file doesn't exist, it generates
    and saves it. If force_generate=True, it overwrites existing XML.
    
    Attributes:
        _component: The resource component
        _loader: The loader for reading/writing XML files
        _force_generate: Whether to force regeneration of XML
    """

    def __init__(
        self,
        component: BaseResource,
        loader: AbstractLoader,
        force_generate: bool = False
    ):
        """
        Initialize the ResourcePromptEngineer.
        
        Args:
            component: The resource to generate/load prompts for
            loader: Loader for file-based reading/writing
            force_generate: If True, regenerate XML from signatures even if file exists
        """
        super().__init__(component, loader)
        self._force_generate = force_generate

    @override
    def get_prompt(self) -> str:
        """
        Get the prompt content for the resource.
        
        Logic:
        - If force_generate=True: Generate XML from signatures and save
        - If XML file doesn't exist: Generate XML from signatures and save
        - Otherwise: Load from existing XML file
        """
        xml_file_exists = self._check_xml_exists()
        
        if self._force_generate or not xml_file_exists:
            # Generate XML from @tool_use decorated methods
            xml_content = self._generate_xml_from_signatures()
            # Save it for future use
            self._loader.write_back(xml_content)
            return self._format_prompt(xml_content)
        else:
            # Load from existing file
            return self._format_prompt(self._load_xml())

    def _format_prompt(self, xml_string: str) -> str:
        """
        Format the prompt content for the resource into function call format.
        
        Transforms tool documentation into function call examples showing how to invoke each tool.
        """
        # Parse the XML to extract tools and convert to function call format
        import xml.etree.ElementTree as ET
        
        try:
            # Wrap in a root element for parsing
            wrapped_xml = f"<root>{xml_string}</root>"
            root = ET.fromstring(wrapped_xml)
            
            # Extract resource name and description
            name_elem = root.find('NAME')
            desc_elem = root.find('PUBLIC_DESCRIPTION')
            
            resource_name = name_elem.text if name_elem is not None else "Resource"
            description = desc_elem.text if desc_elem is not None else ""
            
            # Build formatted output
            output_parts = []
            output_parts.append(f"# {resource_name}")
            if description:
                output_parts.append(f"# {description}")
            output_parts.append("")
            
            # Process each tool
            tools_elem = root.find('TOOLS')
            if tools_elem is not None:
                for tool in tools_elem.findall('TOOL'):
                    tool_name = tool.find('NAME')
                    
                    if tool_name is not None:
                        output_parts.append("<function_call>")
                        output_parts.append(f"<invoke name=\"{tool_name.text}\">")
                        
                        # Add parameters
                        params_elem = tool.find('PARAMETERS')
                        if params_elem is not None:
                            for param in params_elem.findall('PARAMETER'):
                                param_name = param.find('NAME')
                                param_type = param.find('TYPE')
                                param_example = param.find('EXAMPLE')
                                param_default = param.find('DEFAULT')
                                
                                if param_name is not None:
                                    # Use example if available, otherwise show placeholder
                                    if param_example is not None and param_example.text:
                                        value = param_example.text
                                    elif param_default is not None and param_default.text:
                                        value = param_default.text
                                    else:
                                        # Create placeholder based on type
                                        param_type_text = param_type.text if (param_type is not None and param_type.text) else "str"
                                        if 'str' in param_type_text:
                                            value = "example_value"
                                        elif 'int' in param_type_text:
                                            value = "0"
                                        elif 'bool' in param_type_text:
                                            value = "true"
                                        else:
                                            value = "value"
                                    
                                    output_parts.append(f"<parameter name=\"{param_name.text}\">{value}</parameter>")
                        
                        output_parts.append("</invoke>")
                        output_parts.append("</function_call>")
                        output_parts.append("")
            
            return "\n".join(output_parts)
            
        except ET.ParseError:
            # If parsing fails, return original XML
            return xml_string

    def _load_xml(self) -> str:
        """
        Load the XML content for the resource from file.
        """
        return self._loader.get_xml()
    
    def _check_xml_exists(self) -> bool:
        """
        Check if XML file exists for this resource.
        
        Returns:
            True if XML file exists, False otherwise
        """
        try:
            # Try to load XML - if it returns empty string, file doesn't exist
            xml_content = self._loader.get_xml()
            return bool(xml_content.strip())
        except Exception:
            return False
    
    def _generate_xml_from_signatures(self) -> str:
        """
        Generate XML from @tool_use decorated methods.
        
        Returns:
            Generated XML string in the CreateFileResource.xml format
        """
        resource_class = self._component.__class__
        resource_name = resource_class.__name__
        
        # Get public description from class docstring
        public_desc = self._extract_public_description(resource_class)
        
        # Find all @tool_use decorated methods
        tool_methods = Misc.extract_tool_use_methods(resource_class)
        
        # Generate XML
        xml_parts = []
        xml_parts.append(f"<NAME>{resource_name}</NAME>")
        xml_parts.append(f"<PUBLIC_DESCRIPTION>{public_desc}</PUBLIC_DESCRIPTION>")
        xml_parts.append("")
        xml_parts.append("<TOOLS>")
        
        for method_name, method in tool_methods:
            tool_xml = self._generate_tool_xml(method_name, method)
            xml_parts.append(tool_xml)
        
        xml_parts.append("</TOOLS>")
        
        return "\n".join(xml_parts)
    
    def _extract_public_description(self, resource_class) -> str:
        """
        Extract public description from class docstring.
        
        Looks for descriptive text in docstring. Uses first paragraph or
        provides a default description.
        
        Args:
            resource_class: The class to extract description from
            
        Returns:
            Public description string
        """
        import inspect
        
        docstring = inspect.getdoc(resource_class)
        if not docstring:
            return f"{resource_class.__name__} resource."
        
        # Check for <PUBLIC_DESCRIPTION> tag
        match = re.search(
            r'<PUBLIC_DESCRIPTION>(.*?)</PUBLIC_DESCRIPTION>',
            docstring,
            re.DOTALL
        )
        if match:
            return match.group(1).strip()
        
        # Use first paragraph from docstring sections
        sections = Misc.parse_docstring_sections(docstring)
        description = sections.get('description', '')
        
        if description:
            # Get first paragraph
            first_para = description.split('\n\n')[0]
            return first_para.strip()
        
        return f"{resource_class.__name__} resource."
    
    def _generate_tool_xml(self, method_name: str, method: callable) -> str:
        """
        Generate XML for a single tool method.
        
        Args:
            method_name: Name of the method
            method: The method object
            
        Returns:
            XML string for the tool
        """
        # Use Misc utility to parse method signature
        method_info = Misc.parse_method_signature(method)
        
        description = method_info['description']
        parameters = method_info['parameters']
        
        # Build tool XML
        xml_parts = []
        xml_parts.append("<TOOL>")
        xml_parts.append(f"    <NAME>{method_name}</NAME>")
        xml_parts.append(f"    <DESCRIPTION>{description}</DESCRIPTION>")
        
        if parameters:
            xml_parts.append("    <PARAMETERS>")
            for param in parameters:
                param_xml = self._generate_parameter_xml(param)
                xml_parts.append(param_xml)
            xml_parts.append("    </PARAMETERS>")
        
        xml_parts.append("</TOOL>")
        
        return "\n".join(xml_parts)
    
    def _generate_parameter_xml(self, param: dict) -> str:
        """
        Generate XML for a single parameter.
        
        Args:
            param: Parameter info dict with name, type, description, etc.
            
        Returns:
            XML string for the parameter
        """
        xml_parts = []
        xml_parts.append("        <PARAMETER>")
        xml_parts.append(f"            <NAME>{param['name']}</NAME>")
        xml_parts.append(f"            <TYPE>{param['type']}</TYPE>")
        xml_parts.append(f"            <DESCRIPTION>{param['description']}</DESCRIPTION>")
        
        # Add default if present
        if param.get('has_default') and 'default' in param and param['default'] is not None:
            xml_parts.append(f"            <DEFAULT>{param['default']}</DEFAULT>")
        
        # Add example if present
        if 'example' in param:
            xml_parts.append(f"            <EXAMPLE>{param['example']}</EXAMPLE>")
        
        xml_parts.append("        </PARAMETER>")
        
        return "\n".join(xml_parts)



if __name__ == "__main__":
    """
    Demo usage of ResourcePromptEngineer with auto-generation.
    
    This demonstrates:
    1. Loading existing XML file
    2. Auto-generating XML from @tool_use methods when file doesn't exist
    3. Force regenerating XML with force_generate=True
    """
    import os
    import sys
    
    # Add examples path for imports
    examples_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "examples", "agents", "financial-analysis", "resources")
    sys.path.insert(0, examples_path)
    
    # Import will work when run from proper location  # noqa: E402
    from create_file_resource import CreateFileResource  # type: ignore
    from ripgrep_search_resource import RipgrepSearchResource  # type: ignore
    
    from dana.core.prompt_engineers.loaders.file_loader import FileLoader
    
    print("=" * 80)
    print("ResourcePromptEngineer Demo - Auto XML Generation")
    print("=" * 80)
    print()
    
    # Test 1: Load existing XML file (if it exists)
    print("Test 1: RipgrepSearchResource (with defaults)")
    print("-" * 80)
    resource = RipgrepSearchResource()
    loader = FileLoader(resource)
    engineer = ResourcePromptEngineer(resource, loader=loader)
    prompt = engineer.get_prompt()
    print(prompt)
    print()
    
    # Test 2: CreateFileResource (with example)
    print("Test 2: CreateFileResource (with example)")
    print("-" * 80)
    resource = CreateFileResource()
    loader = FileLoader(resource)
    engineer = ResourcePromptEngineer(resource, loader=loader)
    prompt = engineer.get_prompt()
    print(prompt)
    # print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
    # print()
    
    # # Test 2: Force regenerate from signatures
    # print("Test 2: Force regenerate XML from @tool_use method signatures")
    # print("-" * 80)
    # resource = CreateFileResource()
    # loader = FileLoader(resource)
    # engineer = ResourcePromptEngineer(resource, loader=loader, force_generate=True)
    # prompt = engineer.get_prompt()
    # print("Generated XML:")
    # print(prompt)
    # print()
    
    # print("=" * 80)
    # print("Note: XML has been generated/regenerated and saved to file.")
    # print("=" * 80)