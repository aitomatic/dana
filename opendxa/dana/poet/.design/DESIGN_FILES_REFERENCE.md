# POET Design Files Reference

## Main Design Documents (4)

### 1. POET Core Framework
- **Design**: [`opendxa/dana/poet/.design/poet.md`](poet.md)
- **Implementation**: [`opendxa/dana/poet/.design/poet-implementation.md`](poet-implementation.md)
- **Scope**: Complete POET architecture, LLM-powered feedback, P→O→E→T phases
- **Status**: Core design complete, implementation ongoing

### 2. POET Alpha MVP
- **Design**: [`opendxa/dana/poet/.design/poet-alpha.md`](poet-alpha.md)
- **Implementation**: [`opendxa/dana/poet/.design/poet-alpha-implementation.md`](poet-alpha-implementation.md)
- **Scope**: 12-day MVP implementation plan targeting June 26, 2025
- **Status**: **ACTIVE** - Day 1 implementation in progress

### 3. OpenDXA API Service Platform
- **Design**: [`opendxa/api/.design/opendxa_api_service.md`](../../../api/.design/opendxa_api_service.md)
- **Implementation**: [`opendxa/api/.design/opendxa_api_service-implementation.md`](../../../api/.design/opendxa_api_service-implementation.md)
- **Scope**: Unified API platform for POET, prompt rewriting, magic functions, etc.
- **Status**: Design complete, implementation deferred to Beta

### 4. PubSub Event System
- **Design**: [`opendxa/common/pubsub/.design/pubsub.md`](../../../common/pubsub/.design/pubsub.md)
- **Implementation**: [`opendxa/common/pubsub/.design/pubsub-implementation.md`](../../../common/pubsub/.design/pubsub-implementation.md)
- **Scope**: Event-driven communication for delayed feedback from external systems
- **Status**: Design complete, implementation deferred to Beta

## Cross-References Matrix

| Document | References |
|----------|------------|
| `poet.md` | `poet-implementation.md`, `poet-alpha.md`, `../../../api/.design/opendxa_api_service.md`, `../../../common/pubsub/.design/pubsub.md` |
| `poet-alpha.md` | `poet.md`, `../../../api/.design/opendxa_api_service.md`, `../../../common/pubsub/.design/pubsub.md` |
| `opendxa_api_service.md` | `../../dana/poet/.design/poet.md`, `../../common/pubsub/.design/pubsub.md` |
| `pubsub.md` | `../../dana/poet/.design/poet.md` |

## Implementation Progress Summary

### Alpha Phase (Current - June 14)
- **POET Core**: ✅ @poet decorator, POETClient, basic transpilation
- **API Infrastructure**: ✅ OpenDXAServer, APIClient, routes
- **Storage**: ✅ File-based .poet/ directory structure
- **Feedback**: ✅ AlphaFeedbackSystem with LLM translation
- **Makefile**: ✅ `make opendxa-server` target

### Next: Unit Tests (Alpha Day 1 completion)
- [ ] Unit tests for local transpilation mode
- [ ] Unit tests for service mode (when available)
- [ ] Integration tests for end-to-end scenarios

### Beta Phase (July 2025)
- [ ] OpenDXA API Service platform deployment
- [ ] PubSub system for delayed feedback
- [ ] Multiple services (POET + prompt rewriting + magic functions)

### Gamma Phase (August 2025)
- [ ] Advanced domain templates
- [ ] Enterprise features
- [ ] Production scaling

## Key Design Decisions

1. **Alpha Scope**: Local transpilation only, in-memory feedback, single domain (ML monitoring)
2. **Service Architecture**: Unified OpenDXA API platform with plugin architecture
3. **Configuration**: Single `AITOMATIC_API_URL` and `AITOMATIC_API_KEY` for all services
4. **Feedback Strategy**: Immediate feedback via `poet.feedback()`, delayed feedback via PubSub (Beta)
5. **Train Phase**: Only generated when `optimize_for` is specified

## File Organization

```
opendxa/
├── api/
│   └── .design/
│       ├── opendxa_api_service.md
│       └── opendxa_api_service-implementation.md
├── common/
│   └── pubsub/
│       └── .design/
│           ├── pubsub.md
│           └── pubsub-implementation.md
└── dana/
    └── poet/
        └── .design/
            ├── poet.md
            ├── poet-implementation.md
            ├── poet-alpha.md
            ├── poet-alpha-implementation.md
            └── DESIGN_FILES_REFERENCE.md (this file)
```

## Current Focus

**PRIMARY**: [`poet-alpha-implementation.md`](poet-alpha-implementation.md) - Daily tracking for June 26 MVP delivery

All other implementation trackers are synchronized with Alpha priorities but focus on their respective Beta/Gamma timelines.