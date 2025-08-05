import os
import subprocess
import sys
import tempfile
import pkg_resources
from typing import List
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest


class FinanceCodingResource(BaseResource):
    """Finance-specific coding resource for generating and executing Python code for financial calculations."""

    def __init__(
        self,
        name: str = "finance_coding_resource",
        description: str | None = None,
        debug: bool = True,
        timeout: int = 60,  # Financial calculations may take longer
        **kwargs,
    ):
        super().__init__(
            name,
            description
            or "Specialized resource for financial calculations and analysis",
        )
        self.debug = debug
        self.timeout = timeout
        # Initialize LLM resource for code generation
        try:
            self._llm_resource = LLMResource(
                name=f"{name}_llm",
                description="LLM for finance code generation",
                **kwargs,
            )
        except Exception as e:
            self.error(f"Failed to create LLM resource: {e}")
            self._llm_resource = None

        self._is_ready = False
        self._available_packages = None
        self._financial_packages = [
            "numpy",
            "pandas",
            "scipy",
            "statsmodels",
            "yfinance",
            "quantlib",
            "ta-lib",
            "pyfolio",
            "zipline",
        ]
        # Visualization libraries to exclude
        self._forbidden_packages = [
            "matplotlib",
            "seaborn",
            "plotly",
            "bokeh",
            "altair",
            "pygal",
            "chart-studio",
        ]

    def _get_available_packages(self) -> List[str]:
        """Get list of available packages with focus on financial libraries."""
        if self._available_packages is None:
            try:
                # Get installed packages
                installed_packages = [d.project_name for d in pkg_resources.working_set]

                # Add standard library modules
                try:
                    import stdlib_list

                    stdlib_modules = stdlib_list.stdlib_list()
                except ImportError:
                    # Fallback if stdlib_list is not installed
                    stdlib_modules = []

                # Combine and sort, but exclude forbidden visualization packages
                all_packages = list(set(installed_packages + stdlib_modules))
                # Filter out forbidden packages
                all_packages = [
                    pkg for pkg in all_packages if pkg not in self._forbidden_packages
                ]
                all_packages.sort()

                # Check which financial packages are available
                available_financial = [
                    pkg for pkg in self._financial_packages if pkg in all_packages
                ]

                self._available_packages = all_packages
                if self.debug:
                    print(f"Detected {len(all_packages)} available packages")
                    print(
                        f"Available financial packages: {', '.join(available_financial)}"
                    )
            except Exception as e:
                self.warning(f"Could not detect available packages: {e}")
                # Fallback to common packages
                self._available_packages = [
                    "os",
                    "sys",
                    "math",
                    "random",
                    "datetime",
                    "json",
                    "csv",
                    "collections",
                    "itertools",
                    "functools",
                    "re",
                    "string",
                    "numpy",
                    "pandas",
                    "matplotlib",
                    "scipy",
                    "decimal",
                ]

        return self._available_packages

    async def initialize(self) -> None:
        """Initialize the finance coding resource and LLM."""
        await super().initialize()

        if self._llm_resource:
            try:
                await self._llm_resource.initialize()
                self._is_ready = True
                if self.debug:
                    print(
                        f"Finance coding resource [{self.name}] initialized successfully"
                    )
            except Exception as e:
                self.error(f"Failed to initialize LLM resource: {e}")
                self._is_ready = False
        else:
            self.warning(
                "No LLM resource available, finance coding resource will use fallback methods"
            )
            self._is_ready = True

    @ToolCallable.tool
    async def calculate_financial_metrics(
        self, request: str, max_retries: int = 3
    ) -> str:
        """Generate Python code for financial calculations and execute it.

        @description: Generate Python code for financial calculations and execute it. Specialized for financial metrics like NPV, IRR, portfolio analysis, risk metrics, growth rates, etc. IMPORTANT: For growth rate calculations, provide ALL available time-series data points (e.g., quarterly data: {"Q1": 100, "Q2": 110, "Q3": 115, "Q4": 125}) not just start/end values. The tool will analyze multi-period patterns and calculate period-over-period growth rates. Always include temporal context (daily, monthly, quarterly, annual) for all data points.

        Args:
            request: Natural language description of the financial calculation needed. For time-series data (revenue, costs, growth rates), include ALL data points with their time periods, not just totals. Example: "Calculate quarterly growth rate for revenue: Q1 2024: $1.2M, Q2 2024: $1.5M, Q3 2024: $1.8M, Q4 2024: $2.1M"
            max_retries: Maximum number of retry attempts if code generation fails

        Returns:
            The execution result of the generated financial calculation code
        """

        if not self._is_ready:
            await self.initialize()

        if self.debug:
            print(f"Executing financial calculation for request: \n```\n{request}\n```")

        last_error = None
        last_python_code = None

        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    # First attempt: generate and execute
                    python_code = await self._generate_financial_python_code(request)
                else:
                    # Retry attempts: use error feedback to improve
                    python_code = await self._generate_financial_code_with_feedback(
                        request, last_error, last_python_code, attempt
                    )

                # Validate code doesn't contain chart generation
                is_valid, validation_error = self._validate_no_charts(python_code)
                if not is_valid:
                    last_error = validation_error
                    last_python_code = python_code
                    continue

                # Execute the generated code with timeout
                result = self._execute_python_code(python_code, timeout=self.timeout)

                # Check if execution was successful
                if not result.startswith("Error:") and not result.startswith(
                    "TimeoutError:"
                ):
                    if attempt > 0:
                        if self.debug:
                            print(
                                f"Successfully executed code on attempt {attempt + 1}"
                            )
                    if self.debug:
                        print(f"Result: \n```\n{result}\n```")
                    return result
                else:
                    last_error = result
                    last_python_code = python_code

            except Exception as e:
                last_error = f"Error: {str(e)}"
                self.error(f"Attempt {attempt + 1} failed: {e}")

        # All attempts failed
        return f"Failed after {max_retries + 1} attempts. Last error: {last_error}"

    async def _generate_financial_python_code(self, request: str) -> str:
        """Generate Python code for financial calculations."""

        if self._llm_resource and self._llm_resource._is_available:
            return await self._generate_financial_with_llm(request)
        else:
            # Only use fallback if LLM is completely unavailable
            return self._generate_financial_fallback(request)

    async def _generate_financial_with_llm(self, request: str) -> str:
        """Generate financial Python code using LLM."""

        # Get available packages
        available_packages = self._get_available_packages()
        financial_packages = [
            pkg for pkg in self._financial_packages if pkg in available_packages
        ]

        packages_info = ", ".join(available_packages[:50])
        if len(available_packages) > 50:
            packages_info += f" ... and {len(available_packages) - 50} more"

        financial_packages_info = (
            ", ".join(financial_packages)
            if financial_packages
            else "numpy, pandas (basic libraries)"
        )

        prompt = f"""
# ROLE: You are a senior quantitative finance engineer and financial analyst.
# TASK: Write an *executable* Python 3.12 script for financial calculations based on the user's request.
# AVAILABLE PACKAGES: {packages_info}
# FINANCIAL PACKAGES: {financial_packages_info}
# RULES (strict):
#  1. OUTPUT *ONLY* runnable Python code  no comments, markdown, or explanations.
#  2. PREFER pandas for financial data - use DataFrames for time series, multi-period data, and tabular calculations
#  3. Use pandas for: cash flows, financial statements, ratio analysis, time series, and any tabular data
#  4. Use numpy for: mathematical operations, statistical calculations, and array computations
#  5. Include print() statements with clear labels showing:
#     - Input parameters and their values WITH TIME PERIOD (e.g., "Q3 2024 Revenue", "Annual 2023 Expenses")
#     - Intermediate calculations with proper financial terminology AND TIME CONTEXT
#     - Final results with appropriate formatting (percentages, currency, etc.)
#     - ALWAYS include temporal granularity (daily, monthly, quarterly, annual) for ALL financial metrics
#     - For rates and flows: ALWAYS specify the time period (e.g., "Monthly Cash Burn Rate", "Annual Interest Rate")
#  6. Format financial outputs appropriately:
#     - Percentages: show as "12.5%" not "0.125"
#     - Currency: use comma separators and 2 decimal places
#     - Rates: specify if annual, monthly, daily
#     - Use pandas .to_string() with formatters for professional tables
#     - Example: df.to_string(index=False, formatters={{'Amount': '${{:,.2f}}'.format}})
#  7. Handle financial edge cases (division by zero, negative values where inappropriate).
#  8. Use proper financial formulas and conventions.
#  9. MULTI-PERIOD DATA DETECTION FOR GROWTH RATES:
#     - ALWAYS analyze input data structure first - check if data contains multiple time periods
#     - If data spans multiple quarters/years, calculate period-over-period growth rates
#     - Use pandas to identify time series patterns: look for date columns, quarter labels, or sequential periods
#     - For growth rates: NEVER treat multi-period data as single point - extract time series and calculate compound growth
#     - Example: If data has Q1, Q2, Q3, Q4 values, calculate QoQ growth rates, not just end-to-start
#     - Always print data structure analysis: "Detected X periods from Y to Z"
# 10. TIME PERIOD LABELING REQUIREMENTS:
#     - Cash flows: "Annual Operating Cash Flow", "Monthly Cash Burn", "Quarterly Free Cash Flow"
#     - Rates: "Annual Growth Rate", "Monthly Interest Rate", "Daily Burn Rate"
#     - Ratios with time context: "TTM P/E Ratio", "Q3 2024 Current Ratio"
#     - Never output ambiguous labels like "Cash Flow: $X" or "Burn Rate: $X" without time period
# 11. CRITICAL: NO VISUALIZATION LIBRARIES ALLOWED
#     - NEVER import matplotlib, seaborn, plotly, or any chart/plot libraries
#     - NO plt.show(), fig.show(), or any chart display commands
#     - Use ONLY text output with ASCII art, Unicode symbols, and print statements
#     - If visualization is requested, create ASCII representations instead

# FINANCIAL CONCEPTS TO HANDLE WITH PANDAS:
# - Time value of money: Use pd.DataFrame for cash flows with date indices, .sum() for NPV
# - Portfolio metrics: pd.DataFrame for price/return series, .rolling().std() for volatility
# - Risk metrics: pd.DataFrame.quantile() for VaR, .rolling() for time-series risk
# - Bond calculations: pd.date_range() for payment schedules, DataFrame for bond analytics
# - Option pricing: pd.DataFrame for option chains, vectorized calculations
# - Financial ratios: DataFrame operations for multi-period ratio analysis
# - Cash flow analysis: Time-indexed DataFrames, .resample() for period aggregation
# - Loan/mortgage calculations: pd.DataFrame for amortization schedules
# - Growth rate analysis: ALWAYS use .pct_change() for period-over-period, .cumprod() for compound growth

# PANDAS PATTERNS FOR FINANCIAL DATA:
# - Use pd.date_range() for time periods (pd.date_range('2024', periods=12, freq='M'))
# - Create DataFrames with meaningful column names: ['Date', 'Cash_Flow', 'Present_Value']
# - Use .to_string() with formatters for financial table output
# - Apply .rolling() for moving averages and time-series metrics
# - Use .pct_change() for return calculations
# - Use .resample() for period aggregation (monthly to quarterly)

# EXAMPLE REQUEST 1 (NPV Calculation):
#   Calculate the NPV of a project with initial investment of $100,000
#   and annual cash flows of $30,000 for 5 years at a 10% discount rate.
#
# EXAMPLE REQUEST 2 (Growth Rate with Multi-Period Data):
#   Calculate growth rates for quarterly revenue data:
#   Q1 2024: $1.2M, Q2 2024: $1.5M, Q3 2024: $1.8M, Q4 2024: $2.1M
#   
#   The tool will:
#   1. Detect this as time-series data (4 quarters)
#   2. Calculate QoQ growth rates: Q1→Q2: 25%, Q2→Q3: 20%, Q3→Q4: 16.7%
#   3. Calculate compound quarterly growth rate (CQGR): 20.5%
#   4. Calculate annualized growth rate: 75%
#   5. Identify trend: Decelerating growth pattern

# EXAMPLE OUTPUT (format only  do **NOT** include this example in your answer):
# import pandas as pd
# import numpy as np
# 
# # Create pandas DataFrame for cash flow analysis
# periods = pd.date_range(start='2024-01-01', periods=6, freq='YE')
# cash_flows = pd.DataFrame({{
#     'Year': range(2024, 2030),
#     'Date': periods,
#     'Cash_Flow': [-100000, 30000, 30000, 30000, 30000, 30000]
# }})
# cash_flows['Period'] = ['Initial'] + [f'Year {{i}}' for i in range(1, 6)]
# discount_rate = 0.10
# 
# print(f"Annual Discount Rate: {{discount_rate*100:.1f}}%")
# print(f"Analysis Period: {{cash_flows['Year'].min()}} to {{cash_flows['Year'].max()}}")
# 
# # Calculate present values using pandas
# cash_flows['Discount_Factor'] = (1 + discount_rate) ** range(len(cash_flows))
# cash_flows['Present_Value'] = cash_flows['Cash_Flow'] / cash_flows['Discount_Factor']
# 
# # Display formatted DataFrame
# print("\\nCash Flow Analysis:")
# print(cash_flows[['Period', 'Cash_Flow', 'Present_Value']].to_string(
#     index=False, 
#     formatters={{'Cash_Flow': '${{:,.0f}}'.format, 'Present_Value': '${{:,.0f}}'.format}}
# ))
# 
# npv = cash_flows['Present_Value'].sum()
# 
# print(f"\\nNet Present Value (NPV): ${{npv:,.2f}}")
# print(f"Annual Return Rate: {{(npv/abs(cash_flows.iloc[0]['Cash_Flow']))*100:.1f}}%")
# print(f"Project Status: {{'Profitable' if npv > 0 else 'Unprofitable'}}")

# USER REQUEST
{request}
        """

        llm_request = BaseRequest(
            arguments={
                "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,  # Lower temperature for financial calculations
            }
        )

        response = await self._llm_resource.query(llm_request)

        if response.success:
            content = response.content
            if isinstance(content, dict):
                if "choices" in content and content["choices"]:
                    code = content["choices"][0].get("message", {}).get("content", "")
                else:
                    for key in ["content", "text", "message", "result", "code"]:
                        if key in content:
                            code = content[key]
                            break
                    else:
                        code = str(content)
            else:
                code = str(content)

            return self._clean_code(code)
        else:
            self.error(f"LLM generation failed: {response.error}")
            raise Exception(f"LLM generation failed: {response.error}")

    async def _generate_financial_code_with_feedback(
        self, request: str, last_error: str, last_python_code: str, attempt: int
    ) -> str:
        """Generate financial Python code using LLM with error feedback."""

        available_packages = self._get_available_packages()
        financial_packages = [
            pkg for pkg in self._financial_packages if pkg in available_packages
        ]

        packages_info = ", ".join(available_packages[:50])
        if len(available_packages) > 50:
            packages_info += f" ... and {len(available_packages) - 50} more"

        prompt = f"""Generate Python code for financial calculation: {request}

Available packages: {packages_info}
Financial packages: {", ".join(financial_packages) if financial_packages else "numpy, pandas"}

Previous attempt failed with error: {last_error}

Previous code that failed:
```python
{last_python_code}
```

This is attempt {attempt + 1}. Please fix the issues:

CRITICAL REQUIREMENTS:
- Return ONLY executable Python code
- NEVER use matplotlib, seaborn, plotly, or ANY visualization libraries
- NO charts, plots, or graphical output - text only with ASCII representations
- Use proper financial formulas and conventions
- Format outputs appropriately (percentages, currency)
- Include temporal granularity for time-series data
- Handle financial edge cases
- Fix the specific error from the previous attempt

Common financial calculation fixes:
- Division by zero: Check denominators before division
- Negative values: Validate inputs for functions like sqrt, log
- Time periods: Ensure consistent time units (annual vs monthly)
- Array dimensions: Match dimensions for portfolio calculations
- Missing data: Handle NaN values in financial time series
- Chart generation: Replace with ASCII art, tables, or text descriptions

If error mentions visualization/charts:
- Remove all matplotlib/plotting imports
- Replace charts with text tables or ASCII representations
- Use print statements with formatted output instead of plots
"""

        llm_request = BaseRequest(
            arguments={
                "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # Very low temperature for focused fixes
            }
        )

        response = await self._llm_resource.query(llm_request)

        if response.success:
            content = response.content
            if isinstance(content, dict):
                if "choices" in content and content["choices"]:
                    code = content["choices"][0].get("message", {}).get("content", "")
                else:
                    for key in ["content", "text", "message", "result", "code"]:
                        if key in content:
                            code = content[key]
                            break
                    else:
                        code = str(content)
            else:
                code = str(content)

            return self._clean_code(code)
        else:
            self.error(f"LLM generation with feedback failed: {response.error}")
            raise Exception(f"LLM generation with feedback failed: {response.error}")

    def _generate_financial_fallback(self, request: str) -> str:
        """Generate pandas-based financial Python code when LLM is not available."""

        return f'''import pandas as pd
import numpy as np

def calculate_financial_metric():
    """{request}"""
    print("Financial calculation request received")
    print("Note: Using fallback mode - pandas-based calculation")
    
    # Basic example: time series financial calculation using pandas
    periods = pd.date_range(start='2024-01-01', periods=12, freq='M')
    financial_data = pd.DataFrame({{
        'Date': periods,
        'Month': periods.strftime('%Y-%m'),
        'Principal': 1000,
        'Annual_Rate': 0.05,
        'Monthly_Rate': 0.05/12
    }})
    
    # Calculate monthly compound interest
    financial_data['Interest'] = financial_data['Principal'] * financial_data['Monthly_Rate']
    financial_data['Balance'] = financial_data['Principal'] * (1 + financial_data['Annual_Rate']/12) ** range(1, 13)
    
    print(f"Analysis Period: {{financial_data['Month'].iloc[0]}} to {{financial_data['Month'].iloc[-1]}}")
    print(f"Principal Amount: ${{financial_data['Principal'].iloc[0]:,.2f}}")
    print(f"Annual Interest Rate: {{financial_data['Annual_Rate'].iloc[0]*100:.1f}}%")
    
    # Display summary table
    summary = financial_data[['Month', 'Interest', 'Balance']].head(6)
    print("\\nMonthly Interest Calculation (First 6 months):")
    print(summary.to_string(index=False, formatters={{
        'Interest': '${{:,.2f}}'.format,
        'Balance': '${{:,.2f}}'.format
    }}))
    
    final_balance = financial_data['Balance'].iloc[-1]
    total_interest = final_balance - financial_data['Principal'].iloc[0]
    
    print(f"\\nFinal Balance (12 months): ${{final_balance:,.2f}}")
    print(f"Total Interest Earned: ${{total_interest:,.2f}}")
    
    return final_balance

result = calculate_financial_metric()
print(f"\\nFinal Result: ${{result:,.2f}}")
'''

    def _clean_code(self, code: str) -> str:
        """Clean up generated code by removing markdown formatting."""

        # Remove markdown code blocks
        if "```python" in code:
            start = code.find("```python") + 9
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
        elif "```" in code:
            start = code.find("```") + 3
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()

        return code.strip()

    def _validate_time_context(self, output: str) -> str:
        """Add warnings if output lacks proper time context."""
        # Check for common financial terms without time context
        ambiguous_terms = [
            (
                "Cash Burn:",
                "Cash Burn Rate:",
                "Consider specifying: Annual/Monthly/Daily Cash Burn Rate",
            ),
            (
                "Revenue:",
                "Revenue Growth:",
                "Consider specifying: Annual/Quarterly/Monthly Revenue",
            ),
            (
                "Cash Flow:",
                "Operating Cash Flow:",
                "Consider specifying time period for cash flow",
            ),
            (
                "Interest Rate:",
                "Rate:",
                "Consider specifying: Annual/Monthly Interest Rate",
            ),
            (
                "Return:",
                "Return Rate:",
                "Consider specifying: Annual/Monthly/Daily Return",
            ),
        ]

        warnings = []
        for term, context, suggestion in ambiguous_terms:
            if (
                term in output
                and context not in output
                and not any(
                    period in output
                    for period in [
                        "Annual",
                        "Monthly",
                        "Quarterly",
                        "Daily",
                        "Year",
                        "Month",
                        "Quarter",
                        "Day",
                    ]
                )
            ):
                warnings.append(f"⚠️ {suggestion}")

        if warnings:
            return output + "\n\n" + "\n".join(warnings)
        return output

    def _validate_no_charts(self, code: str) -> tuple[bool, str]:
        """Validate that code doesn't contain visualization/chart libraries.

        Returns:
            (is_valid, error_message): is_valid=False if charts detected
        """
        # Check for forbidden imports and function calls
        forbidden_patterns = [
            "import matplotlib",
            "from matplotlib",
            "import seaborn",
            "from seaborn",
            "import plotly",
            "from plotly",
            "import bokeh",
            "from bokeh",
            "plt.show()",
            "plt.plot(",
            "plt.bar(",
            "plt.hist(",
            "plt.scatter(",
            "fig.show()",
            "chart.show()",
            ".plot(",
            ".bar(",
            ".hist(",
            ".scatter(",
            "seaborn.",
            "sns.",
            "plotly.",
            "bokeh.",
        ]

        # Convert to lowercase for case-insensitive checking
        code_lower = code.lower()

        for pattern in forbidden_patterns:
            if pattern.lower() in code_lower:
                return (
                    False,
                    f"CHART GENERATION BLOCKED: Code contains forbidden visualization pattern '{pattern}'. Use text-only output with ASCII art instead.",
                )

        return True, ""

    def _execute_python_code(self, code: str, timeout: int = 60) -> str:
        """
        Execute Python code and return the result. If execution exceeds timeout, returns TimeoutError.
        Args:
            code: Python code to execute
            timeout: Maximum seconds to allow code execution (default 60s for complex financial calculations)
        Returns:
            Output string, or TimeoutError string if timed out
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_file = f.name
            # Execute the code
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            # Clean up
            os.unlink(temp_file)
            # Return output
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return f"TimeoutError: Code execution timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {str(e)}"

    async def cleanup(self) -> None:
        """Clean up the finance coding resource."""
        if self._llm_resource:
            await self._llm_resource.cleanup()
        await super().cleanup()
        if self.debug:
            print(f"Finance coding resource [{self.name}] cleaned up")

    async def query(self, request: str) -> None:
        """Query the finance coding resource."""
        pass

    @ToolCallable.tool
    async def analyze_portfolio(
        self, holdings_json: str, prices_json: str, benchmark: str = "SPY"
    ) -> str:
        """Analyze a portfolio's performance metrics.

        @description: Analyze a portfolio's performance metrics including returns, volatility, and Sharpe ratio. Calculates total portfolio value, individual position values and weights, portfolio diversity metrics, and compares to a benchmark.

        Args:
            holdings_json: JSON string of ticker symbols to number of shares (e.g., '{"AAPL": 100, "GOOGL": 50}')
            prices_json: JSON string of ticker symbols to current prices (e.g., '{"AAPL": 195.50, "GOOGL": 175.25}')
            benchmark: Benchmark ticker for comparison (default: SPY)

        Returns:
            Analysis results including portfolio metrics and comparison to benchmark
        """
        import json

        try:
            holdings = json.loads(holdings_json)
            prices = json.loads(prices_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Analyze portfolio with holdings: {holdings}
        Current prices: {prices}
        Calculate:
        1. Total portfolio value
        2. Individual position values and weights
        3. Portfolio diversity metrics
        4. Compare to benchmark: {benchmark}
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def calculate_loan_metrics(
        self,
        principal: float,
        annual_rate: float,
        years: int,
        payment_frequency: str = "monthly",
    ) -> str:
        """Calculate loan/mortgage metrics.

        @description: Calculate loan/mortgage metrics including payment amount, total interest, and amortization schedule. Provides detailed breakdown of payments, interest vs principal allocation, and complete amortization table.

        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
            years: Loan term in years
            payment_frequency: Payment frequency (monthly, quarterly, annual)

        Returns:
            Loan calculation results including payment details and amortization schedule
        """
        request = f"""
        Calculate loan metrics:
        - Principal: ${principal:,.2f}
        - Annual interest rate: {annual_rate * 100:.2f}%
        - Term: {years} years
        - Payment frequency: {payment_frequency}
        
        Calculate:
        1. Payment amount per period
        2. Total amount paid
        3. Total interest paid
        4. Amortization schedule (first 12 periods and last 12 periods)
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def analyze_income_statement(
        self,
        revenue_json: str,
        expenses_json: str,
        period: str = "annual",
        years: int = 1,
    ) -> str:
        """Analyze income statement and calculate profitability metrics.

        @description: Analyze income statement data to calculate gross profit, operating profit, net profit, and various profitability margins. Supports multi-period analysis for trend identification. IMPORTANT: For growth analysis, provide complete time-series data (e.g., {"Q1_2024": 100000, "Q2_2024": 110000, "Q3_2024": 125000, "Q4_2024": 140000}) to calculate quarter-over-quarter and year-over-year growth rates. Provides insights into revenue growth, expense management, and profitability trends.

        Args:
            revenue_json: JSON string of revenue items. For multi-period analysis, use nested structure (e.g., '{"Q1_2024": {"product_sales": 250000, "service_revenue": 125000}, "Q2_2024": {"product_sales": 275000, "service_revenue": 137500}}')
            expenses_json: JSON string of expense items. For multi-period analysis, use nested structure (e.g., '{"Q1_2024": {"cost_of_goods_sold": 150000, "operating_expenses": 75000}, "Q2_2024": {"cost_of_goods_sold": 165000, "operating_expenses": 82500}}')
            period: Time period - 'annual', 'quarterly', or 'monthly'
            years: Number of years/periods to analyze (for trend analysis)

        Returns:
            Comprehensive income statement analysis with profitability metrics and trends
        """
        import json

        try:
            revenue = json.loads(revenue_json)
            expenses = json.loads(expenses_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Analyze income statement with following data:
        Revenue breakdown: {revenue}
        Expense breakdown: {expenses}
        Period: {period}
        Years to analyze: {years}
        
        Calculate:
        1. Total revenue and revenue growth rate
        2. Gross profit and gross margin
        3. Operating profit (EBIT) and operating margin
        4. Net profit and net margin
        5. EBITDA if depreciation/amortization data available
        6. Expense ratios (each expense category as % of revenue)
        7. Year-over-year growth rates if multiple periods
        8. Common-size income statement (all items as % of revenue)
        9. DuPont analysis components if applicable
        
        Format all percentages as XX.X% and currency with proper formatting.
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def analyze_balance_sheet(
        self,
        assets_json: str,
        liabilities_json: str,
        equity_json: str,
        period_end_date: str,
    ) -> str:
        """Analyze balance sheet and calculate financial position metrics.

        @description: Analyze balance sheet to assess financial position, liquidity, solvency, and capital structure. Calculates key ratios including current ratio, quick ratio, debt-to-equity, and return on assets. Provides insights into working capital management and financial stability.

        Args:
            assets_json: JSON string of assets (e.g., '{"current_assets": {"cash": 100000, "accounts_receivable": 200000, "inventory": 150000}, "fixed_assets": {"property_plant_equipment": 500000}}')
            liabilities_json: JSON string of liabilities (e.g., '{"current_liabilities": {"accounts_payable": 150000, "short_term_debt": 50000}, "long_term_liabilities": {"long_term_debt": 300000}}')
            equity_json: JSON string of equity items (e.g., '{"common_stock": 100000, "retained_earnings": 350000}')
            period_end_date: Date of the balance sheet (e.g., '2024-12-31')

        Returns:
            Comprehensive balance sheet analysis with liquidity, solvency, and efficiency metrics
        """
        import json

        try:
            assets = json.loads(assets_json)
            liabilities = json.loads(liabilities_json)
            equity = json.loads(equity_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Analyze balance sheet as of {period_end_date}:
        Assets: {assets}
        Liabilities: {liabilities}
        Equity: {equity}
        
        Calculate:
        1. Total assets, liabilities, and equity (verify accounting equation)
        2. Working capital and net working capital
        3. Liquidity ratios:
           - Current ratio
           - Quick ratio (acid-test)
           - Cash ratio
        4. Solvency ratios:
           - Debt-to-equity ratio
           - Debt-to-assets ratio
           - Interest coverage (if interest expense available)
        5. Asset composition:
           - Current vs non-current assets breakdown
           - Asset turnover metrics
        6. Capital structure analysis
        7. Book value per share (if share count available)
        8. Common-size balance sheet (all items as % of total assets)
        
        Identify any red flags or areas of concern.
        Format all ratios to 2 decimal places and percentages as XX.X%.
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def analyze_cash_flow(
        self,
        operating_activities_json: str,
        investing_activities_json: str,
        financing_activities_json: str,
        beginning_cash: float,
        period: str = "annual",
    ) -> str:
        """Analyze cash flow statement and calculate cash management metrics.

        @description: Analyze cash flow statement to assess cash generation, usage, and management. Evaluates operating cash flow quality, free cash flow, and cash flow adequacy. Provides insights into company's ability to generate cash and fund operations, investments, and distributions.

        Args:
            operating_activities_json: JSON string of operating cash flows (e.g., '{"net_income": 200000, "depreciation": 50000, "working_capital_changes": -30000}')
            investing_activities_json: JSON string of investing cash flows (e.g., '{"capital_expenditures": -100000, "acquisitions": -50000, "asset_sales": 20000}')
            financing_activities_json: JSON string of financing cash flows (e.g., '{"debt_issuance": 100000, "debt_repayment": -50000, "dividends": -40000}')
            beginning_cash: Cash balance at start of period
            period: Time period - 'annual', 'quarterly', or 'monthly'

        Returns:
            Comprehensive cash flow analysis with quality metrics and sustainability assessment
        """
        import json

        try:
            operating = json.loads(operating_activities_json)
            investing = json.loads(investing_activities_json)
            financing = json.loads(financing_activities_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Analyze cash flow statement for {period} period:
        Beginning cash: ${beginning_cash:,.2f}
        Operating activities: {operating}
        Investing activities: {investing}
        Financing activities: {financing}
        
        Calculate and ALWAYS specify time period:
        1. Net cash from each activity category ({period})
        2. Total change in cash and ending cash balance ({period})
        3. Free cash flow (Operating CF - CapEx) ({period})
        4. Cash flow quality metrics:
           - Operating cash flow to net income ratio
           - Cash flow margin (Operating CF / Revenue if available)
           - Cash return on assets ({period} basis)
        5. Cash flow adequacy:
           - Ability to cover CapEx
           - Ability to cover debt service
           - Ability to pay dividends
        6. Cash burn rate (if negative) - specify as {period} rate and calculate monthly/daily equivalents
        7. Days cash on hand (based on {period} burn rate)
        8. Cash conversion cycle components if data available
        
        CRITICAL: For ALL metrics, specify the time period:
        - "Annual Cash Burn Rate: $X" or "Monthly Cash Burn Rate: $X"
        - "Days Cash on Hand (based on monthly burn): X days"
        - Never just "Cash Burn Rate: $X" without time context
        
        Assess sustainability of cash flows and identify any concerns.
        Format all amounts with proper currency formatting and time period labels.
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def calculate_financial_ratios(
        self,
        financial_data_json: str,
        ratio_categories: str = "all",
    ) -> str:
        """Calculate comprehensive financial ratios for analysis.

        @description: Calculate a comprehensive set of financial ratios across multiple categories including profitability, liquidity, efficiency, leverage, and market valuation. Provides ratio interpretation and benchmarking against industry standards where applicable.

        Args:
            financial_data_json: JSON string containing financial statement data (e.g., '{"revenue": 1000000, "net_income": 100000, "total_assets": 2000000, "total_equity": 1000000, "current_assets": 500000, "current_liabilities": 300000, "shares_outstanding": 100000, "stock_price": 25}')
            ratio_categories: Categories to calculate - 'all', 'profitability', 'liquidity', 'efficiency', 'leverage', 'market' (comma-separated for multiple)

        Returns:
            Comprehensive financial ratio analysis with interpretations and insights
        """
        import json

        try:
            financial_data = json.loads(financial_data_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Calculate financial ratios for categories: {ratio_categories}
        Using financial data: {financial_data}
        
        Calculate applicable ratios from:
        
        PROFITABILITY RATIOS:
        - Return on Assets (ROA)
        - Return on Equity (ROE)
        - Return on Invested Capital (ROIC)
        - Gross Profit Margin
        - Operating Profit Margin
        - Net Profit Margin
        - EBITDA Margin
        
        LIQUIDITY RATIOS:
        - Current Ratio
        - Quick Ratio
        - Cash Ratio
        - Operating Cash Flow Ratio
        
        EFFICIENCY RATIOS:
        - Asset Turnover
        - Inventory Turnover
        - Receivables Turnover
        - Days Sales Outstanding (DSO)
        - Days Inventory Outstanding (DIO)
        - Days Payables Outstanding (DPO)
        - Cash Conversion Cycle
        
        LEVERAGE RATIOS:
        - Debt-to-Equity
        - Debt-to-Assets
        - Interest Coverage
        - Debt Service Coverage
        - Financial Leverage
        
        MARKET VALUATION RATIOS:
        - Price-to-Earnings (P/E)
        - Price-to-Book (P/B)
        - Price-to-Sales (P/S)
        - EV/EBITDA
        - Dividend Yield
        - Earnings Per Share (EPS)
        
        For each ratio:
        1. Calculate the value
        2. Provide brief interpretation
        3. Indicate if it's favorable/unfavorable/neutral
        4. Compare to typical industry ranges if known
        
        Format ratios appropriately (X.XX for most, XX.X% for margins).
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def analyze_financial_trends(
        self,
        historical_data_json: str,
        metrics_to_analyze: str,
        periods: int = 5,
    ) -> str:
        """Analyze financial trends over multiple periods.

        @description: Perform trend analysis on financial metrics over multiple periods to identify patterns, growth rates, and potential concerns. CRITICAL: Provide ALL historical data points with time labels (e.g., {"2020": 100, "2021": 120, "2022": 150, "2023": 180, "2024": 220}) not just start/end values. The tool will calculate period-over-period growth, CAGR, and identify acceleration/deceleration patterns. Provides detailed growth analytics and forecasting insights.

        Args:
            historical_data_json: JSON string with ALL available historical financial data points by period. Include every period available, not just start/end (e.g., '{"2019": {"revenue": 800000, "net_income": 80000}, "2020": {"revenue": 900000, "net_income": 95000}, "2021": {"revenue": 1000000, "net_income": 100000}, "2022": {"revenue": 1200000, "net_income": 130000}, "2023": {"revenue": 1500000, "net_income": 170000}}')
            metrics_to_analyze: Comma-separated list of metrics to analyze (e.g., 'revenue,net_income,margins,ratios')
            periods: Number of historical periods to analyze

        Returns:
            Comprehensive trend analysis with growth rates, patterns, and insights
        """
        import json

        try:
            historical_data = json.loads(historical_data_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Analyze financial trends over {periods} periods:
        Historical data: {historical_data}
        Metrics to analyze: {metrics_to_analyze}
        
        Perform:
        1. Calculate year-over-year growth rates for each metric
        2. Calculate CAGR (Compound Annual Growth Rate) for key metrics
        3. Identify trends (increasing, decreasing, volatile, stable)
        4. Calculate trend lines and R-squared values
        5. Analyze margin trends (expanding, contracting, stable)
        6. Identify any concerning patterns or red flags
        7. Calculate volatility/standard deviation of growth rates
        8. Project next period values based on trends (with disclaimer)
        9. Compare growth rates across different metrics
        10. Identify any structural breaks or significant changes
        
        Present results with:
        - Clear visualizations using ASCII charts if possible
        - Growth rates as percentages (XX.X%)
        - Trend strength indicators
        - Key insights and recommendations
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def compare_financial_statements(
        self,
        company_a_json: str,
        company_b_json: str,
        comparison_type: str = "ratio",
    ) -> str:
        """Compare financial statements between two companies or periods.

        @description: Perform comparative analysis between two sets of financial statements, either for competitive analysis or period-over-period comparison. Calculates differences, ratios, and provides insights on relative performance and positioning.

        Args:
            company_a_json: JSON string with first company/period financial data (e.g., '{"name": "Company A", "revenue": 1000000, "net_income": 100000, "total_assets": 2000000}')
            company_b_json: JSON string with second company/period financial data
            comparison_type: Type of comparison - 'ratio', 'variance', 'common_size', or 'all'

        Returns:
            Detailed comparative analysis with insights and recommendations
        """
        import json

        try:
            company_a = json.loads(company_a_json)
            company_b = json.loads(company_b_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Compare financial statements:
        Entity A: {company_a}
        Entity B: {company_b}
        Comparison type: {comparison_type}
        
        Perform comparative analysis:
        1. Size comparison (revenue, assets, market cap if available)
        2. Profitability comparison:
           - Margin analysis
           - Return metrics (ROA, ROE, ROIC)
        3. Efficiency comparison:
           - Asset utilization
           - Working capital management
        4. Financial health comparison:
           - Liquidity positions
           - Leverage metrics
           - Cash flow generation
        5. Growth rate comparison
        6. Calculate relative ratios (A/B for each metric)
        7. Identify competitive advantages/disadvantages
        8. Common-size analysis (as % of revenue or assets)
        9. Performance scoring/ranking
        
        Present results in:
        - Side-by-side format
        - Percentage differences
        - Visual indicators (better/worse)
        - Key takeaways and strategic insights
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def prepare_visualization_data(
        self,
        financial_data_json: str,
        visualization_type: str = "trend",
        time_periods_json: str = None,
    ) -> str:
        """Prepare financial data for visualization in structured format.

        @description: Transform financial data into structured format suitable for visualization. Instead of generating charts, outputs data in a format that clearly shows trends, comparisons, and patterns. Useful for LLMs to understand and describe financial visualizations without actual graphics.

        Args:
            financial_data_json: JSON string with financial data to visualize
            visualization_type: Type of visualization - 'trend', 'comparison', 'composition', 'distribution', 'waterfall'
            time_periods_json: JSON string with time period labels (optional, e.g., '["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023"]')

        Returns:
            Structured data representation suitable for describing visualizations
        """
        import json

        try:
            financial_data = json.loads(financial_data_json)
            time_periods = json.loads(time_periods_json) if time_periods_json else None
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Prepare {visualization_type} visualization data for: {financial_data}
        Time periods: {time_periods if time_periods else "auto-generate based on data"}
        
        Output structured data in the following format:
        
        1. CHART TITLE and DESCRIPTION
        2. DATA POINTS in tabular format with clear labels
        3. KEY INSIGHTS that would be visible in the chart:
           - Trends (increasing/decreasing/stable)
           - Notable peaks and troughs
           - Percentage changes between periods
           - Outliers or anomalies
        4. TEXTUAL REPRESENTATION using ASCII or symbols:
           - Use ▲ for increases, ▼ for decreases, ─ for stable
           - Show relative magnitudes with bar representations: ████████
           - Include sparkline-style trend: ▁▂▄█▇▅▃▁
        5. SUMMARY STATISTICS:
           - Min, Max, Average, Median
           - Growth rate (CAGR if applicable)
           - Volatility/Standard deviation
        
        For {visualization_type} specifically:
        - trend: Show time series progression with growth rates
        - comparison: Side-by-side metrics with relative differences
        - composition: Breakdown of components with percentages
        - distribution: Frequency/range analysis with quartiles
        - waterfall: Starting value → changes → ending value
        
        Format numbers appropriately and include all temporal context.
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def create_financial_dashboard_data(
        self,
        company_data_json: str,
        dashboard_type: str = "executive",
        period: str = "quarterly",
    ) -> str:
        """Create structured data for financial dashboard representation.

        @description: Generate structured dashboard-style data output that LLMs can use to describe comprehensive financial performance. Organizes key metrics, trends, and insights in a dashboard-like format without actual visualization.

        Args:
            company_data_json: JSON string with comprehensive company financial data
            dashboard_type: Type of dashboard - 'executive', 'operational', 'investor', 'credit'
            period: Time period for the dashboard - 'monthly', 'quarterly', 'annual'

        Returns:
            Structured dashboard data with KPIs, trends, and insights
        """
        import json

        try:
            company_data = json.loads(company_data_json)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Create {dashboard_type} financial dashboard data for {period} period:
        Company data: {company_data}
        
        Structure the output as a text-based dashboard:
        
        ╔════════════════════════════════════════════════════════════╗
        ║                    FINANCIAL DASHBOARD                      ║
        ╠════════════════════════════════════════════════════════════╣
        
        📊 KEY PERFORMANCE INDICATORS ({period})
        ├─────────────────────────────────────────────────────────────
        │ Metric              │ Current │ Previous │ Change │ Status │
        ├─────────────────────────────────────────────────────────────
        │ Revenue             │ $X.XM   │ $X.XM    │ +X.X%  │   ▲    │
        │ Net Income          │ $X.XM   │ $X.XM    │ +X.X%  │   ▲    │
        │ Gross Margin        │ XX.X%   │ XX.X%    │ +X.Xpp │   ▲    │
        └─────────────────────────────────────────────────────────────
        
        📈 TREND INDICATORS (Last 4 {period}s)
        Revenue:    ▁▃▅█ (+X.X% CAGR)
        Profit:     ▂▄▆█ (+X.X% CAGR)
        Cash Flow:  ▃▁▄█ (+X.X% avg)
        
        💰 FINANCIAL HEALTH SCORES
        Liquidity:    ████████░░ (80% - Strong)
        Profitability:████████░░ (85% - Excellent)
        Efficiency:   ██████░░░░ (65% - Good)
        Leverage:     ███████░░░ (70% - Moderate)
        
        ⚠️ ALERTS & INSIGHTS
        • Top Finding: [Key insight about performance]
        • Risk Alert: [Any concerning metrics]
        • Opportunity: [Potential improvement areas]
        
        For {dashboard_type} dashboard, focus on:
        - executive: High-level KPIs, strategic metrics
        - operational: Efficiency ratios, working capital, cash conversion
        - investor: Returns, growth, valuation multiples
        - credit: Liquidity, leverage, coverage ratios
        """
        return await self.calculate_financial_metrics(request)

    @ToolCallable.tool
    async def generate_performance_scorecard(
        self,
        actual_data_json: str,
        target_data_json: str,
        metrics_weights_json: str = None,
    ) -> str:
        """Generate performance scorecard comparing actuals to targets.

        @description: Create a structured performance scorecard that compares actual financial results against targets/budgets. Calculates variances, achievement rates, and weighted performance scores. Ideal for LLMs to assess and describe financial performance.

        Args:
            actual_data_json: JSON string with actual financial results
            target_data_json: JSON string with target/budget values
            metrics_weights_json: Optional JSON string with importance weights for each metric

        Returns:
            Structured scorecard with performance ratings and variance analysis
        """
        import json

        try:
            actual_data = json.loads(actual_data_json)
            target_data = json.loads(target_data_json)
            weights = json.loads(metrics_weights_json) if metrics_weights_json else {}
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"

        request = f"""
        Generate performance scorecard:
        Actual results: {actual_data}
        Target values: {target_data}
        Metric weights: {weights if weights else "equal weights"}
        
        Create structured scorecard output:
        
        ═══════════════════════════════════════════════════════════════
                          PERFORMANCE SCORECARD
        ═══════════════════════════════════════════════════════════════
        
        📋 PERFORMANCE SUMMARY
        Overall Score: XX.X% (Letter Grade: A/B/C/D/F)
        Performance Status: ⭐⭐⭐⭐☆ (4/5 stars)
        
        📊 DETAILED METRICS ANALYSIS
        ┌─────────────────────────────────────────────────────────────┐
        │ Metric          │ Actual │ Target │ Variance │ Achieve% │ Grade │
        ├─────────────────────────────────────────────────────────────┤
        │ Revenue         │ $X.XM  │ $X.XM  │ +$X.XK   │ 105%     │  A+   │
        │ Expenses        │ $X.XM  │ $X.XM  │ -$X.XK   │ 98%      │  A    │
        │ Net Margin      │ XX.X%  │ XX.X%  │ +X.Xpp   │ 110%     │  A+   │
        └─────────────────────────────────────────────────────────────┘
        
        🎯 ACHIEVEMENT VISUALIZATION
        Revenue:     ████████████░ 105% ✓ (Exceeded)
        Costs:       ████████░░░░  80% ⚠ (Below target)
        Profit:      ██████████░░  95% ≈ (Near target)
        
        📈 VARIANCE ANALYSIS
        • Favorable variances: [List positive variances]
        • Unfavorable variances: [List negative variances]
        • Key drivers: [Explain main factors]
        
        💡 PERFORMANCE INSIGHTS
        1. Strengths: [Top performing areas]
        2. Weaknesses: [Underperforming areas]
        3. Action items: [Recommendations for improvement]
        
        Calculate:
        - Percentage achievement for each metric
        - Weighted performance score if weights provided
        - Letter grades (A+ ≥110%, A ≥100%, B ≥90%, C ≥80%, D ≥70%, F <70%)
        - Variance analysis (favorable/unfavorable)
        """
        return await self.calculate_financial_metrics(request)
