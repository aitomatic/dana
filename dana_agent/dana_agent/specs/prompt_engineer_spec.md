# PromptEngineer Class Specification

## Overview

The PromptEngineer class handles all prompt-related complexity in the agentic architecture. It creates, combines, and evolves prompts based on agent state, available resources, and feedback. This class is central to the system's ability to adapt and improve over time.

## Core PromptEngineer Class

```python
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class PromptType(Enum):
    """Types of prompts in the system."""
    SYSTEM = "system"
    USER = "user"
    TOOL = "tool"
    WORKFLOW = "workflow"
    CONTEXT = "context"
    ERROR = "error"
    FEEDBACK = "feedback"

class PromptStrategy(Enum):
    """Strategies for combining prompts."""
    CONCATENATE = "concatenate"
    TEMPLATE = "template"
    HIERARCHICAL = "hierarchical"
    DYNAMIC = "dynamic"
    ADAPTIVE = "adaptive"

@dataclass
class PromptTemplate:
    """Template for generating prompts."""
    name: str
    template: str
    variables: List[str]
    prompt_type: PromptType
    version: str = "1.0.0"
    metadata: Dict[str, Any] = None

@dataclass
class PromptVariant:
    """A variant of a prompt for A/B testing."""
    name: str
    content: str
    performance_score: float = 0.0
    usage_count: int = 0
    success_rate: float = 0.0

class PromptEngineer:
    """
    Handles all prompt creation, combination, and evolution.
    
    This class manages the complexity of creating effective prompts by:
    - Combining state and context elements
    - Adapting prompts based on feedback
    - Evolving prompts through learning
    - Managing prompt templates and variants
    """
    
    def __init__(self, 
                 agent_type: str, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PromptEngineer.
        
        Args:
            agent_type: Type of agent (e.g., 'coding', 'financial_analyst')
            config: Optional configuration dictionary
        """
        self.agent_type = agent_type
        self.config = config or {}
        
        # Prompt storage
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.adaptive_prompts: Dict[str, str] = {}
        self.prompt_variants: Dict[str, List[PromptVariant]] = {}
        
        # Learning and feedback
        self.feedback_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_data: Dict[str, Any] = {}
        
        # Prompt evolution
        self.evolution_engine = PromptEvolutionEngine(self)
        self.adaptation_engine = PromptAdaptationEngine(self)
        
        # Initialize with default templates
        self._initialize_default_templates()
    
    def create_system_prompt(self, 
                           agent_state: Dict[str, Any], 
                           available_resources: Dict[str, Any], 
                           available_workflows: Dict[str, Any]) -> str:
        """
        Create system prompt incorporating state and capabilities.
        
        Args:
            agent_state: Current agent state
            available_resources: Available resources
            available_workflows: Available workflows
        
        Returns:
            Generated system prompt
        """
        # Get base system template
        base_template = self._get_template('system_base')
        
        # Extract context elements
        context_elements = self._extract_context_elements(agent_state)
        resource_elements = self._extract_resource_elements(available_resources)
        workflow_elements = self._extract_workflow_elements(available_workflows)
        
        # Combine elements
        combined_elements = self._combine_context_elements([
            context_elements,
            resource_elements,
            workflow_elements
        ])
        
        # Generate prompt using template
        system_prompt = self._generate_from_template(
            base_template,
            {
                'agent_type': self.agent_type,
                'context': combined_elements,
                'resources': self._format_resources(available_resources),
                'workflows': self._format_workflows(available_workflows),
                'user_preferences': agent_state.get('user_preferences', {}),
                'current_task': agent_state.get('current_context', {}).get('active_task')
            }
        )
        
        # Apply adaptive modifications
        adapted_prompt = self.adaptation_engine.adapt_prompt(
            system_prompt, 
            agent_state, 
            PromptType.SYSTEM
        )
        
        return adapted_prompt
    
    def create_user_prompt(self, 
                          user_input: str, 
                          context: Dict[str, Any]) -> str:
        """
        Create user prompt with context.
        
        Args:
            user_input: User's input message
            context: Additional context
        
        Returns:
            Generated user prompt
        """
        # Get base user template
        base_template = self._get_template('user_base')
        
        # Extract relevant context
        relevant_context = self._extract_relevant_context(context, user_input)
        
        # Generate prompt
        user_prompt = self._generate_from_template(
            base_template,
            {
                'user_input': user_input,
                'context': relevant_context,
                'timestamp': datetime.now().isoformat(),
                'session_info': context.get('session_metadata', {})
            }
        )
        
        return user_prompt
    
    def create_tool_prompt(self, 
                          tool_name: str, 
                          tool_info: Dict[str, Any]) -> str:
        """
        Create prompt for tool execution.
        
        Args:
            tool_name: Name of the tool
            tool_info: Tool information
        
        Returns:
            Generated tool prompt
        """
        template = self._get_template('tool_execution')
        
        return self._generate_from_template(
            template,
            {
                'tool_name': tool_name,
                'tool_description': tool_info.get('description', ''),
                'tool_parameters': tool_info.get('parameters', {}),
                'tool_examples': tool_info.get('examples', [])
            }
        )
    
    def combine_prompts(self, 
                       prompt_parts: List[Dict[str, Any]], 
                       strategy: PromptStrategy = PromptStrategy.CONCATENATE) -> str:
        """
        Combine multiple prompt parts using specified strategy.
        
        Args:
            prompt_parts: List of prompt parts to combine
            strategy: Strategy for combining prompts
        
        Returns:
            Combined prompt
        """
        if strategy == PromptStrategy.CONCATENATE:
            return self._concatenate_prompts(prompt_parts)
        elif strategy == PromptStrategy.TEMPLATE:
            return self._template_combine_prompts(prompt_parts)
        elif strategy == PromptStrategy.HIERARCHICAL:
            return self._hierarchical_combine_prompts(prompt_parts)
        elif strategy == PromptStrategy.DYNAMIC:
            return self._dynamic_combine_prompts(prompt_parts)
        elif strategy == PromptStrategy.ADAPTIVE:
            return self._adaptive_combine_prompts(prompt_parts)
        else:
            raise ValueError(f"Unknown prompt strategy: {strategy}")
    
    def evolve_prompt(self, 
                     prompt_type: str, 
                     feedback: Dict[str, Any], 
                     performance_data: Dict[str, Any]) -> None:
        """
        Evolve prompts based on feedback and performance.
        
        Args:
            prompt_type: Type of prompt to evolve
            feedback: Feedback data
            performance_data: Performance metrics
        """
        # Record feedback
        self.feedback_history.append({
            'timestamp': datetime.now().isoformat(),
            'prompt_type': prompt_type,
            'feedback': feedback,
            'performance': performance_data
        })
        
        # Update performance metrics
        self._update_performance_metrics(prompt_type, performance_data)
        
        # Evolve the prompt
        evolved_prompt = self.evolution_engine.evolve_prompt(
            prompt_type, 
            feedback, 
            performance_data
        )
        
        # Update adaptive prompts
        self.adaptive_prompts[prompt_type] = evolved_prompt
    
    def adapt_to_context(self, 
                        base_prompt: str, 
                        context: Dict[str, Any]) -> str:
        """
        Adapt prompt based on current context.
        
        Args:
            base_prompt: Base prompt to adapt
            context: Current context
        
        Returns:
            Adapted prompt
        """
        return self.adaptation_engine.adapt_prompt(
            base_prompt, 
            context, 
            PromptType.CONTEXT
        )
    
    def get_prompt_variants(self, 
                           prompt_type: str, 
                           count: int = 3) -> List[PromptVariant]:
        """
        Generate multiple prompt variants for A/B testing.
        
        Args:
            prompt_type: Type of prompt
            count: Number of variants to generate
        
        Returns:
            List of prompt variants
        """
        if prompt_type not in self.prompt_variants:
            self.prompt_variants[prompt_type] = []
        
        variants = self.evolution_engine.generate_variants(
            prompt_type, 
            count
        )
        
        # Add to variants list
        for variant in variants:
            self.prompt_variants[prompt_type].append(variant)
        
        return variants
```

## Prompt Templates System

```python
class PromptTemplateManager:
    """Manages prompt templates and their lifecycle."""
    
    def __init__(self, prompt_engineer: 'PromptEngineer'):
        self.prompt_engineer = prompt_engineer
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_versions: Dict[str, List[str]] = {}
    
    def register_template(self, template: PromptTemplate) -> None:
        """Register a new prompt template."""
        self.templates[template.name] = template
        
        if template.name not in self.template_versions:
            self.template_versions[template.name] = []
        
        self.template_versions[template.name].append(template.version)
    
    def get_template(self, name: str, version: str = None) -> Optional[PromptTemplate]:
        """Get a template by name and optional version."""
        if name not in self.templates:
            return None
        
        template = self.templates[name]
        
        if version and template.version != version:
            # Look for specific version
            return None
        
        return template
    
    def update_template(self, name: str, new_template: PromptTemplate) -> None:
        """Update an existing template."""
        if name in self.templates:
            old_version = self.templates[name].version
            self.templates[name] = new_template
            self.template_versions[name].append(new_template.version)
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def get_template_versions(self, name: str) -> List[str]:
        """Get all versions of a template."""
        return self.template_versions.get(name, [])

# Default templates for different agent types
CODING_AGENT_TEMPLATES = {
    'system_base': PromptTemplate(
        name='system_base',
        template="""You are a {agent_type} agent specialized in software engineering tasks.

## Current Context
{context}

## Available Resources
{resources}

## Available Workflows
{workflows}

## User Preferences
{user_preferences}

## Current Task
{current_task}

## Instructions
- Use the available resources and workflows to complete tasks
- Provide clear, actionable responses
- Follow best practices for {agent_type} tasks
- Ask for clarification when needed""",
        variables=['agent_type', 'context', 'resources', 'workflows', 'user_preferences', 'current_task'],
        prompt_type=PromptType.SYSTEM
    ),
    
    'user_base': PromptTemplate(
        name='user_base',
        template="""User Input: {user_input}

Context: {context}

Session: {session_info}
Timestamp: {timestamp}""",
        variables=['user_input', 'context', 'session_info', 'timestamp'],
        prompt_type=PromptType.USER
    ),
    
    'tool_execution': PromptTemplate(
        name='tool_execution',
        template="""Execute tool: {tool_name}

Description: {tool_description}

Parameters: {tool_parameters}

Examples: {tool_examples}""",
        variables=['tool_name', 'tool_description', 'tool_parameters', 'tool_examples'],
        prompt_type=PromptType.TOOL
    )
}

FINANCIAL_ANALYST_TEMPLATES = {
    'system_base': PromptTemplate(
        name='system_base',
        template="""You are a {agent_type} agent specialized in financial analysis and market research.

## Current Context
{context}

## Available Resources
{resources}

## Available Workflows
{workflows}

## User Preferences
{user_preferences}

## Current Task
{current_task}

## Instructions
- Use financial data and analysis tools to provide insights
- Ensure accuracy in financial calculations
- Provide clear explanations of market trends
- Consider risk factors in recommendations""",
        variables=['agent_type', 'context', 'resources', 'workflows', 'user_preferences', 'current_task'],
        prompt_type=PromptType.SYSTEM
    )
}
```

## Prompt Evolution Engine

```python
class PromptEvolutionEngine:
    """Handles prompt evolution and learning."""
    
    def __init__(self, prompt_engineer: 'PromptEngineer'):
        self.prompt_engineer = prompt_engineer
        self.learning_models = {}
        self.evolution_strategies = {
            'mutation': self._mutate_prompt,
            'crossover': self._crossover_prompts,
            'selection': self._select_best_prompts,
            'adaptation': self._adapt_prompt
        }
    
    def evolve_prompt(self, 
                     prompt_type: str, 
                     feedback: Dict[str, Any], 
                     performance_data: Dict[str, Any]) -> str:
        """Evolve a prompt based on feedback and performance."""
        current_prompt = self.prompt_engineer.adaptive_prompts.get(prompt_type, "")
        
        if not current_prompt:
            # Initialize with base template
            template = self.prompt_engineer._get_template(f"{prompt_type}_base")
            current_prompt = template.template if template else ""
        
        # Analyze feedback and performance
        analysis = self._analyze_feedback(feedback, performance_data)
        
        # Apply evolution strategies
        evolved_prompt = self._apply_evolution_strategies(
            current_prompt, 
            analysis
        )
        
        return evolved_prompt
    
    def generate_variants(self, prompt_type: str, count: int) -> List[PromptVariant]:
        """Generate prompt variants for A/B testing."""
        base_prompt = self.prompt_engineer.adaptive_prompts.get(prompt_type, "")
        
        if not base_prompt:
            return []
        
        variants = []
        
        for i in range(count):
            # Generate variant using different strategies
            variant_content = self._generate_variant(base_prompt, i)
            
            variant = PromptVariant(
                name=f"{prompt_type}_variant_{i}",
                content=variant_content
            )
            
            variants.append(variant)
        
        return variants
    
    def _mutate_prompt(self, prompt: str, mutation_rate: float = 0.1) -> str:
        """Mutate a prompt by making small changes."""
        # This would implement actual mutation logic
        # For now, return a simple variation
        return prompt.replace("You are", "You are an advanced")
    
    def _crossover_prompts(self, prompt1: str, prompt2: str) -> str:
        """Combine two prompts through crossover."""
        # This would implement crossover logic
        # For now, return a simple combination
        return f"{prompt1}\n\nAdditional context: {prompt2}"
    
    def _select_best_prompts(self, prompts: List[str], scores: List[float]) -> str:
        """Select the best performing prompt."""
        if not prompts or not scores:
            return prompts[0] if prompts else ""
        
        best_index = scores.index(max(scores))
        return prompts[best_index]
    
    def _adapt_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Adapt prompt to specific context."""
        # This would implement context-specific adaptations
        return prompt
    
    def _analyze_feedback(self, feedback: Dict[str, Any], performance: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feedback and performance data."""
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'improvements': [],
            'performance_score': performance.get('score', 0.0)
        }
        
        # Extract strengths and weaknesses from feedback
        if 'positive_feedback' in feedback:
            analysis['strengths'].extend(feedback['positive_feedback'])
        
        if 'negative_feedback' in feedback:
            analysis['weaknesses'].extend(feedback['negative_feedback'])
        
        if 'suggestions' in feedback:
            analysis['improvements'].extend(feedback['suggestions'])
        
        return analysis
    
    def _apply_evolution_strategies(self, prompt: str, analysis: Dict[str, Any]) -> str:
        """Apply evolution strategies based on analysis."""
        evolved_prompt = prompt
        
        # Apply improvements
        for improvement in analysis['improvements']:
            evolved_prompt = self._apply_improvement(evolved_prompt, improvement)
        
        # Apply mutations based on performance
        if analysis['performance_score'] < 0.5:
            evolved_prompt = self._mutate_prompt(evolved_prompt, 0.2)
        
        return evolved_prompt
    
    def _apply_improvement(self, prompt: str, improvement: str) -> str:
        """Apply a specific improvement to the prompt."""
        # This would implement specific improvement logic
        return prompt
    
    def _generate_variant(self, base_prompt: str, variant_index: int) -> str:
        """Generate a specific variant of the prompt."""
        # This would implement variant generation logic
        return base_prompt
```

## Prompt Adaptation Engine

```python
class PromptAdaptationEngine:
    """Handles prompt adaptation based on context and feedback."""
    
    def __init__(self, prompt_engineer: 'PromptEngineer'):
        self.prompt_engineer = prompt_engineer
        self.adaptation_rules = {}
        self.context_patterns = {}
    
    def adapt_prompt(self, 
                    base_prompt: str, 
                    context: Dict[str, Any], 
                    prompt_type: PromptType) -> str:
        """Adapt a prompt based on context and prompt type."""
        adapted_prompt = base_prompt
        
        # Apply context-specific adaptations
        adapted_prompt = self._apply_context_adaptations(adapted_prompt, context)
        
        # Apply prompt-type-specific adaptations
        adapted_prompt = self._apply_type_adaptations(adapted_prompt, prompt_type)
        
        # Apply user preference adaptations
        adapted_prompt = self._apply_user_preferences(adapted_prompt, context)
        
        return adapted_prompt
    
    def _apply_context_adaptations(self, prompt: str, context: Dict[str, Any]) -> str:
        """Apply context-specific adaptations."""
        adapted_prompt = prompt
        
        # Adapt based on current task
        if 'active_task' in context.get('current_context', {}):
            task = context['current_context']['active_task']
            adapted_prompt += f"\n\nCurrent task: {task}"
        
        # Adapt based on working directory
        if 'working_directory' in context.get('current_context', {}):
            wd = context['current_context']['working_directory']
            adapted_prompt += f"\n\nWorking directory: {wd}"
        
        # Adapt based on focus area
        if 'focus_area' in context.get('current_context', {}):
            focus = context['current_context']['focus_area']
            adapted_prompt += f"\n\nFocus area: {focus}"
        
        return adapted_prompt
    
    def _apply_type_adaptations(self, prompt: str, prompt_type: PromptType) -> str:
        """Apply prompt-type-specific adaptations."""
        if prompt_type == PromptType.SYSTEM:
            # Add system-specific instructions
            prompt += "\n\nRemember to be helpful, accurate, and follow best practices."
        elif prompt_type == PromptType.USER:
            # Add user-specific formatting
            prompt = f"User Request: {prompt}"
        elif prompt_type == PromptType.TOOL:
            # Add tool-specific instructions
            prompt += "\n\nExecute this tool with the provided parameters."
        
        return prompt
    
    def _apply_user_preferences(self, prompt: str, context: Dict[str, Any]) -> str:
        """Apply user preference adaptations."""
        preferences = context.get('user_preferences', {})
        
        # Adapt verbosity
        verbosity = preferences.get('verbosity', 'normal')
        if verbosity == 'concise':
            prompt += "\n\nBe concise in your response."
        elif verbosity == 'detailed':
            prompt += "\n\nProvide detailed explanations and examples."
        
        # Adapt language
        language = preferences.get('language', 'en')
        if language != 'en':
            prompt += f"\n\nRespond in {language}."
        
        return prompt
```

## Prompt Performance Tracking

```python
class PromptPerformanceTracker:
    """Tracks and analyzes prompt performance."""
    
    def __init__(self, prompt_engineer: 'PromptEngineer'):
        self.prompt_engineer = prompt_engineer
        self.performance_data = {}
        self.metrics_calculator = PromptMetricsCalculator()
    
    def track_prompt_performance(self, 
                                prompt_type: str, 
                                prompt_content: str, 
                                result: Dict[str, Any]) -> None:
        """Track performance of a prompt."""
        if prompt_type not in self.performance_data:
            self.performance_data[prompt_type] = []
        
        performance_entry = {
            'timestamp': datetime.now().isoformat(),
            'prompt_content': prompt_content,
            'result': result,
            'metrics': self.metrics_calculator.calculate_metrics(result)
        }
        
        self.performance_data[prompt_type].append(performance_entry)
    
    def get_performance_summary(self, prompt_type: str) -> Dict[str, Any]:
        """Get performance summary for a prompt type."""
        if prompt_type not in self.performance_data:
            return {}
        
        entries = self.performance_data[prompt_type]
        
        if not entries:
            return {}
        
        # Calculate summary statistics
        success_rate = sum(1 for entry in entries if entry['result'].get('success', False)) / len(entries)
        avg_response_time = sum(entry['metrics'].get('response_time', 0) for entry in entries) / len(entries)
        avg_quality_score = sum(entry['metrics'].get('quality_score', 0) for entry in entries) / len(entries)
        
        return {
            'total_executions': len(entries),
            'success_rate': success_rate,
            'average_response_time': avg_response_time,
            'average_quality_score': avg_quality_score,
            'recent_trend': self._calculate_trend(entries[-10:])  # Last 10 entries
        }
    
    def _calculate_trend(self, recent_entries: List[Dict[str, Any]]) -> str:
        """Calculate performance trend from recent entries."""
        if len(recent_entries) < 2:
            return "insufficient_data"
        
        recent_success_rate = sum(1 for entry in recent_entries if entry['result'].get('success', False)) / len(recent_entries)
        older_entries = recent_entries[:-5] if len(recent_entries) > 5 else recent_entries[:-1]
        older_success_rate = sum(1 for entry in older_entries if entry['result'].get('success', False)) / len(older_entries)
        
        if recent_success_rate > older_success_rate + 0.1:
            return "improving"
        elif recent_success_rate < older_success_rate - 0.1:
            return "declining"
        else:
            return "stable"

class PromptMetricsCalculator:
    """Calculates metrics for prompt performance."""
    
    def calculate_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics from result."""
        metrics = {
            'response_time': result.get('execution_time', 0),
            'success': result.get('success', False),
            'quality_score': 0.0,
            'user_satisfaction': 0.0
        }
        
        # Calculate quality score based on result content
        if result.get('success'):
            metrics['quality_score'] = self._calculate_quality_score(result)
        
        # Calculate user satisfaction (if available)
        if 'user_feedback' in result:
            metrics['user_satisfaction'] = result['user_feedback'].get('satisfaction_score', 0.0)
        
        return metrics
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """Calculate quality score based on result content."""
        # This would implement quality scoring logic
        # For now, return a simple score
        return 0.8 if result.get('success') else 0.0
```

## Configuration and Examples

```python
# PromptEngineer Configuration
prompt_config = {
    'max_context_length': 4000,
    'temperature': 0.7,
    'evolution_rate': 0.1,
    'adaptation_threshold': 0.8,
    'variant_count': 3,
    'performance_window': 100,  # Number of executions to consider
    'learning_rate': 0.01
}

# Example usage
def create_coding_agent_prompt_engineer():
    """Create a PromptEngineer for coding agent."""
    config = {
        'max_context_length': 6000,
        'temperature': 0.3,  # Lower temperature for code generation
        'evolution_rate': 0.05,
        'templates': CODING_AGENT_TEMPLATES
    }
    
    return PromptEngineer('coding', config)

def create_financial_analyst_prompt_engineer():
    """Create a PromptEngineer for financial analyst."""
    config = {
        'max_context_length': 4000,
        'temperature': 0.5,
        'evolution_rate': 0.1,
        'templates': FINANCIAL_ANALYST_TEMPLATES
    }
    
    return PromptEngineer('financial_analyst', config)
```

## Error Handling

```python
class PromptError(Exception):
    """Base exception for prompt-related errors."""
    pass

class TemplateNotFoundError(PromptError):
    """Exception raised when template not found."""
    pass

class PromptGenerationError(PromptError):
    """Exception raised when prompt generation fails."""
    pass

class EvolutionError(PromptError):
    """Exception raised when prompt evolution fails."""
    pass
```
