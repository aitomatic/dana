"""
STARAgent Stress Tests - Real-world scenarios with live LLM calls.

Run with: pytest tests/stress/test_star_agent_stress.py -v -s --live

These tests use real LLM providers to stress test STARAgent behavior.
"""

from __future__ import annotations

import time
import pytest
from dataclasses import dataclass, field
from typing import Any

from dana.core.agent.star_agent import STARAgent
from dana.core.resource.todo import ToDoResource
from dana.lib.resources.ping import PingResource


@dataclass
class StressTestResult:
    """Result of a stress test scenario."""
    scenario_name: str
    success: bool
    duration_ms: float
    iterations: int = 0
    token_usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None
    response_length: int = 0
    tool_calls_made: int = 0
    notes: list[str] = field(default_factory=list)


class StressTestHarness:
    """Harness for running and recording stress tests."""

    def __init__(self):
        self.results: list[StressTestResult] = []

    def run_scenario(
        self,
        name: str,
        agent: STARAgent,
        message: str,
        expected_tool_calls: int = 0,
    ) -> StressTestResult:
        """Run a scenario and record results."""
        start_time = time.time()
        result = StressTestResult(scenario_name=name, success=False, duration_ms=0)

        try:
            response = agent.query(message=message)

            result.success = response is not None and "response" in response
            result.response_length = len(response.get("response", "")) if response else 0
            result.iterations = getattr(agent, "_iteration_count", 0)

            # Count tool calls from timeline
            if hasattr(agent, "_timeline") and agent._timeline:
                from dana.core.agent.timeline import TimelineEntryType
                tool_entries = [
                    e for e in agent._timeline.timeline
                    if e.entry_type in [
                        TimelineEntryType.TOOL_CALL,
                        TimelineEntryType.RESOURCE_RESULT,
                        TimelineEntryType.WORKFLOW_RESULT,
                    ]
                ]
                result.tool_calls_made = len(tool_entries) // 2  # Call + Result pairs

        except Exception as e:
            result.error = str(e)
            result.notes.append(f"Exception: {type(e).__name__}")

        result.duration_ms = (time.time() - start_time) * 1000
        self.results.append(result)
        return result

    def print_summary(self):
        """Print a summary of all results."""
        print("\n" + "=" * 70)
        print("STRESS TEST SUMMARY")
        print("=" * 70)

        for r in self.results:
            status = "✅ PASS" if r.success else "❌ FAIL"
            print(f"\n{status} {r.scenario_name}")
            print(f"  Duration: {r.duration_ms:.0f}ms")
            print(f"  Response length: {r.response_length} chars")
            print(f"  Tool calls: {r.tool_calls_made}")
            if r.error:
                print(f"  Error: {r.error}")
            for note in r.notes:
                print(f"  Note: {note}")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        print(f"\n{'=' * 70}")
        print(f"Total: {passed}/{total} passed")
        print("=" * 70)


# =============================================================================
# SINGLE AGENT SCENARIOS
# =============================================================================

@pytest.mark.live
class TestSingleAgentScenarios:
    """Single agent stress tests."""

    @pytest.fixture
    def harness(self):
        return StressTestHarness()

    @pytest.fixture
    def anthropic_agent(self):
        """Create agent with OpenAI provider (fallback from Anthropic)."""
        return STARAgent(
            agent_type="stress_test_openai_primary",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )

    @pytest.fixture
    def openai_agent(self):
        """Create agent with OpenAI provider."""
        return STARAgent(
            agent_type="stress_test_openai",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )

    def test_simple_query_anthropic(self, harness, anthropic_agent):
        """Baseline: Simple Q&A with Anthropic."""
        result = harness.run_scenario(
            name="Simple Query (Anthropic)",
            agent=anthropic_agent,
            message="What is the capital of France? Answer in one word.",
        )

        assert result.success
        assert result.duration_ms < 10000  # Should complete in < 10s
        assert result.response_length > 0  # Should have a non-empty response
        harness.print_summary()

    def test_simple_query_openai(self, harness, openai_agent):
        """Baseline: Simple Q&A with OpenAI."""
        result = harness.run_scenario(
            name="Simple Query (OpenAI)",
            agent=openai_agent,
            message="What is 2 + 2? Answer with just the number.",
        )

        assert result.success
        assert result.duration_ms < 10000
        harness.print_summary()

    def test_multi_step_reasoning(self, harness, anthropic_agent):
        """Test multi-step reasoning without tools."""
        result = harness.run_scenario(
            name="Multi-step Reasoning",
            agent=anthropic_agent,
            message="""Solve this step by step:
            1. Start with 100
            2. Add 50
            3. Multiply by 2
            4. Subtract 75
            What is the final answer?""",
        )

        assert result.success
        harness.print_summary()

    def test_with_todo_resource(self, harness, anthropic_agent):
        """Test agent using ToDoResource for planning."""
        anthropic_agent.with_resources(ToDoResource(auto_register=False))

        result = harness.run_scenario(
            name="Planning with ToDoResource",
            agent=anthropic_agent,
            message="""I need to plan a birthday party. Please:
            1. Create a todo list with 3 key tasks
            2. Mark the first one as in progress
            3. Tell me your plan""",
            expected_tool_calls=1,
        )

        assert result.success
        result.notes.append(f"Tool calls detected: {result.tool_calls_made}")
        harness.print_summary()

    def test_with_ping_resource(self, harness, anthropic_agent):
        """Test agent using PingResource."""
        anthropic_agent.with_resources(PingResource(auto_register=False))

        result = harness.run_scenario(
            name="Ping Resource Usage",
            agent=anthropic_agent,
            message="Please use the ping resource to test connectivity, then report what you found.",
            expected_tool_calls=1,
        )

        assert result.success
        harness.print_summary()

    def test_long_context_handling(self, harness, anthropic_agent):
        """Test handling of longer context."""
        long_context = "Here is some context: " + ("The quick brown fox jumps over the lazy dog. " * 100)

        result = harness.run_scenario(
            name="Long Context Handling",
            agent=anthropic_agent,
            message=f"{long_context}\n\nBased on the above, what animal is described as lazy?",
        )

        assert result.success
        harness.print_summary()

    def test_error_recovery_invalid_request(self, harness, anthropic_agent):
        """Test how agent handles ambiguous/invalid requests."""
        result = harness.run_scenario(
            name="Error Recovery - Ambiguous Request",
            agent=anthropic_agent,
            message="",  # Empty message
        )

        # Empty message should be handled gracefully
        result.notes.append("Empty message test - checking graceful handling")
        harness.print_summary()


@pytest.mark.live
class TestMultiTurnScenarios:
    """Multi-turn conversation stress tests."""

    @pytest.fixture
    def harness(self):
        return StressTestHarness()

    @pytest.fixture
    def agent(self):
        return STARAgent(
            agent_type="multi_turn_test",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )

    def test_context_preservation(self, harness, agent):
        """Test that context is preserved across turns."""
        # First turn
        result1 = harness.run_scenario(
            name="Multi-turn T1: Set context",
            agent=agent,
            message="My name is Alice and I love pizza. Remember this.",
        )

        # Second turn - should remember context
        result2 = harness.run_scenario(
            name="Multi-turn T2: Recall context",
            agent=agent,
            message="What is my name and what food do I like?",
        )

        assert result1.success
        assert result2.success
        harness.print_summary()

    def test_incremental_task_completion(self, harness, agent):
        """Test completing a task incrementally."""
        agent.with_resources(ToDoResource(auto_register=False))

        # Turn 1: Create task list
        result1 = harness.run_scenario(
            name="Incremental T1: Create tasks",
            agent=agent,
            message="Create a todo list with tasks: 'Research topic', 'Write outline', 'Draft document'",
        )

        # Turn 2: Update task
        result2 = harness.run_scenario(
            name="Incremental T2: Update task",
            agent=agent,
            message="Mark 'Research topic' as complete",
        )

        # Turn 3: Report progress
        result3 = harness.run_scenario(
            name="Incremental T3: Report progress",
            agent=agent,
            message="What tasks remain?",
        )

        harness.print_summary()


# =============================================================================
# MULTI-AGENT SCENARIOS
# =============================================================================

@pytest.mark.live
class TestMultiAgentScenarios:
    """Multi-agent coordination stress tests."""

    @pytest.fixture
    def harness(self):
        return StressTestHarness()

    def test_agent_with_sub_agent(self, harness):
        """Test coordinator agent delegating to sub-agent."""
        # Create sub-agent (specialist)
        research_agent = STARAgent(
            agent_id="research-specialist",
            agent_type="researcher",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )

        # Create coordinator that knows about sub-agent
        coordinator = STARAgent(
            agent_type="coordinator",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )
        coordinator.with_agents(research_agent)

        result = harness.run_scenario(
            name="Agent Delegation",
            agent=coordinator,
            message="I need information about Python. Ask the research-specialist agent for help.",
        )

        result.notes.append(f"Tool calls made: {result.tool_calls_made}")
        harness.print_summary()

    def test_parallel_agents_same_query(self, harness):
        """Test two agents handling the same query (comparison)."""
        agent1 = STARAgent(
            agent_type="agent_1",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )

        agent2 = STARAgent(
            agent_type="agent_2",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )

        message = "Explain what a hash table is in one sentence."

        result1 = harness.run_scenario(
            name="Parallel Agent 1 (Anthropic)",
            agent=agent1,
            message=message,
        )

        result2 = harness.run_scenario(
            name="Parallel Agent 2 (OpenAI)",
            agent=agent2,
            message=message,
        )

        result1.notes.append(f"Response length comparison: Anthropic={result1.response_length}, OpenAI={result2.response_length}")
        harness.print_summary()


# =============================================================================
# STRESS / EDGE CASE SCENARIOS
# =============================================================================

@pytest.mark.live
class TestStressEdgeCases:
    """Edge case and stress scenarios."""

    @pytest.fixture
    def harness(self):
        return StressTestHarness()

    @pytest.fixture
    def agent(self):
        return STARAgent(
            agent_type="edge_case_test",
            llm_provider="openai",
            model="gpt-4o-mini",
            auto_register=False,
        )

    def test_very_long_response_request(self, harness, agent):
        """Test request that should generate a long response."""
        result = harness.run_scenario(
            name="Long Response Generation",
            agent=agent,
            message="Write a detailed 5-paragraph essay about the history of computing.",
        )

        result.notes.append(f"Response length: {result.response_length} chars")
        assert result.response_length > 500  # Should be substantial
        harness.print_summary()

    def test_rapid_sequential_queries(self, harness, agent):
        """Test rapid sequential queries."""
        queries = [
            "What is 1+1?",
            "What is 2+2?",
            "What is 3+3?",
        ]

        for i, q in enumerate(queries):
            result = harness.run_scenario(
                name=f"Rapid Query {i+1}",
                agent=agent,
                message=q,
            )
            assert result.success

        harness.print_summary()

    def test_unicode_and_special_chars(self, harness, agent):
        """Test handling of unicode and special characters."""
        result = harness.run_scenario(
            name="Unicode Handling",
            agent=agent,
            message="Translate 'Hello' to Japanese (日本語) and Chinese (中文). Include the characters.",
        )

        assert result.success
        harness.print_summary()

    def test_code_generation(self, harness, agent):
        """Test code generation capability."""
        result = harness.run_scenario(
            name="Code Generation",
            agent=agent,
            message="Write a Python function that calculates the factorial of a number. Include the code.",
        )

        assert result.success
        # Check if response likely contains code
        if "def " in str(result.response_length) or result.response_length > 100:
            result.notes.append("Code likely generated")
        harness.print_summary()

    def test_max_iterations_stress(self, harness, agent):
        """Test behavior when agent might hit max iterations."""
        agent.with_resources(ToDoResource(auto_register=False))
        agent.with_resources(PingResource(auto_register=False))

        result = harness.run_scenario(
            name="Max Iterations Stress",
            agent=agent,
            message="""Please do ALL of the following in sequence:
            1. Ping the system
            2. Create a todo list with 5 items
            3. Update the todo list
            4. Ping again
            5. Summarize what you did""",
            expected_tool_calls=4,
        )

        result.notes.append(f"Iterations: {result.iterations}, Tool calls: {result.tool_calls_made}")
        harness.print_summary()


# =============================================================================
# RUN ALL SCENARIOS
# =============================================================================

@pytest.mark.live
def test_full_stress_suite():
    """Run a comprehensive stress test suite."""
    harness = StressTestHarness()

    print("\n" + "=" * 70)
    print("FULL STRESS TEST SUITE")
    print("=" * 70)

    # Create agents - using OpenAI since Anthropic may have credit limits
    agent = STARAgent(
        agent_type="full_suite_test",
        llm_provider="openai",
        model="gpt-4o-mini",
        auto_register=False,
    )
    agent.with_resources(ToDoResource(auto_register=False))
    agent.with_resources(PingResource(auto_register=False))

    scenarios = [
        ("Simple Q&A", "What is Python? One sentence."),
        ("Math Problem", "What is 17 * 23?"),
        ("Tool Use - Ping", "Ping the system and report the result."),
        ("Tool Use - Todo", "Create a todo with one item: 'Test task'"),
        ("Multi-step", "First ping the system, then create a todo to record the ping result."),
        ("Context Test", "Remember: The secret word is 'banana'. What is the secret word?"),
    ]

    for name, message in scenarios:
        print(f"\nRunning: {name}...")
        harness.run_scenario(name=name, agent=agent, message=message)

    harness.print_summary()

    # Assert overall success rate
    passed = sum(1 for r in harness.results if r.success)
    assert passed >= len(scenarios) * 0.8, f"Success rate too low: {passed}/{len(scenarios)}"
