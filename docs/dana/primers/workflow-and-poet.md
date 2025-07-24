# Workflow + POET Primer

**The beautiful relationship**: POET enhances individual functions, Workflow creates pipelines, and POET can enhance workflows too!

## Core Relationship

```mermaid
graph LR
    A["Individual Functions"] --> B["@poet() Enhancement"]
    C["Workflow Creation"] --> D["Pipeline"]
    B --> C
    D --> E["@poet() Enhancement"]
    
    style A fill:#e3f2fd
    style B fill:#e3f2fd
    style C fill:#f3e5f5
    style D fill:#f3e5f5
    style E fill:#fff3e0
```

## How They Work Together

### **POET** = Intelligent Function Enhancement
- Adds context injection, fault tolerance, output validation, adaptive learning
- Works on individual functions OR workflows
- Always active when you use `@poet()`

### **Workflow** = Pipeline Creation
- Combines functions using Dana's `|` operator
- Creates a single callable from multiple steps
- The result is just another function

## The Magic

```dana
# Step 1: POET enhances individual functions
@poet(domain="document_processing")
def extract_text(file): return ocr_process(file)

@poet(domain="analysis")
def analyze_content(text): return nlp_analysis(text)

@poet(domain="reporting")
def generate_report(analysis): return create_summary(analysis)

# Step 2: Workflow creates a pipeline
document_pipeline = extract_text | analyze_content | generate_report

# Step 3: POET can enhance the entire workflow!
@poet(domain="enterprise_pipeline", retries=3, timeout=120)
def enterprise_document_pipeline = extract_text | analyze_content | generate_report

# Result: Intelligent orchestration
# - Each step has context awareness and fault tolerance
# - The entire pipeline has deterministic execution and adaptive learning
# - Cross-step context sharing and output validation
```

## Benefits of the Combination

| Individual Functions | Workflows | POET-Enhanced Workflows |
|---------------------|-----------|------------------------|
| Single purpose | Multi-step processes | Intelligent orchestration |
| Easy to test | Sequential execution | Fault tolerance & learning |
| Domain focused | Pipeline composition | Cross-step context sharing |
| POET enhanced | Callable as one function | Pipeline-level intelligence |

## Quick Example

```dana
# Create POET-enhanced functions
@poet(domain="data_processing")
def load_data(source): return load(source)

@poet(domain="analysis")
def analyze_data(data): return analyze(data)

# Create workflow
data_workflow = load_data | analyze_data

# Enhance the entire workflow
@poet(domain="enterprise_workflow", retries=2)
def enterprise_workflow = load_data | analyze_data

# Now you have:
# ✅ Reliable individual functions (POET)
# ✅ Composed pipeline (Workflow)
# ✅ Enterprise-grade orchestration (POET + Workflow)
```

**Bottom line**: POET and Workflow are perfectly complementary - use them together for maximum power! 