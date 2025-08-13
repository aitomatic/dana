import textwrap
from pydantic import BaseModel, Field
from abc import abstractmethod, ABC


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
