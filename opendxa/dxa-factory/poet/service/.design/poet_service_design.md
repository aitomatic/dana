# POET Code Generation Service - 3D Design Document

```text
Author: Christopher Nguyen
Date: 2025-06-13
Version: 0.5
Status: Design Phase
```

**Related Documents:**
- [POET Framework Design](../../../../dana/poet/.design/poet_design.md)
- [PubSub Service Design](../../../../common/pubsub/.design/pubsub_design.md)

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

The POET Code Generation Service is a FastAPI-based REST service that provides LLM-powered function enhancement capabilities to Aitomatic agents and external systems. It exposes the core POET functionality as a scalable, secure web service for enterprise deployment.

**Key Innovation**: Transform the POET framework into a production-ready microservice that integrates seamlessly with Aitomatic's agent infrastructure while providing REST API access for external systems.

## Problem Statement

### Current Challenge
The POET framework needs to be exposed as a service that:
- Primarily serves Aitomatic's transpilation workflow for converting Dana code to Python
- Must maintain high reliability for the transpilation pipeline
- Needs to scale to handle concurrent transpilation requests
- Must preserve Dana semantics during enhancement
- Requires enterprise-grade security and monitoring

### User Needs
1. **Aitomatic Transpilation Agents**: Need a reliable service to enhance transpiled Dana code with domain intelligence
2. **Enterprise Ops**: Require monitoring and security for the transpilation pipeline
3. **Developers**: Need clear integration with the transpilation workflow

## Solution Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    POET Service                         │
├─────────────────┬─────────────────┬─────────────────────┤
│  API Layer      │  Core Logic     │  Event System       │
├─────────────────┼─────────────────┼─────────────────────┤
│ - FastAPI       │ - Code Gen      │ - PubSub Client     │
│ - OpenAPI 3.0   │ - Validation    │ - Event Processing  │
│ - Auth/ACL      │ - Templates     │ - Feedback Queue    │
└─────────────────┴─────────────────┴─────────────────────┘
```

### API Endpoints

```typescript
// Function Enhancement
POST /api/v1/functions/enhance
Request:
{
  function_name: string;
  original_code: string;
  domain?: string;
  optimize_for?: string;
  context?: {
    imports: string[];
    dependencies: string[];
    environment: string;
  };
}
Response:
{
  enhanced_code: {
    dana?: string;
    python?: string;
  };
  version: string;
  metadata: {
    domain: string;
    optimizations: string[];
    safety_level: number;
  };
}

// Function Feedback
POST /api/v1/functions/{function_name}/feedback
Request:
{
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
}
Response:
{
  status: "accepted" | "requires_update";
  new_version?: string;
  update_reason?: string;
}

// Function Version Management
GET /api/v1/functions/{function_name}/versions
Response:
{
  versions: Array<{
    version: string;
    created_at: string;
    status: "active" | "deprecated";
    metrics: {
      success_rate: number;
      avg_duration: number;
      error_rate: number;
    };
  }>;
  current_version: string;
}

// Function Execution Events
GET /api/v1/functions/{function_name}/events
Query Parameters:
- start_time: string
- end_time: string
- event_type: string
- limit: number
Response:
{
  events: Array<{
    id: string;
    type: string;
    timestamp: string;
    payload: any;
  }>;
  next_page_token?: string;
}
```

### Event Processing Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  API Endpoints  │     │  Event System   │     │   PubSub Topics │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. Function executed │                       │
         ├─────────────────────►│                       │
         │                      │                       │
         │                      │ 2. Publish execution  │
         │                      │    event              │
         │                      ├──────────────────────►│
         │                      │                       │
         │                      │ 3. Process feedback   │
         │                      │    queue              │
         │                      │◄──────────────────────┤
         │                      │                       │
         │ 4. If feedback       │                       │
         │    requires update   │                       │
         │                      │                       │
         │ 5. Generate new      │                       │
         │    version           │                       │
         │                      │                       │
         │ 6. Publish update    │                       │
         │    event             │                       │
         │                      │◄──────────────────────┤
```

### Storage Structure
```
/poet/
├── functions/
│   └── <function_name>/
│       ├── v1/
│       │   ├── code.dana
│       │   ├── code.py
│       │   ├── params.json
│       │   └── metadata.json
│       └── current -> v1
├── events/
│   ├── pending/
│   └── processed/
└── feedback/
    ├── pending/
    └── processed/
```

## Integration Patterns

### 1. Aitomatic Agent Integration

```python
# Integration endpoint for Aitomatic transpilation agents
@app.post("/v1/aitomatic/enhance")
async def aitomatic_enhance(
    request: AitomaticEnhancementRequest,
    auth: str = Depends(verify_aitomatic_token)
):
    """
    Specialized endpoint for Aitomatic transpilation agents
    """
    # Enhanced request with Aitomatic-specific metadata
    enhanced_request = EnhancementRequest(
        original_code=request.python_code,
        domain=request.domain,
        function_name=request.function_name,
        config=request.config,
        context={
            "source": "aitomatic_transpilation",
            "dana_source": request.dana_source,
            "transpilation_id": request.transpilation_id,
            "agent_id": request.agent_id
        }
    )
    
    # Process enhancement
    result = await enhance_function(enhanced_request, auth)
    
    # Return Aitomatic-compatible response
    return AitomaticEnhancementResponse(
        transpilation_id=request.transpilation_id,
        enhanced_code=result.enhanced_code,
        poet_metadata=result.metadata,
        success=True
    )

class AitomaticEnhancementRequest(BaseModel):
    transpilation_id: str
    agent_id: str
    dana_source: str
    python_code: str
    function_name: str
    domain: str
    config: Dict[str, Any] = {}

class AitomaticEnhancementResponse(BaseModel):
    transpilation_id: str
    enhanced_code: str
    poet_metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
```

### 2. External System Integration

```python
# Generic external system integration
@app.post("/v1/external/enhance")
async def external_enhance(
    request: ExternalEnhancementRequest,
    auth: str = Depends(verify_external_token)
):
    """
    Generic endpoint for external ML/AI systems
    """
    # Map external request to internal format
    internal_request = EnhancementRequest(
        original_code=request.function_code,
        domain=request.domain or "base_reliability",
        optimization_goals=request.objectives,
        config=request.parameters,
        context={
            "source": "external_api",
            "client_id": request.client_id,
            "request_id": request.request_id
        }
    )
    
    return await enhance_function(internal_request, auth)
```

## Security & Authentication

### Authentication Strategy
```python
# opendxa/enterprise/poet/service/auth.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API key authentication"""
    api_key = credentials.credentials
    
    # Validate API key (implement your validation logic)
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key

async def verify_aitomatic_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify Aitomatic-specific authentication"""
    token = credentials.credentials
    
    try:
        # Verify JWT token from Aitomatic
        payload = jwt.decode(
            token, 
            AITOMATIC_PUBLIC_KEY, 
            algorithms=["RS256"]
        )
        
        if payload.get("service") != "aitomatic_transpilation":
            raise HTTPException(status_code=401, detail="Invalid service token")
            
        return token
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def validate_api_key(api_key: str) -> bool:
    """Validate API key against authorized keys"""
    # Implement key validation logic
    # Could check database, cache, or configuration
    return api_key in AUTHORIZED_API_KEYS
```

### Rate Limiting
```python
# opendxa/enterprise/poet/service/rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/enhance")
@limiter.limit("10/minute")
async def enhance_function_rate_limited(
    request: Request,
    enhancement_request: EnhancementRequest,
    auth: str = Depends(security)
):
    """Rate-limited enhancement endpoint"""
    return await enhance_function(enhancement_request, auth)
```

## Monitoring & Observability

### Metrics Collection
```python
# opendxa/enterprise/poet/service/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Metrics
enhancement_requests_total = Counter(
    'poet_enhancement_requests_total',
    'Total enhancement requests',
    ['domain', 'status']
)

enhancement_duration_seconds = Histogram(
    'poet_enhancement_duration_seconds',
    'Enhancement generation time',
    ['domain']
)

active_enhancements = Gauge(
    'poet_active_enhancements',
    'Number of active enhancement requests'
)

# Middleware for metrics collection
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/enhance"):
        start_time = time.time()
        active_enhancements.inc()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            domain = request.url.query_params.get("domain", "unknown")
            status = "success" if response.status_code < 400 else "error"
            
            enhancement_requests_total.labels(domain=domain, status=status).inc()
            enhancement_duration_seconds.labels(domain=domain).observe(time.time() - start_time)
            
            return response
            
        finally:
            active_enhancements.dec()
    else:
        return await call_next(request)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks
```python
@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe"""
    # Check dependencies
    checks = {
        "llm_client": await check_llm_connectivity(),
        "storage": await check_storage_access(),
        "memory": check_memory_usage()
    }
    
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
```

## Deployment Configuration

### Docker Setup
```dockerfile
# opendxa/enterprise/poet/service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash poet
USER poet

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Kubernetes Deployment
```yaml
# opendxa/enterprise/poet/service/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: poet-service
  labels:
    app: poet-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: poet-service
  template:
    metadata:
      labels:
        app: poet-service
    spec:
      containers:
      - name: poet-service
        image: poet-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: POET_LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: poet-secrets
              key: llm-api-key
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## Implementation Plan (3D Methodology)

### 🔄 Phase 1: Core Service Infrastructure (Week 1)
**Goal**: Basic FastAPI service with core endpoints

**Deliverables**:
- [ ] FastAPI application setup (`app.py`)
- [ ] Request/response models (`models.py`)
- [ ] Basic enhancement endpoint (`/v1/enhance`)
- [ ] Health check endpoints (`/health/*`)
- [ ] Configuration management (`config.py`)

**Success Criteria**:
- ✅ Service starts and responds to health checks
- ✅ Basic enhancement endpoint accepts requests
- ✅ OpenAPI documentation generated
- ✅ Docker containerization working

### ⏳ Phase 2: POET Integration (Week 2)  
**Goal**: Integrate POET core functionality

**Deliverables**:
- [ ] Async POET processor (`async_processor.py`)
- [ ] Domain management endpoints (`/v1/domains/*`)
- [ ] Enhancement storage and tracking
- [ ] Error handling and validation

**Success Criteria**:
- ✅ Successful function enhancement via API
- ✅ Multiple domain templates available
- ✅ Enhancement tracking and storage
- ✅ Comprehensive error handling

### ⏳ Phase 3: Security & Authentication (Week 3)
**Goal**: Production-ready security

**Deliverables**:
- [ ] API key authentication (`auth.py`)
- [ ] Aitomatic token verification
- [ ] Rate limiting implementation
- [ ] Security middleware

**Success Criteria**:
- ✅ API key authentication working
- ✅ Aitomatic integration secured
- ✅ Rate limiting prevents abuse
- ✅ Security audit passed

### ⏳ Phase 4: Monitoring & Production Readiness (Week 4)
**Goal**: Full production deployment

**Deliverables**:
- [ ] Prometheus metrics (`monitoring.py`)
- [ ] Structured logging
- [ ] Kubernetes deployment configs
- [ ] Load testing and optimization

**Success Criteria**:
- ✅ Comprehensive metrics collection
- ✅ Kubernetes deployment successful
- ✅ Load testing targets met
- ✅ Production readiness checklist complete

## Quality Gates

### Performance Requirements
- **Response Time**: < 5 seconds for 95% of enhancement requests
- **Throughput**: Handle 100 concurrent requests
- **Memory Usage**: < 2GB per service instance
- **Availability**: 99.9% uptime

### Security Requirements
- **Authentication**: API key and JWT token support
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive request validation
- **Audit Logging**: All requests logged and traceable

### Integration Requirements
- **Aitomatic Compatibility**: Seamless integration with transpilation agents
- **API Standards**: OpenAPI 3.0 specification
- **Monitoring**: Prometheus metrics and health checks
- **Deployment**: Kubernetes-ready with helm charts

## Success Metrics

### Technical Metrics
- **API Response Time**: < 5 seconds P95
- **Error Rate**: < 1% of requests
- **Service Availability**: > 99.9%
- **Resource Usage**: < 2GB memory, < 1 CPU core per instance

### Business Metrics
- **Enhancement Success Rate**: > 95% of generated code compiles and runs
- **User Satisfaction**: > 4.5/5 API usability rating
- **Integration Adoption**: > 90% of Aitomatic agents using POET service
- **External API Usage**: Growth in third-party integrations

## Risk Assessment & Mitigation

### High Risk
**LLM API Dependencies**
- *Risk*: LLM service outages affect availability
- *Mitigation*: Multi-provider support, circuit breakers, caching

**Generated Code Security**
- *Risk*: Generated code may contain vulnerabilities
- *Mitigation*: Code validation, sandboxing, security scanning

### Medium Risk
**Performance Under Load**
- *Risk*: Service degrades under high concurrent load
- *Mitigation*: Async processing, connection pooling, auto-scaling

**API Breaking Changes**
- *Risk*: Service updates break client integrations
- *Mitigation*: API versioning, backward compatibility, deprecation notices

## Future Enhancements

### Post-MVP Features
- **Batch Processing**: Handle multiple enhancements in single request
- **Streaming Responses**: Real-time enhancement progress updates
- **Custom Domains**: User-defined domain templates via API
- **Analytics Dashboard**: Web UI for enhancement analytics
- **A/B Testing**: Compare different enhancement strategies

### Integration Roadmap
- **IDE Plugins**: Direct integration with VSCode, IntelliJ
- **CI/CD Integration**: GitHub Actions, Jenkins plugins
- **MLOps Integration**: Kubeflow, MLflow native support
- **Multi-Language**: Support for TypeScript, Go, Rust function enhancement

This service design provides a production-ready foundation for deploying POET as an enterprise microservice while maintaining integration with Aitomatic's agent infrastructure.

## Service Architecture

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
├─────────────────┬─────────────────┬─────────────────────┤
│  API Layer      │  Core Services  │  Support Services   │
├─────────────────┼─────────────────┼─────────────────────┤
│ - API Gateway   │ - POET Service  │ - Redis Cache       │
│ - Load Balancer │ - LLM Service   │ - Monitoring        │
│ - Auth Service  │ - Event Service │ - Logging           │
└─────────────────┴─────────────────┴─────────────────────┘
```

### Service Scalability

#### 1. Horizontal Scaling
- **API Layer**:
  - Auto-scaling based on request rate
  - Min: 2 replicas, Max: 10 replicas
  - CPU threshold: 70%
  - Memory threshold: 80%

- **Core Services**:
  - Auto-scaling based on queue length
  - Min: 3 replicas, Max: 20 replicas
  - CPU threshold: 60%
  - Memory threshold: 70%

#### 2. Load Distribution
- **Request Routing**:
  - Round-robin load balancing
  - Sticky sessions for long-running operations
  - Circuit breaker for failing instances
  - Health check based routing

- **Queue Management**:
  - Priority queues for different operations
  - Dead letter queues for failed operations
  - Message batching for efficiency
  - Queue monitoring and alerts

#### 3. Resource Management
- **CPU Allocation**:
  - Request: 0.5 CPU
  - Limit: 2 CPU
  - Burst: 4 CPU
  - Throttling on high usage

- **Memory Allocation**:
  - Request: 512MB
  - Limit: 2GB
  - Burst: 4GB
  - OOM killer configuration

### Monitoring & Observability

#### 1. Metrics Collection
- **Service Metrics**:
  - Request rate and latency
  - Error rate and types
  - Resource usage (CPU, memory)
  - Queue length and processing time

- **Business Metrics**:
  - Generation success rate
  - Function execution metrics
  - Feedback processing rate
  - Version update frequency

#### 2. Logging Strategy
- **Log Levels**:
  - ERROR: System errors and failures
  - WARN: Potential issues and warnings
  - INFO: Important state changes
  - DEBUG: Detailed operation info

- **Log Structure**:
  - JSON format for parsing
  - Correlation IDs for tracing
  - Context information
  - Performance metrics

#### 3. Alerting System
- **Critical Alerts**:
  - Service unavailability
  - High error rates
  - Resource exhaustion
  - Security incidents

- **Warning Alerts**:
  - Performance degradation
  - High latency
  - Queue buildup
  - Resource pressure

#### 4. Tracing
- **Distributed Tracing**:
  - Request flow tracking
  - Service dependencies
  - Performance bottlenecks
  - Error propagation

- **Trace Sampling**:
  - 100% for errors
  - 10% for normal requests
  - 50% for slow requests
  - Custom sampling rules

### Deployment Strategy

#### 1. Environment Setup
- **Development**:
  - Single replica
  - Local storage
  - Debug logging
  - Manual scaling

- **Staging**:
  - Multiple replicas
  - Shared storage
  - Production-like config
  - Auto-scaling enabled

- **Production**:
  - High availability
  - Distributed storage
  - Optimized config
  - Full monitoring

#### 2. Deployment Process
- **Rolling Updates**:
  - Max 1 replica down
  - Health check required
  - Rollback on failure
  - Canary deployments

- **Configuration**:
  - Environment variables
  - Config maps
  - Secrets management
  - Feature flags

#### 3. Backup & Recovery
- **Data Backup**:
  - Daily full backup
  - Hourly incremental
  - 30-day retention
  - Cross-region backup

- **Disaster Recovery**:
  - RTO: 1 hour
  - RPO: 1 hour
  - Automated recovery
  - Regular testing