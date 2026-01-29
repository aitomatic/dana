"""
Unit tests for tool_schema module.

Tests JSON schema generation from resources, including support for
Pydantic models, primitive types, and various parameter configurations.
"""

from typing import Any

from pydantic import BaseModel

from dana.common.protocols.war import tool_use
from dana.core.agent.components.tool_schema import (
    _get_pydantic_schema,
    _inline_refs,
    _python_type_to_json_schema,
    generate_resource_schemas,
)
from dana.core.resource import BaseResource


# =============================================================================
# Test Fixtures - Pydantic Models
# =============================================================================


class Student(BaseModel):
    """A simple student model."""

    name: str
    id: str


class Address(BaseModel):
    """An address model."""

    street: str
    city: str
    zip_code: str


class Teacher(BaseModel):
    """A teacher model with nested address."""

    name: str
    subject: str
    address: Address


class Classroom(BaseModel):
    """A classroom with nested list of students."""

    room_number: str
    students: list[Student]


# =============================================================================
# Test Fixtures - Resources
# =============================================================================


class StudentManagementResource(BaseResource):
    """Resource for managing students."""

    def __init__(self):
        super().__init__(resource_type="student_management")

    @tool_use
    def process_students(self, students: list[Student]) -> str:
        """Process a list of students.

        Args:
            students: List of students to process

        Returns:
            Processing result message
        """
        return f"Processed {len(students)} students"

    @tool_use
    def get_student(self, student_id: str, include_grades: bool = False) -> Student:
        """Get a single student by ID.

        Args:
            student_id: The student's unique identifier
            include_grades: Whether to include grade information

        Returns:
            The student object
        """
        return Student(name="Test Student", id=student_id)

    @tool_use
    def search_students(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Student]:
        """Search for students matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching students
        """
        return []


class MixedTypesResource(BaseResource):
    """Resource with various parameter types."""

    def __init__(self):
        super().__init__(resource_type="mixed_types")

    @tool_use
    def process_data(
        self,
        name: str,
        count: int,
        ratio: float,
        enabled: bool,
        tags: list[str],
        metadata: dict,
    ) -> dict:
        """Process data with various types.

        Args:
            name: The name
            count: A count value
            ratio: A ratio value
            enabled: Whether enabled
            tags: List of tags
            metadata: Additional metadata

        Returns:
            Processing result
        """
        return {}


class NestedModelsResource(BaseResource):
    """Resource with nested Pydantic models."""

    def __init__(self):
        super().__init__(resource_type="nested_models")

    @tool_use
    def add_teacher(self, teacher: Teacher) -> str:
        """Add a teacher with address.

        Args:
            teacher: Teacher object with nested address

        Returns:
            Confirmation message
        """
        return f"Added teacher {teacher.name}"

    @tool_use
    def create_classroom(self, classroom: Classroom) -> str:
        """Create a classroom with students.

        Args:
            classroom: Classroom object with list of students

        Returns:
            Confirmation message
        """
        return f"Created classroom {classroom.room_number}"


# =============================================================================
# Tests for _python_type_to_json_schema
# =============================================================================


class TestPythonTypeToJsonSchema:
    """Tests for the _python_type_to_json_schema function."""

    def test_primitive_string(self):
        """Test string type conversion."""
        schema = _python_type_to_json_schema("str")
        assert schema == {"type": "string"}

    def test_primitive_int(self):
        """Test integer type conversion."""
        schema = _python_type_to_json_schema("int")
        assert schema == {"type": "integer"}

    def test_primitive_float(self):
        """Test float type conversion."""
        schema = _python_type_to_json_schema("float")
        assert schema == {"type": "number"}

    def test_primitive_bool(self):
        """Test boolean type conversion."""
        schema = _python_type_to_json_schema("bool")
        assert schema == {"type": "boolean"}

    def test_dict_type(self):
        """Test dict type conversion."""
        schema = _python_type_to_json_schema("dict")
        assert schema == {"type": "object", "additionalProperties": True}

    def test_list_of_primitives_str(self):
        """Test list[str] type conversion."""
        schema = _python_type_to_json_schema("list[str]")
        assert schema == {"type": "array", "items": {"type": "string"}}

    def test_list_of_primitives_int(self):
        """Test list[int] type conversion."""
        schema = _python_type_to_json_schema("list[int]")
        assert schema == {"type": "array", "items": {"type": "integer"}}

    def test_list_without_generic(self):
        """Test plain list type defaults to string items."""
        schema = _python_type_to_json_schema("list")
        assert schema == {"type": "array", "items": {"type": "string"}}

    def test_unknown_type_defaults_to_string(self):
        """Test unknown types default to string."""
        schema = _python_type_to_json_schema("CustomUnknownType")
        assert schema == {"type": "string"}

    def test_any_type_defaults_to_string(self):
        """Test Any type defaults to string."""
        schema = _python_type_to_json_schema("Any")
        assert schema == {"type": "string"}


class TestPythonTypeToJsonSchemaWithTypeObject:
    """Tests for _python_type_to_json_schema with type_object parameter."""

    def test_pydantic_model_direct(self):
        """Test direct Pydantic model generates correct schema."""
        schema = _python_type_to_json_schema("Student", Student)

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "id" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["id"]["type"] == "string"
        assert set(schema["required"]) == {"name", "id"}

    def test_list_of_pydantic_model(self):
        """Test list[PydanticModel] generates correct array schema."""
        schema = _python_type_to_json_schema("list[Student]", list[Student])

        assert schema["type"] == "array"
        assert "items" in schema
        items = schema["items"]
        assert items["type"] == "object"
        assert "properties" in items
        assert "name" in items["properties"]
        assert "id" in items["properties"]

    def test_nested_pydantic_model(self):
        """Test nested Pydantic model gets inlined."""
        schema = _python_type_to_json_schema("Teacher", Teacher)

        assert schema["type"] == "object"
        assert "address" in schema["properties"]
        # The nested Address should be inlined
        address_schema = schema["properties"]["address"]
        assert address_schema["type"] == "object"
        assert "street" in address_schema["properties"]
        assert "city" in address_schema["properties"]
        assert "zip_code" in address_schema["properties"]

    def test_pydantic_model_with_list_field(self):
        """Test Pydantic model with list field."""
        schema = _python_type_to_json_schema("Classroom", Classroom)

        assert schema["type"] == "object"
        assert "students" in schema["properties"]
        students_schema = schema["properties"]["students"]
        assert students_schema["type"] == "array"
        # Nested Student should be inlined
        items_schema = students_schema["items"]
        assert items_schema["type"] == "object"
        assert "name" in items_schema["properties"]

    def test_type_object_takes_priority(self):
        """Test type_object takes priority over string parsing."""
        # Even if string says "str", if type_object is Student, use Student
        schema = _python_type_to_json_schema("str", Student)

        assert schema["type"] == "object"
        assert "name" in schema["properties"]

    def test_none_type_object_falls_back_to_string_parsing(self):
        """Test None type_object falls back to string parsing."""
        schema = _python_type_to_json_schema("list[str]", None)

        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"


# =============================================================================
# Tests for _get_pydantic_schema
# =============================================================================


class TestGetPydanticSchema:
    """Tests for the _get_pydantic_schema function."""

    def test_simple_model_schema(self):
        """Test simple model generates correct schema."""
        schema = _get_pydantic_schema(Student)

        assert schema["type"] == "object"
        assert schema["title"] == "Student"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "id" in schema["properties"]

    def test_nested_model_inlines_refs(self):
        """Test nested model inlines $refs."""
        schema = _get_pydantic_schema(Teacher)

        # Should not have $defs
        assert "$defs" not in schema

        # Nested Address should be inlined
        assert "address" in schema["properties"]
        address_schema = schema["properties"]["address"]
        assert address_schema["type"] == "object"
        assert "street" in address_schema["properties"]

    def test_model_with_list_inlines_refs(self):
        """Test model with list field inlines $refs."""
        schema = _get_pydantic_schema(Classroom)

        # Should not have $defs
        assert "$defs" not in schema

        # Nested Student in list should be inlined
        students_schema = schema["properties"]["students"]
        assert students_schema["type"] == "array"
        items = students_schema["items"]
        assert items["type"] == "object"
        assert "name" in items["properties"]


# =============================================================================
# Tests for _inline_refs
# =============================================================================


class TestInlineRefs:
    """Tests for the _inline_refs function."""

    def test_simple_ref_replacement(self):
        """Test simple $ref gets replaced."""
        schema = {"$ref": "#/$defs/Student"}
        defs = {"Student": {"type": "object", "properties": {"name": {"type": "string"}}}}

        result = _inline_refs(schema, defs)

        assert result["type"] == "object"
        assert "name" in result["properties"]

    def test_nested_ref_replacement(self):
        """Test nested $ref gets replaced."""
        schema = {
            "type": "object",
            "properties": {
                "student": {"$ref": "#/$defs/Student"},
            },
        }
        defs = {"Student": {"type": "object", "properties": {"name": {"type": "string"}}}}

        result = _inline_refs(schema, defs)

        assert result["properties"]["student"]["type"] == "object"

    def test_array_with_ref(self):
        """Test array with $ref items gets replaced."""
        schema = {
            "type": "array",
            "items": {"$ref": "#/$defs/Student"},
        }
        defs = {"Student": {"type": "object", "properties": {"name": {"type": "string"}}}}

        result = _inline_refs(schema, defs)

        assert result["type"] == "array"
        assert result["items"]["type"] == "object"

    def test_no_refs_unchanged(self):
        """Test schema without $refs is unchanged."""
        schema = {"type": "string"}
        defs = {}

        result = _inline_refs(schema, defs)

        assert result == {"type": "string"}

    def test_unknown_ref_unchanged(self):
        """Test unknown $ref is left unchanged."""
        schema = {"$ref": "#/$defs/Unknown"}
        defs = {"Student": {"type": "object"}}

        result = _inline_refs(schema, defs)

        assert result == {"$ref": "#/$defs/Unknown"}


# =============================================================================
# Tests for generate_resource_schemas
# =============================================================================


class TestGenerateResourceSchemas:
    """Tests for the generate_resource_schemas function."""

    def test_basic_resource_schema_generation(self):
        """Test basic schema generation from resource."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        assert len(schemas) == 3  # process_students, get_student, search_students
        function_names = [s["function"]["name"] for s in schemas]
        assert any("process_students" in name for name in function_names)
        assert any("get_student" in name for name in function_names)
        assert any("search_students" in name for name in function_names)

    def test_function_name_format(self):
        """Test function name follows {resource_id}__{method_name} format."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        for schema in schemas:
            func_name = schema["function"]["name"]
            assert "__" in func_name
            parts = func_name.split("__")
            assert len(parts) == 2
            # Second part should be the method name
            assert parts[1] in ["process_students", "get_student", "search_students"]

    def test_pydantic_model_in_parameter(self):
        """Test Pydantic model parameter generates object schema."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        # Find the process_students schema
        process_schema = next(s for s in schemas if "process_students" in s["function"]["name"])
        params = process_schema["function"]["parameters"]

        assert "students" in params["properties"]
        students_param = params["properties"]["students"]
        assert students_param["type"] == "array"
        assert students_param["items"]["type"] == "object"
        assert "name" in students_param["items"]["properties"]
        assert "id" in students_param["items"]["properties"]

    def test_required_params(self):
        """Test required parameters are correctly identified."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        # Find get_student - student_id is required, include_grades has default
        get_schema = next(s for s in schemas if "get_student" in s["function"]["name"])
        params = get_schema["function"]["parameters"]

        assert "student_id" in params["required"]
        assert "include_grades" not in params["required"]

    def test_optional_params_not_in_required(self):
        """Test parameters with defaults are not in required list."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        # Find search_students - query is required, limit and offset have defaults
        search_schema = next(s for s in schemas if "search_students" in s["function"]["name"])
        params = search_schema["function"]["parameters"]

        assert "query" in params["required"]
        assert "limit" not in params["required"]
        assert "offset" not in params["required"]

    def test_mixed_primitive_types(self):
        """Test various primitive types are correctly converted."""
        resource = MixedTypesResource()
        schemas = generate_resource_schemas([resource])

        process_schema = schemas[0]
        props = process_schema["function"]["parameters"]["properties"]

        assert props["name"]["type"] == "string"
        assert props["count"]["type"] == "integer"
        assert props["ratio"]["type"] == "number"
        assert props["enabled"]["type"] == "boolean"
        assert props["tags"]["type"] == "array"
        assert props["metadata"]["type"] == "object"

    def test_nested_pydantic_model_in_parameter(self):
        """Test nested Pydantic model generates correct schema."""
        resource = NestedModelsResource()
        schemas = generate_resource_schemas([resource])

        # Find add_teacher schema
        teacher_schema = next(s for s in schemas if "add_teacher" in s["function"]["name"])
        params = teacher_schema["function"]["parameters"]

        teacher_param = params["properties"]["teacher"]
        assert teacher_param["type"] == "object"
        assert "name" in teacher_param["properties"]
        assert "address" in teacher_param["properties"]

        # Address should be inlined
        address = teacher_param["properties"]["address"]
        assert address["type"] == "object"
        assert "street" in address["properties"]

    def test_pydantic_model_with_list_field_in_parameter(self):
        """Test Pydantic model with list field generates correct schema."""
        resource = NestedModelsResource()
        schemas = generate_resource_schemas([resource])

        # Find create_classroom schema
        classroom_schema = next(s for s in schemas if "create_classroom" in s["function"]["name"])
        params = classroom_schema["function"]["parameters"]

        classroom_param = params["properties"]["classroom"]
        assert classroom_param["type"] == "object"
        assert "students" in classroom_param["properties"]

        students = classroom_param["properties"]["students"]
        assert students["type"] == "array"
        assert students["items"]["type"] == "object"
        assert "name" in students["items"]["properties"]

    def test_multiple_resources(self):
        """Test schema generation from multiple resources."""
        resources = [
            StudentManagementResource(),
            MixedTypesResource(),
        ]
        schemas = generate_resource_schemas(resources)

        # Should have schemas from both resources
        assert len(schemas) == 4  # 3 from student + 1 from mixed

    def test_parameter_descriptions(self):
        """Test parameter descriptions are included."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        get_schema = next(s for s in schemas if "get_student" in s["function"]["name"])
        props = get_schema["function"]["parameters"]["properties"]

        # Check that descriptions are present
        assert "description" in props["student_id"]
        assert "description" in props["include_grades"]

    def test_function_description(self):
        """Test function description is included."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        get_schema = next(s for s in schemas if "get_student" in s["function"]["name"])
        func = get_schema["function"]

        assert "description" in func
        assert "Get a single student" in func["description"]

    def test_schema_structure(self):
        """Test overall schema structure matches OpenAI format."""
        resource = StudentManagementResource()
        schemas = generate_resource_schemas([resource])

        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]
            assert schema["function"]["parameters"]["type"] == "object"
            assert "properties" in schema["function"]["parameters"]
            assert "required" in schema["function"]["parameters"]


# =============================================================================
# Integration Tests
# =============================================================================


class TestToolSchemaIntegration:
    """Integration tests for the full tool schema pipeline."""

    def test_end_to_end_with_complex_resource(self):
        """Test complete flow with a complex resource."""

        class ComplexResource(BaseResource):
            def __init__(self):
                super().__init__(resource_type="complex")

            @tool_use
            def complex_operation(
                self,
                required_str: str,
                required_list: list[Student],
                optional_int: int = 10,
                optional_teacher: Teacher | None = None,
            ) -> dict[str, Any]:
                """A complex operation with various parameter types.

                Args:
                    required_str: A required string
                    required_list: A required list of students
                    optional_int: An optional integer
                    optional_teacher: An optional teacher

                Returns:
                    Operation result
                """
                return {}

        resource = ComplexResource()
        schemas = generate_resource_schemas([resource])

        assert len(schemas) == 1
        schema = schemas[0]

        params = schema["function"]["parameters"]

        # Check required params
        assert "required_str" in params["required"]
        assert "required_list" in params["required"]
        assert "optional_int" not in params["required"]
        assert "optional_teacher" not in params["required"]

        # Check list[Student] schema
        students_schema = params["properties"]["required_list"]
        assert students_schema["type"] == "array"
        assert students_schema["items"]["type"] == "object"

    def test_empty_resource_list(self):
        """Test with empty resource list."""
        schemas = generate_resource_schemas([])
        assert schemas == []

    def test_resource_without_tool_use_methods(self):
        """Test resource without any @tool_use methods."""

        class EmptyResource(BaseResource):
            def __init__(self):
                super().__init__(resource_type="empty")

            def regular_method(self) -> str:
                """Not a tool_use method."""
                return "regular"

        resource = EmptyResource()
        schemas = generate_resource_schemas([resource])

        assert schemas == []
