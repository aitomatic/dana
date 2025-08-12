"""
Financial Statement Analyzer Resource
A clean, modular resource for financial statement analysis with LLM-friendly interfaces.
Focuses on pre-built calculations and safe execution without dynamic code generation.
"""

import logging
from typing import Any

import numpy as np

from dana.common.mixins.tool_callable import ToolCallable
from dana.common.sys_resource.base_sys_resource import BaseSysResource

logger = logging.getLogger(__name__)


class FinancialStatementAnalyzer(BaseSysResource):
    """Financial statement analysis resource with pre-built calculations and safe execution."""

    def __init__(
        self,
        name: str = "financial_statement_analyzer",
        description: str | None = None,
        debug: bool = True,
        **kwargs,
    ):
        super().__init__(
            name,
            description or "Financial statement analysis with pre-built calculations",
        )
        self.debug = debug
        self._calculator = FinancialCalculations()
        self._parser = DataParser()
        self._formatter = OutputFormatter()

    async def initialize(self) -> None:
        """Initialize the financial analyzer resource."""
        await super().initialize()
        if self.debug:
            logger.info(f"Financial statement analyzer [{self.name}] initialized")

    @ToolCallable.tool
    async def analyze_income_statement(self, revenue: str, expenses: str, period: str = "annual") -> str:
        """Analyze income statement and calculate profitability metrics.

        @description: Analyzes income statement data to calculate gross profit, operating profit, net profit, and various profitability margins. Accepts either single values or comma-separated breakdowns. For time series, use format "Q1:250000,Q2:275000,Q3:300000,Q4:325000". For expense categories, use format "COGS:600000,OpEx:150000,Interest:50000". Returns profitability metrics, margins, and growth analysis with proper time period context.

        Args:
            revenue: Revenue data as single value "1000000" or time series "Q1:250000,Q2:275000,Q3:300000,Q4:325000"
            expenses: Expense data as single value "800000" or breakdown "COGS:600000,OpEx:150000,Interest:50000,Tax:50000"
            period: Time period - "annual", "quarterly", or "monthly"

        Returns:
            Formatted analysis with profitability metrics, margins, and insights
        """
        try:
            # Parse input data
            revenue_data = self._parser.parse_financial_data(revenue, "revenue")
            expense_data = self._parser.parse_financial_data(expenses, "expenses")

            if self.debug:
                print("\n[DEBUG] Income Statement Analysis")
                print(f"  Revenue data: {revenue_data}")
                print(f"  Expense data: {expense_data}")
                print(f"  Period: {period}")

            # Perform calculations
            results = self._calculator.analyze_income_statement(revenue_data, expense_data, period)

            if self.debug:
                print("\n[DEBUG] Calculation Results:")
                print(f"  Total Revenue: ${results.get('total_revenue', 0):,.0f}")
                print(f"  Gross Margin: {results.get('gross_margin', 0):.1f}%")
                print(f"  Net Margin: {results.get('net_margin', 0):.1f}%")
                if "period_growth_rates" in results:
                    print(f"  Growth Analysis: {results.get('period_growth_rates')}")

            # Format output
            formatted_output = self._formatter.format_income_statement_analysis(results, period)

            if self.debug:
                print(f"\n[DEBUG] Formatted Output Length: {len(formatted_output)} chars")

            return formatted_output

        except Exception as e:
            logger.error(f"Error analyzing income statement: {e}")
            return f"Error: Failed to analyze income statement - {str(e)}"

    @ToolCallable.tool
    async def calculate_financial_ratios(self, metrics: str, ratio_type: str = "all") -> str:
        """Calculate financial ratios from provided metrics.

        @description: Calculates standard financial ratios including liquidity ratios (current, quick, cash), profitability ratios (ROA, ROE, margins), leverage ratios (debt-to-equity, interest coverage), and efficiency ratios (asset turnover, inventory turnover). Input metrics as comma-separated key:value pairs. Example: "current_assets:500000,current_liabilities:300000,total_assets:2000000,total_equity:1000000,net_income:100000,revenue:1500000". Returns calculated ratios with interpretations and industry benchmarks where applicable.

        Args:
            metrics: Financial metrics as key:value pairs (e.g., "current_assets:500000,current_liabilities:300000,revenue:1000000")
            ratio_type: Type of ratios to calculate - "liquidity", "profitability", "leverage", "efficiency", or "all"

        Returns:
            Calculated ratios with interpretations and assessment
        """
        try:
            # Parse metrics
            metrics_dict = self._parser.parse_metrics(metrics)

            if self.debug:
                print("\n[DEBUG] Financial Ratio Calculation")
                print(f"  Parsed metrics: {metrics_dict}")
                print(f"  Ratio type: {ratio_type}")

            # Calculate ratios based on type
            if ratio_type == "all":
                results = {}
                results.update(self._calculator.calculate_liquidity_ratios(metrics_dict))
                results.update(self._calculator.calculate_profitability_ratios(metrics_dict))
                results.update(self._calculator.calculate_leverage_ratios(metrics_dict))
                results.update(self._calculator.calculate_efficiency_ratios(metrics_dict))
            elif ratio_type == "liquidity":
                results = self._calculator.calculate_liquidity_ratios(metrics_dict)
            elif ratio_type == "profitability":
                results = self._calculator.calculate_profitability_ratios(metrics_dict)
            elif ratio_type == "leverage":
                results = self._calculator.calculate_leverage_ratios(metrics_dict)
            elif ratio_type == "efficiency":
                results = self._calculator.calculate_efficiency_ratios(metrics_dict)
            else:
                return f"Error: Unknown ratio type '{ratio_type}'. Use: liquidity, profitability, leverage, efficiency, or all"

            if self.debug:
                print("\n[DEBUG] Calculated Ratios:")
                for key, value in results.items():
                    if isinstance(value, dict) and "value" in value:
                        print(f"  {key}: {value['value']:.2f} - {value.get('interpretation', 'N/A')}")

            # Format output
            formatted_output = self._formatter.format_ratio_analysis(results, ratio_type)

            if self.debug:
                print(f"\n[DEBUG] Formatted Output Length: {len(formatted_output)} chars")

            return formatted_output

        except Exception as e:
            logger.error(f"Error calculating ratios: {e}")
            return f"Error: Failed to calculate ratios - {str(e)}"

    @ToolCallable.tool
    async def analyze_cash_flow(
        self, operating_cf: str, investing_cf: str, financing_cf: str, beginning_cash: str = "0", period: str = "annual"
    ) -> str:
        """Analyze cash flow statement and calculate key metrics.

        @description: Analyzes cash flow components to assess cash generation, usage, and sustainability. Calculates free cash flow, burn rate (with time period), cash runway, and quality of earnings. Accepts single values or detailed breakdowns. For breakdowns use format "NetIncome:200000,Depreciation:50000,WorkingCapital:-30000". Always returns metrics with proper time period context (e.g., "Monthly Burn Rate" not just "Burn Rate").

        Args:
            operating_cf: Operating cash flow as single value "250000" or breakdown "NetIncome:200000,Depreciation:50000,WorkingCapital:-30000"
            investing_cf: Investing cash flow as single value "-100000" or breakdown "CapEx:-80000,Acquisitions:-20000,AssetSales:10000"
            financing_cf: Financing cash flow as single value "-50000" or breakdown "DebtIssuance:100000,DebtRepayment:-80000,Dividends:-70000"
            beginning_cash: Beginning cash balance (default "0")
            period: Time period - "annual", "quarterly", or "monthly"

        Returns:
            Cash flow analysis with FCF, burn rate, runway, and sustainability assessment
        """
        try:
            # Parse input data
            operating_data = self._parser.parse_financial_data(operating_cf, "operating_cf")
            investing_data = self._parser.parse_financial_data(investing_cf, "investing_cf")
            financing_data = self._parser.parse_financial_data(financing_cf, "financing_cf")
            begin_cash = float(beginning_cash)

            if self.debug:
                print("\n[DEBUG] Cash Flow Analysis")
                print(f"  Operating CF data: {operating_data}")
                print(f"  Investing CF data: {investing_data}")
                print(f"  Financing CF data: {financing_data}")
                print(f"  Beginning cash: ${begin_cash:,.0f}")
                print(f"  Period: {period}")

            # Perform calculations
            results = self._calculator.analyze_cash_flow(operating_data, investing_data, financing_data, begin_cash, period)

            if self.debug:
                print("\n[DEBUG] Cash Flow Results:")
                print(f"  Operating CF: ${results.get('operating_cash_flow', 0):,.0f}")
                print(f"  Free Cash Flow: ${results.get('free_cash_flow', 0):,.0f}")
                if "burn_rate" in results:
                    burn_data = results["burn_rate"]
                    print(f"  Burn Rate ({period}): ${burn_data.get(f'{period}_burn', 0):,.0f}")
                    print(f"  Cash Runway: {results.get('cash_runway_months', 0):.1f} months")

            # Format output
            formatted_output = self._formatter.format_cash_flow_analysis(results, period)

            if self.debug:
                print(f"\n[DEBUG] Formatted Output Length: {len(formatted_output)} chars")

            return formatted_output

        except Exception as e:
            logger.error(f"Error analyzing cash flow: {e}")
            return f"Error: Failed to analyze cash flow - {str(e)}"

    @ToolCallable.tool
    async def analyze_balance_sheet(self, assets: str, liabilities: str, equity: str, period_end: str = "2024-12-31") -> str:
        """Analyze balance sheet and calculate financial position metrics.

        @description: Analyzes balance sheet to assess financial position, liquidity, and solvency. Calculates working capital, debt ratios, and asset composition. Input categories as comma-separated pairs. For assets use: "cash:100000,receivables:200000,inventory:150000,ppe:500000". For liabilities: "payables:150000,short_term_debt:50000,long_term_debt:300000". Returns comprehensive position analysis with health indicators.

        Args:
            assets: Asset breakdown as "cash:100000,receivables:200000,inventory:150000,ppe:500000,intangibles:50000"
            liabilities: Liability breakdown as "payables:150000,short_term_debt:50000,long_term_debt:300000"
            equity: Equity breakdown as "common_stock:100000,retained_earnings:350000,apic:50000"
            period_end: Balance sheet date (e.g., "2024-12-31")

        Returns:
            Balance sheet analysis with liquidity, solvency, and structure metrics
        """
        try:
            # Parse input data
            asset_data = self._parser.parse_financial_data(assets, "assets")
            liability_data = self._parser.parse_financial_data(liabilities, "liabilities")
            equity_data = self._parser.parse_financial_data(equity, "equity")

            if self.debug:
                print("\n[DEBUG] Balance Sheet Analysis")
                print(f"  Asset data: {asset_data}")
                print(f"  Liability data: {liability_data}")
                print(f"  Equity data: {equity_data}")
                print(f"  Period end: {period_end}")

            # Perform calculations
            results = self._calculator.analyze_balance_sheet(asset_data, liability_data, equity_data, period_end)

            if self.debug:
                print("\n[DEBUG] Balance Sheet Results:")
                print(f"  Total Assets: ${sum(asset_data.values()):,.0f}")
                print(f"  Total Liabilities: ${sum(liability_data.values()):,.0f}")
                print(f"  Total Equity: ${sum(equity_data.values()):,.0f}")
                print(f"  Current Ratio: {results.get('current_ratio', 0):.2f}")
                print(f"  Debt-to-Equity: {results.get('debt_to_equity', 0):.2f}")
                print(f"  Working Capital: ${results.get('working_capital', 0):,.0f}")

            # Format output
            formatted_output = self._formatter.format_balance_sheet_analysis(results, period_end)

            if self.debug:
                print(f"\n[DEBUG] Formatted Output Length: {len(formatted_output)} chars")

            return formatted_output

        except Exception as e:
            logger.error(f"Error analyzing balance sheet: {e}")
            return f"Error: Failed to analyze balance sheet - {str(e)}"

    @ToolCallable.tool
    async def analyze_growth_trends(self, metric_data: str, metric_name: str = "Revenue") -> str:
        """Analyze growth trends for financial metrics over time.

        @description: Performs growth analysis on time-series financial data. CRITICAL: Provide ALL data points with time labels (e.g., "Q1_2023:100000,Q2_2023:110000,Q3_2023:125000,Q4_2023:140000,Q1_2024:150000") not just start/end values. Calculates period-over-period growth, CAGR, trend analysis, and growth acceleration/deceleration patterns. Identifies seasonality and provides forward projections.

        Args:
            metric_data: Time series data as "Q1_2023:100000,Q2_2023:110000,Q3_2023:125000,Q4_2023:140000"
            metric_name: Name of the metric being analyzed (e.g., "Revenue", "Net Income", "Free Cash Flow")

        Returns:
            Comprehensive growth analysis with rates, trends, and projections
        """
        try:
            # Parse time series data
            time_series = self._parser.parse_time_series(metric_data)

            if self.debug:
                print("\n[DEBUG] Growth Trend Analysis")
                print(f"  Metric: {metric_name}")
                print(f"  Time series data: {time_series}")
                print(f"  Number of periods: {len(time_series)}")

            # Perform growth analysis
            results = self._calculator.analyze_growth_trends(time_series, metric_name)

            if self.debug:
                print("\n[DEBUG] Growth Analysis Results:")
                if "cagr" in results:
                    print(f"  CAGR: {results['cagr']:.1f}%")
                if "average_growth" in results:
                    print(f"  Average Growth: {results['average_growth']:.1f}%")
                    print(f"  Growth Trend: {results.get('growth_trend', 'N/A')}")
                if "projection" in results:
                    proj = results["projection"]
                    print(f"  Next Period Projection: ${proj['next_period_value']:,.0f} ({proj['projected_growth']:.1f}% growth)")

            # Format output
            formatted_output = self._formatter.format_growth_analysis(results, metric_name)

            if self.debug:
                print(f"\n[DEBUG] Formatted Output Length: {len(formatted_output)} chars")

            return formatted_output

        except Exception as e:
            logger.error(f"Error analyzing growth trends: {e}")
            return f"Error: Failed to analyze growth trends - {str(e)}"

    @ToolCallable.tool
    async def compare_financial_statements(self, company_a_data: str, company_b_data: str, comparison_type: str = "ratio") -> str:
        """Compare financial metrics between two companies or periods.

        @description: Performs comparative analysis between two sets of financial data. Useful for competitive analysis or period-over-period comparison. Input format: "revenue:1000000,net_income:100000,total_assets:2000000,total_equity:1000000". Calculates relative ratios, performance differences, and provides competitive positioning insights.

        Args:
            company_a_data: First company/period data as "revenue:1000000,net_income:100000,assets:2000000"
            company_b_data: Second company/period data in same format
            comparison_type: Type of comparison - "ratio", "variance", "common_size", or "all"

        Returns:
            Detailed comparative analysis with insights and relative performance metrics
        """
        try:
            # Parse input data
            data_a = self._parser.parse_metrics(company_a_data)
            data_b = self._parser.parse_metrics(company_b_data)

            if self.debug:
                print("\n[DEBUG] Financial Comparison")
                print(f"  Company A data: {data_a}")
                print(f"  Company B data: {data_b}")
                print(f"  Comparison type: {comparison_type}")

            # Perform comparison
            results = self._calculator.compare_financials(data_a, data_b, comparison_type)

            if self.debug:
                print("\n[DEBUG] Comparison Results:")
                if "performance_summary" in results:
                    print(f"  Performance Summary: {results['performance_summary']}")
                if "differences" in results and len(results["differences"]) > 0:
                    print("  Key Differences:")
                    for metric, diff in list(results["differences"].items())[:3]:  # Show top 3
                        print(f"    {metric}: {diff['percentage']:.1f}% difference")

            # Format output
            formatted_output = self._formatter.format_comparison_analysis(results, comparison_type)

            if self.debug:
                print(f"\n[DEBUG] Formatted Output Length: {len(formatted_output)} chars")

            return formatted_output

        except Exception as e:
            logger.error(f"Error comparing financials: {e}")
            return f"Error: Failed to compare financials - {str(e)}"

    async def cleanup(self) -> None:
        """Clean up the financial analyzer resource."""
        await super().cleanup()
        if self.debug:
            logger.info(f"Financial statement analyzer [{self.name}] cleaned up")

    async def query(self, request: str) -> None:
        """Query the financial analyzer resource."""
        pass


class DataParser:
    """Parse string inputs into structured financial data."""

    def parse_financial_data(self, data_str: str, data_type: str) -> dict[str, float]:
        """Parse financial data from string format."""
        if not data_str:
            raise ValueError(f"Empty {data_type} data provided")

        result = {}

        # Check if it's a single value
        if ":" not in data_str and "," not in data_str:
            try:
                # Single value case
                result[data_type] = float(data_str)
                return result
            except ValueError:
                raise ValueError(f"Invalid {data_type} format: {data_str}")

        # Parse key:value pairs
        pairs = data_str.split(",")
        for pair in pairs:
            if ":" not in pair:
                raise ValueError(f"Invalid format in {data_type}: {pair}. Expected 'key:value'")

            key, value = pair.split(":", 1)
            key = key.strip()
            try:
                result[key] = float(value.strip())
            except ValueError:
                raise ValueError(f"Invalid number in {data_type}: {value}")

        return result

    def parse_metrics(self, metrics_str: str) -> dict[str, float]:
        """Parse metrics from key:value string format."""
        return self.parse_financial_data(metrics_str, "metrics")

    def parse_time_series(self, series_str: str) -> list[tuple[str, float]]:
        """Parse time series data maintaining order."""
        if not series_str:
            raise ValueError("Empty time series data")

        result = []
        pairs = series_str.split(",")

        for pair in pairs:
            if ":" not in pair:
                raise ValueError(f"Invalid time series format: {pair}")

            period, value = pair.split(":", 1)
            period = period.strip()
            try:
                value = float(value.strip())
                result.append((period, value))
            except ValueError:
                raise ValueError(f"Invalid value in time series: {value}")

        return result


class FinancialCalculations:
    """Pre-built financial calculations and analysis functions."""

    def analyze_income_statement(self, revenue_data: dict[str, float], expense_data: dict[str, float], period: str) -> dict[str, Any]:
        """Analyze income statement and calculate profitability metrics."""
        results = {}

        # Calculate totals
        total_revenue = sum(revenue_data.values())
        total_expenses = sum(expense_data.values())

        # Handle time series data
        if len(revenue_data) > 1 and all("Q" in k or "M" in k for k in revenue_data.keys()):
            # Time series analysis
            periods = sorted(revenue_data.keys())
            revenues = [revenue_data[p] for p in periods]

            # Growth analysis
            growth_rates = []
            for i in range(1, len(revenues)):
                growth = ((revenues[i] - revenues[i - 1]) / revenues[i - 1]) * 100
                growth_rates.append(growth)

            results["period_growth_rates"] = {f"{periods[i]}→{periods[i + 1]}": rate for i, rate in enumerate(growth_rates)}
            results["average_growth"] = np.mean(growth_rates) if growth_rates else 0
            results["growth_trend"] = self._analyze_trend(growth_rates)

        # Calculate margins
        cogs = expense_data.get("COGS", expense_data.get("cogs", 0))
        gross_profit = total_revenue - cogs

        operating_expenses = sum(v for k, v in expense_data.items() if k.lower() not in ["cogs", "interest", "tax", "taxes"])
        operating_income = gross_profit - operating_expenses

        interest = expense_data.get("Interest", expense_data.get("interest", 0))
        ebt = operating_income - interest

        taxes = expense_data.get("Tax", expense_data.get("taxes", 0))
        net_income = ebt - taxes

        # Profitability metrics
        results.update(
            {
                "total_revenue": total_revenue,
                "gross_profit": gross_profit,
                "operating_income": operating_income,
                "net_income": net_income,
                "gross_margin": (gross_profit / total_revenue * 100) if total_revenue > 0 else 0,
                "operating_margin": (operating_income / total_revenue * 100) if total_revenue > 0 else 0,
                "net_margin": (net_income / total_revenue * 100) if total_revenue > 0 else 0,
                "expense_ratio": (total_expenses / total_revenue * 100) if total_revenue > 0 else 0,
            }
        )

        # EBITDA if depreciation available
        depreciation = expense_data.get("Depreciation", expense_data.get("depreciation", 0))
        amortization = expense_data.get("Amortization", expense_data.get("amortization", 0))
        if depreciation or amortization:
            ebitda = operating_income + depreciation + amortization
            results["ebitda"] = ebitda
            results["ebitda_margin"] = (ebitda / total_revenue * 100) if total_revenue > 0 else 0

        # Quality assessment
        results["profitability_assessment"] = self._assess_profitability(results)

        return results

    def calculate_liquidity_ratios(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Calculate liquidity ratios."""
        ratios = {}

        current_assets = metrics.get("current_assets", 0)
        current_liabilities = metrics.get("current_liabilities", 0)
        cash = metrics.get("cash", 0)
        inventory = metrics.get("inventory", 0)

        if current_liabilities > 0:
            ratios["current_ratio"] = {
                "value": current_assets / current_liabilities,
                "interpretation": self._interpret_current_ratio(current_assets / current_liabilities),
            }

            quick_assets = current_assets - inventory
            ratios["quick_ratio"] = {
                "value": quick_assets / current_liabilities,
                "interpretation": self._interpret_quick_ratio(quick_assets / current_liabilities),
            }

            ratios["cash_ratio"] = {
                "value": cash / current_liabilities,
                "interpretation": self._interpret_cash_ratio(cash / current_liabilities),
            }

        # Working capital
        ratios["working_capital"] = {
            "value": current_assets - current_liabilities,
            "interpretation": "Positive" if current_assets > current_liabilities else "Negative",
        }

        return ratios

    def calculate_profitability_ratios(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Calculate profitability ratios."""
        ratios = {}

        revenue = metrics.get("revenue", 0)
        net_income = metrics.get("net_income", 0)
        total_assets = metrics.get("total_assets", 0)
        total_equity = metrics.get("total_equity", 0)

        if revenue > 0:
            ratios["net_margin"] = {
                "value": (net_income / revenue) * 100,
                "interpretation": self._interpret_margin((net_income / revenue) * 100),
            }

        if total_assets > 0:
            roa = (net_income / total_assets) * 100
            ratios["return_on_assets"] = {"value": roa, "interpretation": self._interpret_roa(roa)}

        if total_equity > 0:
            roe = (net_income / total_equity) * 100
            ratios["return_on_equity"] = {"value": roe, "interpretation": self._interpret_roe(roe)}

        return ratios

    def calculate_leverage_ratios(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Calculate leverage/solvency ratios."""
        ratios = {}

        total_debt = metrics.get("total_debt", 0)
        total_equity = metrics.get("total_equity", 0)
        total_assets = metrics.get("total_assets", 0)
        ebit = metrics.get("ebit", metrics.get("operating_income", 0))
        interest = metrics.get("interest_expense", 0)

        if total_equity > 0:
            debt_to_equity = total_debt / total_equity
            ratios["debt_to_equity"] = {"value": debt_to_equity, "interpretation": self._interpret_debt_to_equity(debt_to_equity)}

        if total_assets > 0:
            debt_to_assets = total_debt / total_assets
            ratios["debt_to_assets"] = {"value": debt_to_assets, "interpretation": self._interpret_debt_to_assets(debt_to_assets)}

        if interest > 0 and ebit > 0:
            interest_coverage = ebit / interest
            ratios["interest_coverage"] = {
                "value": interest_coverage,
                "interpretation": self._interpret_interest_coverage(interest_coverage),
            }

        return ratios

    def calculate_efficiency_ratios(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Calculate efficiency/activity ratios."""
        ratios = {}

        revenue = metrics.get("revenue", 0)
        total_assets = metrics.get("total_assets", 0)
        inventory = metrics.get("inventory", 0)
        cogs = metrics.get("cogs", metrics.get("cost_of_goods_sold", 0))
        receivables = metrics.get("accounts_receivable", 0)

        if total_assets > 0 and revenue > 0:
            asset_turnover = revenue / total_assets
            ratios["asset_turnover"] = {"value": asset_turnover, "interpretation": self._interpret_asset_turnover(asset_turnover)}

        if inventory > 0 and cogs > 0:
            inventory_turnover = cogs / inventory
            ratios["inventory_turnover"] = {
                "value": inventory_turnover,
                "days": 365 / inventory_turnover,
                "interpretation": self._interpret_inventory_turnover(inventory_turnover),
            }

        if receivables > 0 and revenue > 0:
            receivables_turnover = revenue / receivables
            ratios["receivables_turnover"] = {
                "value": receivables_turnover,
                "days": 365 / receivables_turnover,
                "interpretation": self._interpret_receivables_turnover(receivables_turnover),
            }

        return ratios

    def analyze_cash_flow(
        self,
        operating_data: dict[str, float],
        investing_data: dict[str, float],
        financing_data: dict[str, float],
        beginning_cash: float,
        period: str,
    ) -> dict[str, Any]:
        """Analyze cash flow statement."""
        results = {}

        # Calculate totals
        operating_cf = sum(operating_data.values())
        investing_cf = sum(investing_data.values())
        financing_cf = sum(financing_data.values())

        total_cf_change = operating_cf + investing_cf + financing_cf
        ending_cash = beginning_cash + total_cf_change

        # Extract key components
        capex = investing_data.get("CapEx", investing_data.get("capital_expenditures", 0))
        if capex > 0:
            capex = -capex  # Ensure CapEx is negative

        # Free cash flow
        free_cash_flow = operating_cf + capex

        results.update(
            {
                "operating_cash_flow": operating_cf,
                "investing_cash_flow": investing_cf,
                "financing_cash_flow": financing_cf,
                "total_change_in_cash": total_cf_change,
                "beginning_cash": beginning_cash,
                "ending_cash": ending_cash,
                "free_cash_flow": free_cash_flow,
                "capex": capex,
            }
        )

        # Cash burn analysis if negative
        if operating_cf < 0:
            # Calculate burn rate based on period
            if period == "annual":
                monthly_burn = operating_cf / 12
                daily_burn = operating_cf / 365
            elif period == "quarterly":
                monthly_burn = operating_cf / 3
                daily_burn = operating_cf / 90
            else:  # monthly
                monthly_burn = operating_cf
                daily_burn = operating_cf / 30

            results["burn_rate"] = {f"{period}_burn": operating_cf, "monthly_burn": monthly_burn, "daily_burn": daily_burn}

            # Cash runway
            if monthly_burn < 0:
                months_runway = ending_cash / abs(monthly_burn)
                results["cash_runway_months"] = months_runway
                results["cash_runway_days"] = months_runway * 30

        # Quality metrics
        net_income = operating_data.get("NetIncome", operating_data.get("net_income", 0))
        if net_income != 0:
            results["cash_flow_quality_ratio"] = operating_cf / net_income

        # Cash flow adequacy
        dividends = financing_data.get("Dividends", financing_data.get("dividends", 0))
        debt_repayment = financing_data.get("DebtRepayment", financing_data.get("debt_repayment", 0))

        required_cash = abs(capex) + abs(dividends) + abs(debt_repayment)
        if required_cash > 0:
            results["cash_flow_adequacy"] = operating_cf / required_cash

        # Assessment
        results["cash_flow_assessment"] = self._assess_cash_flow(results)

        return results

    def analyze_balance_sheet(
        self, asset_data: dict[str, float], liability_data: dict[str, float], equity_data: dict[str, float], period_end: str
    ) -> dict[str, Any]:
        """Analyze balance sheet structure and health."""
        results = {"period_end": period_end}

        # Calculate totals
        total_assets = sum(asset_data.values())
        total_liabilities = sum(liability_data.values())
        total_equity = sum(equity_data.values())

        # Verify accounting equation
        equation_check = abs(total_assets - (total_liabilities + total_equity))
        results["accounting_equation_balanced"] = equation_check < 1.0

        # Current vs non-current breakdown
        current_asset_keys = ["cash", "receivables", "inventory", "current_assets"]
        current_assets = sum(v for k, v in asset_data.items() if any(ca in k.lower() for ca in current_asset_keys))

        current_liability_keys = ["payables", "short_term", "current_liabilities"]
        current_liabilities = sum(v for k, v in liability_data.items() if any(cl in k.lower() for cl in current_liability_keys))

        # Asset composition
        results["asset_composition"] = {
            "total_assets": total_assets,
            "current_assets": current_assets,
            "non_current_assets": total_assets - current_assets,
            "current_asset_ratio": (current_assets / total_assets * 100) if total_assets > 0 else 0,
        }

        # Capital structure
        results["capital_structure"] = {
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "debt_ratio": (total_liabilities / total_assets * 100) if total_assets > 0 else 0,
            "equity_ratio": (total_equity / total_assets * 100) if total_assets > 0 else 0,
        }

        # Working capital
        results["working_capital"] = current_assets - current_liabilities
        results["working_capital_ratio"] = current_assets / current_liabilities if current_liabilities > 0 else 0

        # Key balance sheet ratios
        if current_liabilities > 0:
            results["current_ratio"] = current_assets / current_liabilities

            # Quick ratio
            inventory = asset_data.get("inventory", 0)
            quick_assets = current_assets - inventory
            results["quick_ratio"] = quick_assets / current_liabilities

        # Debt ratios
        long_term_debt = sum(v for k, v in liability_data.items() if "long_term" in k.lower() or "debt" in k.lower())

        if total_equity > 0:
            results["debt_to_equity"] = total_liabilities / total_equity
            results["long_term_debt_to_equity"] = long_term_debt / total_equity

        # Financial health assessment
        results["financial_health_assessment"] = self._assess_financial_health(results)

        return results

    def analyze_growth_trends(self, time_series: list[tuple[str, float]], metric_name: str) -> dict[str, Any]:
        """Analyze growth trends in time series data."""
        results = {"metric_name": metric_name}

        if len(time_series) < 2:
            return {"error": "Need at least 2 data points for trend analysis"}

        periods = [p[0] for p in time_series]
        values = [p[1] for p in time_series]

        # Period-over-period growth
        growth_rates = []
        for i in range(1, len(values)):
            if values[i - 1] != 0:
                growth = ((values[i] - values[i - 1]) / abs(values[i - 1])) * 100
                growth_rates.append({"period": f"{periods[i - 1]}→{periods[i]}", "growth_rate": growth})

        results["period_growth_rates"] = growth_rates

        # CAGR calculation
        if len(values) > 1 and values[0] > 0 and values[-1] > 0:
            years = len(values) - 1
            cagr = (((values[-1] / values[0]) ** (1 / years)) - 1) * 100
            results["cagr"] = cagr

        # Statistical analysis
        results["statistics"] = {
            "mean": np.mean(values),
            "median": np.median(values),
            "std_dev": np.std(values),
            "cv": (np.std(values) / np.mean(values) * 100) if np.mean(values) != 0 else 0,
        }

        # Trend analysis
        growth_values = [g["growth_rate"] for g in growth_rates]
        if growth_values:
            results["average_growth"] = np.mean(growth_values)
            results["growth_volatility"] = np.std(growth_values)
            results["growth_trend"] = self._analyze_trend(growth_values)

        # Simple linear projection
        if len(values) >= 3:
            # Use numpy polyfit for linear regression
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)

            # Project next period
            next_value = slope * len(values) + intercept
            results["projection"] = {
                "next_period_value": next_value,
                "projected_growth": ((next_value - values[-1]) / values[-1] * 100) if values[-1] != 0 else 0,
                "trend_slope": slope,
            }

        return results

    def compare_financials(self, data_a: dict[str, float], data_b: dict[str, float], comparison_type: str) -> dict[str, Any]:
        """Compare two sets of financial data."""
        results = {"comparison_type": comparison_type, "entity_a": {}, "entity_b": {}, "differences": {}, "ratios": {}}

        # Get common metrics
        all_metrics = set(data_a.keys()) | set(data_b.keys())

        for metric in all_metrics:
            val_a = data_a.get(metric, 0)
            val_b = data_b.get(metric, 0)

            results["entity_a"][metric] = val_a
            results["entity_b"][metric] = val_b

            # Calculate differences
            if comparison_type in ["variance", "all"]:
                diff = val_a - val_b
                pct_diff = ((val_a - val_b) / val_b * 100) if val_b != 0 else 0
                results["differences"][metric] = {"absolute": diff, "percentage": pct_diff}

            # Calculate ratios
            if comparison_type in ["ratio", "all"]:
                ratio = val_a / val_b if val_b != 0 else 0
                results["ratios"][metric] = ratio

        # Common size analysis
        if comparison_type in ["common_size", "all"]:
            # Use revenue as base if available
            base_a = data_a.get("revenue", data_a.get("total_assets", 1))
            base_b = data_b.get("revenue", data_b.get("total_assets", 1))

            results["common_size_a"] = {k: (v / base_a * 100) if base_a != 0 else 0 for k, v in data_a.items()}
            results["common_size_b"] = {k: (v / base_b * 100) if base_b != 0 else 0 for k, v in data_b.items()}

        # Performance scoring
        results["performance_summary"] = self._compare_performance(data_a, data_b)

        return results

    # Helper methods for interpretations
    def _interpret_current_ratio(self, ratio: float) -> str:
        if ratio >= 2.0:
            return "Strong liquidity"
        elif ratio >= 1.5:
            return "Good liquidity"
        elif ratio >= 1.0:
            return "Adequate liquidity"
        else:
            return "Liquidity concern"

    def _interpret_quick_ratio(self, ratio: float) -> str:
        if ratio >= 1.0:
            return "Strong immediate liquidity"
        elif ratio >= 0.7:
            return "Adequate immediate liquidity"
        else:
            return "Potential liquidity stress"

    def _interpret_cash_ratio(self, ratio: float) -> str:
        if ratio >= 0.5:
            return "Strong cash position"
        elif ratio >= 0.2:
            return "Adequate cash position"
        else:
            return "Low cash coverage"

    def _interpret_margin(self, margin: float) -> str:
        if margin >= 20:
            return "Excellent profitability"
        elif margin >= 10:
            return "Good profitability"
        elif margin >= 5:
            return "Moderate profitability"
        elif margin > 0:
            return "Low profitability"
        else:
            return "Unprofitable"

    def _interpret_roa(self, roa: float) -> str:
        if roa >= 15:
            return "Excellent asset efficiency"
        elif roa >= 10:
            return "Good asset efficiency"
        elif roa >= 5:
            return "Moderate asset efficiency"
        else:
            return "Poor asset efficiency"

    def _interpret_roe(self, roe: float) -> str:
        if roe >= 20:
            return "Excellent returns for shareholders"
        elif roe >= 15:
            return "Good returns for shareholders"
        elif roe >= 10:
            return "Moderate returns for shareholders"
        else:
            return "Low returns for shareholders"

    def _interpret_debt_to_equity(self, ratio: float) -> str:
        if ratio <= 0.5:
            return "Conservative leverage"
        elif ratio <= 1.0:
            return "Moderate leverage"
        elif ratio <= 2.0:
            return "High leverage"
        else:
            return "Very high leverage - risk concern"

    def _interpret_debt_to_assets(self, ratio: float) -> str:
        if ratio <= 0.3:
            return "Low debt burden"
        elif ratio <= 0.5:
            return "Moderate debt burden"
        elif ratio <= 0.7:
            return "High debt burden"
        else:
            return "Very high debt burden"

    def _interpret_interest_coverage(self, ratio: float) -> str:
        if ratio >= 5:
            return "Strong debt service ability"
        elif ratio >= 3:
            return "Good debt service ability"
        elif ratio >= 1.5:
            return "Adequate debt service ability"
        else:
            return "Debt service concern"

    def _interpret_asset_turnover(self, ratio: float) -> str:
        if ratio >= 2.0:
            return "High asset efficiency"
        elif ratio >= 1.0:
            return "Good asset efficiency"
        else:
            return "Low asset efficiency"

    def _interpret_inventory_turnover(self, ratio: float) -> str:
        if ratio >= 12:
            return "Very efficient inventory management"
        elif ratio >= 6:
            return "Good inventory management"
        elif ratio >= 4:
            return "Adequate inventory management"
        else:
            return "Slow inventory turnover"

    def _interpret_receivables_turnover(self, ratio: float) -> str:
        if ratio >= 12:
            return "Excellent collection efficiency"
        elif ratio >= 8:
            return "Good collection efficiency"
        elif ratio >= 6:
            return "Adequate collection efficiency"
        else:
            return "Collection concerns"

    def _analyze_trend(self, values: list[float]) -> str:
        if not values:
            return "No trend data"

        if len(values) == 1:
            return "Single period - no trend"

        # Simple trend detection
        increasing = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
        decreasing = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1])

        total_changes = len(values) - 1

        if increasing == total_changes:
            return "Consistent growth"
        elif decreasing == total_changes:
            return "Consistent decline"
        elif increasing > decreasing:
            return "Generally increasing"
        elif decreasing > increasing:
            return "Generally decreasing"
        else:
            return "Mixed/volatile"

    def _assess_profitability(self, metrics: dict[str, Any]) -> str:
        operating_margin = metrics.get("operating_margin", 0)
        net_margin = metrics.get("net_margin", 0)

        if net_margin >= 15 and operating_margin >= 20:
            return "Excellent profitability across all levels"
        elif net_margin >= 10 and operating_margin >= 15:
            return "Strong profitability performance"
        elif net_margin >= 5:
            return "Moderate profitability"
        elif net_margin > 0:
            return "Low but positive profitability"
        else:
            return "Unprofitable - requires attention"

    def _assess_cash_flow(self, metrics: dict[str, Any]) -> str:
        operating_cf = metrics.get("operating_cash_flow", 0)
        free_cf = metrics.get("free_cash_flow", 0)
        cf_adequacy = metrics.get("cash_flow_adequacy", 0)

        if operating_cf > 0 and free_cf > 0:
            if cf_adequacy and cf_adequacy > 1.5:
                return "Strong cash generation with excellent coverage"
            else:
                return "Positive cash generation"
        elif operating_cf > 0 and free_cf < 0:
            return "Positive operations but high CapEx requirements"
        else:
            return "Cash flow concerns - negative operating cash flow"

    def _assess_financial_health(self, metrics: dict[str, Any]) -> str:
        current_ratio = metrics.get("current_ratio", 0)
        debt_to_equity = metrics.get("debt_to_equity", 0)
        working_capital = metrics.get("working_capital", 0)

        if current_ratio >= 1.5 and debt_to_equity <= 1.0 and working_capital > 0:
            return "Strong financial position"
        elif current_ratio >= 1.0 and debt_to_equity <= 2.0:
            return "Adequate financial position"
        else:
            return "Financial position requires attention"

    def _compare_performance(self, data_a: dict[str, float], data_b: dict[str, float]) -> dict[str, str]:
        """Compare performance between two entities."""
        summary = {}

        # Revenue comparison
        rev_a = data_a.get("revenue", 0)
        rev_b = data_b.get("revenue", 0)
        if rev_a and rev_b:
            summary["size"] = "Entity A larger" if rev_a > rev_b else "Entity B larger"

        # Profitability comparison
        margin_a = (data_a.get("net_income", 0) / rev_a * 100) if rev_a > 0 else 0
        margin_b = (data_b.get("net_income", 0) / rev_b * 100) if rev_b > 0 else 0
        if margin_a > margin_b:
            summary["profitability"] = f"Entity A more profitable ({margin_a:.1f}% vs {margin_b:.1f}%)"
        else:
            summary["profitability"] = f"Entity B more profitable ({margin_b:.1f}% vs {margin_a:.1f}%)"

        return summary


class OutputFormatter:
    """Format analysis results for clear presentation."""

    def format_income_statement_analysis(self, results: dict[str, Any], period: str) -> str:
        """Format income statement analysis results."""
        output = f"""
📊 INCOME STATEMENT ANALYSIS ({period.upper()})

💰 REVENUE & PROFITABILITY
• Total Revenue: ${results.get("total_revenue", 0):,.0f}
• Gross Profit: ${results.get("gross_profit", 0):,.0f}
• Operating Income: ${results.get("operating_income", 0):,.0f}
• Net Income: ${results.get("net_income", 0):,.0f}

📈 PROFIT MARGINS
• Gross Margin: {results.get("gross_margin", 0):.1f}%
• Operating Margin: {results.get("operating_margin", 0):.1f}%
• Net Margin: {results.get("net_margin", 0):.1f}%
"""

        # Add EBITDA if available
        if "ebitda" in results:
            output += f"• EBITDA Margin: {results.get('ebitda_margin', 0):.1f}%\n"

        # Add growth analysis if available
        if "period_growth_rates" in results:
            output += "\n📊 GROWTH ANALYSIS\n"
            for period, rate in results["period_growth_rates"].items():
                output += f"• {period}: {'+' if rate > 0 else ''}{rate:.1f}%\n"
            output += f"• Average Growth: {results.get('average_growth', 0):.1f}%\n"
            output += f"• Growth Trend: {results.get('growth_trend', 'N/A')}\n"

        output += f"\n💡 ASSESSMENT: {results.get('profitability_assessment', 'N/A')}"

        return output

    def format_ratio_analysis(self, results: dict[str, Any], ratio_type: str) -> str:
        """Format financial ratio analysis results."""
        output = f"""
📊 FINANCIAL RATIO ANALYSIS - {ratio_type.upper()}

"""

        # Group ratios by category
        categories = {
            "LIQUIDITY RATIOS": ["current_ratio", "quick_ratio", "cash_ratio", "working_capital"],
            "PROFITABILITY RATIOS": ["net_margin", "return_on_assets", "return_on_equity"],
            "LEVERAGE RATIOS": ["debt_to_equity", "debt_to_assets", "interest_coverage"],
            "EFFICIENCY RATIOS": ["asset_turnover", "inventory_turnover", "receivables_turnover"],
        }

        for category, ratio_keys in categories.items():
            category_ratios = {k: v for k, v in results.items() if k in ratio_keys}

            if category_ratios:
                output += f"📈 {category}\n"

                for ratio_name, ratio_data in category_ratios.items():
                    if isinstance(ratio_data, dict):
                        value = ratio_data.get("value", 0)
                        interp = ratio_data.get("interpretation", "")

                        # Format based on ratio type
                        if "margin" in ratio_name or "return" in ratio_name:
                            output += f"• {ratio_name.replace('_', ' ').title()}: {value:.1f}% - {interp}\n"
                        elif ratio_name == "working_capital":
                            output += f"• {ratio_name.replace('_', ' ').title()}: ${value:,.0f} - {interp}\n"
                        else:
                            output += f"• {ratio_name.replace('_', ' ').title()}: {value:.2f} - {interp}\n"

                        # Add days if available
                        if "days" in ratio_data:
                            output += f"  → Days: {ratio_data['days']:.0f}\n"

                output += "\n"

        return output

    def format_cash_flow_analysis(self, results: dict[str, Any], period: str) -> str:
        """Format cash flow analysis results."""
        output = f"""
💵 CASH FLOW ANALYSIS ({period.upper()})

📊 CASH FLOW SUMMARY
• Operating Cash Flow: ${results.get("operating_cash_flow", 0):,.0f}
• Investing Cash Flow: ${results.get("investing_cash_flow", 0):,.0f}
• Financing Cash Flow: ${results.get("financing_cash_flow", 0):,.0f}
• Total Change in Cash: ${results.get("total_change_in_cash", 0):,.0f}

💰 CASH POSITION
• Beginning Cash: ${results.get("beginning_cash", 0):,.0f}
• Ending Cash: ${results.get("ending_cash", 0):,.0f}
• Free Cash Flow: ${results.get("free_cash_flow", 0):,.0f}
"""

        # Add burn rate analysis if applicable
        if "burn_rate" in results:
            burn_data = results["burn_rate"]
            output += f"""
🔥 BURN RATE ANALYSIS
• {period.title()} Cash Burn Rate: ${burn_data[f"{period}_burn"]:,.0f}
• Monthly Cash Burn Rate: ${burn_data["monthly_burn"]:,.0f}
• Daily Cash Burn Rate: ${burn_data["daily_burn"]:,.0f}
• Cash Runway: {results.get("cash_runway_months", 0):.1f} months ({results.get("cash_runway_days", 0):.0f} days)
"""

        # Add quality metrics
        if "cash_flow_quality_ratio" in results:
            output += "\n📈 QUALITY METRICS\n"
            output += f"• Cash Flow Quality (OCF/NI): {results['cash_flow_quality_ratio']:.2f}\n"

        if "cash_flow_adequacy" in results:
            output += f"• Cash Flow Adequacy: {results['cash_flow_adequacy']:.2f}\n"

        output += f"\n💡 ASSESSMENT: {results.get('cash_flow_assessment', 'N/A')}"

        return output

    def format_balance_sheet_analysis(self, results: dict[str, Any], period_end: str) -> str:
        """Format balance sheet analysis results."""
        asset_comp = results.get("asset_composition", {})
        capital_struct = results.get("capital_structure", {})

        output = f"""
📋 BALANCE SHEET ANALYSIS (as of {period_end})

🏢 ASSET COMPOSITION
• Total Assets: ${asset_comp.get("total_assets", 0):,.0f}
• Current Assets: ${asset_comp.get("current_assets", 0):,.0f} ({asset_comp.get("current_asset_ratio", 0):.1f}%)
• Non-Current Assets: ${asset_comp.get("non_current_assets", 0):,.0f}

💼 CAPITAL STRUCTURE
• Total Liabilities: ${capital_struct.get("total_liabilities", 0):,.0f} ({capital_struct.get("debt_ratio", 0):.1f}%)
• Total Equity: ${capital_struct.get("total_equity", 0):,.0f} ({capital_struct.get("equity_ratio", 0):.1f}%)

📊 KEY METRICS
• Working Capital: ${results.get("working_capital", 0):,.0f}
• Current Ratio: {results.get("current_ratio", 0):.2f}
• Quick Ratio: {results.get("quick_ratio", 0):.2f}
• Debt-to-Equity: {results.get("debt_to_equity", 0):.2f}
"""

        # Add accounting equation check
        if results.get("accounting_equation_balanced"):
            output += "\n✅ Accounting equation balanced"
        else:
            output += "\n⚠️ Warning: Accounting equation imbalance detected"

        output += f"\n\n💡 ASSESSMENT: {results.get('financial_health_assessment', 'N/A')}"

        return output

    def format_growth_analysis(self, results: dict[str, Any], metric_name: str) -> str:
        """Format growth trend analysis results."""
        output = f"""
📈 GROWTH ANALYSIS - {metric_name.upper()}

"""

        # Period-over-period growth
        if "period_growth_rates" in results:
            output += "📊 PERIOD-OVER-PERIOD GROWTH\n"
            for period_data in results["period_growth_rates"]:
                period = period_data["period"]
                rate = period_data["growth_rate"]
                output += f"• {period}: {'+' if rate > 0 else ''}{rate:.1f}%\n"

        # Summary statistics
        if "statistics" in results:
            stats = results["statistics"]
            output += f"""
📊 STATISTICAL SUMMARY
• Mean Value: ${stats["mean"]:,.0f}
• Median Value: ${stats["median"]:,.0f}
• Standard Deviation: ${stats["std_dev"]:,.0f}
• Coefficient of Variation: {stats["cv"]:.1f}%
"""

        # Growth metrics
        if "cagr" in results:
            output += f"\n• CAGR: {results['cagr']:.1f}%\n"

        if "average_growth" in results:
            output += f"• Average Growth Rate: {results['average_growth']:.1f}%\n"
            output += f"• Growth Volatility: {results.get('growth_volatility', 0):.1f}%\n"
            output += f"• Growth Trend: {results.get('growth_trend', 'N/A')}\n"

        # Projection
        if "projection" in results:
            proj = results["projection"]
            output += f"""
🔮 PROJECTION (Next Period)
• Projected Value: ${proj["next_period_value"]:,.0f}
• Projected Growth: {proj["projected_growth"]:.1f}%
• Trend Direction: {"↗️ Upward" if proj["trend_slope"] > 0 else "↘️ Downward"}
"""

        return output

    def format_comparison_analysis(self, results: dict[str, Any], comparison_type: str) -> str:
        """Format comparison analysis results."""
        output = f"""
📊 COMPARATIVE ANALYSIS - {comparison_type.upper()}

"""

        # Key metrics comparison
        if "entity_a" in results and "entity_b" in results:
            output += "📈 KEY METRICS COMPARISON\n"
            output += "Metric               | Entity A         | Entity B         | Difference\n"
            output += "-" * 70 + "\n"

            for metric in results["entity_a"].keys():
                val_a = results["entity_a"][metric]
                val_b = results["entity_b"][metric]

                if "differences" in results and metric in results["differences"]:
                    diff = results["differences"][metric]["percentage"]
                    diff_str = f"{'+' if diff > 0 else ''}{diff:.1f}%"
                else:
                    diff_str = "N/A"

                output += f"{metric[:20]:<20} | ${val_a:>15,.0f} | ${val_b:>15,.0f} | {diff_str:>10}\n"

        # Performance summary
        if "performance_summary" in results:
            output += "\n💡 PERFORMANCE SUMMARY\n"
            for key, value in results["performance_summary"].items():
                output += f"• {key.title()}: {value}\n"

        return output
