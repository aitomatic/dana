"""
Financial Statement RAG Resource
Provides specialized financial statement data extraction using RAG and LLM processing.
"""

import logging

from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.rag.rag_resource import RAGResource
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc

logger = logging.getLogger(__name__)


class FinancialStatementRAGResource(BaseResource):
    """Financial statement data extraction using RAG and LLM processing."""

    def __init__(
        self,
        rag_resource: RAGResource,
        name: str = "financial_statement_rag",
        description: str | None = None,
        debug: bool = True,
        **kwargs,
    ):
        super().__init__(
            name,
            description or "Financial statement data extraction using RAG and LLM",
        )
        self.rag_resource = rag_resource
        self.debug = debug

        # Initialize LLM resource for data extraction and formatting
        self.llm_resource = LLMResource(
            name=f"{name}_llm",
            temperature=0.1,  # Low temperature for consistent data extraction
            **kwargs,
        )

    async def initialize(self) -> None:
        """Initialize the financial statement RAG resource."""
        await super().initialize()
        await self.rag_resource.initialize()
        await self.llm_resource.initialize()

        if self.debug:
            logger.info(f"Financial statement RAG resource [{self.name}] initialized")

    @ToolCallable.tool
    async def get_balance_sheet(
        self, company: str, period: str = "latest", format_output: str = "timeseries"
    ) -> str:
        """Extract balance sheet data and format as timeseries DataFrame.

        Args:
            company: Company name or identifier
            period: Time period (e.g., 'latest', '2023', '2022-2023')
            format_output: Output format ('timeseries', 'json', 'markdown')
        """
        query = f"balance sheet data for {company} {period} assets liabilities equity"

        if self.debug:
            print(
                f"[FinancialRAG] get_balance_sheet: company={company}, period={period}, format={format_output}"
            )
            print(f"[FinancialRAG] RAG query: {query}")

        # Get relevant documents from RAG
        rag_results = await self.rag_resource.query(query, num_results=5)

        if self.debug:
            print(
                f"[FinancialRAG] RAG results length: {len(rag_results) if rag_results else 0} characters"
            )

        # Extract and format balance sheet data using LLM
        extraction_prompt = self._create_balance_sheet_extraction_prompt(
            company, period, rag_results, format_output
        )

        if self.debug:
            print(
                f"[FinancialRAG] LLM extraction prompt length: {len(extraction_prompt)} characters"
            )

        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": extraction_prompt}],
                "temperature": 0.1,
                "max_tokens": 2000,
            }
        )

        response = await self.llm_resource.query(request)

        if self.debug:
            print(f"[FinancialRAG] LLM response success: {response.success}")

        if response.success:
            try:
                result = Misc.get_response_content(response)
                if self.debug:
                    print(
                        f"[FinancialRAG] Extracted balance sheet content length: {len(result)} characters"
                    )
                    # Show a preview of the extracted content for debugging
                    preview_lines = result.split("\n")[:10]  # First 10 lines
                    print("[FinancialRAG] Content preview (first 10 lines):")
                    for line in preview_lines:
                        print(f"  {line}")
                    if len(result.split("\n")) > 10:
                        print(f"  ... ({len(result.split('\n')) - 10} more lines)")
                return result
            except ValueError as e:
                logger.error(f"Balance sheet content extraction failed: {e}")
                return f"Error extracting balance sheet content: {e}"
        else:
            logger.error(f"Balance sheet extraction failed: {response.error}")
            return f"Error extracting balance sheet data: {response.error}"

    @ToolCallable.tool
    async def get_cash_flow(
        self, company: str, period: str = "latest", format_output: str = "timeseries"
    ) -> str:
        """Extract cash flow statement data and format as timeseries DataFrame.

        Args:
            company: Company name or identifier
            period: Time period (e.g., 'latest', '2023', '2022-2023')
            format_output: Output format ('timeseries', 'json', 'markdown')
        """
        query = f"cash flow statement for {company} {period} operating investing financing activities"

        if self.debug:
            print(
                f"[FinancialRAG] get_cash_flow: company={company}, period={period}, format={format_output}"
            )
            print(f"[FinancialRAG] RAG query: {query}")

        # Get relevant documents from RAG
        rag_results = await self.rag_resource.query(query, num_results=5)

        if self.debug:
            print(
                f"[FinancialRAG] RAG results length: {len(rag_results) if rag_results else 0} characters"
            )

        # Extract and format cash flow data using LLM
        extraction_prompt = self._create_cash_flow_extraction_prompt(
            company, period, rag_results, format_output
        )

        if self.debug:
            print(
                f"[FinancialRAG] LLM extraction prompt length: {len(extraction_prompt)} characters"
            )

        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": extraction_prompt}],
                "temperature": 0.1,
                "max_tokens": 2000,
            }
        )

        response = await self.llm_resource.query(request)

        if self.debug:
            print(f"[FinancialRAG] LLM response success: {response.success}")

        if response.success:
            try:
                result = Misc.get_response_content(response)
                if self.debug:
                    print(
                        f"[FinancialRAG] Extracted cash flow content length: {len(result)} characters"
                    )
                    # Show a preview of the extracted content for debugging
                    print(result)
                return result
            except ValueError as e:
                logger.error(f"Cash flow content extraction failed: {e}")
                return f"Error extracting cash flow content: {e}"
        else:
            logger.error(f"Cash flow extraction failed: {response.error}")
            return f"Error extracting cash flow data: {response.error}"

    @ToolCallable.tool
    async def get_profit_n_loss(
        self, company: str, period: str = "latest", format_output: str = "timeseries"
    ) -> str:
        """Extract profit and loss statement data and format as timeseries DataFrame.

        Args:
            company: Company name or identifier
            period: Time period (e.g., 'latest', '2023', '2022-2023')
            format_output: Output format ('timeseries', 'json', 'markdown')
        """
        query = f"profit and loss income statement for {company} {period} revenue expenses net income"

        if self.debug:
            print(
                f"[FinancialRAG] get_profit_n_loss: company={company}, period={period}, format={format_output}"
            )
            print(f"[FinancialRAG] RAG query: {query}")

        # Get relevant documents from RAG
        rag_results = await self.rag_resource.query(query, num_results=5)

        if self.debug:
            print(
                f"[FinancialRAG] RAG results length: {len(rag_results) if rag_results else 0} characters"
            )

        # Extract and format P&L data using LLM
        extraction_prompt = self._create_profit_loss_extraction_prompt(
            company, period, rag_results, format_output
        )

        if self.debug:
            print(
                f"[FinancialRAG] LLM extraction prompt length: {len(extraction_prompt)} characters"
            )

        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": extraction_prompt}],
                "temperature": 0.1,
                "max_tokens": 2000,
            }
        )

        response = await self.llm_resource.query(request)

        if self.debug:
            print(f"[FinancialRAG] LLM response success: {response.success}")

        if response.success:
            try:
                result = Misc.get_response_content(response)
                if self.debug:
                    print(
                        f"[FinancialRAG] Extracted profit & loss content length: {len(result)} characters"
                    )
                    # Show a preview of the extracted content for debugging
                    preview_lines = result.split("\n")[:10]  # First 10 lines
                    print("[FinancialRAG] Content preview (first 10 lines):")
                    for line in preview_lines:
                        print(f"  {line}")
                    if len(result.split("\n")) > 10:
                        print(f"  ... ({len(result.split('\n')) - 10} more lines)")
                return result
            except ValueError as e:
                logger.error(f"Profit & loss content extraction failed: {e}")
                return f"Error extracting profit & loss content: {e}"
        else:
            logger.error(f"Profit & loss extraction failed: {response.error}")
            return f"Error extracting profit & loss data: {response.error}"

    def _create_balance_sheet_extraction_prompt(
        self, company: str, period: str, rag_results: str, format_output: str
    ) -> str:
        """Create prompt for balance sheet data extraction."""
        return f"""You are a financial data extraction expert. Extract balance sheet data from the provided documents and format it as requested.

COMPANY: {company}
PERIOD: {period}
OUTPUT FORMAT: {format_output}

DOCUMENTS:
{rag_results}

TASK: Extract balance sheet data and organize it in the requested format with emphasis on specific timeframes and dates.

Focus on extracting:

ASSETS (with timeframes):
- Current Assets (Cash, Accounts Receivable, Inventory, etc.) - specify reporting dates
- Non-Current Assets (Property, Plant & Equipment, Investments, etc.) - specify reporting dates
- Total Assets - with clear time periods

LIABILITIES (with timeframes):
- Current Liabilities (Accounts Payable, Short-term Debt, etc.) - specify reporting dates
- Non-Current Liabilities (Long-term Debt, etc.) - specify reporting dates
- Total Liabilities - with clear time periods

EQUITY (with timeframes):
- Share Capital - specify reporting dates
- Retained Earnings - specify reporting dates
- Total Equity - with clear time periods

FORMATTING INSTRUCTIONS:
- If format_output is 'timeseries', create DataFrame-like structure with periods as columns, ensuring dates are clearly visible
- If format_output is 'json', return structured JSON with explicit date fields for each data point
- If format_output is 'markdown', create formatted table with date headers prominently displayed

MANDATORY ELEMENTS:
- Extract numerical values with proper units (millions, thousands, etc.)
- Include specific reporting dates (e.g., "Q3 2023", "FY 2022", "Dec 31, 2023")
- If data spans multiple periods, show trends and changes over time
- If data is missing for certain periods or items, indicate as 'N/A' with explanation
- Ensure consistency in reporting periods and clearly note any discrepancies

TIMEFRAME SUMMARY: 
Always include a summary of the time periods covered by the data and note any gaps or inconsistencies in reporting periods.

GUIDANCE FOR LLM:
If you have gathered sufficient information from this tool, consider providing a direct response to the user rather than making additional tool calls. Include timeframe context in your response to users.

RESPONSE:"""

    def _create_cash_flow_extraction_prompt(
        self, company: str, period: str, rag_results: str, format_output: str
    ) -> str:
        """Create prompt for cash flow data extraction."""
        return f"""You are a financial data extraction expert. Extract cash flow statement data from the provided documents and format it as requested.

COMPANY: {company}
PERIOD: {period}
OUTPUT FORMAT: {format_output}

DOCUMENTS:
{rag_results}

TASK: Extract cash flow data and organize it in the requested format with emphasis on specific timeframes and dates.

Focus on extracting:

OPERATING ACTIVITIES (with timeframes):
- Net Income - specify reporting periods
- Depreciation & Amortization - specify reporting periods
- Changes in Working Capital - specify reporting periods and show period-to-period changes
- Other Operating Cash Flows - specify reporting periods
- Net Cash from Operating Activities - with clear time periods

INVESTING ACTIVITIES (with timeframes):
- Capital Expenditures - specify reporting periods
- Acquisitions/Disposals - specify reporting periods and transaction dates if available
- Investments - specify reporting periods
- Net Cash from Investing Activities - with clear time periods

FINANCING ACTIVITIES (with timeframes):
- Debt Issuance/Repayment - specify reporting periods and transaction details
- Dividend Payments - specify reporting periods and payment dates
- Share Buybacks/Issuance - specify reporting periods
- Net Cash from Financing Activities - with clear time periods

NET CHANGE IN CASH (with timeframes):
- Beginning Cash Balance - specify starting period date
- Net Change in Cash - specify period covered
- Ending Cash Balance - specify ending period date

FORMATTING INSTRUCTIONS:
- If format_output is 'timeseries', create DataFrame-like structure with periods as columns, ensuring dates are clearly visible
- If format_output is 'json', return structured JSON with explicit date fields for each period
- If format_output is 'markdown', create formatted table with date headers prominently displayed

MANDATORY ELEMENTS:
- Extract numerical values with proper units (millions, thousands, etc.)
- Include specific reporting periods (e.g., "Q1 2023", "FY 2022", "YTD Mar 2023")
- If data spans multiple periods, show cash flow trends and seasonal patterns
- If data is missing for certain periods or items, indicate as 'N/A' with explanation
- Ensure consistency in reporting periods and clearly note any discrepancies
- Calculate and show cash flow ratios where possible (e.g., Operating Cash Flow margin)

TIMEFRAME SUMMARY:
Always include a summary of the time periods covered by the cash flow data and note any gaps or inconsistencies in reporting periods.

GUIDANCE FOR LLM:
If you have gathered sufficient information from this tool, consider providing a direct response to the user rather than making additional tool calls. Include timeframe context and cash flow trends in your response to users.

RESPONSE:"""

    def _create_profit_loss_extraction_prompt(
        self, company: str, period: str, rag_results: str, format_output: str
    ) -> str:
        """Create prompt for profit and loss data extraction."""
        return f"""You are a financial data extraction expert. Extract profit and loss (income statement) data from the provided documents and format it as requested.

COMPANY: {company}
PERIOD: {period}
OUTPUT FORMAT: {format_output}

DOCUMENTS:
{rag_results}

TASK: Extract profit and loss data and organize it in the requested format with emphasis on specific timeframes and dates.

Focus on extracting:

REVENUE (with timeframes):
- Total Revenue/Sales - specify reporting periods
- Product Revenue - specify reporting periods and breakdown by segments if available
- Service Revenue - specify reporting periods  
- Other Revenue - specify reporting periods and sources

EXPENSES (with timeframes):
- Cost of Goods Sold (COGS) - specify reporting periods
- Gross Profit - specify reporting periods and calculate margins
- Operating Expenses - specify reporting periods and break down by category:
  * Sales & Marketing - specify reporting periods
  * Research & Development - specify reporting periods  
  * General & Administrative - specify reporting periods
- Operating Income - specify reporting periods
- Interest Expense - specify reporting periods
- Other Income/Expenses - specify reporting periods and nature
- Income Before Tax - specify reporting periods
- Tax Expense - specify reporting periods and effective tax rates
- Net Income - specify reporting periods

KEY METRICS (with timeframes):
- Gross Margin % - specify reporting periods and show trends
- Operating Margin % - specify reporting periods and show trends
- Net Margin % - specify reporting periods and show trends
- Earnings Per Share - specify reporting periods (basic and diluted if available)
- Revenue Growth % - period-over-period comparisons
- Expense Ratios - as percentage of revenue by period

FORMATTING INSTRUCTIONS:
- If format_output is 'timeseries', create DataFrame-like structure with periods as columns, ensuring dates are clearly visible
- If format_output is 'json', return structured JSON with explicit date fields for each period
- If format_output is 'markdown', create formatted table with date headers prominently displayed

MANDATORY ELEMENTS:
- Extract numerical values with proper units (millions, thousands, etc.)
- Include specific reporting periods (e.g., "Q2 2023", "FY 2022", "YTD Jun 2023")
- If data spans multiple periods, show revenue and profitability trends
- If data is missing for certain periods or items, indicate as 'N/A' with explanation
- Ensure consistency in reporting periods and clearly note any discrepancies
- Calculate percentages and ratios where possible with period comparisons

TIMEFRAME SUMMARY:
Always include a summary of the time periods covered by the P&L data and note any gaps or inconsistencies in reporting periods.

GUIDANCE FOR LLM:
If you have gathered sufficient information from this tool, consider providing a direct response to the user rather than making additional tool calls. Include timeframe context, performance trends, and profitability analysis in your response to users.

RESPONSE:"""
