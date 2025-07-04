from llm_pyexecutor.cli import PipCommandsExtrator as PipParser
from llm_pyexecutor.code import PythonCodeExtractor as PythonParser
from llm_pyexecutor.code import extract_dependecies as extract_import_packages
from llm_pyexecutor.code import is_standard_package
from llm_pyexecutor.local_executor import LLMPythonCodeExecutor

from dana.common.mixins.queryable import ToolCallable
from dana.base.resource import BaseResource, ResourceResponse


class CodeResource(BaseResource):
    """A resource for executing Python code from natural language text.

    This class handles:
    - Extracting Python code from natural language text
    - Managing dependencies through pip
    - Executing code in a virtual environment
    - Providing execution results and error handling
    """

    def __init__(self, name: str = "", description: str = ""):
        """Initialize the CodeResource with optional name and description."""
        name = name or "code_resource"
        description = description or "Run Python code for a given task."
        super().__init__(name=name, description=description)
        self.runner = LLMPythonCodeExecutor()

    @ToolCallable.tool
    async def query(self, params: str) -> ResourceResponse:
        """Parse natural language text into a single valid Python code block and run it.

        Args:
            str: The natural language text that contains pip install commands and Python code.

        Returns:
            ResourceResponse: The result of the code execution, including:
                - success (bool): Boolean indicating if execution was successful
                - content (dict): The code that was executed and the result of the execution if successful
                - error (Optional[str]): Error details if execution failed
        """
        text = params
        try:
            code = self._extract_code(text)
            required_packages = self._extract_packages(text, code)
            self._install_dependencies(required_packages)
            result = self._execute_code(code)
            return ResourceResponse(success=True, content={"code": code, "result": result})
        except Exception as e:
            return ResourceResponse(success=False, error=str(e), content={"code": code})

    def _extract_code(self, text: str, separator: str = "```") -> str:
        """Extract and validate Python code from text using the specified separator."""
        if separator in text and len(text.split(separator)) > 1:
            codes = text.split(separator)
            codes = [code for code in [PythonParser.get_code(code) for code in codes] if code is not None]
        else:
            codes = [text]

        clean_code = "".join(line + "\n" for line in codes)

        try:
            PythonParser.is_python_code(clean_code)
        except Exception as e:
            raise Exception(f"Failed to extract valid Python code: {str(e)}")

        return clean_code

    def _extract_packages(self, text: str, code: str) -> list[str]:
        """Extract unique non-standard package names from text and code."""
        try:
            python_path = self.runner._executor_venv.get_pyexecutor()
            pip_packages = self._extract_pip_packages(text)
            python_packages = [deps["module"] for deps in extract_import_packages(code)]

            std_check_script = str(self.runner.path / "scripts" / "is_standard_pkg.py")
            std_packages = is_standard_package(python_path, std_check_script, ".")

            return [pkg for pkg in pip_packages + python_packages if pkg not in std_packages]
        except Exception as e:
            raise Exception(f"Failed to extract required packages: {str(e)}")

    def _extract_pip_packages(self, text: str, separator: str = "```") -> list[str]:
        """Extract unique package names from pip install commands in the text."""
        if separator in text and len(text.split(separator)) > 1:
            codes = text.split(separator)
        else:
            codes = [text]

        codes = [PipParser.get_pip_install_command(code) for code in codes]
        codes = [code for code in codes if code is not None]
        clean_code = "".join(line + "\n" for line in codes)
        clean_code = PipParser.remove_repititive_lines(clean_code)
        return list(set(PipParser.get_packages(clean_code)))

    def _install_dependencies(self, packages: list[str]) -> None:
        """Install the specified packages into the virtual environment if not already installed."""
        if not packages:
            return

        try:
            not_yet_installed = self.runner._executor_venv.check_additional_dependencies(
                packages,
                str(self.runner.executor_dir_path),
            )
            if not_yet_installed:
                self.runner._executor_venv.install_additional_dependencies(
                    not_yet_installed,
                    str(self.runner.executor_dir_path),
                )
        except Exception as e:
            raise Exception(f"Failed to install dependencies: {str(e)}")

    def _execute_code(self, code: str) -> str:
        """Execute the given Python code in the virtual environment and return the stdout."""
        try:
            python_path = self.runner._executor_venv.get_pyexecutor()
            result = self.runner._code_executor.execute_code(
                python_path,
                code,
                str(self.runner.executor_dir_path),
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to execute code: {str(e)}")
