# Dana REPL Guide - Interactive Development Environment

*Your interactive workspace for Dana development, testing, and debugging*

---

## Quick Start

```bash
# Start the REPL
python -m opendxa.dana.repl.dana_repl_app

# Or from your code
from opendxa.dana.repl.repl import REPL
repl = REPL()
result = repl.execute("x = 42\nprint(x)")
```

---

## Essential REPL Commands

### Basic Execution
```
dana> name = "OpenDXA"
dana> print(f"Hello, {name}!")
Hello, OpenDXA!

dana> agent.status = "ready"
dana> log.info(f"Agent status: {agent.status}")
[INFO] Agent status: ready
```

### Special Commands
| Command | Purpose |
|---------|---------|
| `##nlp on` | Enable natural language mode |
| `##nlp off` | Disable natural language mode |
| `##nlp status` | Check NLP availability |
| `help` or `?` | Show help |
| `exit` or `quit` | Exit REPL |
| `##` | Force execute incomplete block |

### Memory Inspection
```
dana> # Check current state
dana> print(private)
dana> print(public)
dana> print(system)
```

---

## Multiline Programming

The REPL automatically handles multiline input for complex logic:

### Conditional Logic
```
dana> if temperature > 100:
...     alert_level = "critical"
...     log.error("Temperature critical!")
...     trigger_alert()
... elif temperature > 80:
...     alert_level = "warning"
...     log.warn("Temperature elevated")
... else:
...     alert_level = "normal"
...     log.info("Temperature normal")
```

### Loops and Processing
```
dana> items = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
dana> processed = []
dana> for item in items:
...     result = reason("Summarize document", context=item)
...     processed.append(result)
...     log.info(f"Processed {item}")
```

### Complex Functions
```
dana> def analyze_document(doc_path):
...     document = load_document(doc_path)
...     
...     # Multi-step analysis
...     summary = reason("Summarize key points", context=document)
...     risks = reason("Identify potential risks", context=document)
...     recommendations = reason("Suggest actions", context=[summary, risks])
...     
...     return {
...         "summary": summary,
...         "risks": risks,
...         "recommendations": recommendations
...     }
```

---

## Interactive Development Workflows

### 1. Rapid Prototyping
```
# Quick idea testing
dana> idea = "Analyze customer sentiment"
dana> sample_data = "Customer said: 'Love the new features!'"
dana> result = reason(idea, context=sample_data)
dana> print(result)

# Iterate and refine
dana> refined_idea = "Rate customer sentiment on 1-10 scale"
dana> result = reason(refined_idea, context=sample_data, format="json")
```

### 2. Step-by-Step Debugging
```
# Test each step individually
dana> data = load_api_data()
dana> print(f"Loaded {len(data)} records")

dana> filtered_data = filter_valid_records(data)
dana> print(f"Valid records: {len(filtered_data)}")

dana> analysis = reason("Find patterns", context=filtered_data)
dana> log.debug(f"Analysis result: {analysis}")
```

### 3. Context Experimentation
```
# Test different context approaches
dana> context1 = [user_data, preferences]
dana> result1 = reason("Recommend products", context=context1)

dana> context2 = [user_data, preferences, purchase_history, trending_items]
dana> result2 = reason("Recommend products", context=context2)

dana> # Compare results
dana> print(f"Simple context: {result1}")
dana> print(f"Rich context: {result2}")
```

---

## Natural Language Mode

Enable NLP mode for natural language programming:

```
dana> ##nlp on
✅ NLP mode enabled

dana> add the numbers 42 and 17
✅ Execution result:
59

dana> load the sales data and find the top 3 products
✅ Transcoded to Dana:
sales_data = load_data("sales")
top_products = reason("Find top 3 products", context=sales_data)
print(top_products)

dana> ##nlp off
✅ NLP mode disabled
```

---

## Engineering Workflows

### API Development Testing
```
dana> # Test API integration
dana> api_response = fetch_api("/users/123")
dana> if api_response.status == 200:
...     user_data = api_response.data
...     analysis = reason("Analyze user behavior", context=user_data)
...     print(f"User analysis: {analysis}")
... else:
...     log.error(f"API error: {api_response.status}")

dana> # Test error handling
dana> try_api_call("invalid_endpoint")
```

### Document Processing Pipeline
```
dana> # Load documents
dana> docs = load_documents("contracts/*.pdf")
dana> print(f"Found {len(docs)} documents")

dana> # Process first document as test
dana> test_doc = docs[0]
dana> key_terms = reason("Extract key terms", context=test_doc)
dana> print(f"Key terms: {key_terms}")

dana> # Process all documents
dana> results = []
dana> for doc in docs:
...     result = reason("Extract key information", context=doc)
...     results.append({"doc": doc.name, "info": result})
...     print(f"Processed: {doc.name}")
```

### Agent Behavior Testing
```
dana> # Set up test scenario
dana> agent.role = "customer_service"
dana> customer_query = "I want to return a product"

dana> # Test response generation
dana> response = reason("Generate helpful response", context=[agent.role, customer_query])
dana> print(f"Agent response: {response}")

dana> # Test different personalities
dana> agent.personality = "friendly"
dana> friendly_response = reason("Generate helpful response", context=[agent, customer_query])

dana> agent.personality = "professional"
dana> professional_response = reason("Generate helpful response", context=[agent, customer_query])
```

---

## Debugging Techniques

### State Inspection
```
dana> # Check variable values
dana> print(f"Current variables: {locals()}")
dana> print(f"Agent state: {agent}")
dana> print(f"System info: {system}")

dana> # Trace execution
dana> log_level = DEBUG
dana> result = complex_operation()  # Will show detailed logs
```

### Error Investigation
```
dana> # Reproduce error conditions
dana> test_data = create_problematic_data()
dana> try:
...     result = process_data(test_data)
... except Exception as e:
...     log.error(f"Error details: {e}")
...     log.debug(f"Data that caused error: {test_data}")
```

### Performance Testing
```
dana> import time
dana> start_time = time.time()
dana> result = expensive_operation()
dana> end_time = time.time()
dana> print(f"Operation took {end_time - start_time:.2f} seconds")
```

---

## Best Practices

### 1. Use Descriptive Variables
```
# Good
dana> customer_sentiment_analysis = reason("Analyze sentiment", context=reviews)

# Avoid
dana> x = reason("stuff", context=data)
```

### 2. Log Important Steps
```
dana> log.info("Starting document analysis")
dana> result = analyze_documents()
dana> log.info(f"Analyzed {result.count} documents")
```

### 3. Test Incrementally
```
# Build up complexity gradually
dana> basic_analysis = reason("Simple question", context=data)
dana> detailed_analysis = reason("Complex question", context=[data, basic_analysis])
```

### 4. Save Working Code
```
dana> # Once you have working code, save it
dana> working_solution = """
... data = load_source()
... analysis = reason("Analyze data", context=data)
... report = generate_report(analysis)
... """
dana> save_to_file("working_solution.dana", working_solution)
```

---

## Integration with Development

### Export to Files
```python
# From your development environment
from opendxa.dana.repl.repl import REPL

repl = REPL()

# Test code interactively
test_code = """
agent.task = "document_analysis"
documents = load_documents("data/")
results = analyze_all(documents)
"""

result = repl.execute(test_code)
if result.success:
    # Export to production file
    save_to_production_file(test_code)
```

### Automated Testing
```python
# Create REPL tests
def test_document_processing():
    repl = REPL()
    
    # Set up test data
    repl.execute("test_docs = load_test_documents()")
    
    # Test processing
    result = repl.execute("process_documents(test_docs)")
    
    assert result.success
    assert "processed" in result.output.lower()
```

---

## Configuration

### Environment Setup
```bash
# Required for LLM features
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"
# or configure in opendxa_config.json
```

### Custom Configuration
```python
# Programmatic REPL setup
from opendxa.dana.repl.repl import REPL
from opendxa.common.resource import LLMResource

repl = REPL()
repl.add_resource("llm", LLMResource(model="gpt-4"))
```

---

## Next Steps

- **Build Real Agents**: Apply REPL learnings to [Agent Recipes](../recipes/)
- **Advanced Debugging**: See [Troubleshooting Guide](../troubleshooting/debugging-guide.md)
- **Production Deployment**: Learn [Best Practices](../setup/production-guide.md)
- **Language Mastery**: Deep dive into [Dana Syntax](dana-syntax.md) 