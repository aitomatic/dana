"""
Clean BaseSTARAgent implementation with minimal STAR pattern contract.

This module provides the core STAR (See-Think-Act-Reflect) pattern contract
without implementation details like LLM integration or rich state management.
"""

from abc import abstractmethod
import asyncio
from collections.abc import AsyncIterator
import logging
import threading

from dana.common.observable import observable
from dana.common.protocols import DictParams, STARAgentProtococol
from dana.common.protocols.types import LearningPhase
from dana.core.agent.base_agent import BaseAgent
from dana.core.runtime.protocols import StreamEvent, StreamEventType


logger = logging.getLogger(__name__)


EXIT_STAR_LOOP_FLAG = "EXIT_STAR_LOOP_FLAG"


class BaseSTARAgent(BaseAgent, STARAgentProtococol):
    """
    Minimal base class defining the STAR (See-Think-Act-Reflect) pattern contract.

    Provides core STAR pattern orchestration and basic agent identity without
    implementation details like LLM integration or rich state management.

    The STAR loop executes: SEE -> THINK -> ACT -> REFLECT

    See docs/architecture/star-pattern-schema.md for the historical XML prompt schema.
    """

    MAX_ITERATIONS = 20

    # ============================================================================
    # CORE STAR PATTERN CONTRACT (Abstract Methods)
    # ============================================================================

    @abstractmethod
    def _see(self, trace_inputs: DictParams) -> DictParams:
        """
        SEE: See the inputs and produce percepts.

        Args:
            trace_inputs (DictParams): any new user/agent inputs

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_percepts (DictParams): the percepts produced by this SEE phase.
        """
        result = {"trace_percepts": trace_inputs}
        self.broadcast(result)
        return result

    @abstractmethod
    def _think(self, trace_percepts: DictParams) -> DictParams:
        """
        THINK: Think about the percepts and produce thoughts.

        Args:
            trace_percepts (DictParams): the percepts produced by this SEE phase.

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_thoughts (DictParams): the thoughts produced by this THINK phase.
        """
        result = {"trace_thoughts": trace_percepts}
        self.broadcast(result)
        return result

    @abstractmethod
    def _act(self, trace_thoughts: DictParams) -> DictParams:
        """
        ACT: Act on the thoughts and produce outputs.

        TODO: this is a good place to send feedback to the user if we are about to make tool calls

        Args:
            trace_thoughts (DictParams): the thoughts produced by this THINK phase.

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_outputs (DictParams): the outputs produced by this ACT phase.
        """
        result = {"trace_outputs": trace_thoughts}
        self.broadcast(result)
        return result

    @abstractmethod
    def _reflect(self, trace_outputs: DictParams) -> DictParams:
        """
        REFLECT: Reflect on the outputs for learning.

        Args:
            trace_outputs (DictParams): the outputs produced by this ACT phase.

        Returns:
            - bool: True if the agent should continue the loop, False otherwise.
            - trace_learning (DictParams): the learning produced by this REFLECT phase.
        """
        result = {"trace_learning": trace_outputs}
        self.broadcast(result)
        return result

    # ============================================================================
    # ASYNC STAR METHODS
    # ============================================================================

    @abstractmethod
    async def _think_async(self, trace_percepts: DictParams) -> DictParams:
        """
        THINK (async): Async version of _think with native async LLM calls.

        Args:
            trace_percepts (DictParams): the percepts produced by this SEE phase.

        Returns:
            - trace_thoughts (DictParams): the thoughts produced by this THINK phase.
        """
        result = {"trace_thoughts": trace_percepts}
        self.broadcast(result)
        return result

    @abstractmethod
    async def _act_async(self, trace_thoughts: DictParams) -> DictParams:
        """
        ACT (async): Async version of _act with native async tool execution.

        Args:
            trace_thoughts (DictParams): the thoughts produced by this THINK phase.

        Returns:
            - trace_outputs (DictParams): the outputs produced by this ACT phase.
        """
        result = {"trace_outputs": trace_thoughts}
        self.broadcast(result)
        return result

    # ============================================================================
    # EXIT STAR LOOP FLAG
    # ============================================================================

    def _mark_star_loop_exit(self, trace: DictParams | None = None) -> DictParams:
        if not trace:
            trace = {}

        trace[EXIT_STAR_LOOP_FLAG] = True
        return trace

    def _do_exit_star_loop(self, trace: DictParams) -> bool:
        return trace.get(EXIT_STAR_LOOP_FLAG, False) if trace else True

    # ============================================================================
    # STAR LOOP ORCHESTRATION
    # ============================================================================

    def query(self, **kwargs) -> DictParams:
        """Main entry point - orchestrates the STAR loop.

        Args:
            **kwargs: Additional arguments passed to STAR loop.
        """

        @observable(name=f"Dana {self.agent_type}-agent-query")
        def _do_query(trace_inputs: DictParams) -> DictParams:
            trace_outputs: DictParams = {}

            for _ in range(self.MAX_ITERATIONS):
                try:
                    trace_percepts = self._see(trace_inputs.get("trace_inputs", {}))
                    trace_thoughts = self._think(trace_percepts.get("trace_percepts", {}))
                    trace_outputs = self._act(trace_thoughts.get("trace_thoughts", {}))

                    # Trigger acquisitive learning asynchronously at end of each STAR loop
                    if not self._do_exit_star_loop(trace_outputs.get("trace_outputs", {})):
                        acquisitive_input = trace_outputs.get("trace_outputs", {}).copy()
                        acquisitive_input["phase"] = LearningPhase.ACQUISITIVE

                        # Sync path: use thread (no event loop available)
                        def run_reflect(acq_input):
                            try:
                                self._reflect(acq_input)
                            except Exception as reflect_err:
                                logger.error("Reflection failed: %s", reflect_err, exc_info=True)

                        threading.Thread(target=run_reflect, args=(acquisitive_input,), daemon=True).start()

                    if self._do_exit_star_loop(trace_outputs.get("trace_outputs", {})):
                        break

                except Exception as e:
                    import traceback

                    logger.error("Error in query: %s\n%s", e, traceback.format_exc())
                    trace_outputs = {"trace_outputs": {"error": e}}
                    break

            # _trace_episode["phase"] = LearningPhase.EPISODIC
            # trace_learning = self._reflect(trace_outputs)

            return trace_outputs

        try:
            result = _do_query(trace_inputs={"trace_inputs": kwargs})
            result = result.get("trace_outputs", {}) if result else {}

        except Exception as e:
            logger.error("Error in query: %s", e)
            result = {"error": e}

        return result

    async def aquery(self, **kwargs) -> DictParams:
        """Async version of query that uses async STAR methods.

        Args:
            **kwargs: Additional arguments passed to STAR loop.
        """

        @observable(name=f"Dana {self.agent_type}-agent-aquery")
        async def _do_aquery(trace_inputs: DictParams) -> DictParams:
            trace_outputs: DictParams = {}

            for _ in range(self.MAX_ITERATIONS):
                try:
                    # _see is sync (no async ops needed)
                    trace_percepts = self._see(trace_inputs.get("trace_inputs", {}))
                    # _think_async uses native async LLM call
                    trace_thoughts = await self._think_async(trace_percepts.get("trace_percepts", {}))
                    # _act_async uses native async tool execution
                    trace_outputs = await self._act_async(trace_thoughts.get("trace_thoughts", {}))

                    # Trigger acquisitive learning asynchronously at end of each STAR loop
                    if not self._do_exit_star_loop(trace_outputs.get("trace_outputs", {})):
                        acquisitive_input = trace_outputs.get("trace_outputs", {}).copy()
                        acquisitive_input["phase"] = LearningPhase.ACQUISITIVE

                        # Async path: use asyncio.create_task (proper async, not threads)
                        async def _async_reflect(acq_input):
                            try:
                                self._reflect(acq_input)
                            except Exception as reflect_err:
                                logger.error("Async reflection failed", error=str(reflect_err), exc_info=True)

                        asyncio.create_task(_async_reflect(acquisitive_input))

                    if self._do_exit_star_loop(trace_outputs.get("trace_outputs", {})):
                        break

                except Exception as e:
                    logger.error("Error in aquery: %s", e)
                    trace_outputs = {"trace_outputs": {"error": e}}
                    break

            return trace_outputs

        try:
            result = await _do_aquery(trace_inputs={"trace_inputs": kwargs})
            result = result.get("trace_outputs", {}) if result else {}

        except Exception as e:
            logger.error("Error in aquery: %s", e)
            result = {"error": e}

        return result

    async def aquery_stream(self, **kwargs) -> AsyncIterator[StreamEvent]:
        """Streaming version of aquery. Yields StreamEvent objects.

        Subclasses override _think_stream() to stream text deltas during the
        think phase. The default implementation falls back to aquery() and
        emits a single DONE event — subclasses provide richer streaming.

        Yields:
            StreamEvent: Events with types TEXT_DELTA, TOOL_CALL_START,
                         TOOL_RESULT, ERROR, or DONE.
        """
        # Default: no streaming support — subclasses override
        try:
            result = await self.aquery(**kwargs)
            response = result.get("response", "") if result else ""
            if response:
                yield StreamEvent(
                    event_type=StreamEventType.TEXT_DELTA,
                    data=response,
                    iteration=0,
                )
        except Exception as exc:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data=str(exc),
                iteration=0,
            )
            return
        yield StreamEvent(event_type=StreamEventType.DONE, data=None, iteration=0)

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"BaseSTARAgent(type={self.agent_type}, id={self.object_id})"

    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"BaseSTARAgent(agent_type='{self.agent_type}', object_id='{self.object_id}')"
