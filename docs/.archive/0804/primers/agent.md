# Agent Struct Primer

## TL;DR (1 minute read)

```dana
# Define an agent with built-in AI capabilities
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015

# Create instances and use built-in AI methods
inspector = QualityInspector(domain="semiconductor")
plan = inspector.plan("Inspect wafer batch WB-2024-001")
solution = inspector.solve("High defect rate in etching process")

# Memory and conversation history
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
defects = inspector.recall("common_defects")

# Override built-in methods with custom logic
def plan(inspector: QualityInspector, task: str) -> list[str]:
    return ["Custom step 1", "Custom step 2"]

# Method resolution: custom → built-in AI
result = inspector.plan("task")  # Uses custom plan()
```

---

**What it is**: The `agent` keyword creates intelligent struct types with built-in AI capabilities. Agents are special structs that inherit from the struct system but add planning, problem-solving, memory, and conversation capabilities out of the box.

## Key Syntax

**Agent Definition**:
```dana
agent AgentName:
    field1: type = default_value
    field2: type = default_value
```

**Built-in Methods**:
```dana
# AI-powered planning
plan = agent.plan("task description", context_optional)

# AI-powered problem-solving
solution = agent.solve("problem description", context_optional)

# Memory operations
agent.remember("key", value)
value = agent.recall("key")
```

## Built-in Agent Methods

### 1. `plan(task: str, context: dict | None = None) -> Any`

AI-powered planning that considers the agent's configuration:

```dana
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

inspector = QualityInspector()

# Basic planning
plan = inspector.plan("Inspect wafer batch WB-2024-001")
# Returns: ["1. Perform wafer-level inspection", "2. Check for surface defects", ...]

# With context
plan = inspector.plan("Optimize process", {"batch_size": 1000, "defect_rate": 0.05})
```

### 2. `solve(problem: str, context: dict | None = None) -> Any`

AI-powered problem-solving with domain expertise:

```dana
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

inspector = QualityInspector()

# AI-powered problem-solving
solution = inspector.solve("High defect rate in etching process")
# Returns: {"problem": "High defect rate", "recommendations": [...], ...}
```

### 3. `remember(key: str, value: Any) -> bool` & `recall(key: str) -> Any`

Memory operations for storing and retrieving information:

```dana
agent QualityInspector:
    domain: str = "semiconductor"

inspector = QualityInspector()

# Store and retrieve information
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
defects = inspector.recall("common_defects")  # ["misalignment", "surface_roughness"]
```

## Method Overriding

You can override built-in methods with custom logic while maintaining built-in capabilities as fallback:

```dana
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

# Override with custom logic
def plan(inspector: QualityInspector, task: str) -> list[str]:
    steps = []
    if inspector.domain == "semiconductor":
        steps.append("1. Perform wafer-level inspection")
        steps.append("2. Check for surface defects")
    
    if inspector.expertise_level == "senior":
        steps.append("3. Senior review and approval")
    
    return steps

# Create instance
inspector = QualityInspector()

# Uses custom method (not AI)
plan = inspector.plan("Inspect wafer batch")
# Returns: ["1. Perform wafer-level inspection", "2. Check for surface defects", "3. Senior review and approval"]
```

**Method Resolution Order**:
1. **Custom method** defined in current scope (highest priority)
2. **Built-in AI method** (fallback)

## Real-World Examples

### Manufacturing Quality Inspector

```dana
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015
    inspection_tools: list[str] = ["microscope", "spectrometer"]

# Create specialized inspectors
wafer_inspector = QualityInspector(
    domain="semiconductor",
    expertise_level="senior",
    tolerance_threshold=0.012
)

pcb_inspector = QualityInspector(
    domain="electronics",
    expertise_level="junior",
    tolerance_threshold=0.05
)

# Use built-in AI capabilities
wafer_plan = wafer_inspector.plan("Inspect wafer batch WB-2024-001")
pcb_solution = pcb_inspector.solve("High defect rate in solder joints")

# Memory for domain knowledge
wafer_inspector.remember("common_defects", ["misalignment", "surface_roughness"])
```

### Customer Service Agent

```dana
agent CustomerServiceAgent:
    department: str = "general"
    languages: list[str] = ["english"]
    expertise_areas: list[str] = ["billing", "technical_support"]

# Create specialized agents
billing_agent = CustomerServiceAgent(
    department="billing",
    languages=["english", "spanish"],
    expertise_areas=["billing", "refunds", "payment_plans"]
)

# AI-powered responses
billing_plan = billing_agent.plan("Handle customer billing dispute")
billing_agent.remember("customer_123", {"previous_issues": ["late_payment"], "preferences": "email"})
```

### Custom Method Override Example

```dana
agent FinancialAdvisor:
    specialization: str = "retirement"
    certifications: list[str] = ["CFP", "CPA"]

# Override with domain-specific logic
def plan(advisor: FinancialAdvisor, goal: str) -> dict:
    return {
        "goal": goal,
        "specialization": advisor.specialization,
        "steps": ["1. Assess savings", "2. Calculate needs", "3. Develop strategy"],
        "timeline": "12 months"
    }

# Create advisor and use custom methods
advisor = FinancialAdvisor(specialization="retirement")
plan = advisor.plan("Save for retirement")
```

## Best Practices

### 1. Use Descriptive Field Names

```dana
# ✅ Good - descriptive and specific
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015

# ❌ Avoid - too generic
agent Agent:
    field1: str = "value1"
    field2: str = "value2"
```

### 2. Method Override Best Practices

```dana
# ✅ Good - proper parameter naming and type hints
def plan(inspector: QualityInspector, task: str) -> list[str]:
    return ["Step 1", "Step 2"]

# ❌ Avoid - using 'agent' parameter name (reserved)
def plan(agent: QualityInspector, task: str) -> list[str]:
    return ["Step 1", "Step 2"]
```

### 3. Memory Management

```dana
# ✅ Good - use meaningful keys
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
inspector.remember("best_practices", ["calibrate_daily", "check_temperature"])

# ❌ Avoid - unclear keys
inspector.remember("data1", ["misalignment", "surface_roughness"])
```

### 4. Context-Aware Responses

```dana
# ✅ Good - provide relevant context
plan = inspector.plan("Inspect batch", {
    "batch_size": 1000,
    "defect_rate": 0.05,
    "equipment": "wafer_inspector_3000"
})

# ❌ Avoid - no context
plan = inspector.plan("Inspect batch")
```

## Integration with Dana's Type System

Agents work seamlessly with Dana's existing type system:

```dana
# Agents can be used in function signatures
def process_inspection(inspector: QualityInspector, data: bytes) -> dict:
    plan = inspector.plan("Process inspection data")
    return {"plan": plan, "data_processed": true}

# Agents can be used in structs
struct InspectionReport:
    inspector: QualityInspector
    findings: list[str]
    timestamp: str

# Agents can be used in lists and other collections
inspectors = [
    QualityInspector(domain="semiconductor"),
    QualityInspector(domain="electronics")
]

# Process all inspectors
for inspector in inspectors:
    plan = inspector.plan("Daily inspection")
```

## Summary

Agents in Dana provide:
- **Built-in Intelligence**: AI-powered planning and problem-solving out of the box
- **Method Overriding**: Custom behavior while maintaining built-in capabilities
- **Memory Systems**: Persistent conversation history and domain knowledge
- **Type Safety**: Full Dana type system integration
- **Domain Expertise**: Context-aware responses based on agent configuration

Perfect for: AI applications, intelligent systems, domain-specific agents, and rapid AI development. 