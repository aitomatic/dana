# CORRAL Actor Interface Specification

## Overview

The `CorralActor` mixin provides a standardized interface for Dana agents to utilize the CORRAL knowledge lifecycle. This mixin can be applied to `AgentInstance` to add comprehensive knowledge management capabilities while maintaining compatibility with existing agent functionality.

## Interface Design Philosophy

### Principles
- **Seamless Integration**: Works with existing AgentInstance without breaking changes
- **Progressive Enhancement**: Agents can adopt CORRAL capabilities incrementally
- **Dana Alignment**: Fully integrated with Resources, Workflows, and ContextEngine
- **Performance Aware**: Optimized for real-time agent operation
- **Extensible**: Support for custom knowledge types and operations

### Usage Pattern
```python
from dana.frameworks.corral import CorralActor
from dana.core.agent import AgentInstance

class EnhancedAgent(AgentInstance, CorralActor):
    """Agent with CORRAL knowledge capabilities"""
    pass

# Or apply as mixin to existing agents
agent = AgentInstance(agent_type, values)
CorralActor.apply_to_instance(agent)  # Dynamic mixin application
```

## Core Interface Methods

### Knowledge Lifecycle Operations

#### Curate
```python
def curate_knowledge(self, 
    source: Union[str, Resource, Workflow, Interaction],
    context: Optional[Dict[str, Any]] = None,
    quality_threshold: float = 0.7,
    auto_categorize: bool = True
) -> CurationResult:
    """
    Curate knowledge from various sources.
    
    Args:
        source: Information source (text, resource, workflow result, etc.)
        context: Additional context for curation
        quality_threshold: Minimum quality score for acceptance
        auto_categorize: Whether to automatically categorize curated knowledge
        
    Returns:
        CurationResult with curated knowledge items and metadata
    """

def curate_from_interaction(self,
    user_query: str,
    agent_response: str, 
    outcome: Outcome,
    user_feedback: Optional[Feedback] = None
) -> CurationResult:
    """Curate knowledge from agent-user interactions."""

def curate_from_workflow_execution(self,
    workflow: Workflow,
    execution_result: ExecutionResult,
    performance_metrics: Optional[Dict[str, float]] = None
) -> CurationResult:
    """Learn from workflow execution outcomes."""
```

#### Organize
```python
def organize_knowledge(self,
    knowledge_items: List[Knowledge],
    categories: Optional[List[KnowledgeCategory]] = None,
    create_relationships: bool = True,
    update_indices: bool = True
) -> OrganizationResult:
    """
    Organize knowledge into structured, indexed form.
    
    Args:
        knowledge_items: Raw or partially structured knowledge
        categories: Target categories (auto-detected if None)
        create_relationships: Whether to establish cross-references
        update_indices: Whether to update search indices
        
    Returns:
        OrganizationResult with structured knowledge graph
    """

def categorize_knowledge(self,
    knowledge: Knowledge,
    confidence_threshold: float = 0.8
) -> KnowledgeCategory:
    """Automatically categorize knowledge into CORRAL taxonomy."""

def establish_relationships(self,
    new_knowledge: Knowledge,
    existing_knowledge: Optional[List[Knowledge]] = None
) -> List[KnowledgeRelationship]:
    """Create relationships between knowledge items."""
```

#### Retrieve
```python
def retrieve_knowledge(self,
    query: Union[str, Query, ProblemContext],
    categories: Optional[List[KnowledgeCategory]] = None,
    context: Optional[Dict[str, Any]] = None,
    max_results: int = 10,
    min_confidence: float = 0.5
) -> RetrievalResult:
    """
    Retrieve relevant knowledge for current needs.
    
    Args:
        query: Search query or problem context
        categories: Specific knowledge categories to search
        context: Additional context for relevance scoring
        max_results: Maximum number of results to return
        min_confidence: Minimum confidence threshold
        
    Returns:
        RetrievalResult with ranked, relevant knowledge
    """

def retrieve_for_problem(self,
    problem_context: ProblemContext
) -> ProblemRelevantKnowledge:
    """Get knowledge specifically relevant to current problem."""

def retrieve_analogous_situations(self,
    current_context: Context,
    similarity_threshold: float = 0.7
) -> List[AnalogousSituation]:
    """Find similar past situations and their outcomes."""
```

#### Reason
```python
def reason_with_knowledge(self,
    knowledge_set: List[Knowledge],
    problem: Union[str, ProblemContext],
    reasoning_type: Optional[ReasoningType] = None
) -> ReasoningResult:
    """
    Apply reasoning to knowledge for problem solving.
    
    Args:
        knowledge_set: Available knowledge for reasoning
        problem: Problem to solve or question to answer
        reasoning_type: Specific type of reasoning (causal, analogical, etc.)
        
    Returns:
        ReasoningResult with conclusions and reasoning trace
    """

def explain_decision(self,
    decision: Decision,
    knowledge_used: List[Knowledge]
) -> Explanation:
    """Generate explanation for agent decisions using causal knowledge."""

def predict_outcomes(self,
    proposed_action: Action,
    context: Context
) -> List[PredictedOutcome]:
    """Predict likely outcomes of proposed actions."""
```

#### Act
```python
def act_on_knowledge(self,
    reasoning_result: ReasoningResult,
    execution_context: Optional[ExecutionContext] = None
) -> ActionResult:
    """
    Convert reasoning results into executable actions.
    
    Args:
        reasoning_result: Output from reasoning process
        execution_context: Context for action execution
        
    Returns:
        ActionResult with executed actions and outcomes
    """

def recommend_workflow(self,
    problem: str,
    available_resources: Optional[List[Resource]] = None
) -> WorkflowRecommendation:
    """Recommend workflows based on procedural knowledge."""

def suggest_resources(self,
    problem_context: ProblemContext
) -> ResourceSuggestion:
    """Suggest relevant resources based on declarative knowledge."""
```

#### Learn
```python
def learn_from_outcome(self,
    knowledge_used: List[Knowledge],
    action_taken: Action,
    outcome: Outcome,
    context: Context
) -> LearningResult:
    """
    Update knowledge based on action outcomes.
    
    Args:
        knowledge_used: Knowledge that informed the action
        action_taken: Action that was executed
        outcome: Result of the action
        context: Situational context
        
    Returns:
        LearningResult with knowledge updates and insights
    """

def update_knowledge_confidence(self,
    knowledge_items: List[Knowledge],
    validation_results: List[ValidationResult]
) -> ConfidenceUpdateResult:
    """Update confidence scores based on validation results."""

def discover_patterns(self,
    experience_history: List[Experience],
    pattern_types: Optional[List[PatternType]] = None
) -> List[DiscoveredPattern]:
    """Discover new patterns from accumulated experience."""
```

### Complete Cycle Operations

#### CORRAL Cycle Execution
```python
def execute_corral_cycle(self,
    problem: Union[str, ProblemContext],
    initial_knowledge: Optional[List[Knowledge]] = None,
    cycle_config: Optional[CORRALConfig] = None
) -> CORRALResult:
    """
    Execute complete CORRAL cycle for problem solving.
    
    Args:
        problem: Problem to solve using CORRAL
        initial_knowledge: Starting knowledge (if any)
        cycle_config: Configuration for cycle execution
        
    Returns:
        CORRALResult with complete cycle outcome and learned knowledge
    """

def continuous_corral(self,
    problem_stream: Iterator[ProblemContext],
    learning_rate: float = 0.1
) -> Iterator[CORRALResult]:
    """Execute CORRAL continuously on stream of problems."""
```

### Integration with Dana Architecture

#### AgentState Integration
```python
def get_knowledge_state(self) -> KnowledgeState:
    """Get current knowledge state for integration with AgentState."""

def set_knowledge_state(self, knowledge_state: KnowledgeState) -> None:
    """Set knowledge state from AgentState."""

def sync_with_agent_mind(self) -> None:
    """Synchronize CORRAL knowledge with AgentMind memory systems."""
```

#### ContextEngine Integration
```python
def contribute_to_context(self,
    problem_context: ProblemContext,
    context_depth: str = "standard"
) -> Dict[str, Any]:
    """Contribute knowledge-based context to ContextEngine."""

def assess_context_needs(self,
    problem: ProblemContext,
    template: str
) -> ContextNeeds:
    """Assess what knowledge would improve context assembly."""
```

#### Resource and Workflow Integration
```python
def enhance_resource_discovery(self,
    resource_query: ResourceQuery
) -> EnhancedResourceResult:
    """Use relational knowledge to improve resource discovery."""

def optimize_workflow_selection(self,
    workflow_candidates: List[Workflow],
    context: Context
) -> WorkflowOptimization:
    """Use procedural knowledge to optimize workflow selection."""
```

## Configuration and Customization

### CORRAL Configuration
```python
@dataclass
class CORRALConfig:
    # Curation settings
    curation_sources: List[SourceType] = field(default_factory=lambda: ['interaction', 'workflow', 'resource'])
    quality_threshold: float = 0.7
    auto_validation: bool = True
    
    # Organization settings
    auto_categorization: bool = True
    relationship_discovery: bool = True
    indexing_strategy: IndexingStrategy = IndexingStrategy.MULTI_DIMENSIONAL
    
    # Retrieval settings
    max_retrieval_results: int = 10
    min_confidence_threshold: float = 0.5
    context_window: int = 5  # Number of related knowledge items to include
    
    # Reasoning settings
    reasoning_types: List[ReasoningType] = field(default_factory=lambda: ['causal', 'analogical'])
    explanation_depth: ExplanationDepth = ExplanationDepth.STANDARD
    confidence_propagation: bool = True
    
    # Action settings
    action_execution_mode: ActionMode = ActionMode.INTEGRATED  # vs STANDALONE
    fallback_strategies: bool = True
    risk_assessment: bool = True
    
    # Learning settings
    learning_rate: float = 0.1
    pattern_discovery: bool = True
    knowledge_pruning: bool = True
    meta_learning: bool = True
```

### Custom Extensions
```python
class CustomCorralActor(CorralActor):
    """Example of extending CORRAL with domain-specific capabilities"""
    
    def curate_domain_specific_knowledge(self, domain_data: DomainData) -> CurationResult:
        """Custom curation for specific domain"""
        pass
        
    def reason_with_domain_rules(self, knowledge: List[Knowledge], domain_context: DomainContext) -> ReasoningResult:
        """Custom reasoning using domain-specific rules"""
        pass
```

## Performance Considerations

### Optimization Strategies
- **Lazy Loading**: Load detailed knowledge only when needed
- **Caching**: Cache frequently accessed knowledge and results
- **Parallel Processing**: Execute CORRAL operations concurrently where possible
- **Incremental Updates**: Update knowledge incrementally rather than rebuilding
- **Smart Indexing**: Use appropriate indices for common query patterns

### Resource Management
```python
def optimize_knowledge_storage(self) -> OptimizationResult:
    """Optimize knowledge storage based on usage patterns."""

def manage_knowledge_lifecycle(self) -> LifecycleResult:
    """Archive old knowledge, promote frequently used knowledge."""

def monitor_performance_metrics(self) -> PerformanceMetrics:
    """Track CORRAL operation performance for optimization."""
```

## Error Handling and Resilience

### Error Recovery
```python
def handle_curation_errors(self, error: CurationError) -> RecoveryAction:
    """Handle errors in knowledge curation process."""

def handle_reasoning_failures(self, error: ReasoningError) -> FallbackReason:
    """Provide fallback reasoning when primary reasoning fails."""

def validate_knowledge_integrity(self) -> IntegrityReport:
    """Check and repair knowledge base integrity."""
```

### Graceful Degradation
- **Partial Knowledge**: Operate with incomplete knowledge when necessary
- **Confidence Awareness**: Acknowledge and communicate uncertainty
- **Fallback Modes**: Provide alternative approaches when CORRAL components fail
- **User Notification**: Inform users when knowledge-based features are degraded

## Usage Examples

### Basic Usage
```python
# Create CORRAL-enabled agent
agent = EnhancedAgent(agent_type, values)

# Execute complete CORRAL cycle
problem = "Deploy microservice with zero downtime"
result = agent.execute_corral_cycle(problem)

# Access learned knowledge
knowledge_gained = result.knowledge_updates
confidence_improvements = result.confidence_changes
```

### Advanced Usage
```python
# Custom CORRAL configuration
config = CORRALConfig(
    quality_threshold=0.8,
    reasoning_types=['causal', 'analogical', 'temporal'],
    learning_rate=0.2
)

# Execute with custom config
result = agent.execute_corral_cycle(problem, cycle_config=config)

# Continuous learning from problem stream
for corral_result in agent.continuous_corral(problem_stream):
    if corral_result.confidence_improvement > threshold:
        agent.consolidate_knowledge(corral_result.knowledge_updates)
```

### Integration with Existing Agent Methods
```python
# Enhanced solve method using CORRAL
class CORRALEnhancedAgent(AgentInstance, CorralActor):
    
    def solve_sync(self, problem: str, **kwargs) -> Any:
        # Use CORRAL to enhance problem solving
        corral_result = self.execute_corral_cycle(problem)
        
        # Use CORRAL insights for workflow selection
        workflow_rec = self.recommend_workflow(problem)
        
        # Execute enhanced workflow
        enhanced_kwargs = {**kwargs, 'corral_insights': corral_result.insights}
        return super().solve_sync(workflow_rec.workflow, **enhanced_kwargs)
```