# Dana Resource System Primer

## TL;DR (2 minute read)

Resources are specialized structs in Dana that represent external tools, data sources, and services. They support fields, methods via struct-function pattern, inheritance, and lifecycle management.

```dana
# Resource definition
resource DocumentRAG:
    sources: list = []
    chunk_size: int = 1024
    domain: str = "documents"

# Resource instantiation
docs = DocumentRAG(sources=["report.pdf", "analysis.pdf"])
print("Resource domain:", docs.domain)  # Output: documents

# Resource methods via struct-function pattern
def (self: DocumentRAG) query(request: str) -> str:
    return f"Analysis of {len(self.sources)} documents: {request}"

# Direct usage
result = docs.query("What are the key findings?")

# Resource inheritance
resource BaseResource:
    kind: str = "base"
    version: str = "1.0.0"

resource MyRAG(BaseResource):
    sources: list = []
    domain: str = "documents"

# Agent integration with resources
agent_blueprint DataAnalyst:
    name: str = "DataAnalyst"
    domain: str = "analysis"

analyst = DataAnalyst()
```

---

**What it is**: Resources are first-class types in Dana using the `resource` keyword. They work as specialized structs with full functionality including inheritance, methods, and integration with agents and other Dana features.

## Features

The resource system provides:
- `resource` keyword for defining resource types
- Resource instantiation with field initialization
- Struct-function pattern for resource methods
- Resource inheritance from base resources
- Complex field types (lists, dicts, nested structures)
- Resource lifecycle methods (start, stop, context managers)
- Integration with agents and workflows
- Dictionary field subscript access within methods

**Working Examples:**
```dana
# Basic resource with methods
resource CalculatorResource:
    operation: str = "add"
    default_value: int = 0

def (self: CalculatorResource) add(a: int, b: int) -> int:
    return a + b

def (self: CalculatorResource) multiply(a: int, b: int) -> int:
    return a * b

# Resource with inheritance
resource BaseResource:
    kind: str = "base"
    version: str = "1.0.0"

resource ExtendedResource(BaseResource):
    extra_field: str = "extra"
    chunk_size: int = 1024

# Resource with complex state management
resource StatefulResource:
    current_state: str = "initialized"
    transition_count: int = 0
    processors: dict = {"uppercase": "to_upper"}

def (self: StatefulResource) register_processor(name: str, func: str) -> bool:
    self.processors[name] = func  # Dict subscript access works!
    return true
```

## What are Resources?

Resources represent external tools, data sources, services, or computational capabilities that can be defined independently and used by agents. Examples include:

- **MCP Resources**: Model Context Protocol endpoints for tool calling
- **RAG Resources**: Retrieval Augmented Generation systems with document stores
- **Knowledge Resources**: Structured knowledge bases with facts, plans, and heuristics
- **Human Resources**: Interactive human-in-the-loop interfaces
- **Database Resources**: Connection endpoints to databases
- **API Resources**: External web service endpoints

## Core Concepts

### Resource Definition
Resources are defined using the `resource` keyword as specialized structs with fields only (no methods inside the resource definition):

```dana
# Resource definition - fields only
resource DocumentRAG:
    sources: list = []
    chunk_size: int = 1024
    domain: str = "documents"
```

### Resource Methods
Methods are added to resources using the struct-function pattern, where the first parameter is the resource instance:

```dana
# Define methods outside the resource using struct-function pattern
def (self: DocumentRAG) query(request: str) -> str:
    return f"Analyzing {len(self.sources)} documents for: {request}"

def (self: DocumentRAG) add_source(source: str) -> bool:
    self.sources.append(source)
    return true
```

### Resource Instantiation
Resources are instantiated like any struct with optional field initialization:

```dana
# Create resource instances
docs = DocumentRAG()  # Use defaults
docs_custom = DocumentRAG(sources=["doc1.pdf", "doc2.pdf"], chunk_size=512)
```

### Resource Inheritance
Resources can inherit from other resources, gaining their fields and compatible with their methods:

```dana
resource BaseResource:
    kind: str = "base"
    version: str = "1.0.0"

resource SpecializedRAG(BaseResource):
    sources: list = []
    domain: str = "specialized"

# Inherited resource has all parent fields
rag = SpecializedRAG()
print(rag.kind)     # "base" (inherited)
print(rag.version)  # "1.0.0" (inherited)
print(rag.domain)   # "specialized" (own field)
```

## Resource Lifecycle Management

Resources support lifecycle management through standard methods:

```dana
resource LifecycleResource:
    state: str = "created"
    initialized: bool = false

# Lifecycle methods
def (self: LifecycleResource) start() -> bool:
    self.state = "running"
    self.initialized = true
    return true

def (self: LifecycleResource) stop() -> bool:
    self.state = "stopped"
    return true

def (self: LifecycleResource) is_running() -> bool:
    return self.state == "running"

# Usage
lifecycle = LifecycleResource()
lifecycle.start()  # Initialize resource
result = lifecycle.is_running()  # Check state
lifecycle.stop()   # Cleanup resource
```

### State Management
Resources can manage complex internal state and transitions:

```dana
resource StatefulResource:
    current_state: str = "initialized"
    transition_count: int = 0
    valid_transitions: dict = {
        "initialized": ["running", "error"],
        "running": ["paused", "stopped", "error"],
        "paused": ["running", "stopped"],
        "stopped": ["initialized"]
    }

def (self: StatefulResource) transition_to(new_state: str) -> bool:
    valid = self.valid_transitions.get(self.current_state, [])
    if new_state in valid:
        self.current_state = new_state
        self.transition_count += 1
        return true
    return false
```

## Basic Usage Examples

### 1. Simple Resource Definition and Usage

```dana
# Basic resource definition
resource SimpleResource:
    name: str = "test"
    value: int = 42
    active: bool = true

# Create and use instance
simple = SimpleResource(name="custom", value=100)
print(simple.name)    # "custom"
print(simple.value)   # 100
print(simple.active)  # true
```

### 2. Resource with Methods

```dana
# Resource definition
resource CalculatorResource:
    operation: str = "add"
    history: list = []

# Add methods using struct-function pattern
def (self: CalculatorResource) add(a: int, b: int) -> int:
    result = a + b
    self.history.append(f"{a} + {b} = {result}")
    return result

def (self: CalculatorResource) multiply(a: int, b: int) -> int:
    result = a * b
    self.history.append(f"{a} * {b} = {result}")
    return result

def (self: CalculatorResource) get_history() -> list:
    return self.history

# Usage
calc = CalculatorResource()
sum_result = calc.add(5, 3)        # 8
prod_result = calc.multiply(4, 6)  # 24
history = calc.get_history()       # ["5 + 3 = 8", "4 * 6 = 24"]
```

### 3. Resource with Complex Fields

```dana
# Resource with dictionary and list fields
resource DictResource:
    processors: dict = {"uppercase": "to_upper", "lowercase": "to_lower"}
    config: dict = {"timeout": 30, "retries": 3}

# Methods can access and modify dictionary fields
def (self: DictResource) register_processor(name: str, func: str) -> bool:
    self.processors[name] = func  # Dict subscript access works
    return true

def (self: DictResource) get_processor(name: str) -> str:
    if name in self.processors:
        return self.processors[name]
    return "default"

# Usage
dict_resource = DictResource()
dict_resource.register_processor("reverse", "to_reverse")
processor = dict_resource.get_processor("reverse")  # "to_reverse"
```

### 4. Resource Inheritance

```dana
# Base resource
resource BaseResource:
    kind: str = "base"
    name: str = ""
    version: str = "1.0.0"

# Specialized resource inherits from base
resource TestRAG(BaseResource):
    sources: list = []
    chunk_size: int = 1024
    domain: str = "documents"

# Create instance - has all parent and child fields
rag = TestRAG(name="MyRAG", sources=["doc1.pdf", "doc2.pdf"])
print(rag.kind)       # "base" (inherited)
print(rag.version)    # "1.0.0" (inherited)
print(rag.name)       # "MyRAG" (set on creation)
print(rag.domain)     # "documents" (own field)
```

## Standard Query Interface

Resources commonly implement a `query(request: str) -> str` method as their primary interface:

```dana
resource QueryResource:
    responses: dict = {"hello": "world", "test": "response"}

def (self: QueryResource) query(request: str) -> str:
    if request in self.responses:
        return self.responses[request]
    return f"Unknown query: {request}"

# Usage
query_resource = QueryResource()
result = query_resource.query("hello")  # "world"
```

## Context Manager Support

Resources can be used as context managers with `with` statements:

```dana
resource ContextResource:
    is_open: bool = false
    operation_count: int = 0

# Define context manager methods
def (self: ContextResource) enter_context() -> ContextResource:
    self.is_open = true
    self.operation_count += 1
    return self

def (self: ContextResource) exit_context(exc_type, exc_val, exc_tb) -> bool:
    self.is_open = false
    return false  # Don't suppress exceptions

# Usage with context manager
context_resource = ContextResource()
with context_resource as res:
    # Resource is available within context
    assert res.operation_count == 1
```

## Working with Agents

Resources integrate seamlessly with Dana's agent system:

```dana
# Define resources
resource DataSource:
    endpoint: str = "http://api.example.com"
    api_key: str = ""
    cache_enabled: bool = true

def (self: DataSource) fetch_data(query: str) -> str:
    return f"Data from {self.endpoint}: {query}"

# Define agent blueprint
agent_blueprint DataAnalyst:
    name: str = "DataAnalyst"
    domain: str = "analysis"

# Create instances
data_source = DataSource(endpoint="http://api.finance.com")
analyst = DataAnalyst()

# Both agents and resources work independently
data = data_source.fetch_data("stock prices")
print(analyst.name)  # "DataAnalyst"
```

## Resource Patterns

### Document Processing Resource
```dana
resource DocumentStore:
    documents: list = []
    search_index: dict = {}

def (self: DocumentStore) add_document(doc_id: str, content: str) -> bool:
    self.documents.append({"id": doc_id, "content": content})
    self.search_index[doc_id] = content
    return true

def (self: DocumentStore) search(query: str) -> list:
    results = []
    for doc_id, content in self.search_index.items():
        if query.lower() in content.lower():
            results.append(doc_id)
    return results
```

### Text Processing Resource
```dana
resource TextProcessor:
    default_processor: str = "identity"

def (self: TextProcessor) process(text: str, processor_name: str = "") -> str:
    if processor_name == "":
        processor_name = self.default_processor
    
    if processor_name == "uppercase":
        return text.upper()
    elif processor_name == "lowercase":
        return text.lower()
    elif processor_name == "reverse":
        return text[::-1]
    else:
        return text

# Usage
processor = TextProcessor()
result = processor.process("hello", "uppercase")  # "HELLO"
```

## Advanced Patterns

### Resource with Complex State Management
```dana
resource StatefulResource:
    current_state: str = "initialized"
    transition_count: int = 0
    last_transition: str = ""

def (self: StatefulResource) transition_to(new_state: str) -> bool:
    valid_transitions = {
        "initialized": ["running", "error"],
        "running": ["paused", "stopped", "error"],
        "paused": ["running", "stopped", "error"],
        "stopped": ["initialized", "error"],
        "error": ["initialized"]
    }
    
    if new_state in valid_transitions.get(self.current_state, []):
        self.last_transition = f"{self.current_state} -> {new_state}"
        self.current_state = new_state
        self.transition_count += 1
        return true
    return false

def (self: StatefulResource) get_status() -> str:
    return f"{self.current_state} (transitions: {self.transition_count})"
```

### Resource with Complex Defaults
```dana
resource ComplexDefaultsResource:
    config: dict = {"timeout": 30, "retries": 3, "backoff": 1.5}
    tags: list = ["default", "test"]
    nested: dict = {"level1": {"level2": {"value": 42}}}
    computed: str = "computed_" + "value"

# Create with custom values
custom = ComplexDefaultsResource(
    config={"timeout": 60, "retries": 5},
    tags=["custom", "production"]
)

print(custom.config["timeout"])  # 60
print(custom.tags[0])            # "custom"
```

### Resource Error Handling
```dana
resource ErrorTestResource:
    should_fail: bool = false
    error_message: str = "Test error"

def (self: ErrorTestResource) safe_operation() -> str:
    if self.should_fail:
        return f"ERROR: {self.error_message}"
    return "success"

def (self: ErrorTestResource) divide(a: float, b: float) -> str:
    if b == 0:
        return "ERROR: Division by zero"
    return str(a / b)

# Usage
error_resource = ErrorTestResource()
result = error_resource.divide(10, 0)  # "ERROR: Division by zero"
```

## Working with Structs

Resources integrate with Dana's struct system:

```dana
# Define a struct
struct Config:
    name: str
    value: int
    enabled: bool

# Resource that uses structs
resource StructResource:
    configs: list = []
    default_config: Config = Config(name="default", value=0, enabled=false)

def (self: StructResource) add_config(config: Config) -> bool:
    self.configs.append(config)
    return true

def (self: StructResource) get_config(name: str) -> Config:
    for config in self.configs:
        if config.name == name:
            return config
    return self.default_config

# Usage
struct_resource = StructResource()
config = Config(name="production", value=100, enabled=true)
struct_resource.add_config(config)
retrieved = struct_resource.get_config("production")
print(retrieved.value)  # 100
```

## Integration with Workflows

Resources work within workflow patterns:

```dana
# Define resources for workflow
resource InputProcessor:
    batch_size: int = 100
    timeout: int = 30

resource DataTransformer:
    transformation_rules: dict = {}
    output_format: str = "json"

resource OutputHandler:
    destination: str = "console"
    format_options: dict = {}

# Resource methods
def (self: InputProcessor) process_batch(data: list) -> list:
    end_index = min(len(data), self.batch_size)
    return [f"processed_{item}" for item in data[:end_index]]

def (self: DataTransformer) transform(data: list) -> str:
    transformed = [f"{self.output_format}:{item}" for item in data]
    return str(transformed)

def (self: OutputHandler) send(data: str) -> bool:
    return f"Sent to {self.destination}: {data}" != ""

# Pipeline struct
struct DataPipeline:
    processor: InputProcessor
    transformer: DataTransformer
    handler: OutputHandler

# Use pipeline with resources
pipeline = DataPipeline(
    processor=InputProcessor(batch_size=50),
    transformer=DataTransformer(output_format="csv"),
    handler=OutputHandler(destination="file")
)

input_data = ["item1", "item2", "item3"]
processed = pipeline.processor.process_batch(input_data)
transformed = pipeline.transformer.transform(processed)
sent = pipeline.handler.send(transformed)
```

## Resource Method Patterns

### Multiple Method Signatures
```dana
resource OverloadTestResource:
    data: dict = {}

# Different method patterns
def (self: OverloadTestResource) get(key: str) -> str:
    return self.data.get(key, "not_found")

def (self: OverloadTestResource) get_with_default(key: str, default: str) -> str:
    return self.data.get(key, default)

def (self: OverloadTestResource) set(key: str, value: str) -> bool:
    self.data[key] = value
    return true

def (self: OverloadTestResource) set_multiple(kwargs: dict) -> int:
    count = 0
    for key, value in kwargs.items():
        self.data[key] = value
        count += 1
    return count

# Usage
overload = OverloadTestResource()
overload.set("name", "test")
name = overload.get("name")  # "test"
missing = overload.get_with_default("missing", "default")  # "default"
```

## Best Practices

### Field Type Declarations
```dana
# Explicit type annotations for clarity
resource TypedResource:
    string_field: str = "hello"
    int_field: int = 123
    float_field: float = 3.14
    bool_field: bool = true
    list_field: list = [1, 2, 3]
    dict_field: dict = {"key": "value"}
```

### Resource Initialization
```dana
# Initialize with meaningful defaults
resource ConfigurableResource:
    host: str = "localhost"
    port: int = 8080
    timeout: int = 30

# Override specific fields on creation
config = ConfigurableResource(host="example.com", port=9000)
```

### Method Organization
```dana
resource OrganizedResource:
    state: str = "initialized"

# Lifecycle methods
def (self: OrganizedResource) start() -> bool:
    self.state = "running"
    return true

def (self: OrganizedResource) stop() -> bool:
    self.state = "stopped"
    return true

# Business logic methods
def (self: OrganizedResource) process(data: str) -> str:
    if self.state != "running":
        return "Resource not running"
    return f"Processed: {data}"
```

## Summary

The Dana resource system provides a structured way to define and manage external tools, data sources, and services. Resources are implemented as specialized structs with methods defined via the struct-function pattern.

Key features:
- **Type Safety**: Resources are first-class types with field type checking
- **Inheritance**: Resources can inherit from base resources
- **Lifecycle Management**: Support for start/stop and context managers
- **Complex Fields**: Full support for lists, dicts, and nested structures
- **Method Flexibility**: Define resource behavior through struct-functions
- **Integration**: Works seamlessly with agents, workflows, and other Dana features