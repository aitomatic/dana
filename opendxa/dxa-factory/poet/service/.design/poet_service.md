# POET Code Generation Service - 3D Design Document

```text
Author: Christopher Nguyen
Date: 2025-06-13
Version: 0.5
Status: Design Phase
```

**Related Documents:**
- [POET Framework Design](../../../../dana/poet/.design/poet.md)
- [PubSub Service Design](../../../../common/pubsub/.design/pubsub.md)

## 3D Methodology Status

**Phase**: ✅ Design Complete → 🔄 Implementation → ⏳ Testing → ⏳ Deployment

**Design Quality Gate**: ✅ PASSED
- ✅ Problem statement clearly defined
- ✅ Solution architecture specified
- ✅ API design with OpenAPI specification
- ✅ Implementation plan with phases
- ✅ Success criteria defined
- ✅ Security and performance requirements

## Executive Summary

The POET Code Generation Service is an LLM-powered transpiler that receives complete function code (including @poet decorators) and generates full POET implementations. It parses decorator parameters, transforms the original function into an enhanced O' phase, and generates complete P→O'→E→T implementations.

**Key Innovation**: Acts as a true transpiler that receives decorated function code with full context (imports, SandboxContext) and returns complete POET implementations where the original function is transformed into an enhanced O' phase that maintains the user's intent while integrating seamlessly with POET architecture.

## Goals
- Transform simple functions into production-ready implementations
- Generate P→O→E phases for all functions (built-in reliability)
- Generate Train phase only when optimize_for is specified
- Provide domain-specific optimization through templates
- Support zero-config reliability with automatic P→O→E phases

## Non-Goals
- ❌ Execute POET functions (handled by Dana runtime)
- ❌ Manage function state (handled by client-side storage)
- ❌ Handle feedback processing (handled by PubSub system)
- ❌ Custom LLM model training
- ❌ Complex plugin architecture (using simple templates)

## Problem Statement

### Current Challenge
Building production-ready functions requires:
- Manual implementation of error handling, retries, timeouts
- Complex monitoring and feedback collection systems
- Domain-specific optimization that takes weeks to implement
- Slow iteration when requirements change
- No learning mechanism to improve over time

The POET service addresses this by:
- Automatically generating P→O→E phases for reliability
- Conditionally adding Train phase when optimize_for is specified
- Using domain templates for specialized enhancements
- Enabling zero-config production readiness

### User Needs
1. **Dana Runtime**: Needs to transpile @poet decorated functions into executable POET implementations
2. **Developers**: Need functions automatically enhanced without manual reliability engineering
3. **Domain Experts**: Need domain-specific intelligence added to their functions

## Solution Architecture

### Key Design Principle: Progressive Enhancement

### POET Transpilation Process

The service operates as a transpiler:

1. **Receives Complete Function Code**: Full function text including @poet decorator
2. **Parses Decorator**: Extracts parameters (domain, optimize_for, etc.)
3. **Transforms Original into O'**: User's function is redesigned to maintain intent while integrating with POET architecture
4. **Generates Full Implementation**: Creates P→O'→E(→T) with transformed user logic

**Input Example**:
```python
# Complete function code sent to service:
@poet(domain="ml_monitoring", optimize_for="accuracy")
def detect_drift(current_data, reference_data):
    return {"drift_detected": False, "score": 0.0}
```

**Output**: Complete POET implementation with:
- **P**: Input validation based on function signature
- **O'**: User's `detect_drift` logic completely transformed with:
  * ML monitoring domain enhancements (statistical tests, adaptive windowing)
  * POET integration facilities (error handling, metrics, state management)
  * Same logical intent but redesigned for POET architecture
- **E**: Output validation for drift detection format
- **T**: Accuracy optimization feedback collection (because optimize_for="accuracy")

The service receives context including imports, SandboxContext, and module information to generate appropriate implementations.

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    POET Service                         │
├─────────────────┬─────────────────┬─────────────────────┤
│  API Layer      │  Core Logic     │  Template System    │
├─────────────────┼─────────────────┼─────────────────────┤
│ - FastAPI       │ - Phase Gen     │ - Domain Templates  │
│ - OpenAPI 3.0   │ - Validation    │ - Base Templates    │
│ - Auth/ACL      │ - Enhancement   │ - Template Store    │
└─────────────────┴─────────────────┴─────────────────────┘
```

### API Endpoints

```typescript
// POET Transpilation API
POST /api/v1/transpile
Request:
{
  function_code: string;         // Complete function code including @poet decorator
  language: "python" | "dana";
  context?: {
    sandbox_context?: any;       // SandboxContext from Dana runtime
    imports: string[];           // Available imports in the module
    module_path?: string;        // Module location for relative imports
    dependencies?: string[];     // External dependencies
  };
}
Response:
{
  poet_implementation: {
    code: string;                // Complete POET implementation with P→O'→E(→T)
    language: "python" | "dana";
  };
  metadata: {
    decorator_params: {          // Parsed from @poet decorator
      domain?: string;
      optimize_for?: string;
      retries?: number;
      timeout?: number;
    };
    phases_included: string[];   // ["perceive", "operate", "enforce"] or includes "train"
    original_function_name: string;
    enhancements: string[];      // List of enhancements applied during O→O' transformation
  };
}
```

### Transpilation Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Dana Runtime  │     │  POET Service   │     │    LLM Service  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. Send complete      │                       │
         │    function code      │                       │
         │    with @poet         │                       │
         │    decorator + context│                       │
         ├─────────────────────►│                       │
         │                      │                       │
         │                      │ 2. Parse @poet        │
         │                      │    decorator params   │
         │                      │                       │
         │                      │ 3. Load domain        │
         │                      │    template           │
         │                      │                       │
         │                      │ 4. Generate POET      │
         │                      │    implementation     │
         │                      │    (P→O'→E→T)         │
         │                      ├──────────────────────►│
         │                      │                       │
         │                      │ 5. Return complete    │
         │                      │    POET code          │
         │                      │◄──────────────────────┤
         │                      │                       │
         │ 6. Return POET       │                       │
         │    implementation    │                       │
         │    for execution     │                       │
         │◄─────────────────────┤                       │
```

### Storage Structure
```
/poet/
├── templates/
│   ├── base/
│   │   ├── v1/
│   │   │   ├── template.txt     # Unified template with P→O→E phases
│   │   │   ├── train_addon.txt  # Optional Train phase template
│   │   │   └── metadata.json    # Template metadata
│   │   └── current -> v1        # Current version
│   ├── ml_monitoring/
│   │   ├── v1/
│   │   │   ├── template.txt     # ML-specific P→O→E template
│   │   │   ├── train_addon.txt  # ML-specific Train template
│   │   │   └── metadata.json
│   │   └── current -> v1
│   └── api_operations/
│       ├── v1/
│       │   ├── template.txt     # API-specific P→O→E template
│       │   ├── train_addon.txt  # API-specific Train template
│       │   └── metadata.json
│       └── current -> v1
└── cache/
    └── enhanced_functions/      # Cached enhanced functions
```

**Template Usage**:
- Always use `template.txt` for P→O→E phases
- Only append `train_addon.txt` content when `optimize_for` is specified
- This ensures Train phase is truly optional and conditional

**Example Template Structure**:

`ml_monitoring/template.txt`:
```
Generate enhanced Python implementation for {function_name}.
Domain: ML Monitoring

Requirements:
- Perceive: Validate data types, handle missing data, detect data characteristics
- Operate: Statistical tests (KS, KL divergence), parallel processing, adaptive windowing
- Enforce: Validate output format, ensure statistical significance

Original function:
{original_code}

Generate complete enhanced function with ML monitoring intelligence.
```

`ml_monitoring/train_addon.txt`:
```
Additional Train phase requirement:
- Train: Emit monitoring events, track performance metrics, optimize for {optimize_for}
- Collect feedback related to {optimize_for} objective
- Enable continuous learning and parameter adjustment
```

## Implementation Plan

### Phase 1: Core Enhancement (Week 1)
- Implement basic function enhancement with P→O→E
- Add template loading system
- Set up LLM integration
- Support conditional Train phase based on optimize_for

### Phase 2: Domain Templates (Week 2)
- Create domain-specific templates
- Implement template validation
- Set up template versioning
- Add enhancement caching

### Phase 3: Production Readiness (Week 3)
- Add security measures
- Implement monitoring
- Add performance optimization
- Complete API documentation

## Success Criteria
- Enhancement generation time < 10 seconds
- 99.9% uptime for enhancement service
- Generated code maintains original function semantics
- Successful enhancement rate > 95%
- Train phase only included when optimize_for is specified
- Template loading time < 1 second

## Risk Mitigation
- LLM service failures → Fallback to basic P→O→E enhancement
- Template validation failures → Use base templates
- High latency → Implement caching for enhanced functions
- Security issues → Strict validation of generated code
- Invalid optimize_for values → Default to no Train phase

## Quality Gates
- All generated code must pass syntax validation
- All generated code must maintain original function semantics
- Train phase must only be included when optimize_for is specified
- All templates must be validated before use
- All security checks must pass before returning enhanced code

## Performance Requirements
- Enhancement generation latency < 10 seconds
- Concurrent request support > 100
- Cache hit rate > 80% for repeated enhancements
- Memory usage < 1GB per request
- Template loading time < 100ms

## Deployment Phase

### Deployment Strategy
- Deploy as Kubernetes service
- Use rolling updates
- Implement health checks
- Set up auto-scaling

### Monitoring Plan
- Monitor transformation latency
- Track success/failure rates
- Monitor cache performance
- Track resource usage

### Rollback Procedures
- Maintain previous version
- Quick rollback on issues
- Preserve cache during rollback
- Validate rollback success

## Security Considerations
- Input validation
- Rate limiting
- Access control
- Secure template storage
- LLM service security
