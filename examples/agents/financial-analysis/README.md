# Financial Analysis Agents

A comprehensive system for financial data analysis and report generation using coordinated AI agents.

## Overview

This project demonstrates a multi-agent architecture for financial analysis:

- **FinancialAnalysisAgent**: Specialist agent for extracting financial data, calculating ratios, and performing quantitative analysis
- **FinancialReportCoordinatorAgent**: Orchestrator agent that creates structured reports by delegating tasks and consolidating results

## Architecture

```
User Request
     ↓
FinancialReportCoordinatorAgent
     ├── Creates report structure
     ├── Delegates analysis tasks → FinancialAnalysisAgent
     │                                    ├── Searches documents (semantic + text)
     │                                    ├── Extracts financial data
     │                                    ├── Calculates ratios and metrics
     │                                    └── Returns detailed analysis
     ├── Consolidates results
     ├── Manages report files
     └── Delivers final report
```

## Agents

### FinancialAnalysisAgent

**Purpose**: Specialist for extracting and analyzing financial data from documents.

**Capabilities**:
- Semantic search for financial concepts
- Fast text search for exact terms
- Read files with line range support
- Calculate financial ratios (liquidity, profitability, leverage, efficiency)
- Analyze trends and growth rates
- Extract specific financial line items
- Provide interpretations with proper sourcing

**Resources**:
- `SemanticSearchResource` - Concept-based document search
- `RipgrepSearchResource` - Fast exact text search  
- `ReadFileResource` - Read files with line ranges
- `EditFileResource` - Edit files (optional)
- `CreateFileResource` - Create files (optional)
- `ListDirResource` - List directories

**Usage**:
```python
from agents import FinancialAnalysisAgent

analyst = FinancialAnalysisAgent(
    agent_id="financial-analysis-001",
    workspace_root="path/to/data",
    model="gpt-4.1-mini"
)

result = analyst.converse("Calculate the current ratio for AMD")
```

### FinancialReportCoordinatorAgent

**Purpose**: Orchestrator for creating comprehensive financial reports.

**Capabilities**:
- Analyze user requirements and design report structure
- Break down complex requests into analysis tasks
- Delegate quantitative analysis to FinancialAnalysisAgent
- Consolidate results into well-structured reports
- Manage report drafts through file operations
- Synthesize findings into executive summaries

**Sub-Agents**:
- `FinancialAnalysisAgent` - For all quantitative analysis

**Resources**:
- `CreateFileResource` - Create report files
- `EditFileResource` - Update report sections
- `ReadFileResource` - Read report state
- `ListDirResource` - List existing reports

**Usage**:
```python
from agents import FinancialAnalysisAgent, FinancialReportCoordinatorAgent

# Initialize specialist
analyst = FinancialAnalysisAgent(
    agent_id="financial-analysis-001",
    workspace_root="data/",
    model="gpt-4.1-mini"
)

# Initialize coordinator
coordinator = FinancialReportCoordinatorAgent(
    agent_id="coordinator-001",
    workspace_root="./",
    financial_analysis_agent=analyst,
    model="gpt-4.1-mini"
)

# Create comprehensive report
result = coordinator.converse(
    "Create a comprehensive financial health report for AMD"
)
```

## Directory Structure

```
financial-analysis/
├── agents/                          # Agent implementations
│   ├── __init__.py                 # Package exports
│   ├── financial_analysis_agent.py # Specialist agent
│   └── financial_report_coordinator.py # Coordinator agent
│
├── resources/                       # Reusable resources
│   ├── semantic_search_resource.py # RAG-based semantic search
│   ├── ripgrep_search_resource.py  # Fast text search
│   ├── read_file_resource.py       # File reading
│   ├── edit_file_resource.py       # File editing
│   ├── create_file_resource.py     # File creation
│   └── list_dir_resource.py        # Directory listing
│
├── prompts/                         # Agent prompt definitions
│   ├── FinancialAnalysisAgent.xml  # Analyst system prompt
│   └── FinancialReportCoordinator.xml # Coordinator system prompt
│
├── data/                            # Financial documents
│   └── AMD-AR.md                   # AMD annual report (markdown)
│
├── reports/                         # Generated reports (output)
│   └── .gitkeep
│
├── examples/                        # Demo scripts
│   └── create_financial_health_report.py
│
├── tests/                           # Test suite
│   ├── fixtures/                   # Test data
│   ├── test_ripgrep_search_resource.py
│   └── test_financial_report_coordinator.py
│
└── README.md                        # This file
```

## Report Types

### Financial Health Report

A comprehensive analysis covering:

1. **Executive Summary** - Synthesis of overall findings
2. **Liquidity Analysis** - Current ratio, quick ratio
3. **Profitability Analysis** - Gross, operating, and net margins; ROE, ROA
4. **Leverage Analysis** - Debt-to-equity, interest coverage
5. **Efficiency Analysis** - Asset turnover, inventory turnover
6. **Conclusions and Recommendations** - Strategic insights

## How It Works

### Agent Delegation

The coordinator delegates to the analyst using standard XML tool calls:

```xml
<tool_call>
    <target type="agent" id="financial-analysis-001"/>
    <method>invoke</method>
    <arguments>
        <message>Calculate AMD's current ratio with sources and interpretation</message>
    </arguments>
</tool_call>
```

### File Management

The coordinator manages reports through resources:

1. **Create draft**: Use `create-file` to generate report outline
2. **Read state**: Use `read-file` to check current report
3. **Update sections**: Use `edit-file` to insert analysis results
4. **List reports**: Use `list-dir` to show completed reports

### Search Strategy

The analyst uses a two-path search strategy:

1. **Primary**: Semantic search for concept-based retrieval
2. **Fallback**: Ripgrep text search for exact terms
3. **Detail**: Read files for precise value extraction

## Getting Started

### Quick Start

```bash
# Navigate to financial-analysis directory
cd examples/agents/financial-analysis

# Run the demo script
python examples/create_financial_health_report.py
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_financial_report_coordinator.py -v

# Run with detailed output
pytest tests/ -v -s
```

### Creating Custom Reports

```python
from agents import FinancialAnalysisAgent, FinancialReportCoordinatorAgent

# Setup
analyst = FinancialAnalysisAgent(
    agent_id="financial-analysis-001",
    workspace_root="data/",
    model="gpt-4.1-mini"
)

coordinator = FinancialReportCoordinatorAgent(
    agent_id="coordinator-001",
    workspace_root="./",
    financial_analysis_agent=analyst,
    model="gpt-4.1-mini"
)

# Request custom report
result = coordinator.converse("""
    Create a profitability analysis report for AMD covering:
    - Gross, operating, and net profit margins
    - Trend analysis over multiple periods
    - Comparison to industry benchmarks
    Save the report in the reports directory.
""")
```

## Key Features

### 1. Semantic Understanding
- Natural language queries: "What is the current ratio?"
- Concept-based search: Finds related content even with different terminology
- Context-aware: Understands financial concepts and relationships

### 2. Accurate Calculations
- Shows formulas: `Current Ratio = Current Assets / Current Liabilities`
- Cites sources: "Balance Sheet, Line 156"
- Provides context: Explains what metrics mean

### 3. Professional Reports
- Structured format: Clear sections and hierarchy
- Comprehensive analysis: Multiple dimensions covered
- Actionable insights: Conclusions and recommendations

### 4. Transparent Coordination
- Visible delegation: See which tasks go to which agents
- Traceable results: Every number has a source
- Progressive generation: Reports built incrementally

## Configuration

### LLM Models

Both agents support different LLM providers:

```python
# OpenAI
agent = FinancialAnalysisAgent(model="gpt-4.1-mini", llm_provider="openai")

# Anthropic
agent = FinancialAnalysisAgent(model="claude-sonnet-4", llm_provider="anthropic")
```

### Workspace Configuration

```python
# Analyst workspace: where financial data is located
analyst_workspace = "path/to/financial/documents"

# Coordinator workspace: where reports will be saved
coordinator_workspace = "path/to/reports/output"

analyst = FinancialAnalysisAgent(workspace_root=analyst_workspace)
coordinator = FinancialReportCoordinatorAgent(workspace_root=coordinator_workspace)
```

### Notifications

Enable verbose notifications to see agent activity:

```python
agent.enable_notifications(verbose=True)  # See all activity
agent.enable_notifications(verbose=False)  # Quiet mode
```

## Examples

### Example 1: Simple Metric Extraction

```python
analyst.converse("What is AMD's total revenue in 2023?")
# Returns: Revenue figure with source citation
```

### Example 2: Ratio Calculation

```python
analyst.converse("Calculate AMD's current ratio")
# Returns: Formula, calculation, components, interpretation
```

### Example 3: Comprehensive Report

```python
coordinator.converse("Create a financial health report for AMD")
# Creates: Multi-section report with executive summary
```

## Extending the System

### Adding New Report Types

1. Update coordinator prompt: Add template in `prompts/FinancialReportCoordinator.xml`
2. Define structure: Specify sections and analyses needed
3. Test: Add tests for the new report type

### Adding New Resources

1. Create resource: Implement in `resources/`
2. Register: Add to agent initialization
3. Document: Update prompt with resource capabilities

### Adding New Metrics

1. Update analyst prompt: Add metric to intent recognition
2. Provide examples: Show calculation method
3. Test: Verify extraction and calculation

## Troubleshooting

### No results found
- Check that data files exist in the data directory
- Verify workspace_root paths are correct
- Try alternative search terms

### Report not created
- Check reports directory exists and is writable
- Verify coordinator has create-file resource
- Enable notifications to see where it fails

### Agent delegation fails
- Verify sub-agent is registered: `coordinator.available_agents`
- Check agent IDs match in prompt and initialization
- Ensure both agents use same registry

## License

This project is part of the OpenDXA framework.

## Support

For issues or questions:
- Check test files for usage examples
- Review agent prompts for capabilities
- Enable verbose notifications for debugging


