# POET Domain Templates

## Overview

Domain templates are the core mechanism by which POET encodes domain-specific intelligence. Instead of complex plugin architectures, POET uses simple text templates that the LLM understands to generate appropriate enhancements for different domains.

## Template Architecture

### Base Template Structure
```python
class DomainTemplate:
    def __init__(self, name: str, description: str, template: str, requirements: list[str]):
        self.name = name
        self.description = description
        self.template = template
        self.requirements = requirements
    
    def format(self, function_name: str, original_code: str, config: dict) -> str:
        return self.template.format(
            function_name=function_name,
            original_code=original_code,
            domain_requirements="\n".join(self.requirements),
            **config
        )
```

### Template Categories

1. **Reliability Templates** - Basic error handling, retries, timeouts
2. **Domain-Specific Templates** - ML monitoring, API operations, customer service
3. **Optimization Templates** - Performance, cost, accuracy optimization
4. **Integration Templates** - Third-party service integration patterns

## Core Domain Templates

### 1. Base Reliability Template

```python
BASE_RELIABILITY_TEMPLATE = """
Generate enhanced Python implementation for {function_name}.
Domain: General Reliability

Requirements:
- Perceive: Input validation, type checking, edge case detection
- Operate: Retry logic with exponential backoff, timeout handling, graceful degradation
- Enforce: Output validation, consistent error handling, logging
- Train: Execution tracking, performance metrics, error reporting

Original function:
{original_code}

Generate complete enhanced function with reliability patterns.
Include proper error handling, retries, and monitoring hooks.
Maintain the original function signature and return type.
"""

RELIABILITY_REQUIREMENTS = [
    "Add comprehensive input validation",
    "Implement retry logic with exponential backoff",
    "Include timeout handling for operations",
    "Add structured logging and error reporting",
    "Provide graceful degradation on failures",
    "Include execution time tracking",
    "Maintain original function contract"
]
```

### 2. ML Monitoring Template

```python
ML_MONITORING_TEMPLATE = """
Generate enhanced Python implementation for {function_name}.
Domain: ML Model Monitoring

Requirements:
- Perceive: Data type detection, statistical validation, missing value handling
- Operate: Statistical tests (KS, KL divergence, Chi-square), parallel processing, adaptive windowing
- Enforce: Statistical significance validation, confidence intervals, alert thresholds
- Train: Monitoring metrics, drift events, performance tracking

Statistical Tests to Consider:
- Kolmogorov-Smirnov test for continuous distributions
- KL divergence for categorical distributions
- Chi-square test for categorical data
- Mann-Whitney U test for non-parametric data
- Population Stability Index (PSI) for feature stability

Windowing Strategies:
- Fixed-size sliding windows
- Adaptive windows based on data velocity
- Time-based windows for temporal data
- Stratified sampling for large datasets

Original function:
{original_code}

Generate complete enhanced function with ML monitoring intelligence.
Choose appropriate statistical tests based on data characteristics.
Include parallel processing for multiple features.
Add comprehensive monitoring and alerting capabilities.
"""

ML_MONITORING_REQUIREMENTS = [
    "Automatically detect data types (continuous, categorical, mixed)",
    "Select appropriate statistical tests based on data characteristics",
    "Implement parallel processing for multiple features",
    "Add adaptive windowing strategies",
    "Include feature importance weighting",
    "Generate actionable drift recommendations",
    "Provide confidence scores and statistical significance",
    "Handle edge cases (sparse data, missing values, schema changes)",
    "Emit structured monitoring events for learning",
    "Support real-time and batch processing modes"
]
```

### 3. API Operations Template

```python
API_OPERATIONS_TEMPLATE = """
Generate enhanced Python implementation for {function_name}.
Domain: API Operations

Requirements:
- Perceive: Request validation, authentication, rate limit detection
- Operate: Circuit breaker pattern, retry with jitter, connection pooling
- Enforce: Response validation, SLA compliance, security checks
- Train: API metrics, performance tracking, error analytics

API Patterns to Include:
- Circuit breaker for downstream service protection
- Exponential backoff with jitter for retries
- Connection pooling and keep-alive
- Request/response compression
- Timeout handling with fallback strategies
- Rate limiting and backpressure

Security Considerations:
- Input sanitization and validation
- Authentication token management
- SSL/TLS verification
- Request signing where applicable
- Sensitive data redaction in logs

Original function:
{original_code}

Generate complete enhanced function with API reliability patterns.
Include proper error handling, circuit breakers, and monitoring.
Ensure security best practices are followed.
"""

API_OPERATIONS_REQUIREMENTS = [
    "Implement circuit breaker pattern for fault tolerance",
    "Add exponential backoff with jitter for retries",
    "Include connection pooling and reuse",
    "Add comprehensive request/response validation",
    "Implement rate limiting and backpressure handling",
    "Include security validations and input sanitization",
    "Add structured API metrics and monitoring",
    "Handle various HTTP error codes appropriately",
    "Provide fallback strategies for service unavailability",
    "Include authentication and authorization handling"
]
```

### 4. Customer Service Template

```python
CUSTOMER_SERVICE_TEMPLATE = """
Generate enhanced Python implementation for {function_name}.
Domain: Customer Service

Requirements:
- Perceive: Sentiment analysis, urgency detection, context understanding
- Operate: Response personalization, escalation logic, knowledge base integration
- Enforce: Professional tone, policy compliance, response quality
- Train: Satisfaction tracking, interaction analytics, improvement feedback

Customer Service Patterns:
- Sentiment analysis for emotional tone detection
- Urgency classification (high, medium, low priority)
- Context preservation across conversation turns
- Automated escalation triggers
- Knowledge base and FAQ integration
- Response quality validation

Quality Assurance:
- Professional tone enforcement
- Policy compliance checking
- Appropriate response length
- Empathy and understanding indicators
- Resolution effectiveness tracking

Original function:
{original_code}

Generate complete enhanced function with customer service intelligence.
Include sentiment analysis, escalation logic, and quality assurance.
Ensure responses are helpful, professional, and compliant.
"""

CUSTOMER_SERVICE_REQUIREMENTS = [
    "Analyze customer sentiment and emotional state",
    "Detect urgency levels and escalation triggers",
    "Maintain context across conversation turns",
    "Ensure professional and empathetic tone",
    "Validate policy compliance in responses",
    "Include knowledge base integration",
    "Track customer satisfaction indicators",
    "Provide response quality scoring",
    "Handle multiple languages and cultural contexts",
    "Include privacy and data protection measures"
]
```

### 5. Financial Risk Assessment Template

```python
FINANCIAL_RISK_TEMPLATE = """
Generate enhanced Python implementation for {function_name}.
Domain: Financial Risk Assessment

Requirements:
- Perceive: Data quality validation, regulatory compliance, risk factor identification
- Operate: Risk scoring models, stress testing, scenario analysis
- Enforce: Regulatory reporting, audit trails, risk thresholds
- Train: Model performance tracking, risk prediction accuracy, regulatory feedback

Risk Assessment Patterns:
- Multi-factor risk scoring models
- Stress testing under adverse scenarios
- Regulatory compliance validation
- Audit trail generation
- Real-time risk monitoring
- Portfolio optimization constraints

Regulatory Considerations:
- Basel III compliance for banking
- GDPR for data protection
- SOX for financial reporting
- MiFID II for investment services
- Regional regulatory requirements

Original function:
{original_code}

Generate complete enhanced function with financial risk intelligence.
Include regulatory compliance, audit trails, and risk monitoring.
Ensure all calculations are transparent and auditable.
"""

FINANCIAL_RISK_REQUIREMENTS = [
    "Implement multi-factor risk scoring models",
    "Add stress testing and scenario analysis",
    "Ensure regulatory compliance validation",
    "Generate comprehensive audit trails",
    "Include real-time risk threshold monitoring",
    "Provide transparent calculation methodologies",
    "Handle various asset classes and risk types",
    "Include portfolio correlation analysis",
    "Add regulatory reporting capabilities",
    "Ensure data privacy and security compliance"
]
```

## Template Selection Logic

```python
class DomainTemplateSelector:
    def __init__(self):
        self.templates = {
            "base": BaseReliabilityTemplate(),
            "ml_monitoring": MLMonitoringTemplate(),
            "api": APIOperationsTemplate(),
            "customer_service": CustomerServiceTemplate(),
            "financial_risk": FinancialRiskTemplate()
        }
    
    def select_template(self, domain: str, function_context: dict) -> DomainTemplate:
        """Select appropriate template based on domain and context"""
        
        # Direct domain match
        if domain in self.templates:
            return self.templates[domain]
        
        # Infer domain from function characteristics
        inferred_domain = self._infer_domain(function_context)
        if inferred_domain:
            return self.templates[inferred_domain]
        
        # Default to base reliability
        return self.templates["base"]
    
    def _infer_domain(self, context: dict) -> str:
        """Infer domain from function characteristics"""
        
        # Check imports and dependencies
        imports = context.get("imports", [])
        if any("requests" in imp or "http" in imp for imp in imports):
            return "api"
        
        if any("sklearn" in imp or "numpy" in imp or "pandas" in imp for imp in imports):
            return "ml_monitoring"
        
        # Check function parameters
        params = context.get("parameters", [])
        if any("customer" in param or "query" in param for param in params):
            return "customer_service"
        
        # Check for financial keywords
        keywords = context.get("keywords", [])
        financial_keywords = ["risk", "portfolio", "price", "trading", "investment"]
        if any(keyword in financial_keywords for keyword in keywords):
            return "financial_risk"
        
        return None
```

## Template Customization

### Configuration-Based Customization
```python
@poet(
    domain="ml_monitoring",
    config={
        "statistical_tests": ["ks", "kl_divergence"],
        "window_strategy": "adaptive",
        "parallel_processing": True,
        "alert_threshold": 0.05
    }
)
def detect_drift(current_data, reference_data):
    return basic_drift_check(current_data, reference_data)
```

### Capability-Based Enhancement
```python
@poet(
    domain="ml_monitoring",
    capabilities=["drift_detection", "anomaly_detection", "performance_tracking"]
)
def comprehensive_monitor(model_data):
    return simple_monitor(model_data)
```

## Template Evolution and Learning

### Feedback-Driven Template Improvement
```python
class TemplateEvolution:
    def update_template_based_on_feedback(self, domain: str, feedback_patterns: dict):
        """Update template based on production feedback"""
        
        template = self.templates[domain]
        
        # Common failure patterns inform template updates
        if feedback_patterns["common_failures"]:
            new_requirements = self._generate_requirements_from_failures(
                feedback_patterns["common_failures"]
            )
            template.requirements.extend(new_requirements)
        
        # Performance issues inform optimization patterns
        if feedback_patterns["performance_issues"]:
            optimization_patterns = self._generate_optimization_patterns(
                feedback_patterns["performance_issues"]
            )
            template.template += f"\n\nOptimization Patterns:\n{optimization_patterns}"
        
        # Update template version
        template.version += 1
        template.last_updated = time.time()
```

## Best Practices for Template Design

### 1. Clear Structure
- Follow P.O.E.T. stages consistently
- Provide specific, actionable requirements
- Include domain-specific patterns and considerations

### 2. Comprehensive Coverage
- Address common use cases in the domain
- Include edge case handling
- Provide fallback strategies

### 3. Learning Integration
- Include monitoring and tracking hooks
- Emit structured events for feedback collection
- Support iterative improvement

### 4. Security and Compliance
- Address domain-specific security requirements
- Include regulatory compliance where applicable
- Ensure data privacy and protection

### 5. Performance Considerations
- Include scalability patterns
- Address resource constraints
- Provide optimization strategies

## Template Testing and Validation

### Template Quality Metrics
```python
class TemplateValidator:
    def validate_template(self, template: DomainTemplate) -> ValidationResult:
        """Validate template quality and completeness"""
        
        validation_results = {
            "structure_valid": self._validate_structure(template),
            "requirements_complete": self._validate_requirements(template),
            "examples_working": self._test_template_examples(template),
            "domain_coverage": self._assess_domain_coverage(template)
        }
        
        return ValidationResult(validation_results)
```

This template system enables POET to generate domain-specific enhancements that go far beyond basic reliability patterns, providing deep domain intelligence that would typically require extensive manual development.