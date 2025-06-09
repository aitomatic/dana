"""
Dana Import System

Custom import system that allows importing Dana (.na) files as Python modules.
"""

import importlib.util
import sys
from importlib.abc import Loader, MetaPathFinder
from pathlib import Path
from typing import Optional, Sequence


class DanaModuleFinder(MetaPathFinder):
    """Custom module finder for Dana (.na) files."""
    
    def __init__(self):
        self.dana_paths = [
            Path.cwd() / "dana",  # ./dana/ directory
            Path.cwd(),           # Current directory
        ]
    
    def find_spec(self, fullname: str, path: Optional[Sequence[str]], target=None):
        """Find Dana module specifications."""
        
        # Only handle 'dana.*' imports
        if not fullname.startswith('dana.'):
            return None
        
        # Extract module name (e.g., 'dana.simple_module' -> 'simple_module')
        module_name = fullname.split('.')[-1]
        
        # Search for .na file
        dana_file = self._find_dana_file(module_name)
        if dana_file is None:
            return None
        
        # Create module spec
        spec = importlib.util.spec_from_loader(
            fullname,
            DanaModuleLoader(dana_file),
            origin=str(dana_file)
        )
        return spec
    
    def _find_dana_file(self, module_name: str) -> Optional[Path]:
        """Find .na file for given module name."""
        for search_path in self.dana_paths:
            dana_file = search_path / f"{module_name}.na"
            if dana_file.exists():
                return dana_file
        return None


class DanaModuleLoader(Loader):
    """Loader for Dana modules that converts them to Python modules."""
    
    def __init__(self, dana_file_path: Path):
        self.dana_file_path = dana_file_path
    
    def create_module(self, spec):
        """Create the module object."""
        return None  # Use default module creation
    
    def exec_module(self, module):
        """Execute the module by loading and compiling Dana code."""
        
        # Read Dana source code
        dana_source = self.dana_file_path.read_text()
        
        # Parse Dana code into AST
        try:
            from opendxa.dana.sandbox.parser.dana_parser import DanaParser, ParseResult, Program
            parser = DanaParser()
            parsed = parser.parse(dana_source)
            
            # Wrap Program in ParseResult if needed
            if isinstance(parsed, Program):
                parse_result = ParseResult(program=parsed, errors=[])
            else:
                parse_result = parsed
            
            if not parse_result.is_valid:
                raise ImportError(f"Dana parsing failed: {parse_result.errors}")
        except ImportError as e:
            # If we can't find the parser, create a basic mock for Step 1
            if "No module named" in str(e):
                # For Step 1, we'll create a basic placeholder
                parse_result = self._create_basic_parse_result(dana_source)
            else:
                raise e
        
        # Create Python interface for Dana module
        from opendxa.dana.runtime.module_wrapper import DanaModuleWrapper
        dana_module_wrapper = DanaModuleWrapper(
            module_name=module.__name__,
            dana_ast=parse_result.program if hasattr(parse_result, 'program') else None,
            dana_source=dana_source
        )
        
        # Expose Dana functions as Python module attributes
        for func_name, python_callable in dana_module_wrapper.python_interface.items():
            setattr(module, func_name, python_callable)
        
        # Store Dana wrapper for debugging/introspection
        module._dana_wrapper = dana_module_wrapper
        module.__file__ = str(self.dana_file_path)
    
    def _create_basic_parse_result(self, dana_source: str):
        """Create a basic parse result for Step 1 testing."""
        class BasicParseResult:
            def __init__(self, source):
                self.is_valid = True
                self.errors = []
                self.program = None
                self.source = source
        
        return BasicParseResult(dana_source)


def install_dana_import_system():
    """Install Dana import system in Python."""
    if not any(isinstance(finder, DanaModuleFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, DanaModuleFinder())
        print("Dana import system installed successfully")
    else:
        print("Dana import system already installed") 