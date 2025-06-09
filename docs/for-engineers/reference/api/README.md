# OpenDXA API Reference

Complete reference documentation for OpenDXA framework components and the Dana programming language.

## 🚀 Quick Start

### Dana Language (Recommended Entry Point)
```python
# Import Dana - the main programming interface
import opendxa.dana as dana

# Execute Dana code
result = dana.eval('''
# AI-powered data analysis
data = [1, 4, 7, 2, 9, 3, 8, 5]
analysis = reason(f"Analyze this dataset: {data}")
log(f"Analysis: {analysis}")
analysis
''')

if result.success:
    print(f"Result: {result.result}")
    print(f"Output: {result.output}")
```

### OpenDXA Framework Components
```python
# Import OpenDXA common utilities
from opendxa.common import DXA_LOGGER, LLMResource, ConfigLoader

# Configure logging
DXA_LOGGER.configure(level=DXA_LOGGER.INFO, console=True)

# Load configuration
config = ConfigLoader().get_default_config()

# Create resources
llm = LLMResource()
```

## 📖 API Documentation

### Core Platform APIs

| Document | Description | Key Components |
|----------|-------------|----------------|
| **[Dana Sandbox](dana-sandbox.md)** | Main Dana execution API | `DanaSandbox`, `ExecutionResult`, `dana.run()`, `dana.eval()` |
| **[OpenDXA Common](opendxa-common.md)** | Shared framework utilities | Resources, mixins, configuration, logging |

### Dana Language Reference

| Document | Description | Key Topics |
|----------|-------------|------------|
| **[Core Functions](core-functions.md)** | Essential Dana functions | `reason()`, `log()`, `print()`, `log_level()` |
| **[Built-in Functions](built-in-functions.md)** | Pythonic built-in functions | `len()`, `sum()`, `max()`, `min()`, `abs()`, `round()` |
| **[Type System](type-system.md)** | Type hints and type checking | Variable types, function signatures, validation |
| **[Scoping System](scoping.md)** | Variable scopes and security | `private:`, `public:`, `system:`, `local:` |

### Advanced Features

| Document | Description | Key Topics |
|----------|-------------|------------|
| **[Function Calling](function-calling.md)** | Function calls and imports | Dana→Dana, Dana→Python, Python→Dana |
| **[Sandbox Security](sandbox-security.md)** | Security model and restrictions | Sandboxing, context isolation, safety |

## 🎯 API by Use Case

### Getting Started with Dana
**Recommended Path:** [Dana Sandbox](dana-sandbox.md) → [Core Functions](core-functions.md) → [Type System](type-system.md)

```python
import opendxa.dana as dana

# Your first Dana program
result = dana.eval('''
user_name: str = "Alice"
age: int = 25

greeting = f"Hello {user_name}, you are {age} years old."
analysis = reason(f"Generate a personalized greeting for: {greeting}")

log(f"Generated: {analysis}")
analysis
''')
```

### Building Applications
**Recommended Path:** [OpenDXA Common](opendxa-common.md) → [Dana Sandbox](dana-sandbox.md) → [Function Calling](function-calling.md)

```python
from opendxa.common import DXA_LOGGER, LLMResource, Configurable
import opendxa.dana as dana

class AIApplication(Configurable):
    def __init__(self):
        super().__init__()
        self.dana_sandbox = dana.DanaSandbox(debug=True)
        self.llm = LLMResource()
        
    def process_request(self, user_input: str):
        dana_code = f'''
        user_request = "{user_input}"
        analysis = reason(f"Process this request: {{user_request}}")
        analysis
        '''
        
        result = self.dana_sandbox.eval(dana_code)
        return result.result if result.success else "Processing failed"
```

### AI and Reasoning
- [Core Functions: `reason()`](core-functions.md#reason) - LLM integration and AI reasoning
- [OpenDXA Common: LLMResource](opendxa-common.md#llmresource) - Direct LLM resource access
- [Type System: AI function signatures](type-system.md#ai-functions) - Type safety for AI operations

### Data Processing
- [Built-in Functions: Collections](built-in-functions.md#collection-functions) - `len()`, `sum()`, `max()`, `min()`
- [Type System: Data types](type-system.md#data-types) - `list`, `dict`, `tuple`, `set`
- [Dana Sandbox: Batch Processing](dana-sandbox.md#batch-processing) - Process multiple files

### Logging and Debugging
- [Core Functions: Logging](core-functions.md#logging-functions) - `log()`, `log_level()`
- [OpenDXA Common: DXALogger](opendxa-common.md#dxalogger) - Advanced logging features
- [Dana Sandbox: Debug Mode](dana-sandbox.md#debug-mode) - Execution debugging

### Security and Isolation
- [Scoping System](scoping.md) - Variable scope security model
- [Sandbox Security](sandbox-security.md) - Runtime security and isolation
- [Dana Sandbox: Security Considerations](dana-sandbox.md#security-considerations) - Safe code execution

### Integration and Extension
- [Function Calling](function-calling.md) - Dana↔Python integration
- [OpenDXA Common: Mixins](opendxa-common.md#mixins) - Reusable functionality
- [OpenDXA Common: Tool Integration](opendxa-common.md#tool-integration) - AI tool development

## 🔧 Development Workflow

### 1. Basic Dana Development
```python
import opendxa.dana as dana

# Development workflow
sandbox = dana.DanaSandbox(debug=True)

# Iterative development
code_v1 = "x = 10\nresult = x * 2"
result1 = sandbox.eval(code_v1)

# Build on previous results
code_v2 = "y = result + 5\nfinal = y"
result2 = sandbox.eval(code_v2)

print(f"Final result: {result2.result}")
```

### 2. Application Development
```python
from opendxa.common import Loggable, LLMResource
import opendxa.dana as dana

class DataAnalyzer(Loggable):
    def __init__(self):
        super().__init__()
        self.sandbox = dana.DanaSandbox()
        self.llm = LLMResource()
    
    def analyze_dataset(self, data: list):
        self.info(f"Analyzing dataset with {len(data)} items")
        
        # Use Dana for structured analysis
        dana_code = f'''
        dataset = {data}
        statistics = {{
            "mean": sum(dataset) / len(dataset),
            "max": max(dataset),
            "min": min(dataset),
            "size": len(dataset)
        }}
        
        # AI-powered insights
        insight = reason(f"Provide insights for dataset statistics: {{statistics}}")
        
        {{
            "statistics": statistics,
            "ai_insight": insight
        }}
        '''
        
        result = self.sandbox.eval(dana_code)
        
        if result.success:
            self.info("Analysis completed successfully")
            return result.result
        else:
            self.error(f"Analysis failed: {result.error}")
            return None

# Usage
analyzer = DataAnalyzer()
analysis = analyzer.analyze_dataset([1, 5, 3, 8, 2, 9, 4, 7])
```

### 3. Production Integration
```python
from fastapi import FastAPI, HTTPException
from opendxa.common import DXA_LOGGER, OpenDXAError
import opendxa.dana as dana

app = FastAPI()

# Configure production logging
DXA_LOGGER.configure(level=DXA_LOGGER.INFO, console=True)

# Global Dana sandbox for request processing
dana_sandbox = dana.DanaSandbox()

@app.post("/process")
async def process_data(data: dict):
    """Production endpoint using Dana for data processing."""
    try:
        DXA_LOGGER.info(f"Processing request with {len(data)} keys")
        
        # Use Dana for processing logic
        dana_code = f'''
        input_data = {data}
        
        # Process data with AI reasoning
        analysis = reason(f"Process and analyze: {{input_data}}")
        
        # Log processing
        log(f"Processed data with keys: {{list(input_data.keys())}}")
        
        {{
            "processed_data": input_data,
            "analysis": analysis,
            "status": "completed"
        }}
        '''
        
        result = dana_sandbox.eval(dana_code)
        
        if result.success:
            DXA_LOGGER.info("Request processed successfully")
            return result.result
        else:
            DXA_LOGGER.error(f"Dana processing failed: {result.error}")
            raise HTTPException(status_code=500, detail="Processing failed")
            
    except OpenDXAError as e:
        DXA_LOGGER.error(f"OpenDXA error: {e}")
        raise HTTPException(status_code=500, detail="Service error")
```

## 📋 API Implementation Status

| Component | Status | Documentation | Coverage |
|-----------|--------|---------------|----------|
| **Core Platform** |
| Dana Sandbox | ✅ Complete | [dana-sandbox.md](dana-sandbox.md) | 100% |
| OpenDXA Common | ✅ Complete | [opendxa-common.md](opendxa-common.md) | 95% |
| **Dana Language** |
| Core Functions | ✅ Complete | [core-functions.md](core-functions.md) | 100% |
| Built-in Functions | ✅ Complete | [built-in-functions.md](built-in-functions.md) | 100% |
| Type System | ✅ Complete | [type-system.md](type-system.md) | 100% |
| Scoping System | ✅ Complete | [scoping.md](scoping.md) | 100% |
| **Advanced Features** |
| Function Calling | ✅ Complete | [function-calling.md](function-calling.md) | 95% |
| Sandbox Security | ✅ Complete | [sandbox-security.md](sandbox-security.md) | 90% |

## 🔍 Quick Reference

### Essential Imports
```python
# Dana programming
import opendxa.dana as dana

# OpenDXA framework
from opendxa.common import (
    DXA_LOGGER, ConfigLoader, LLMResource,
    Loggable, ToolCallable, Configurable,
    OpenDXAError, LLMError, ResourceError
)

# Advanced Dana features
from opendxa.dana.sandbox.sandbox_context import SandboxContext
```

### Core APIs at a Glance

| API | Purpose | Example |
|-----|---------|---------|
| `dana.eval(code)` | Execute Dana code | `dana.eval("x = 10\nx * 2")` |
| `dana.run(file)` | Execute Dana file | `dana.run("script.na")` |
| `DanaSandbox()` | Persistent execution context | `sandbox = dana.DanaSandbox(debug=True)` |
| `LLMResource()` | Direct LLM access | `llm = LLMResource(); llm.generate("prompt")` |
| `DXA_LOGGER` | Framework logging | `DXA_LOGGER.info("message")` |
| `ConfigLoader()` | Configuration management | `config = ConfigLoader().get_default_config()` |

### Dana Language Quick Reference
```dana
# Variables with type hints
name: str = "Alice"
age: int = 25
scores: list = [95, 87, 92]

# AI reasoning
analysis: str = reason(f"Analyze scores: {scores}")

# Scoping
private:secret = "hidden-data"      # Private scope
public:shared = "visible-data"      # Public scope
system:config = {"debug": true}     # System scope
local_var = "function-local"        # Local scope (default)

# Built-in functions
total = sum(scores)
average = total / len(scores)
best_score = max(scores)

# Logging and output
log(f"Average score: {average}", "info")
print(f"Best score: {best_score}")
```

## 🛠️ Testing Your Setup

### Verify Dana Installation
```python
import opendxa.dana as dana

# Test basic functionality
result = dana.eval('''
# Test computation
x = 10
y = 20
result = x + y

# Test logging
log(f"Computation: {x} + {y} = {result}")

# Test AI (if LLM configured)
# insight = reason("What is 10 + 20?")

result
''')

print(f"Success: {result.success}")
print(f"Result: {result.result}")
print(f"Output: {result.output}")
```

### Verify OpenDXA Common
```python
from opendxa.common import DXA_LOGGER, ConfigLoader

# Test logging
DXA_LOGGER.configure(level=DXA_LOGGER.INFO, console=True)
DXA_LOGGER.info("OpenDXA Common is working!")

# Test configuration
try:
    config = ConfigLoader().get_default_config()
    print("✓ Configuration system working")
except Exception as e:
    print(f"Configuration warning: {e}")

print("✓ OpenDXA Common verified")
```

## 🔗 Related Documentation

### Getting Started
- [Setup Guide](../../setup/README.md) - Installation and configuration
- [Troubleshooting](../../troubleshooting/README.md) - Common issues and solutions

### Learning Resources
- [Recipes](../../recipes/README.md) - Practical examples and patterns
- [Dana Language Specification](../../../design/01_dana_language_specification/overview.md) - Complete language reference

### Contributing
- [Contribution Guidelines](../../../for-contributors/README.md) - How to contribute to OpenDXA
- [Architecture Guide](../../../for-contributors/architecture/README.md) - System architecture details

## 🤝 Community & Support

- **Documentation Issues:** Found an error or want to improve the API docs? See our [contribution guidelines](../../../for-contributors/README.md)
- **Questions:** Join our [Discord community](https://discord.gg/6jGD4PYk) for real-time help
- **Bug Reports:** Submit issues on our [GitHub repository](https://github.com/aitomatic/opendxa)

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>