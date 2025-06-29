# Dana Agent Keyword - Native Intelligence Capabilities

This directory demonstrates the **native `agent` keyword** in Dana language, which provides built-in intelligence capabilities including planning, problem-solving, memory, and method overriding. The agent keyword extends Dana's struct system with AI-powered capabilities while maintaining the language's simplicity and type safety.

## 🎯 Learning Objectives

After completing these examples, you will understand:

- How to define agents with built-in intelligence capabilities
- Agent method overriding and custom behavior
- Built-in `plan()` and `solve()` methods with AI reasoning
- Memory systems and conversation history
- Type hint support for adaptive responses
- Real-world applications in manufacturing and business domains
- Integration with Dana's existing struct and function systems

## 🚀 Key Innovation

The `agent` keyword transforms agent creation from **6-8 weeks** to **2-3 days** by providing:

- **Built-in Intelligence**: AI-powered planning and problem-solving out of the box
- **Method Overriding**: Custom behavior while maintaining built-in capabilities
- **Memory Systems**: Persistent conversation history and domain knowledge
- **Type Safety**: Full Dana type system integration
- **Domain Expertise**: Context-aware responses based on agent configuration

## 📚 Examples Overview

### [`01_basic_agent.na`](01_basic_agent.na) ⭐ **Start Here**
**Estimated Time:** 15 minutes

**What You'll Learn:**
- Basic agent definition and instantiation
- Built-in `plan()` and `solve()` methods
- Agent field configuration and defaults
- Memory and conversation history

**Key Concepts:**
```dana
# Agent definition with built-in intelligence
agent ManufacturingInspector:
    process_type: str = "assembly"
    tolerance_threshold: float = 0.02
    alert_channels: list[str] = ["email", "slack"]

# Create instance and use built-in capabilities
inspector = ManufacturingInspector(process_type="welding")
plan = inspector.plan("Inspect production line for defects")
solution = inspector.solve("High defect rate in batch A-2024-001")
```

### [`02_method_override.na`](02_method_override.na) ⭐⭐
**Estimated Time:** 20 minutes

**What You'll Learn:**
- Overriding built-in agent methods
- Custom behavior while maintaining AI capabilities
- Method resolution and inheritance patterns
- Combining custom logic with built-in intelligence

**Key Concepts:**
```dana
# Define custom plan method
def plan(inspector: ManufacturingInspector, objective: str, context: dict) -> list[str]:
    return [f"Custom plan for {objective}"]

# Agent uses custom method instead of built-in AI
inspector = ManufacturingInspector()
result = inspector.plan("test objective")  # Uses custom method
```

### [`03_type_hint_adaptation.na`](03_type_hint_adaptation.na) ⭐⭐
**Estimated Time:** 25 minutes

**What You'll Learn:**
- Type hint detection and response adaptation
- Dynamic response formatting based on context
- JSON vs list vs dict response types
- Context-aware AI reasoning

**Key Concepts:**
```dana
# Default behavior (returns list)
steps = inspector.plan("optimize production")

# Explicit type hints
steps: list = inspector.plan("optimize production")  # Returns list
plan_dict: dict = inspector.plan("optimize production")  # Returns dict
```

### [`04_memory_systems.na`](04_memory_systems.na) ⭐⭐⭐
**Estimated Time:** 30 minutes

**What You'll Learn:**
- Agent memory and persistence
- Conversation history tracking
- Domain knowledge accumulation
- Cross-session memory management

**Key Concepts:**
```dana
# Memory operations
inspector.remember("defect_pattern", "edge_cracking_common")
pattern = inspector.recall("defect_pattern")

# Conversation history
history = inspector.get_conversation_history()
memory_keys = inspector.get_memory_keys()
```

### [`05_real_world_manufacturing.na`](05_real_world_manufacturing.na) ⭐⭐⭐
**Estimated Time:** 35 minutes

**What You'll Learn:**
- Real-world semiconductor manufacturing scenarios
- Multi-agent coordination patterns
- Complex domain-specific reasoning
- Production line optimization workflows

**Key Concepts:**
```dana
# Specialized manufacturing agents
agent WaferInspector:
    inspection_mode: str = "automatic"
    defect_threshold: float = 0.015

agent ProcessEngineer:
    expertise: str = "plasma_etch"
    optimization_level: str = "aggressive"

# Multi-agent coordination
inspector = WaferInspector()
engineer = ProcessEngineer()

inspection_plan = inspector.plan("batch WB-2024-001 inspection")
optimization = engineer.solve("reduce defect rate by 50%")
```

### [`06_advanced_integration.na`](06_advanced_integration.na) ⭐⭐⭐⭐
**Estimated Time:** 40 minutes

**What You'll Learn:**
- Agent integration with Dana pipelines
- Struct composition with agents
- Function polymorphism with agent types
- Complex workflow orchestration

**Key Concepts:**
```dana
# Agent in pipeline
def process_with_agent(data: RawData, agent: ManufacturingAgent) -> ProcessedData:
    plan = agent.plan("process data efficiently")
    return data | apply_plan(plan)

# Struct composition
struct ProductionLine:
    name: str
    inspector: WaferInspector
    engineer: ProcessEngineer
    status: str
```

## 🚀 Quick Start

1. **Start with basic concepts:**
   ```bash
   dana examples/dana/10_agent_keyword/01_basic_agent.na
   ```

2. **Progress through examples in order:**
   - Each builds on concepts from previous examples
   - Pay attention to the AI-powered responses vs custom overrides

3. **Experiment with modifications:**
   - Add new fields to existing agents
   - Create custom method overrides
   - Try different type hints and observe response changes

## 💡 Key Design Principles

### **Agent = Struct + Built-in Intelligence**
```dana
# ✅ DANA AGENT WAY
agent QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"

inspector = QualityInspector()
plan = inspector.plan("optimize yield")  # AI-powered planning
solution = inspector.solve("defect analysis")  # AI-powered problem solving
```

### **Method Override Pattern**
```dana
# Custom behavior while keeping built-in capabilities
def plan(inspector: QualityInspector, objective: str, context: dict) -> list[str]:
    # Custom logic here
    return [f"Custom plan: {objective}"]

# Agent uses custom method, not built-in AI
result = inspector.plan("test")  # Returns custom result
```

### **Type-Aware Responses**
```dana
# Adaptive responses based on type hints
steps: list = agent.plan("task")  # Returns list
plan_dict: dict = agent.plan("task")  # Returns dict
```

## ✅ Advantages of Dana Agents

| Aspect | Dana Agents | Traditional Agent Frameworks |
|--------|-------------|------------------------------|
| **Setup Time** | 2-3 days | 6-8 weeks |
| **Built-in AI** | Yes - plan()/solve() | Requires custom implementation |
| **Method Override** | Native Dana syntax | Complex inheritance patterns |
| **Type Safety** | Full Dana type system | Often dynamic/weak typing |
| **Memory** | Built-in conversation history | Requires external systems |
| **Integration** | Native Dana pipelines | Complex API integration |
| **Learning Curve** | Dana syntax only | Multiple frameworks/languages |

## 🔧 Common Patterns

### **Agent Definition Pattern**
```dana
agent DomainExpert:
    domain: str = "manufacturing"
    expertise_level: str = "senior"
    specialization: str = "quality_control"
```

### **Method Override Pattern**
```dana
def plan(expert: DomainExpert, objective: str, context: dict) -> list[str]:
    # Custom planning logic
    return [f"Custom step for {objective}"]

def solve(expert: DomainExpert, problem: str, context: dict) -> dict:
    # Custom problem-solving logic
    return {"solution": f"Custom solution for {problem}"}
```

### **Memory Pattern**
```dana
# Store domain knowledge
agent.remember("common_defects", ["edge_cracking", "surface_contamination"])
agent.remember("best_practices", ["calibrate_daily", "check_temperature"])

# Retrieve knowledge
defects = agent.recall("common_defects")
practices = agent.recall("best_practices")
```

### **Type-Aware Response Pattern**
```dana
# List response for step-by-step plans
steps: list = agent.plan("optimize process")

# Dict response for detailed analysis
analysis: dict = agent.plan("analyze defects")

# Default behavior adapts to context
result = agent.plan("task")  # Returns appropriate type
```

## 🧪 Practice Exercises

1. **Basic Exercise:** Create a `CustomerServiceAgent` with:
   - Built-in customer interaction capabilities
   - Custom response templates
   - Memory for customer preferences
   - Type-aware response formatting

2. **Intermediate Exercise:** Build a `DataAnalystAgent` that:
   - Overrides `plan()` for data analysis workflows
   - Uses `solve()` for statistical problem solving
   - Maintains memory of analysis patterns
   - Integrates with Dana data processing pipelines

3. **Advanced Exercise:** Create a multi-agent system with:
   - `QualityInspector` for defect detection
   - `ProcessEngineer` for optimization
   - `ProductionManager` for coordination
   - Cross-agent communication and memory sharing

## 🔗 Related Examples

- **Structs and Functions** (`07_structs_and_functions/`): Foundation for agent data modeling
- **Advanced Features** (`03_advanced_features/`): Advanced Dana patterns
- **Multi-Agent Systems** (`08_a2a_multi_agents/`): Complex agent coordination

## 📖 Further Reading

- [Agent Keyword Design](../agent/.design/agent_keyword_design.md): Technical design document
- [Dana Language Specification](../../reference/01_dana_language_specification/): Core language concepts
- [Agent Model Documentation](../../reference/04_agent_and_orchestration/): Agent architecture details 