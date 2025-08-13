# Workflow Primer

## TL;DR (1 minute read)

```dana
# Instead of this (manual function composition):
data = load_data("file.csv")  
cleaned = clean_data(data)
result = analyze_data(cleaned)

# Do this (workflow):
workflow DataPipeline = load_data | clean_data | analyze_data

# Execute with an agent (workflows require agents)
agent DataAnalyst
result = DataPipeline.execute(DataAnalyst, "file.csv")

# Rich metadata for trading/sharing
workflow PremiumAnalyzer:
    pipeline = load_data | advanced_analysis | generate_insights
    price: float = 299.99
    domain: str = "data_analytics"
    required_capabilities: list[str] = ["advanced_analytics"]

# Same workflow, different results based on agent expertise
agent JuniorAnalyst: expertise: str = "basic"
agent SeniorAnalyst: expertise: str = "expert"

basic_result = DataPipeline.execute(JuniorAnalyst, "data.csv")    # Basic analysis
expert_result = DataPipeline.execute(SeniorAnalyst, "data.csv")  # Expert insights

# Workflows compose with functions seamlessly
workflow ComplexFlow = preprocessing | DataPipeline | generate_report
```

**What it is**: Dana workflows are **first-class struct entities** that can be created, shared, and traded between agents. Unlike function composition, workflows are structured data requiring agent execution with expertise differentiation.

## Why Workflows Matter

### The Problem with Function Composition
```dana
# Old way: Functions composed directly  
def data_processor = load_data | clean_data | analyze_data
result = data_processor("input.csv")  # Direct execution
```

**Limitations:**
- No metadata or versioning
- Can't be shared between agents
- No capability requirements
- No trading or marketplace support
- Same result regardless of who runs it

### The Workflow Solution
```dana
# New way: Workflows as structured entities
workflow DataProcessor = load_data | clean_data | analyze_data

# Agents execute workflows with their expertise
agent JuniorAnalyst:
    expertise: str = "basic"

agent SeniorAnalyst:
    expertise: str = "expert" 
    specialization: str = "financial_data"

# Same workflow, different results based on agent expertise
junior_result = DataProcessor.execute(JuniorAnalyst, "data.csv")    # Basic analysis
senior_result = DataProcessor.execute(SeniorAnalyst, "data.csv")   # Expert insights
```

## Two Simple Concepts

Dana has just **two concepts** for all your composition needs:

### 1. **Functions** - Individual building blocks
```dana
def load_data(path: str) -> dict:
    return {"data": f"loaded from {path}"}

def clean_data(data: dict) -> dict:
    return {"cleaned": data["data"]}

# Functions execute directly
result = load_data("file.csv")  # ✅ Direct execution
```

### 2. **Workflows** - Structured compositions 
```dana
# Workflows require agents to execute
workflow DataCleaner = load_data | clean_data

agent DataAgent
result = DataCleaner.execute(DataAgent, "file.csv")  # ✅ Agent-mediated execution

# ❌ This won't work - workflows need agents
result = DataCleaner("file.csv")  # Error: Agent required
```

## Creating Workflows

### Direct Assignment (Recommended)
```dana
# Simple and clean - just like function composition but with workflow keyword
workflow SimpleAnalysis = load_data | clean_data | analyze_data

# With parameters and placeholders  
workflow CustomerService = capture_issue | research_solution($$, priority="high") | implement_fix

# Reuse existing functions and workflows
workflow ComplexFlow = preprocessing | SimpleAnalysis | generate_report
```

### With Rich Metadata (For Trading/Sharing)
```dana
workflow PremiumDataAnalyzer:
    # Execution pipeline
    pipeline = load_data | validate_schema | advanced_analysis | generate_insights
    
    # Metadata for marketplace
    name: str = "Premium Data Analysis Suite"
    version: str = "2.1.0"
    description: str = "Enterprise-grade data analysis with advanced insights"
    domain: str = "data_analytics"
    
    # Requirements
    required_capabilities: list[str] = ["advanced_analytics", "machine_learning"]
    permissions: list[str] = ["files:read", "network:access"]
    minimum_expertise: str = "expert"
    
    # Marketplace info
    price: float = 299.99
    license: str = "commercial"
```

## Universal Composition

Functions and workflows compose seamlessly:

```dana
# Mix functions and workflows in any combination
def preprocess_data(x: str) -> dict: ...
workflow DataCleaner = clean_data | validate_data
def final_report(x: dict) -> str: ...

# All compositions become workflows
workflow MegaProcessor = preprocess_data | DataCleaner | final_report

# Nested workflows work naturally
workflow OuterFlow = setup | MegaProcessor | cleanup

# Agent context flows through everything
agent ProcessingAgent
result = OuterFlow.execute(ProcessingAgent, "input.txt")
```

## Agent-Driven Execution

### Why Agent-Only Execution?

Workflows represent **intelligent processes** that benefit from agent capabilities:

```dana
workflow DocumentAnalysis = extract_text | analyze_sentiment | generate_summary

# Different agents provide different value
agent BasicAgent:
    expertise: str = "junior"

agent ExpertAgent:
    expertise: str = "senior"
    specialization: str = "legal_documents"
    capabilities: list[str] = ["legal_analysis", "contract_review"]

# Same workflow, different outcomes
basic_result = DocumentAnalysis.execute(BasicAgent, "contract.pdf")
# Result: Basic text analysis

expert_result = DocumentAnalysis.execute(ExpertAgent, "contract.pdf") 
# Result: Deep legal insights, risk assessment, compliance notes
```

### Built-in Agent Methods

Every agent can execute workflows and has built-in intelligence:

```dana
agent MyAgent

# Execute any workflow
result = MyAgent.execute_workflow(SomeWorkflow, input_data)

# Built-in conversational AI
response = MyAgent.chat("How should I analyze this data?")

# Planning and problem-solving  
plan = MyAgent.plan("Process quarterly reports")
solution = MyAgent.solve("Data quality issues detected")

# Memory management
MyAgent.remember("important_fact", "Always validate inputs first")
fact = MyAgent.recall("important_fact")
```

## Workflow Trading and Sharing

### Share Workflows Between Agents
```dana
# Agent A creates a workflow
workflow CustomerServiceFlow = capture_issue | research_solution | provide_resolution

# Agent A sends to Agent B
agent CustomerAgent
agent SupportAgent

CustomerAgent.send_workflow(CustomerServiceFlow, recipient=SupportAgent)

# Agent B receives and uses it
received_workflow = SupportAgent.receive_workflow()
result = received_workflow.execute(SupportAgent, customer_issue)
```

### Marketplace Integration
```dana
# Publish to marketplace
workflow PremiumAnalyzer:
    pipeline = advanced_analysis | deep_insights | executive_summary
    price: float = 199.99
    license: str = "commercial"

marketplace.publish(PremiumAnalyzer)

# Discover and purchase workflows
available = marketplace.search(domain="financial_analysis", expertise="expert")
purchased = marketplace.buy(workflow_id="premium_analyzer_v2", buyer=my_agent)
```

## Real-World Examples

### Data Processing Pipeline
```dana
workflow DataPipeline = load_csv | clean_data | calculate_stats | save_results

agent DataScientist:
    expertise: str = "expert"
    specialization: str = "data_analysis"

result = DataPipeline.execute(DataScientist, "sales_data.csv")
# Expert-level statistical analysis with insights
```

### Customer Service Workflow
```dana  
workflow CustomerSupport = capture_issue | analyze_sentiment | research_solutions | craft_response

agent SupportAgent:
    expertise: str = "intermediate"
    capabilities: list[str] = ["customer_service", "product_knowledge"]

response = CustomerSupport.execute(SupportAgent, customer_message)
# Personalized, knowledgeable customer service response
```

### Financial Analysis
```dana
workflow RiskAssessment:
    pipeline = load_financials | calculate_ratios | assess_risk | generate_report
    domain: str = "financial_analysis"
    required_capabilities: list[str] = ["financial_modeling", "risk_analysis"]

agent FinancialAnalyst:
    expertise: str = "expert"
    capabilities: list[str] = ["financial_modeling", "risk_analysis", "regulatory_compliance"]

assessment = RiskAssessment.execute(FinancialAnalyst, company_data)
# Professional risk analysis with regulatory insights
```

## Migration from Function Composition

### Easy Migration Path

```dana
# OLD: Function composition
def legacy_pipeline = validate_data | transform_data | analyze_data

# NEW: Workflow (one line change!)
workflow MigratedPipeline = validate_data | transform_data | analyze_data

# Benefits gained automatically:
# ✅ Agent-mediated execution with expertise
# ✅ Rich metadata and versioning support  
# ✅ Trading and sharing capabilities
# ✅ Type safety and validation
# ✅ Observability and error handling
```

### Automated Migration Tools

```dana
# Linter flags old patterns
def data_processor = load | process | save  # LINT: Consider converting to workflow

# One-click fix converts to:
workflow data_processor = load | process | save
```

## Advanced Features

### Error Handling and Observability
```dana
workflow RobustProcessor:
    pipeline = load_data | validate_data | process_data | save_data
    timeout: int = 300  # seconds
    max_retries: int = 3
    deterministic: bool = true

agent ProcessingAgent
result = RobustProcessor.execute(ProcessingAgent, "data.csv")

# Rich execution information
print(f"Status: {result.status}")           # "success" or "failed"  
print(f"Execution time: {result.execution_time}s")
print(f"Quality score: {result.quality_score}")     # Agent-enhanced quality
print(f"Steps: {len(result.step_traces)}")          # Detailed step traces
```

### Permissions and Security
```dana
workflow SecureProcessor:
    pipeline = read_sensitive_data | analyze_data | save_results
    permissions: list[str] = ["files:read", "files:write", "encryption:decrypt"]

agent LimitedAgent:
    permissions: list[str] = ["files:read"]  # Missing required permissions

# This will fail with clear error message
try:
    SecureProcessor.execute(LimitedAgent, "sensitive.csv")
except WorkflowPermissionError as e:
    print(f"Permission denied: {e}")  # "Agent lacks required permissions: files:write, encryption:decrypt"
```

### Type Safety
```dana
# Workflows are fully typed
def load_csv(path: str) -> dict: ...
def analyze_data(data: dict) -> str: ...

workflow TypedFlow = load_csv | analyze_data
# Type: WorkflowType[str, str] (inferred from pipeline)

agent TypedAgent
result = TypedFlow.execute(TypedAgent, "data.csv")
# result.pipeline_result is guaranteed to be str type

# Type errors caught at composition time
def bad_function(x: int) -> float: ...
workflow BadFlow = load_csv | bad_function  # Error: Type mismatch (dict -> int)
```

## Key Benefits

### For Developers
- **Zero Learning Curve**: Same pipe syntax (`|`) you already know
- **Simple Mental Model**: Functions + Workflows (no complex composition types)
- **Type Safety**: Full type checking across all compositions
- **Easy Migration**: One-line conversion from function composition

### For Agents
- **Intelligence Enhancement**: Agents apply expertise to workflow execution
- **Capability Matching**: Workflows specify required agent capabilities  
- **Result Enrichment**: Same workflow, different insights based on agent specialization
- **Collaboration**: Seamless workflow sharing between agents

### For Organizations  
- **Workflow Marketplace**: Buy, sell, and trade specialized workflows
- **Reusability**: Workflows as portable, versioned digital assets
- **Standardization**: Consistent workflow metadata and execution patterns
- **Observability**: Built-in tracing, metrics, and error reporting

## Pro Tips

### 1. Start Simple
```dana
# Begin with direct assignment
workflow SimpleFlow = step1 | step2 | step3

# Add metadata when you need sharing/trading
workflow EnterpriseFlow:
    pipeline = step1 | step2 | step3
    version: str = "1.0.0"
    price: float = 99.99
```

### 2. Leverage Agent Expertise
```dana
# Design workflows that benefit from different agent capabilities
workflow DocumentReview = extract_text | analyze_content | generate_recommendations

# Let different agents provide different value
legal_review = DocumentReview.execute(LegalAgent, "contract.pdf")      # Legal analysis
technical_review = DocumentReview.execute(TechnicalAgent, "spec.pdf")  # Technical insights
```

### 3. Compose Incrementally
```dana
# Build complex workflows from simpler ones
workflow DataIngestion = load_data | validate_schema
workflow DataProcessing = clean_data | transform_data  
workflow DataOutput = generate_report | send_notifications

workflow FullDataPipeline = DataIngestion | DataProcessing | DataOutput
```

### 4. Use Metadata Strategically
```dana
# Minimal metadata for internal workflows
workflow InternalFlow = step1 | step2

# Rich metadata for shared/traded workflows
workflow MarketplaceFlow:
    pipeline = step1 | step2
    name: str = "Premium Data Processor"
    description: str = "Enterprise-grade data processing with advanced analytics"
    version: str = "2.1.0"
    domain: str = "data_analytics"  
    required_capabilities: list[str] = ["advanced_analytics"]
    price: float = 299.99
```

## Bottom Line

Dana workflows transform function composition into **intelligent, tradeable entities**:

- **Simple**: Just two concepts (Functions + Workflows)
- **Powerful**: Agent-mediated execution with expertise differentiation  
- **Structured**: Rich metadata for trading, versioning, and collaboration
- **Familiar**: Same pipe syntax (`|`) with enhanced capabilities
- **Future-Ready**: Built for agent economies and workflow marketplaces

Start with simple workflows using familiar pipe syntax, then add structure and intelligence as your needs grow. The same workflow can provide basic automation for junior agents and expert insights for senior agents - it's all about who executes it!