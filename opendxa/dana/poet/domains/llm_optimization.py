"""
LLM Optimization Domain Plugin for POET

Provides domain-specific intelligence for LLM reasoning tasks,
including prompt optimization and response validation.
"""

from typing import Any, Dict, Tuple


class LLMOptimizationPlugin:
    """Domain plugin for LLM optimization and reasoning tasks."""
    
    def __init__(self):
        self.optimization_history = {}
        
    def process_inputs(self, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
        """Process inputs for LLM reasoning with optimization."""
        
        # For functions that only take a prompt, just optimize the prompt
        if len(args) == 1 and not kwargs:
            prompt = args[0]
            optimized_prompt = self._optimize_prompt(prompt)
            return {
                "args": (optimized_prompt,),
                "kwargs": {}
            }
        
        # For more complex function signatures, extract and optimize
        prompt = args[0] if args else kwargs.get("prompt", "")
        
        # Basic prompt optimization
        optimized_prompt = self._optimize_prompt(prompt)
        
        # Keep other arguments as-is
        if len(args) == 1:
            return {
                "args": (optimized_prompt,),
                "kwargs": kwargs
            }
        else:
            # Multiple arguments - replace first with optimized prompt
            new_args = (optimized_prompt,) + args[1:]
            return {
                "args": new_args,
                "kwargs": kwargs
            }
    
    def validate_output(self, operation_result: Dict, processed_input: Dict) -> Any:
        """Validate LLM output and ensure quality."""
        
        result = operation_result["result"]
        execution_time = operation_result.get("execution_time", 0)
        
        # Basic validation
        if result is None:
            raise ValueError("Empty response from LLM")
            
        if isinstance(result, str) and len(result.strip()) == 0:
            raise ValueError("Empty text response from LLM")
        
        # Quality checks
        if isinstance(result, str):
            # Check for common LLM failure patterns
            if "I cannot" in result or "I'm unable" in result:
                # Log but don't fail - might be a legitimate response
                pass
                
            # Check for very short responses that might indicate problems
            if len(result.strip()) < 10 and execution_time < 0.5:
                # Very quick, very short response might indicate an error
                raise ValueError("Suspiciously short response from LLM")
        
        return result
    
    def _optimize_prompt(self, prompt: str) -> str:
        """Apply basic prompt optimization techniques."""
        
        if not prompt or not isinstance(prompt, str):
            return prompt
            
        optimized = prompt.strip()
        
        # Add clarity instructions for very short prompts
        if len(optimized) < 20:
            optimized = f"Please provide a detailed and accurate response to: {optimized}"
            
        # Add structure request for complex queries
        elif len(optimized) > 200 and not any(word in optimized.lower() for word in ["step", "list", "format"]):
            optimized += "\n\nPlease structure your response clearly with key points."
            
        return optimized
    
    def _enhance_llm_options(self, options: Dict) -> Dict:
        """Enhance LLM options with optimization defaults."""
        
        enhanced = options.copy()
        
        # Set reasonable defaults if not specified
        if "temperature" not in enhanced:
            enhanced["temperature"] = 0.7  # Balanced creativity/consistency
            
        if "max_tokens" not in enhanced:
            enhanced["max_tokens"] = 2000  # Reasonable default
            
        # Optimize system message if not provided
        if "system_message" not in enhanced:
            enhanced["system_message"] = (
                "You are a helpful AI assistant. Provide clear, accurate, and "
                "well-structured responses. If you're uncertain about something, "
                "state your uncertainty explicitly."
            )
        
        return enhanced