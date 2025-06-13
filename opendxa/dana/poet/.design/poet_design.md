# POET LLM Code Generation - 3D Design Document

```text
Author: Christopher Nguyen
Date: 2025-06-13
Version: 0.5
Status: Design Phase
```

**Related Documents:**
- [POET Code Generation Service Design](../../../dxa-factory/poet/service/.design/poet_service_design.md)
- [POET Pub/Sub Design](../../../common/pubsub/.design/pubsub_design.md)

## 3D Methodology Status

**Phase**: ✅ Design Complete → 🔄 Implementation → ⏳ Testing → ⏳ Deployment

**Design Quality Gate**: ✅ PASSED
- ✅ Problem statement clearly defined
- ✅ Solution architecture specified
- ✅ Implementation plan with phases
- ✅ Success criteria defined
- ✅ Risk mitigation planned

## Executive Summary

POET (Perceive → Operate → Enforce → Train) is an LLM-powered code generation framework that transforms simple function definitions into production-ready implementations with built-in reliability, domain intelligence, and continuous learning capabilities.

**Key Innovation**: The LLM generates entire enhanced function implementations that learn and improve through production feedback, eliminating manual reliability engineering.

## Problem Statement

Building production-ready functions today requires:
- Manual implementation of error handling, retries, timeouts
- Complex monitoring and feedback collection systems
- Domain-specific optimization that takes weeks to implement
- Slow iteration when requirements change
- No learning mechanism to improve over time

**User Need**: Developers want functions that "just work better" and continuously improve, without manual reliability engineering.

## Solution Architecture

### Core Concept
```python
# User writes simple function
@poet(domain="ml_monitoring")
def detect_drift(current_data, reference_data):
    return {"drift_detected": False, "score": 0.0}

# POET generates enhanced version with:
# - Statistical tests (KS, KL divergence) (Perceive)
# - Retry logic and error handling (Operate)  
# - Output validation and checks (Enforce)
# - Feedback collection hooks (Train)
```

### Function Enhancement Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Dana Runtime  │     │  POET Service   │     │    LLM Service  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. @poet function    │                       │
         │    encountered       │                       │
         ├─────────────────────►│                       │
         │                      │                       │
         │                      │ 2. Request enhanced   │
         │                      │    implementation     │
         │                      ├──────────────────────►│
         │                      │                       │
         │                      │ 3. Return enhanced    │
         │                      │    code (Dana/Python) │
         │                      │◄──────────────────────┤
         │                      │                       │
         │ 4. Return enhanced   │                       │
         │    code              │                       │
         │◄─────────────────────┤                       │
         │                      │                       │
         │ 5. Store in .poet/   │                       │
         │    <function>/v1/    │                       │
         │                      │                       │
         │ 6. Safety audit      │                       │
         │                      │                       │
         │ 7. Execute P→O→E→T   │                       │
         │                      │                       │
         │ 8. Emit execution    │                       │
         │    event             │                       │
         └─────────────────────►│                       │
```

### Feedback Loop Design

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Dana Runtime  │     │  POET Service   │     │   PubSub System │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. Register mailbox  │                       │
         │    for function      │                       │
         │    feedback          │                       │
         ├─────────────────────►│                       │
         │                      │                       │
         │                      │ 2. Create feedback    │
         │                      │    subscription       │
         │                      ├──────────────────────►│
         │                      │                       │
         │                      │ 3. Acknowledge        │
         │                      │    subscription       │
         │                      │◄──────────────────────┤
         │ 4. Subscription      │                       │
         │    confirmed         │                       │
         │◄─────────────────────┤                       │
         │                      │                       │
         │ 5. Execute function  │                       │
         │                      │                       │
         │ 6. Emit execution    │                       │
         │    event             │                       │
         ├─────────────────────►│                       │
         │                      │                       │
         │                      │ 7. Publish to         │
         │                      │    feedback topic     │
         │                      │◄──────────────────────┤
         │                      │                       │
         │                      │ 8. Process feedback   │
         │                      │    queue              │
         │                      │◄──────────────────────┤
         │                      │                       │
         │ 9. If feedback       │                       │
         │    requires update   │                       │
         │                      │                       │
         │ 10. Request new      │                       │
         │     version          │                       │
         ├─────────────────────►│                       │
```

### Storage Structure
```
module_dir/
└── .poet/
    └── <function_name>/
        ├── v1/
        │   ├── code.dana        # Enhanced Dana code
        │   ├── code.py          # Enhanced Python code
        │   ├── params.json      # Function parameters
        │   ├── state.json       # Runtime state
        │   └── metadata.json    # Version metadata
        ├── v2/                  # Created if feedback triggers update
        ├── current -> v1        # Symlink to current version
        └── feedback/            # Local feedback storage
            ├── pending/         # Unprocessed feedback
            └── processed/       # Processed feedback
```

### Event Schema
```typescript
interface POETEvent {
  id: string;
  type: string;
  timestamp: number;
  correlation_id?: string;
  causation_id?: string;  // Links to triggering event
  metadata: {
    version: string;
    environment: string;
    service: string;
  };
  payload: any;
}

interface FunctionExecutionEvent extends POETEvent {
  type: "function.execution";
  payload: {
    function_name: string;
    version: string;
    execution_id: string;
    start_time: number;
    end_time: number;
    status: "success" | "failure";
    metrics: {
      duration_ms: number;
      memory_mb: number;
      cpu_percent: number;
    };
    error?: {
      type: string;
      message: string;
      stack_trace?: string;
    };
  };
}

interface FunctionFeedbackEvent extends POETEvent {
  type: "function.feedback";
  payload: {
    function_name: string;
    version: string;
    execution_id: string;
    feedback_type: "performance" | "error" | "user" | "system";
    rating?: number;
    comments?: string;
    metrics?: {
      success_rate: number;
      avg_duration: number;
      error_rate: number;
    };
    suggestions?: string[];
  };
}
```

### Progressive User Experience
1. **Level 1**: `@poet()` - Instant reliability (retries, timeouts)
2. **Level 2**: `@poet(domain="ml_monitoring")` - Domain intelligence  
3. **Level 3**: `@poet(optimize_for="accuracy")` - Specific optimization goals

### Architecture Components

#### 1. LLM Code Generator
Core service that generates enhanced function implementations:

```python
class POETCodeGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.domain_templates = DomainTemplates()
    
    def enhance_function(self, original_func, config):
        # Generate enhanced implementation via LLM
        template = self.domain_templates.get(config.domain)
        enhanced_code = self.llm.generate(template.format(
            function_name=original_func.__name__,
            original_code=inspect.getsource(original_func),
            domain_requirements=template.requirements
        ))
        return self.compile_and_validate(enhanced_code)
```

#### 2. Domain Templates
Simple text templates that encode domain knowledge:

```python
ML_MONITORING_TEMPLATE = """
Generate enhanced Python implementation for {function_name}.
Domain: ML Monitoring

Requirements:
- Perceive: Validate data types, handle missing data, detect data characteristics
- Operate: Statistical tests (KS, KL divergence), parallel processing, adaptive windowing
- Enforce: Validate output format, ensure statistical significance
- Train: Emit monitoring events, track performance metrics

Original function:
{original_code}

Generate complete enhanced function with ML monitoring intelligence.
"""
```

#### 3. Aitomatic Integration
POET integrates with Aitomatic services via clean interfaces:

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   DANA Code     │───▶│  Transpilation Agent │───▶│  POET Service   │
│   (.na files)   │    │  (Aitomatic Agent)   │    │  (Enhancement)  │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
                                  │                          │
                                  ▼                          ▼
                       ┌──────────────────────┐    ┌─────────────────┐
                       │   Python Functions   │    │ Enhanced Python │
                       │   (Base Functions)   │    │  (Production)   │
                       └──────────────────────┘    └─────────────────┘
```

#### 4. File Storage System
Simple file-based storage for enhanced versions:

```
project/
├── my_module.py
└── .poet/
    ├── detect_drift_v1.py
    ├── detect_drift_v2.py
    ├── detect_drift_current.py -> detect_drift_v2.py
    ├── detect_drift_params.json
    └── events/
        ├── pending/
        └── processed/
```

#### 5. Event-Driven Learning System
Persistent event queue for cross-session learning:

```python
class POETEventQueue:
    def __init__(self, storage_path=".poet/events"):
        self.storage_path = Path(storage_path)
        self.pending_dir = self.storage_path / "pending"
        self.processed_dir = self.storage_path / "processed"
    
    def emit(self, event_type: str, payload: dict):
        """Emit event with persistent storage"""
        event = {
            "type": event_type,
            "payload": payload,
            "timestamp": time.time(),
            "id": str(uuid.uuid4())
        }
        
        # Persist immediately (crash-safe)
        event_file = self.pending_dir / f"{event['id']}.json"
        with open(event_file, 'w') as f:
            json.dump(event, f)
```

## Use Cases

### Primary Use Case: ML Model Monitoring
Transform simple monitoring functions into production-grade systems:

**Input**: Basic drift detection function
**Output**: Sophisticated monitoring with:
- Automatic statistical test selection (KS, KL divergence)
- Feature importance weighting
- Adaptive windowing
- Alert fatigue reduction
- Cost-benefit optimization

See detailed examples in `ML_MONITORING_EXAMPLES.md`

### Secondary Use Cases
- API monitoring and reliability
- Customer service automation
- Financial risk assessment
- Prompt optimization

See `examples/` directory for complete implementations.

## Implementation Plan (3D Methodology)

### 🔄 Phase 1: Core Infrastructure (Weeks 1-2)
**Goal**: Basic LLM code generation working

**Immediate Next Steps**:
1. **Create basic file structure**:
   ```bash
   opendxa/dana/poet/generator.py          # POETCodeGenerator class
   opendxa/dana/poet/decorator.py          # @poet decorator
   opendxa/dana/poet/storage.py            # File storage system
   opendxa/dana/poet/domains/base.py       # Basic domain template
   opendxa/common/event_queue.py           # Event system
   ```

2. **Build POETCodeGenerator**:
   ```python
   class POETCodeGenerator:
       def enhance_function(self, original_func, config):
           # Send function + domain template to LLM
           # Get back enhanced Python code
           # Validate and compile
           # Return enhanced function
   ```

3. **Create @poet decorator**:
   ```python
   def poet(domain=None, optimize_for=None):
       # Intercept function calls
       # Route to POETCodeGenerator
       # Replace with enhanced version
   ```

4. **Add ML monitoring domain**:
   ```python
   ML_MONITORING_TEMPLATE = """
   Generate enhanced Python for ML monitoring...
   Include: KS tests, KL divergence, windowing...
   """
   ```

5. **Test basic flow**:
   ```python
   @poet(domain="ml_monitoring")
   def detect_drift(data):
       return {"drift_detected": False}
   # Should generate sophisticated drift detection
   ```

**Deliverables**:
- [ ] POETCodeGenerator class (`opendxa/dana/poet/generator.py`)
- [ ] Function decorator and interception (`opendxa/dana/poet/decorator.py`)
- [ ] Simple file storage system (`opendxa/dana/poet/storage.py`)
- [ ] Basic domain template (`opendxa/dana/poet/domains/base.py`)
- [ ] POETEventQueue implementation (`opendxa/common/event_queue.py`)

**Success Criteria**:
- ✅ Can enhance any function with basic retries/timeouts
- ✅ Generated code executes successfully
- ✅ Fallback to original function on generation failure

### ⏳ Phase 2: Domain Intelligence (Weeks 3-4)  
**Goal**: Domain-specific enhancements working

**Deliverables**:
- [ ] ML monitoring domain template (`opendxa/dana/poet/domains/ml_monitoring.py`)
- [ ] API operations domain template (`opendxa/dana/poet/domains/api.py`)
- [ ] Aitomatic agent integration layer
- [ ] Domain template validation system

**Success Criteria**:
- ✅ Different domains produce visibly different enhancements
- ✅ ML monitoring domain handles statistical tests automatically
- ✅ Integration with Aitomatic transpilation agent works

### ⏳ Phase 3: Feedback Orchestration & Learning (Weeks 5-6)
**Goal**: Functions improve over time through production feedback

**Deliverables**:
- [ ] Feedback collection integrations (alerts, MLOps, cost tracking)
- [ ] Learning orchestration (pattern analysis, regeneration triggers)
- [ ] Success rate tracking and metrics

**Success Criteria**:
- ✅ Functions automatically regenerate when performance degrades
- ✅ Learning objectives influence generated code behavior
- ✅ Feedback correlation works across session restarts

### ⏳ Phase 4: Production Readiness (Weeks 7-8)
**Goal**: Ready for real-world ML monitoring usage

**Deliverables**:
- [ ] Comprehensive error handling and security validation
- [ ] Performance optimization (caching, async generation)
- [ ] Complete documentation and ML monitoring showcase
- [ ] Production deployment examples

**Success Criteria**:
- ✅ Sub-10 second enhancement generation
- ✅ 95%+ generated code reliability
- ✅ Complete ML monitoring agent demonstration

## Quality Gates

### Development Standards
- **Code Quality**: All generated code must pass syntax validation
- **Security**: Generated code limited to safe operations only
- **Performance**: Enhancement generation < 10 seconds
- **Reliability**: Fallback to original function if enhancement fails

### Error Handling Strategy

#### 1. Code Generation Errors
- **LLM Generation Failures**:
  - Retry with exponential backoff (max 3 attempts)
  - Fallback to simpler enhancement if complex generation fails
  - Log detailed error context for debugging
  - Alert if failure rate exceeds threshold

- **Validation Failures**:
  - Detailed error messages with specific validation failures
  - Automatic retry with different parameters
  - Fallback to original function if validation fails
  - Track validation failure patterns

#### 2. Runtime Errors
- **Function Execution Errors**:
  - Automatic retry with exponential backoff
  - Circuit breaker for repeated failures
  - Detailed error logging with context
  - Alert on error rate thresholds

- **State Management Errors**:
  - Transaction rollback on failure
  - State recovery mechanisms
  - Version rollback capability
  - Audit trail of state changes

#### 3. Feedback Processing Errors
- **Feedback Collection Errors**:
  - Retry with backoff
  - Queue feedback for later processing
  - Alert on persistent failures
  - Track feedback processing metrics

### Security Considerations

#### 1. Code Generation Security
- **Input Validation**:
  - Sanitize all function inputs
  - Validate code structure
  - Check for malicious patterns
  - Rate limit generation requests

- **Output Validation**:
  - Static code analysis
  - Security pattern checking
  - Resource usage limits
  - Sandboxed execution testing

#### 2. Runtime Security
- **Function Execution**:
  - Resource limits (CPU, memory, time)
  - Network access restrictions
  - File system access controls
  - Environment isolation

- **State Management**:
  - Access control for state changes
  - Audit logging of all operations
  - Encryption of sensitive data
  - Version control security

#### 3. Feedback Security
- **Feedback Collection**:
  - Validate feedback sources
  - Rate limit feedback submission
  - Sanitize feedback content
  - Track feedback patterns

### Performance Requirements

#### 1. Response Time SLAs
- **Code Generation**:
  - 95th percentile < 10 seconds
  - 99th percentile < 30 seconds
  - Timeout at 60 seconds
  - Cache frequent generations

- **Function Execution**:
  - 95th percentile < 100ms
  - 99th percentile < 500ms
  - Timeout at 5 seconds
  - Circuit breaker on slow responses

#### 2. Resource Usage
- **Memory**:
  - Max 1GB per generation
  - Max 256MB per execution
  - Memory monitoring
  - Automatic cleanup

- **CPU**:
  - Max 2 cores per generation
  - Max 1 core per execution
  - CPU time monitoring
  - Throttling on high usage

#### 3. Storage Requirements
- **Function Storage**:
  - Max 10MB per function
  - Max 10 versions per function
  - Automatic cleanup of old versions
  - Compression for large functions

- **Event Storage**:
  - Max 1MB per event
  - 30-day retention
  - Automatic archival
  - Compression for old events

#### 4. Scalability Targets
- **Throughput**:
  - 100 generations per minute
  - 1000 executions per minute
  - 10000 events per minute
  - Auto-scaling based on load

- **Concurrency**:
  - 50 concurrent generations
  - 500 concurrent executions
  - 1000 concurrent events
  - Queue-based throttling

## Risk Assessment & Mitigation

### High Risk
**LLM Generation Reliability**
- *Risk*: Generated code may be incorrect or insecure
- *Mitigation*: Strict validation, sandboxed execution, fallback to original

**Security Concerns** 
- *Risk*: Executing dynamically generated code
- *Mitigation*: Whitelist allowed operations, code review, static analysis

### Medium Risk
**Performance Impact**
- *Risk*: LLM generation latency affects user experience  
- *Mitigation*: Asynchronous generation, aggressive caching, local LLM option

**Integration Complexity**
- *Risk*: Complex integration with Aitomatic services
- *Mitigation*: Well-defined interfaces, extensive integration testing

## Success Metrics

### User Experience Metrics
- Time from `@poet()` to working enhancement: < 30 seconds
- Zero-config success rate: > 90%
- User satisfaction score: > 4.0/5.0

### Technical Performance Metrics  
- Generated code success rate: > 95%
- Enhancement generation time: < 10 seconds
- Storage overhead per function: < 1MB

### Business Impact Metrics
- Reduction in manual reliability code: > 50%
- Developer productivity improvement: > 30%
- Production incident reduction: > 40%

## Design Decisions

### KISS Principles Applied
- **Simple storage**: Flat files, no complex databases
- **Minimal config**: Smart defaults, progressive disclosure
- **Direct enhancement**: LLM generates code, not metadata
- **Agent integration**: Clean service boundaries

### YAGNI Principles Applied  
- **No frameworks**: Domain templates, not plugin architectures
- **No premature optimization**: Basic reliability first
- **No speculative features**: Build for actual user needs
- **Service abstraction**: Let Aitomatic handle transpilation

This design prioritizes developer experience and practical utility over architectural sophistication, making POET genuinely useful for everyday coding tasks while leveraging Aitomatic's agent infrastructure.

## POET System Modules

The complete POET system is designed across three key module directories:

### 1. Core POET Framework
**Location**: `opendxa/dana/poet/.design/`
- Main POET design documents and architecture
- ML monitoring examples and domain templates  
- Core framework implementation plans
- Learning system design and feedback orchestration

### 2. PubSub Communication Infrastructure
**Location**: `opendxa/common/pubsub/.design/`
- Event-driven architecture for feedback orchestration
- Integration patterns with Aitomatic services
- Cross-system communication protocols
- Event persistence and processing pipelines

### 3. POET REST API Service
**Location**: `opendxa/enterprise/poet/service/.design/`
- FastAPI-based REST service architecture
- OpenAPI 3.0 specification and endpoints
- Enterprise deployment and security patterns
- Kubernetes configuration and monitoring

These three modules work together to provide:
- **Core POET** (dana/poet) - The enhancement framework and domain intelligence
- **PubSub** (common/pubsub) - The communication and feedback infrastructure  
- **Service** (enterprise/poet/service) - The REST API deployment and enterprise integration

## Related Documents

- `supporting_docs/ml_monitoring_examples.md` - Complete ML monitoring use cases
- `supporting_docs/domain_templates.md` - Domain-specific template specifications
- `supporting_docs/feedback_orchestration.md` - Detailed feedback loop architecture
- `supporting_docs/pubsub_design.md` - Event-driven architecture
- `supporting_docs/implementation_tracker.md` - Detailed implementation progress tracking