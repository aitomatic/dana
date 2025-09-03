# DANA Language Syntax Cheatsheet

*Concise reference for essential DANA syntax*

---

## Variables & Data Types
```dana
# Basic assignment (auto-scoped to local)
name = "OpenDXA"
count = 42
active = true
data = none
# F-strings
greeting = f"Hello, {name}!"
status = f"Processing {count} items"
# Scoped assignment
private:agent_status = "ready"
public:temperature = 72.5
system:debug_mode = true
```

## Core Functions
```dana
# AI reasoning with semantic type coercion
analysis = reason("Analyze this data")
summary = reason("Summarize", context=documents, temperature=0.7)
count: int = reason("How many items?")          # Returns integer
data: dict = reason("Get structured data")      # Returns dictionary
# Resource loading and management
websearch = use("mcp", url="http://localhost:8880/websearch")
rag = use("rag", sources=["docs/"], force_reload=True)
weather = use("mcp", url="http://127.0.0.1:8000/mcp")
# Agent creation and management
my_agent = agent(module=agent_module)
agent_pool = agent_pool(agents=[agent1, agent2])
# Enhanced reasoning with resources and agents
result = reason("Query", resources=[weather], agents=pool)
# Logging and output
log("Processing started", level="INFO")
log_level("DEBUG", "dana")                     # Set logging level
print("Hello, world!")                         # Standard output
# POET enhancement (fault tolerance)
@poet(domain="data_analysis", retries=3)
def analyze_data(data):
    return reason(f"Analyze: {data}")
# State management
set("system:agent_status", "ready")
set_model("claude-3-5-sonnet-20241022")        # Set LLM model
```

## Control Flow
```dana
# Conditionals
if condition:
    action()
elif other_condition:
    other_action()
else:
    default_action()
# Loops
while condition:
    process_item()
for item in items:
    process(item)
```

## Operators
```dana
# Comparison: ==, !=, >, <, >=, <=
if score >= 90:
    grade = "A"
# Logical: and, or, not
if user.authenticated and not system:maintenance_mode:
    allow_access()
# Membership: in (note: "not in" is NOT supported)
if "error" in log_message:
    flag_for_review()
# Arithmetic: +, -, *, /, %
total = price + tax
```

## Structs & Methods
```dana
# Struct definition
struct User:
    name: str
    email: str
    age: int
# Instantiation
user = User(name="Alice", email="alice@example.com", age=30)
# Method definition
def greet(user: User) -> str:
    return f"Hello, {user.name}!"
# Method calling (equivalent)
greeting = user.greet()     # Method syntax
greeting = greet(user)      # Function syntax
```

## Built-in Functions
```dana
# Numeric
len([1, 2, 3])              # → 3
sum([1, 2, 3])              # → 6
max([1, 2, 3])              # → 3
min([1, 2, 3])              # → 1
abs(-5)                     # → 5
round(3.14159, 2)           # → 3.14
# Type conversion
int("42")                   # → 42
float("3.14")               # → 3.14
bool(1)                     # → true
# Collections
sorted([3, 1, 2])           # → [1, 2, 3]
list(range(1, 4))           # → [1, 2, 3]
range(5)                    # → [0, 1, 2, 3, 4]
all([true, 1, "yes"])       # → true
any([false, 0, "text"])     # → true
```

## Python Library Imports
```dana
# Standard library modules (add .py extension)
import math.py
import json.py
import os.py as operating_system
import datetime.py
import threading.py
import time.py
# Third-party libraries
import pandas.py as pd
import numpy.py as np
import uvicorn.py
# From-imports (import specific functions/classes)
from math.py import sqrt, pi
from json.py import dumps as json_dumps
from pandas.py import DataFrame
# Usage examples
pi_value = math.pi                      # → 3.141592653589793
sqrt_result = math.sqrt(16)             # → 4.0
json_string = json.dumps({"key": "value"})
current_dir = operating_system.getcwd()
# Data science workflows
df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
subset = df.iloc[0:2]                   # Pandas slicing
array = np.array([1, 2, 3, 4, 5])
mean_val = np.mean(array)               # → 3.0
```

## Resource Management & Method Calls
```dana
# MCP services
websearch = use("mcp", url="http://localhost:8880/websearch")
tools = websearch.list_openai_functions()
results = websearch.search("query")
# RAG services with context management
rag = use("rag", sources=["docs/"])
answer = rag.retrieve("What is DANA?")
# Multi-source RAG
with use("rag", sources=["docs/", "https://example.com"], force_reload=True) as docs:
    answer = reason("What is the latest feature?", resources=[docs])
# Resource context management
with use("mcp", url="http://localhost:8080/sse") as mcp:
    functions = mcp.list_openai_functions()
    result = reason("Get weather", resources=[mcp])
# Multi-resource reasoning
weather_svc = use("mcp", url="http://127.0.0.1:8000/mcp")
docs_svc = use("rag", sources=["docs/"])
answer = reason("Plan trip using weather and docs", resources=[weather_svc, docs_svc])
# Python library objects
import pandas.py as pd
df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
filtered = df[df["A"] > 1]              # Pandas filtering
first_row = df.iloc[0]                  # Row selection
```

## Output & Logging
```dana
# Standard output
print("Hello, world!")
print(f"Result: {result}")
# Enhanced logging with color coding
log("Processing started")                      # Default INFO level
log("Debug info", level="DEBUG")
log("Warning message", level="WARNING")
log("Error occurred", level="ERROR")
# Set logging levels
log_level("DEBUG", "dana")                     # Set Dana namespace to DEBUG
log_level("INFO", "my_module")                 # Set specific module level
```

## Collections
```dana
# Lists
items = ["a", "b", "c"]
items.append("d")
items[0]                    # First item
items[-1]                   # Last item
# Dictionaries
data = {"name": "Alice", "age": 25}
data["email"] = "alice@example.com"
name = data.get("name", "Unknown")
# Iteration
for item in items:
    process(item)
for key, value in data.items():
    print(f"{key}: {value}")
```

## Scope Reference
| Scope | Syntax | Usage |
|-------|--------|-------|
| **local** | `variable = value` | Default (preferred) |
| **private** | `private:variable = value` | Agent private |
| **public** | `public:variable = value` | World state |
| **system** | `system:variable = value` | System state |

## Agent System
```dana
# Agent definition (required components)
system:agent_name = "Weather Agent"
system:agent_description = "Provides weather information and forecasts"
# Agent resources
weather_info = use("mcp", url="http://127.0.0.1:8000/mcp")
# Agent solve function (required)
def solve(question: str) -> str:
    return reason(question, resources=[weather_info])
# Agent creation and management
weather_agent = agent(module=weather_module)
search_agent = agent(module=search_module)
remote_agent = agent(url="http://localhost:5009", timeout=1800)
# Agent pools for multi-agent systems
pool = agent_pool(agents=[weather_agent, search_agent, remote_agent])
available_agents = pool.get_agent_cards()
# Multi-agent reasoning
answer = reason("Complex task", agents=pool)
# Agent keyword syntax (alternative)
agent WeatherAgent:
    name : str = "Weather Reporter"
    description : str = "Weather information provider"
    resources : list = [weather_info]
# Agent deployment
# dana deploy agent_file.na --port 5001
```

## Function Composition & Pipelines
```dana
# Define composable functions
def plan_trip(location: str, weather: str) -> str:
    return reason(f"Plan a day trip in {location} with weather: {weather}")
def estimate_cost(trip: str) -> str:
    return reason(f"Estimate cost for trip: {trip}")
# Pipeline composition with pipe operator
pipeline = plan_trip | estimate_cost
result = pipeline("Tokyo", "sunny")
# Complex workflow patterns
def plan(task: str, agents: list) -> dict:
    steps = reason(f"Create plan for {task} using agents: {agents}")
    return {"task": task, "steps": json.loads(steps)}
def execute(data: dict) -> str:
    context = ""
    for step in data["steps"]:
        answer = reason(f"Step: {step}. Context: {context}", agents=pool)
        context += answer
    return reason(f"Final answer: {context}")
workflow = plan | execute
```

## Python Interoperability
```dana
# In Python code
from opendxa.dana import dana
# Enable Dana module imports
dana.enable_module_imports()
try:
    import order_intelligence  # Dana module (.na file)
    
    # Use Dana functions from Python
    analysis = order_intelligence.analyze_order(order_data)
    risk = order_intelligence.assess_risk(customer_data)
    
finally:
    dana.disable_module_imports()
# Direct reasoning from Python
ai_insights = dana.reason(f"Analyze this data: {data}")
# Dana module structure (order_intelligence.na)
def analyze_order(order_data):
    return reason(f"Analyze order: {order_data}")
def assess_risk(customer_data):
    return reason(f"Assess risk: {customer_data}")
```

## POET Framework (Fault Tolerance)
```dana
# POET decorator for enhanced functions
@poet(domain="data_analysis", retries=3, timeout=30)
def analyze_data(data):
    return reason(f"Analyze this data: {data}")
# POET configuration options
@poet(
    domain="web_search",           # Domain specialization
    retries=2,                     # Retry attempts
    timeout=60,                    # Timeout in seconds
    enable_training=True           # Enable learning
)
def search_and_analyze(query):
    return reason(f"Search and analyze: {query}")
# Feedback for POET-enhanced functions
result = analyze_data(my_data)
feedback(result, {"quality": "good", "accuracy": 0.95})
```

## Advanced Features
```dana
# Semantic type coercion
count: int = reason("How many items?")          # Auto-converts to int
data: dict = reason("Get structured data")      # Auto-converts to dict
float_val: float = reason("What's the price?")  # Auto-converts to float
# Model configuration
set_model("claude-3-5-sonnet-20241022")
set_model("gpt-4")
# Enhanced reasoning with context
result = reason(
    "Complex query",
    resources=[weather_svc, docs_svc],
    agents=agent_pool,
    temperature=0.7,
    max_tokens=1000
)
# Resource configuration
rag_svc = use("rag", 
    sources=["docs/", "https://example.com"], 
    force_reload=True,
    cache_timeout=3600
)
mcp_svc = use("mcp", 
    url="http://localhost:8880/search",
    timeout=30,
    retries=3
)
```

## DANA Limitations (Not Supported)
```dana
# ❌ These Python features don't work in DANA:
# No "not in" operator
# if item not in list:  # ❌ ERROR
# No "is" operator  
# if value is None:     # ❌ ERROR
# No try/except blocks
# try:                  # ❌ ERROR
#     risky_operation()
# except:
#     handle_error()
# No tuple unpacking
# x, y = point          # ❌ ERROR
# for key, val in items: # ❌ ERROR (use .items())
# No inline if/else (ternary operator)
# result = x if condition else y  # ❌ ERROR
# No generator expressions
# sum([x for x in list])          # ❌ ERROR
# No inline comments
# items = [1, 2, 3]  # comment    # ❌ ERROR
# No multi-import from Python modules
# from math.py import sin, cos, tan      # ❌ ERROR
# Must import individually:
# from math.py import sin
# from math.py import cos
```

## Quick Rules
- **✅ Use:** `private:status = "ready"` (colon notation)
- **❌ Avoid:** `private.status = "ready"` (dot notation)
- **✅ Use:** `f"Hello, {name}!"` (f-strings)
- **❌ Avoid:** `"Hello, " + name` (concatenation)
- **✅ Use:** Type hints for semantic coercion: `result: int = reason("count")`
- **✅ Use:** Named arguments for structs
- **✅ Use:** `log()` for colored output, `print()` for standard output
- **✅ Use:** `struct` instead of `class`
- **✅ Use:** `import math.py` (Python modules need .py)
- **❌ Avoid:** `import math` (for Python modules)
- **✅ Use:** `import dana_module` (Dana modules no extension)
- **✅ Use:** `from math.py import sqrt` (single imports)
- **❌ Avoid:** `from math.py import sin, cos` (multi-import)
- **✅ Use:** `with use()` for resource management
- **✅ Use:** `@poet()` for fault-tolerant functions
- **✅ Use:** `agent()` and `agent_pool()` for multi-agent systems
- **✅ Use:** `reason()` with resources and agents for complex queries 