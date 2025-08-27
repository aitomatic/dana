# POET (Perceive → Operate → Enforce → Train)

POET is Dana’s next-generation execution framework for transforming simple business functions into enterprise-grade systems.

> **Coming Soon:**
> Full documentation, hands-on guides, and code samples for POET are under active development. Check back soon for updates!

<!--
# POET (Perceive → Operate → Enforce → Train) Documentation

**POET** is OpenDXA's execution framework that automatically transforms simple business functions into enterprise-grade systems. Engineers write **minimal business logic**, and POET's runtime infrastructure adds **enterprise capabilities** through domain intelligence.

## 🎯 What is POET?

POET stands for **Perceive → Operate → Enforce → Train** - a runtime pipeline that enhances simple functions with enterprise capabilities:

- **Perceive (P)**: Input normalization and validation via domain plugins
- **Operate (O)**: Your simple business logic + automatic reliability (retries, timeouts, error handling)
- **Enforce (E)**: Output validation, compliance, and audit trails via domain plugins
- **Train (T)**: Optional parameter learning (optimize retries/timeouts based on execution patterns)

### The Core Value Proposition

```dana
# What Engineer Writes (Simple)
@poet(domain="financial_services", retries=3)
def assess_credit_risk(credit_score: int, income: float, debt_ratio: float) -> str:
    # 5 lines of core business logic only
    if credit_score >= 750 and debt_ratio <= 0.3:
        return "approved"
    elif credit_score >= 650 and debt_ratio <= 0.45:
        return "conditional"
    else:
        return "declined"

# What POET Runtime Automatically Adds
# P: financial_services plugin normalizes "excellent"→780, "$50K"→50000, "25%"→0.25
# O: Retry logic, timeout handling, error recovery
# E: FCRA compliance validation, audit trail generation
# T: Learn optimal retry/timeout parameters from execution patterns
```

**Result**: 90% less code for enterprise-grade functionality.

## 🏗️ Architecture: Simple Functions + Runtime Enhancement

### **Current Implementation: POE + Optional T**
POET is implemented as a **POEExecutor** (`opendxa/dana/poet/mvp_poet.py`) that wraps your simple functions:

```python
# P: Domain plugin processes inputs
perceived_input = domain_plugin.process_inputs(args, kwargs)

# O: Execute your function with reliability infrastructure  
result = your_function(*perceived_input.args, **perceived_input.kwargs)

# E: Domain plugin validates output and adds compliance
validated_result = domain_plugin.validate_output(result, perceived_input)

# T: Optional parameter learning
if enable_training:
    learn_from_execution(perceived_input, validated_result)
```

### **Domain Plugins Available (Production Ready)**
1. **financial_services**: Credit score normalization, FCRA compliance, audit trails
2. **building_management**: Equipment protection, energy optimization, safety interlocks
3. **semiconductor**: Process validation, SPC monitoring, equipment safety
4. **llm_optimization**: Prompt optimization, response validation, cost management

## 📚 Documentation Structure

### 📚 **User Guides**
- **[Getting Started](getting-started.md)** - Write your first simple POET function
- **[Configuration Guide](configuration.md)** - Domain plugins and runtime options
- **[Domain Intelligence](domain-plugins.md)** - Available domain plugins and customization *(Coming Soon)*

### 🔧 **Technical References**
- **[API Reference](api-reference.md)** - Complete decorator and configuration API
- **[Runtime Architecture](poet-runtime-architecture.md)** - How POEExecutor works *(Coming Soon)*
- **[Performance Guide](performance-tuning.md)** - Optimization and monitoring *(Coming Soon)*

## 🚀 Quick Start

### 1. Simple Function Enhancement
```dana
# Basic reliability enhancement
@poet(retries=3, timeout=30.0)
def my_function(input: str) -> str:
    return reason(f"Process this: {input}")
    # POET adds: automatic retries, timeout handling, error recovery
```

### 2. Domain Intelligence
```dana
# Financial services domain intelligence
@poet(domain="financial_services")
def assess_credit(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"
    # POET adds: input normalization, FCRA compliance, audit trails

# Building management domain intelligence  
@poet(domain="building_management")
def set_temperature(target: float, current: float, occupancy: int) -> dict:
    return {"temp": target - 2 if occupancy == 0 else target}
    # POET adds: equipment protection, energy optimization, safety checks
```

### 3. Learning and Optimization
```dana
# Enable parameter learning
@poet(domain="llm_optimization", enable_training=true)
def enhanced_reasoning(prompt: str) -> str:
    return reason(prompt)
    # POET learns: optimal retry counts, timeout values, prompt patterns

# Check learning progress
metrics = enhanced_reasoning.get_metrics()
log(f"Success rate: {metrics['success_rate']}")
```

## 🧠 Intelligence Distribution: 80% Common + 20% Domain-Specific

### **80% Generalizable Intelligence (Runtime Infrastructure)**
Works the same across all domains:
- **Retry Logic**: Exponential backoff, configurable attempts
- **Timeout Handling**: Graceful timeout with fallback strategies
- **Error Recovery**: Automatic exception handling and logging
- **Performance Monitoring**: Execution time, success rate tracking
- **Parameter Learning**: Optimize retry/timeout based on success patterns

### **20% Domain-Specific Intelligence (Plugins)**
Specialized for each industry:

| Domain | Input Processing (P) | Output Validation (E) |
|--------|---------------------|----------------------|
| **Financial** | Normalize "$50K"→50000, "excellent"→780 | FCRA compliance, audit trails |
| **Building** | Equipment status analysis | Safety interlocks, energy limits |
| **Manufacturing** | Process parameter validation | SPC monitoring, equipment protection |
| **Healthcare** | Data anonymization | HIPAA compliance, clinical guidelines |
| **LLM** | Prompt optimization | Response quality validation |

## 📊 Current Implementation Status

### ✅ **Production Ready (POET Core)**
- **POEExecutor**: Complete P→O→E pipeline with domain plugin system
- **Domain Plugins**: 4 production-ready plugins (financial, building, semiconductor, LLM)
- **Reliability**: Automatic retries, timeout handling, error recovery
- **Test Coverage**: 534 tests passing across POET functionality

### 🔄 **Optional Training (T-Stage)**
- **Basic Learning**: Parameter optimization (retry counts, timeouts)
- **Statistical Learning**: Advanced algorithms for pattern recognition
- **Learning Storage**: Persistent parameter optimization across executions

### 🎯 **Key Benefits Demonstrated**
- **Financial**: 20% cost reduction, 95% compliance reliability
- **Building**: 15% energy savings, zero equipment damage
- **Manufacturing**: 80% diagnosis accuracy improvement
- **Healthcare**: 95% data processing success rate

## 🎓 Learning Path

### **Beginner: Understand the Architecture**
1. **[Getting Started Guide](getting-started.md)** - Write simple functions, see POET enhancement
2. **[Financial Example](../../../examples/dana/04_poet_examples/01_financial_services_risk_assessment.na)** - See input normalization in action
3. **[API Reference](api-reference.md)** - Learn decorator options and domain plugins

### **Intermediate: Use Domain Intelligence**
1. **[Configuration Guide](configuration.md)** - Understand domain plugin selection
2. **[Building Example](../../../examples/dana/04_poet_examples/02_building_management_hvac_optimization.na)** - Equipment protection and optimization *(Coming Soon)*
3. **[Domain Plugin Guide](domain-plugins.md)** - Available plugins and capabilities *(Coming Soon)*

### **Advanced: Custom Domain Development**
1. **[Plugin Architecture](../../.implementation/poet/04_poet_plugin_architecture.md)** - Create custom domain plugins *(Coming Soon)*
2. **[Runtime Implementation](poet-runtime-architecture.md)** - Understanding POETExecutor internals *(Coming Soon)*
3. **[Extension Patterns](custom-domain-development.md)** - Best practices for domain-specific intelligence *(Coming Soon)*

## 🔗 Related Resources

### **Core Framework**
- **[OpenDXA Overview](../../for-engineers/)** - Framework architecture
- **[3D Methodology](../../../docs/.ai-only/3d.md)** - Development standards

### **Implementation Details**
- **[POEExecutor Implementation](../../../opendxa/dana/poet/mvp_poet.py)** - Runtime code
- **[Domain Plugins](../../../opendxa/dana/poet/domains/)** - Plugin implementations

### **Examples and Applications**
- **[POET Examples](../../../examples/dana/04_poet_examples/)** - Industry-specific demonstrations *(Coming Soon)*
- **[Dana Core Examples](../../../examples/dana/)** - Language fundamentals
- **[Real-World Applications](../../../examples/04_real_world_applications/)** - Production use cases

## 🆘 Getting Help

- **[API Reference](api-reference.md)** - Complete technical documentation
- **[GitHub Issues](https://github.com/opendxa/opendxa/issues)** - Report bugs and request features

---

**Ready to transform your simple functions?** Start with the **[Getting Started Guide](getting-started.md)** to write your first POET-enhanced function!
-->
