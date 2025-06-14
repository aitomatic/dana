# POET Alpha Development Plan - 3D Design Document

```text
Author: Christopher Nguyen
Date: 2025-06-14
Version: 1.0
Status: Design Phase
Target: MVP by June 26, 2025 (12 days)
Implementation Tracker: poet-alpha-implementation.md
```

**Related Documents:**
- [POET Core Framework Design](poet.md) - Complete POET architecture and LLM-powered feedback
- [OpenDXA API Service Design](../../../api/.design/opendxa_api_service.md) - Unified API platform with POET as first service
- [PubSub Design](../../../common/pubsub/.design/pubsub.md) - Delayed feedback infrastructure

## 3D Methodology Status

**Phase**: ✅ Design → 🔄 Implementation → ⏳ Testing → ⏳ Deployment

**Implementation Tracking**: See [poet-alpha-implementation.md](poet-alpha-implementation.md) for:
- Design review status and quality gates
- Daily implementation progress tracking  
- Phase-by-phase deliverables and checkboxes
- Quality monitoring and technical debt tracking
- Risk management and blocker resolution

**Critical Constraint**: MVP delivery by June 26, 2025 (12 days)

## Executive Summary

POET Alpha is the MVP version targeting June 26 delivery. It implements the core POET transpilation with LLM-powered feedback translation, focusing on the essential path: `@poet() → enhanced function → poet.feedback() → learning`. Alpha deliberately excludes delayed feedback/PubSub to accelerate delivery, using in-memory state management for immediate feedback learning.

**Key Trade-offs for Speed**:
- ✅ Local POETTranspiler only (no Aitomatic service integration)
- ✅ In-memory feedback storage (no PubSub/persistence)
- ✅ Basic domain templates (ML monitoring focus)
- ✅ LLM-powered feedback translation (core innovation)
- ❌ Delayed feedback collection (deferred to Beta)
- ❌ Enterprise service deployment (deferred to Beta)
- ❌ Complex domain template system (deferred to Gamma)

## Problem Statement

**Immediate Need**: Demonstrate POET's core value proposition by June 26:
1. Functions enhanced with minimal configuration
2. LLM-powered feedback understanding  
3. Functions that improve based on feedback
4. End-to-end learning loop working

**Success Definition**: An AI engineer can decorate a function, get immediate enhancements, provide natural language feedback, and see the function regenerate with improvements.

## Goals

### Alpha Goals (June 26)
- **Core Flow Working**: `@poet() → enhanced function → feedback → learning → regeneration`
- **LLM Integration**: Feedback translation using LLMResource
- **Basic Domain**: ML monitoring template sufficient for demos
- **Local Development**: Complete local development experience
- **Documentation**: Clear examples and usage patterns

### Post-Alpha Goals (Deferred)
- **Beta (July)**: Delayed feedback, PubSub integration, Aitomatic service
- **Gamma (August)**: Advanced domains, enterprise deployment, production scaling
- **Delta (September)**: Full ecosystem integration, advanced learning algorithms

## Non-Goals for Alpha

- ❌ Production-grade persistence (file-based is sufficient)
- ❌ Advanced domain templates (focus on ML monitoring only)
- ❌ External system integration (PagerDuty, MLflow, etc.)
- ❌ Advanced security/auth (local development focus)
- ❌ Performance optimization (correctness over speed)
- ❌ Comprehensive error handling (happy path focus)

## Proposed Solution

### Alpha Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    POET Alpha MVP                       │
├─────────────────┬─────────────────┬─────────────────────┤
│  Core Runtime   │  Service Layer  │  Learning Engine    │
├─────────────────┼─────────────────┼─────────────────────┤
│ - @poet()       │ - POETService   │ - Generated train() │
│ - POETClient    │ - /poet/* APIs  │ - LLM translation   │
│ - Feedback API  │ - Local/Remote  │ - Simple patterns   │
└─────────────────┴─────────────────┴─────────────────────┘
```

### Core Components for Alpha

#### 1. Unified API Architecture
```python
# opendxa/api/server.py - Generic OpenDXA server
class OpenDXAServer:
    def __init__(self, host="localhost", port=8080):
        self.app = FastAPI(title="OpenDXA API Server")
        self.host = host
        self.port = port
        self._setup_routes()
    
    def _setup_routes(self):
        # POET endpoints
        from opendxa.dana.poet.routes import router as poet_router
        self.app.include_router(poet_router, prefix="/poet")
        # Future: other OpenDXA services can be added here

# opendxa/api/client.py - Generic client utilities
class APIClient:
    def __init__(self, base_uri: str):
        self.base_uri = base_uri
        self.session = httpx.Client(base_url=base_uri, timeout=30.0)
    
    def post(self, endpoint: str, data: dict) -> dict:
        """POST with standardized error handling."""
        try:
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise POETServiceError(f"Connection failed to {self.base_uri}: {e}")
        except httpx.HTTPStatusError as e:
            raise POETServiceError(f"Service error ({e.response.status_code}): {e.response.text}")

# opendxa/dana/poet/client.py - POET-specific client
class POETClient:
    def __init__(self):
        # Load from .env file - generalized for all Aitomatic services
        self.service_uri = os.getenv("AITOMATIC_API_URL", "local")
        self.api_key = os.getenv("AITOMATIC_API_KEY")  # None for local mode
        self.local_mode = self.service_uri == "local"
        
        if self.local_mode:
            from .transpiler import LocalPOETTranspiler
            self.transpiler = LocalPOETTranspiler()
        else:
            from opendxa.api.client import APIClient
            self.api_client = APIClient(self.service_uri, api_key=self.api_key)
    
    def transpile_function(self, function_code: str, config: POETConfig) -> TranspiledFunction:
        """Unified API - local or remote execution with fail-fast behavior."""
        if self.local_mode:
            return self.transpiler.transpile_function(function_code, config)
        else:
            # Fail fast on service errors - use /poet prefix for POET endpoints
            response_data = self.api_client.post("/poet/transpile", {
                "function_code": function_code,
                "config": config.dict()
            })
            return TranspiledFunction.from_response(response_data)

# Configuration via .env - generalized for all Aitomatic services
# AITOMATIC_API_URL=local                           # Default (local mode)
# AITOMATIC_API_URL=http://localhost:8080           # Local OpenDXA server
# AITOMATIC_API_URL=https://api.aitomatic.com       # Production Aitomatic API
# AITOMATIC_API_KEY=sk-ait-xxxxx                    # API key (not needed for local)

# Usage remains simple:
@poet()  # Uses AITOMATIC_API_URL from .env
def detect_drift(data):
    return {"drift_detected": False}
```

#### 2. Basic Feedback System
```python
# opendxa/dana/poet/feedback.py
class AlphaFeedbackSystem:
    def __init__(self):
        self.executions = {}  # In-memory storage
        self.trainers = {}    # Cached train() methods
    
    def feedback(self, result: POETResult, feedback_payload: Any) -> None:
        """Alpha implementation - in-memory only."""
        execution_id = result._poet["execution_id"]
        
        # Load generated train() method
        trainer = self._get_trainer(result._poet["function_name"], result._poet["version"])
        
        # Let train() handle the feedback
        trainer.train(execution_id, feedback_payload)
```

#### 3. Generated Train Methods
```python
# .poet/{function_name}/v1/train.py (generated)
class AlphaTrainer:
    def __init__(self):
        self.llm = LLMResource()
        self.state = {}  # Simple in-memory state
    
    def train(self, execution_id: str, raw_feedback: Any) -> None:
        """Alpha: Simple LLM translation + pattern detection."""
        # Translate feedback using LLM
        # Update simple learning state
        # Trigger regeneration if needed
        pass
```

### Implementation Overview

See [poet-alpha-implementation.md](poet-alpha-implementation.md) for detailed:
- Daily implementation phases and deliverables
- Quality gates and testing requirements  
- Progress tracking and milestone monitoring
- Technical configuration and setup details

## Technical Decisions for Alpha

### 1. Simplified Storage
**Decision**: File-based storage in `.poet/` directory
**Rationale**: Faster implementation than database integration
**Future**: Database integration in Beta

```
.poet/
├── {function_name}/
│   ├── v1/
│   │   ├── enhanced.py    # Enhanced function code
│   │   ├── train.py       # Generated trainer (if optimize_for)
│   │   └── metadata.json  # Function metadata
│   └── current -> v1      # Symlink to current version
└── executions/
    └── {execution_id}.json # Execution context
```

### 2. In-Memory Feedback
**Decision**: In-memory feedback storage with file persistence
**Rationale**: Simpler than PubSub integration
**Future**: PubSub integration in Beta

```python
class AlphaFeedbackStore:
    def __init__(self):
        self.executions = {}     # execution_id -> execution_data
        self.feedback = {}       # execution_id -> [feedback_list]
        self.learning_state = {} # function_name -> learning_data
```

### 3. Basic Domain Templates
**Decision**: Single ML monitoring template
**Rationale**: Focus on quality over quantity
**Future**: Multi-domain templates in Gamma

### 4. Unified API with .env Configuration
**Decision**: opendxa.api module with .env-based configuration
**Rationale**: 
- Consistent with LLM configuration patterns
- Clean separation of API infrastructure
- Simple configuration management
- Fail-fast for reliability

**Implementation**: 
```bash
# .env configuration - generalized for all Aitomatic services
AITOMATIC_API_URL=local                           # Default
AITOMATIC_API_URL=http://localhost:8080           # Local server
AITOMATIC_API_URL=https://api.aitomatic.com       # Production API
AITOMATIC_API_KEY=sk-ait-xxxxx                    # API key (production only)

# Makefile integration
make opendxa-server  # Starts local OpenDXA server (POET + future services)

# Usage (no changes needed)
@poet()
def func(): pass
```
**Future**: Beta adds authentication, retries, service discovery

## Quality Gates

### Code Quality Standards
- **Type Hints**: All functions must have type annotations
- **Docstrings**: All public APIs documented
- **Error Handling**: Graceful degradation on failures
- **Testing**: Unit tests for all core functionality
- **Linting**: Pass `ruff check` and `ruff format`

### Functional Requirements
- **Reliability**: Functions execute successfully 95%+ of time
- **Feedback**: Accepts any feedback format without errors
- **Learning**: Shows measurable improvement after feedback
- **Performance**: Function enhancement < 10 seconds
- **Storage**: Persistent across session restarts

### User Experience Requirements
- **Simple API**: Only `@poet()` and `poet.feedback()` needed
- **Clear Errors**: Helpful error messages with suggestions
- **Fast Setup**: Working example in < 5 minutes
- **Documentation**: Complete usage examples provided

## Risk Assessment & Mitigation

### High Risk: LLM Integration Reliability
**Risk**: LLM responses may be unparseable or incorrect
**Mitigation**: 
- Robust parsing with fallbacks
- Structured prompts with examples
- Validation of extracted learning signals
- Graceful degradation on parsing failures

### High Risk: Function Enhancement Quality
**Risk**: Generated enhanced functions may not work
**Mitigation**:
- Extensive testing of generated code
- Validation before execution
- Fallback to original function on failures
- Conservative enhancement patterns

### Medium Risk: Learning Loop Effectiveness
**Risk**: Feedback may not lead to meaningful improvements
**Mitigation**:
- Simple, proven learning patterns
- Clear improvement metrics
- Manual validation of regenerated functions
- Conservative regeneration triggers

### Medium Risk: Time Pressure
**Risk**: 12-day deadline is aggressive
**Mitigation**:
- Daily progress checkpoints
- Minimum viable feature set
- Parallel development where possible
- Buffer days built into schedule

## Success Metrics

### Alpha Success Criteria (June 26)
- **Functional**: Complete ML monitoring example working end-to-end
- **Technical**: All core APIs implemented and tested
- **User Experience**: Documentation complete, examples working
- **Performance**: Function enhancement < 10 seconds
- **Quality**: No critical bugs, graceful error handling

### Demo Success Metrics
- **Showcase Value**: Clear before/after improvement demonstration
- **Learning Evidence**: Function behavior changes based on feedback
- **Simplicity**: Developer only needs to remember `poet.feedback(result, feedback)`
- **Robustness**: Handles various feedback formats naturally

## Post-Alpha Roadmap

### Beta (July 2025): Enterprise Integration
- Delayed feedback via PubSub
- Aitomatic service integration
- External system connectors (PagerDuty, MLflow)
- Multi-user support
- Persistent storage

### Gamma (August 2025): Domain Expansion
- Additional domain templates (API operations, financial analysis)
- Advanced learning algorithms
- Performance optimization
- Production deployment patterns

### Delta (September 2025): Ecosystem Integration
- Full Aitomatic agent integration
- Advanced analytics and monitoring
- Multi-model learning strategies
- Enterprise security features

## Implementation Guidelines

### Development Workflow
1. **Feature Branch**: Create branch for each component
2. **Test-Driven**: Write tests before implementation
3. **Daily Standups**: Progress check every morning
4. **Integration Testing**: Test complete flows daily
5. **Documentation**: Update docs with each feature

### Code Organization
```
opendxa/
├── api/                   # Generic API infrastructure  
│   ├── __init__.py       
│   ├── server.py         # OpenDXAServer class
│   └── client.py         # Generic APIClient utilities
└── dana/poet/
    ├── __init__.py
    ├── decorator.py      # @poet() decorator
    ├── client.py         # POETClient (local/remote)
    ├── routes.py         # FastAPI POET endpoints
    ├── transpiler.py     # Local transpilation logic
    ├── feedback.py       # Feedback system
    ├── storage.py        # File-based storage
    ├── templates/
    │   └── ml_monitoring.py # Domain template
    └── examples/
        └── drift_detection.py # Complete example

# Additional files
Makefile                  # opendxa-server target
.env                      # AITOMATIC_API_URL, AITOMATIC_API_KEY configuration
```

### Testing Strategy
- **Unit Tests**: Each component tested in isolation (targeting 80% coverage)
- **Integration Tests**: End-to-end scenarios with both local and service modes
- **Service Tests**: REST API endpoints with test fixtures
- **Example Tests**: All documentation examples working in both modes
- **Performance Tests**: Enhancement speed validation
- **Error Tests**: Error handling and graceful degradation
- **Regression Tests**: Prevent regressions during rapid development

This Alpha plan prioritizes speed and core functionality to hit the June 26 deadline while establishing a solid foundation for post-Alpha enhancements. The focus on in-memory storage and local-only operation significantly reduces complexity while preserving the core innovation of LLM-powered feedback translation.

## Next Steps for Execution

1. **Immediate (Today)**: Begin Phase 1, Day 1 implementation
2. **Team Coordination**: Assign components if multiple developers
3. **Daily Progress**: Track against this schedule
4. **Risk Monitoring**: Watch for LLM integration and enhancement quality issues
5. **Demo Preparation**: Start demo script development early

The plan is aggressive but achievable with focused execution on the core value proposition.