# Dana Advanced Features

Explore Dana's powerful AI reasoning capabilities and advanced application patterns. This is where Dana's unique strengths shine!

## 🎯 Learning Objectives

By completing these examples, you'll master:
- ✅ AI reasoning integration with the `reason()` function
- ✅ Building complete AI-powered applications
- ✅ Hybrid systems combining LLM reasoning with validation
- ✅ Function composition and complex data flows
- ✅ Real-world monitoring and automation patterns

## 📚 Examples (Recommended Order)

### 1. **reason_demo.na** - AI Reasoning Introduction
```bash
uv run python -m dana.dana.exec.dana reason_demo.na
```
**What you'll learn:**
- Basic `reason()` function usage
- Context management for AI reasoning
- Prompt engineering patterns
- LLM integration fundamentals

**Key concepts:** `reason(prompt)`, context building, AI integration

### 2. **reasoning_example.na** - Practical AI Applications
```bash
uv run python -m dana.dana.exec.dana reasoning_example.na
```
**What you'll learn:**
- Real-world reasoning scenarios
- Structured prompt patterns
- Response processing and validation

**Key concepts:** Practical AI usage, prompt patterns

### 3. **hybrid_math_agent.na** ⭐ **FLAGSHIP EXAMPLE**
```bash
uv run python -m dana.dana.exec.dana hybrid_math_agent.na
```
**What you'll learn:**
- Complete AI agent architecture
- LLM reasoning with deterministic validation
- Tool integration patterns
- Query parsing and routing
- Error handling in AI systems

**Key concepts:** AI agents, validation patterns, tool integration

### 4. **temperature_monitor.na** - Real-World Automation
```bash
uv run python -m dana.dana.exec.dana temperature_monitor.na
```
**What you'll learn:**
- Monitoring and alerting patterns
- Real-world sensor simulation
- Automated decision making
- System health patterns

**Key concepts:** Monitoring, automation, decision systems

### 5. **function_composition_demo*.na** - Advanced Patterns
```bash
# Try different composition examples
uv run python -m dana.dana.exec.dana function_composition_demo.na
uv run python -m dana.dana.exec.dana function_composition_demo_simple.na
uv run python -m dana.dana.exec.dana function_composition_demo_working.na
```
**What you'll learn:**
- Function composition techniques
- Data pipeline patterns
- Complex application architecture

**Key concepts:** Function composition, data pipelines

## 🚀 Quick Start

```bash
cd examples/dana/03_advanced_features/

# Start with AI reasoning basics
uv run python -m dana.dana.exec.dana reason_demo.na

# See a complete AI agent in action
uv run python -m dana.dana.exec.dana hybrid_math_agent.na

# Explore real-world patterns  
uv run python -m dana.dana.exec.dana temperature_monitor.na
```

## 🤖 AI Reasoning Patterns

### **Basic AI Reasoning**
```dana
# Simple reasoning with context
prompt = "What are the benefits of renewable energy?"
response = reason(prompt)
log(f"AI Response: {response}")

# Contextual reasoning
context = "You are an environmental expert."
detailed_prompt = f"{context}\n\nQuestion: {prompt}"
expert_response = reason(detailed_prompt)
```

### **Structured Query Pattern**
```dana
# Build structured prompts for better results
func create_analysis_prompt(data, question):
    local.prompt = f"""
Analyze the following data and answer the question:

Data: {data}
Question: {question}

Provide a clear, structured response with:
1. Key observations
2. Analysis
3. Conclusion
"""
    return local.prompt

# Use the structured prompt
data = {"sales": [100, 150, 200], "costs": [80, 90, 120]}
question = "What is the profitability trend?"
prompt = create_analysis_prompt(data, question)
analysis = reason(prompt)
```

### **AI Agent with Tools Pattern**
```dana
# Route queries to appropriate tools
func process_query(user_query):
    # Determine what type of query this is
    if "calculate" in user_query or "math" in user_query:
        return handle_math_query(user_query)
    elif "weather" in user_query:
        return handle_weather_query(user_query)
    else:
        # Fall back to general AI reasoning
        return reason(f"Help the user with this request: {user_query}")

func handle_math_query(query):
    # Extract math expression and validate
    prompt = f"""
Extract the mathematical expression from this query and solve it:
Query: {query}
Provide just the expression and answer.
"""
    return reason(prompt)
```

### **Validation and Verification Pattern**
```dana
# Combine AI reasoning with deterministic validation
func verified_calculation(expression):
    # Get AI solution
    ai_prompt = f"Solve this step by step: {expression}"
    ai_result = reason(ai_prompt)
    
    # Get deterministic solution (if possible)
    deterministic_result = calculate_directly(expression)
    
    if deterministic_result != null:
        # Compare results
        if results_match(ai_result, deterministic_result):
            return f"✅ Verified: {deterministic_result} (AI agrees)"
        else:
            return f"⚠️ Mismatch: AI says {ai_result}, calc says {deterministic_result}"
    else:
        return f"AI Solution: {ai_result}"
```

## 🏗️ Application Architecture Patterns

### **AI Agent Architecture**
```dana
# Complete agent with state management
private:agent_state = {
    "name": "DataAnalyst",
    "capabilities": ["math", "analysis", "reporting"],
    "memory": {}
}

func process_request(request):
    log.info(f"Agent {agent_state['name']} processing: {request}")
    
    # Parse request intent
    intent = classify_intent(request)
    
    # Route to appropriate handler
    if intent == "analysis":
        return handle_analysis(request)
    elif intent == "calculation":
        return handle_calculation(request)
    else:
        return handle_general_query(request)

func classify_intent(request):
    prompt = f"""
Classify this request into one category:
- analysis: data analysis, trends, insights
- calculation: math, arithmetic, formulas  
- general: other questions

Request: {request}
Category:"""
    
    return reason(prompt).strip().lower()
```

### **Monitoring and Alerting Pattern**
```dana
# Real-world monitoring system
func monitor_system():
    # Collect metrics
    private:metrics = {
        "cpu_usage": get_cpu_usage(),
        "memory_usage": get_memory_usage(),
        "disk_usage": get_disk_usage(),
        "response_time": get_response_time()
    }
    
    # Check for issues
    private:alerts = []
    for metric, value in metrics.items():
        if is_critical_level(metric, value):
            alert = create_alert(metric, value)
            alerts.append(alert)
            log.error(f"CRITICAL: {alert}")
    
    # Generate summary report
    if len(alerts) > 0:
        return generate_alert_report(alerts)
    else:
        return "System healthy - all metrics normal"

func is_critical_level(metric, value):
    thresholds = {
        "cpu_usage": 90,
        "memory_usage": 85,
        "disk_usage": 95,
        "response_time": 5000
    }
    return value > thresholds.get(metric, 100)
```

## 🔄 Practice Exercises

### **Exercise 1: AI Research Assistant**
Build an AI research assistant that can answer questions with citations:
```dana
# Your task: Create a function that:
# - Takes a research question
# - Uses AI to provide an answer
# - Includes relevant context and reasoning
# - Formats the response professionally

func research_assistant(question, domain="general"):
    # Add your implementation here
    pass
```

### **Exercise 2: Smart Data Validator**
Create a system that uses AI to validate and clean data:
```dana
# Your task: Build a validator that:
# - Analyzes data for inconsistencies
# - Uses AI to suggest corrections
# - Validates the corrections
# - Returns clean data with a report

func smart_validator(raw_data):
    # Add your implementation here
    pass
```

### **Exercise 3: Decision Support System**
Build a system that helps with complex decisions:
```dana
# Your task: Create a decision support tool that:
# - Takes a decision scenario
# - Analyzes pros and cons using AI
# - Provides recommendations with reasoning
# - Considers multiple factors and stakeholders

func decision_support(scenario, criteria, constraints):
    # Add your implementation here  
    pass
```

## ⚠️ AI Integration Best Practices

### ✅ **Do This**
```dana
# Provide clear, specific prompts
prompt = f"""
Role: You are a financial analyst
Task: Analyze quarterly sales data
Data: {sales_data}
Format: Provide 3 bullet points with specific numbers
"""

# Validate AI responses when possible
ai_result = reason(prompt)
if can_validate(ai_result):
    validated = validate_response(ai_result)
    if not validated:
        log.warning("AI response validation failed")

# Handle AI failures gracefully
try:
    response = reason(prompt)
except Exception as e:
    log.error(f"AI reasoning failed: {e}")
    response = "Unable to process request at this time"
```

### ❌ **Avoid This**
```dana
# Don't use vague prompts
vague_prompt = "analyze this"  # Too vague
response = reason(vague_prompt)

# Don't trust AI responses blindly
calculation = reason("What is 2+2?")
result = int(calculation)  # No validation!

# Don't ignore error handling
response = reason(prompt)  # What if this fails?
important_decision = response.split()[0]  # Could crash
```

## 🎯 Key Takeaways

### **AI Reasoning Power**
- Use `reason()` for complex analysis and generation
- Provide clear context and specific instructions
- Validate AI responses when possible
- Handle failures gracefully

### **Agent Patterns**
- Break complex tasks into smaller functions
- Use state management for complex agents
- Implement clear query routing and intent detection
- Combine AI reasoning with deterministic validation

### **Real-World Applications**
- Monitor systems and generate intelligent alerts
- Automate decision-making with AI support
- Build tools that get smarter over time
- Create hybrid systems (AI + traditional logic)

## ➡️ **Next Steps**

Ready to make your functions even smarter?
1. **[POET Examples](../04_poet_examples/)** - Add automatic optimization and learning
2. **[MCP Integration](../05_mcp_integration/)** - Connect to external tools and APIs
3. **[Real-World Applications](../../04_real_world_applications/)** - See production examples

---

**Ready to optimize?** Continue to **[04_poet_examples](../04_poet_examples/)** to learn how POET can make your functions self-improving! 