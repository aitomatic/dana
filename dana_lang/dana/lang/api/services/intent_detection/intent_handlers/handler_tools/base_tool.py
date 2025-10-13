import textwrap
from pydantic import BaseModel, Field
from abc import abstractmethod, ABC
from typing import Any
import re
from ast import literal_eval


class ToolResult(BaseModel):
    name: str
    result: str
    require_user: bool = True
    metadata: dict = Field(default_factory=dict)


class BaseArgument(BaseModel):
    name: str
    type: str
    description: str
    example: str = "Value"


class InputSchema(BaseModel):
    type: str = "object"
    properties: list[BaseArgument] = Field(default_factory=list)
    required: list[str] = Field(default_factory=list)


class BaseToolInformation(BaseModel):
    name: str
    description: str
    input_schema: InputSchema

    def validate_arguments(self, arguments: dict) -> bool:
        for argument in self.input_schema.required:
            if argument not in arguments:
                return False
        return True

    def usage(self, format="xml") -> str:
        if format == "xml":
            parameter_str = "\n".join([f"<{arg.name}>{arg.example}</{arg.name}>" for arg in self.input_schema.properties])
            return textwrap.dedent(f"""<{self.name}>
{parameter_str}
</{self.name}>""").strip()


class BaseTool(ABC):
    def __init__(self, tool_information: BaseToolInformation):
        self.tool_information = tool_information

    async def execute(self, **kwargs) -> ToolResult:
        if not self.tool_information.validate_arguments(kwargs):
            raise ValueError(f"Invalid arguments for tool {self.tool_information.name}")
        return await self._execute(**kwargs)

    @abstractmethod
    async def _execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError("Subclasses must implement this method")

    def __repr__(self) -> str:
        parameter_str = "\n".join(
            [
                f"- {arg.name}: {'(required)' if arg.name in self.tool_information.input_schema.required else ''} {arg.description}"
                for arg in self.tool_information.input_schema.properties
            ]
        )
        return f"""## {self.name}
Description: {self.tool_information.description}
Parameters:
{parameter_str}
Usage:
{self.tool_information.usage()}"""

    @property
    def name(self) -> str:
        return self.tool_information.name

    def as_dict(self) -> dict:
        return {self.tool_information.name: self}

    def get_arguments(self) -> dict[str, tuple[bool, BaseArgument]]:
        """
        Get the arguments needed for running the tool.
        Returns:
            Dictionary of arguments and whether they are required or not and the argument itself
            - True: Required
            - False: Optional
        Example:
            {
                "input": (True, BaseArgument(name="input", type="string", description="The input to the tool"))
            }
        """
        required_args = self.tool_information.input_schema.required
        return {arg.name: (True if arg.name in required_args else False, arg) for arg in self.tool_information.input_schema.properties}

    def _eval_result(self, result: str, arg: BaseArgument) -> Any:
        try:
            if arg.type in ["array", "list"]:
                result = result.replace("\n", "")
                result = literal_eval(result)
            elif "str" not in arg.type:
                result = literal_eval(result)
        except Exception as _:
            if len(result) > 200:
                sample_result = result[:100] + "..." + result[-100:]
            else:
                sample_result = result
            raise ValueError(f"Failed to parse argument {arg.name} to {arg.type} from XML string: \n```xml\n{sample_result}\n```")
        return result

    def parse_arguments_from_xml_string_without_closing_tags(self, xml_string: str) -> dict[str, Any]:
        arguments = self.get_arguments()
        start_parts = []
        end_parts = []
        for arg_name in arguments.keys():
            start_parts.append(f"<{arg_name}>")
            end_parts.append(f"</{arg_name}>")
        full_argument_regex = rf"({'|'.join(start_parts + end_parts)})"
        full_argument_regex = re.compile(full_argument_regex, re.DOTALL)
        split_xml_string = re.split(full_argument_regex, xml_string)
        kwargs = {}
        current_block = None
        current_content = []
        for block in split_xml_string:
            if block in end_parts:
                continue
            if block in start_parts:
                if current_block is not None:
                    required, arg = arguments[current_block]
                    result = "\n".join(current_content)
                    kwargs[current_block] = self._eval_result(result, arg)
                current_block = block.strip("<").strip(">")
                current_content = []
            else:
                if block.strip():
                    current_content.append(block)
        if current_block and current_block not in kwargs:
            required, arg = arguments[current_block]
            if required:
                if not current_content:
                    raise ValueError(f"Required argument {current_block} not found in XML string")
            result = "\n".join(current_content)
            kwargs[current_block] = self._eval_result(result, arg)

        for arg_name, (required, _) in arguments.items():
            if arg_name not in kwargs:
                if required:
                    raise ValueError(f"Required argument {arg_name} not found in XML string")

        return kwargs

    def parse_arguments_from_xml_string(self, xml_string: str) -> dict[str, Any]:
        """
        Get the arguments from an XML string.
        Args:
            xml_string: The XML string to parse
        Returns:
            Dictionary of arguments and their values
        Example:
            {
                "input": "value"
            }
        """
        try:
            arguments = self.get_arguments()
            kwargs = {}
            for arg_name, (required, arg) in arguments.items():
                arg_string = f"<{arg_name}.*?>(.*?)</{arg_name}>"
                match = re.search(arg_string, xml_string, re.DOTALL)
                result = None
                try:
                    result = match.group(1)
                except Exception as _:
                    # If the argument is required and not found, raise an error
                    if required:
                        error_msg = f"Required argument {arg_name} not found in XML string"
                        open_tag = f"<{arg_name}>"
                        close_tag = f"</{arg_name}>"
                        if open_tag in xml_string:
                            if close_tag not in xml_string:
                                error_msg += f". {open_tag} exists but {close_tag} not found"
                        raise ValueError(error_msg)
                    else:
                        continue
                result = self._eval_result(result, arg)
                kwargs[arg_name] = result
            return kwargs
        except Exception as first_error:
            try:
                return self.parse_arguments_from_xml_string_without_closing_tags(xml_string)
            except Exception as second_error:
                raise ValueError(f"Failed to parse arguments from XML string: \n{second_error} \n{first_error}")


if __name__ == "__main__":
    tool = BaseToolInformation(
        name="schema_tool",
        description="A tool that returns the schema of the input",
        input_schema=InputSchema(
            type="object",
            properties=[
                BaseArgument(name="input", type="string", description="The input to the tool"),
            ],
            required=["input"],
        ),
    )
    print(str(tool.usage()))
