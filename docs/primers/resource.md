# Dana Resource System Primer

## TL;DR (2 minute read)

**✅ The `resource` keyword is now implemented!** Resources work as specialized structs. The agent `.use()` method integration is still in development.

```dana
# Resource definition - works today!
resource DocumentRAG:
    sources: list = []
    chunk_size: int = 1024
    domain: str = "documents"

# Resource instantiation - works!
docs = DocumentRAG(sources=["report.pdf", "analysis.pdf"])
print("Resource domain:", docs.domain)  # Output: documents

# Resource behavior via struct-function pattern - works!
def (resource: DocumentRAG) query(request: str) -> str:
    return f"Analysis of {len(resource.sources)} documents: {request}"

# Direct usage - works!
result = docs.query("What are the key findings?")

# Agent integration - proposed future enhancement
agent_blueprint DataAnalyst:
    name: str = "DataAnalyst"

agent Alice(DataAnalyst)

# Future: agent.use() method (not yet implemented)
# def (agent: Alice) analyze(company: str) -> str:
#     return agent.use(docs).query(f"Analyze {company}")
```

---

**What it is**: Resources are now first-class types in Dana using the `resource` keyword. They work as specialized structs with behavior defined through the struct-function pattern. Agent integration via `.use()` is planned.

## Current Status & Future Vision

**Today (Current Dana)**: Resources are accessed through the legacy `use()` and `py_use()` functions:
```dana
agent_blueprint DataWorker:
    name: str = "DataWorker"

agent Alice(DataWorker)

# Current approach - functional calls
mcp_client = py_use("mcp", endpoint="http://localhost:8880")
result = mcp_client.call_tool("search", {"query": "test"})
```

**Proposed (Future Dana)**: Resources as first-class types with agent `.use()` method:
```dana
# Resources defined as structs  
resource MCPService(BaseResource):
    endpoint: str = "http://localhost:8880"

def (resource: MCPService) query(request: str) -> str:
    return f"MCP result for: {request}"

# Agent access via .use() method
def (agent: Alice) search(query: str) -> str:
    return agent.use(mcp_service).query(query)
```

## What are Resources?

Resources represent external tools, data sources, services, or computational capabilities that can be defined independently and used by agents. Examples include:

- **MCP Resources**: Model Context Protocol endpoints for tool calling
- **RAG Resources**: Retrieval Augmented Generation systems with document stores
- **Knowledge Resources**: Structured knowledge bases with facts, plans, and heuristics
- **Human Resources**: Interactive human-in-the-loop interfaces
- **Database Resources**: Connection endpoints to databases
- **API Resources**: External web service endpoints

## Implementation Status

✅ **The `resource` keyword is now implemented and working!**

**What exists today:**
- ✅ `resource` keyword for defining resource types (implemented!)
- ✅ Resource instantiation and field access
- ✅ Struct-function pattern for resource behavior  
- ✅ Standard `query()` interface via struct-functions
- Agent blueprints and singleton agents (`agent_blueprint`, `agent`)
- Basic agent functionality

**What's still in development:**
- 🚧 Agent `.use()` method for accessing resources
- 🚧 Resource lifecycle management (start/stop/suspend)
- 🚧 Resource transfer between agents via handles
- 🚧 Inheritance between resource types

## Core Concepts (Proposed)

### Independent Resource Definition
Resources would be defined independently of agents and instantiated at module level:

```dana
# Proposed syntax (not yet implemented)
my_docs: DocumentRAG = DocumentRAG(sources=["report1.pdf", "report2.pdf"])
market_api: MCPResource = MCPResource(endpoint="http://localhost:8880/market-data")
```

### Agent .use() Method (Proposed)
Agents would access resources using a `.use()` method, providing:
- Proper resource lifecycle management
- Security and access control
- Clear ownership and responsibility
- Structured resource sharing between agents

### Standard Resource Interface (Proposed)
All resources would implement a standard `query()` method as the primary interface:

```dana
# Proposed pattern: agent.use(resource).query(request)
result = analyst.use(docs).query("What are the key findings?")
```

### Resource Definition
Resources are defined using the `resource` keyword. Like all structs in Dana, they contain only fields:

```dana
# Resource definition - fields only
resource MyResource(BaseResource):
    kind: str = "custom"
    endpoint: str = ""
    timeout: int = 30

# Resource behavior implemented via struct-function pattern
def (resource: MyResource) start() -> bool:
    # Allocate/init external connections
    return true

def (resource: MyResource) stop() -> bool:
    # Release/cleanup
    return true

def (resource: MyResource) query(request: str) -> str:
    # Standard query interface
    return f"Custom response to: {request}"
```

### Resource Lifecycle
Resources follow a defined lifecycle:
- **CREATED**: Resource instance created but not initialized
- **RUNNING**: Resource active and available for use
- **SUSPENDED**: Resource temporarily unavailable
- **TERMINATED**: Resource permanently shut down

## Basic Usage

### 1. Defining a Custom Resource

```dana
# Resource definition - struct only, no functions inside
resource DocumentRAG(BaseResource):
    kind: str = "rag"
    sources: list[str] = []
    chunk_size: int = 1024
    domain: str = "documents"

# Resource functions use struct-function pattern
def (resource: DocumentRAG) start() -> bool:
    print(f"Loading {len(resource.sources)} document sources")
    # Initialize vector database, load embeddings, etc.
    return true

# Standard query method - implemented as external function
def (resource: DocumentRAG) query(request: str) -> str:
    if not resource.is_running():
        return "Resource not available"
    
    # Perform RAG query
    return f"Answer based on {len(resource.sources)} documents: {request}"
```

### 2. Using Resources with Agents

```dana
# Define resources independently
docs: DocumentRAG = DocumentRAG(
    sources=["report1.pdf", "report2.pdf"],
    description="Financial analysis documents"
)

market_api: MCPResource = MCPResource(
    endpoint="http://localhost:8880/market-data",
    description="Real-time market data"
)

# Agent definition
agent DataAnalyst:
    name: str = "DataAnalyst"

# Agent functions use .use() to access resources
def (analyst: DataAnalyst) analyze_company(company: str) -> str:
    # Use standard query interface on all resources
    document_context = analyst.use(docs).query(f"Financial data for {company}")
    market_data = analyst.use(market_api).query(f"Current price for {company}")
    
    # Combine with LLM reasoning
    analysis = reason(f"""
    Based on documents: {document_context}
    And market data: {market_data}
    Provide analysis for {company}
    """)
    
    return analysis
```

### 3. Resource Transfer Between Agents

Resources can be transferred between agents using portable handles:

```dana
# Shared resource
shared_data: DocumentRAG = DocumentRAG(sources=["important_docs.pdf"])

agent SourceAgent:
    name: str = "SourceAgent"

def (source: SourceAgent) share_data() -> ResourceHandle:
    # Create portable handle from resource
    return to_handle(shared_data)

agent TargetAgent:
    name: str = "TargetAgent"

def (target: TargetAgent) receive_data(handle: ResourceHandle) -> bool:
    # Reconstruct resource from handle
    received_data: DocumentRAG = from_handle(handle)
    
    # Use the reconstructed resource with standard query interface
    result = target.use(received_data).query("What documents are available?")
    return true
```

## Standard Query Interface

All resources implement a standard `query(request: str) -> str` method. This provides a consistent interface regardless of resource type:

```dana
# All these use the same query pattern:
doc_result = agent.use(document_rag).query("What are the key findings?")
api_result = agent.use(mcp_service).query("Get current stock prices")  
human_result = agent.use(human_interface).query("Do you approve this decision?")
knowledge_result = agent.use(knowledge_base).query("What are best practices?")
```

The query method handles:
- **Request interpretation**: Understanding what the agent is asking for
- **Resource-specific processing**: Using the resource's capabilities appropriately  
- **Response formatting**: Returning results in a consistent string format
- **Error handling**: Managing resource unavailability or failures

## Lifecycle and Context Managers

- All resources support start()/stop() by default. If you define `def (resource: X) start()` or `stop()`, they are called by lifecycle helpers.
- Resources are context managers; using `with` or `async with` automatically calls start()/stop():

```dana
# Sync context manager
with docs:
    result = agent.use(docs).query("Key findings?")

# Async context manager inside an async function
def (agent: DataAnalyst) analyze_async(topic: str) -> str:
    # Pseudocode illustrating async with; actual awaiting depends on call site
    async with market_api:
        return agent.use(market_api).query(f"Analyze {topic}")
```

### Minimal built-in methods

- start() -> bool: bring the resource up; idempotent
- stop() -> bool: tear the resource down; idempotent
- query(request) -> result: primary operation entrypoint (override per resource)
- get_stats() -> dict: optional lightweight telemetry
- get_metadata() -> dict: optional static metadata

## Standard Resource Types

### MCP Resource
For Model Context Protocol endpoints:

```dana
# Resource definition - struct only
resource MyMCP(MCPResource):
    endpoint: str = "http://localhost:8880/tools"
    auth: dict = {"api_key": "your-key"}
    timeout: int = 60

# MCP resource behavior
def (resource: MyMCP) query(request: str) -> str:
    # Implement MCP-specific query logic
    return f"MCP result for: {request}"

# Create resource instance
tools: MyMCP = MyMCP()

# Usage in agent:
agent WebSearcher:
    name: str = "WebSearcher"

def (searcher: WebSearcher) search(query: str) -> str:
    return searcher.use(tools).query(f"Search web for: {query}")
```

### RAG Resource
For document retrieval systems:

```dana
# Resource definition - struct only
resource CompanyRAG(RAGResource):
    sources: list[str] = ["10k.pdf", "earnings.pdf"]
    chunk_size: int = 512
    embedding_model: str = "all-MiniLM-L6-v2"

# RAG resource behavior
def (resource: CompanyRAG) query(request: str) -> str:
    # Implement RAG-specific query logic
    return f"RAG analysis of {len(resource.sources)} documents: {request}"

# Create resource instance
company_docs: CompanyRAG = CompanyRAG()
    
# Usage in agent:
agent DocumentAnalyzer:
    name: str = "DocumentAnalyzer"

def (analyzer: DocumentAnalyzer) analyze_trends() -> str:
    context = analyzer.use(company_docs).query("What are the revenue trends?")
    return context
```

### Knowledge Resource
For structured knowledge operations:

```dana
# Resource definition - struct only
resource DomainKnowledge(KnowledgeResource):
    sources: list[str] = ["knowledge_base.json"]
    domain: str = "finance"

# Knowledge resource behavior
def (resource: DomainKnowledge) query(request: str) -> str:
    # Implement knowledge-specific query logic
    return f"Knowledge from {resource.domain} domain: {request}"

# Create resource instance
knowledge_base: DomainKnowledge = DomainKnowledge()
    
# Usage in agent:
agent KnowledgeWorker:
    name: str = "KnowledgeWorker"

def (worker: KnowledgeWorker) analyze_investment() -> str:
    # Knowledge resources can handle different types of queries
    facts = worker.use(knowledge_base).query("What are key investment strategies?")
    plan = worker.use(knowledge_base).query("Create a plan for portfolio optimization")
    return f"Facts: {facts}\nPlan: {plan}"
```

### Human Resource
For human-in-the-loop interactions:

```dana
# Resource definition - struct only
resource UserInterface(HumanResource):
    interface_type: str = "console"
    timeout: int = 300
    prompt_template: str = "Please provide input: {question}"

# Human resource behavior
def (resource: UserInterface) query(request: str) -> str:
    # Implement human interaction logic
    formatted_prompt = resource.prompt_template.format(question=request)
    return f"Human response to: {formatted_prompt}"

# Create resource instance
human_interface: UserInterface = UserInterface()
    
# Usage in agent:
agent InteractiveAgent:
    name: str = "InteractiveAgent"

def (agent: InteractiveAgent) get_approval(decision: str) -> str:
    response = agent.use(human_interface).query(f"Should we proceed with {decision}?")
    return response
```

## Advanced Patterns

### Resource Composition
Combine multiple resources for complex workflows:

```dana
# Define resources independently
documents: DocumentRAG = DocumentRAG(sources=["docs/"])
market_data: MCPResource = MCPResource(endpoint="http://api.market.com")
human_expert: HumanResource = HumanResource()

agent ComplexAnalyst:
    name: str = "ComplexAnalyst"

def (analyst: ComplexAnalyst) comprehensive_analysis(topic: str) -> str:
    # Gather data from multiple resources using standard query interface
    doc_insights = analyst.use(documents).query(f"Analyze documents about {topic}")
    market_insights = analyst.use(market_data).query(f"Get market analysis for {topic}")
    
    # Get human validation
    human_feedback = analyst.use(human_expert).query(
        f"Please review this AI analysis:\nDocs: {doc_insights}\nMarket: {market_insights}"
    )
    
    # Final reasoning with all contexts
    return reason(f"""
    Document analysis: {doc_insights}
    Market analysis: {market_insights}
    Human feedback: {human_feedback}
    
    Provide final recommendation for: {topic}
    """)
```

### Resource Inheritance
Create specialized resources by inheriting from base types:

```dana
# Specialized resource definition - struct only
resource FinancialRAG(RAGResource):
    kind: str = "finance_rag"
    domain: str = "finance"
    financial_keywords: list[str] = ["revenue", "profit", "assets", "liabilities"]

# Specialized query function
def (resource: FinancialRAG) query(request: str) -> str:
    # Enhance query with financial context
    enhanced_request = f"Financial analysis: {request}. Focus on {resource.financial_keywords}"
    
    # Call parent RAG functionality (conceptually)
    base_result = f"RAG result for: {enhanced_request}"
    
    # Post-process for financial data
    return f"Financial Analysis: {base_result}"
```

### Conditional Resource Activation
Initialize resources only when needed:

```dana
# Heavy resource defined but not created initially
heavy_resource: ComplexRAG = None

agent EfficientAgent:
    name: str = "EfficientAgent"

def (agent: EfficientAgent) _is_complex_query(query: str) -> bool:
    # Check if query requires heavy processing
    return len(query) > 100 or "analyze" in query

def (agent: EfficientAgent) analyze_if_needed(query: str) -> str:
    # Only initialize expensive resource if complex query
    if agent._is_complex_query(query):
        if heavy_resource is None:
            heavy_resource = ComplexRAG(sources=["large_corpus/"])
            heavy_resource.start()
        
        return agent.use(heavy_resource).query(query)
    else:
        # Use simple processing
        return f"Simple analysis for: {query}"
```

## Resource Security and Best Practices

### 1. Agent-Only Access Enforcement
```dana
# This will cause a runtime error - resources must be in agent context
# direct_resource = MCPResource(endpoint="http://example.com")  # ERROR!
```

### 2. Proper Resource Lifecycle Management
```dana
# Resource defined independently
my_resource: MCPResource = MCPResource(endpoint="http://api.com")

agent ResponsibleAgent:
    resources_initialized: bool = false

def (agent: ResponsibleAgent) initialize_resources():
    if not agent.resources_initialized:
        my_resource.start()
        agent.resources_initialized = true

def (agent: ResponsibleAgent) cleanup():
    if agent.resources_initialized:
        my_resource.stop()
        agent.resources_initialized = false

def (agent: ResponsibleAgent) work():
    # Always use .use() with standard query interface
    result = agent.use(my_resource).query("Process the current data")
    return result
```

### 3. Error Handling
```dana
# Resource defined independently
my_resource: RAGResource = RAGResource(sources=["docs.pdf"])

agent RobustAgent:
    name: str = "RobustAgent"

def (agent: RobustAgent) safe_resource_call(query: str) -> str:
    try:
        if not my_resource.is_running():
            if not my_resource.start():
                return "Failed to initialize resource"
        
        return agent.use(my_resource).query(query)
    except ResourceError as e:
        return f"Resource error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
```

## Current Reality vs Future Vision

### Today's Dana (What Actually Works)
```dana
# Current agent syntax that works
agent_blueprint DataWorker:
    name: str = "DataWorker"
    domain: str = "analysis"

agent Alice(DataWorker):
    domain = "financial_analysis"

# Current approach - external resource calls (implementation varies)
# Note: py_use() may or may not be fully implemented yet
print("Alice domain:", Alice.domain)
```

### Proposed Resource System (Future Enhancement)
```dana
# Proposed resource definition
resource MyMCP(MCPResource):
    endpoint: str = "http://api.com"

def (resource: MyMCP) query(request: str) -> str:
    return f"MCP result for: {request}"

# Create resource instance
mcp: MyMCP = MyMCP()

agent_blueprint DataWorker:
    name: str = "DataWorker"

agent Alice(DataWorker)

# Proposed agent resource usage
def (agent: Alice) analyze() -> str:
    return agent.use(mcp).query("Search for test data")
```

## Integration with Dana Features

### With Agents and Workflows
Resources work seamlessly with Dana's agent and workflow systems:

```dana
# Define resource
docs: DocumentRAG = DocumentRAG(sources=["reports/"])

agent DataAnalyst:
    name: str = "DataAnalyst"

def (analyst: DataAnalyst) analyze_company(company: str) -> str:
    return analyst.use(docs).query(f"Analysis for {company}")

workflow AnalysisWorkflow:
    analyst: DataAnalyst = DataAnalyst()

def (workflow: AnalysisWorkflow) run(company: str) -> str:
    return workflow.analyst.analyze_company(company)
```

### With Promises and Concurrency
Resources support Dana's promise-based concurrency:

```dana
# Define resource
analyzer: DocumentRAG = DocumentRAG(sources=["docs/"])

agent ConcurrentAgent:
    name: str = "ConcurrentAgent"

def (agent: ConcurrentAgent) analyze_single_company(company: str) -> str:
    return agent.use(analyzer).query(f"Analysis for {company}")

def (agent: ConcurrentAgent) parallel_analysis(companies: list[str]) -> list[str]:
    promises = []
    
    for company in companies:
        # Each analysis runs concurrently
        promise = deliver agent.analyze_single_company(company)
        promises.append(promise)
    
    # Wait for all analyses to complete
    return [await p for p in promises]
```

## Troubleshooting

### Common Errors

1. **AgentAccessError**: Trying to use resources outside agent context
   ```
   Solution: Move resource usage inside agent methods
   ```

2. **ResourceError**: Resource not found or not initialized
   ```
   Solution: Check resource name and ensure proper initialization
   ```

3. **Resource not running**: Calling methods on uninitialized resources
   ```
   Solution: Call resource.start() or check resource.is_running()
   ```

### Debugging Tips

1. **Check resource state**: Use `resource.state` to see current lifecycle phase
2. **Verify agent context**: Ensure resource operations are within agent methods
3. **Test resource handles**: Validate handles before transfer using `handle.validate()`
4. **Monitor resource statistics**: Use registry statistics for system health

## Conclusion

The Dana resource system provides a powerful, secure, and structured way to manage external resources within agent contexts. By enforcing agent-only access and providing comprehensive lifecycle management, it enables robust, scalable agent applications while maintaining clear separation of concerns and security boundaries.

Key benefits:
- **Type Safety**: Resources are first-class types with compile-time checking
- **Security**: Agent-only access prevents unauthorized resource usage  
- **Lifecycle Management**: Automatic resource initialization and cleanup
- **Portability**: Resource handles enable seamless agent-to-agent transfer
- **Extensibility**: Easy to create custom resource types for specific needs
- **Integration**: Works seamlessly with Dana's agent, workflow, and concurrency features