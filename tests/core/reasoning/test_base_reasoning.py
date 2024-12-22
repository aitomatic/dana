"""Tests for BaseReasoning implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from dxa.core.reasoning.base_reasoner import BaseReasoner
from dxa.core.reasoning.types import Objective, Plan, Signal, SignalType

class SimpleReasoning(BaseReasoner):
    """Simple reasoning implementation for testing."""
    
    async def _create_objective(self, task: Any) -> Objective:
        return Objective(
            original=str(task),
            current=str(task)
        )
        
    async def _create_plan(self, objective: Objective) -> Plan:
        return Plan(
            steps=[{"action": "solve", "input": objective.current}],
            rationale="Simple test plan"
        )
        
    async def _execute_step(self, step: Any, context: Any) -> Dict[str, Any]:
        return {
            "output": f"Executed {step['action']} with {step['input']}",
            "confidence": 1.0
        }

@pytest.fixture
def reasoning():
    """Create test reasoning instance."""
    return SimpleReasoning(config={
        "max_iterations": 3,
        "confidence_threshold": 0.5
    })

@pytest.mark.asyncio
async def test_basic_execution(reasoning):
    """Test basic reasoning execution."""
    result = await reasoning.reason_about("test task", {})
    assert result.success
    assert "Executed solve with test task" in result.output
    assert result.confidence >= 0.5

@pytest.mark.asyncio
async def test_objective_review(reasoning):
    """Test objective review and update."""
    reasoning._review_objective = AsyncMock(return_value=ReviewResult(
        needs_update=True,
        updated_item=Objective(
            original="test",
            current="refined test"
        ),
        rationale="Test refinement"
    ))
    
    result = await reasoning.reason_about("test", {})
    assert any(
        s.type == SignalType.OBJECTIVE 
        for s in result.signals
    )

@pytest.mark.asyncio
async def test_resource_check(reasoning):
    """Test resource health check."""
    reasoning._state.resources = {
        "test": {"health": 0.1}  # Unhealthy resource
    }
    
    result = await reasoning.reason_about("test", {})
    assert not result.success
    assert "Insufficient resources" in result.output["error"]

@pytest.mark.asyncio
async def test_max_iterations(reasoning):
    """Test max iterations limit."""
    # Force non-completion
    reasoning._evaluate_progress = AsyncMock(return_value=ProgressEvaluation(
        is_complete=False,
        iterations=0
    ))
    
    result = await reasoning.reason_about("test", {})
    assert not result.success
    assert "Max iterations exceeded" in result.output["error"]

@pytest.mark.asyncio
async def test_replanning(reasoning):
    """Test plan updates."""
    reasoning._review_plan = AsyncMock(return_value=ReviewResult(
        needs_update=True,
        updated_item=Plan(
            steps=[{"action": "new_step"}],
            rationale="Updated plan"
        ),
        rationale="Test update"
    ))
    
    result = await reasoning.reason_about("test", {})
    assert any(
        s.type == SignalType.PROGRESS and s.content["action"] == "plan_updated"
        for s in result.signals
    )