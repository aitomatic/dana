# Agent Primer

## TL;DR (1 minute read)

```dana
# Define reusable agent blueprints (like struct definitions)
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015

# Create singleton agents with optional overrides
agent Alice(QualityInspector):
    expertise_level = "expert"
    tolerance_threshold = 0.01

# Or simple base agents
agent Bob

# Use built-in AI methods
plan = Alice.plan("Inspect wafer batch WB-2024-001")
solution = Alice.solve("High defect rate in etching process")
response = Bob.chat("How can I help with quality inspection?")

# Memory and conversation
Alice.remember("common_defects", ["misalignment", "surface_roughness"])
defects = Alice.recall("common_defects")

# A2A agents for remote intelligence
import a2a_agent
remote = a2a_agent(url="https://api.example.com/agent")
result = remote.query("What's the status of batch 123?")
```

---

**What it is**: Dana provides three agent forms: `agent_blueprint` for defining reusable agent types (like struct templates), singleton `agent` for creating named agent instances, and `a2a_agent()` function for connecting to remote agent services. Agents have built-in AI capabilities including planning, problem-solving, memory, and conversation.

## Key Syntax

### Agent Blueprint (Reusable Type Definition)
```dana
agent_blueprint BlueprintName:
    field1: type = default_value
    field2: type = default_value
```

### Singleton Agents (Instance Creation)
```dana
# Create from blueprint with overrides
agent Alias(BlueprintName):
    field1 = new_value

# Create from blueprint without overrides
agent Alias(BlueprintName)

# Create minimal base agent
agent Name
```

### Agent-to-Agent (A2A) Connection
```dana
import a2a_agent

# Connect to remote agent service
remote_agent = a2a_agent(url="https://api.example.com/agent")
result = remote_agent.query("task")
```

### Built-in Methods
```dana
# AI-powered planning
plan = agent.plan("task description", context_optional)

# AI-powered problem-solving
solution = agent.solve("problem description", context_optional)

# Conversational AI
response = agent.chat("message", context_optional, max_context_turns=5)

# Memory operations
agent.remember("key", value)
value = agent.recall("key")
```

## Agent Forms Explained

### 1. Agent Blueprint - Reusable Type Definitions

Agent blueprints define instantiable agent types, similar to struct definitions:

```dana
agent_blueprint Person:
    name: str = "Anonymous"
    age: int = 0
    skills: list[str] = []

# Blueprint is a type, not an instance
# You can create multiple instances from it
john = Person(name="John", age=30)
jane = Person(name="Jane", age=25, skills=["coding", "design"])
```

### 2. Singleton Agents - Named Instances

Singleton agents create single, named instances:

```dana
# From blueprint with overrides
agent Alice(Person):
    name = "Alice"
    age = 28
    skills = ["management", "coding"]

# From blueprint without overrides (uses defaults)
agent Bob(Person)

# Minimal base agent (no blueprint)
agent Charlie

# These are instances, ready to use
Alice.chat("Hello!")  # Works immediately
Bob.plan("Daily tasks")
Charlie.solve("Problem X")
```

### 3. A2A Agents - Remote Intelligence

A2A agents connect to remote agent services:

```dana
import a2a_agent

# Connect to remote agent API
remote = a2a_agent(
    url="https://api.aitomatic.com/agents/qa",
    name="QA_Expert"
)

# Query remote intelligence
result = remote.query("How do I test this feature?")
analysis = remote.analyze({"code": "...", "type": "security"})
```

## Built-in Agent Methods

### 1. `plan(task: str, context: dict | None = None) -> Any`

AI-powered planning that considers the agent's configuration:

```dana
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

agent inspector(QualityInspector)

# Basic planning
plan = inspector.plan("Inspect wafer batch WB-2024-001")
# Returns: ["1. Perform wafer-level inspection", "2. Check for surface defects", ...]

# With context
plan = inspector.plan("Optimize process", {"batch_size": 1000, "defect_rate": 0.05})
```

### 2. `solve(problem: str, context: dict | None = None) -> Any`

AI-powered problem-solving with domain expertise:

```dana
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

agent inspector(QualityInspector)

# AI-powered problem-solving
solution = inspector.solve("High defect rate in etching process")
# Returns: {"problem": "High defect rate", "recommendations": [...], ...}
```

### 3. `chat(message: str, context: dict | None = None, max_context_turns: int = 5) -> Any`

Conversational AI with memory and context awareness:

```dana
agent Alice

# Have a conversation
response1 = Alice.chat("Hello, I need help with quality inspection")
response2 = Alice.chat("What should I check first?")
response3 = Alice.chat("Thanks, what about surface defects?")

# With additional context
response = Alice.chat(
    "Analyze this batch",
    context={"batch_id": "WB-2024-001", "defect_rate": 0.05},
    max_context_turns=10  # Include more conversation history
)
```

### 4. `remember(key: str, value: Any) -> bool` & `recall(key: str) -> Any`

Memory operations for storing and retrieving information:

```dana
agent_blueprint QualityInspector:
    domain: str = "semiconductor"

agent inspector(QualityInspector)

# Store and retrieve information
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
defects = inspector.recall("common_defects")  # ["misalignment", "surface_roughness"]
```

## Method Overriding

You can override built-in methods with custom logic while maintaining built-in capabilities as fallback:

```dana
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

# Override with custom logic
def (inspector: QualityInspector) plan(task: str) -> list[str]:
    steps = []
    if inspector.domain == "semiconductor":
        steps.append("1. Perform wafer-level inspection")
        steps.append("2. Check for surface defects")
    
    if inspector.expertise_level == "senior":
        steps.append("3. Senior review and approval")
    
    return steps

# Create instance
agent inspector(QualityInspector)

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
# Define the blueprint
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015
    inspection_tools: list[str] = ["microscope", "spectrometer"]

# Create specialized singleton agents
agent WaferExpert(QualityInspector):
    domain = "semiconductor"
    expertise_level = "expert"
    tolerance_threshold = 0.012

agent PCBInspector(QualityInspector):
    domain = "electronics"
    expertise_level = "junior"
    tolerance_threshold = 0.05

# Use built-in AI capabilities
wafer_plan = WaferExpert.plan("Inspect wafer batch WB-2024-001")
pcb_solution = PCBInspector.solve("High defect rate in solder joints")

# Memory for domain knowledge
WaferExpert.remember("common_defects", ["misalignment", "surface_roughness"])

# Have a conversation
response = WaferExpert.chat("What defects should I look for in this batch?")
```

### Customer Service Agents

```dana
# Define the blueprint
agent_blueprint CustomerServiceAgent:
    department: str = "general"
    languages: list[str] = ["english"]
    expertise_areas: list[str] = ["billing", "technical_support"]

# Create specialized singleton agents
agent BillingExpert(CustomerServiceAgent):
    department = "billing"
    languages = ["english", "spanish"]
    expertise_areas = ["billing", "refunds", "payment_plans"]

agent TechSupport(CustomerServiceAgent):
    department = "technical"
    expertise_areas = ["network", "software", "hardware"]

# Conversational AI
customer_response = BillingExpert.chat("I have a question about my bill")
tech_response = TechSupport.chat("My internet is not working")

# AI-powered planning
billing_plan = BillingExpert.plan("Handle customer billing dispute")

# Memory for customer context
BillingExpert.remember("customer_123", {
    "previous_issues": ["late_payment"],
    "preferences": "email"
})
```

### Multi-Agent Collaboration

```dana
# Define blueprints
agent_blueprint DataAnalyst:
    specialization: str = "general"
    tools: list[str] = ["pandas", "matplotlib"]

agent_blueprint ReportWriter:
    style: str = "technical"
    format: str = "markdown"

# Create collaborative agents
agent Analyst(DataAnalyst):
    specialization = "financial"
    tools = ["pandas", "numpy", "seaborn"]

agent Writer(ReportWriter):
    style = "executive"
    format = "pdf"

# Collaborate on a task
analysis = Analyst.solve("Analyze Q4 revenue trends")
Analyst.remember("q4_analysis", analysis)

report_plan = Writer.plan("Create executive report from Q4 analysis")
final_report = Writer.chat(f"Based on this analysis: {analysis}, create an executive summary")
```

### Remote Agent Integration

```dana
import a2a_agent

# Connect to specialized remote agents
sentiment_agent = a2a_agent(
    url="https://api.aitomatic.com/agents/sentiment",
    name="SentimentAnalyzer"
)

translation_agent = a2a_agent(
    url="https://api.aitomatic.com/agents/translate",
    name="Translator"
)

# Use remote intelligence
sentiment = sentiment_agent.analyze("Customer feedback text here")
translation = translation_agent.translate(
    text="Hello world",
    from_lang="en",
    to_lang="es"
)

# Combine local and remote agents
agent LocalExpert
local_analysis = LocalExpert.solve(f"Interpret sentiment: {sentiment}")
```

## Best Practices

### 1. Choose the Right Agent Form

```dana
# ✅ Use agent_blueprint for reusable types
agent_blueprint InspectorType:
    domain: str = "general"
    level: str = "junior"

# ✅ Use singleton agents for named instances
agent Alice(InspectorType):
    level = "senior"

# ✅ Use a2a_agent for remote services
import a2a_agent
remote = a2a_agent(url="https://api.example.com/agent")

# ❌ Avoid - using blueprint as instance
# InspectorType.plan("task")  # Error: blueprint is not an instance
```

### 2. Use Descriptive Field Names

```dana
# ✅ Good - descriptive and specific
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015

# ❌ Avoid - too generic
agent_blueprint Agent:
    field1: str = "value1"
    field2: str = "value2"
```

### 3. Method Override Best Practices

```dana
# ✅ Good - use struct method syntax for overrides
def (inspector: QualityInspector) plan(task: str) -> list[str]:
    return ["Step 1", "Step 2"]

# ✅ Good - access agent fields properly
def (inspector: QualityInspector) solve(problem: str) -> str:
    if inspector.expertise_level == "senior":
        return "Advanced solution"
    return "Basic solution"
```

### 4. Memory and Conversation Management

```dana
# ✅ Good - use meaningful memory keys
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
inspector.remember("best_practices", ["calibrate_daily", "check_temperature"])

# ✅ Good - manage conversation context
response = agent.chat(
    "Continue our discussion",
    max_context_turns=10  # Include more history for continuity
)

# ❌ Avoid - unclear keys and no context management
inspector.remember("data1", ["misalignment", "surface_roughness"])
agent.chat("What?")  # No context about what to continue
```

### 5. Context-Aware Responses

```dana
# ✅ Good - provide relevant context
plan = inspector.plan("Inspect batch", {
    "batch_size": 1000,
    "defect_rate": 0.05,
    "equipment": "wafer_inspector_3000"
})

# ✅ Good - use conversation context
response = agent.chat(
    "Analyze this",
    context={"data": analysis_results, "priority": "high"}
)

# ❌ Avoid - no context when needed
plan = inspector.plan("Inspect batch")  # Missing batch details
```

## Integration with Dana's Type System

Agents work seamlessly with Dana's existing type system:

```dana
# Agent blueprints in function signatures
def process_inspection(inspector: QualityInspector, data: bytes) -> dict:
    plan = inspector.plan("Process inspection data")
    return {"plan": plan, "data_processed": true}

# Agents in structs
struct InspectionTeam:
    lead: QualityInspector  # Agent blueprint type
    members: list[QualityInspector]
    report_writer: ReportWriter

# Create instances and collections
agent_blueprint QualityInspector:
    domain: str = "general"

# Multiple instances from blueprint
inspector1 = QualityInspector(domain="semiconductor")
inspector2 = QualityInspector(domain="electronics")

# Singleton agents in collections
agent Alice(QualityInspector)
agent Bob(QualityInspector)

team = [Alice, Bob]  # List of agent instances
for member in team:
    plan = member.plan("Daily inspection")
```

## Agent Templates (Optional Import)

For common agent patterns, Dana provides pre-built templates:

```dana
import agent_templates

# Use pre-built templates
cs_agent = agent_from_template(
    "customer_service",
    domain="billing",
    response_style="friendly"
)

tech_agent = agent_from_template(
    "technical_support",
    expertise="networking",
    troubleshooting_level="advanced"
)

data_agent = agent_from_template(
    "data_analyst",
    specialization="financial",
    visualization_tools=["matplotlib", "plotly"]
)
```

## Summary

Dana's agent system provides:
- **Three Forms**: `agent_blueprint` for types, singleton `agent` for instances, `a2a_agent()` for remote services
- **Built-in Intelligence**: AI-powered planning, problem-solving, and conversation out of the box
- **Conversation Memory**: Persistent chat history with context awareness
- **Method Overriding**: Custom behavior while maintaining built-in capabilities
- **Remote Integration**: Connect to external agent services via A2A
- **Type Safety**: Full Dana type system integration
- **Domain Expertise**: Context-aware responses based on agent configuration

Perfect for: AI applications, multi-agent systems, conversational AI, domain-specific intelligence, and rapid AI development. 