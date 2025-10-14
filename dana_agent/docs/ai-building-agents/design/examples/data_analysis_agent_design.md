# Data Analysis Agent - Design Example

## Overview

This document applies the STARAgent Team Design Methodology to create a Data Analysis Agent that helps analysts reason through data analysis tasks and execute them using Python with libraries like pandas, numpy, and matplotlib.

---

## Phase 1: Problem Analysis

### 1.1 Problem Definition

**What problem needs to be solved?**
Data analysts need an intelligent assistant that can:
- Understand analysis requests in natural language
- Reason through the appropriate analytical approach
- Generate correct Python code for the analysis
- Execute the code safely
- Interpret and explain results

**Who are the users/stakeholders?**
- Data scientists
- Business analysts
- Researchers
- Data engineers
- Anyone working with structured data

**What are the success criteria?**
- Correct analytical approach chosen
- Valid, executable Python code generated
- Safe execution (no destructive operations)
- Clear reasoning explanations
- Accurate result interpretation
- Reproducible analysis

**What are the constraints?**
- Must explain reasoning before coding
- Code must be safe (no file deletion, system calls, etc.)
- Must handle common data formats (CSV, JSON, Excel)
- Must work with pandas, numpy, matplotlib, seaborn
- Must provide clear error messages
- Must handle missing data gracefully

### 1.2 Core Capabilities Required

**External Systems:**
- Python execution environment (sandboxed)
- File system access (read data files)
- Data visualization libraries
- Statistical computation libraries

**Cognitive Tasks:**
- Understand analysis intent
- Reason about analytical approach
- Generate Python code
- Interpret results
- Detect data quality issues
- Suggest next steps

**Workflows/Processes:**
- Analysis reasoning workflow
- Code generation and execution workflow
- Data validation workflow
- Visualization workflow

**Domain Knowledge:**
- Statistical methods
- Data manipulation techniques
- Python/pandas best practices
- Data visualization principles

---

## Phase 2: Component Identification

### 2.1 Resource Analysis

**Reusable Resources (from library):**
- ✅ `ConversationResource` - for understanding user intent
- ✅ `LLMResource` - for reasoning and code generation

**Resources to Create:**
- ❌ `PythonExecutionResource` - Safe Python code execution
  - Execute code in sandboxed environment
  - Capture stdout, stderr, return values
  - Handle exceptions gracefully
  - Timeout protection
  - **Why needed**: Core capability for executing analysis
  - **Domain-agnostic**: Yes - can execute any Python code safely

- ❌ `DataFrameOperationsResource` - pandas/numpy operations
  - Load data from various formats
  - Infer schema and data types
  - Basic data profiling
  - Memory-efficient operations
  - **Why needed**: Common data operations abstracted
  - **Domain-agnostic**: Yes - works with any tabular data

- ❌ `DataValidationResource` - Data quality checks
  - Check for missing values
  - Detect outliers
  - Validate data types
  - Assess completeness
  - **Why needed**: Ensure data quality before analysis
  - **Domain-agnostic**: Yes - general data quality patterns

### 2.2 Workflow Analysis

**Workflows to Create:**

1. **AnalysisReasoningWorkflow**
   - **Purpose**: Reason through the analytical approach before coding
   - **Steps**: Understand request → Identify data characteristics → Choose methods → Explain approach
   - **Deterministic**: Partially (structured reasoning steps)
   - **Domain-specific**: Yes (data analysis domain)
   - **Pattern**: Sequential with LLM reasoning

2. **PythonAnalysisWorkflow**
   - **Purpose**: Generate, validate, and execute Python code for analysis
   - **Steps**: Generate code → Validate syntax → Execute → Capture results → Interpret
   - **Deterministic**: Yes (clear execution steps)
   - **Domain-specific**: Yes (Python/pandas specific)
   - **Pattern**: Sequential pipeline with error handling

3. **DataProfilingWorkflow**
   - **Purpose**: Quickly profile a dataset to understand its structure
   - **Steps**: Load data → Infer types → Calculate statistics → Detect issues → Generate report
   - **Deterministic**: Yes
   - **Domain-specific**: Yes (data profiling)
   - **Pattern**: Sequential with parallel stat calculations

4. **VisualizationWorkflow**
   - **Purpose**: Generate appropriate visualizations for data
   - **Steps**: Understand data → Choose viz type → Generate code → Execute → Render
   - **Deterministic**: Mostly
   - **Domain-specific**: Yes (data visualization)
   - **Pattern**: Sequential with validation

### 2.3 Agent Analysis

**Single Agent Approach:**
Given the focused domain (data analysis) and clear workflows, a **Single Specialist Agent** is appropriate.

**Rationale:**
- Single domain expertise (data analysis)
- Clear workflow orchestration
- No need for multi-agent coordination
- User interacts with one agent
- Workflows provide determinism

**Agent Pattern**: Single Specialist (like WebResearchAgent)

---

## Phase 3: Specialization Decomposition

### 3.1 Agent Identity

**PUBLIC_DESCRIPTION:**
```
<PUBLIC_DESCRIPTION>
Data Analysis Agent specializes in reasoning through data analysis tasks
and executing them in Python.

Use this agent for:
- Exploratory data analysis (EDA)
- Statistical analysis and hypothesis testing
- Data visualization and plotting
- Data cleaning and transformation
- Pandas/numpy operations
- Descriptive and inferential statistics

The agent follows a two-step process:
1. **Reason**: Explains the analytical approach before coding
2. **Execute**: Generates and runs Python code, interprets results

Capabilities:
- Load data from CSV, JSON, Excel, Parquet
- Profile datasets (types, missing data, distributions)
- Generate statistical summaries
- Create visualizations (matplotlib, seaborn)
- Handle missing data and outliers
- Validate data quality
- Explain results in plain language

Safety Features:
- Sandboxed code execution
- No destructive file operations
- Memory limits enforced
- Timeout protection
</PUBLIC_DESCRIPTION>
```

**PRIVATE_IDENTITY:**
```
<PRIVATE_IDENTITY>
You are a data analysis specialist who thinks carefully before coding.

Your process:
1. **Understand**: Clarify the analysis request and data context
2. **Reason**: Think through the analytical approach step-by-step
3. **Plan**: Decide on methods, libraries, and techniques
4. **Generate**: Write clean, well-commented Python code
5. **Execute**: Run the code and capture results
6. **Interpret**: Explain what the results mean

Your principles:
- Always reason before coding - explain your analytical strategy
- Write pedagogical code with clear variable names and comments
- Validate data before analysis (check for missing values, types, outliers)
- Use appropriate statistical methods for the question
- Create clear, informative visualizations
- Explain results in language the user can understand
- Acknowledge limitations and assumptions
- Suggest follow-up analyses when appropriate

You are methodical, thorough, pedagogical, and scientifically rigorous.
You never execute code without first explaining your reasoning.
You always validate your assumptions about the data.
</PRIVATE_IDENTITY>
```

### 3.2 Agent Scope

**Responsibilities:**
- Understand analysis requests in natural language
- Reason through appropriate analytical approaches
- Generate Python code for data analysis
- Execute code safely in sandboxed environment
- Profile and validate data quality
- Create appropriate visualizations
- Interpret and explain results
- Suggest next steps or follow-up analyses
- Handle errors gracefully with clear explanations

**Non-Responsibilities (what agent does NOT do):**
- Does NOT perform machine learning model training (that's MLAgent's job)
- Does NOT deploy code to production (that's DeploymentAgent's job)
- Does NOT access databases directly (use DatabaseAgent)
- Does NOT handle real-time streaming data (use StreamingAgent)
- Does NOT perform distributed computing (use SparkAgent)
- Does NOT create web applications or dashboards

**Dependencies:**
- User provides data files or data sources
- Python execution environment available
- Required libraries installed (pandas, numpy, matplotlib, seaborn, scipy)
- Sufficient memory for data operations
- Write access to temporary directory for outputs

**Outputs:**
- Analytical reasoning explanation
- Generated Python code
- Execution results (stdout, stderr, return values)
- Generated visualizations (PNG/SVG files)
- Result interpretation
- Recommended next steps
- Data quality reports

---

## Phase 4: Composition Strategy

### 4.1 Workflow Designs

#### Workflow 1: AnalysisReasoningWorkflow

**Purpose**: Think through the analysis before writing code

**Structure**:
```python
class AnalysisReasoningWorkflow(BaseWorkflow):
    """
    Reason through analytical approach before coding.

    USE FOR: Understanding what analysis to perform and why
    STEPS: Parse request → Analyze data context → Choose methods → Explain reasoning
    """

    def __init__(self, **kwargs):
        super().__init__(workflow_id="analysis-reasoning", **kwargs)
        self.conversation = ConversationResource()

    @validate_input(
        analysis_request={"required": True, "type": str, "min_length": 1},
        data_context={"type": dict, "default": {}},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        analysis_request = kwargs["analysis_request"]
        data_context = kwargs.get("data_context", {})

        # Use LLM to reason through approach
        reasoning_prompt = f"""
        Analysis Request: {analysis_request}

        Data Context:
        - Columns: {data_context.get('columns', [])}
        - Shape: {data_context.get('shape', 'unknown')}
        - Types: {data_context.get('types', {})}
        - Missing Data: {data_context.get('missing_summary', {})}

        Task: Reason through the analytical approach:
        1. What is the user trying to understand?
        2. What analytical methods are appropriate?
        3. What assumptions do we need to validate?
        4. What are the steps to perform this analysis?
        5. What libraries/functions should we use?

        Provide a clear, step-by-step reasoning.
        """

        reasoning_result = self._generate_reasoning(reasoning_prompt)

        return {
            "reasoning": reasoning_result["reasoning"],
            "methods_chosen": reasoning_result["methods"],
            "assumptions": reasoning_result["assumptions"],
            "steps": reasoning_result["steps"],
        }
```

**Pattern Used**: Sequential with LLM reasoning

---

#### Workflow 2: PythonAnalysisWorkflow

**Purpose**: Generate, execute, and interpret Python analysis code

**Structure**:
```python
class PythonAnalysisWorkflow(BaseWorkflow):
    """
    Generate and execute Python code for data analysis.

    USE FOR: Executing analytical code after reasoning
    STEPS: Generate code → Validate → Execute → Capture results → Interpret
    """

    def __init__(self, **kwargs):
        super().__init__(workflow_id="python-analysis", **kwargs)
        self.python_executor = PythonExecutionResource()

    @validate_input(
        analysis_plan={"required": True, "type": dict},
        data_path={"required": True, "type": str},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        analysis_plan = kwargs["analysis_plan"]
        data_path = kwargs["data_path"]

        # Pipeline: Generate → Validate → Execute → Interpret
        workflow = (
            CallableWorkflow(
                self._generate_code,
                "analysis_plan=analysis_plan, data_path=data_path -> generated_code"
            )
            | CallableWorkflow(
                self._validate_code_safety,
                "code=generated_code -> validated_code"
            )
            | CallableWorkflow(
                self.python_executor.execute_code,
                "code=validated_code, timeout=30 -> execution_result"
            )
            | CallableWorkflow(
                self._interpret_results,
                "execution_result=execution_result -> interpretation"
            )
        )

        return workflow.execute(**kwargs)

    def _generate_code(self, analysis_plan: dict, data_path: str) -> str:
        """Generate Python code based on analysis plan"""
        # Use LLM to generate code
        pass

    def _validate_code_safety(self, code: str) -> str:
        """Validate that code is safe to execute"""
        # Check for dangerous operations
        dangerous_patterns = [
            "os.remove", "os.system", "subprocess",
            "eval(", "exec(", "__import__",
            "open(", "write"
        ]
        for pattern in dangerous_patterns:
            if pattern in code:
                raise ValueError(f"Unsafe operation detected: {pattern}")
        return code

    def _interpret_results(self, execution_result: dict) -> dict:
        """Interpret execution results"""
        # Use LLM to interpret results
        pass
```

**Pattern Used**: Sequential Pipeline with validation

---

#### Workflow 3: DataProfilingWorkflow

**Purpose**: Quickly understand dataset characteristics

**Structure**:
```python
class DataProfilingWorkflow(BaseWorkflow):
    """
    Profile a dataset to understand its structure and quality.

    USE FOR: Initial data exploration
    STEPS: Load → Infer types → Calculate stats → Detect issues → Report
    """

    def __init__(self, **kwargs):
        super().__init__(workflow_id="data-profiling", **kwargs)
        self.dataframe_ops = DataFrameOperationsResource()
        self.data_validation = DataValidationResource()

    @validate_input(
        data_path={"required": True, "type": str},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        data_path = kwargs["data_path"]

        # Phase 1: Load and basic info
        df_info = self.dataframe_ops.load_and_describe(data_path)

        # Phase 2: Parallel quality checks
        async def quality_checks():
            return await asyncio.gather(
                self.data_validation.check_missing_data(df_info),
                self.data_validation.detect_outliers(df_info),
                self.data_validation.check_data_types(df_info),
            )

        missing_report, outlier_report, type_report = asyncio.run(quality_checks())

        # Phase 3: Generate summary report
        profile = {
            "shape": df_info["shape"],
            "columns": df_info["columns"],
            "types": df_info["types"],
            "missing_data": missing_report,
            "outliers": outlier_report,
            "type_issues": type_report,
            "summary_statistics": df_info["describe"],
        }

        return profile
```

**Pattern Used**: Phased (sequential load → parallel checks → sequential synthesis)

---

### 4.2 Agent Composition

```python
# dana/lib/agents/data_analysis.py

from dana.core.agent.star_agent import STARAgent
from dana.lib.resources import ConversationResource
from dana.lib.workflows.data_analysis import (
    AnalysisReasoningWorkflow,
    PythonAnalysisWorkflow,
    DataProfilingWorkflow,
    VisualizationWorkflow,
)

class DataAnalysisAgent(STARAgent):
    """
    Data Analysis Agent for reasoning through and executing data analysis tasks.
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        super().__init__(
            agent_type="data-analyst",
            agent_id=agent_id or "data-analyst",
            **kwargs
        )

        self.with_workflows(
            AnalysisReasoningWorkflow(workflow_id="analysis-reasoning"),
            PythonAnalysisWorkflow(workflow_id="python-analysis"),
            DataProfilingWorkflow(workflow_id="data-profiling"),
            VisualizationWorkflow(workflow_id="visualization"),
        ).with_resources(
            PythonExecutionResource(resource_id="python-executor"),
            DataFrameOperationsResource(resource_id="dataframe-ops"),
            DataValidationResource(resource_id="data-validation"),
            ConversationResource(resource_id="conversation"),
        )
```

**Composition Characteristics:**
- **Minimal agent code**: ~30 lines (mostly configuration)
- **4 workflows**: Focused, domain-specific orchestration
- **4 resources**: Mix of domain-specific and reusable
- **Clear identity**: Defined in separate .prt file
- **Single specialist pattern**

---

### 4.3 Resource Designs

#### Resource 1: PythonExecutionResource

```python
# dana/lib/resources/python_execution.py

class PythonExecutionResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Safe Python code execution resource.

    Provides methods for:
    - **execute_code**: Execute Python code in sandboxed environment
    - **validate_syntax**: Check code syntax before execution
    - **get_execution_context**: Retrieve available libraries and environment

    Safety Features:
    - Sandboxed execution (no system access)
    - Timeout protection (default 30s)
    - Memory limits
    - Captures stdout, stderr, return values
    - Graceful exception handling

    USE CASES:
    - Data analysis code execution
    - Script testing and validation
    - Interactive Python environments
    - Code generation verification
    </PUBLIC_DESCRIPTION>
    """

    def __init__(self, timeout: int = 30, memory_limit_mb: int = 512, **kwargs):
        super().__init__(resource_id="python-executor", **kwargs)
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.sandbox = self._create_sandbox()

    @tool_use
    @observable
    def execute_code(
        self,
        code: str,
        timeout: int | None = None,
        capture_output: bool = True,
        **kwargs
    ) -> DictParams:
        """
        Execute Python code in sandboxed environment.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (default: 30)
            capture_output: Capture stdout/stderr (default: True)

        Returns:
            Dictionary with:
            - success: bool
            - return_value: any (if code returns something)
            - stdout: str (captured output)
            - stderr: str (captured errors)
            - execution_time: float (seconds)
            - error: str (if execution failed)
        """
        timeout = timeout or self.timeout

        try:
            # Execute in sandbox with timeout
            result = self.sandbox.execute(
                code=code,
                timeout=timeout,
                capture_output=capture_output,
            )

            return {
                "success": True,
                "return_value": result.return_value,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
            }

        except TimeoutError as e:
            return {
                "success": False,
                "error": f"Execution timeout after {timeout}s",
                "stdout": "",
                "stderr": "",
                "execution_time": timeout,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "execution_time": 0,
            }

    @tool_use
    @observable
    def validate_syntax(self, code: str, **kwargs) -> DictParams:
        """
        Validate Python code syntax without executing.

        Args:
            code: Python code to validate

        Returns:
            Dictionary with:
            - valid: bool
            - error: str (if invalid)
            - line_number: int (if error)
        """
        try:
            compile(code, "<string>", "exec")
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line_number": e.lineno,
            }
```

**Pattern Used**: External capability resource with safety features

---

#### Resource 2: DataFrameOperationsResource

```python
# dana/lib/resources/dataframe_operations.py

class DataFrameOperationsResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    DataFrame operations and data loading resource.

    Provides methods for:
    - **load_data**: Load data from various formats (CSV, JSON, Excel, Parquet)
    - **describe_dataframe**: Get statistical description
    - **infer_schema**: Infer data types and schema
    - **sample_data**: Get representative sample

    Supports:
    - Multiple file formats
    - Automatic type inference
    - Memory-efficient loading
    - Missing data detection

    USE CASES:
    - Initial data loading
    - Data profiling
    - Schema inference
    - Data quality assessment
    </PUBLIC_DESCRIPTION>
    """

    @tool_use
    @observable
    def load_and_describe(self, file_path: str, **kwargs) -> DictParams:
        """
        Load data and return comprehensive description.

        Args:
            file_path: Path to data file

        Returns:
            Dictionary with:
            - shape: (rows, cols)
            - columns: list of column names
            - types: dict of column types
            - describe: statistical summary
            - sample: first few rows
            - memory_usage: memory footprint
        """
        try:
            # Auto-detect format and load
            df = self._load_file(file_path)

            return {
                "success": True,
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "types": df.dtypes.to_dict(),
                "describe": df.describe().to_dict(),
                "sample": df.head().to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
```

**Pattern Used**: Domain-agnostic operations on structured data

---

## Phase 5: Validation and Refinement

### 5.1 Design Validation

**Component Reusability:**
- ✅ `PythonExecutionResource` - can be used by any agent needing Python execution
- ✅ `DataFrameOperationsResource` - works with any tabular data
- ✅ `DataValidationResource` - general data quality patterns
- ✅ Workflows are data-analysis specific but composable

**Composition Clarity:**
- ✅ Clear hierarchy: Agent → Workflows → Resources
- ✅ Dependencies explicit in __init__
- ✅ Components testable independently

**Specialization:**
- ✅ Agent has focused role (data analysis)
- ✅ Workflows are domain-specific orchestration
- ✅ Resources are domain-agnostic capabilities
- ✅ Scope is appropriate (not too broad, not too narrow)

**Determinism:**
- ✅ Code execution is deterministic (given same code)
- ✅ Validation steps are explicit
- ✅ Error handling is comprehensive
- ✅ Workflows provide clear progression

**Performance:**
- ✅ Data profiling uses parallel quality checks
- ✅ Fast path for simple profiling (skip heavy stats)
- ✅ Code execution has timeout protection
- ✅ System prompt is focused and appropriate size

### 5.2 Example Usage

**Use Case: Exploratory Data Analysis**

```python
# User asks: "Can you analyze sales_data.csv and tell me about the trends?"

# Step 1: Agent profiles the data
profiling_result = agent.query(
    message="Profile sales_data.csv",
    workflow="data-profiling"
)
# Returns: shape, columns, types, missing data summary, outliers

# Step 2: Agent reasons about the analysis
reasoning_result = agent.query(
    message="Analyze sales trends over time",
    data_context=profiling_result
)
# Returns: reasoning about time-series analysis approach

# Step 3: Agent generates and executes code
analysis_result = agent.query(
    message="Execute the time-series analysis",
    analysis_plan=reasoning_result,
    data_path="sales_data.csv"
)
# Returns: code, execution results, interpretation, visualization
```

---

## Key Design Decisions

1. **Single Agent vs Multi-Agent**: Chose single specialist because domain is focused and workflows provide sufficient organization

2. **Reasoning-First Approach**: Agent always reasons before coding to ensure appropriate methods and catch issues early

3. **Sandboxed Execution**: Safety is critical - all code runs in sandbox with timeouts and memory limits

4. **Domain-Agnostic Resources**: PythonExecutionResource and DataFrameOperationsResource are reusable across domains

5. **Validation at Multiple Levels**: Syntax validation, safety validation, data validation all explicit

6. **Graceful Error Handling**: Every component has fallback paths and clear error messages

7. **Observable Execution**: All steps are observable for debugging and monitoring

---

## Implementation Checklist

- [ ] Create PythonExecutionResource with sandbox implementation
- [ ] Create DataFrameOperationsResource with multi-format support
- [ ] Create DataValidationResource with quality checks
- [ ] Implement AnalysisReasoningWorkflow
- [ ] Implement PythonAnalysisWorkflow
- [ ] Implement DataProfilingWorkflow
- [ ] Implement VisualizationWorkflow
- [ ] Create DataAnalysisAgent composition
- [ ] Write agent identity prompt file
- [ ] Create unit tests for each resource
- [ ] Create unit tests for each workflow
- [ ] Create integration tests for full agent
- [ ] Add example notebooks demonstrating usage
- [ ] Document safety limitations and constraints

---

## Related Documents

- [Agent Team Design Guide](../agent_team_design_guide.md)
- [Agent Design Patterns](../agent_design_patterns.md)
- [Workflow Design Patterns](../workflow_design_patterns.md)
- [Resource Design Patterns](../resource_design_patterns.md)
