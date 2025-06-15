# OpenDXA API Service - 3D Design Document

```text
Author: Christopher Nguyen
Date: 2025-06-13
Version: 0.5
Status: Design Phase
```

## Overview

The OpenDXA API Service provides a unified REST platform for all OpenDXA services, with POET being primarily a Dana language feature with Python support for development and testing.

## Architecture

### Service Components

1. **Core API Server**
   - FastAPI-based server
   - Authentication/Authorization
   - Request validation
   - Response formatting

2. **Service Modules**
   - POET Service (Dana-first)
   - Other OpenDXA services
   - Service discovery
   - Health monitoring

3. **Client Libraries**
   - Dana client library
   - Python client library
   - Type definitions
   - Documentation

### POET Service Integration

#### Code Generation and Caching
1. **Storage Structure**
   ```
   .dana/
   ├── poet/                     # POET-specific storage
   │   ├── {function_name}/
   │   │   ├── v{version}/
   │   │   │   ├── enhanced.na      # Enhanced Dana function code
   │   │   │   ├── train.na         # Train method (if optimize_for specified)
   │   │   │   └── metadata.json    # Function metadata
   │   ├── cache/                   # Generated code cache
   │   │   └── {function_name}/
   │   │       └── {source_hash}.json  # Cached generated code
   │   ├── executions/              # Execution contexts
   │   └── feedback/               # Feedback data
   ├── magic/                    # Magic function cache (future)
   └── other/                    # Other Dana features (future)
   ```

2. **Caching Strategy**
   - Cache key: `{function_name}_{source_hash}`
   - Cache includes:
     - Generated code (Dana or Python)
     - Source code hash
     - Generation metadata
     - Timestamp
   - Cache invalidation:
     - Source code changes
     - POET version changes
     - Cache corruption

3. **API Endpoints**
   ```
   POST /api/v1/poet/enhance
   - Input: Dana function code
   - Output: Enhanced Dana code or Python fallback
   - Cache: Check before generation

   GET /api/v1/poet/cache/{function_name}
   - Input: Function name
   - Output: Cached code if available
   - Cache: Direct lookup

   DELETE /api/v1/poet/cache/{function_name}
   - Input: Function name
   - Output: Success/failure
   - Cache: Invalidate cache
   ```

4. **Python Fallback**
   - Primary goal: Generate Dana code
   - Fallback to Python when:
     1. Function requires Python-specific features
     2. LLM determines Python is more appropriate
     3. Dana enhancement fails
   - Fallback process:
     1. Log fallback reason
     2. Generate Python implementation
     3. Store in cache with fallback metadata
     4. Monitor performance for potential Dana migration

## API Endpoints

### POET Service

1. **Function Enhancement**
   - `POST /poet/transpile`
   - Input: Function code, configuration
   - Output: Enhanced function code

2. **Feedback Processing**
   - `POST /poet/feedback`
   - Input: Execution result, feedback
   - Output: Learning status

3. **Function Management**
   - `GET /poet/functions`
   - `GET /poet/functions/{id}`
   - `DELETE /poet/functions/{id}`

## Client Libraries

### Dana Client (Primary)

```dana
# Dana client example
import poet_client

@poet(domain="ml_monitoring")
def detect_drift(current_data, reference_data):
    return {"drift_detected": false, "score": 0.0}
```

### Python Client (Secondary)

```python
# Python client example (for development/testing)
from opendxa.api.client import APIClient

client = APIClient(base_uri="http://localhost:8080")
response = client.post("/poet/transpile", {
    "function_code": "...",
    "config": {...}
})
```

## Configuration

### Environment Variables

```bash
# API Service Configuration
AITOMATIC_API_URL=local                           # Default (localhost:8080)
AITOMATIC_API_URL=http://localhost:8080           # Local server (explicit)
AITOMATIC_API_URL=https://api.aitomatic.com       # Production API
AITOMATIC_API_KEY=sk-ait-xxxxx                    # API key (production only)
```

## Security

1. **Authentication**
   - API key validation
   - Rate limiting
   - Request signing

2. **Authorization**
   - Role-based access
   - Resource permissions
   - Audit logging

## Monitoring

1. **Metrics**
   - Request latency
   - Error rates
   - Resource usage
   - Function performance

2. **Logging**
   - Request/response logs
   - Error tracking
   - Performance metrics
   - Security events

## Future Enhancements

1. **Additional Services**
   - Agent management
   - Resource management
   - System monitoring

2. **Advanced Features**
   - WebSocket support
   - GraphQL API
   - Batch operations
   - Caching layer