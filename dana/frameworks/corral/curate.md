# CORRAL Curate API - Knowledge Curation for Dana Programmers

The Curate phase extracts, organizes, and synthesizes knowledge from three types: Contextual Knowledge (CK), Documentary Knowledge (DK), and Experiential Knowledge (XK).

## Getting Started

```dana
# 1. Hiring a specialist - no sources needed
kb = curate_knowledge(
    domain="semiconductor manufacturing",
    task="defect analysis"
)

# 2. Basic usage with sources
kb = curate_knowledge(
    sources=["./docs/", "./data/"],
    domain="software development",
    task="knowledge extraction"
)
```

## Advanced Usage Patterns

### Domain-Specific Specialists
```dana
# Hire domain specialists using built-in knowledge
semiconductor_specialist = curate_semiconductor_knowledge(
    domain="semiconductor manufacturing and fabrication",
    task="defect analysis and quality control"
)

banking_specialist = curate_banking_knowledge(
    domain="retail banking and financial services", 
    task="fraud detection and risk management"
)

ic_design_specialist = curate_ic_design_knowledge(
    domain="integrated circuit design and verification",
    task="physical design optimization and DRC compliance"
)
```

### Complex Natural Language Context
```dana
# Rich domain and task descriptions
kb = curate_knowledge(
    sources=["./logs/", "./data/", "./reports/"],
    domain="SaaS customer support and product management",
    task="support ticket analysis with focus on onboarding issues and feature request prioritization"
)

# Multi-faceted banking context
kb = curate_knowledge(
    sources=["./transaction_logs/", "./customer_profiles/"],
    domain="retail banking and financial services",
    task="fraud detection with BSA/AML compliance monitoring and small business focus"
)
```

### Learning-Enhanced Knowledge
```dana
# Integrate experiential knowledge
kb = curate_knowledge(
    sources=["./transaction_logs/", "./customer_profiles/"],
    domain="consumer banking and fraud prevention",
    task="fraud detection with historical pattern analysis",
    learning_data={
        "fraud_patterns": [...],
        "detection_performance": [...],
        "expert_feedback": [...]
    }
)
```

### Domain-Specific with Sources
```dana
# Specialized functions with custom sources
defect_analysis = curate_semiconductor_knowledge(
    sources=["./process_logs/", "./equipment_data/", "./defect_maps/"],
    domain="semiconductor manufacturing and plasma etching",
    task="defect analysis on layer 3 with pattern recognition"
)

fraud_detection = curate_banking_knowledge(
    sources=["./transaction_logs/", "./customer_profiles/", "./risk_scores/"],
    domain="small business banking and risk management",
    task="fraud detection with enhanced monitoring and alerting"
)
```

### Error Handling Patterns
```dana
# Handle missing or invalid sources gracefully
kb = curate_knowledge(
    sources=["./valid.md", "./invalid.txt", "./missing.pdf"],
    domain="general documentation",
    task="knowledge extraction"
)

# Check for knowledge gaps
if kb.gaps:
    print(f"Knowledge gaps found: {len(kb.gaps)}")
```

### Integration Patterns
```dana
# Curate knowledge for full CORRAL pipeline
kb = curate_knowledge(
    sources=["./process_logs/", "./equipment_data/"],
    domain="semiconductor manufacturing",
    task="defect analysis"
)

# Pass to Organize phase
organized = organize_knowledge(kb.existing_knowledge, domain=kb.domain)

# Pass to Retrieve phase
context = retrieve_knowledge_context(
    "What causes pattern defects in layer 3?",
    domain=kb.domain,
    organized=organized
)
```

## Core API Functions

### 1. curate_knowledge_base
```dana
curate_knowledge_base(
    context: dict,
    sources: list,
    learning_data: dict = None,
    llm_assisted: bool = True)
    -> dict
```
Main entry point for curating the complete knowledge base.

**Parameters:**
- `context`: Dictionary with domain, task, and contextual factors
- `sources`: List of file paths to extract knowledge from
- `learning_data`: Optional dictionary with historical patterns and feedback
- `llm_assisted`: Whether to use LLM for intelligent curation (default: True)

**Returns:**
- Dictionary containing curated knowledge across all three types (CK, DK, XK)

**Example:**
```dana
context = {
    "domain": "semiconductor_fabrication",
    "task": "defect_analysis",
    "location": "fab_floor_3",
    "time_period": "last_30_days"
}

sources = ["./process_logs/", "./equipment_data/", "./defect_maps/"]
learning_data = {
    "historical_defects": [...],
    "process_improvements": [...],
    "expert_feedback": [...]
}

kb = curate_knowledge_base(context, sources, learning_data)

# Access different knowledge types
ck = kb["contextual_knowledge"]      # Context about fab operations
dk = kb["documentary_knowledge"]     # Process logs, equipment data
xk = kb["experiential_knowledge"]    # Learned defect patterns
insights = kb["synthesis_insights"]  # Cross-knowledge insights
```



## Domain-Specific Functions

### 2. curate_semiconductor_defect_analysis
```dana
curate_semiconductor_defect_analysis(
    sources: list,
    context: dict,
    learning_data: dict = None)
    -> dict
```
Specialized curation for semiconductor defect analysis.

**Example:**
```dana
context = {
    "location": "fab_floor_3",
    "time_period": "last_30_days",
    "equipment_type": "plasma_etch"
}

sources = ["./process_logs/", "./equipment_data/", "./defect_maps/"]
learning_data = {"historical_defects": [...], "process_improvements": [...]}

defect_analysis = curate_semiconductor_defect_analysis(sources, context, learning_data)
```

### 3. curate_banking_fraud_detection
```dana
curate_banking_fraud_detection(sources: list, context: dict, learning_data: dict = None) -> dict
```
Specialized curation for banking fraud detection.

**Example:**
```dana
context = {
    "user_role": "risk_analyst",
    "regulatory_requirements": ["BSA", "AML"],
    "customer_segment": "retail_banking"
}

sources = ["./transaction_logs/", "./customer_profiles/", "./risk_scores/"]
learning_data = {"fraud_patterns": [...], "false_positives": [...]}

fraud_detection = curate_banking_fraud_detection(sources, context, learning_data)
```

### 4. curate_ic_design_support
```dana
curate_ic_design_support(sources: list, context: dict, learning_data: dict = None) -> dict
```
Specialized curation for IC design customer support.

**Example:**
```dana
context = {
    "design_tool": "Cadence",
    "design_stage": "physical_design",
    "customer_tier": "enterprise"
}

sources = ["./support_tickets/", "./design_docs/", "./tool_documentation/"]
learning_data = {"common_issues": [...], "resolution_patterns": [...]}

design_support = curate_ic_design_support(sources, context, learning_data)
```

## Return Value Structure

### Knowledge Base Return Value
```dana
{
    "contextual_knowledge": {
        "domain": "semiconductor_fabrication",
        "task": "defect_analysis",
        "context_factors": {"location": "fab_floor_3", "time_period": "last_30_days"},
        "knowledge_requirements": {...},
        "extraction_conditions": {...},
        "synthesis_requirements": {...}
    },
    "documentary_knowledge": [
        {
            "source_id": "./process_logs/",
            "source_type": "document",
            "content": {...},
            "metadata": {...},
            "quality_metrics": {"completeness": 0.95, "accuracy": 0.98},
            "extraction_status": "completed"
        }
    ],
    "experiential_knowledge": [
        {
            "knowledge_id": "defect_pattern_001",
            "knowledge_type": "pattern",
            "confidence": 0.87,
            "learning_history": [...],
            "applicability_conditions": {...},
            "last_updated": "2024-01-01T00:00:00Z"
        }
    ],
    "synthesis_insights": {
        "cross_knowledge_patterns": [...],
        "recommendations": [...],
        "predictive_insights": [...],
        "knowledge_gaps": [...]
    },
    "curation_timestamp": "2024-01-01T00:00:00Z"
}
```



## Error Handling

The API handles errors gracefully:

```dana
# Invalid source paths are logged but don't stop processing
context = {"domain": "general", "task": "knowledge_extraction"}
sources = ["./valid.md", "./invalid.txt", "./missing.pdf"]
kb = curate_knowledge_base(context, sources)

# Check for failed extractions
failed_sources = [
    source for source in sources 
    if source not in [dk["source_id"] for dk in kb["documentary_knowledge"]]
]
if failed_sources:
    print(f"Failed to extract: {failed_sources}")

# Check for knowledge gaps
if kb["synthesis_insights"]["knowledge_gaps"]:
    print(f"Knowledge gaps found: {len(kb['synthesis_insights']['knowledge_gaps'])}")
```

## Integration with Other CORRAL Phases

```dana
# Curate knowledge for the full CORRAL pipeline
kb = curate_knowledge_base(context, sources, learning_data)

# Pass to Organize phase
organized = organize_knowledge(kb["documentary_knowledge"], domain=kb["contextual_knowledge"]["domain"])

# Pass to Retrieve phase
context = retrieve_knowledge_context(
    "What causes pattern defects in layer 3?", 
    domain=kb["contextual_knowledge"]["domain"], 
    organized=organized
)
```

## Best Practices

1. **Use Domain Context**: Always provide domain and task context for better curation
2. **Include Learning Data**: Add experiential knowledge when available for better insights
3. **Leverage Domain-Specific Functions**: Use specialized functions for known domains
4. **Monitor Knowledge Gaps**: Check synthesis insights for identified gaps
5. **Preserve Context**: Pass contextual knowledge to subsequent CORRAL phases
6. **Enable LLM Assistance**: Use LLM-assisted mode for intelligent curation
7. **Iterate with Feedback**: Use learning data to improve curation over time 