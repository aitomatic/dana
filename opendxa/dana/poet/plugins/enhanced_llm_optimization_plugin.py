"""
Enhanced LLM Optimization Plugin for POET with Prompt Learning

This plugin extends the basic LLM optimization plugin to include:
- LLM-powered prompt analysis and optimization
- Contextual prompt improvement based on execution feedback
- Domain-specific prompt templates and patterns
- Iterative prompt refinement through learning

Author: OpenDXA Team
Version: 2.0.0
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.poet.plugins.base import POETPlugin


@dataclass
class PromptAnalysis:
    """Analysis of prompt quality and improvement suggestions."""
    
    clarity_score: float  # 0-1, how clear the prompt is
    completeness_score: float  # 0-1, how complete the context is
    specificity_score: float  # 0-1, how specific the instructions are
    improvements: list[str]  # Specific improvement suggestions
    optimized_prompt: str  # LLM-generated optimized version
    confidence: float  # 0-1, confidence in the optimization
    

@dataclass
class PromptHistory:
    """Historical performance data for a prompt pattern."""
    
    original_prompt: str
    optimized_prompts: list[str]
    performance_scores: list[float]
    execution_times: list[float]
    success_rates: list[float]
    best_variant: str | None = None
    convergence_score: float = 0.0


class PromptLearner(Loggable):
    """LLM-powered prompt learning and optimization system."""
    
    def __init__(self, storage_path: str | None = None):
        super().__init__()
        self.storage_path = Path(storage_path) if storage_path else Path("tmp/poet_prompt_learning")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Prompt history by function name
        self.prompt_history: dict[str, PromptHistory] = {}
        self.analysis_cache: dict[str, PromptAnalysis] = {}
        
        # Learning parameters
        self.min_executions_for_learning = 5
        self.analysis_frequency = 10  # Analyze every N executions
        self.execution_count = 0
        
        self._load_prompt_history()
    
    def analyze_prompt(self, prompt: str, domain: str, function_name: str, 
                      performance_context: dict | None = None) -> PromptAnalysis:
        """
        Use LLM to analyze and optimize a prompt.
        
        Args:
            prompt: Original prompt to analyze
            domain: Domain context (e.g., "financial_services")
            function_name: Name of the function using this prompt
            performance_context: Recent performance metrics
            
        Returns:
            PromptAnalysis with optimization suggestions
        """
        # Check cache first
        cache_key = f"{hash(prompt)}_{domain}_{function_name}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        try:
            analysis = self._perform_llm_analysis(prompt, domain, function_name, performance_context)
            self.analysis_cache[cache_key] = analysis
            return analysis
        except Exception as e:
            self.warning(f"LLM prompt analysis failed: {e}")
            # Return basic analysis as fallback
            return PromptAnalysis(
                clarity_score=0.7,
                completeness_score=0.7,
                specificity_score=0.7,
                improvements=["Consider adding more specific context"],
                optimized_prompt=prompt,
                confidence=0.3
            )
    
    def _perform_llm_analysis(self, prompt: str, domain: str, function_name: str,
                             performance_context: dict | None = None) -> PromptAnalysis:
        """Perform the actual LLM-based prompt analysis."""
        
        # Build analysis context
        context_info = f"""
Domain: {domain}
Function: {function_name}
Original Prompt: "{prompt}"
"""
        
        if performance_context:
            context_info += f"""
Recent Performance:
- Success Rate: {performance_context.get('success_rate', 'N/A')}
- Avg Response Quality: {performance_context.get('avg_quality', 'N/A')}
- Common Issues: {performance_context.get('common_issues', 'None noted')}
"""

        # For now, we'll simulate LLM analysis with intelligent heuristics
        # In production, this would call an actual LLM with a detailed analysis prompt
        return self._simulate_llm_analysis(prompt, domain, function_name)
    
    def _simulate_llm_analysis(self, prompt: str, domain: str, function_name: str) -> PromptAnalysis:
        """Simulate LLM analysis with intelligent heuristics."""
        
        improvements = []
        clarity_score = 0.7
        completeness_score = 0.7
        specificity_score = 0.7
        
        # Analyze prompt length and structure
        if len(prompt) < 20:
            improvements.append("Add more context and specific instructions")
            completeness_score -= 0.2
            
        if len(prompt) > 500:
            improvements.append("Consider breaking into clearer, more focused instructions")
            clarity_score -= 0.1
        
        # Check for domain-specific context
        domain_keywords = {
            "financial_services": ["credit", "risk", "income", "score", "compliance", "regulation"],
            "building_management": ["temperature", "energy", "hvac", "occupancy", "efficiency"],
            "semiconductor": ["process", "fab", "yield", "defect", "tolerance", "spc"],
            "llm_optimization": ["prompt", "response", "quality", "context", "instruction"]
        }
        
        if domain in domain_keywords:
            found_keywords = any(keyword in prompt.lower() for keyword in domain_keywords[domain])
            if not found_keywords:
                improvements.append(f"Add domain-specific context for {domain}")
                completeness_score -= 0.2
        
        # Check for output format specification
        format_indicators = ["format", "structure", "return", "output", "response"]
        if not any(indicator in prompt.lower() for indicator in format_indicators):
            improvements.append("Specify the expected output format clearly")
            specificity_score -= 0.2
        
        # Check for examples
        if "example" not in prompt.lower() and len(prompt) > 100:
            improvements.append("Consider adding examples for clarity")
            clarity_score -= 0.1
        
        # Generate optimized prompt
        optimized_prompt = self._generate_optimized_prompt(prompt, improvements, domain)
        
        return PromptAnalysis(
            clarity_score=max(0.1, clarity_score),
            completeness_score=max(0.1, completeness_score),
            specificity_score=max(0.1, specificity_score),
            improvements=improvements[:3],  # Limit to top 3
            optimized_prompt=optimized_prompt,
            confidence=0.8 if improvements else 0.9
        )
    
    def _generate_optimized_prompt(self, original: str, improvements: list[str], domain: str) -> str:
        """Generate an optimized version of the prompt."""
        
        optimized = original.strip()
        
        # Apply improvements
        if "Add more context" in str(improvements):
            if domain == "financial_services":
                optimized = f"For financial risk assessment, analyze the following data carefully: {optimized}"
            elif domain == "building_management":
                optimized = f"For building system optimization, consider energy efficiency and occupant comfort: {optimized}"
            elif domain == "semiconductor":
                optimized = f"For semiconductor process analysis, ensure quality and yield optimization: {optimized}"
        
        if "expected output format" in str(improvements):
            optimized += "\n\nProvide your response in a clear, structured format with specific actionable recommendations."
        
        if "domain-specific context" in str(improvements):
            optimized = f"Context: {domain.replace('_', ' ').title()} domain analysis.\n\n{optimized}"
        
        return optimized
    
    def record_execution_feedback(self, function_name: str, prompt: str, 
                                 performance_score: float, execution_time: float, 
                                 success: bool, error_type: str | None = None):
        """Record execution feedback for prompt learning."""
        
        if function_name not in self.prompt_history:
            self.prompt_history[function_name] = PromptHistory(
                original_prompt=prompt,
                optimized_prompts=[],
                performance_scores=[],
                execution_times=[],
                success_rates=[]
            )
        
        history = self.prompt_history[function_name]
        
        # Record performance
        history.performance_scores.append(performance_score)
        history.execution_times.append(execution_time)
        history.success_rates.append(1.0 if success else 0.0)
        
        # Keep only recent history (last 50 executions)
        max_history = 50
        if len(history.performance_scores) > max_history:
            history.performance_scores = history.performance_scores[-max_history:]
            history.execution_times = history.execution_times[-max_history:]
            history.success_rates = history.success_rates[-max_history:]
        
        # Update best variant if this is better
        if len(history.performance_scores) >= 5:
            recent_avg = sum(history.performance_scores[-5:]) / 5
            if not history.best_variant or recent_avg > 0.8:
                history.best_variant = prompt
        
        self._save_prompt_history()
    
    def should_optimize_prompt(self, function_name: str) -> bool:
        """Determine if this prompt should be optimized based on learning criteria."""
        
        self.execution_count += 1
        
        # Don't optimize too frequently
        if self.execution_count % self.analysis_frequency != 0:
            return False
        
        # Need minimum executions to establish baseline
        if function_name not in self.prompt_history:
            return False
            
        history = self.prompt_history[function_name]
        if len(history.performance_scores) < self.min_executions_for_learning:
            return False
        
        # Optimize if performance is poor or declining
        recent_performance = sum(history.performance_scores[-5:]) / 5 if len(history.performance_scores) >= 5 else 0
        recent_success = sum(history.success_rates[-5:]) / 5 if len(history.success_rates) >= 5 else 0
        
        return recent_performance < 0.7 or recent_success < 0.8
    
    def get_learning_recommendations(self, function_name: str) -> list[str]:
        """Get human-readable learning recommendations."""
        
        if function_name not in self.prompt_history:
            return ["Insufficient data for recommendations"]
        
        history = self.prompt_history[function_name]
        if len(history.performance_scores) < 3:
            return ["Collecting performance data..."]
        
        recommendations = []
        
        # Analyze performance trends
        recent_performance = sum(history.performance_scores[-3:]) / 3
        recent_success = sum(history.success_rates[-3:]) / 3
        
        if recent_performance < 0.6:
            recommendations.append("Low response quality detected - consider prompt optimization")
        
        if recent_success < 0.8:
            recommendations.append("High failure rate - prompt may need clearer instructions")
        
        if len(history.execution_times) >= 3:
            avg_time = sum(history.execution_times[-3:]) / 3
            if avg_time > 10.0:
                recommendations.append("Slow response times - consider simplifying prompt")
        
        if len(history.optimized_prompts) > 0:
            recommendations.append(f"Tested {len(history.optimized_prompts)} prompt variants")
        
        return recommendations or ["Performance within acceptable ranges"]
    
    def _load_prompt_history(self):
        """Load prompt history from storage."""
        history_file = self.storage_path / "prompt_history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    data = json.load(f)
                    for func_name, hist_data in data.items():
                        self.prompt_history[func_name] = PromptHistory(**hist_data)
            except Exception as e:
                self.warning(f"Failed to load prompt history: {e}")
    
    def _save_prompt_history(self):
        """Save prompt history to storage."""
        history_file = self.storage_path / "prompt_history.json"
        try:
            data = {
                func_name: asdict(history) 
                for func_name, history in self.prompt_history.items()
            }
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.warning(f"Failed to save prompt history: {e}")


class EnhancedLLMOptimizationPlugin(POETPlugin, Loggable):
    """Enhanced LLM optimization plugin with prompt learning capabilities."""

    __version__ = "2.0.0"
    __author__ = "OpenDXA Team"

    def __init__(self, enable_prompt_learning: bool = True, storage_path: str | None = None):
        Loggable.__init__(self)
        self.enable_prompt_learning = enable_prompt_learning
        self.prompt_learner = PromptLearner(storage_path) if enable_prompt_learning else None
        
        # Basic optimization parameters (learnable)
        self.prompt_enhancement_enabled = True
        self.context_optimization_level = 0.7  # 0-1 scale
        self.response_validation_threshold = 0.6
        
        # Execution tracking
        self.execution_history = {}

    def get_plugin_name(self) -> str:
        """Get unique plugin identifier."""
        return "enhanced_llm_optimization"

    def process_inputs(self, args: tuple, kwargs: dict) -> dict[str, Any]:
        """Process inputs with enhanced prompt optimization."""
        
        # Extract prompt from arguments
        prompt = self._extract_prompt(args, kwargs)
        if not prompt:
            return {"args": args, "kwargs": kwargs}
        
        # Get function name from context (set by POEExecutor)
        function_name = getattr(self, '_current_function_name', 'unknown')
        domain = getattr(self, '_current_domain', 'llm_optimization')
        
        optimized_prompt = prompt
        
        # Apply prompt learning if enabled
        if self.prompt_learner and self.enable_prompt_learning:
            try:
                # Check if we should optimize this prompt
                if self.prompt_learner.should_optimize_prompt(function_name):
                    analysis = self.prompt_learner.analyze_prompt(
                        prompt, domain, function_name,
                        self._get_performance_context(function_name)
                    )
                    
                    if analysis.confidence > 0.7:
                        optimized_prompt = analysis.optimized_prompt
                        self.debug(f"Applied LLM prompt optimization for {function_name}")
                    
            except Exception as e:
                self.warning(f"Prompt learning failed: {e}")
        
        # Apply basic optimizations
        if self.prompt_enhancement_enabled:
            optimized_prompt = self._apply_basic_optimizations(optimized_prompt)
        
        # Return optimized arguments
        return self._replace_prompt_in_args(args, kwargs, optimized_prompt)
    
    def validate_output(self, result: Any, context: dict[str, Any]) -> Any:
        """Validate LLM output and record feedback for learning."""
        
        # Basic validation first
        validated_result = self._basic_output_validation(result, context)
        
        # Record feedback for prompt learning
        if self.prompt_learner and self.enable_prompt_learning:
            try:
                function_name = getattr(self, '_current_function_name', 'unknown')
                prompt = self._extract_prompt_from_context(context)
                
                if prompt and function_name != 'unknown':
                    performance_score = self._calculate_response_quality(validated_result, context)
                    execution_time = context.get('execution_time', 0.0)
                    success = validated_result is not None
                    
                    self.prompt_learner.record_execution_feedback(
                        function_name, prompt, performance_score, 
                        execution_time, success
                    )
                    
            except Exception as e:
                self.warning(f"Failed to record prompt learning feedback: {e}")
        
        return validated_result
    
    def receive_feedback(self, feedback: dict[str, Any]) -> None:
        """Receive feedback about plugin performance for learning."""
        function_name = feedback.get('function_name', 'unknown')
        
        # Store execution context for learning
        if function_name not in self.execution_history:
            self.execution_history[function_name] = []
        
        self.execution_history[function_name].append(feedback)
        
        # Keep only recent history
        if len(self.execution_history[function_name]) > 100:
            self.execution_history[function_name] = self.execution_history[function_name][-100:]
    
    def get_learning_status(self) -> dict[str, Any]:
        """Get current learning status for this plugin."""
        if not self.prompt_learner:
            return {
                "learning_enabled": False,
                "parameters_learned": 0,
                "learning_progress": "disabled",
                "performance_trend": "stable",
            }
        
        total_functions = len(self.prompt_learner.prompt_history)
        total_optimizations = sum(
            len(history.optimized_prompts) 
            for history in self.prompt_learner.prompt_history.values()
        )
        
        return {
            "learning_enabled": True,
            "parameters_learned": 3,  # prompt_enhancement, context_optimization, validation_threshold
            "learning_progress": f"optimizing_{total_functions}_functions",
            "performance_trend": "improving" if total_optimizations > 0 else "baseline",
            "functions_tracked": total_functions,
            "total_optimizations": total_optimizations,
        }
    
    def get_learnable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get parameters that can be learned/optimized."""
        return {
            "prompt_enhancement_enabled": {
                "current_value": self.prompt_enhancement_enabled,
                "type": "categorical",
                "range": [True, False],
                "impact": "Enables/disables basic prompt enhancements"
            },
            "context_optimization_level": {
                "current_value": self.context_optimization_level,
                "type": "continuous", 
                "range": (0.0, 1.0),
                "impact": "Controls how aggressively to optimize context"
            },
            "response_validation_threshold": {
                "current_value": self.response_validation_threshold,
                "type": "continuous",
                "range": (0.0, 1.0), 
                "impact": "Threshold for response quality validation"
            }
        }
    
    def apply_learned_parameters(self, learned_params: dict[str, Any]) -> None:
        """Apply learned parameters to plugin behavior."""
        if "prompt_enhancement_enabled" in learned_params:
            self.prompt_enhancement_enabled = learned_params["prompt_enhancement_enabled"]
            
        if "context_optimization_level" in learned_params:
            self.context_optimization_level = max(0.0, min(1.0, learned_params["context_optimization_level"]))
            
        if "response_validation_threshold" in learned_params:
            self.response_validation_threshold = max(0.0, min(1.0, learned_params["response_validation_threshold"]))
    
    def get_learning_recommendations(self, function_name: str) -> list[str]:
        """Get learning recommendations for a specific function."""
        if self.prompt_learner:
            return self.prompt_learner.get_learning_recommendations(function_name)
        return ["Prompt learning disabled"]
    
    # Private helper methods
    
    def _extract_prompt(self, args: tuple, kwargs: dict) -> str | None:
        """Extract prompt from function arguments."""
        if args and isinstance(args[0], str):
            return args[0]
        if 'prompt' in kwargs and isinstance(kwargs['prompt'], str):
            return kwargs['prompt']
        return None
    
    def _replace_prompt_in_args(self, args: tuple, kwargs: dict, new_prompt: str) -> dict[str, Any]:
        """Replace prompt in arguments with optimized version."""
        if args and isinstance(args[0], str):
            return {"args": (new_prompt,) + args[1:], "kwargs": kwargs}
        elif 'prompt' in kwargs:
            new_kwargs = kwargs.copy()
            new_kwargs['prompt'] = new_prompt
            return {"args": args, "kwargs": new_kwargs}
        else:
            # Fallback - add as first argument
            return {"args": (new_prompt,) + args, "kwargs": kwargs}
    
    def _apply_basic_optimizations(self, prompt: str) -> str:
        """Apply basic prompt optimizations."""
        if not prompt or not isinstance(prompt, str):
            return prompt
            
        optimized = prompt.strip()
        
        # Add clarity for very short prompts
        if len(optimized) < 20:
            optimized = f"Please provide a detailed and accurate response to: {optimized}"
        
        # Add structure request based on optimization level
        if self.context_optimization_level > 0.5 and len(optimized) > 100:
            if "format" not in optimized.lower() and "structure" not in optimized.lower():
                optimized += "\n\nPlease structure your response clearly and concisely."
        
        return optimized
    
    def _basic_output_validation(self, result: Any, context: dict[str, Any]) -> Any:
        """Perform basic output validation."""
        if result is None:
            raise ValueError("Empty response from LLM")
            
        if isinstance(result, str) and len(result.strip()) == 0:
            raise ValueError("Empty text response from LLM")
        
        # Quality threshold check
        if isinstance(result, str):
            quality_score = self._calculate_response_quality(result, context)
            if quality_score < self.response_validation_threshold:
                self.warning(f"Response quality below threshold: {quality_score}")
                
        return result
    
    def _calculate_response_quality(self, result: Any, context: dict[str, Any]) -> float:
        """Calculate response quality score."""
        if not isinstance(result, str):
            return 0.8  # Default for non-string responses
            
        quality = 0.5  # Base score
        
        # Length-based quality
        if len(result) > 10:
            quality += 0.2
        if len(result) > 50:
            quality += 0.1
            
        # Content quality indicators
        if any(word in result.lower() for word in ['however', 'because', 'therefore', 'analysis']):
            quality += 0.1
            
        # Execution time factor
        execution_time = context.get('execution_time', 0.0)
        if 1.0 <= execution_time <= 10.0:  # Sweet spot
            quality += 0.1
            
        return min(1.0, quality)
    
    def _extract_prompt_from_context(self, context: dict[str, Any]) -> str | None:
        """Extract prompt from execution context."""
        args = context.get('perceived_input', {}).get('args', ())
        kwargs = context.get('perceived_input', {}).get('kwargs', {})
        return self._extract_prompt(args, kwargs)
    
    def _get_performance_context(self, function_name: str) -> dict[str, Any]:
        """Get performance context for prompt analysis."""
        if function_name not in self.execution_history:
            return {}
            
        recent_executions = self.execution_history[function_name][-10:]  # Last 10
        if not recent_executions:
            return {}
            
        success_rate = sum(1 for ex in recent_executions if ex.get('success', False)) / len(recent_executions)
        avg_quality = sum(ex.get('output_quality', 0.5) for ex in recent_executions) / len(recent_executions)
        
        # Identify common issues
        common_issues = []
        error_types = [ex.get('error_type') for ex in recent_executions if ex.get('error_type')]
        if len(error_types) > len(recent_executions) / 2:
            common_issues.append("High error rate")
            
        return {
            "success_rate": success_rate,
            "avg_quality": avg_quality,
            "common_issues": common_issues
        }
    
    def set_current_context(self, function_name: str, domain: str):
        """Set current execution context for learning."""
        self._current_function_name = function_name
        self._current_domain = domain

    def get_plugin_info(self) -> dict[str, Any]:
        """Get comprehensive plugin information."""
        base_info = super().get_plugin_info()
        base_info.update({
            "domain": "llm_optimization", 
            "capabilities": [
                "process_inputs", "validate_output", "prompt_optimization", 
                "response_validation", "quality_checks", "prompt_learning",
                "performance_tracking", "adaptive_optimization"
            ],
            "learning_features": [
                "llm_prompt_analysis", "iterative_optimization", 
                "performance_feedback", "context_adaptation"
            ] if self.enable_prompt_learning else [],
            "supported_models": ["gpt", "claude", "llama", "generic"],
            "optimization_features": [
                "prompt_enhancement", "context_optimization", 
                "response_validation", "adaptive_learning"
            ],
        })
        return base_info