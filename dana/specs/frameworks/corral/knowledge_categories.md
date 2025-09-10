# CORRAL Knowledge Categories

## Category Taxonomy

The CORRAL framework organizes knowledge into five primary categories designed to align with Dana's resource/workflow architecture and provide comprehensive coverage of agent understanding needs.

## 1. Declarative Knowledge (Whats/Facts)

### Definition
Static, factual knowledge about entities, properties, and states in the world.

### Subcategories

#### Topical Knowledge
- **Domain Facts**: Technical specifications, business rules, scientific principles
- **Entity Properties**: Characteristics of objects, people, systems, concepts
- **Relationships**: Static connections between entities
- **Classifications**: Taxonomies, categorizations, type hierarchies

#### Contextual Knowledge
- **Environmental States**: Current conditions, system status, market conditions
- **Situational Facts**: Location-specific, time-specific, context-specific information
- **Configuration Data**: Settings, parameters, constraints, preferences

#### Factual Knowledge
- **Ground Truth**: Verified, authoritative information
- **Data Points**: Measurements, observations, recorded facts
- **Historical Records**: Past events, decisions, outcomes, baselines

### Storage Schema
```python
@dataclass
class DeclarativeKnowledge:
    entity: str
    property: str  
    value: Any
    confidence: float
    source: str
    timestamp: datetime
    context: Dict[str, Any]
    validation_history: List[ValidationEvent]
```

### Dana Integration
- **Resources**: Declarative knowledge describes what resources are and their properties
- **Context Assembly**: Facts inform ContextEngine about current state
- **Decision Support**: Provides factual foundation for reasoning

## 2. Procedural Knowledge (Hows/Methods)

### Definition
Knowledge about how to perform tasks, execute processes, and achieve goals.

### Subcategories

#### Workflow Knowledge
- **Process Steps**: Sequential procedures, algorithms, methodologies
- **Task Decomposition**: How to break complex problems into subtasks
- **Execution Patterns**: Common workflow templates and variations
- **Orchestration**: How to coordinate multiple processes

#### Skills Knowledge
- **Competencies**: Learned abilities and their proficiency levels
- **Techniques**: Specific methods for achieving outcomes
- **Best Practices**: Optimized approaches based on experience
- **Tool Usage**: How to effectively use resources and capabilities

#### Pattern Knowledge
- **Solution Templates**: Reusable approaches for common problems
- **Adaptation Strategies**: How to modify procedures for different contexts
- **Optimization Methods**: How to improve efficiency and effectiveness
- **Error Recovery**: How to handle failures and exceptions

### Storage Schema
```python
@dataclass
class ProceduralKnowledge:
    procedure_name: str
    steps: List[ProcedureStep]
    preconditions: List[Condition]
    postconditions: List[Condition]
    success_rate: float
    efficiency_metrics: Dict[str, float]
    context_requirements: List[str]
    variations: List[ProcedureVariation]
```

### Dana Integration
- **Workflows**: Procedural knowledge directly maps to Dana workflows
- **Strategy Selection**: Guides choice of problem-solving approaches
- **Capability Discovery**: Informs what the agent can do

## 3. Causal Knowledge (Whys/Reasoning)

### Definition
Knowledge about cause-effect relationships, explanations, and predictive understanding.

### Subcategories

#### Causal Relationships
- **Direct Causation**: A directly causes B
- **Indirect Causation**: A causes B through intermediate factors
- **Conditional Causation**: A causes B only under certain conditions
- **Probabilistic Causation**: A increases likelihood of B

#### Explanatory Knowledge
- **Mechanisms**: How and why causal relationships work
- **Justifications**: Reasons behind decisions and rules
- **Root Causes**: Fundamental factors underlying effects
- **Dependencies**: What factors influence what outcomes

#### Predictive Knowledge
- **Outcome Models**: Expected results of actions
- **Risk Assessment**: Potential negative consequences
- **Scenario Planning**: Multiple possible futures
- **Confidence Intervals**: Uncertainty in predictions

### Storage Schema
```python
@dataclass
class CausalKnowledge:
    cause: str
    effect: str
    mechanism: str
    conditions: List[Condition]
    strength: float  # How strong the causal relationship is
    confidence: float  # How certain we are about this relationship
    supporting_evidence: List[Evidence]
    counter_evidence: List[Evidence]
```

### Dana Integration
- **Decision Explanation**: Provides reasoning behind agent choices
- **Risk Assessment**: Predicts consequences of proposed actions
- **Learning**: Enables understanding of why things worked or failed

## 4. Relational Knowledge (Whos/Wheres/Structure)

### Definition
Knowledge about relationships, structures, networks, and positional information.

### Subcategories

#### Social Knowledge
- **People**: Individuals, their roles, expertise, preferences
- **Organizations**: Structure, hierarchy, culture, processes
- **Authority**: Who has decision-making power in what contexts
- **Collaboration**: How people and teams work together effectively

#### Spatial Knowledge
- **Geography**: Physical locations, layouts, navigation
- **Topology**: Network structures, connectivity, adjacency
- **Hierarchies**: Organizational, technical, conceptual structures
- **Boundaries**: What belongs where, access controls, scope limits

#### Network Knowledge
- **Connections**: Relationships between entities
- **Dependencies**: What relies on what
- **Communication**: How information flows between entities
- **Influence**: How entities affect each other

### Storage Schema
```python
@dataclass
class RelationalKnowledge:
    entity1: str
    entity2: str
    relationship_type: str
    relationship_properties: Dict[str, Any]
    bidirectional: bool
    strength: float
    context_dependent: bool
    temporal_aspects: Dict[str, Any]
```

### Dana Integration
- **Resource Discovery**: Finds related resources through relationships
- **Context Understanding**: Provides social and structural context
- **Workflow Routing**: Knows who to involve and how to reach them

## 5. Conditional Knowledge (Whens/Context)

### Definition
Knowledge about when, where, and under what circumstances other knowledge applies.

### Subcategories

#### Temporal Knowledge
- **Schedules**: When things happen, availability, deadlines
- **Sequences**: Order dependencies, timing requirements
- **History**: Past events, trends, patterns over time
- **Lifecycle**: How things change over time

#### Situational Knowledge
- **Context Dependencies**: When knowledge/procedures apply
- **Triggers**: Events that activate certain behaviors
- **Conditions**: Prerequisites, environmental factors
- **Exceptions**: When normal rules don't apply

#### Adaptive Knowledge
- **Dynamic Rules**: Knowledge that changes based on circumstances
- **Contextual Variations**: How approaches differ by situation
- **Adaptation Strategies**: How to modify behavior for context
- **Learning Curves**: How performance changes with experience

### Storage Schema
```python
@dataclass
class ConditionalKnowledge:
    base_knowledge_id: str
    conditions: List[Condition]
    context_requirements: Dict[str, Any]
    validity_period: Optional[TimePeriod]
    confidence_modifiers: Dict[str, float]
    override_priority: int
    application_count: int
```

### Dana Integration
- **Context-Aware Execution**: Adapts behavior based on current situation
- **Dynamic Workflow Selection**: Chooses appropriate workflows for context
- **Temporal Reasoning**: Understands timing and sequencing requirements

## Cross-Category Relationships

### Knowledge Interaction Patterns
- **Declarative** feeds **Causal**: Facts enable reasoning about relationships
- **Procedural** uses **Conditional**: Methods adapt to context
- **Relational** informs **Causal**: Structure enables understanding of influence
- **All categories** inform **ContextEngine**: Comprehensive context for LLM prompting

### Retrieval Strategies
- **Multi-category Queries**: Retrieve related knowledge across categories
- **Hierarchical Retrieval**: Start with broad categories, drill down to specifics
- **Confidence-weighted Combination**: Blend knowledge based on reliability
- **Context-sensitive Ranking**: Prioritize based on current situation relevance

## Implementation Considerations

### Storage Efficiency
- **Deduplication**: Avoid storing same knowledge in multiple categories
- **Reference Linking**: Use relationships instead of duplication
- **Compression**: Optimize storage for frequently accessed knowledge
- **Archiving**: Move old, unused knowledge to cold storage

### Retrieval Performance
- **Indexing Strategy**: Multi-dimensional indices for fast access
- **Caching**: Keep frequently used knowledge in memory
- **Precomputation**: Calculate common query results in advance
- **Lazy Loading**: Load detailed knowledge only when needed

### Consistency Management
- **Conflict Detection**: Identify contradictory knowledge
- **Version Control**: Track knowledge evolution over time
- **Validation**: Continuously verify knowledge accuracy
- **Reconciliation**: Resolve conflicts through evidence weighting