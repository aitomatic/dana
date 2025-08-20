"""
Simple unit tests for receiver function import system.

Tests the behavior of importing struct types and their associated receiver functions.
"""

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


class TestReceiverFunctionImportsSimple:
    """Simple test receiver function import behavior."""

    def test_receiver_function_same_context(self):
        """Test that receiver functions work when defined in the same context."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test receiver function in the same context
        test_code = """
struct FileLoader:
    name : str = "FileLoader"

def (loader: FileLoader) list_files(path: str):
    return ["file1.txt", "file2.txt", "file3.txt"]

loader = FileLoader()
name = loader.name
files = loader.list_files("some_path")
"""

        interpreter._eval_source_code(test_code, context)

        # Check if the receiver function worked
        assert context.get("name") == "FileLoader"
        assert context.get("files") == ["file1.txt", "file2.txt", "file3.txt"]

    def test_struct_import_without_receiver_functions(self):
        """Test that struct imports work without receiver functions."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        code = """
struct SimpleStruct:
    name: str = "test"

simple = SimpleStruct()
"""

        interpreter._eval_source_code(code, context)
        assert context.get("simple").name == "test"

    def test_receiver_function_import_issue_resolved(self, tmp_path):
        """Test that receiver functions now work when imported from a module."""
        # Initialize the module system for the test
        import os

        from dana.__init__.init_modules import initialize_module_system, reset_module_system

        # Add tmp_path to DANAPATH so the interpreter can find the module
        original_danapath = os.environ.get("DANAPATH", "")
        os.environ["DANAPATH"] = f"{tmp_path}{os.pathsep}{original_danapath}"

        # Reset and reinitialize the module system with the updated DANAPATH
        reset_module_system()
        initialize_module_system()

        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Create a test module file using tmp_path fixture
        module_content = """
struct FileLoader:
    name : str = "FileLoader"

def (loader: FileLoader) list_files(path: str):
    return ["file1.txt", "file2.txt", "file3.txt"]
"""

        module_file = tmp_path / "simple_test_file_loader.na"
        with open(module_file, "w") as f:
            f.write(module_content)

        # Test the import issue using the module
        test_code = f"""
from {module_file.stem} import FileLoader

loader = FileLoader()
name = loader.name
files = loader.list_files("some_path")
"""

        interpreter._eval_source_code(test_code, context)

        # Restore original DANAPATH
        if original_danapath:
            os.environ["DANAPATH"] = original_danapath
        else:
            os.environ.pop("DANAPATH", None)

        # Check if the receiver function now works
        assert context.get("name") == "FileLoader"
        assert context.get("files") == ["file1.txt", "file2.txt", "file3.txt"]

    def test_multiple_receiver_functions_import(self, tmp_path):
        """Test that multiple receiver functions work when imported from a module."""
        # Initialize the module system for the test
        import os

        from dana.__init__.init_modules import initialize_module_system, reset_module_system

        # Add tmp_path to DANAPATH so the interpreter can find the module
        original_danapath = os.environ.get("DANAPATH", "")
        os.environ["DANAPATH"] = f"{tmp_path}{os.pathsep}{original_danapath}"

        # Reset and reinitialize the module system with the updated DANAPATH
        reset_module_system()
        initialize_module_system()

        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Create a test module file with multiple receiver functions
        module_content = """
struct Calculator:
    name : str = "Calculator"

def (calc: Calculator) add(a: int, b: int):
    return a + b

def (calc: Calculator) multiply(a: int, b: int):
    return a * b

def (calc: Calculator) get_name():
    return calc.name
"""

        module_file = tmp_path / "test_calculator.na"
        with open(module_file, "w") as f:
            f.write(module_content)

        # Test importing and using multiple receiver functions
        test_code = f"""
from {module_file.stem} import Calculator

calc = Calculator()
name = calc.get_name()
sum_result = calc.add(3, 5)
product_result = calc.multiply(4, 6)
"""

        interpreter._eval_source_code(test_code, context)

        # Restore original DANAPATH
        if original_danapath:
            os.environ["DANAPATH"] = original_danapath
        else:
            os.environ.pop("DANAPATH", None)

        # Check if all receiver functions work
        assert context.get("name") == "Calculator"
        assert context.get("sum_result") == 8
        assert context.get("product_result") == 24

    def test_receiver_function_with_parameters_import(self, tmp_path):
        """Test that receiver functions with parameters work when imported from a module."""
        # Initialize the module system for the test
        import os

        from dana.__init__.init_modules import initialize_module_system, reset_module_system

        # Add tmp_path to DANAPATH so the interpreter can find the module
        original_danapath = os.environ.get("DANAPATH", "")
        os.environ["DANAPATH"] = f"{tmp_path}{os.pathsep}{original_danapath}"

        # Reset and reinitialize the module system with the updated DANAPATH
        reset_module_system()
        initialize_module_system()

        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Create a test module file with receiver functions that take parameters
        module_content = """
struct Counter:
    value: int = 0

def (counter: Counter) increment(amount: int):
    return counter.value + amount

def (counter: Counter) get_value():
    return counter.value
"""

        module_file = tmp_path / "test_counter.na"
        with open(module_file, "w") as f:
            f.write(module_content)

        # Test importing and using receiver functions with parameters
        test_code = f"""
from {module_file.stem} import Counter

counter = Counter()
counter.value = 10
current_value = counter.get_value()
incremented_value = counter.increment(5)
"""

        interpreter._eval_source_code(test_code, context)

        # Restore original DANAPATH
        if original_danapath:
            os.environ["DANAPATH"] = original_danapath
        else:
            os.environ.pop("DANAPATH", None)

        # Check if receiver functions with parameters work
        assert context.get("current_value") == 10
        assert context.get("incremented_value") == 15
