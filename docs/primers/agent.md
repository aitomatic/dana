# Agent Primer

## TL;DR (1 minute read)

```dana
# Define reusable agent blueprints (like struct definitions)
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015

# Create instances from blueprints
inspector = QualityInspector()
custom_inspector = QualityInspector(expertise_level="expert", tolerance_threshold=0.01)

# Create singleton agents
agent Solo                          # Simple singleton
agent Jimmy(QualityInspector)       # Singleton from blueprint
agent Config(QualityInspector):     # Singleton with field overrides
    expertise_level = "expert"

# Use built-in agent methods
plan = inspector.plan("Inspect wafer batch WB-2024-001")
solution = Jimmy.solve("High defect rate in etching process")

# Memory operations (isolated per agent instance)
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
defects = inspector.recall("common_defects")
```

---

**What it is**: Dana provides two agent forms: `agent_blueprint` for defining reusable agent types, and `agent` for creating singleton instances. Both have built-in methods for planning, problem-solving, and memory management with isolated memory per instance.

## Key Syntax

### Agent Blueprint Definition
```dana
agent_blueprint BlueprintName:
    field1: type = default_value
    field2: type = default_value
```

### Blueprint Instance Creation
```dana
# Create instance with defaults
instance = BlueprintName()

# Create instance with custom values
instance = BlueprintName(field1=value1, field2=value2)
```

### Singleton Agent Creation
```dana
# Simple singleton agent
agent AgentName

# Singleton from blueprint (inherits all fields)
agent AgentName(BlueprintName)

# Singleton with field overrides
agent AgentName(BlueprintName):
    field1 = new_value
    field2 = new_value
```

### Built-in Methods (All Agents)
```dana
# Planning method
plan = agent.plan("task description")

# Problem-solving method
solution = agent.solve("problem description")

# Memory operations
agent.remember("key", value)  # Returns true on success
value = agent.recall("key")   # Returns stored value or None

# Chat method (for simple agents)
response = agent.chat("message")
```

## Agent Blueprints

Agent blueprints define reusable agent types, similar to struct definitions:

```dana
agent_blueprint Person:
    name: str = "Anonymous"
    age: int = 0
    skills: list = []

# Create multiple instances from blueprint
john = Person(name="John", age=30)
jane = Person(name="Jane", age=25, skills=["coding", "design"])

# Access fields
print(john.name)  # "John"
print(jane.age)   # 25
```

### Complex Field Types

Agent blueprints support various field types:

```dana
agent_blueprint ComplexAgent:
    name: str = "complex"
    config: dict = {"retries": 3, "timeout": 30}
    flags: list = ["A", "B", "C"]
    is_active: bool = true
    experience_years: int = 5

# Create instance and access fields
agent_instance = ComplexAgent()
print(agent_instance.config.get("timeout"))  # 30
print(len(agent_instance.flags))             # 3
```

### Blueprint Composition

Agent blueprints support composition through nested structs and field references:

```dana
# Define base components
agent_blueprint Address:
    street: str = "Unknown"
    city: str = "Unknown"
    state: str = "Unknown"

agent_blueprint Person:
    name: str = "Anonymous"
    age: int = 0
    address: Address = Address()

# Create instance with composed fields
my_person = Person(name="John", age=30)
print(my_person.name)                    # "John"
print(my_person.address.street)          # "Unknown"
print(my_person.address.city)            # "Unknown"
```

## Singleton Agents

Singleton agents create named, persistent instances:

### Simple Singleton
```dana
# Create simple singleton
agent Solo

# Use built-in methods
response = Solo.chat("hello")
plan = Solo.plan("daily tasks")
```

### Singleton from Blueprint
```dana
agent_blueprint PersonAgent:
    name: str = "Person"
    role: str = "general"

# Singleton inherits all blueprint fields
agent Jimmy(PersonAgent)

print(Jimmy.name)  # "Person"
print(Jimmy.role)  # "general"
```

### Singleton with Field Overrides
```dana
agent_blueprint ConfigAgent:
    name: str = "Config"
    version: str = "1.0"
    enabled: bool = true

# Override specific fields
agent Config(ConfigAgent):
    version = "2.0"
    enabled = false

print(Config.name)     # "Config" (inherited)
print(Config.version)  # "2.0" (overridden)
print(Config.enabled)  # false (overridden)
```

## Built-in Agent Methods

### 1. `plan(task: str) -> str`

Generates a plan for the given task:

```dana
agent_blueprint QualityInspector:
    name: str = "inspector"
    domain: str = "semiconductor"

inspector = QualityInspector()

# Generate plan
plan = inspector.plan("Inspect wafer batch WB-2024-001")
# Returns string containing agent name and planning information
```

### 2. `solve(problem: str) -> str`

Generates a solution for the given problem:

```dana
agent_blueprint QualityInspector:
    name: str = "inspector"
    expertise_level: str = "senior"

inspector = QualityInspector()

# Generate solution
solution = inspector.solve("High defect rate in etching process")
# Returns string containing agent name and solving information
```

### 3. `chat(message: str) -> str`

Conversational interface (especially useful for simple agents):

```dana
agent Solo

# Have a conversation
response = Solo.chat("hello")
# Returns conversational response
```

### 4. `remember(key: str, value: Any) -> bool` & `recall(key: str) -> Any`

Memory operations with isolated storage per agent instance:

```dana
agent_blueprint DataAgent:
    name: str = "data_agent"

agent1 = DataAgent()
agent2 = DataAgent()

# Store in separate instances - memories are isolated
agent1.remember("key", "value1")
agent2.remember("key", "value2")

# Retrieve from each instance
print(agent1.recall("key"))  # "value1"
print(agent2.recall("key"))  # "value2"
```

## Agent Composition Patterns

### Complex Blueprint Composition
```dana
agent_blueprint DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "default"

agent_blueprint CacheConfig:
    enabled: bool = true
    ttl: int = 300

agent_blueprint AppConfig:
    name: str = "App"
    version: str = "1.0"
    database: DatabaseConfig = DatabaseConfig()
    cache: CacheConfig = CacheConfig()

# Create instance with composed configuration
config = AppConfig(version="2.0")
print(config.name)                    # "App"
print(config.version)                 # "2.0"
print(config.database.host)           # "localhost"
print(config.cache.enabled)           # true
```

### Singleton with Field Overrides
```dana
agent_blueprint OverrideBase:
    name: str = "Base"
    value: int = 100
    enabled: bool = false

# Singleton with selective overrides
agent OverrideTest(OverrideBase):
    name = "Override"
    value = 200
    enabled = true

print(OverrideTest.name)    # "Override"
print(OverrideTest.value)   # 200
print(OverrideTest.enabled) # true
```

## Real-World Examples

### Manufacturing Quality System

```dana
# Define base blueprint
agent_blueprint QualityInspector:
    name: str = "inspector"
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015
    inspection_tools: list = ["microscope", "spectrometer"]

# Create blueprint instances for different tasks
wafer_expert = QualityInspector(
    name="WaferExpert",
    expertise_level="expert",
    tolerance_threshold=0.012
)

# Create singleton agents for persistent roles
agent PCBInspector(QualityInspector):
    name = "PCBInspector"
    domain = "electronics"
    expertise_level = "junior"
    tolerance_threshold = 0.05

# Use both types
wafer_plan = wafer_expert.plan("Inspect wafer batch WB-2024-001")
pcb_solution = PCBInspector.solve("High defect rate in solder joints")

# Each maintains separate memory
wafer_expert.remember("batch_results", {"pass": 95, "fail": 5})
PCBInspector.remember("common_issues", ["cold_joints", "bridges"])
```

### Multi-Agent Collaboration
```dana
# Different agent types for collaboration
agent_blueprint DataAnalyst:
    specialization: str = "general"
    tools: list = ["pandas", "numpy"]

agent_blueprint ReportWriter:
    style: str = "technical"
    format: str = "markdown"

# Create collaborative team
analyst = DataAnalyst(specialization="financial")
agent Writer(ReportWriter):
    style = "executive"
    format = "pdf"

# Collaborative workflow
analysis = analyst.solve("Q4 revenue analysis")
analyst.remember("q4_analysis", analysis)

# Writer can access shared context through memory patterns
report_plan = Writer.plan("Create executive summary")
```

### Memory Isolation Demo
```dana
agent_blueprint MemoryAgent:
    name: str = "MemoryTest"
    role: str = "tester"

# Create multiple instances
agent1 = MemoryAgent()
agent2 = MemoryAgent()

# Also create singletons
agent Singleton1(MemoryAgent)
agent Singleton2(MemoryAgent)

# Each maintains separate memory
agent1.remember("data", "instance1_data")
agent2.remember("data", "instance2_data")
Singleton1.remember("data", "singleton1_data")
Singleton2.remember("data", "singleton2_data")

# Retrieve isolated values
print(agent1.recall("data"))    # "instance1_data"
print(agent2.recall("data"))    # "instance2_data"
print(Singleton1.recall("data")) # "singleton1_data"
print(Singleton2.recall("data")) # "singleton2_data"
```

## Advanced Override Patterns

### Complex Data Structure Overrides
```dana
agent_blueprint ComplexBase:
    name: str = "Complex"
    settings: dict = {"timeout": 30, "retries": 3, "debug": false}
    tags: list = ["base", "default"]

agent ComplexOverride(ComplexBase):
    settings = {"timeout": 60, "retries": 5, "debug": true, "new": "value"}
    tags = ["override", "custom"]

# All fields completely replaced, not merged
print(ComplexOverride.settings.get("timeout"))  # 60
print(ComplexOverride.settings.get("new"))      # "value"
print(ComplexOverride.tags)                     # ["override", "custom"]
```

### Nested Structure Overrides
```dana
agent_blueprint NestedBase:
    name: str = "Nested"
    config: dict = {
        "database": {"host": "localhost", "port": 5432},
        "cache": {"enabled": false, "ttl": 300}
    }

agent NestedOverride(NestedBase):
    config = {
        "database": {"host": "prod.example.com", "port": 5432},
        "cache": {"enabled": true, "ttl": 600},
        "logging": {"level": "info"}
    }

# Access nested overrides
db = NestedOverride.config.get("database")
print(db.get("host"))  # "prod.example.com"
```

## Best Practices

### 1. Choose the Right Agent Form

```dana
# ✅ Use agent_blueprint for reusable types
agent_blueprint InspectorType:
    domain: str = "general"
    level: str = "junior"

# ✅ Create instances for temporary/multiple agents
temp_inspector = InspectorType(level="senior")

# ✅ Use singleton agents for persistent roles
agent MainInspector(InspectorType):
    level = "expert"
```

### 2. Memory Management

```dana
# ✅ Good - use meaningful memory keys
inspector.remember("common_defects", ["misalignment", "surface_roughness"])

# ✅ Good - check for missing keys
defects = inspector.recall("defects")
if defects == None:
    inspector.remember("defects", [])

# ✅ Good - leverage memory isolation
agent1.remember("session_data", {"user": "alice"})
agent2.remember("session_data", {"user": "bob"})
```

### 3. Method Usage Patterns

```dana
# ✅ Good - handle empty parameters gracefully
plan_result = agent.plan("")    # Should still work
solve_result = agent.solve("")  # Should still work

# ✅ Good - use return values properly
if agent.remember("key", "value") == true:
    print("Successfully stored")

# ✅ Good - consistent method calls across agent types
blueprint_instance = Inspector()
singleton_agent = MainInspector  # (assuming defined earlier)

plan1 = blueprint_instance.plan("task")
plan2 = MainInspector.plan("task")  # Same interface
```

### 4. Field Override Best Practices

```dana
# ✅ Good - partial overrides preserve other fields
agent Config(BaseAgent):
    timeout = 60  # Override only what needs changing

# ✅ Good - type consistency in overrides
agent TypeSafe(BaseAgent):
    count = 100      # int -> int (good)
    enabled = true   # bool -> bool (good)

# ⚠️ Acceptable - type changes are allowed but use carefully
agent TypeChange(BaseAgent):
    count = "unlimited"  # int -> str (works but consider implications)
```

## Testing Agent Functionality

### Memory Persistence Testing
```dana
agent_blueprint TestAgent:
    name: str = "test"

# Test multiple memory operations
agent_instance = TestAgent()
agent_instance.remember("key1", "value1")
agent_instance.remember("key2", "value2")
agent_instance.remember("key3", "value3")

# All values persist
print(agent_instance.recall("key1"))  # "value1"
print(agent_instance.recall("key2"))  # "value2"
print(agent_instance.recall("key3"))  # "value3"
```

### Method Performance Testing
```dana
agent_blueprint PerformanceAgent:
    name: str = "perf_test"

agent_instance = PerformanceAgent()

# Multiple rapid method calls work reliably
for i in range(10):
    plan_result = agent_instance.plan(f"task {i}")
    solve_result = agent_instance.solve(f"problem {i}")
    agent_instance.remember(f"key{i}", f"value{i}")
    recall_result = agent_instance.recall(f"key{i}")
```

## Summary

Dana's agent system provides:
- **Agent Blueprints**: Define reusable agent types with fields and inheritance
- **Singleton Agents**: Create persistent named agents with optional field overrides
- **Instance Creation**: Create multiple instances from blueprints for temporary use
- **Built-in Methods**: Planning, problem-solving, chat, and memory operations
- **Memory Isolation**: Each agent instance/singleton has its own memory space
- **Field Access**: Direct access to agent fields and complex data types
- **Inheritance**: Full support for blueprint inheritance and field overrides
- **Type Safety**: Consistent interface across all agent forms

Perfect for: Multi-agent systems, persistent agent roles, collaborative AI applications, and domain-specific agent implementations with memory requirements.