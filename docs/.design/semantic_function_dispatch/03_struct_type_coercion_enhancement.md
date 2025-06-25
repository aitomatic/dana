# ENHANCEMENT: Advanced Struct Type Hints and Context-Aware Prompting

## 🚀 **CRUCIAL ADDITION: Struct Type Hints Support**

The semantic function dispatch system must support **Dana struct types** for complex data structure generation:

### **Struct Type Coercion Examples**
```dana
struct Step:
    action: str
    step_number: int

struct Location:
    name: str
    lat: float
    lng: float
    
struct TripPlan:
    destination: str
    steps: list[Step]
    locations: list[Location]
    budget: float

# REVOLUTIONARY: LLM functions return structured data
plan: TripPlan = reason("Plan me a 3-day trip to Tokyo with budget $2000")
# Should return properly structured TripPlan instance

steps: list[Step] = reason("Plan me a trip to Tokyo") 
# Should return list of Step instances with proper action/step_number

locations: list[Location] = reason("Find 5 restaurants in Tokyo")
# Should return list of Location instances with coordinates
```

## 🧠 **Context-Aware Prompting Enhancement**

### **Code Context Injection Strategy**
When `reason()` function executes, inject comprehensive context:

```dana
def plan(task: str) -> list:
    current_line = "return reason(task)"
    current_function = """
    def plan(task: str) -> list:
        return reason(task)
    """
    # LLM receives enhanced prompt with context
    return reason(task)  # Automatically knows to return list format
```

### **Context Levels**
1. **Line Context**: Current executing line
2. **Block Context**: Current function/struct/class definition  
3. **File Context**: Relevant parts of current Dana file
4. **Type Context**: Expected return type from function signature

### **Enhanced Prompt Generation**
```python
def generate_context_aware_prompt(query, expected_type, code_context):
    if expected_type == list[Step]:
        return f"""
        Context: Function expects list[Step] where Step has action:str, step_number:int
        Current function: {code_context.function_def}
        
        Return ONLY a JSON array of objects with 'action' and 'step_number' fields for: {query}
        Example: [{"action": "Book flight", "step_number": 1}, {"action": "Reserve hotel", "step_number": 2}]
        """
    elif expected_type == TripPlan:
        return f"""
        Context: Function expects TripPlan struct with destination, steps, locations, budget
        Current function: {code_context.function_def}
        
        Return ONLY a JSON object matching TripPlan structure for: {query}
        """
```

## 📋 **Updated Implementation Requirements**

### **Phase 1: Enhanced Core Infrastructure**
- [ ] **Struct Type Detection**: Parse and understand Dana struct definitions
- [ ] **Complex Type Resolution**: Handle `list[CustomStruct]`, `dict[str, Struct]`
- [ ] **Code Context Extraction**: Capture current line, function, file context
- [ ] **JSON Schema Generation**: Auto-generate JSON schemas from Dana structs

### **Phase 2: Advanced Type Coercion**
- [ ] **Struct Instance Creation**: Parse JSON into Dana struct instances
- [ ] **List/Dict Coercion**: Handle collections of structs
- [ ] **Validation & Error Handling**: Validate returned data against struct schema
- [ ] **Nested Struct Support**: Handle structs containing other structs

### **Phase 3: Context-Aware Prompting**
- [ ] **Context Injection**: Pass code context to LLM functions
- [ ] **Prompt Optimization**: Generate type-specific, context-aware prompts
- [ ] **Schema Documentation**: Include struct field descriptions in prompts
- [ ] **Example Generation**: Auto-generate examples from struct definitions

## 🔄 **Advanced Expected Behavior**

### **Struct Type Coercion**
```dana
struct Task:
    title: str
    priority: int  # 1-10
    estimated_hours: float
    
tasks: list[Task] = reason("Create a project plan for building a website")
# Expected return:
# [
#   Task(title="Design mockups", priority=8, estimated_hours=16.0),
#   Task(title="Setup development environment", priority=9, estimated_hours=4.0),
#   Task(title="Implement frontend", priority=7, estimated_hours=40.0)
# ]
```

### **Function Return Type Context**
```dana
def analyze_sentiment(text: str) -> bool:
    # LLM automatically knows to return boolean sentiment
    return reason(f"Is this text positive: {text}")

def extract_entities(text: str) -> list[str]:
    # LLM automatically knows to return list of entity strings
    return reason(f"Extract named entities from: {text}")

def generate_summary(text: str) -> str:
    # LLM automatically knows to return concise string summary
    return reason(f"Summarize this text: {text}")
```

### **Automatic Type Coercion**
```dana
def get_bool(string_decision: str) -> bool:
    return string_decision  # Magically runs bool(string_decision) with semantic understanding

def get_number(text_amount: str) -> float:
    return text_amount  # Magically extracts and converts to float

def get_struct(json_string: str) -> Task:
    return json_string  # Magically parses JSON into Task struct
```

## 🧪 **Enhanced Test Cases Needed**

### **Struct Type Tests**
```dana
# Test 1: Simple struct creation
struct Person:
    name: str
    age: int

person: Person = reason("Create a person named John who is 25")
assert person.name == "John"
assert person.age == 25

# Test 2: Complex nested structs
struct Address:
    street: str
    city: str
    zipcode: str

struct Company:
    name: str
    address: Address
    employees: list[Person]

company: Company = reason("Create a tech startup in San Francisco with 3 employees")
assert len(company.employees) == 3
assert company.address.city == "San Francisco"
```

### **Context-Aware Function Tests**
```dana
def plan_vacation(destination: str) -> list[str]:
    return reason(f"Plan activities for {destination}")

activities: list[str] = plan_vacation("Tokyo")
# Should return ["Visit Senso-ji Temple", "Try sushi at Tsukiji", "See Mount Fuji"]

def estimate_cost(project: str) -> float:
    return reason(f"Estimate cost for {project}")

cost: float = estimate_cost("Building a mobile app")
# Should return 15000.0 or similar numeric value
```

## ⚙️ **Enhanced Configuration**

```bash
# New environment variables
DANA_STRUCT_COERCION=enabled|disabled           # Default: enabled
DANA_CONTEXT_INJECTION=minimal|normal|verbose   # Default: normal
DANA_SCHEMA_VALIDATION=strict|loose|disabled    # Default: strict
DANA_JSON_FORMATTING=pretty|compact             # Default: compact
```

## 🤔 **Critical Design Questions**

1. **Struct Validation**: Should invalid JSON/data cause errors or warnings?
2. **Context Scope**: How much code context should be passed to LLM (performance vs accuracy)?
3. **Schema Generation**: Should struct schemas include field descriptions/examples?
4. **Nested Complexity**: How deep should nested struct support go?
5. **Performance**: Should struct parsing be cached or always fresh?

## 🎯 **Success Criteria Updates**

1. **Struct Coercion**: LLM functions successfully return valid struct instances 90% of time
2. **Context Awareness**: Functions with return type hints work correctly 95% of time  
3. **JSON Validation**: Returned data validates against struct schemas
4. **Performance**: Struct parsing overhead < 50ms per operation
5. **Error Handling**: Clear, actionable error messages for invalid data

## 📊 **Implementation Priority**

**CRUCIAL (Must Have)**:
- ✅ Struct type detection and schema generation
- ✅ Basic struct instance creation from JSON
- ✅ Context injection for function return types

**IMPORTANT (Should Have)**:
- ✅ Complex nested struct support  
- ✅ List/dict coercion with structs
- ✅ Context-aware prompt optimization

**OPTIONAL (Nice to Have)**:
- ⚪ Automatic type coercion magic (`return string_decision` → `bool`)
- ⚪ Schema documentation in prompts
- ⚪ Advanced validation and error recovery

This enhancement transforms Dana from basic type coercion to **intelligent structured data generation** - a game changer for AI-driven development! 