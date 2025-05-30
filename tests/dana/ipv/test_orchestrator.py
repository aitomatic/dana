"""
Unit tests for IPV orchestrator.

Tests the IPVOrchestrator class that coordinates the execution of
the three IPV phases (Infer-Process-Validate) in sequence.
"""

from opendxa.dana.ipv.base import IPVConfig, IPVExecutionError, IPVPhase, IPVPhaseType, IPVResult, PrecisionLevel, ReliabilityLevel
from opendxa.dana.ipv.orchestrator import IPVOrchestrator
from opendxa.dana.ipv.phases import InferPhase, ProcessPhase, ValidatePhase


class MockPhase(IPVPhase):
    """Mock IPV phase for testing."""

    def __init__(
        self, phase_type: IPVPhaseType, should_succeed: bool = True, result_value: str = "mock result", execution_time: float = 0.1
    ):
        super().__init__(phase_type)
        self.should_succeed = should_succeed
        self.result_value = result_value
        self.execution_time = execution_time
        self.call_count = 0
        self.last_input = None
        self.last_context = None
        self.last_config = None

    def execute(self, input_data, context, config):
        self.call_count += 1
        self.last_input = input_data
        self.last_context = context
        self.last_config = config

        if self.should_succeed:
            return IPVResult(
                success=True,
                result=self.result_value,
                execution_time=self.execution_time,
                metadata={"phase": self.phase_type.value, "call_count": self.call_count},
            )
        else:
            return IPVResult(
                success=False,
                result=None,
                error=IPVExecutionError(f"{self.phase_type.value} phase failed"),
                execution_time=self.execution_time,
            )


class TestIPVOrchestrator:
    """Test IPVOrchestrator class."""

    def test_default_initialization(self):
        """Test orchestrator with default phases."""
        orchestrator = IPVOrchestrator()

        assert isinstance(orchestrator.infer_phase, InferPhase)
        assert isinstance(orchestrator.process_phase, ProcessPhase)
        assert isinstance(orchestrator.validate_phase, ValidatePhase)
        assert orchestrator._debug_mode is False
        assert len(orchestrator._execution_history) == 0

    def test_custom_phases_initialization(self):
        """Test orchestrator with custom phases."""
        infer_phase = MockPhase(IPVPhaseType.INFER)
        process_phase = MockPhase(IPVPhaseType.PROCESS)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        assert orchestrator.infer_phase == infer_phase
        assert orchestrator.process_phase == process_phase
        assert orchestrator.validate_phase == validate_phase

    def test_debug_mode(self):
        """Test debug mode setting."""
        infer_phase = MockPhase(IPVPhaseType.INFER)
        process_phase = MockPhase(IPVPhaseType.PROCESS)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        # Initially debug mode is off
        assert orchestrator._debug_mode is False
        assert infer_phase._debug_mode is False
        assert process_phase._debug_mode is False
        assert validate_phase._debug_mode is False

        # Enable debug mode
        orchestrator.set_debug_mode(True)
        assert orchestrator._debug_mode is True
        assert infer_phase._debug_mode is True
        assert process_phase._debug_mode is True
        assert validate_phase._debug_mode is True

        # Disable debug mode
        orchestrator.set_debug_mode(False)
        assert orchestrator._debug_mode is False
        assert infer_phase._debug_mode is False
        assert process_phase._debug_mode is False
        assert validate_phase._debug_mode is False

    def test_successful_pipeline_execution(self):
        """Test successful execution of the complete IPV pipeline."""
        infer_phase = MockPhase(IPVPhaseType.INFER, result_value="infer result")
        process_phase = MockPhase(IPVPhaseType.PROCESS, result_value="process result")
        validate_phase = MockPhase(IPVPhaseType.VALIDATE, result_value="validate result")

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        config = IPVConfig(reliability=ReliabilityLevel.HIGH)
        result = orchestrator.execute_ipv_pipeline("test input", "test context", config)

        # Check final result
        assert result.is_success()
        assert result.result == "validate result"
        assert result.execution_time is not None and result.execution_time > 0

        # Check that all phases were called
        assert infer_phase.call_count == 1
        assert process_phase.call_count == 1
        assert validate_phase.call_count == 1

        # Check phase inputs
        assert infer_phase.last_input == "test input"
        assert infer_phase.last_context == "test context"
        assert infer_phase.last_config == config

        assert process_phase.last_input == "infer result"
        assert process_phase.last_context == "test context"
        assert process_phase.last_config == config

        assert validate_phase.last_input == "process result"
        # validate_phase gets the infer result as context
        assert validate_phase.last_context == "infer result"
        assert validate_phase.last_config == config

        # Check execution history
        assert len(orchestrator._execution_history) == 1
        execution_record = orchestrator._execution_history[0]
        assert execution_record["success"] is True
        assert execution_record["input_data"] == "test input"
        assert execution_record["final_result"] == "validate result"

    def test_pipeline_with_default_config(self):
        """Test pipeline execution with default configuration."""
        infer_phase = MockPhase(IPVPhaseType.INFER)
        process_phase = MockPhase(IPVPhaseType.PROCESS)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        result = orchestrator.execute_ipv_pipeline("test input")

        assert result.is_success()
        assert result.result is not None
        assert result.execution_time is not None and result.execution_time > 0

        # Check that default config was used
        assert isinstance(infer_phase.last_config, IPVConfig)
        assert infer_phase.last_config.reliability == ReliabilityLevel.HIGH

    def test_pipeline_with_debug_config(self):
        """Test pipeline execution with debug mode in config."""
        infer_phase = MockPhase(IPVPhaseType.INFER)
        process_phase = MockPhase(IPVPhaseType.PROCESS)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        config = IPVConfig(debug_mode=True)
        result = orchestrator.execute_ipv_pipeline("test input", config=config)

        assert result.is_success()
        # Debug mode should have been enabled
        assert orchestrator._debug_mode is True
        assert all(phase._debug_mode for phase in [infer_phase, process_phase, validate_phase])

    def test_infer_phase_failure(self):
        """Test pipeline failure in INFER phase."""
        infer_phase = MockPhase(IPVPhaseType.INFER, should_succeed=False)
        process_phase = MockPhase(IPVPhaseType.PROCESS)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        result = orchestrator.execute_ipv_pipeline("test input")

        # Pipeline should fail
        assert not result.is_success()
        assert isinstance(result.error, IPVExecutionError)

        # Only infer phase should have been called
        assert infer_phase.call_count == 1
        assert process_phase.call_count == 0
        assert validate_phase.call_count == 0

        # Check execution history
        assert len(orchestrator._execution_history) == 1
        execution_record = orchestrator._execution_history[0]
        assert execution_record["success"] is False
        assert len(execution_record["errors"]) > 0

    def test_process_phase_failure(self):
        """Test pipeline failure in PROCESS phase."""
        infer_phase = MockPhase(IPVPhaseType.INFER)
        process_phase = MockPhase(IPVPhaseType.PROCESS, should_succeed=False)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        result = orchestrator.execute_ipv_pipeline("test input")

        # Pipeline should fail
        assert not result.is_success()
        assert isinstance(result.error, IPVExecutionError)

        # Infer and process phases should have been called
        assert infer_phase.call_count == 1
        assert process_phase.call_count == 1
        assert validate_phase.call_count == 0

    def test_validate_phase_failure(self):
        """Test pipeline failure in VALIDATE phase."""
        infer_phase = MockPhase(IPVPhaseType.INFER)
        process_phase = MockPhase(IPVPhaseType.PROCESS)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE, should_succeed=False)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        result = orchestrator.execute_ipv_pipeline("test input")

        # Pipeline should fail
        assert not result.is_success()
        assert isinstance(result.error, IPVExecutionError)

        # All phases should have been called
        assert infer_phase.call_count == 1
        assert process_phase.call_count == 1
        assert validate_phase.call_count == 1

    def test_execution_history(self):
        """Test execution history tracking."""
        orchestrator = IPVOrchestrator()

        # Initially empty
        assert len(orchestrator.get_execution_history()) == 0

        # Execute pipeline multiple times
        for i in range(3):
            result = orchestrator.execute_ipv_pipeline(f"input {i}")
            assert result.is_success()

        # Check history
        history = orchestrator.get_execution_history()
        assert len(history) == 3

        for i, record in enumerate(history):
            assert record["input_data"] == f"input {i}"
            assert record["success"] is True
            assert "execution_id" in record
            assert "total_time" in record

        # Clear history
        orchestrator.clear_execution_history()
        assert len(orchestrator.get_execution_history()) == 0

    def test_performance_stats(self):
        """Test performance statistics calculation."""
        infer_phase = MockPhase(IPVPhaseType.INFER, execution_time=0.1)
        process_phase = MockPhase(IPVPhaseType.PROCESS, execution_time=0.2)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE, execution_time=0.1)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        # Initially no stats
        stats = orchestrator.get_performance_stats()
        assert stats["total_executions"] == 0

        # Execute successful pipelines
        for i in range(3):
            result = orchestrator.execute_ipv_pipeline(f"input {i}")
            assert result.is_success()

        # Execute one failed pipeline
        failing_infer = MockPhase(IPVPhaseType.INFER, should_succeed=False)
        orchestrator.infer_phase = failing_infer
        result = orchestrator.execute_ipv_pipeline("failing input")
        assert not result.is_success()

        # Check stats
        stats = orchestrator.get_performance_stats()
        assert stats["total_executions"] == 4
        assert stats["successful_executions"] == 3
        assert stats["failed_executions"] == 1
        assert stats["success_rate"] == 0.75
        assert "avg_execution_time" in stats
        assert "min_execution_time" in stats
        assert "max_execution_time" in stats
        assert "common_errors" in stats

    def test_metadata_propagation(self):
        """Test that metadata is properly propagated through the pipeline."""
        infer_phase = MockPhase(IPVPhaseType.INFER)
        process_phase = MockPhase(IPVPhaseType.PROCESS)
        validate_phase = MockPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        result = orchestrator.execute_ipv_pipeline("test input")

        assert result.is_success()
        assert "iteration" in result.metadata
        assert "infer_metadata" in result.metadata
        assert "process_metadata" in result.metadata
        assert "validate_metadata" in result.metadata
        assert "phase_times" in result.metadata

        # Check phase times
        phase_times = result.metadata["phase_times"]
        assert "infer" in phase_times
        assert "process" in phase_times
        assert "validate" in phase_times
        assert all(time > 0 for time in phase_times.values())

    def test_max_iterations_config(self):
        """Test that max_iterations configuration is respected."""
        # This test is more relevant when we implement actual iteration logic
        # For now, we just verify the config is passed through
        config = IPVConfig(max_iterations=5)
        orchestrator = IPVOrchestrator()

        result = orchestrator.execute_ipv_pipeline("test input", config=config)
        assert result.is_success()

        # Check that the config was used
        execution_record = orchestrator.get_execution_history()[0]
        assert execution_record["config"]["max_iterations"] == 5


class TestIPVOrchestratorIntegration:
    """Integration tests for IPV orchestrator with real phases."""

    def test_real_phases_integration(self):
        """Test orchestrator with real IPV phases."""
        orchestrator = IPVOrchestrator()

        config = IPVConfig(reliability=ReliabilityLevel.HIGH, precision=PrecisionLevel.EXACT, debug_mode=True)

        result = orchestrator.execute_ipv_pipeline("Extract the price from: The item costs $29.99", context=None, config=config)

        assert result.is_success()
        assert result.result is not None
        assert result.execution_time is not None and result.execution_time > 0

        # Check execution history
        history = orchestrator.get_execution_history()
        assert len(history) == 1
        assert history[0]["success"] is True

    def test_different_input_types(self):
        """Test orchestrator with different input types."""
        orchestrator = IPVOrchestrator()

        test_inputs = ["string input", {"dict": "input"}, ["list", "input"], 42, None]

        for test_input in test_inputs:
            result = orchestrator.execute_ipv_pipeline(test_input)
            # All should succeed with default phases
            assert result.is_success(), f"Failed for input type: {type(test_input)}"

    def test_context_passing(self):
        """Test that context is properly passed through phases."""

        class ContextTrackingPhase(IPVPhase):
            def __init__(self, phase_type):
                super().__init__(phase_type)
                self.received_contexts = []

            def execute(self, input_data, context, config):
                self.received_contexts.append(context)
                return IPVResult(success=True, result=f"{self.phase_type.value} result", metadata={"context_received": context is not None})

        infer_phase = ContextTrackingPhase(IPVPhaseType.INFER)
        process_phase = ContextTrackingPhase(IPVPhaseType.PROCESS)
        validate_phase = ContextTrackingPhase(IPVPhaseType.VALIDATE)

        orchestrator = IPVOrchestrator(infer_phase=infer_phase, process_phase=process_phase, validate_phase=validate_phase)

        test_context = {"test": "context"}
        result = orchestrator.execute_ipv_pipeline("test input", test_context)

        assert result.is_success()

        # Check context passing
        assert len(infer_phase.received_contexts) == 1
        assert infer_phase.received_contexts[0] == test_context

        assert len(process_phase.received_contexts) == 1
        assert process_phase.received_contexts[0] == test_context

        assert len(validate_phase.received_contexts) == 1
        # Validate phase receives the infer result as context
        assert validate_phase.received_contexts[0] == "infer result"
