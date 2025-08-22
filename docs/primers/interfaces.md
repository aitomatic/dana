# Interfaces Primer

## TL;DR (1 minute read)

```dana
# Define behavioral contracts
interface IProcessor:
    process(data: str) -> str
    get_status() -> str
    set_config(config: dict) -> None

# Types automatically satisfy interfaces by implementing required methods
struct TextProcessor:
    status: str = "ready"
    config: dict = {}

def (processor: TextProcessor) process(data: str) -> str:
    return data.upper()

def (processor: TextProcessor) get_status() -> str:
    return processor.status

def (processor: TextProcessor) set_config(config: dict) -> None:
    processor.config = config

# Use interfaces for polymorphic functions
def process_with_any_processor(processor: IProcessor, data: str) -> str:
    return processor.process(data)

# Works with any type that implements IProcessor
text_processor = TextProcessor()
result = process_with_any_processor(text_processor, "hello")  # "HELLO"
```

---

**What it is**: Go-style structural interfaces that define behavioral contracts. Types automatically satisfy interfaces by implementing the required methods, enabling type-safe polymorphism without explicit inheritance.

## Key Syntax

**Interface Definition**:
```dana
interface InterfaceName:
    method1(param: type) -> return_type
    method2(param: type) -> return_type
    get_property() -> type
    set_property(value: type) -> None
```

**Interface Embedding**:
```dana
interface IReadable:
    read() -> str
    get_is_open() -> bool

interface IWritable:
    write(data: str) -> bool
    get_is_writable() -> bool

interface IReadWriter:
    IReadable    # Embedded interface
    IWritable    # Embedded interface
    close() -> bool
```

**Polymorphic Functions**:
```dana
def process_data(processor: IProcessor, data: str) -> str:
    return processor.process(data)
```

## Real-World Examples

### Data Processing Pipeline
```dana
interface IDataProcessor:
    process(data: list) -> list
    get_processed_count() -> int
    reset_count() -> None
    get_config() -> dict
    set_config(config: dict) -> None

struct NumberProcessor:
    processed_count: int = 0
    config: dict = {}

def (processor: NumberProcessor) process(data: list) -> list:
    result = []
    for item in data:
        result.append(item * 2)
    processor.processed_count = processor.processed_count + len(data)
    return result

def (processor: NumberProcessor) get_processed_count() -> int:
    return processor.processed_count

def (processor: NumberProcessor) reset_count() -> None:
    processor.processed_count = 0

def (processor: NumberProcessor) get_config() -> dict:
    return processor.config

def (processor: NumberProcessor) set_config(config: dict) -> None:
    processor.config = config

# Polymorphic processing function
def process_with_any_processor(processor: IDataProcessor, data: list) -> list:
    return processor.process(data)

# Works with any processor implementation
number_processor = NumberProcessor()
result = process_with_any_processor(number_processor, [1, 2, 3, 4, 5])
log(f"Result: {result}")  # [2, 4, 6, 8, 10]
log(f"Processed: {number_processor.get_processed_count()}")  # 5
```

### Agent System with Interfaces
```dana
interface IAgent:
    plan(problem: str) -> str
    solve(problem: str) -> str
    get_domain() -> str
    set_domain(domain: str) -> None
    get_confidence() -> float
    set_confidence(confidence: float) -> None

agent_blueprint MathAgent:
    domain: str = "mathematics"

def (agent: MathAgent) plan(problem: str) -> str:
    return f"Planning math problem: {problem}"

def (agent: MathAgent) solve(problem: str) -> str:
    return f"Solving math problem with confidence {agent.confidence}"

def (agent: MathAgent) get_domain() -> str:
    return agent.domain

def (agent: MathAgent) set_domain(domain: str) -> None:
    agent.domain = domain

def (agent: MathAgent) get_confidence() -> float:
    return agent.confidence

def (agent: MathAgent) set_confidence(confidence: float) -> None:
    agent.confidence = confidence

# Function that works with any agent
def solve_problem_with_agent(agent: IAgent, problem: str) -> str:
    plan = agent.plan(problem)
    solution = agent.solve(problem)
    return f"Plan: {plan}, Solution: {solution}"

math_agent = MathAgent()
result = solve_problem_with_agent(math_agent, "2 + 2")
log(result)  # "Plan: Planning math problem: 2 + 2, Solution: Solving math problem with confidence 0.9"
```

### Resource Management with Embedded Interfaces
```dana
interface IReadable:
    read() -> str
    get_is_open() -> bool

interface IWritable:
    write(data: str) -> bool
    get_is_writable() -> bool

interface IReadWriter:
    IReadable    # Embedded interface
    IWritable    # Embedded interface
    close() -> bool

struct FileHandler:
    data: str = ""
    is_open: bool = true
    is_writable: bool = true

def (file: FileHandler) read() -> str:
    return file.data

def (file: FileHandler) get_is_open() -> bool:
    return file.is_open

def (file: FileHandler) write(data: str) -> bool:
    if file.is_writable:
        file.data = data
        return true
    return false

def (file: FileHandler) get_is_writable() -> bool:
    return file.is_writable

def (file: FileHandler) close() -> bool:
    file.is_open = false
    return true

# Function that works with any readable resource
def read_from_any_source(source: IReadable) -> str:
    if source.get_is_open():
        return source.read()
    return "Source is closed"

# Function that works with any writable resource
def write_to_any_destination(dest: IWritable, data: str) -> bool:
    return dest.write(data)

# Function that works with any read-write resource
def copy_between_resources(source: IReadable, dest: IWritable) -> bool:
    if source.get_is_open() and dest.get_is_writable():
        data = source.read()
        return dest.write(data)
    return false

file_handler = FileHandler()
read_from_any_source(file_handler)  # Works with IReadable
write_to_any_destination(file_handler, "test data")  # Works with IWritable
```

## Interface Embedding and Composition

Interfaces can embed other interfaces to compose larger contracts:

```dana
interface ILogger:
    log(message: str) -> None
    get_log_level() -> str
    set_log_level(level: str) -> None

interface IConfigurable:
    get_config() -> dict
    set_config(config: dict) -> None
    reload_config() -> bool

interface IProcessable:
    process(input: any) -> any
    get_processing_stats() -> dict

interface IComplexSystem:
    ILogger        # Embedded interface
    IConfigurable  # Embedded interface
    IProcessable   # Embedded interface
    start() -> bool
    stop() -> bool
    get_status() -> str

struct ComplexSystem:
    log_level: str = "info"
    config: dict = {}
    processing_stats: dict = {}
    is_running: bool = false

# Implement all methods from embedded interfaces plus additional methods
def (system: ComplexSystem) log(message: str) -> None:
    # Simulate logging
    pass

def (system: ComplexSystem) get_log_level() -> str:
    return system.log_level

def (system: ComplexSystem) set_log_level(level: str) -> None:
    system.log_level = level

def (system: ComplexSystem) get_config() -> dict:
    return system.config

def (system: ComplexSystem) set_config(config: dict) -> None:
    system.config = config

def (system: ComplexSystem) reload_config() -> bool:
    return true

def (system: ComplexSystem) process(input: any) -> any:
    system.processing_stats["processed_count"] = system.processing_stats.get("processed_count", 0) + 1
    return f"Processed: {input}"

def (system: ComplexSystem) get_processing_stats() -> dict:
    return system.processing_stats

def (system: ComplexSystem) start() -> bool:
    system.is_running = true
    return true

def (system: ComplexSystem) stop() -> bool:
    system.is_running = false
    return true

def (system: ComplexSystem) get_status() -> str:
    if system.is_running:
        return "running"
    return "stopped"
```

## Union Types with Interfaces

Interfaces work seamlessly with union types:

```dana
interface IUnionInterface:
    process_data(data: str | bytes) -> str | int
    get_result() -> str | None
    set_config(config: dict | None) -> None

struct UnionStruct:
    config: dict | None = None
    last_result: str | None = None

def (obj: UnionStruct) process_data(data: str | bytes) -> str | int:
    if isinstance(data, str):
        obj.last_result = f"String: {data}"
        return len(data)
    else:
        obj.last_result = f"Bytes: {len(data)} bytes"
        return len(data)

def (obj: UnionStruct) get_result() -> str | None:
    return obj.last_result

def (obj: UnionStruct) set_config(config: dict | None) -> None:
    obj.config = config
```

## Type Safety and Validation

**Runtime Interface Validation**:
```dana
interface IValidator:
    validate(data: any) -> bool
    get_errors() -> list[str]

struct DataValidator:
    errors: list = []

def (validator: DataValidator) validate(data: any) -> bool:
    if isinstance(data, str) and len(data) > 0:
        return true
    validator.errors.append("Data must be non-empty string")
    return false

def (validator: DataValidator) get_errors() -> list[str]:
    return validator.errors

# Function that enforces interface contract
def validate_data(validator: IValidator, data: any) -> bool:
    return validator.validate(data)

validator = DataValidator()
is_valid = validate_data(validator, "test")  # true
is_valid = validate_data(validator, "")      # false
errors = validator.get_errors()              # ["Data must be non-empty string"]
```

## Best Practices

### 1. **Interface Naming Convention**
```dana
# Use I prefix for interfaces
interface IProcessor: ...
interface IAgent: ...
interface IWorkflow: ...

# Use descriptive names that indicate behavior
interface IDataProcessor: ...
interface IFileHandler: ...
interface INetworkConnection: ...
```

### 2. **Keep Interfaces Focused**
```dana
# Good: Single responsibility
interface ILogger:
    log(message: str) -> None
    get_level() -> str

interface IConfigurable:
    get_config() -> dict
    set_config(config: dict) -> None

# Avoid: Too many responsibilities
interface IMegaInterface:
    log(message: str) -> None
    get_config() -> dict
    process_data(data: list) -> list
    connect_to_database() -> bool
    send_email() -> bool
```

### 3. **Use Property Accessors**
```dana
# Good: Use getter/setter methods for properties
interface IUser:
    get_name() -> str
    set_name(name: str) -> None
    get_email() -> str
    set_email(email: str) -> None

# Avoid: Direct field access in interfaces
interface IUser:
    name: str  # Don't expose fields directly
    email: str
```

### 4. **Leverage Interface Embedding**
```dana
# Compose interfaces from smaller, focused ones
interface IReadable:
    read() -> str
    get_is_open() -> bool

interface IWritable:
    write(data: str) -> bool
    get_is_writable() -> bool

interface IReadWriter:
    IReadable
    IWritable
    close() -> bool
```

### 5. **Polymorphic Function Design**
```dana
# Design functions to accept interface types
def process_with_any_processor(processor: IProcessor, data: str) -> str:
    return processor.process(data)

# This enables maximum flexibility
text_processor = TextProcessor()
number_processor = NumberProcessor()
image_processor = ImageProcessor()

# All work with the same function
result1 = process_with_any_processor(text_processor, "hello")
result2 = process_with_any_processor(number_processor, "123")
result3 = process_with_any_processor(image_processor, "image.jpg")
```

## Common Patterns

### 1. **Factory Pattern with Interfaces**
```dana
interface IProcessor:
    process(data: str) -> str

struct TextProcessor:
    pass

struct NumberProcessor:
    pass

def (text: TextProcessor) process(data: str) -> str:
    return data.upper()

def (number: NumberProcessor) process(data: str) -> str:
    return str(len(data))

def create_processor(type: str) -> IProcessor:
    if type == "text":
        return TextProcessor()
    elif type == "number":
        return NumberProcessor()
    else:
        raise ValueError(f"Unknown processor type: {type}")

# Usage
text_processor = create_processor("text")
number_processor = create_processor("number")
```

### 2. **Strategy Pattern**
```dana
interface ISortStrategy:
    sort(data: list) -> list

struct BubbleSort:
    pass

struct QuickSort:
    pass

def (bubble: BubbleSort) sort(data: list) -> list:
    # Bubble sort implementation
    return sorted(data)

def (quick: QuickSort) sort(data: list) -> list:
    # Quick sort implementation
    return sorted(data)

def sort_data(strategy: ISortStrategy, data: list) -> list:
    return strategy.sort(data)

# Usage
bubble_sort = BubbleSort()
quick_sort = QuickSort()

result1 = sort_data(bubble_sort, [3, 1, 4, 1, 5])
result2 = sort_data(quick_sort, [3, 1, 4, 1, 5])
```

### 3. **Observer Pattern**
```dana
interface IObserver:
    update(data: any) -> None

interface ISubject:
    attach(observer: IObserver) -> None
    detach(observer: IObserver) -> None
    notify(data: any) -> None

struct DataSubject:
    observers: list = []

def (subject: DataSubject) attach(observer: IObserver) -> None:
    subject.observers.append(observer)

def (subject: DataSubject) detach(observer: IObserver) -> None:
    # Remove observer implementation
    pass

def (subject: DataSubject) notify(data: any) -> None:
    for observer in subject.observers:
        observer.update(data)

struct LoggerObserver:
    pass

def (logger: LoggerObserver) update(data: any) -> None:
    log(f"Logger received: {data}")
```

## Integration with Dana Systems

### Agent Blueprints
```dana
interface IAgent:
    plan(problem: str) -> str
    solve(problem: str) -> str
    get_domain() -> str

agent_blueprint MathAgent:
    domain: str = "mathematics"

def (agent: MathAgent) plan(problem: str) -> str:
    return f"Planning math problem: {problem}"

def (agent: MathAgent) solve(problem: str) -> str:
    return f"Solving math problem in domain {agent.domain}"

def (agent: MathAgent) get_domain() -> str:
    return agent.domain
```

### Resources
```dana
interface IResource:
    initialize() -> bool
    get_status() -> str
    cleanup() -> bool

resource DatabaseResource:
    status: str = "initialized"

def (resource: DatabaseResource) initialize() -> bool:
    resource.status = "ready"
    return true

def (resource: DatabaseResource) get_status() -> str:
    return resource.status

def (resource: DatabaseResource) cleanup() -> bool:
    resource.status = "cleaned"
    return true
```

### Workflows
```dana
interface IWorkflow:
    execute(data: any) -> any
    get_name() -> str
    validate() -> bool

workflow DataProcessingWorkflow:
    name: str = "DataProcessor"

def (workflow: DataProcessingWorkflow) execute(data: any) -> any:
    return f"Processed: {data}"

def (workflow: DataProcessingWorkflow) get_name() -> str:
    return workflow.name

def (workflow: DataProcessingWorkflow) validate() -> bool:
    return true
```

## Summary

Dana's interface system provides:

- **Structural Typing**: Types automatically satisfy interfaces by implementing required methods
- **Runtime Validation**: Interface compliance is checked when methods are called
- **Interface Embedding**: Compose larger interfaces from smaller ones
- **Polymorphic Functions**: Write functions that work with any type implementing an interface
- **Type Safety**: Compile-time and runtime type checking for interface compliance
- **Zero Breaking Changes**: Existing code continues to work unchanged

Interfaces enable clean, flexible, and type-safe polymorphism without the complexity of traditional inheritance systems.
