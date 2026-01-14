"""
HarnessAgent - Instrumented STARAgent for robustness testing.

Wraps STARAgent with phase instrumentation, loop tracking, and fault injection.

By default uses the codec system (CSXMLCodec) for reliable tool parsing.
Pass codec=None to use the legacy system for backward compatibility testing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from dana.common.protocols import DictParams
from dana.core.agent.star_agent import STARAgent
from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG
from dana.core.knowledge.prompts.codecs import CSXMLCodec

from .fault_injection import FaultInjector
from .mocks.llm_client import MockLLMClient


@dataclass
class PhaseRecord:
    """Record of a single phase execution."""

    phase: str
    iteration: int
    timestamp: float
    duration_ms: float
    input_keys: list[str]
    output_keys: list[str]
    exit_flag_set: bool
    error: str | None = None


@dataclass
class LoopRecord:
    """Record of a complete STAR loop execution."""

    start_time: float
    end_time: float
    iterations: int
    phases: list[PhaseRecord] = field(default_factory=list)
    exit_reason: str = "unknown"
    final_response: str | None = None
    error: str | None = None


class HarnessAgent(STARAgent):
    """
    STARAgent wrapper with instrumentation for robustness testing.

    Features:
    - Phase execution tracking (timing, inputs, outputs)
    - Loop iteration counting
    - Exit reason capture
    - Fault injection integration
    - Mock LLM support
    """

    def __init__(
        self,
        mock_llm: MockLLMClient | None = None,
        fault_injector: FaultInjector | None = None,
        agent_type: str = "test_harness",
        auto_register: bool = False,
        codec: type | None = CSXMLCodec,  # Default to codec system for reliability
        **kwargs,
    ):
        # Initialize with codec system by default for reliable tool parsing
        # Pass codec=None to test legacy system
        super().__init__(
            agent_type=agent_type,
            auto_register=auto_register,
            codec=codec,
            **kwargs,
        )

        # Override LLM client if mock provided
        self._mock_llm = mock_llm
        if mock_llm is not None:
            self._llm_client = mock_llm

        # Fault injection
        self._fault_injector = fault_injector

        # Instrumentation
        self._phase_history: list[PhaseRecord] = []
        self._loop_records: list[LoopRecord] = []
        self._current_loop: LoopRecord | None = None
        self._current_iteration: int = 0

    # ==================== LLM Client Override ====================

    @property
    def llm_client(self):
        """Return mock LLM if configured, otherwise real LLM."""
        if self._mock_llm is not None:
            return self._mock_llm
        return super().llm_client

    @llm_client.setter
    def llm_client(self, value):
        """Set the LLM client."""
        if isinstance(value, MockLLMClient):
            self._mock_llm = value
        else:
            self._llm_client = value

    # ==================== Instrumented STAR Methods ====================

    def _record_phase_start(self, phase: str, trace: DictParams | None) -> float:
        """Record the start of a phase."""
        return time.time()

    def _record_phase_end(
        self,
        phase: str,
        start_time: float,
        trace_in: DictParams | None,
        trace_out: DictParams | None,
        error: str | None = None,
    ) -> None:
        """Record the end of a phase."""
        duration_ms = (time.time() - start_time) * 1000

        # Check if exit flag was set
        exit_flag_set = False
        if trace_out:
            # Check nested trace structures
            for key in ["trace_percepts", "trace_thoughts", "trace_outputs", "trace_learning"]:
                if key in trace_out and isinstance(trace_out[key], dict):
                    if trace_out[key].get(EXIT_STAR_LOOP_FLAG, False):
                        exit_flag_set = True
                        break
            # Also check top level
            if trace_out.get(EXIT_STAR_LOOP_FLAG, False):
                exit_flag_set = True

        record = PhaseRecord(
            phase=phase,
            iteration=self._current_iteration,
            timestamp=start_time,
            duration_ms=duration_ms,
            input_keys=list(trace_in.keys()) if trace_in else [],
            output_keys=list(trace_out.keys()) if trace_out else [],
            exit_flag_set=exit_flag_set,
            error=error,
        )
        self._phase_history.append(record)

        if self._current_loop:
            self._current_loop.phases.append(record)

    def _see(self, trace_inputs: DictParams) -> DictParams:
        """Instrumented _see method."""
        start_time = self._record_phase_start("see", trace_inputs)

        # Inject fault if configured
        if self._fault_injector:
            try:
                self._fault_injector.inject("see", trace_inputs)
            except Exception as e:
                self._record_phase_end("see", start_time, trace_inputs, None, str(e))
                raise

        try:
            result = super()._see(trace_inputs)
            self._record_phase_end("see", start_time, trace_inputs, result)
            return result
        except Exception as e:
            self._record_phase_end("see", start_time, trace_inputs, None, str(e))
            raise

    def _think(self, trace_percepts: DictParams) -> DictParams:
        """Instrumented _think method."""
        start_time = self._record_phase_start("think", trace_percepts)

        # Inject fault if configured
        if self._fault_injector:
            try:
                self._fault_injector.inject("think", trace_percepts)
            except Exception as e:
                self._record_phase_end("think", start_time, trace_percepts, None, str(e))
                raise

        try:
            result = super()._think(trace_percepts)
            self._record_phase_end("think", start_time, trace_percepts, result)
            return result
        except Exception as e:
            self._record_phase_end("think", start_time, trace_percepts, None, str(e))
            raise

    def _act(self, trace_thoughts: DictParams) -> DictParams:
        """Instrumented _act method."""
        start_time = self._record_phase_start("act", trace_thoughts)

        # Inject fault if configured
        if self._fault_injector:
            try:
                self._fault_injector.inject("act", trace_thoughts)
            except Exception as e:
                self._record_phase_end("act", start_time, trace_thoughts, None, str(e))
                raise

        try:
            result = super()._act(trace_thoughts)
            self._record_phase_end("act", start_time, trace_thoughts, result)
            return result
        except Exception as e:
            self._record_phase_end("act", start_time, trace_thoughts, None, str(e))
            raise

    def _reflect(self, trace_outputs: DictParams) -> DictParams:
        """Instrumented _reflect method."""
        start_time = self._record_phase_start("reflect", trace_outputs)

        # Inject fault if configured
        if self._fault_injector:
            try:
                self._fault_injector.inject("reflect", trace_outputs)
            except Exception as e:
                self._record_phase_end("reflect", start_time, trace_outputs, None, str(e))
                raise

        try:
            result = super()._reflect(trace_outputs)
            self._record_phase_end("reflect", start_time, trace_outputs, result)
            return result
        except Exception as e:
            self._record_phase_end("reflect", start_time, trace_outputs, None, str(e))
            raise

    # ==================== Query Instrumentation ====================

    def query(self, **kwargs) -> DictParams:
        """Instrumented query method."""
        # Start new loop record
        self._current_loop = LoopRecord(
            start_time=time.time(),
            end_time=0,
            iterations=0,
        )
        self._current_iteration = 0

        try:
            result = super().query(**kwargs)

            # Determine exit reason
            self._current_loop.exit_reason = self._determine_exit_reason(result)
            self._current_loop.final_response = result.get("response", "")

            return result
        except Exception as e:
            self._current_loop.error = str(e)
            self._current_loop.exit_reason = "exception"
            raise
        finally:
            self._current_loop.end_time = time.time()
            self._current_loop.iterations = self._current_iteration
            self._loop_records.append(self._current_loop)
            self._current_loop = None

    def _determine_exit_reason(self, result: DictParams) -> str:
        """Determine why the loop exited."""
        # Check for error
        if result.get("error"):
            return "error"

        # Check phase history for exit flag
        for record in reversed(self._phase_history):
            if record.iteration == self._current_iteration - 1:
                if record.exit_flag_set:
                    if record.phase == "think":
                        return "no_tool_calls"
                    return f"exit_flag_in_{record.phase}"

        # Check if max iterations was reached
        if self._current_iteration >= 10:  # MAX_ITERATIONS
            return "max_iterations"

        return "normal"

    # ==================== Instrumentation API ====================

    def get_loop_count(self) -> int:
        """Get the number of loop iterations in the last query."""
        if self._loop_records:
            return self._loop_records[-1].iterations
        return 0

    def get_phase_history(self) -> list[PhaseRecord]:
        """Get full phase execution history."""
        return self._phase_history.copy()

    def get_loop_records(self) -> list[LoopRecord]:
        """Get all loop records."""
        return self._loop_records.copy()

    def get_last_loop(self) -> LoopRecord | None:
        """Get the most recent loop record."""
        return self._loop_records[-1] if self._loop_records else None

    def get_exit_reason(self) -> str:
        """Get the exit reason for the last query."""
        if self._loop_records:
            return self._loop_records[-1].exit_reason
        return "no_query"

    def get_phases_by_name(self, phase: str) -> list[PhaseRecord]:
        """Get all records for a specific phase."""
        return [r for r in self._phase_history if r.phase == phase]

    def get_phase_durations(self, phase: str | None = None) -> dict[str, list[float]]:
        """Get duration statistics by phase."""
        durations: dict[str, list[float]] = {}
        for record in self._phase_history:
            if phase is None or record.phase == phase:
                if record.phase not in durations:
                    durations[record.phase] = []
                durations[record.phase].append(record.duration_ms)
        return durations

    def clear_history(self) -> None:
        """Clear all instrumentation history."""
        self._phase_history.clear()
        self._loop_records.clear()
        self._current_iteration = 0

    def get_errors(self) -> list[PhaseRecord]:
        """Get all phase records that had errors."""
        return [r for r in self._phase_history if r.error is not None]

    def had_errors(self) -> bool:
        """Check if any phase had errors."""
        return any(r.error is not None for r in self._phase_history)

    # ==================== Test Helpers ====================

    def assert_no_errors(self) -> None:
        """Assert that no errors occurred during execution."""
        errors = self.get_errors()
        if errors:
            error_msgs = [f"{e.phase}@{e.iteration}: {e.error}" for e in errors]
            raise AssertionError(f"Errors occurred: {error_msgs}")

    def assert_exit_reason(self, expected: str) -> None:
        """Assert the exit reason matches expected."""
        actual = self.get_exit_reason()
        if actual != expected:
            raise AssertionError(f"Expected exit reason '{expected}', got '{actual}'")

    def assert_iteration_count(self, expected: int) -> None:
        """Assert the iteration count matches expected."""
        actual = self.get_loop_count()
        if actual != expected:
            raise AssertionError(f"Expected {expected} iterations, got {actual}")

    def assert_phase_executed(self, phase: str, min_times: int = 1) -> None:
        """Assert a phase was executed at least min_times."""
        count = len(self.get_phases_by_name(phase))
        if count < min_times:
            raise AssertionError(f"Expected {phase} executed at least {min_times} times, got {count}")
