# CORRAL Framework - Complete Knowledge Lifecycle

## Overview

The CORRAL framework implements a complete knowledge lifecycle for Dana agents: **Curate → Organize → Retrieve → Reason → Act → Learn**. This framework enables agents to build, maintain, and continuously improve their knowledge through direct experience and outcome feedback.

## Core Concept

CORRAL creates a self-improving knowledge system where each problem-solving cycle makes the agent smarter, more accurate, and more effective. The framework integrates seamlessly with Dana's resource/workflow paradigm while building genuine understanding over time.

## Knowledge Categories

The framework organizes knowledge into five primary categories that align with Dana's architecture:

### 1. Declarative Knowledge (Whats/Facts)
- **Topical**: Domain facts, entities, relationships, properties
- **Contextual**: Situational knowledge, environmental states
- **Factual**: Ground truth, verified information, data points

### 2. Procedural Knowledge (Hows/Methods)
- **Workflows**: Step-by-step processes, algorithms, methods
- **Skills**: Learned capabilities, competencies, techniques
- **Patterns**: Recurring solution approaches, best practices

### 3. Causal Knowledge (Whys/Reasoning)
- **Causal**: Cause-effect relationships, dependencies, mechanisms
- **Explanatory**: Reasoning behind facts, justifications, rationales
- **Predictive**: Future implications, likely outcomes, scenarios

### 4. Relational Knowledge (Whos/Wheres/Structure)
- **Social**: People, roles, organizations, authority structures
- **Spatial**: Locations, geography, topology, layouts
- **Network**: Connections, relationships, hierarchies, dependencies

### 5. Conditional Knowledge (Whens/Context)
- **Temporal**: Time-based knowledge, schedules, sequences, history
- **Situational**: Context-dependent knowledge, conditions, triggers
- **Adaptive**: Dynamic knowledge that changes based on circumstances

## CORRAL Lifecycle Operations

### Curate (Input/Acquisition)
- Automatic extraction from agent interactions
- Learning from workflow execution outcomes
- Integration with external knowledge sources
- Active learning through strategic questioning

### Organize (Structure/Storage)
- Multi-dimensional knowledge graph organization
- Vector embeddings for semantic clustering
- Temporal versioning and confidence scoring
- Cross-cutting indices for efficient access

### Retrieve (Query/Access)
- Context-aware knowledge retrieval
- Multi-modal query processing
- Semantic similarity matching
- Graph traversal for connected knowledge

### Reason (Inference/Analysis)
- Causal chain inference
- Predictive outcome modeling
- Knowledge gap identification
- Analogical reasoning patterns

### Act (Application/Execution)
- Workflow recommendation based on procedural knowledge
- Resource suggestion from declarative knowledge
- Strategy adaptation using conditional knowledge
- Decision explanation through causal knowledge

### Learn (Feedback/Adaptation)
- Outcome-based confidence updates
- Pattern discovery from action results
- Causal model refinement
- Meta-learning optimization

## Integration with Dana Architecture

### Resource Alignment
- **Dana Resources (Whats)** ↔ **Declarative + Relational Knowledge**
- **Dana Workflows (Hows)** ↔ **Procedural + Conditional Knowledge**
- **Context/Reasoning** ↔ **Causal + Conditional Knowledge**

### Integration Points
- **AgentState**: Knowledge system as part of centralized agent mind
- **ContextEngine**: Knowledge informs optimal LLM context assembly
- **Workflow System**: Procedural knowledge guides workflow selection
- **Resource Discovery**: Declarative knowledge suggests relevant resources

## CorralActor Mixin

The `CorralActor` mixin provides the interface for agents to utilize the CORRAL knowledge lifecycle:

```python
class CorralActor:
    """Mixin that adds CORRAL knowledge capabilities to agents"""
    
    def curate_knowledge(self, source, context=None)
    def organize_knowledge(self, knowledge, categories)  
    def retrieve_knowledge(self, query, context=None)
    def reason_with_knowledge(self, knowledge, problem)
    def act_on_knowledge(self, reasoning_result)
    def learn_from_outcome(self, knowledge_used, outcome)
    
    def execute_corral_cycle(self, problem)  # Complete cycle
```

## Benefits

1. **Continuous Improvement**: Each interaction makes the agent more capable
2. **Transparent Reasoning**: Causal knowledge enables explanation of decisions
3. **Context Awareness**: Knowledge retrieval adapts to current situation
4. **Failure Learning**: Mistakes become learning opportunities
5. **Knowledge Transfer**: Insights from one domain inform others
6. **Adaptive Behavior**: Agent behavior evolves based on experience

## Implementation Architecture

The CORRAL framework consists of:
- **Knowledge Storage**: Multi-dimensional knowledge graph
- **Reasoning Engine**: Inference and analysis capabilities
- **Learning Engine**: Outcome-based knowledge updates
- **Integration Layer**: Seamless Dana architecture integration
- **Actor Mixin**: Simple interface for agent integration