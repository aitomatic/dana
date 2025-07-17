"""
Phase 2: POET Integration Module

This module integrates the POET framework with the Dana workflow system to provide:
1. Runtime objective inference
2. Dynamic validation gates
3. POET-powered step enhancement
4. Context-aware operation execution

Phase 2 focuses on connecting the existing workflow engine with POET's Operate phase
for enhanced runtime behavior and validation.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from dana.frameworks.workflow.core import WorkflowEngine, WorkflowStep, ContextEngine, SafetyValidator
from dana.frameworks.poet.phases.operate import OperatePhase
from dana.frameworks.poet.core.types import POETConfig

logger = logging.getLogger(__name__)


@dataclass
class POETObjective:
    """Represents a runtime objective inferred by POET."""
    name: str
    description: str
    criteria: Dict[str, Any]
    priority: int = 1
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class POETRuntimeEngine:
    """Integrates POET framework with Dana workflows for runtime enhancement."""
    
    def __init__(
        self,
        poet_config: Optional[POETConfig] = None,
        context_engine: Optional[ContextEngine] = None,
        safety_validator: Optional[SafetyValidator] = None
    ):
        self.config = poet_config or POETConfig()
        self.context_engine = context_engine or ContextEngine()
        self.safety_validator = safety_validator or SafetyValidator()
        self.operate_phase = OperatePhase(self.config)
        self._objectives: List[POETObjective] = []
        
    def add_objective(self, objective: POETObjective) -> None:
        """Add a runtime objective for POET to consider."""
        self._objectives.append(objective)
        logger.info(f"Added POET objective: {objective.name}")
        
    def infer_objectives(self, workflow_steps: List[WorkflowStep], context: Dict[str, Any]) -> List[POETObjective]:
        """Infer runtime objectives based on workflow and context."""
        inferred = []
        
        # Analyze workflow complexity
        complexity_score = len(workflow_steps)
        if complexity_score > 10:
            inferred.append(POETObjective(
                name="optimize_performance",
                description="Workflow complexity suggests performance optimization needed",
                criteria={"max_steps": 5, "timeout": 30},
                priority=2
            ))
            
        # Analyze data sensitivity
        sensitive_keywords = ["password", "secret", "private", "confidential"]
        for step in workflow_steps:
            if any(keyword in str(step.name).lower() for keyword in sensitive_keywords):
                inferred.append(POETObjective(
                    name="enhance_security",
                    description="Sensitive data detected - security validation required",
                    criteria={"validation_level": "strict", "encryption": True},
                    priority=3
                ))
                break
                
        # Analyze context for business objectives
        if "business_critical" in str(context).lower():
            inferred.append(POETObjective(
                name="ensure_reliability",
                description="Business critical workflow - reliability validation required",
                criteria={"retry_count": 3, "fallback_enabled": True},
                priority=1
            ))
            
        return inferred
        
    def create_validation_gate(self, objective: POETObjective) -> Callable:
        """Create a validation gate based on a POET objective."""
        def gate_function(step: WorkflowStep, context: Dict[str, Any]) -> bool:
            criteria = objective.criteria
            
            # Performance gate
            if objective.name == "optimize_performance" and "timeout" in criteria:
                timeout = getattr(step, 'timeout', None)
                if timeout is not None and timeout > criteria["timeout"]:
                    logger.warning(f"Step {step.name} exceeds timeout criteria")
                    return False
                    
            # Security gate
            if objective.name == "enhance_security" and "validation_level" in criteria:
                validation_result = self.safety_validator.validate_step(step)
                if criteria["validation_level"] == "strict" and not validation_result.is_safe:
                    logger.error(f"Step {step.name} failed security validation")
                    return False
                    
            return True
            
        return gate_function
        
    def enhance_step_with_objective(self, step: WorkflowStep, objective: POETObjective) -> WorkflowStep:
        """Enhance a workflow step based on POET objectives."""
        # Create enhanced step with updated configuration
        enhanced_metadata = step.metadata.copy() if hasattr(step, 'metadata') else {}
        
        # Apply objective criteria to metadata
        if objective.name == "ensure_reliability" and "retry_count" in objective.criteria:
            enhanced_metadata["retry_count"] = objective.criteria["retry_count"]
            
        if objective.name == "optimize_performance" and "timeout" in objective.criteria:
            enhanced_metadata["timeout"] = objective.criteria["timeout"]
            
        # Create enhanced step
        enhanced_step = WorkflowStep(
            name=f"{step.name}_enhanced",
            function=step.function,
            error_handler=getattr(step, 'error_handler', None),
            timeout=getattr(step, 'timeout', None),
            metadata=enhanced_metadata
        )
        
        return enhanced_step
        
    def execute_with_poet(self, steps: List[WorkflowStep], input_data: Any, context: Dict[str, Any] = None) -> Any:
        """Execute workflow with POET runtime objectives and validation."""
        context = context or {}
        
        # Infer objectives
        objectives = self.infer_objectives(steps, context)
        objectives.extend(self._objectives)
        
        logger.info(f"Executing with {len(objectives)} POET objectives")
        
        # Apply objectives to steps
        enhanced_steps = []
        for step in steps:
            enhanced_step = step
            for objective in objectives:
                if self.create_validation_gate(objective)(step, context):
                    enhanced_step = self.enhance_step_with_objective(enhanced_step, objective)
            enhanced_steps.append(enhanced_step)
            
        # Create enhanced workflow engine
        engine = WorkflowEngine(
            context_engine=self.context_engine,
            safety_validator=self.safety_validator
        )
        
        # Execute with POET operate phase
        def execute_workflow(steps_list, data):
            return engine.execute(steps_list, data, metadata=context)
            
        return self.operate_phase.operate(
            func=execute_workflow,
            args=(enhanced_steps, input_data),
            kwargs={},
            context=context
        )


class POETWorkflowEngine:
    """High-level POET-powered workflow engine."""
    
    def __init__(self, poet_config: Optional[POETConfig] = None):
        self.runtime_engine = POETRuntimeEngine(poet_config)
        
    def add_objective(self, name: str, description: str, criteria: Dict[str, Any], priority: int = 1):
        """Add a POET objective for runtime optimization."""
        objective = POETObjective(
            name=name,
            description=description,
            criteria=criteria,
            priority=priority
        )
        self.runtime_engine.add_objective(objective)
        
    def run(self, steps: List[WorkflowStep], input_data: Any, context: Dict[str, Any] = None) -> Any:
        """Run workflow with POET runtime enhancement."""
        return self.runtime_engine.execute_with_poet(steps, input_data, context)