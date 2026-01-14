"""
Fault Injection Framework for STARAgent robustness testing.

Allows injecting faults at specific STAR phases with configurable probability.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal


@dataclass
class FaultConfig:
    """Configuration for a single fault injection."""

    phase: Literal["see", "think", "act", "reflect"]
    fault_type: Literal["exception", "timeout", "empty", "malformed", "hang", "delay"]
    probability: float = 1.0  # 0.0-1.0
    delay_ms: int = 0
    exception_type: type[Exception] = RuntimeError
    message: str = "Injected fault"
    # For conditional faults
    condition: Callable[[dict], bool] | None = None
    # Track how many times this fault has been triggered
    trigger_count: int = field(default=0, init=False)
    # Maximum number of times to trigger (-1 = unlimited)
    max_triggers: int = -1

    def should_trigger(self, context: dict | None = None) -> bool:
        """Determine if this fault should trigger."""
        # Check max triggers
        if self.max_triggers >= 0 and self.trigger_count >= self.max_triggers:
            return False

        # Check probability
        if random.random() > self.probability:
            return False

        # Check condition
        if self.condition is not None and context is not None:
            if not self.condition(context):
                return False

        return True

    def trigger(self) -> None:
        """Mark fault as triggered."""
        self.trigger_count += 1


class FaultInjector:
    """
    Injects faults at specific STAR phases for robustness testing.

    Usage:
        injector = FaultInjector()
        injector.add_fault(FaultConfig(
            phase="think",
            fault_type="exception",
            probability=0.5,
            message="Random think failure"
        ))

        # In HarnessAgent
        def _think(self, trace):
            self.fault_injector.inject("think", trace)
            return super()._think(trace)
    """

    def __init__(self, configs: list[FaultConfig] | None = None):
        self.configs: list[FaultConfig] = configs or []
        self.fault_history: list[dict[str, Any]] = []
        self._enabled = True

    def add_fault(self, config: FaultConfig) -> None:
        """Add a fault configuration."""
        self.configs.append(config)

    def add_faults(self, configs: list[FaultConfig]) -> None:
        """Add multiple fault configurations."""
        self.configs.extend(configs)

    def clear_faults(self) -> None:
        """Clear all fault configurations."""
        self.configs.clear()

    def clear_history(self) -> None:
        """Clear fault history."""
        self.fault_history.clear()

    def enable(self) -> None:
        """Enable fault injection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable fault injection."""
        self._enabled = False

    def get_faults_for_phase(self, phase: str) -> list[FaultConfig]:
        """Get all fault configs for a specific phase."""
        return [c for c in self.configs if c.phase == phase]

    def should_fault(self, phase: str, context: dict | None = None) -> FaultConfig | None:
        """Check if a fault should be injected for this phase."""
        if not self._enabled:
            return None

        for config in self.get_faults_for_phase(phase):
            if config.should_trigger(context):
                return config
        return None

    def inject(self, phase: str, context: dict | None = None) -> None:
        """
        Inject a fault for the given phase.

        Raises:
            Exception: If fault_type is "exception"
            TimeoutError: If fault_type is "timeout"
        """
        fault = self.should_fault(phase, context)
        if fault is None:
            return

        # Record the fault
        fault.trigger()
        self.fault_history.append({
            "phase": phase,
            "fault_type": fault.fault_type,
            "timestamp": time.time(),
            "context_keys": list(context.keys()) if context else [],
        })

        # Execute the fault
        if fault.fault_type == "exception":
            raise fault.exception_type(fault.message)

        elif fault.fault_type == "timeout":
            raise TimeoutError(fault.message)

        elif fault.fault_type == "delay":
            time.sleep(fault.delay_ms / 1000)

        elif fault.fault_type == "hang":
            # Simulate a hang by sleeping for a very long time
            # In practice, tests should use timeouts
            time.sleep(fault.delay_ms / 1000 if fault.delay_ms > 0 else 60)

        # "empty" and "malformed" are handled at the mock LLM level, not here

    def wrap_method(self, method: Callable, phase: str) -> Callable:
        """
        Wrap a method to inject faults before execution.

        Usage:
            agent._see = injector.wrap_method(agent._see, "see")
        """
        def wrapped(*args, **kwargs):
            # Extract context from first positional arg if it's a dict
            context = args[0] if args and isinstance(args[0], dict) else None
            self.inject(phase, context)
            return method(*args, **kwargs)
        return wrapped

    def wrap_async_method(self, method: Callable, phase: str) -> Callable:
        """
        Wrap an async method to inject faults before execution.
        """
        async def wrapped(*args, **kwargs):
            context = args[0] if args and isinstance(args[0], dict) else None
            self.inject(phase, context)
            return await method(*args, **kwargs)
        return wrapped


# ==================== Preset Fault Scenarios ====================

class FaultScenarios:
    """Preset fault injection scenarios for common test cases."""

    @staticmethod
    def think_phase_exception() -> FaultConfig:
        """Exception during _think phase."""
        return FaultConfig(
            phase="think",
            fault_type="exception",
            exception_type=RuntimeError,
            message="Think phase failure",
        )

    @staticmethod
    def act_phase_exception() -> FaultConfig:
        """Exception during _act phase."""
        return FaultConfig(
            phase="act",
            fault_type="exception",
            exception_type=RuntimeError,
            message="Act phase failure",
        )

    @staticmethod
    def reflect_phase_exception() -> FaultConfig:
        """Exception during _reflect phase."""
        return FaultConfig(
            phase="reflect",
            fault_type="exception",
            exception_type=RuntimeError,
            message="Reflect phase failure",
        )

    @staticmethod
    def intermittent_think_failure(probability: float = 0.3) -> FaultConfig:
        """Intermittent failures in _think phase."""
        return FaultConfig(
            phase="think",
            fault_type="exception",
            probability=probability,
            message="Intermittent think failure",
        )

    @staticmethod
    def slow_think(delay_ms: int = 2000) -> FaultConfig:
        """Slow _think phase to test timeout handling."""
        return FaultConfig(
            phase="think",
            fault_type="delay",
            delay_ms=delay_ms,
        )

    @staticmethod
    def slow_act(delay_ms: int = 2000) -> FaultConfig:
        """Slow _act phase to test timeout handling."""
        return FaultConfig(
            phase="act",
            fault_type="delay",
            delay_ms=delay_ms,
        )

    @staticmethod
    def first_think_fails() -> FaultConfig:
        """First _think call fails, subsequent succeed."""
        return FaultConfig(
            phase="think",
            fault_type="exception",
            message="First think failure",
            max_triggers=1,
        )

    @staticmethod
    def all_phases_monitored() -> list[FaultConfig]:
        """
        Monitor all phases without causing failures.

        Useful for tracking phase execution order and timing.
        """
        return [
            FaultConfig(phase="see", fault_type="delay", delay_ms=0),
            FaultConfig(phase="think", fault_type="delay", delay_ms=0),
            FaultConfig(phase="act", fault_type="delay", delay_ms=0),
            FaultConfig(phase="reflect", fault_type="delay", delay_ms=0),
        ]

    @staticmethod
    def cascade_failure_on_iteration(iteration: int) -> list[FaultConfig]:
        """
        Cause a failure on a specific iteration.

        Useful for testing MAX_ITERATIONS handling.
        """
        call_count = {"see": 0}

        def on_nth_iteration(context: dict) -> bool:
            call_count["see"] += 1
            return call_count["see"] == iteration

        return [
            FaultConfig(
                phase="think",
                fault_type="exception",
                message=f"Failure on iteration {iteration}",
                condition=on_nth_iteration,
            )
        ]
