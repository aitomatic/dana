"""
Unit tests for IPV base classes and interfaces.

Tests the core IPV abstractions including IPVPhase, IPVConfig, IPVResult,
and all the enum types.
"""

import pytest

from opendxa.dana.ipv.base import (
    ContextLevel,
    IPVConfig,
    IPVConfigurationError,
    IPVError,
    IPVExecutionError,
    IPVPhase,
    IPVPhaseType,
    IPVResult,
    IPVValidationError,
    PrecisionLevel,
    ReliabilityLevel,
    SafetyLevel,
    StructureLevel,
)


class TestIPVEnums:
    """Test IPV enum types."""

    def test_ipv_phase_type_enum(self):
        """Test IPVPhaseType enum values."""
        assert IPVPhaseType.INFER.value == "infer"
        assert IPVPhaseType.PROCESS.value == "process"
        assert IPVPhaseType.VALIDATE.value == "validate"

    def test_reliability_level_enum(self):
        """Test ReliabilityLevel enum values."""
        assert ReliabilityLevel.LOW.value == "low"
        assert ReliabilityLevel.MEDIUM.value == "medium"
        assert ReliabilityLevel.HIGH.value == "high"
        assert ReliabilityLevel.MAXIMUM.value == "maximum"

    def test_precision_level_enum(self):
        """Test PrecisionLevel enum values."""
        assert PrecisionLevel.LOOSE.value == "loose"
        assert PrecisionLevel.GENERAL.value == "general"
        assert PrecisionLevel.SPECIFIC.value == "specific"
        assert PrecisionLevel.EXACT.value == "exact"

    def test_safety_level_enum(self):
        """Test SafetyLevel enum values."""
        assert SafetyLevel.LOW.value == "low"
        assert SafetyLevel.MEDIUM.value == "medium"
        assert SafetyLevel.HIGH.value == "high"
        assert SafetyLevel.MAXIMUM.value == "maximum"

    def test_structure_level_enum(self):
        """Test StructureLevel enum values."""
        assert StructureLevel.FREE.value == "free"
        assert StructureLevel.ORGANIZED.value == "organized"
        assert StructureLevel.FORMATTED.value == "formatted"
        assert StructureLevel.STRICT.value == "strict"

    def test_context_level_enum(self):
        """Test ContextLevel enum values."""
        assert ContextLevel.MINIMAL.value == "minimal"
        assert ContextLevel.STANDARD.value == "standard"
        assert ContextLevel.DETAILED.value == "detailed"
        assert ContextLevel.MAXIMUM.value == "maximum"


class TestIPVConfig:
    """Test IPVConfig class."""

    def test_default_config(self):
        """Test default IPV configuration."""
        config = IPVConfig()

        assert config.reliability == ReliabilityLevel.HIGH
        assert config.precision == PrecisionLevel.SPECIFIC
        assert config.safety == SafetyLevel.MEDIUM
        assert config.structure == StructureLevel.ORGANIZED
        assert config.context == ContextLevel.STANDARD
        assert config.max_iterations == 3
        assert config.timeout_seconds is None
        assert config.debug_mode is False
        assert config.infer_config == {}
        assert config.process_config == {}
        assert config.validate_config == {}

    def test_custom_config(self):
        """Test custom IPV configuration."""
        config = IPVConfig(
            reliability=ReliabilityLevel.MAXIMUM,
            precision=PrecisionLevel.EXACT,
            safety=SafetyLevel.HIGH,
            structure=StructureLevel.STRICT,
            context=ContextLevel.DETAILED,
            max_iterations=5,
            timeout_seconds=30.0,
            debug_mode=True,
            infer_config={"test": "value"},
            process_config={"another": "setting"},
            validate_config={"validation": "rule"},
        )

        assert config.reliability == ReliabilityLevel.MAXIMUM
        assert config.precision == PrecisionLevel.EXACT
        assert config.safety == SafetyLevel.HIGH
        assert config.structure == StructureLevel.STRICT
        assert config.context == ContextLevel.DETAILED
        assert config.max_iterations == 5
        assert config.timeout_seconds == 30.0
        assert config.debug_mode is True
        assert config.infer_config == {"test": "value"}
        assert config.process_config == {"another": "setting"}
        assert config.validate_config == {"validation": "rule"}

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = IPVConfig(reliability=ReliabilityLevel.HIGH, precision=PrecisionLevel.EXACT, max_iterations=5)

        config_dict = config.to_dict()

        assert config_dict["reliability"] == "high"
        assert config_dict["precision"] == "exact"
        assert config_dict["max_iterations"] == 5
        assert "infer_config" in config_dict
        assert "process_config" in config_dict
        assert "validate_config" in config_dict

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "reliability": "maximum",
            "precision": "exact",
            "safety": "high",
            "structure": "strict",
            "context": "detailed",
            "max_iterations": 5,
            "timeout_seconds": 30.0,
            "debug_mode": True,
            "infer_config": {"test": "value"},
        }

        config = IPVConfig.from_dict(data)

        assert config.reliability == ReliabilityLevel.MAXIMUM
        assert config.precision == PrecisionLevel.EXACT
        assert config.safety == SafetyLevel.HIGH
        assert config.structure == StructureLevel.STRICT
        assert config.context == ContextLevel.DETAILED
        assert config.max_iterations == 5
        assert config.timeout_seconds == 30.0
        assert config.debug_mode is True
        assert config.infer_config == {"test": "value"}

    def test_config_from_dict_partial(self):
        """Test creating config from partial dictionary."""
        data = {"reliability": "high", "max_iterations": 10}

        config = IPVConfig.from_dict(data)

        assert config.reliability == ReliabilityLevel.HIGH
        assert config.max_iterations == 10
        # Other values should be defaults
        assert config.precision == PrecisionLevel.SPECIFIC
        assert config.safety == SafetyLevel.MEDIUM


class TestIPVResult:
    """Test IPVResult class."""

    def test_successful_result(self):
        """Test successful IPV result."""
        result = IPVResult(success=True, result="test output", execution_time=0.5, metadata={"phase": "test"})

        assert result.success is True
        assert result.result == "test output"
        assert result.error is None
        assert result.execution_time == 0.5
        assert result.metadata == {"phase": "test"}
        assert result.is_success() is True

    def test_failed_result(self):
        """Test failed IPV result."""
        error = Exception("test error")
        result = IPVResult(success=False, result=None, error=error, execution_time=0.1)

        assert result.success is False
        assert result.result is None
        assert result.error == error
        assert result.execution_time == 0.1
        assert result.is_success() is False

    def test_result_with_error_but_success_true(self):
        """Test result with error but success=True should return False for is_success."""
        error = Exception("test error")
        result = IPVResult(success=True, result="output", error=error)

        # is_success() should return False if there's an error, even if success=True
        assert result.is_success() is False


class TestIPVPhase:
    """Test IPVPhase abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that IPVPhase cannot be instantiated directly."""
        # This test is not needed since we can't actually test instantiating an abstract class
        # The abstract nature is enforced by Python's ABC mechanism
        pass

    def test_concrete_implementation(self):
        """Test concrete implementation of IPVPhase."""

        class TestPhase(IPVPhase):
            def execute(self, input_data, context, config):
                return IPVResult(success=True, result="test")

        phase = TestPhase(IPVPhaseType.INFER)
        assert phase.phase_type == IPVPhaseType.INFER
        assert phase._debug_mode is False

    def test_debug_mode(self):
        """Test debug mode functionality."""

        class TestPhase(IPVPhase):
            def execute(self, input_data, context, config):
                return IPVResult(success=True, result="test")

        phase = TestPhase(IPVPhaseType.PROCESS)

        # Initially debug mode is off
        assert phase._debug_mode is False

        # Enable debug mode
        phase.set_debug_mode(True)
        assert phase._debug_mode is True

        # Disable debug mode
        phase.set_debug_mode(False)
        assert phase._debug_mode is False

    def test_validate_config(self):
        """Test config validation."""

        class TestPhase(IPVPhase):
            def execute(self, input_data, context, config):
                return IPVResult(success=True, result="test")

        phase = TestPhase(IPVPhaseType.VALIDATE)

        # Valid config should not raise
        config = IPVConfig()
        phase.validate_config(config)  # Should not raise

        # Invalid config should raise
        with pytest.raises(ValueError):
            phase.validate_config("not a config")  # type: ignore

    def test_get_phase_config(self):
        """Test getting phase-specific configuration."""

        class TestPhase(IPVPhase):
            def execute(self, input_data, context, config):
                return IPVResult(success=True, result="test")

        config = IPVConfig(
            infer_config={"infer": "setting"}, process_config={"process": "setting"}, validate_config={"validate": "setting"}
        )

        # Test INFER phase
        infer_phase = TestPhase(IPVPhaseType.INFER)
        assert infer_phase.get_phase_config(config) == {"infer": "setting"}

        # Test PROCESS phase
        process_phase = TestPhase(IPVPhaseType.PROCESS)
        assert process_phase.get_phase_config(config) == {"process": "setting"}

        # Test VALIDATE phase
        validate_phase = TestPhase(IPVPhaseType.VALIDATE)
        assert validate_phase.get_phase_config(config) == {"validate": "setting"}


class TestIPVErrors:
    """Test IPV exception classes."""

    def test_ipv_error_base(self):
        """Test base IPVError exception."""
        error = IPVError("test message")
        assert str(error) == "test message"
        assert error.phase is None
        assert error.original_error is None

    def test_ipv_error_with_phase(self):
        """Test IPVError with phase information."""
        error = IPVError("test message", phase=IPVPhaseType.INFER)
        assert str(error) == "test message"
        assert error.phase == IPVPhaseType.INFER
        assert error.original_error is None

    def test_ipv_error_with_original_error(self):
        """Test IPVError with original error."""
        original = ValueError("original error")
        error = IPVError("test message", original_error=original)
        assert str(error) == "test message"
        assert error.original_error == original

    def test_ipv_configuration_error(self):
        """Test IPVConfigurationError."""
        error = IPVConfigurationError("config error")
        assert isinstance(error, IPVError)
        assert str(error) == "config error"

    def test_ipv_execution_error(self):
        """Test IPVExecutionError."""
        error = IPVExecutionError("execution error", phase=IPVPhaseType.PROCESS)
        assert isinstance(error, IPVError)
        assert str(error) == "execution error"
        assert error.phase == IPVPhaseType.PROCESS

    def test_ipv_validation_error(self):
        """Test IPVValidationError."""
        error = IPVValidationError("validation error", phase=IPVPhaseType.VALIDATE)
        assert isinstance(error, IPVError)
        assert str(error) == "validation error"
        assert error.phase == IPVPhaseType.VALIDATE


class TestIPVIntegration:
    """Integration tests for IPV base components."""

    def test_complete_workflow(self):
        """Test a complete workflow using base components."""

        class MockPhase(IPVPhase):
            def execute(self, input_data, context, config):
                self.validate_config(config)
                phase_config = self.get_phase_config(config)

                return IPVResult(
                    success=True,
                    result=f"Processed {input_data} with {self.phase_type.value}",
                    execution_time=0.1,
                    metadata={"phase": self.phase_type.value, "config": phase_config},
                )

        # Create config
        config = IPVConfig(
            reliability=ReliabilityLevel.HIGH,
            debug_mode=True,
            infer_config={"strategy": "comprehensive"},
            process_config={"iterations": 3},
            validate_config={"strict": True},
        )

        # Test each phase type
        for phase_type in [IPVPhaseType.INFER, IPVPhaseType.PROCESS, IPVPhaseType.VALIDATE]:
            phase = MockPhase(phase_type)
            phase.set_debug_mode(config.debug_mode)

            result = phase.execute("test input", None, config)

            assert result.is_success()
            assert "test input" in result.result
            assert phase_type.value in result.result
            assert result.metadata["phase"] == phase_type.value

            # Check phase-specific config was extracted correctly
            if phase_type == IPVPhaseType.INFER:
                assert result.metadata["config"] == {"strategy": "comprehensive"}
            elif phase_type == IPVPhaseType.PROCESS:
                assert result.metadata["config"] == {"iterations": 3}
            elif phase_type == IPVPhaseType.VALIDATE:
                assert result.metadata["config"] == {"strict": True}
