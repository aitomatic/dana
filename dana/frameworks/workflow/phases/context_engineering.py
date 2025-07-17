"""
Phase 3: Context Engineering

This module implements advanced context management and KNOWS integration
for the Dana workflow system.

Key Features:
- KNOWS knowledge extraction system integration
- Advanced knowledge curation patterns
- Context-aware step execution
- Context snapshots and versioning
- Knowledge traceability and provenance
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from dana.frameworks.workflow.core.context.context_engine import ContextEngine
from dana.frameworks.workflow.core.steps.workflow_step import WorkflowStep
from dana.frameworks.workflow.core.engine.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeTrace:
    """Trace information for knowledge provenance."""
    step_id: str
    workflow_id: str
    timestamp: datetime
    source: str
    transformation: str
    input_context: Dict[str, Any]
    output_context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextSnapshot:
    """Snapshot of context state at a point in time."""
    snapshot_id: str
    timestamp: datetime
    knowledge_points: List[Dict[str, Any]]
    context_metadata: Dict[str, Any]
    workflow_state: Dict[str, Any]


class KNOWSExtractor:
    """KNOWS knowledge extraction system integration."""
    
    def __init__(self, context_engine: ContextEngine):
        self.context_engine = context_engine
        logger.info("Initialized KNOWS knowledge extractor")
    
    def extract_from_step(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract knowledge from a workflow step execution."""
        knowledge_points = []
        
        # Extract step metadata as knowledge
        if step.metadata:
            knowledge_points.append({
                "content": f"Step {step.name} metadata: {json.dumps(step.metadata)}",
                "source": f"workflow_step_{step.name}",
                "tags": ["step_metadata", "workflow", step.name],
                "metadata": {
                    "step_name": step.name,
                    "execution_context": execution_context,
                    "extraction_method": "step_metadata"
                }
            })
        
        # Extract function signature information
        if step.function:
            import inspect
            try:
                sig = inspect.signature(step.function)
                knowledge_points.append({
                    "content": f"Function signature: {sig}",
                    "source": f"function_{step.name}",
                    "tags": ["function_signature", step.name],
                    "metadata": {
                        "parameters": list(sig.parameters.keys()),
                        "extraction_method": "function_signature"
                    }
                })
            except Exception:
                pass
        
        return knowledge_points
    
    def extract_from_result(self, step: WorkflowStep, result: Any, execution_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract knowledge from step execution results."""
        knowledge_points = []
        
        # Extract result information
        result_type = type(result).__name__
        knowledge_points.append({
            "content": f"Step {step.name} result: {result} (type: {result_type})",
            "source": f"step_result_{step.name}",
            "tags": ["step_result", step.name, result_type],
            "metadata": {
                "step_name": step.name,
                "result_type": result_type,
                "execution_context": execution_context,
                "extraction_method": "step_result"
            }
        })
        
        return knowledge_points
    
    def extract_from_error(self, step: WorkflowStep, error: Exception, execution_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract knowledge from step execution errors."""
        return [{
            "content": f"Step {step.name} error: {str(error)} (type: {type(error).__name__})",
            "source": f"step_error_{step.name}",
            "tags": ["step_error", step.name, type(error).__name__],
            "metadata": {
                "step_name": step.name,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "execution_context": execution_context,
                "extraction_method": "step_error"
            }
        }]


class ContextEngineeringEngine:
    """Advanced context management and KNOWS integration engine."""
    
    def __init__(self, context_engine: Optional[ContextEngine] = None):
        self.context_engine = context_engine or ContextEngine()
        self.knows_extractor = KNOWSExtractor(self.context_engine)
        self.knowledge_traces: List[KnowledgeTrace] = []
        self.context_snapshots: Dict[str, ContextSnapshot] = {}
        logger.info("Initialized ContextEngineeringEngine")
    
    def execute_with_context(self, workflow_engine: WorkflowEngine, steps: List[WorkflowStep], 
                           initial_input: Any, workflow_id: str = None) -> Any:
        """Execute workflow with advanced context management."""
        workflow_id = workflow_id or f"workflow_{datetime.now().isoformat()}"
        
        # Create initial context snapshot
        initial_snapshot = self.create_context_snapshot(workflow_id, "initial")
        
        try:
            # Enhance steps with context awareness
            enhanced_steps = [self.enhance_step_with_context(step) for step in steps]
            
            # Execute workflow with context injection
            result = self._execute_with_context_injection(
                workflow_engine, enhanced_steps, initial_input, workflow_id
            )
            
            # Create final context snapshot
            final_snapshot = self.create_context_snapshot(workflow_id, "final")
            
            return result
            
        except Exception as e:
            # Extract error knowledge
            error_knowledge = self.knows_extractor.extract_from_error(
                WorkflowStep(name="workflow_error", function=None), e,
                {"workflow_id": workflow_id, "stage": "execution"}
            )
            for kp in error_knowledge:
                self.context_engine.add_knowledge(**kp)
            raise
    
    def enhance_step_with_context(self, step: WorkflowStep) -> WorkflowStep:
        """Enhance a workflow step with context awareness."""
        import functools
        
        def context_aware_wrapper(original_func):
            @functools.wraps(original_func)
            def wrapper(input_data, context=None):
                # Extract knowledge before execution
                pre_knowledge = self.knows_extractor.extract_from_step(
                    step, {"stage": "pre_execution", "input": input_data}
                )
                for kp in pre_knowledge:
                    self.context_engine.add_knowledge(**kp)
                
                # Execute original function
                try:
                    result = original_func(input_data)
                    
                    # Extract knowledge from successful execution
                    result_knowledge = self.knows_extractor.extract_from_result(
                        step, result, {"stage": "post_execution", "input": input_data}
                    )
                    for kp in result_knowledge:
                        self.context_engine.add_knowledge(**kp)
                    
                    # Create knowledge trace
                    trace = KnowledgeTrace(
                        step_id=step.name,
                        workflow_id=context.get("workflow_id", "unknown") if context else "unknown",
                        timestamp=datetime.now(),
                        source="step_execution",
                        transformation=f"{step.name}_execution",
                        input_context={"input": str(input_data)},
                        output_context={"result": str(result)}
                    )
                    self.knowledge_traces.append(trace)
                    
                    return result
                    
                except Exception as e:
                    # Extract knowledge from error
                    error_knowledge = self.knows_extractor.extract_from_error(
                        step, e, {"stage": "error", "input": input_data}
                    )
                    for kp in error_knowledge:
                        self.context_engine.add_knowledge(**kp)
                    raise
                    
            return wrapper
        
        # Create enhanced step
        enhanced_function = context_aware_wrapper(step.function)
        enhanced_metadata = dict(step.metadata)
        enhanced_metadata.update({
            "context_aware": True,
            "knows_integration": True,
            "original_step": step.name
        })
        
        return WorkflowStep(
            name=f"{step.name}_context_aware",
            function=enhanced_function,
            pre_conditions=step.pre_conditions,
            post_conditions=step.post_conditions,
            error_handler=step.error_handler,
            metadata=enhanced_metadata,
            timeout=step.timeout
        )
    
    def create_context_snapshot(self, workflow_id: str, stage: str) -> ContextSnapshot:
        """Create a snapshot of current context state."""
        snapshot_id = f"{workflow_id}_{stage}_{datetime.now().isoformat()}"
        
        # Export knowledge points
        knowledge_points = []
        for kp_id, kp in self.context_engine._knowledge_store.items():
            knowledge_points.append({
                "id": kp_id,
                "content": kp.content,
                "source": kp.source,
                "tags": kp.tags,
                "timestamp": kp.timestamp.isoformat(),
                "metadata": kp.metadata
            })
        
        snapshot = ContextSnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now(),
            knowledge_points=knowledge_points,
            context_metadata={
                "workflow_id": workflow_id,
                "stage": stage,
                "knowledge_count": len(knowledge_points),
                "trace_count": len(self.knowledge_traces)
            },
            workflow_state={
                "total_traces": len(self.knowledge_traces),
                "context_stats": self.context_engine.get_stats()
            }
        )
        
        self.context_snapshots[snapshot_id] = snapshot
        logger.info(f"Created context snapshot: {snapshot_id}")
        return snapshot
    
    def get_knowledge_traces(self, workflow_id: str = None) -> List[KnowledgeTrace]:
        """Get knowledge traces, optionally filtered by workflow."""
        if workflow_id:
            return [trace for trace in self.knowledge_traces if trace.workflow_id == workflow_id]
        return self.knowledge_traces.copy()
    
    def search_context_knowledge(self, query: str, tags: List[str] = None, 
                               source: str = None) -> List[Dict[str, Any]]:
        """Search for knowledge in the context engine."""
        results = self.context_engine.search_knowledge(query)
        
        if tags:
            results = [r for r in results if any(tag in r.tags for tag in tags)]
        
        if source:
            results = [r for r in results if r.source == source]
        
        return [
            {
                "content": r.content,
                "source": r.source,
                "tags": r.tags,
                "timestamp": r.timestamp.isoformat(),
                "metadata": r.metadata
            }
            for r in results
        ]
    
    def export_context_state(self, workflow_id: str) -> Dict[str, Any]:
        """Export complete context state for a workflow."""
        workflow_traces = self.get_knowledge_traces(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "knowledge_traces": [
                {
                    "step_id": trace.step_id,
                    "timestamp": trace.timestamp.isoformat(),
                    "source": trace.source,
                    "transformation": trace.transformation,
                    "input_context": trace.input_context,
                    "output_context": trace.output_context,
                    "metadata": trace.metadata
                }
                for trace in workflow_traces
            ],
            "context_snapshots": [
                {
                    "snapshot_id": snap.snapshot_id,
                    "timestamp": snap.timestamp.isoformat(),
                    "stage": snap.context_metadata.get("stage"),
                    "knowledge_count": snap.context_metadata.get("knowledge_count", 0)
                }
                for snap in self.context_snapshots.values()
                if workflow_id in snap.snapshot_id
            ],
            "context_stats": self.context_engine.get_stats()
        }
    
    def _execute_with_context_injection(self, workflow_engine: WorkflowEngine, 
                                      steps: List[WorkflowStep], initial_input: Any,
                                      workflow_id: str) -> Any:
        """Internal method to execute workflow with context injection."""
        # This is a simplified version - in practice, would integrate more deeply
        return workflow_engine.execute(steps, initial_input, workflow_id=workflow_id)


class ContextAwareWorkflowEngine:
    """High-level interface for context-aware workflow execution."""
    
    def __init__(self, workflow_engine: Optional[WorkflowEngine] = None):
        self.workflow_engine = workflow_engine or WorkflowEngine()
        self.context_engine = ContextEngine()
        self.context_engineering = ContextEngineeringEngine(self.context_engine)
    
    def run(self, steps: List[WorkflowStep], initial_input: Any, 
            workflow_id: str = None) -> Dict[str, Any]:
        """Run workflow with full context engineering support."""
        workflow_id = workflow_id or f"context_workflow_{datetime.now().isoformat()}"
        
        logger.info(f"Starting context-aware workflow: {workflow_id}")
        
        # Execute with context engineering
        result = self.context_engineering.execute_with_context(
            self.workflow_engine, steps, initial_input, workflow_id
        )
        
        # Export final state
        final_state = self.context_engineering.export_context_state(workflow_id)
        
        return {
            "result": result,
            "workflow_id": workflow_id,
            "context_state": final_state,
            "knowledge_traces": len(self.context_engineering.get_knowledge_traces(workflow_id)),
            "context_snapshots": len([
                s for s in self.context_engineering.context_snapshots.values()
                if workflow_id in s.snapshot_id
            ])
        }