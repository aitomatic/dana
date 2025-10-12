"""
Unit tests for workflow validation decorators.
"""

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output


class TestValidateInput:
    """Test @validate_input decorator."""

    def test_required_parameter_present(self):
        """Test that required parameter validation passes when present."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"required": True, "type": str})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "query": kwargs["query"]}

        workflow = TestWorkflow()
        result = workflow._do_execute(query="test query")
        assert result["success"] is True
        assert result["query"] == "test query"

    def test_required_parameter_missing(self):
        """Test that required parameter validation fails when missing."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"required": True, "type": str})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "required" in result["message"].lower()
        assert result["field"] == "query"

    def test_type_validation_success(self):
        """Test that type validation passes for correct type."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(count={"type": int})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "count": kwargs.get("count")}

        workflow = TestWorkflow()
        result = workflow._do_execute(count=5)
        assert result["success"] is True
        assert result["count"] == 5

    def test_type_validation_failure(self):
        """Test that type validation fails for incorrect type."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(count={"type": int})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute(count="5")
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "type" in result["message"].lower()

    def test_enum_validation_success(self):
        """Test that enum validation passes for valid value."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(synthesis_type={"enum": ["themes", "timeline"]})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "type": kwargs.get("synthesis_type")}

        workflow = TestWorkflow()
        result = workflow._do_execute(synthesis_type="themes")
        assert result["success"] is True
        assert result["type"] == "themes"

    def test_enum_validation_failure(self):
        """Test that enum validation fails for invalid value."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(synthesis_type={"enum": ["themes", "timeline"]})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute(synthesis_type="invalid")
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "one of" in result["message"].lower()

    def test_min_value_validation_success(self):
        """Test that min_value validation passes."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(max_sources={"type": int, "min_value": 1})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "value": kwargs.get("max_sources")}

        workflow = TestWorkflow()
        result = workflow._do_execute(max_sources=5)
        assert result["success"] is True
        assert result["value"] == 5

    def test_min_value_validation_failure(self):
        """Test that min_value validation fails."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(max_sources={"type": int, "min_value": 1})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute(max_sources=0)
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert ">=" in result["message"]

    def test_max_value_validation_failure(self):
        """Test that max_value validation fails."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(max_sources={"type": int, "max_value": 100})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute(max_sources=101)
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "<=" in result["message"]

    def test_min_length_validation_success(self):
        """Test that min_length validation passes."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"type": str, "min_length": 1})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "query": kwargs.get("query")}

        workflow = TestWorkflow()
        result = workflow._do_execute(query="test")
        assert result["success"] is True

    def test_min_length_validation_failure(self):
        """Test that min_length validation fails."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"type": str, "min_length": 1})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute(query="")
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "length" in result["message"].lower()

    def test_max_length_validation_failure(self):
        """Test that max_length validation fails."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"type": str, "max_length": 10})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute(query="this is a very long query")
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "length" in result["message"].lower()

    def test_default_value_applied(self):
        """Test that default values are applied when parameter is missing."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(max_results={"type": int, "default": 10})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "max_results": kwargs.get("max_results")}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is True
        assert result["max_results"] == 10

    def test_custom_validator_success(self):
        """Test that custom validator passes."""

        def is_even(value):
            return value % 2 == 0

        class TestWorkflow(BaseWorkflow):
            @validate_input(count={"type": int, "validator": is_even})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "count": kwargs.get("count")}

        workflow = TestWorkflow()
        result = workflow._do_execute(count=4)
        assert result["success"] is True

    def test_custom_validator_failure(self):
        """Test that custom validator fails."""

        def is_even(value):
            return value % 2 == 0

        class TestWorkflow(BaseWorkflow):
            @validate_input(count={"type": int, "validator": is_even})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute(count=5)
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "validation" in result["message"].lower()

    def test_multiple_parameters(self):
        """Test validation of multiple parameters."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(
                query={"required": True, "type": str, "min_length": 1},
                max_results={"type": int, "min_value": 1, "max_value": 100, "default": 10},
                include_metadata={"type": bool, "default": False},
            )
            def _do_execute(self, **kwargs) -> DictParams:
                return {
                    "success": True,
                    "query": kwargs["query"],
                    "max_results": kwargs["max_results"],
                    "include_metadata": kwargs["include_metadata"],
                }

        workflow = TestWorkflow()
        result = workflow._do_execute(query="test", max_results=20)
        assert result["success"] is True
        assert result["query"] == "test"
        assert result["max_results"] == 20
        assert result["include_metadata"] is False

    def test_optional_parameter_none(self):
        """Test that optional parameters can be None."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(optional_param={"type": str})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "value": kwargs.get("optional_param")}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is True
        assert result["value"] is None


class TestValidateOutput:
    """Test @validate_output decorator."""

    def test_required_field_present(self):
        """Test that required output field validation passes when present."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(success={"required": True, "type": bool})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is True

    def test_required_field_missing(self):
        """Test that required output field validation fails when missing."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(success={"required": True, "type": bool})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"data": "something"}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "required" in result["message"].lower()

    def test_output_type_validation_success(self):
        """Test that output type validation passes."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(results={"type": list})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"results": [1, 2, 3]}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["results"] == [1, 2, 3]

    def test_output_type_validation_failure(self):
        """Test that output type validation fails."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(results={"type": list})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"results": "not a list"}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "type" in result["message"].lower()

    def test_output_enum_validation_failure(self):
        """Test that output enum validation fails."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(status={"enum": ["pending", "completed", "failed"]})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"status": "invalid_status"}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "one of" in result["message"].lower()

    def test_output_min_length_validation(self):
        """Test that output min_length validation works."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(results={"type": list, "min_length": 1})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"results": []}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "length" in result["message"].lower()

    def test_multiple_output_fields(self):
        """Test validation of multiple output fields."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(
                success={"required": True, "type": bool},
                results={"required": True, "type": list, "min_length": 0},
                query={"required": True, "type": str},
            )
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "results": [1, 2, 3], "query": "test"}

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is True
        assert result["results"] == [1, 2, 3]
        assert result["query"] == "test"

    def test_output_not_dict(self):
        """Test that output validation fails if result is not a dict."""

        class TestWorkflow(BaseWorkflow):
            @validate_output(success={"required": True})
            def _do_execute(self, **kwargs) -> DictParams:
                return "not a dict"  # type: ignore

        workflow = TestWorkflow()
        result = workflow._do_execute()
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "dictionary" in result["message"].lower()


class TestCombinedValidation:
    """Test combining @validate_input and @validate_output."""

    def test_both_decorators_success(self):
        """Test that both decorators work together successfully."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"required": True, "type": str, "min_length": 1})
            @validate_output(success={"required": True, "type": bool}, results={"required": True, "type": list})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"success": True, "results": ["result1", "result2"], "query": kwargs["query"]}

        workflow = TestWorkflow()
        result = workflow._do_execute(query="test")
        assert result["success"] is True
        assert result["results"] == ["result1", "result2"]

    def test_input_validation_fails_first(self):
        """Test that input validation fails before output validation."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"required": True, "type": str})
            @validate_output(success={"required": True, "type": bool})
            def _do_execute(self, **kwargs) -> DictParams:
                # This should never execute due to input validation failure
                return {"wrong": "output"}

        workflow = TestWorkflow()
        result = workflow._do_execute()  # Missing query
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "required" in result["message"].lower()

    def test_output_validation_fails_after_input_success(self):
        """Test that output validation can fail even when input validation passes."""

        class TestWorkflow(BaseWorkflow):
            @validate_input(query={"required": True, "type": str})
            @validate_output(success={"required": True, "type": bool})
            def _do_execute(self, **kwargs) -> DictParams:
                return {"query": kwargs["query"]}  # Missing success field

        workflow = TestWorkflow()
        result = workflow._do_execute(query="test")
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "success" in result["message"]
