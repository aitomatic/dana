# Dana Language Reference - Complete Syntax Guide

> ⚠️ IMPORTANT FOR AI CODE GENERATORS:
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

*Essential reference for Dana language syntax, functions, and patterns*

---

## Quick Reference

### Basic Structure
```python
# Variables and assignment
variable = "value"
scope.variable = "scoped value"

# Function calls
result = reason("What is this?", context=data)
use("kb.entry.id")

# Conditionals
if condition:
 action()
elif other_condition:
 other_action()
else:
 default_action()

# Loops
while condition:
 repeated_action()
```

### State Scopes
| Scope | Purpose | Example |
|-------|---------|---------|
| `local:` | Function/tool local | `result = analysis` (auto-scoped to local, preferred) |
| `private:` | Agent private | `private:internal_state = "processing"` |
| `public:` | World state | `public:weather = "sunny"` |
| `system:` | System state | `system:memory_usage = 85` |

---

## Complete Language Specification

### 1. Variables and Assignment

#### Basic Assignment
```python
# Simple assignment (auto-scoped to local)
name = "OpenDXA"
count = 42
active = true
data = none

# Explicit scoped assignment
private:agent_status = "ready"
public:temperature = 72.5
processing = true # Auto-scoped to local (preferred)
```

#### Supported Data Types
```python
# Strings
message = "Hello, world!"
path = "/path/to/file"

# Numbers
count = 123
percentage = 45.67

# Booleans
active = true
completed = false

# None/null
result = none

# F-strings (formatted strings)
greeting = f"Hello, {name}!"
status_msg = f"Processing {count} items at {percentage}% complete"
```

### 2. Function Calls

#### `reason()` - LLM Reasoning
The core function for AI reasoning and analysis.

```python
# Basic reasoning
analysis = reason("Analyze this data for trends")

# With context
summary = reason("Summarize key points", context=documents)

# Multiple context variables
insights = reason("Compare data sources", context=[sales_data, market_data, competitors])

# Temperature control (0.0 = deterministic, 1.0 = creative)
creative_ideas = reason("Generate innovative solutions", temperature=0.9)
precise_answer = reason("What is the exact value?", temperature=0.1)

# Format control
structured_data = reason("List the top 5 issues", format="json")
plain_text = reason("Explain the process", format="text")
```

#### `use()` - Load Knowledge/Programs
Execute knowledge base entries or sub-programs.

```python
# Load knowledge base entry
use("kb.finance.credit_scoring.v2")

# Execute sub-program
use("workflows.data_validation")

# Load domain-specific knowledge
use("kb.legal.contract_analysis")

# MCP Resource Integration (NEW)
websearch = use("mcp", url="http://localhost:8880/websearch")
database = use("mcp.database", "https://db.company.com/mcp")
api_client = use("mcp.weather")

# A2A Agent Integration (NEW)
analyst = use("a2a.research-agent", "https://agents.company.com")
planner = use("a2a.workflow-coordinator")
```

#### `set()` - Direct State Setting
Directly set values in the runtime context.

```python
# Set system values
set("system:agent_status", "ready")
set("public:current_time", "2024-01-15T10:30:00Z")

# Set configuration
set("system:debug_mode", true)
```

### 3. Control Flow

#### Conditional Statements
```python
# Simple if with scoped variable
if private:agent_status == "ready":
 begin_processing()

# If-elif-else chain
if score >= 90:
 grade = "A"
elif score >= 80:
 grade = "B"
elif score >= 70:
 grade = "C"
else:
 grade = "F"

# Complex conditions
if (temperature > 100 and pressure > 50) or system_override:
 trigger_alert()
```

#### Loops
```python
# While loop
while queue.size > 0:
 item = queue.pop()
 process_item(item)

# Conditional processing
while not task_complete:
 result = process_next_step()
 if result == "error":
 handle_error()
 elif result == "complete":
 task_complete = true
```

### 4. Expressions and Operators

#### Comparison Operators
```python
# Equality
if name == "admin":
 grant_access()

if count != 0:
 process_items()

# Numerical comparisons
if temperature > 100:
 alert("Overheating")

if score >= passing_grade:
 mark_passed()

if pressure <= safe_limit:
 continue_operation()
```

#### Logical Operators
```python
# AND operator
if user.authenticated and user.has_permission:
 allow_access()

# OR operator
if status == "error" or status == "warning":
 log_issue()

# Complex logic
if (user.role == "admin" or user.role == "manager") and not system:maintenance_mode:
 show_admin_panel()
```

#### Membership and Contains
```python
# Check if value is in collection
if error_code in critical_errors:
 escalate_immediately()

# String contains
if "error" in log_message:
 flag_for_review()
```

#### Arithmetic Operators
```python
# Basic math
total = price + tax
discount_price = price * 0.9
average = sum / count
remainder = total % batch_size
```

### 5. Output and Logging

#### Log Levels
```python
# Set log level
log_level = DEBUG # Options: DEBUG, INFO, WARN, ERROR

# Log with different levels
log.debug("Detailed debugging information")
log.info("General information")
log.warn("Warning condition detected")
log.error("Error occurred")

# Default log (INFO level)
log("Process completed successfully")

# F-string logging
log.info(f"Processed {count} items in {duration} seconds")
```

#### Print Statements
```python
# Simple print
print("Hello, world!")

# Print variables
print(result)
print(f"The answer is: {answer}")

# Print expressions
print("Result: " + str(calculation))
```

### 6. Advanced Patterns

#### Error Handling Pattern
```python
# Retry with verification
attempts = 0
max_attempts = 3

while attempts < max_attempts:
 result = process_data()

 if verify_result(result):
 log.info("Processing successful")
 break
 else:
 attempts = attempts + 1
 log.warn(f"Attempt {attempts} failed, retrying...")

 if attempts >= max_attempts:
 log.error("Max attempts reached, escalating")
 escalate_failure()
```

#### Context Management Pattern
```python
# Save context, process, restore
original_context = current_context

# Modify context for specific task
current_context = specialized_context
result = reason("Perform specialized analysis", context=current_context)

# Restore original context
current_context = original_context
```

#### Conditional Processing Chain
```python
# Multi-step conditional processing
if data_source == "api":
 raw_data = fetch_from_api()
elif data_source == "file":
 raw_data = load_from_file()
elif data_source == "database":
 raw_data = query_database()
else:
 log.error("Unknown data source")
 raw_data = none

if raw_data != none:
 processed_data = clean_data(raw_data)
 analysis = reason("Analyze the processed data", context=processed_data)

 if confidence(analysis) > 0.8:
 save_results(analysis)
 else:
 request_human_review(analysis)
```

---

## Common Patterns and Examples

### Document Processing
```python
# Load and process documents
documents = load_documents("contracts/*.pdf")

# Extract key information
for doc in documents:
 key_terms = reason("Extract key terms and conditions", context=doc)
 compliance_check = reason("Check for compliance issues", context=[doc, regulations])

 # Store results
 analysis[doc.name] = {
 "key_terms": key_terms,
 "compliance": compliance_check,
 "processed_at": system:current_time
 }
```

### API Integration
```python
# Fetch data from external API
api_response = fetch_api("/users/active")

if api_response.status == 200:
 users = api_response.data

 # Process each user
 for user in users:
 user_analysis = reason("Analyze user activity patterns", context=user)

 if "high_risk" in user_analysis:
 log.warn(f"High risk user detected: {user.id}")
 trigger_review(user.id)
```

### Workflow Automation
```python
# Multi-step workflow
workflow_status = "started"

# Step 1: Data collection
raw_data = collect_data_sources()
log.info("Data collection completed")

# Step 2: Validation
validation_result = reason("Validate data quality and completeness", context=raw_data)

if "valid" in validation_result:
 # Step 3: Processing
 processed_data = process_data(raw_data)

 # Step 4: Analysis
 analysis = reason("Perform comprehensive analysis", context=processed_data)

 # Step 5: Generate report
 report = reason("Generate executive summary", context=[processed_data, analysis])

 workflow_status = "completed"
 log.info("Workflow completed successfully")
else:
 workflow_status = "failed"
 log.error("Data validation failed")
```

---

## Best Practices

### 1. Clear Variable Naming
```python
# Good
user_authentication_status = "verified"
document_processing_result = reason("Extract key data", context=contract)

# Avoid
x = "verified"
result = reason("stuff", context=thing)
```

### 2. Effective Context Management
```python
# Provide relevant context
analysis = reason("Analyze customer sentiment", context=[reviews, feedback, ratings])

# Not just everything
analysis = reason("Analyze customer sentiment", context=entire_database)
```

### 3. Logging and Debugging
```python
# Log important steps
log.info("Starting document processing")
result = process_documents()
log.info(f"Processed {result.count} documents successfully")

# Debug information
log.debug(f"Processing document: {doc.filename}")
log.debug(f"Context size: {len(context)} items")
```

### 4. Error Handling
```python
# Always check results
api_result = call_external_api()

if api_result.error:
 log.error(f"API call failed: {api_result.error}")
 fallback_result = use_fallback_method()
else:
 process_successful_result(api_result)
```

---

## Next Steps

- Learn by Example: Check out [Common Recipes](../recipes/README.md) for real-world patterns
- Interactive Development: Use the [REPL Guide](repl-guide.md) for hands-on exploration
- Advanced Concepts: Explore [Setup Guide](../setup/README.md)
- Troubleshooting: See [Troubleshooting Guide](../troubleshooting/README.md) when things go wrong

---

## `while` - Loops
```python
counter = 0
while counter < 10:
    log.info(f"Processing item {counter}")
    counter = counter + 1
```

---

## Object Method Calls (NEW)

Dana now supports calling methods on objects returned by `use()` or other sources:

```python
# Basic object method calls
websearch = use("mcp", url="http://localhost:8880/websearch")
tools = websearch.list_tools()
search_results = websearch.search("Dana programming language")

# Chained method calls with arguments
database = use("mcp.database")
query_result = database.query("SELECT * FROM users WHERE active = true")
record_count = database.count_records("users")

# Method calls with mixed arguments
api_client = use("mcp.weather")
weather_data = api_client.get_forecast("San Francisco", days=7, detailed=true)

# Object method calls in expressions
if websearch.health_check():
    search_results = websearch.search(query)
    log.info(f"Found {len(search_results)} results")
```

### Async Method Support
Object methods can be synchronous or asynchronous - Dana handles both automatically:

```python
# Works with both sync and async methods
agent = use("a2a.research-agent")
analysis = agent.analyze_market("tech stocks")  # May be async internally
report = agent.generate_report(analysis)        # May be async internally
```

---

## With Statements (NEW)

> **⚠️ Current Limitation**: `with` statements currently support only a single `as` clause. 
> Multiple resources require nested `with` statements:
> ```python
> # ❌ Not supported yet
> with use("mcp.database") as db, use("mcp.search") as search:
> 
> # ✅ Use nested statements instead
> with use("mcp.database") as db:
>     with use("mcp.search") as search:
>         # your code here
> ```

Use `with` statements for scoped resource management and temporary contexts:

```python
# Resource scoping
with use("mcp.database", "https://db.company.com") as database:
    users = database.query("SELECT * FROM users")
    database.update("UPDATE users SET last_seen = NOW()")
    # database automatically cleaned up after this block

# Temporary context management  
with use("a2a.research-agent") as analyst:
    market_data = analyst.collect_data("tech sector")
    analysis = analyst.analyze(market_data)
    report = analyst.generate_summary(analysis)
    # analyst resources released after this block

# Multiple resource management - use nested statements
with use("mcp", url="http://localhost:8880/websearch") as websearch:
    with use("mcp.database") as database:
        search_results = websearch.search("customer feedback")
        database.store_results(search_results)
```

---

## Advanced Control Structures

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
