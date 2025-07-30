# Agent Struct Primer

## TL;DR (1 minute read)

```dana
# Define an agent with built-in intelligence
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015

# Create instances and use built-in AI capabilities
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

## Why Should You Care?

If you're building AI applications, you've probably written a lot of boilerplate:

```python
# Python way - lots of setup
class QualityInspector:
    def __init__(self, domain, expertise_level):
        self.domain = domain
        self.expertise_level = expertise_level
        self.memory = {}
        self.conversation_history = []
    
    def plan(self, task):
        # Need to implement planning logic
        # Need to integrate with LLM
        # Need to handle context
        pass
    
    def solve(self, problem):
        # Need to implement problem-solving
        # Need to access domain knowledge
        # Need to format responses
        pass

# Usage - lots of setup required
inspector = QualityInspector("semiconductor", "senior")
# Need to initialize LLM, memory, etc.
```

**Dana's agent keyword gives you AI capabilities instantly:**

```dana
# Dana way - AI capabilities built-in
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

# That's it! Now you have:
# - AI-powered planning
# - Problem-solving with context
# - Memory and conversation history
# - Method overriding capabilities

inspector = QualityInspector()
plan = inspector.plan("Inspect wafer batch")  # AI-powered!
solution = inspector.solve("High defect rate")  # AI-powered!
```

**The agent keyword transforms agent creation from 6-8 weeks to 2-3 days:**

- **Built-in Intelligence**: AI-powered planning and problem-solving out of the box
- **Method Overriding**: Custom behavior while maintaining built-in capabilities
- **Memory Systems**: Persistent conversation history and domain knowledge
- **Type Safety**: Full Dana type system integration
- **Domain Expertise**: Context-aware responses based on agent configuration

## The Big Picture

```dana
# Agents are special structs with built-in AI capabilities
agent ManufacturingInspector:
    process_type: str = "assembly"
    tolerance_threshold: float = 0.02
    alert_channels: list[str] = ["email", "slack"]

# Create instances just like structs
inspector = ManufacturingInspector(process_type="welding")

# Use built-in AI methods
plan = inspector.plan("Inspect production line for defects")
solution = inspector.solve("High defect rate in batch A-2024-001")

# Memory and conversation
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
defects = inspector.recall("common_defects")

# Override with custom logic
def plan(inspector: ManufacturingInspector, task: str) -> list[str]:
    return ["Custom inspection step 1", "Custom inspection step 2"]
```

## Built-in Agent Methods

### 1. `plan(task: str, context: dict | None = None) -> Any`

AI-powered planning that considers the agent's configuration and context:

```dana
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

inspector = QualityInspector()

# AI-powered planning
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

### 3. `remember(key: str, value: Any) -> bool`

Store information in agent memory:

```dana
agent QualityInspector:
    domain: str = "semiconductor"

inspector = QualityInspector()

# Store information
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
inspector.remember("best_practices", ["calibrate_daily", "check_temperature"])
```

### 4. `recall(key: str) -> Any`

Retrieve information from agent memory:

```dana
agent QualityInspector:
    domain: str = "semiconductor"

inspector = QualityInspector()

# Store and retrieve
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
defects = inspector.recall("common_defects")  # ["misalignment", "surface_roughness"]
```

## Method Overriding

You can override built-in methods with custom logic while maintaining the built-in capabilities as fallback:

```dana
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

# Override with custom logic
def plan(inspector: QualityInspector, task: str) -> list[str]:
    log(f"🔧 Using CUSTOM plan() method for task: {task}")
    
    # Custom planning logic
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

### Method Resolution Order

1. **Custom method** defined in current scope (highest priority)
2. **Built-in AI method** (fallback)

```dana
# This inspector uses custom plan()
inspector1 = QualityInspector()
plan1 = inspector1.plan("task")  # Uses custom plan()

# This inspector uses built-in AI plan() (no custom method defined)
inspector2 = QualityInspector()
plan2 = inspector2.plan("task")  # Uses built-in AI plan()
```

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
pcb_inspector.remember("solder_issues", ["cold_solder", "bridging"])
```

### Customer Service Agent

```dana
agent CustomerServiceAgent:
    department: str = "general"
    languages: list[str] = ["english"]
    expertise_areas: list[str] = ["billing", "technical_support"]
    response_time_target: int = 300  # seconds

# Create specialized agents
billing_agent = CustomerServiceAgent(
    department="billing",
    languages=["english", "spanish"],
    expertise_areas=["billing", "refunds", "payment_plans"]
)

tech_agent = CustomerServiceAgent(
    department="technical",
    languages=["english"],
    expertise_areas=["software", "hardware", "network"]
)

# AI-powered responses
billing_plan = billing_agent.plan("Handle customer billing dispute")
tech_solution = tech_agent.solve("Customer can't access their account")

# Memory for customer history
billing_agent.remember("customer_123", {"previous_issues": ["late_payment"], "preferences": "email"})
```

### Custom Method Override Example

```dana
agent FinancialAdvisor:
    specialization: str = "retirement"
    certifications: list[str] = ["CFP", "CPA"]
    risk_tolerance: str = "moderate"

# Override with domain-specific logic
def plan(advisor: FinancialAdvisor, goal: str) -> dict:
    plan_structure = {
        "goal": goal,
        "specialization": advisor.specialization,
        "steps": [],
        "timeline": "12 months"
    }
    
    if advisor.specialization == "retirement":
        plan_structure["steps"] = [
            "1. Assess current retirement savings",
            "2. Calculate retirement needs",
            "3. Develop investment strategy",
            "4. Set up automatic contributions"
        ]
    
    return plan_structure

def solve(advisor: FinancialAdvisor, problem: str) -> dict:
    return {
        "problem": problem,
        "advisor_type": advisor.specialization,
        "recommendations": [
            "Schedule consultation",
            "Review current portfolio",
            "Adjust risk allocation"
        ],
        "next_steps": "Follow up in 30 days"
    }

# Create advisor
advisor = FinancialAdvisor(specialization="retirement")

# Use custom methods
plan = advisor.plan("Save for retirement")
solution = advisor.solve("Market volatility concerns")
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
inspector.remember("data2", ["calibrate_daily", "check_temperature"])
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

## Performance and Memory

- **Fast Creation**: Agent instances are created as fast as regular structs
- **Memory Efficient**: Built-in methods are shared across instances
- **Context Isolation**: Each agent instance has its own memory and context
- **Method Resolution**: Custom methods take priority over built-in methods

## Before vs After

### Traditional Approach (6-8 weeks)

```python
# Python way - lots of boilerplate
class QualityInspector:
    def __init__(self, domain, expertise_level):
        self.domain = domain
        self.expertise_level = expertise_level
        self.memory = {}
        self.conversation_history = []
    
    def plan(self, task):
        # Need to implement planning logic
        # Need to integrate with LLM
        # Need to handle context
        # Need to format responses
        pass
    
    def solve(self, problem):
        # Need to implement problem-solving
        # Need to access domain knowledge
        # Need to format responses
        pass

# Usage - lots of setup required
inspector = QualityInspector("semiconductor", "senior")
# Need to initialize LLM, memory, etc.
```

### Dana Agent Approach (2-3 days)

```dana
# Dana way - AI capabilities built-in
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

# That's it! Now you have AI-powered capabilities
inspector = QualityInspector()
plan = inspector.plan("Inspect wafer batch")  # AI-powered!
solution = inspector.solve("High defect rate")  # AI-powered!
```

**Bottom line**: The `agent` keyword gives you AI-powered structs with built-in intelligence, memory, and problem-solving capabilities. It's like having a Python class with AI methods already implemented, but with Dana's type safety and simplicity. The key innovation is that agents are special structs that inherit from the struct system while adding AI capabilities, making them both powerful and easy to use. 