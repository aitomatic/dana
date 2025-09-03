# POET Architecture: Simple Functions + Runtime Enhancement

This document describes how POET transforms simple business functions into enterprise-grade systems through runtime infrastructure and domain intelligence.

## 🏗️ Core Architecture Principle

**Engineers write simple business logic. POET runtime provides enterprise capabilities.**

```dana
# What Engineers Write (5-10 lines)
@poet(domain="financial_services")
def assess_credit_risk(credit_score: int, income: float, debt_ratio: float) -> str:
    if credit_score >= 750 and debt_ratio <= 0.3:
        return "approved"
    elif credit_score >= 650 and debt_ratio <= 0.45:
        return "conditional"
    else:
        return "declined"

# What POET Runtime Automatically Adds
# P: Input normalization ("excellent"→780, "$50K"→50000, "25%"→0.25)
# O: Retry logic, timeout handling, error recovery
# E: FCRA compliance validation, audit trail generation
# T: Optional parameter learning (retry/timeout optimization)
```

## 🔄 POET Pipeline Implementation

### Current Implementation: POEExecutor
Located in `opendxa/dana/poet/mvp_poet.py`

```python
class POEExecutor(Loggable):
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # P: Perceive - Domain plugin input processing
            perceived_input = self._perceive(args, kwargs)
            
            # O: Operate - Your function + reliability infrastructure
            operation_result = self._operate_with_retry(func, perceived_input)
            
            # E: Enforce - Domain plugin output validation
            final_result = self._enforce(operation_result, perceived_input)
            
            # T: Train - Optional parameter learning
            if self.config.enable_training:
                self._train(perceived_input, operation_result)
            
            return final_result
        return wrapper
```

### P-Stage: Perceive (Input Processing)
**Who**: Domain plugins  
**What**: Transform varied input formats into standardized data

```python
def _perceive(self, args, kwargs) -> Dict[str, Any]:
    if self.domain_plugin:
        return self.domain_plugin.process_inputs(args, kwargs)
    return {"args": args, "kwargs": kwargs}
```

**Examples by Domain**:
- **Financial**: `"excellent"` → 780, `"$50K"` → 50000.0, `"25%"` → 0.25
- **Building**: Temperature unit conversion, occupancy normalization
- **LLM**: Prompt optimization, context formatting

### O-Stage: Operate (Execution + Reliability)
**Who**: POEExecutor runtime  
**What**: Execute your simple function with enterprise reliability

```python
def _operate_with_retry(self, func, perceived_input):
    for attempt in range(self.config.retries):
        try:
            with timeout(self.config.timeout):
                result = func(*perceived_input["args"], **perceived_input["kwargs"])
                return {"result": result, "attempts": attempt + 1}
        except (TimeoutError, RetryableError) as e:
            if attempt == self.config.retries - 1:
                raise OperateError(f"Failed after {self.config.retries} attempts") from e
            sleep(exponential_backoff(attempt))
```

**Provides**:
- Automatic retry logic with exponential backoff
- Timeout handling and monitoring
- Error recovery and categorization
- Performance metrics collection

### E-Stage: Enforce (Output Validation)
**Who**: Domain plugins  
**What**: Add compliance, validation, and audit trails

```python
def _enforce(self, operation_result, perceived_input):
    if self.domain_plugin:
        return self.domain_plugin.validate_output(operation_result, perceived_input)
    return operation_result["result"]
```

**Examples by Domain**:
- **Financial**: FCRA compliance checking, audit trail generation
- **Building**: Safety interlock validation, energy efficiency checks
- **Manufacturing**: SPC monitoring, equipment protection protocols

### T-Stage: Train (Optional Parameter Learning)
**Who**: POEExecutor learning algorithms  
**What**: Optimize retry/timeout parameters based on execution patterns

```python
def _train(self, perceived_input, operation_result):
    if self.parameters:
        self.parameters.update_from_execution(
            success=operation_result.get("success", True),
            attempts=operation_result.get("attempts", 1),
            execution_time=operation_result.get("execution_time", 0)
        )
```

**Learns**:
- Optimal retry counts for different error types
- Best timeout values for various input complexities
- Success pattern recognition

## 🧩 Domain Plugin Architecture

### Plugin Interface
```python
class DomainPlugin:
    def process_inputs(self, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
        """P-stage: Normalize and validate inputs"""
        
    def validate_output(self, operation_result: Dict, processed_input: Dict) -> Any:
        """E-stage: Validate output and add compliance"""
```

### Available Plugins

#### 1. Financial Services (`financial_services.py`)
```python
class FinancialServicesPlugin(DomainPlugin):
    def process_inputs(self, args, kwargs):
        # Normalize credit scores: "excellent" → 780
        # Convert income: "$50K" → 50000.0  
        # Convert ratios: "25%" → 0.25
        
    def validate_output(self, operation_result, processed_input):
        # FCRA compliance validation
        # Audit trail generation
        # Risk threshold checking
```

#### 2. Building Management (`building_management.py`)
```python
class BuildingManagementPlugin(DomainPlugin):
    def process_inputs(self, args, kwargs):
        # Temperature unit conversion
        # Occupancy data processing
        # Equipment status analysis
        
    def validate_output(self, operation_result, processed_input):
        # Equipment safety interlocks
        # Energy efficiency validation
        # Temperature range checking
```

#### 3. LLM Optimization (`llm_optimization.py`)
```python
class LLMOptimizationPlugin(DomainPlugin):
    def process_inputs(self, args, kwargs):
        # Prompt length optimization
        # Context formatting
        # Request parameter tuning
        
    def validate_output(self, operation_result, processed_input):
        # Response quality validation
        # Length and completeness checking
        # Cost optimization reporting
```

#### 4. Semiconductor (`semiconductor.py`)
```python
class SemiconductorPlugin(DomainPlugin):
    def process_inputs(self, args, kwargs):
        # Process parameter validation
        # Equipment status monitoring
        # Recipe parameter normalization
        
    def validate_output(self, operation_result, processed_input):
        # Statistical process control monitoring
        # Equipment protection interlocks
        # Yield optimization validation
```

## 📊 Intelligence Distribution: 80% Common + 20% Domain

### 80% Generalizable Intelligence (POEExecutor Runtime)
**Same for all domains:**
- Retry logic with exponential backoff
- Timeout handling and monitoring
- Error categorization and recovery
- Performance metrics collection
- Parameter learning algorithms
- Resource management

### 20% Domain-Specific Intelligence (Plugins)
**Customized per industry:**

| Industry | Input Processing (P) | Output Validation (E) |
|----------|-------------------|---------------------|
| **Financial** | Credit score normalization, income parsing | FCRA compliance, audit trails |
| **Building** | Unit conversion, equipment status | Safety interlocks, energy validation |
| **Manufacturing** | Process validation, recipe parsing | SPC monitoring, equipment protection |
| **Healthcare** | Data anonymization, clinical codes | HIPAA compliance, clinical guidelines |
| **LLM** | Prompt optimization, context formatting | Quality validation, cost optimization |

## 🚀 Benefits of This Architecture

### For Engineers
- **90% less boilerplate code**: Focus on business logic only
- **Automatic enterprise capabilities**: Reliability, compliance, monitoring
- **Domain expertise**: Industry intelligence without domain knowledge
- **Consistent patterns**: Same `@poet()` decorator across all domains

### For Operations
- **Automatic reliability**: Built-in retry, timeout, error handling
- **Industry compliance**: Domain plugins ensure regulatory requirements
- **Performance monitoring**: Built-in metrics and optimization
- **Consistent behavior**: Same runtime characteristics across functions

### For Business
- **Faster development**: Simple functions vs complex enterprise code
- **Reduced risk**: Proven domain intelligence and compliance
- **Better reliability**: Enterprise-grade error handling and recovery
- **Domain expertise**: Industry best practices built-in

## 🔧 Configuration Patterns

### Simple Reliability Enhancement
```dana
@poet(retries=3, timeout=30.0)
def my_function(input: str) -> str:
    return process_data(input)
```

### Domain Intelligence
```dana
@poet(domain="financial_services")
def credit_assessment(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"
```

### Production Configuration
```dana
@poet(
    domain="building_management",
    retries=2,
    timeout=15.0,
    enable_training=false,  # Disable learning for stability
    collect_metrics=true    # Enable monitoring
)
def hvac_control(target: float, current: float, occupancy: int) -> dict:
    return {"temperature": target, "mode": "normal"}
```

### Learning-Enabled Systems
```dana
@poet(
    domain="llm_optimization", 
    enable_training=true,      # Learn optimal parameters
    retries=2,
    timeout=30.0
)
def enhanced_reasoning(prompt: str) -> str:
    return reason(prompt)
```

## 🎯 Design Philosophy

### KISS/YAGNI Principles Applied
1. **Engineers write minimal code**: Just core business logic
2. **Runtime provides maximum value**: Enterprise capabilities without complexity  
3. **Domain plugins add intelligence**: Industry expertise without domain knowledge
4. **Learning is optional**: Add complexity only when beneficial

### Separation of Concerns
- **Business Logic**: Engineer's domain expertise (5-10 lines)
- **Runtime Infrastructure**: POEExecutor provides reliability (80% common)
- **Domain Intelligence**: Plugins provide industry expertise (20% specific)
- **Operations**: Built-in monitoring and optimization

### Value Proposition
**Transform this complexity:**
```python
# Manual enterprise function (50+ lines)
def manual_credit_assessment(raw_data):
    # Input validation and normalization (10 lines)
    # Retry logic and error handling (15 lines)  
    # Core business logic (5 lines)
    # Compliance validation (10 lines)
    # Audit trail generation (8 lines)
    # Performance monitoring (5 lines)
```

**Into this simplicity:**
```dana
# POET-enhanced function (5 lines)
@poet(domain="financial_services")
def simple_credit_assessment(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"
```

---

**Next Steps**: 
- **[Getting Started](getting-started.md)** - Write your first POET function
- **[API Reference](api-reference.md)** - Complete configuration options
- **Domain Plugins** - Create custom plugins *(Coming Soon)* 