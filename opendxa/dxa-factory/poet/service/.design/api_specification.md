# POET Service API Specification

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: POET Code Generation Service
  description: |
    LLM-powered function enhancement service for Aitomatic agents and external systems.
    
    The POET service transforms simple function implementations into production-ready code with:
    - Domain-specific intelligence (ML monitoring, API operations, etc.)
    - Built-in reliability patterns (retries, error handling, monitoring)
    - Learning capabilities through feedback collection
    
    ## Authentication
    All endpoints require authentication via Bearer token in the Authorization header.
    
    ## Rate Limiting
    - Standard API: 100 requests/minute per API key
    - Aitomatic endpoints: 1000 requests/minute per service token
    
    ## Error Handling
    All errors follow RFC 7807 Problem Details standard.
    
  version: 1.0.0
  contact:
    name: Aitomatic POET Team
    email: poet-support@aitomatic.com
  license:
    name: Proprietary
    
servers:
  - url: https://poet.aitomatic.com/api
    description: Production server
  - url: https://poet-staging.aitomatic.com/api
    description: Staging server
  - url: http://localhost:8080
    description: Local development

security:
  - bearerAuth: []

paths:
  /v1/enhance:
    post:
      summary: Enhance function code
      description: |
        Transform a simple function into production-ready code using POET framework.
        
        The service will:
        1. Analyze the input function and domain
        2. Apply appropriate domain template
        3. Generate enhanced code with reliability patterns
        4. Return enhanced implementation with metadata
        
      operationId: enhanceFunction
      tags:
        - Enhancement
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EnhancementRequest'
            examples:
              ml_monitoring:
                summary: ML Monitoring Enhancement
                value:
                  original_code: |
                    @poet(domain="ml_monitoring")
                    def detect_drift(current_data, reference_data):
                        return {"drift_detected": false, "score": 0.0}
                  domain: ml_monitoring
                  function_name: detect_drift
                  optimization_goals: ["accuracy", "performance"]
                  config:
                    statistical_tests: ["ks", "kl_divergence"]
                    parallel_processing: true
                  context:
                    model_name: customer_churn_model
                    feature_type: continuous
              api_reliability:
                summary: API Reliability Enhancement
                value:
                  original_code: |
                    def fetch_user_data(user_id):
                        return requests.get(f"/api/users/{user_id}").json()
                  domain: api_operations
                  optimization_goals: ["reliability", "performance"]
                  config:
                    max_retries: 3
                    timeout_seconds: 10
      responses:
        '200':
          description: Function successfully enhanced
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnhancementResponse'
              examples:
                success:
                  summary: Successful Enhancement
                  value:
                    enhancement_id: enh_123456789
                    enhanced_code: |
                      def detect_drift_enhanced(current_data, reference_data):
                          # PERCEIVE: Validate inputs and detect data characteristics
                          if not current_data or len(current_data) == 0:
                              return {"drift_detected": False, "score": 0.0, "reason": "No data"}
                          
                          data_type = infer_data_type(current_data)
                          
                          # OPERATE: Apply appropriate statistical tests
                          if data_type == "continuous":
                              statistic, p_value = ks_2samp(reference_data, current_data)
                              method = "ks_test"
                          else:
                              score = calculate_kl_divergence(current_data, reference_data)
                              method = "kl_divergence"
                          
                          # ENFORCE: Validate results and format output
                          result = {
                              "drift_detected": p_value < 0.05 if method == "ks_test" else score > 0.1,
                              "score": statistic if method == "ks_test" else score,
                              "method": method,
                              "confidence": calculate_confidence(len(current_data))
                          }
                          
                          # TRAIN: Emit monitoring events
                          poet_events.emit("drift.detected", {
                              "execution_id": str(uuid.uuid4()),
                              "result": result
                          })
                          
                          return result
                    metadata:
                      version: v1
                      generator: poet-service
                      domain_features: ["statistical_tests", "parallel_processing", "monitoring"]
                      llm_model: gpt-4
                      generation_timestamp: "2024-06-12T22:30:00Z"
                    execution_time_ms: 1250
                    domain_applied: ml_monitoring
                    capabilities_added: ["drift_detection", "error_handling", "monitoring", "statistical_validation"]
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'

  /v1/domains:
    get:
      summary: List available domains
      description: Get list of all available domain templates with their capabilities
      operationId: listDomains
      tags:
        - Domains
      responses:
        '200':
          description: List of available domains
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/DomainInfo'
              examples:
                domains:
                  summary: Available Domains
                  value:
                    - name: ml_monitoring
                      display_name: ML Model Monitoring
                      description: Statistical drift detection and model health monitoring
                      capabilities: ["drift_detection", "statistical_tests", "parallel_processing"]
                      example_use_cases: ["Model drift detection", "Feature monitoring", "Data quality checks"]
                    - name: api_operations
                      display_name: API Operations
                      description: Reliable API client operations with retries and circuit breakers
                      capabilities: ["retry_logic", "circuit_breaker", "rate_limiting"]
                      example_use_cases: ["External API calls", "Microservice communication", "Third-party integrations"]

  /v1/domains/{domain_name}:
    get:
      summary: Get domain details
      description: Get detailed information about a specific domain template
      operationId: getDomainDetails
      tags:
        - Domains
      parameters:
        - name: domain_name
          in: path
          required: true
          schema:
            type: string
            enum: [ml_monitoring, api_operations, customer_service, financial_risk, base_reliability]
          example: ml_monitoring
      responses:
        '200':
          description: Domain details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DomainDetails'
        '404':
          $ref: '#/components/responses/NotFound'

  /v1/feedback:
    post:
      summary: Submit enhancement feedback
      description: |
        Submit feedback about an enhancement's performance for the learning system.
        
        This endpoint enables the continuous learning aspect of POET by collecting:
        - Performance metrics from production usage
        - User satisfaction and success indicators
        - Error reports and improvement suggestions
        
      operationId: submitFeedback
      tags:
        - Feedback
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FeedbackRequest'
            examples:
              success_feedback:
                summary: Successful Enhancement Feedback
                value:
                  enhancement_id: enh_123456789
                  feedback_type: performance_metrics
                  success: true
                  performance_metrics:
                    accuracy: 0.94
                    false_positive_rate: 0.06
                    execution_time_ms: 250
                  user_comments: "Drift detection working well, reduced false positives significantly"
                  context:
                    model_name: customer_churn_model
                    production_environment: true
              failure_feedback:
                summary: Failed Enhancement Feedback
                value:
                  enhancement_id: enh_987654321
                  feedback_type: error_report
                  success: false
                  user_comments: "Generated code failed on categorical data, needs KL divergence"
                  context:
                    error_type: "statistical_test_failure"
                    data_type: "categorical"
      responses:
        '200':
          description: Feedback received successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: feedback_received
                  feedback_id:
                    type: string
                    example: fb_123456789
                  processed_at:
                    type: string
                    format: date-time
                    example: "2024-06-12T22:30:00Z"
        '400':
          $ref: '#/components/responses/BadRequest'

  /v1/aitomatic/enhance:
    post:
      summary: Aitomatic agent enhancement (Internal)
      description: |
        Specialized endpoint for Aitomatic transpilation agents.
        
        This endpoint provides optimized integration for the Aitomatic ecosystem:
        - Direct integration with transpilation workflow
        - Enhanced metadata tracking
        - Automatic correlation with DANA source code
        
        **Note**: This endpoint requires Aitomatic service authentication.
        
      operationId: aitomaticEnhance
      tags:
        - Aitomatic Integration
      security:
        - aitomaticAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AitomaticEnhancementRequest'
      responses:
        '200':
          description: Enhancement completed for Aitomatic agent
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AitomaticEnhancementResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalError'

  /health:
    get:
      summary: Basic health check
      description: Simple health check endpoint
      operationId: healthCheck
      tags:
        - Health
      security: []
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: healthy
                  service:
                    type: string
                    example: poet-generation
                  timestamp:
                    type: string
                    format: date-time
                    example: "2024-06-12T22:30:00Z"

  /health/live:
    get:
      summary: Liveness probe
      description: Kubernetes liveness probe endpoint
      operationId: livenessProbe
      tags:
        - Health
      security: []
      responses:
        '200':
          description: Service is alive
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: alive

  /health/ready:
    get:
      summary: Readiness probe
      description: Kubernetes readiness probe endpoint
      operationId: readinessProbe
      tags:
        - Health
      security: []
      responses:
        '200':
          description: Service is ready
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: ready
                  checks:
                    type: object
                    properties:
                      llm_client:
                        type: boolean
                      storage:
                        type: boolean
                      memory:
                        type: boolean
        '503':
          description: Service not ready
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: not_ready
                  checks:
                    type: object

  /metrics:
    get:
      summary: Prometheus metrics
      description: Prometheus metrics endpoint for monitoring
      operationId: getMetrics
      tags:
        - Monitoring
      security: []
      responses:
        '200':
          description: Prometheus metrics
          content:
            text/plain:
              schema:
                type: string
                example: |
                  # HELP poet_enhancement_requests_total Total enhancement requests
                  # TYPE poet_enhancement_requests_total counter
                  poet_enhancement_requests_total{domain="ml_monitoring",status="success"} 42
                  # HELP poet_enhancement_duration_seconds Enhancement generation time
                  # TYPE poet_enhancement_duration_seconds histogram
                  poet_enhancement_duration_seconds_bucket{domain="ml_monitoring",le="1.0"} 15

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: API key or JWT token for authentication
    aitomaticAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: Aitomatic service authentication token

  schemas:
    EnhancementRequest:
      type: object
      required:
        - original_code
      properties:
        original_code:
          type: string
          description: Original function code to enhance
          example: |
            @poet(domain="ml_monitoring")
            def detect_drift(data):
                return {"drift_detected": false}
        domain:
          type: string
          enum: [ml_monitoring, api_operations, customer_service, financial_risk, base_reliability]
          default: base_reliability
          description: Domain template to use for enhancement
        function_name:
          type: string
          description: Function name (auto-detected if not provided)
          example: detect_drift
        optimization_goals:
          type: array
          items:
            type: string
            enum: [accuracy, performance, reliability, cost, security]
          description: Optimization objectives for the enhancement
          example: ["accuracy", "performance"]
        config:
          type: object
          additionalProperties: true
          description: Additional configuration parameters
          example:
            statistical_tests: ["ks", "kl_divergence"]
            parallel_processing: true
        context:
          type: object
          additionalProperties: true
          description: Execution context metadata
          example:
            model_name: customer_churn_model
            feature_type: continuous

    EnhancementResponse:
      type: object
      required:
        - enhancement_id
        - enhanced_code
        - metadata
        - execution_time_ms
        - domain_applied
        - capabilities_added
      properties:
        enhancement_id:
          type: string
          description: Unique enhancement identifier
          example: enh_123456789
        enhanced_code:
          type: string
          description: Generated enhanced function code
          example: "def detect_drift_enhanced(data): # POET generated code..."
        metadata:
          type: object
          additionalProperties: true
          description: Enhancement metadata
          example:
            version: v1
            generator: poet-service
            domain_features: ["statistical_tests", "parallel_processing"]
        execution_time_ms:
          type: integer
          description: Generation time in milliseconds
          example: 1250
        domain_applied:
          type: string
          description: Domain template used
          example: ml_monitoring
        capabilities_added:
          type: array
          items:
            type: string
          description: List of capabilities added to the function
          example: ["drift_detection", "error_handling", "monitoring"]

    FeedbackRequest:
      type: object
      required:
        - enhancement_id
        - feedback_type
        - success
      properties:
        enhancement_id:
          type: string
          description: Enhancement this feedback relates to
          example: enh_123456789
        feedback_type:
          type: string
          enum: [performance_metrics, error_report, user_satisfaction, production_usage]
          description: Type of feedback being submitted
        success:
          type: boolean
          description: Whether the enhancement was successful
        performance_metrics:
          type: object
          additionalProperties:
            type: number
          description: Quantitative performance measurements
          example:
            accuracy: 0.94
            false_positive_rate: 0.06
            execution_time_ms: 250
        user_comments:
          type: string
          description: Free-form user feedback
          example: "Drift detection working well, reduced false positives significantly"
        context:
          type: object
          additionalProperties: true
          description: Additional context for the feedback
          example:
            model_name: customer_churn_model
            production_environment: true

    DomainInfo:
      type: object
      required:
        - name
        - display_name
        - description
        - capabilities
        - example_use_cases
      properties:
        name:
          type: string
          description: Domain identifier
          example: ml_monitoring
        display_name:
          type: string
          description: Human-readable domain name
          example: ML Model Monitoring
        description:
          type: string
          description: Domain description
          example: Statistical drift detection and model health monitoring
        capabilities:
          type: array
          items:
            type: string
          description: List of domain capabilities
          example: ["drift_detection", "statistical_tests", "parallel_processing"]
        example_use_cases:
          type: array
          items:
            type: string
          description: Common use cases for this domain
          example: ["Model drift detection", "Feature monitoring", "Data quality checks"]

    DomainDetails:
      allOf:
        - $ref: '#/components/schemas/DomainInfo'
        - type: object
          properties:
            template_preview:
              type: string
              description: Preview of the domain template
              example: "Generate enhanced Python for ML monitoring with statistical tests..."
            configuration_options:
              type: object
              additionalProperties: true
              description: Available configuration options
              example:
                statistical_tests:
                  type: array
                  options: ["ks", "kl_divergence", "chi_square"]
                parallel_processing:
                  type: boolean
                  default: true
            example_transformations:
              type: array
              items:
                type: object
                properties:
                  input:
                    type: string
                  output:
                    type: string
              description: Example input/output transformations

    AitomaticEnhancementRequest:
      type: object
      required:
        - transpilation_id
        - agent_id
        - dana_source
        - python_code
        - function_name
        - domain
      properties:
        transpilation_id:
          type: string
          description: Unique transpilation request identifier
          example: trans_123456789
        agent_id:
          type: string
          description: Aitomatic agent identifier
          example: agent_ml_transpiler_v1
        dana_source:
          type: string
          description: Original DANA source code
          example: |
            @poet(domain="ml_monitoring")
            def detect_drift(current_data: list[float], reference_data: list[float]) -> dict:
                return {"drift_detected": false, "score": 0.0}
        python_code:
          type: string
          description: Transpiled Python code
          example: |
            def detect_drift(current_data, reference_data):
                return {"drift_detected": False, "score": 0.0}
        function_name:
          type: string
          description: Function name
          example: detect_drift
        domain:
          type: string
          description: POET domain to apply
          example: ml_monitoring
        config:
          type: object
          additionalProperties: true
          description: Enhancement configuration
          default: {}

    AitomaticEnhancementResponse:
      type: object
      required:
        - transpilation_id
        - enhanced_code
        - poet_metadata
        - success
      properties:
        transpilation_id:
          type: string
          description: Original transpilation request identifier
          example: trans_123456789
        enhanced_code:
          type: string
          description: POET-enhanced function code
        poet_metadata:
          type: object
          additionalProperties: true
          description: POET enhancement metadata
        success:
          type: boolean
          description: Whether enhancement was successful
        error_message:
          type: string
          description: Error message if enhancement failed
          nullable: true

    Error:
      type: object
      required:
        - type
        - title
        - status
        - detail
      properties:
        type:
          type: string
          format: uri
          description: URI identifying the problem type
          example: "https://poet.aitomatic.com/errors/invalid-domain"
        title:
          type: string
          description: Short, human-readable summary
          example: "Invalid Domain"
        status:
          type: integer
          description: HTTP status code
          example: 400
        detail:
          type: string
          description: Human-readable explanation
          example: "The specified domain 'invalid_domain' is not supported"
        instance:
          type: string
          format: uri
          description: URI identifying the specific occurrence
          example: "/v1/enhance"

  responses:
    BadRequest:
      description: Bad request - invalid input
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            invalid_domain:
              summary: Invalid Domain
              value:
                type: "https://poet.aitomatic.com/errors/invalid-domain"
                title: "Invalid Domain"
                status: 400
                detail: "The specified domain 'invalid_domain' is not supported"
                instance: "/v1/enhance"
            invalid_code:
              summary: Invalid Code
              value:
                type: "https://poet.aitomatic.com/errors/invalid-code"
                title: "Invalid Function Code"
                status: 400
                detail: "The provided code could not be parsed as a valid Python function"
                instance: "/v1/enhance"

    Unauthorized:
      description: Unauthorized - invalid or missing authentication
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            missing_token:
              summary: Missing Authentication
              value:
                type: "https://poet.aitomatic.com/errors/unauthorized"
                title: "Authentication Required"
                status: 401
                detail: "Bearer token is required for this endpoint"
                instance: "/v1/enhance"

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            domain_not_found:
              summary: Domain Not Found
              value:
                type: "https://poet.aitomatic.com/errors/not-found"
                title: "Domain Not Found"
                status: 404
                detail: "The requested domain 'unknown_domain' was not found"
                instance: "/v1/domains/unknown_domain"

    RateLimited:
      description: Rate limit exceeded
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            rate_limited:
              summary: Rate Limit Exceeded
              value:
                type: "https://poet.aitomatic.com/errors/rate-limited"
                title: "Rate Limit Exceeded"
                status: 429
                detail: "Rate limit of 100 requests per minute exceeded"
                instance: "/v1/enhance"
      headers:
        Retry-After:
          description: Number of seconds to wait before retrying
          schema:
            type: integer
            example: 60

    InternalError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            llm_error:
              summary: LLM Service Error
              value:
                type: "https://poet.aitomatic.com/errors/llm-service-error"
                title: "LLM Service Unavailable"
                status: 500
                detail: "The LLM service is temporarily unavailable"
                instance: "/v1/enhance"
```

## API Usage Examples

### Python Client Example

```python
import requests
import json

class POETClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def enhance_function(self, code: str, domain: str = "base_reliability", **kwargs):
        """Enhance a function using POET service"""
        payload = {
            "original_code": code,
            "domain": domain,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/v1/enhance",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def get_domains(self):
        """Get available domains"""
        response = requests.get(
            f"{self.base_url}/v1/domains",
            headers=self.headers
        )
        return response.json()
    
    def submit_feedback(self, enhancement_id: str, success: bool, **kwargs):
        """Submit feedback for an enhancement"""
        payload = {
            "enhancement_id": enhancement_id,
            "feedback_type": "performance_metrics",
            "success": success,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/v1/feedback",
            headers=self.headers,
            json=payload
        )
        return response.json()

# Usage example
client = POETClient("https://poet.aitomatic.com/api", "your_api_key")

# Enhance a drift detection function
code = """
@poet(domain="ml_monitoring")
def detect_drift(current_data, reference_data):
    return {"drift_detected": False, "score": 0.0}
"""

result = client.enhance_function(
    code=code,
    domain="ml_monitoring",
    optimization_goals=["accuracy", "performance"],
    config={
        "statistical_tests": ["ks", "kl_divergence"],
        "parallel_processing": True
    }
)

print(f"Enhancement ID: {result['enhancement_id']}")
print(f"Enhanced code:\n{result['enhanced_code']}")

# Submit feedback
client.submit_feedback(
    enhancement_id=result['enhancement_id'],
    success=True,
    performance_metrics={
        "accuracy": 0.94,
        "execution_time_ms": 250
    }
)
```

### cURL Examples

```bash
# Enhance a function
curl -X POST "https://poet.aitomatic.com/api/v1/enhance" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "original_code": "@poet(domain=\"ml_monitoring\")\ndef detect_drift(data):\n    return {\"drift\": False}",
    "domain": "ml_monitoring",
    "optimization_goals": ["accuracy"],
    "config": {
      "statistical_tests": ["ks", "kl_divergence"]
    }
  }'

# Get available domains
curl -X GET "https://poet.aitomatic.com/api/v1/domains" \
  -H "Authorization: Bearer your_api_key"

# Submit feedback
curl -X POST "https://poet.aitomatic.com/api/v1/feedback" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "enhancement_id": "enh_123456789",
    "feedback_type": "performance_metrics",
    "success": true,
    "performance_metrics": {
      "accuracy": 0.94,
      "execution_time_ms": 250
    }
  }'

# Health check
curl -X GET "https://poet.aitomatic.com/api/health"
```

This API specification provides a complete interface for the POET code generation service, supporting both external integrations and Aitomatic agent workflows.