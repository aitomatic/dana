# OpenDXA API Service Design

```text
Author: Christopher Nguyen
Date: 2025-06-14
Version: 1.0
Status: Design Phase
```

**Related Documents:**
- [POET Framework Design](../../dana/poet/.design/poet.md)
- [PubSub Service Design](../../common/pubsub/.design/pubsub.md)
- [OpenDXA API Service Implementation](opendxa_api_service-implementation.md)

## Executive Summary

The OpenDXA API Service is a unified REST API platform that provides multiple AI-powered development services. It serves as the central API gateway for all OpenDXA capabilities, with POET transpilation as the first service implementation, followed by prompt rewriting, magic functions, and other AI development tools.

**Key Innovation**: Single API endpoint (`AITOMATIC_API_URL`) that provides access to all OpenDXA services through a consistent REST interface, enabling seamless integration and unified authentication across the entire OpenDXA ecosystem.

## Goals

### Platform Goals
- **Unified API Gateway**: Single endpoint for all OpenDXA services
- **Consistent Interface**: Standardized REST patterns across all services
- **Extensible Architecture**: Easy addition of new AI-powered services
- **Production Ready**: Enterprise-grade reliability, security, and performance
- **Developer Experience**: Simple configuration and intuitive APIs

### Service Goals
- **POET Transpilation**: Transform functions with P→O→E→(T) phases
- **Prompt Rewriting**: Optimize prompts for better LLM performance
- **Magic Functions**: Generate utility functions from natural language
- **Code Enhancement**: General code improvement and optimization services
- **Domain Intelligence**: Specialized knowledge injection for various domains

## Non-Goals

- ❌ Execute generated code (handled by client environments)
- ❌ Manage application state (handled by client applications)
- ❌ Provide LLM models directly (uses external LLM services)
- ❌ Replace existing development tools (complements existing workflows)
- ❌ Handle real-time collaboration (focuses on transformation services)

## Problem Statement

### Current Development Challenges
Modern AI-assisted development requires:
- **Multiple Disconnected Tools**: Separate services for different AI tasks
- **Complex Integration**: Different APIs, authentication, and patterns
- **Inconsistent Quality**: Varying levels of reliability and error handling
- **Configuration Overhead**: Multiple API keys and endpoint management
- **Limited Extensibility**: Difficult to add new AI capabilities

### OpenDXA Solution
The unified API service addresses these by:
- **Single Integration Point**: One API for all OpenDXA services
- **Consistent Patterns**: Standardized request/response formats
- **Enterprise Reliability**: Built-in error handling, rate limiting, monitoring
- **Simple Configuration**: Single `AITOMATIC_API_URL` and `AITOMATIC_API_KEY`
- **Extensible Framework**: Plugin architecture for new services

## Solution Architecture

### Service Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenDXA API Service Platform                 │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│   API Gateway   │   Service Core  │  Service Layer  │   Plugins   │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ - FastAPI       │ - Request Route │ - POET Service  │ - Templates │
│ - OpenAPI 3.0   │ - Auth/ACL      │ - Prompt Service│ - Validators│
│ - Rate Limiting │ - Validation    │ - Magic Service │ - Enhancers │
│ - Monitoring    │ - Error Handle  │ - Code Service  │ - Analyzers │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
```

### Unified API Design

```typescript
// Base OpenDXA API Structure
GET  /                           # Service information and health
GET  /health                     # Health check endpoint
GET  /services                   # Available services list

// Service-specific endpoints
POST /poet/transpile             # POET function transpilation
POST /poet/feedback              # POET feedback submission
GET  /poet/functions/{name}      # POET function status

POST /prompt/rewrite             # Prompt optimization
POST /prompt/analyze             # Prompt analysis
GET  /prompt/templates           # Available prompt templates

POST /magic/generate             # Magic function generation
POST /magic/enhance              # Existing function enhancement
GET  /magic/suggestions          # Code suggestions

POST /code/analyze               # Code analysis and insights
POST /code/optimize              # General code optimization
POST /code/document              # Automatic documentation
```

### Service Registration Architecture

```python
# Service Plugin Interface
class OpenDXAService:
    """Base class for all OpenDXA services"""
    
    def get_name(self) -> str:
        """Service identifier (e.g., 'poet', 'prompt', 'magic')"""
        pass
    
    def get_routes(self) -> APIRouter:
        """FastAPI router with service endpoints"""
        pass
    
    def get_health_status(self) -> Dict[str, Any]:
        """Service health and status information"""
        pass

# Service Registry
class ServiceRegistry:
    """Manages registration and discovery of OpenDXA services"""
    
    def register_service(self, service: OpenDXAService):
        """Register a new service with the platform"""
        pass
    
    def get_available_services(self) -> List[str]:
        """List all registered services"""
        pass
```

## Service Implementations

### 1. POET Transpilation Service (Alpha Priority)

**Endpoints**:
```typescript
POST /poet/transpile
Request: {
  function_code: string;         // Complete function with @poet decorator
  language: "python" | "dana";
  context?: {
    sandbox_context?: any;
    imports: string[];
    module_path?: string;
  };
}
Response: {
  poet_implementation: {
    code: string;                // Enhanced P→O→E→(T) implementation
    language: string;
  };
  metadata: {
    decorator_params: object;
    phases_included: string[];   // ["perceive", "operate", "enforce"] + optional "train"
    original_function_name: string;
    enhancements: string[];
  };
}
```

### 2. Prompt Rewriting Service (Future)

**Endpoints**:
```typescript
POST /prompt/rewrite
Request: {
  original_prompt: string;
  target_model?: string;         // Optimize for specific LLM
  optimization_goals?: string[]; // ["clarity", "specificity", "performance"]
  domain?: string;               // Domain-specific optimization
}
Response: {
  rewritten_prompt: string;
  improvements: string[];
  confidence_score: number;
  optimization_notes: string;
}
```

### 3. Magic Functions Service (Future)

**Endpoints**:
```typescript
POST /magic/generate
Request: {
  description: string;           // Natural language function description
  language: "python" | "typescript" | "javascript";
  context?: {
    existing_code?: string;      // Related code for context
    dependencies?: string[];     // Available libraries
    style_guide?: string;        // Coding standards
  };
}
Response: {
  generated_function: {
    code: string;
    language: string;
    dependencies: string[];
  };
  explanation: string;
  usage_examples: string[];
  test_cases?: string[];
}
```

### 4. General Code Enhancement Service (Future)

**Endpoints**:
```typescript
POST /code/analyze
POST /code/optimize  
POST /code/document
```

## API Configuration & Client Integration

### Environment Configuration
```bash
# Single configuration for all OpenDXA services
AITOMATIC_API_URL=local                           # Local development
AITOMATIC_API_URL=http://localhost:8080           # Local API server
AITOMATIC_API_URL=https://api.aitomatic.com       # Production API
AITOMATIC_API_KEY=sk-ait-xxxxx                    # API authentication
```

### Client SDK Pattern
```python
# Unified client for all services
from opendxa.api.client import OpenDXAClient

client = OpenDXAClient()  # Uses AITOMATIC_API_URL from environment

# Service-specific clients
poet_client = client.poet()
prompt_client = client.prompt()  # Future
magic_client = client.magic()    # Future
```

## Implementation Strategy

### Phase 1: Foundation & POET (Alpha - Current)
- [🔄] **Core API Infrastructure**: FastAPI service with plugin architecture
- [🔄] **POET Service Implementation**: Full transpilation capabilities
- [🔄] **Authentication Framework**: Basic API key authentication
- [🔄] **Documentation System**: OpenAPI 3.0 specification

### Phase 2: Service Expansion (Beta)
- [ ] **Prompt Rewriting Service**: LLM prompt optimization
- [ ] **Magic Functions Service**: Natural language to code generation
- [ ] **Enhanced Authentication**: Role-based access control
- [ ] **Advanced Monitoring**: Metrics, logging, alerting

### Phase 3: Enterprise Features (Gamma)
- [ ] **General Code Service**: Analysis, optimization, documentation
- [ ] **Custom Domain Services**: Specialized industry capabilities
- [ ] **Advanced Security**: OAuth, audit logging, compliance
- [ ] **High Availability**: Load balancing, auto-scaling

## Technical Decisions

### 1. Plugin Architecture
**Decision**: Service registry pattern with dynamic route registration
**Rationale**: Enables independent service development and deployment
**Implementation**: Each service provides routes, health checks, and metadata

### 2. Unified Error Handling
**Decision**: Standardized error response format across all services
**Rationale**: Consistent developer experience and easier client implementation
**Implementation**: Shared exception handlers and response schemas

### 3. OpenAPI First Design
**Decision**: All services must provide OpenAPI 3.0 specifications
**Rationale**: Auto-generated documentation and client SDKs
**Implementation**: FastAPI automatic schema generation with manual enhancement

### 4. Versioning Strategy
**Decision**: URL path versioning (`/v1/poet/transpile`) for major changes
**Rationale**: Clear versioning with backward compatibility
**Implementation**: Version-specific routers with shared business logic

## Quality Gates

### Service Quality Standards
- **API Documentation**: Complete OpenAPI 3.0 specification
- **Error Handling**: Comprehensive error responses with helpful messages
- **Performance**: Response time targets (< 10s for transpilation, < 2s for analysis)
- **Security**: Input validation, rate limiting, authentication
- **Testing**: Unit tests, integration tests, API contract tests

### Platform Quality Standards
- **Availability**: 99.9% uptime target
- **Scalability**: Auto-scaling based on load
- **Monitoring**: Health checks, metrics, alerting
- **Documentation**: Developer guides, API reference, examples

## Security Considerations

### Authentication & Authorization
- **API Key Authentication**: Simple token-based auth for MVP
- **Rate Limiting**: Per-key request limits to prevent abuse
- **Input Validation**: Strict validation of all request parameters
- **Output Sanitization**: Safe handling of generated code content

### Data Protection
- **No Data Persistence**: Stateless service design
- **Secure Transport**: HTTPS/TLS for all communications
- **Audit Logging**: Request/response logging for security monitoring
- **Privacy**: No storage of user code or sensitive information

## Success Metrics

### Platform Metrics
- **Service Adoption**: Number of registered services
- **API Usage**: Requests per service, error rates
- **Developer Experience**: Time to integration, documentation feedback
- **Performance**: Response times, availability metrics

### Business Metrics
- **User Engagement**: Active developers using multiple services
- **Service Quality**: User satisfaction scores per service
- **Growth**: New service onboarding rate
- **Reliability**: Error rates and resolution times

This unified service design positions OpenDXA as a comprehensive AI development platform while maintaining the flexibility to add new capabilities as they're developed.