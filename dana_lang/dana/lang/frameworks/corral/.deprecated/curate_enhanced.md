# CORRAL Enhanced Curate API - Query-Driven Knowledge Curation

The Enhanced Curate API implements a sophisticated query-driven knowledge curation pipeline that optimizes knowledge curation based on runtime reasoning needs. This approach starts "from the end" by understanding what knowledge is needed for specific queries and works backwards to curate the right knowledge efficiently.

## **Pipeline Architecture**

The system implements three levels of sophistication, eliminating the naive RAG-only approach. All pipelines use Dana's native pipeline notation with explicit `$` for clarity and are organized into meaningful sub-pipelines.

### **Sub-Pipelines**

The complex curation process is broken down into logical sub-pipelines:

#### **query_analysis_pipeline**
```dana
(query, domain) | task_intake(llm_assisted) | reasoning_blueprint_design(llm_assisted)
```
Analyzes the query and designs the reasoning approach.

#### **knowledge_retrieval_pipeline**
```dana
$ | retrieval_pattern_design(llm_assisted) | structure_scoring(sources, llm_assisted)
```
Designs retrieval patterns and scores knowledge structure.

#### **knowledge_synthesis_pipeline**
```dana
$ | gap_analysis(llm_assisted) | local_synthesis(learning_data, llm_assisted)
```
Analyzes gaps and synthesizes missing knowledge.

#### **knowledge_validation_pipeline**
```dana
$ | validation_gate(llm_assisted) | trust_tagging(llm_assisted) | canonical_synthesis(llm_assisted)
```
Validates, assesses trust, and synthesizes knowledge.

#### **context_optimization_pipeline**
```dana
$ | scoped_compilation(llm_assisted) | context_window_builder()
```
Optimizes knowledge for runtime reasoning.

### **Sub-Pipelines**

The complex curation process is broken down into logical sub-pipelines:

#### **query_analysis_pipeline**
```dana
query_analysis_pipeline = task_intake | reasoning_blueprint_design
```
Analyzes the query and designs the reasoning approach.
**Parameters**: `(query: str, domain: str)` (from `task_intake`)

#### **knowledge_retrieval_pipeline**
```dana
knowledge_retrieval_pipeline = retrieval_pattern_design | structure_scoring
```
Designs retrieval patterns and scores knowledge structure.
**Parameters**: `(sources: list)` (from `structure_scoring`)

#### **knowledge_synthesis_pipeline**
```dana
knowledge_synthesis_pipeline = gap_analysis | local_synthesis
```
Analyzes gaps and synthesizes missing knowledge.
**Parameters**: `(learning_data: dict)` (from `local_synthesis`)

#### **knowledge_validation_pipeline**
```dana
knowledge_validation_pipeline = validation_gate | trust_tagging | canonical_synthesis
```
Validates, assesses trust, and synthesizes knowledge.
**Parameters**: None (all functions take previous output)

#### **context_optimization_pipeline**
```dana
context_optimization_pipeline = scoped_compilation | context_window_builder
```
Optimizes knowledge for runtime reasoning.
**Parameters**: None (all functions take previous output)

### **Level 1: Query-aware RAG**
```dana
query_analysis_pipeline(query, domain) | reason_requirements() | 
store_selection_vector(sources) | compile_and_index() | build_context_bundle()
```
**Purpose**: Quick, query-aware knowledge retrieval without sophisticated synthesis.
**Suitable for**: Quick exploration, prototyping, simple queries.

### **Level 2: Local Synthesis (no external packs)**
```dana
query_analysis_pipeline(query, domain) | knowledge_retrieval_pipeline(sources) | 
knowledge_synthesis_pipeline(learning_data) | knowledge_validation_pipeline | 
context_optimization_pipeline
```
**Purpose**: Advanced knowledge curation with local synthesis of missing knowledge.
**Suitable for**: Production reasoning tasks, complex queries, when external knowledge unavailable.

### **Level 3: Pack-augmented, Bayesian-conditioned**
```dana
query_analysis_pipeline(query, domain) | knowledge_retrieval_pipeline(sources) | 
gap_analysis() | pack_acquisition(domain) | local_synthesis(learning_data) | 
knowledge_validation_pipeline | context_optimization_pipeline
```
**Purpose**: Maximum confidence by acquiring external knowledge packs for critical gaps.
**Suitable for**: Critical decisions, high-stakes queries, when maximum confidence required.

## **Core Philosophy**

### **Dana Pipeline Notation**
The enhanced curation system uses Dana's native pipeline notation:
- **Pipeline composition**: Steps are chained using the `|` operator
- **Data flow**: Each step transforms and passes data to the next step
- **Direct pipeline expressions**: Pipelines are defined as expressions, not functions
- **LLM Integration**: All steps use LLM assistance when possible for intelligent processing

#### **Example Pipeline Usage**
```dana
# Define a pipeline directly as an expression
pipeline = (input_data) | step1() | step2(param) | step3()

# Use within a function
def process_data(input_data, param):
    return (input_data) | step1() | step2(param) | step3()
```

### **Query-Driven Optimization**
Instead of generic knowledge curation, this system:
- **Anticipates** what knowledge will be needed for specific reasoning tasks
- **Structures** knowledge for optimal retrieval and reasoning
- **Validates** knowledge quality against specific query requirements
- **Packages** knowledge for efficient runtime consumption

### **Bayesian Role Assignment**
Each knowledge document is dynamically assigned Bayesian roles based on the specific query:
- **Priors**: Background knowledge and assumptions
- **Evidence**: Observations and data relevant to the query
- **Likelihood**: Models and patterns for interpreting evidence
- **Posteriors**: Updated beliefs after Bayesian inference

## **Getting Started**

### **Basic Usage**
```dana
# Level 1: Query-aware RAG
context = curate_knowledge_for_query(
    query="What causes pattern defects in layer 3?",
    domain="semiconductor manufacturing",
    sources=["./process_logs/", "./equipment_data/"],
    level=1
)

# Level 2: Local Synthesis
context = curate_knowledge_for_query(
    query="What causes pattern defects in layer 3?",
    domain="semiconductor manufacturing",
    sources=["./process_logs/", "./equipment_data/"],
    learning_data={"historical_patterns": [...]},
    level=2
)

# Level 3: Pack-augmented
context = curate_knowledge_for_query(
    query="What causes pattern defects in layer 3?",
    domain="semiconductor manufacturing",
    sources=["./process_logs/", "./equipment_data/"],
    learning_data={"historical_patterns": [...]},
    level=3
)
```

## **Pipeline Steps Explained**

### **1. Task Intake**
```dana
query_reqs = task_intake(query, domain, llm_assisted=True)
```
- Analyzes the query to extract requirements
- Identifies intent (analysis, diagnosis, planning, prediction)
- Determines reasoning type (causal, temporal, spatial, comparative)
- Establishes confidence thresholds and context scope

### **2. Reasoning Blueprint Design**
```dana
reasoning_blueprint = reasoning_blueprint_design(query_reqs, llm_assisted=True)
```
- Plans the reasoning steps needed to answer the query
- Designs knowledge patterns that support each reasoning step
- Creates inference chains and validation checkpoints
- Establishes confidence requirements for each step

### **3. Retrieval Pattern Design**
```dana
retrieval_patterns = retrieval_pattern_design(reasoning_blueprint, llm_assisted=True)
```
- Designs patterns for retrieving and structuring knowledge
- Identifies knowledge sources to query for each reasoning step
- Establishes relevance criteria and ranking factors
- Optimizes knowledge structure for reasoning efficiency

### **4. Structure Scoring**
```dana
structure_scores = structure_scoring(retrieval_patterns, sources, llm_assisted=True)
```
- Scores how well available knowledge supports the reasoning patterns
- Evaluates coverage completeness and structure alignment
- Assesses retrieval efficiency and reasoning support
- Identifies areas where knowledge structure needs improvement

### **5. Gap Analysis**
```dana
knowledge_gaps = gap_analysis(query_reqs, reasoning_blueprint, structure_scores, llm_assisted=True)
```
- Identifies missing knowledge for the reasoning task
- Categorizes gaps by type (missing evidence, incomplete chains, uncertain relationships)
- Assesses impact level (critical, important, nice-to-have)
- Suggests sources for filling gaps

### **6. Local Synthesis (Level 2) / Pack Acquisition (Level 3)**
```dana
# Level 2: Create missing knowledge locally
synthesized_knowledge = local_synthesis(knowledge_gaps, learning_data, llm_assisted=True)

# Level 3: Acquire external knowledge packs
external_packs = pack_acquisition(knowledge_gaps, domain, llm_assisted=True)
```

### **7. Validation Gate**
```dana
validated_knowledge = validation_gate(knowledge, query_reqs, llm_assisted=True)
```
- Validates knowledge quality against query requirements
- Checks relevance, accuracy, and completeness
- Ensures consistency with other knowledge
- Verifies confidence thresholds are met

### **8. Trust Tagging**
```dana
trust_assessments = trust_tagging(knowledge, llm_assisted=True)
```
- Assesses reliability and trustworthiness of knowledge
- Evaluates source reliability, content quality, and recency
- Checks consistency with other sources
- Applies trust tags (verified, experimental, anecdotal, etc.)

### **9. Canonical Synthesis**
```dana
canonical_knowledge = canonical_synthesis(validated_knowledge, trust_assessments, llm_assisted=True)
```
- Synthesizes knowledge into consistent, integrated form
- Resolves conflicts and inconsistencies
- Creates standardized knowledge representations
- Ensures knowledge is ready for reasoning

### **10. Scoped Compilation**
```dana
scoped_knowledge = scoped_compilation(canonical_knowledge, query_reqs, llm_assisted=True)
```
- Compiles knowledge scoped specifically to the query
- Selects only relevant knowledge for the reasoning task
- Optimizes knowledge organization for runtime efficiency
- Reduces context window size while maintaining completeness

### **11. Context Window Builder**
```dana
context_window = context_window_builder(scoped_knowledge, query_reqs, reasoning_blueprint)
```
- Assigns Bayesian roles to knowledge documents
- Estimates confidence for reasoning steps
- Checks reasoning readiness
- Packages knowledge for optimal runtime consumption

## **Data Structures**

### **QueryRequirements**
```dana
struct QueryRequirements:
    query: str
    intent: str  # "analysis", "diagnosis", "planning", "prediction"
    reasoning_type: str  # "causal", "temporal", "spatial", "comparative"
    knowledge_domains: list
    evidence_requirements: list
    confidence_threshold: float
    context_scope: dict
```

### **ReasoningBlueprint**
```dana
struct ReasoningBlueprint:
    reasoning_steps: list  # ["causal_analysis", "pattern_recognition", "root_cause_diagnosis"]
    knowledge_patterns: list
    inference_chains: list
    validation_checkpoints: list
    confidence_requirements: dict
```

### **ContextWindow**
```dana
struct ContextWindow:
    query: str
    reasoning_blueprint: ReasoningBlueprint
    curated_knowledge: list  # Knowledge documents with Bayesian roles
    confidence_estimates: dict
    reasoning_ready: bool
    optimization_metadata: dict
```

## **Advanced Usage Patterns**

### **Domain-Specific Reasoning**
```dana
# Semiconductor defect analysis with causal reasoning
context = curate_knowledge_for_query(
    query="What causes pattern defects in layer 3?",
    domain="semiconductor manufacturing",
    sources=["./process_logs/", "./equipment_data/"],
    level=2
)

# Banking fraud detection with temporal reasoning
context = curate_knowledge_for_query(
    query="Is this transaction sequence suspicious?",
    domain="retail banking",
    sources=["./transaction_logs/", "./customer_profiles/"],
    level=2
)
```

### **Multi-Step Reasoning**
```dana
# Complex reasoning requiring multiple steps
context = curate_knowledge_for_query(
    query="How can we optimize the manufacturing process to reduce defects while maintaining yield?",
    domain="semiconductor manufacturing",
    sources=["./process_logs/", "./equipment_data/", "./quality_reports/"],
    learning_data={"optimization_history": [...]},
    level=3
)
```

### **Confidence-Driven Curation**
```dana
# High-confidence requirements for critical decisions
context = curate_knowledge_for_query(
    query="Should we halt production due to quality concerns?",
    domain="semiconductor manufacturing",
    sources=["./quality_metrics/", "./process_parameters/"],
    level=3  # Use external packs for maximum confidence
)
```

## **Integration with Runtime Reasoning**

### **Context Window Usage**
```dana
# Get curated context for runtime reasoning
context = curate_knowledge_for_query(query, domain, sources, level=2)

# Check if ready for reasoning
if context.reasoning_ready:
    # Use context for Bayesian reasoning
    result = bayesian_reasoning(
        query=context.query,
        priors=extract_priors(context.curated_knowledge),
        evidence=extract_evidence(context.curated_knowledge),
        likelihood_models=extract_likelihood_models(context.curated_knowledge)
    )
else:
    print(f"Knowledge gaps detected: {context.confidence_estimates}")
```

### **Progressive Enhancement**
```dana
# Start with Level 1 for quick answers
context_l1 = curate_knowledge_for_query(query, domain, sources, level=1)

# Upgrade to Level 2 for better reasoning
if context_l1.confidence_estimates["overall"] < 0.8:
    context_l2 = curate_knowledge_for_query(query, domain, sources, learning_data, level=2)

# Use Level 3 for critical decisions
if critical_decision:
    context_l3 = curate_knowledge_for_query(query, domain, sources, learning_data, level=3)
```

## **Performance Optimization**

### **Caching and Reuse**
- Context windows can be cached for similar queries
- Knowledge synthesis results can be reused across queries
- External packs can be pre-loaded for common domains

### **Parallel Processing**
- Multiple pipeline steps can run in parallel where independent
- Knowledge gap analysis can trigger concurrent synthesis
- Trust assessment can run alongside validation

### **Incremental Updates**
- New knowledge can be incrementally integrated
- Confidence estimates can be updated based on feedback
- Reasoning blueprints can be refined over time

## **Best Practices**

1. **Start with Level 1** for quick exploration and prototyping
2. **Use Level 2** for production reasoning tasks with local knowledge
3. **Deploy Level 3** for critical decisions requiring external expertise
4. **Monitor confidence estimates** to identify knowledge gaps
5. **Validate reasoning readiness** before runtime execution
6. **Cache context windows** for similar queries to improve performance
7. **Iterate on reasoning blueprints** based on runtime feedback
8. **Maintain trust assessments** to ensure knowledge quality

## **Comparison with Standard CORRAL**

| Feature | Standard CORRAL | Enhanced CORRAL |
|---------|----------------|-----------------|
| **Approach** | Generic knowledge curation | Query-driven optimization |
| **Knowledge Types** | CK/DK/XK classification | Dynamic Bayesian role assignment |
| **Pipeline** | Simple extraction → synthesis | 11-step reasoning-optimized pipeline |
| **Confidence** | Basic quality metrics | Multi-dimensional confidence estimation |
| **Gap Analysis** | None | Systematic gap identification and filling |
| **Trust Assessment** | None | Comprehensive trust tagging |
| **External Integration** | None | External pack acquisition (Level 3) |
| **Runtime Optimization** | None | Context window optimization |

The Enhanced CORRAL provides sophisticated query-driven knowledge curation that optimizes for runtime reasoning accuracy and efficiency, while maintaining compatibility with the standard CORRAL approach. 