"""
Prompt Optimization Domain Template

Implements Use Case C: Prompt optimization based on results/feedback (POET)
Extends LLM optimization with learning capabilities for prompt improvement.

Features:
- Prompt effectiveness tracking and history
- A/B testing for prompt variants
- Learning from user feedback to improve prompts
- Automatic prompt refinement based on success metrics
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

    def _generate_perceive(self, func_info: FunctionInfo) -> CodeBlock:
        """Enhanced perceive phase with prompt history tracking"""
        # Get base LLM perceive logic
        base_perceive = super()._generate_perceive(func_info)

        # Add prompt optimization specific logic
        enhanced_perceive = f"""
{base_perceive.code}

# === Prompt History & Optimization ===
from dana.frameworks.poet.storage import POETStorage

# Load prompt history and performance metrics
poet_storage = POETStorage()
prompt_history = []

try:
    # Get historical prompt performance for this function
    function_key = f"{{func_info.name}}_prompt_history"
    if poet_storage.exists(function_key):
        history_data = poet_storage.load_training_data(function_key)
        prompt_history = history_data.get("prompt_variants", [])
        
        # Sort by effectiveness score
        prompt_history.sort(key=lambda x: x.get("effectiveness_score", 0), reverse=True)
        
        log(f"Loaded {{len(prompt_history)}} historical prompt variants")
except Exception as e:
    log(f"Could not load prompt history: {{e}}")

# === Prompt Variant Generation ===
prompt_variants = []

# Always include the original prompt
prompt_variants.append({{
    "variant_id": "original",
    "prompt": optimized_prompt,
    "modifications": []
}})

# Generate variants based on historical performance
if prompt_history and len(prompt_history) > 0:
    # Use best performing historical prompt as a variant
    best_historical = prompt_history[0]
    if best_historical.get("prompt") != optimized_prompt:
        prompt_variants.append({{
            "variant_id": "best_historical",
            "prompt": best_historical["prompt"],
            "modifications": ["historical_best"],
            "historical_score": best_historical.get("effectiveness_score", 0)
        }})

# Generate new variants using simple strategies
# Variant 1: Add clarity instruction
clarity_prompt = optimized_prompt + "\\n\\nPlease provide a clear, well-structured response."
prompt_variants.append({{
    "variant_id": "clarity_enhanced",
    "prompt": clarity_prompt,
    "modifications": ["clarity_instruction"]
}})

# Variant 2: Add conciseness instruction
if len(optimized_prompt) > 50:
    concise_prompt = optimized_prompt + "\\n\\nPlease be concise and to the point."
    prompt_variants.append({{
        "variant_id": "concise_enhanced", 
        "prompt": concise_prompt,
        "modifications": ["conciseness_instruction"]
    }})

# Select variant for this execution (simple rotation for A/B testing)
import time
variant_index = int(time.time()) % len(prompt_variants)
selected_variant = prompt_variants[variant_index]

log(f"Selected prompt variant: {{selected_variant['variant_id']}}")

# Update validated inputs with variant info
validated_inputs["prompt_variants"] = prompt_variants
validated_inputs["selected_variant"] = selected_variant
validated_inputs["optimized_prompt"] = selected_variant["prompt"]
validated_inputs["prompt_history"] = prompt_history[:5]  # Keep top 5
""".strip()

        return CodeBlock(
            code=enhanced_perceive,
            dependencies=base_perceive.dependencies + ["dana.poet.storage", "time"],
            imports=base_perceive.imports + ["from dana.frameworks.poet.storage import POETStorage", "import time"],
            metadata={**base_perceive.metadata, "prompt_variants": True, "historical_learning": True, "ab_testing": True},
        )

    def _generate_operate(self, func_info: FunctionInfo) -> CodeBlock:
        """Enhanced operate phase with variant tracking"""
        # Get base LLM operate logic
        base_operate = super()._generate_operate(func_info)

        # Add variant tracking
        enhanced_operate = f"""
{base_operate.code}

# === Track Variant Performance ===
execution_metadata["prompt_variant_used"] = validated_inputs["selected_variant"]["variant_id"]
execution_metadata["prompt_modifications"] = validated_inputs["selected_variant"]["modifications"]
execution_metadata["variant_count"] = len(validated_inputs["prompt_variants"])

# Measure response time for this variant
execution_metadata["response_time"] = execution_metadata.get("total_execution_time", 0)
""".strip()

        return CodeBlock(
            code=enhanced_operate,
            dependencies=base_operate.dependencies,
            imports=base_operate.imports,
            metadata={**base_operate.metadata, "variant_tracking": True},
        )

    def _generate_enforce(self, func_info: FunctionInfo) -> CodeBlock:
        """Enhanced enforce phase with effectiveness scoring"""
        # Get base LLM enforce logic
        base_enforce = super()._generate_enforce(func_info)

        # Add effectiveness measurement
        enhanced_enforce = f"""
{base_enforce.code}

# === Prompt Effectiveness Scoring ===
# Calculate effectiveness based on multiple factors
effectiveness_factors = []

# Factor 1: Response quality (from base enforce)
effectiveness_factors.append(quality_score)

# Factor 2: Response time (faster is better)
response_time = execution_metadata.get("response_time", 10.0)
time_score = max(0, 1.0 - (response_time / 30.0))  # Normalize to 0-1
effectiveness_factors.append(time_score * 0.5)  # Weight: 50%

# Factor 3: Token efficiency
tokens_used = execution_metadata.get("total_tokens_used", 1000)
token_score = max(0, 1.0 - (tokens_used / 2000.0))  # Normalize to 0-1
effectiveness_factors.append(token_score * 0.3)  # Weight: 30%

# Factor 4: Response length appropriateness
response_length = len(response_text)
if 50 <= response_length <= 500:
    length_score = 1.0
elif response_length < 50:
    length_score = response_length / 50.0
else:
    length_score = max(0, 1.0 - ((response_length - 500) / 1000.0))
effectiveness_factors.append(length_score * 0.2)  # Weight: 20%

# Calculate overall effectiveness
effectiveness_score = sum(effectiveness_factors) / len(effectiveness_factors)

# Store effectiveness data
validation_metadata["effectiveness_score"] = effectiveness_score
validation_metadata["effectiveness_factors"] = {{
    "quality": quality_score,
    "time": time_score,
    "tokens": token_score,
    "length": length_score
}}
validation_metadata["prompt_variant"] = validated_inputs["selected_variant"]["variant_id"]

log(f"Prompt effectiveness score: {{effectiveness_score:.2f}}")
""".strip()

        return CodeBlock(
            code=enhanced_enforce,
            dependencies=base_enforce.dependencies,
            imports=base_enforce.imports,
            metadata={**base_enforce.metadata, "effectiveness_scoring": True},
        )

    def _generate_train(self, func_info: FunctionInfo) -> CodeBlock | None:
        """Generate comprehensive learning phase for prompt optimization"""

        train_code = """
# === TRAIN PHASE: Prompt Learning ===
from dana.frameworks.poet.feedback import get_feedback_system
from dana.frameworks.poet.storage import POETStorage

if execution_id and final_result:
    try:
        # Record execution for feedback tracking
        feedback_system = get_feedback_system()
        if feedback_system:
            feedback_system.record_execution(
                execution_id=execution_id,
                function_name=func_info.name,
                prompt_used=validated_inputs["selected_variant"]["prompt"],
                result=final_result,
                metadata={
                    "domain": "prompt_optimization",
                    "variant_id": validated_inputs["selected_variant"]["variant_id"],
                    "effectiveness_score": validation_metadata.get("effectiveness_score", 0),
                    "quality_score": validation_metadata.get("quality_score", 0),
                    "tokens_used": execution_metadata.get("total_tokens_used", 0),
                    "response_time": execution_metadata.get("response_time", 0),
                    "prompt_modifications": validated_inputs["selected_variant"]["modifications"]
                }
            )
        
        # Store prompt performance data for learning
        poet_storage = POETStorage()
        function_key = f"{func_info.name}_prompt_history"
        
        # Load existing history
        history_data = {}
        if poet_storage.exists(function_key):
            history_data = poet_storage.load_training_data(function_key)
        
        prompt_variants = history_data.get("prompt_variants", [])
        
        # Add or update this variant's performance
        variant_data = {
            "prompt": validated_inputs["selected_variant"]["prompt"],
            "variant_id": validated_inputs["selected_variant"]["variant_id"],
            "modifications": validated_inputs["selected_variant"]["modifications"],
            "effectiveness_score": validation_metadata.get("effectiveness_score", 0),
            "execution_count": 1,
            "last_execution": execution_id,
            "timestamp": time.time()
        }
        
        # Update existing variant or add new one
        variant_found = False
        for i, variant in enumerate(prompt_variants):
            if variant.get("variant_id") == variant_data["variant_id"]:
                # Update with running average
                old_score = variant.get("effectiveness_score", 0)
                old_count = variant.get("execution_count", 0)
                new_score = variant_data["effectiveness_score"]
                
                # Calculate weighted average
                total_count = old_count + 1
                avg_score = (old_score * old_count + new_score) / total_count
                
                variant["effectiveness_score"] = avg_score
                variant["execution_count"] = total_count
                variant["last_execution"] = execution_id
                variant["timestamp"] = time.time()
                
                variant_found = True
                break
        
        if not variant_found:
            prompt_variants.append(variant_data)
        
        # Keep only top 20 variants
        prompt_variants.sort(key=lambda x: x.get("effectiveness_score", 0), reverse=True)
        prompt_variants = prompt_variants[:20]
        
        # Save updated history
        history_data["prompt_variants"] = prompt_variants
        history_data["last_updated"] = time.time()
        history_data["total_executions"] = history_data.get("total_executions", 0) + 1
        
        poet_storage.save_training_data(function_key, history_data)
        
        log(f"Prompt learning: Recorded performance for variant '{variant_data['variant_id']}' (score: {variant_data['effectiveness_score']:.2f})")
        
        # Adaptive improvement: Generate new variant if current ones aren't performing well
        if all(v.get("effectiveness_score", 0) < 0.7 for v in prompt_variants[:3]):
            log("All prompt variants performing below threshold - consider manual optimization")
            
    except Exception as e:
        log(f"Prompt learning failed: {e}")
""".strip()

        return CodeBlock(
            code=train_code,
            dependencies=["dana.poet.feedback", "dana.poet.storage", "time"],
            imports=[
                "from dana.frameworks.poet.feedback import get_feedback_system",
                "from dana.frameworks.poet.storage import POETStorage",
                "import time",
            ],
            metadata={
                "phase": "train",
                "domain": "prompt_optimization",
                "learning_enabled": True,
                "feedback_tracking": True,
                "adaptive_improvement": True,
                "variant_optimization": True,
            },
        )
