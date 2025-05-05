"""Tests for the ToolCallable mixin."""

import pytest
from opendxa.common.mixins.tool_callable import ToolCallable
from opendxa.common.mixins.tool_formats import ToolFormat

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
class TestToolCallable:
    """Test suite for the ToolCallable mixin."""
    
    def test_tool_decorator(self):
        """Test the tool decorator."""
        class TestClass(ToolCallable):
            @ToolCallable.tool
            async def test_tool(self, param1: str) -> dict:
                """Test tool description.
                
                @param1: Parameter description
                """
                return {"result": param1}
        
        obj = TestClass()
        assert "test_tool" in obj._tool_callable_function_cache
    
    def test_private_methods_ignored(self):
        """Test that private methods are ignored."""
        class TestClass(ToolCallable):
            @ToolCallable.tool
            async def _private_tool(self, param1: str) -> dict:
                """Private tool description.
                
                @param1: Parameter description
                """
                return {"result": param1}
            
            @ToolCallable.tool
            async def public_tool(self, param1: str) -> dict:
                """Public tool description.
                
                @param1: Parameter description
                """
                return {"result": param1}
        
        obj = TestClass()
        assert "_private_tool" not in obj._tool_callable_function_cache
        assert "public_tool" in obj._tool_callable_function_cache
    
    def test_list_mcp_tools(self):
        """Test listing MCP tools."""
        class TestClass(ToolCallable):
            @ToolCallable.tool
            async def test_tool(self, param1: str) -> dict:
                """Test tool description.
                
                @description: This is the description of the tool.

                @param1: Parameter description
                """
                return {"result": param1}
        
        obj = TestClass()
        tools = obj.list_mcp_tools()
        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "test_tool"
        assert tool.description == "This is the description of the tool."
        assert "param1" in tool.inputSchema["properties"]
    
    def test_list_openai_functions(self):
        """Test listing OpenAI functions."""
        class TestClass(ToolCallable):
            @ToolCallable.tool
            async def test_tool(self, param1: str) -> dict:
                """Test tool description.
                
                @description: This is the description of the tool.
                @param1: Parameter description
                """
                return {"result": param1}
        
        obj = TestClass()
        functions = obj.list_openai_functions()
        assert len(functions) == 1
        function = functions[0]["function"]
        assert function["name"] == ToolFormat.build_tool_name(obj.name, obj.id, "test_tool")
        assert function["description"] == "This is the description of the tool."
        assert "param1" in function["parameters"]["properties"]
    
    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test calling a tool."""
        class TestClass(ToolCallable):
            @ToolCallable.tool
            async def test_tool(self, param1: str) -> dict:
                """Test tool description.
                
                @param1: Parameter description
                """
                return {"result": param1}
        
        obj = TestClass()
        result = await obj.call_tool("test_tool", {"param1": "test_value"})
        assert result == {"result": "test_value"}
    
    def test_parse_name_id_function_string(self):
        """Test parsing name-id-function string."""
        resource_name, resource_id, tool_name = ToolFormat.parse_tool_name(
            "resource_name__resource_id__tool_name"
        )
        assert resource_name == "resource_name"
        assert resource_id == "resource_id"
        assert tool_name == "tool_name"
    
    def test_build_name_id_function_string(self):
        """Test building name-id-function string."""
        result = ToolFormat.build_tool_name(
            "resource_name",
            "resource_id",
            "tool_name"
        )
        assert result == "resource_name__resource_id__tool_name"
    
    def test_multiple_tools(self):
        """Test multiple tools in a class."""
        class TestClass(ToolCallable):
            @ToolCallable.tool
            async def tool1(self, param1: str) -> dict:
                """Tool 1 description.
                
                @param1: Parameter description
                """
                return {"result": param1}
            
            @ToolCallable.tool
            async def tool2(self, param2: int) -> dict:
                """Tool 2 description.
                
                @param2: Parameter description
                """
                return {"result": param2}
        
        obj = TestClass()
        tools = obj.list_mcp_tools()
        assert len(tools) == 2
        tool_names = {tool.name for tool in tools}
        assert tool_names == {"tool1", "tool2"}
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test error handling in tool calls."""
        class TestClass(ToolCallable):
            @ToolCallable.tool
            async def test_tool(self, param1: str) -> dict:
                """Test tool description.
                
                @param1: Parameter description
                """
                raise ValueError("Test error")
        
        obj = TestClass()
        with pytest.raises(ValueError, match="Test error"):
            await obj.call_tool("test_tool", {"param1": "test_value"})
    
    @pytest.mark.asyncio
    async def test_actual_generated_function_name(self):
        """Test the actual generated function name with an autogenerated ID."""
        class TestResource(ToolCallable):
            @ToolCallable.tool
            async def test_tool(self, param1: str) -> dict:
                """Test tool description.
                
                @param1: Parameter description
                """
                return {"result": param1}
        
        # Create an instance which will have an autogenerated UUID
        resource = TestResource()
        
        # Get the OpenAI functions
        functions = resource.list_openai_functions()
        assert len(functions) == 1
        
        # Get the generated function name
        function_name = functions[0]["function"]["name"]
        
        # Parse the function name to verify its components
        resource_name, resource_id, tool_name = ToolFormat.parse_tool_name(function_name)
        
        # Verify the components
        assert resource_name == resource.name
        assert resource_id == resource.id
        assert tool_name == "test_tool"
        
        # Verify the format is correct
        assert function_name == f"{resource_name}__{resource_id}__{tool_name}"

        # Verify the ID is a string of the expected length (base64 encoded)
        assert isinstance(resource_id, str)
        assert len(resource_id) == 8
        # try:
        #     uuid.UUID(resource_id) # ID is base64, not hex UUID
        # except ValueError:
        #     assert False, f"Invalid UUID format: {resource_id}"

