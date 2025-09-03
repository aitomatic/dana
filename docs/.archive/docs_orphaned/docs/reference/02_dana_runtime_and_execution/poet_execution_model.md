| [← REPL](./repl.md) | [Code Context Analyzer →](./code_context_analyzer.md) |
|---|---|

# POET Execution Model

**Relevant Modules**:
- `opendxa.dana.poet.mvp_poet`: Core POET implementation
- `opendxa.dana.poet.domains`: Domain-specific POET plugins
- `opendxa.common.resource.llm_resource`: LLM integration

## 1. Overview

POET (Perceive-Operate-Encode-Transform) is an execution model that enhances Dana functions with AI-powered domain expertise. It provides a structured approach to integrating Large Language Models (LLMs) and domain knowledge into Dana program execution.

The POET model operates through a four-phase cycle that transforms data and reasoning through domain-specific intelligence:

1. **Perceive**: Understand and contextualize input data
2. **Operate**: Apply domain-specific operations and logic
3. **Encode**: Structure and format results appropriately  
4. **Transform**: Adapt output for downstream consumption

## 2. POET-Enhanced Functions

Functions decorated with POET capabilities follow the standard Dana function signature but gain access to domain expertise through the POET execution context.

### Basic POET Function Pattern

```dana
@poet(domain="financial_analysis")
def analyze_market_data(data: dict) -> dict:
    # Standard Dana code with POET context available
    analysis = reason(
        "Analyze market trends and provide insights",
        context=data,
        temperature=0.3
    )
    
    return {
        "analysis": analysis,
        "confidence": calculate_confidence(analysis),
        "recommendations": generate_recommendations(analysis)
    }
```

### POET Context Access

Within POET-enhanced functions, the execution context provides:

- **Domain Knowledge**: Access to domain-specific expertise
- **LLM Integration**: Structured reasoning capabilities
- **Context Management**: Automatic context scoping and cleanup
- **Resource Management**: Efficient resource allocation and cleanup

```dana
def poet_enhanced_function(input_data: dict) -> dict:
    # Access POET status and context
    poet_status = get_poet_status()
    
    # Domain-specific reasoning
    if poet_status.domain == "healthcare":
        result = reason(
            "Analyze medical data following healthcare protocols",
            context=input_data,
            domain_context=poet_status.domain_context
        )
    else:
        result = reason(
            "Perform general analysis",
            context=input_data
        )
    
    return result
```

## 3. Domain Plugin Architecture

POET domains provide specialized knowledge and capabilities for specific industries or use cases.

### Available Domains

- **financial_services**: Financial analysis, risk assessment, compliance
- **healthcare**: Medical data analysis, diagnosis support, protocol compliance
- **manufacturing**: Process optimization, quality control, predictive maintenance
- **general**: Generic domain for general-purpose tasks

### Domain Context Structure

```dana
struct DomainContext:
    domain_name: str
    expertise_areas: list
    compliance_requirements: list
    data_schemas: dict
    processing_rules: dict
    
struct POETStatus:
    domain: str
    context: DomainContext
    execution_phase: str  # "perceive", "operate", "encode", "transform"
    retry_count: int
    last_error: str
```

## 4. Execution Flow

### Phase 1: Perceive
- Input validation and contextualization
- Domain-specific data interpretation
- Context preparation for reasoning

### Phase 2: Operate  
- Core domain logic execution
- LLM-powered reasoning and analysis
- Business rule application

### Phase 3: Encode
- Result structuring and validation
- Domain-specific formatting
- Compliance checking

### Phase 4: Transform
- Output adaptation for consumers
- Format conversion and optimization
- Context cleanup

### Example Execution Trace

```dana
# Input processing through POET phases
def risk_assessment(portfolio: dict) -> dict:
    # Phase 1: Perceive
    validated_data = validate_portfolio_structure(portfolio)
    market_context = gather_market_context()
    
    # Phase 2: Operate
    risk_analysis = reason(
        "Assess portfolio risk based on current market conditions",
        context=[validated_data, market_context],
        domain="financial_services"
    )
    
    # Phase 3: Encode
    structured_results = format_risk_report(risk_analysis)
    compliance_check = verify_regulatory_compliance(structured_results)
    
    # Phase 4: Transform
    final_report = generate_client_report(structured_results)
    
    return final_report
```

## 5. Error Handling and Retry Logic

POET functions include sophisticated error handling with domain-aware retry strategies:

```dana
def robust_poet_function(data: dict) -> dict:
    poet_status = get_poet_status()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            result = execute_domain_logic(data)
            return result
        except DomainError as e:
            log(f"Domain error on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                # Apply domain-specific recovery strategy
                data = apply_error_recovery(data, e, poet_status.domain)
            else:
                raise e
    
    raise MaxRetriesExceeded(f"Failed after {max_retries} attempts")
```

## 6. Resource Management

POET execution includes automatic resource management:

- **LLM Connection Pooling**: Efficient reuse of LLM connections
- **Context Scoping**: Automatic cleanup of temporary contexts
- **Memory Management**: Optimization for large-scale processing
- **Cache Management**: Intelligent caching of domain knowledge

## 7. Integration with Dana Interpreter

POET functions integrate seamlessly with the Dana interpreter:

- Function calls are transparent to the caller
- POET context is automatically managed
- Resource allocation follows Dana's sandbox model
- Error propagation follows Dana's exception handling

## 8. Performance Considerations

- **Lazy Loading**: Domain contexts loaded on-demand
- **Connection Reuse**: LLM connections pooled across function calls
- **Caching**: Intelligent caching of reasoning results
- **Batch Processing**: Optimized batch operations for large datasets

---

*Note: This document describes the conceptual POET execution model. Implementation details may vary based on the specific domain plugins and LLM integrations configured.* 