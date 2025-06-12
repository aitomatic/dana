# LLM Prompt Learning Implementation for POET

## Overview

This implementation adds **LLM-powered prompt learning** to POET's T-stage (Train), enabling automatic prompt optimization based on execution feedback. This represents a hybrid approach that combines statistical parameter learning with LLM-driven prompt intelligence.

## Architecture

### Core Components

1. **PromptLearner**: LLM-powered prompt analysis and optimization
2. **EnhancedLLMOptimizationPlugin**: Extended plugin with prompt learning capabilities  
3. **POEExecutor Integration**: T-stage hooks for plugin learning feedback
4. **Execution Tracking**: Performance metrics and recommendation system

### Plugin Design

```python
@poet(domain="enhanced_llm_optimization", enable_training=True)
def analyze_risk(credit_score: int, income: float) -> str:
    prompt = f"Analyze financial risk for score {credit_score}, income ${income}"
    return reason(prompt)
```

The enhanced plugin automatically:
- **P-stage**: Analyzes and optimizes prompts before execution
- **E-stage**: Records execution feedback for learning
- **T-stage**: Receives feedback to improve future optimizations

### Learning Process

1. **Execution Tracking**: Records performance metrics for each prompt
2. **Trigger Optimization**: Analyzes prompts when performance is poor
3. **LLM Analysis**: Uses intelligent heuristics (simulating LLM reasoning) to optimize prompts
4. **Feedback Loop**: Applies optimized prompts and measures improvement

## Key Features

### 1. Intelligent Prompt Analysis
- **Clarity Score**: How clear and understandable the prompt is
- **Completeness Score**: Whether sufficient context is provided
- **Specificity Score**: How specific and actionable instructions are
- **Domain Adaptation**: Adds domain-specific context and requirements

### 2. Performance-Driven Learning
- **Optimization Triggers**: Poor performance (< 0.7 quality) or low success rate (< 0.8)
- **Execution Frequency**: Analyzes prompts every N executions to avoid overhead
- **Historical Tracking**: Maintains performance history for trend analysis

### 3. Learnable Parameters
- **prompt_enhancement_enabled**: Toggle basic prompt enhancements
- **context_optimization_level**: Control aggressiveness of context optimization (0-1)
- **response_validation_threshold**: Quality threshold for validation (0-1)

### 4. Learning Recommendations
- Human-readable insights about prompt performance
- Specific suggestions for improvement
- Progress tracking across functions

## Implementation Details

### Plugin Integration
The enhanced plugin extends the base POETPlugin with learning methods:
- `receive_feedback()`: Gets execution feedback from T-stage
- `get_learning_status()`: Reports learning progress and metrics  
- `apply_learned_parameters()`: Updates plugin behavior based on learning

### POEExecutor Changes
Added plugin learning hooks in key stages:
- **P-stage**: Sets execution context for learning-enabled plugins
- **E-stage**: Provides rich context for output validation and feedback
- **T-stage**: Sends comprehensive feedback to plugins for learning

### Storage and Persistence
- **Prompt History**: Stores performance data in JSON format
- **Analysis Cache**: Caches LLM analysis results for efficiency
- **Learning Metrics**: Tracks convergence and optimization progress

## Usage Examples

### Basic Usage
```python
from opendxa.dana.poet import poet

@poet(domain="enhanced_llm_optimization", enable_training=True)
def analyze_financial_risk(credit_score: int, income: float) -> str:
    prompt = f"Analyze risk for credit {credit_score}, income ${income}"
    return reason(prompt)
```

### Advanced Configuration
```python
config = POETConfig(
    domain="enhanced_llm_optimization",
    enable_training=True,
    learning_algorithm="statistical"
)

executor = POETExecutor(config)
enhanced_function = executor(your_function)
```

### Learning Status
```python
# Check learning progress
status = enhanced_function._poet_executor.domain_plugin.get_learning_status()
print(f"Functions tracked: {status['functions_tracked']}")
print(f"Optimizations: {status['total_optimizations']}")

# Get recommendations
recommendations = enhanced_function._poet_executor.domain_plugin.get_learning_recommendations("your_function")
for rec in recommendations:
    print(f"- {rec}")
```

## Testing

Comprehensive test suite covering:
- **PromptLearner**: Analysis, feedback recording, optimization triggers
- **Plugin Integration**: Input processing, output validation, learning status
- **POET Integration**: End-to-end learning cycles with POEExecutor
- **Persistence**: Save/load of learning data

Run tests:
```bash
uv run pytest tests/dana/poet/test_llm_prompt_learning.py -v
```

## Future Enhancements

### 1. Real LLM Integration
Replace simulation with actual LLM calls:
```python
def _perform_llm_analysis(self, prompt, domain, function_name, context):
    llm_prompt = self._build_analysis_prompt(prompt, domain, context)
    analysis_result = self.llm_client.analyze(llm_prompt)
    return self._parse_analysis_result(analysis_result)
```

### 2. Cross-Function Learning
Enable learning insights to transfer between similar functions:
- Pattern recognition across prompts
- Domain-specific optimization templates
- Shared optimization strategies

### 3. Advanced Learning Algorithms
- **Reinforcement Learning**: Optimize prompts based on reward signals
- **Multi-Objective Optimization**: Balance quality, speed, and resource usage
- **Adaptive Strategies**: Switch between learning approaches based on performance

### 4. Integration with Existing LLM Tools
- **LangSmith**: Integration for prompt tracking and analytics
- **Weights & Biases**: Advanced experiment tracking
- **MLflow**: Model and prompt versioning

## Benefits

1. **Automatic Improvement**: Prompts get better over time without manual intervention
2. **Domain Intelligence**: Leverages POET's domain plugin architecture
3. **Hybrid Approach**: Combines statistical reliability with LLM intelligence
4. **Progressive Enhancement**: Start simple, add complexity as needed (KISS/YAGNI)
5. **Explainable Learning**: Provides clear recommendations and insights

## Implementation Impact

This implementation successfully demonstrates:
- **Feasibility**: LLM learning in POET's T-stage is technically viable
- **Value**: Clear benefits for prompt optimization use cases
- **Architecture**: Clean integration with existing POET plugin system
- **Scalability**: Framework supports future enhancements and real LLM integration

The hybrid statistical + LLM learning approach represents a compelling evolution of POET's learning capabilities, providing immediate value while establishing the foundation for more advanced prompt optimization features.