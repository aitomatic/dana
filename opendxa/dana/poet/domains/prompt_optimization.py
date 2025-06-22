"""
Prompt Optimization Domain Template

Implements Use Case C: Prompt optimization based on results/feedback (POET)
Extends LLM optimization with learning capabilities for prompt improvement.
"""

from .base import CodeBlock, FunctionInfo
from .llm_optimization import LLMOptimizationDomain


class PromptOptimizationDomain(LLMOptimizationDomain):
    """
    Domain template for prompt optimization with learning.

    Extends LLM optimization with:
    - Prompt effectiveness tracking
    - A/B testing for prompt variants
    - Learning from user feedback
    - Automatic prompt improvement
    """

    def _generate_train(self, func_info: FunctionInfo) -> CodeBlock | None:
        """Generate learning phase for prompt optimization"""

        train_code = """
# === TRAIN PHASE: Prompt Learning ===
# Collect feedback for prompt optimization
if execution_id and final_result:
    from opendxa.dana.poet.feedback import get_feedback_system
    
    feedback_system = get_feedback_system()
    if feedback_system:
        # Record execution for potential feedback
        feedback_system.record_execution(
            execution_id=execution_id,
            function_name=func_info.name,
            prompt_used=validated_inputs.get("optimized_prompt"),
            result=final_result,
            metadata={
                "domain": "prompt_optimization",
                "quality_score": validation_metadata.get("quality_score", 0),
                "tokens_used": execution_metadata.get("total_tokens_used", 0),
                "execution_time": execution_metadata.get("total_execution_time", 0)
            }
        )
""".strip()

        return CodeBlock(
            code=train_code,
            dependencies=["opendxa.dana.poet.feedback"],
            imports=["from opendxa.dana.poet.feedback import get_feedback_system"],
            metadata={"phase": "train", "domain": "prompt_optimization", "learning_enabled": True, "feedback_tracking": True},
        )
