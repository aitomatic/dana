"""
Financial Statement RAG Resource
Provides specialized financial statement data extraction using RAG and LLM processing.
"""

import logging

from dana.common.mixins.tool_callable import ToolCallable
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.sys_resource.rag.rag_resource import RAGResource
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc

logger = logging.getLogger(__name__)


class FinancialStatementRAGResource(BaseSysResource):
    """Financial statement data extraction using RAG and LLM processing."""

    def __init__(
        self,
        name: str = "financial_statement_rag",
        description: str | None = None,
        debug: bool = True,
        rag_resource: RAGResource | None = None,
        **kwargs,
    ):
        super().__init__(
            name,
            description or "Financial statement data extraction using RAG and LLM",
        )
        self.rag_resource = rag_resource or RAGResource(
            name=f"{name}_rag",
            **kwargs,
        )
        self.debug = debug

        # Initialize LLM resource for data extraction and formatting
        self.llm_resource = LLMResource(
            name=f"{name}_llm",
            temperature=0.1,  # Low temperature for consistent data extraction
            **kwargs,
        )
        self._cache = {}

    async def initialize(self) -> None:
        """Initialize the financial statement RAG resource."""
        await super().initialize()
        await self.rag_resource.initialize()
        await self.llm_resource.initialize()

        if self.debug:
            logger.info(f"Financial statement RAG resource [{self.name}] initialized")

    @ToolCallable.tool
    async def get_balance_sheet(self, company: str, period: str = "latest", format_output: str = "timeseries") -> str:
        """Extract balance sheet data and format as timeseries DataFrame.

        Args:
            company: Company name or identifier
            period: Time period (e.g., 'latest', '2023', '2022-2023')
            format_output: Output format ('timeseries', 'json', 'markdown')
        """
        query = f"balance sheet data for {company} {period} assets liabilities equity"

        if self.debug:
            print(f"[FinancialRAG] get_balance_sheet: company={company}, period={period}, format={format_output}")
            print(f"[FinancialRAG] RAG query: {query}")

        # Get relevant documents from RAG
        rag_results = await self.rag_resource.query(query, num_results=5)

        if self.debug:
            print(f"[FinancialRAG] RAG results length: {len(rag_results) if rag_results else 0} characters")

        # Extract and format balance sheet data using LLM
        extraction_prompt = self._create_balance_sheet_extraction_prompt(company, period, rag_results, format_output)

        if self.debug:
            print(f"[FinancialRAG] LLM extraction prompt length: {len(extraction_prompt)} characters")

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
                    print(f"[FinancialRAG] Extracted balance sheet content length: {len(result)} characters")
                    # Show a preview of the extracted content for debugging
                    print(result)
                return result
            except ValueError as e:
                logger.error(f"Balance sheet content extraction failed: {e}")
                return f"Error extracting balance sheet content: {e}"
        else:
            logger.error(f"Balance sheet extraction failed: {response.error}")
            return f"Error extracting balance sheet data: {response.error}"

    @ToolCallable.tool
    async def get_cash_flow(self, company: str, period: str = "latest", format_output: str = "timeseries") -> str:
        """Extract cash flow statement data and format as timeseries DataFrame.

        Args:
            company: Company name or identifier
            period: Time period (e.g., 'latest', '2023', '2022-2023')
            format_output: Output format ('timeseries', 'json', 'markdown')
        """
        query = f"cash flow statement for {company} {period} operating investing financing activities"

        if self.debug:
            print(f"[FinancialRAG] get_cash_flow: company={company}, period={period}, format={format_output}")
            print(f"[FinancialRAG] RAG query: {query}")

        # Get relevant documents from RAG
        rag_results = await self.rag_resource.query(query, num_results=5)

        if self.debug:
            print(f"[FinancialRAG] RAG results length: {len(rag_results) if rag_results else 0} characters")

        # Extract and format cash flow data using LLM
        extraction_prompt = self._create_cash_flow_extraction_prompt(company, period, rag_results, format_output)

        if self.debug:
            print(f"[FinancialRAG] LLM extraction prompt length: {len(extraction_prompt)} characters")

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
                    print(f"[FinancialRAG] Extracted cash flow content length: {len(result)} characters")
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
    async def get_profit_n_loss(self, company: str, period: str = "latest", format_output: str = "timeseries") -> str:
        """Extract profit and loss statement data and format as timeseries DataFrame.

        Args:
            company: Company name or identifier
            period: Time period (e.g., 'latest', '2023', '2022-2023')
            format_output: Output format ('timeseries', 'json', 'markdown')
        """
        query = f"profit and loss income statement for {company} {period} revenue expenses net income"

        if self.debug:
            print(f"[FinancialRAG] get_profit_n_loss: company={company}, period={period}, format={format_output}")
            print(f"[FinancialRAG] RAG query: {query}")

        # Get relevant documents from RAG
        rag_results = await self.rag_resource.query(query, num_results=5)

        if self.debug:
            print(f"[FinancialRAG] RAG results length: {len(rag_results) if rag_results else 0} characters")

        # Extract and format P&L data using LLM
        extraction_prompt = self._create_profit_loss_extraction_prompt(company, period, rag_results, format_output)

        if self.debug:
            print(f"[FinancialRAG] LLM extraction prompt length: {len(extraction_prompt)} characters")

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
                    print(f"[FinancialRAG] Extracted profit & loss content length: {len(result)} characters")
                    print(result)
                return result
            except ValueError as e:
                logger.error(f"Profit & loss content extraction failed: {e}")
                return f"Error extracting profit & loss content: {e}"
        else:
            logger.error(f"Profit & loss extraction failed: {response.error}")
            return f"Error extracting profit & loss data: {response.error}"

    def _create_balance_sheet_extraction_prompt(self, company: str, period: str, rag_results: str, format_output: str) -> str:
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

REQUIRED HEADER INFORMATION:
- Always start your response with a clear statement of the monetary units used
- Examples: "All figures in USD millions", "All figures in USD thousands", "All figures in USD (actual dollars)"
- If mixed units are present, clearly indicate which sections use which units
- Place this unit information prominently at the very beginning of your response

MANDATORY ELEMENTS:
- Extract numerical values with proper units (millions, thousands, etc.)
- Include specific reporting dates (e.g., "Q3 2023", "FY 2022", "Dec 31, 2023")
- If data spans multiple periods, show trends and changes over time
- If data is missing for certain periods or items, indicate as 'N/A' with explanation
- Ensure consistency in reporting periods and clearly note any discrepancies

IMPORTANT NUMBER FORMATTING:
- Use standard positive/negative notation: positive numbers as "100", negative numbers as "-100"
- Handle parentheses carefully based on accounting conventions:
  * Single parentheses around dollar amounts like "($ 1,085,122)" are POSITIVE values - extract as "1085122"
  * Double parentheses or explicit negative indicators like "($ (16,825)" are NEGATIVE values - extract as "-16825"
  * Look for context clues: losses, negative equity, deficits should be negative
  * Assets, revenues, positive equity should be positive regardless of parentheses formatting
- Examples: 
  * "($ 1,085,122)" → "1085122" (positive)
  * "($ (16,825)" → "-16825" (negative)
  * "$ 891,257" → "891257" (positive)
- When in doubt, use financial statement context to determine if the value should be positive or negative

TIMEFRAME SUMMARY: 
Always include a summary of the time periods covered by the data and note any gaps or inconsistencies in reporting periods.

GUIDANCE FOR LLM:
If you have gathered sufficient information from this tool, consider providing a direct response to the user rather than making additional tool calls. Include timeframe context in your response to users.

RESPONSE:"""

    def _create_cash_flow_extraction_prompt(self, company: str, period: str, rag_results: str, format_output: str) -> str:
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

REQUIRED HEADER INFORMATION:
- Always start your response with a clear statement of the monetary units used
- Examples: "All figures in USD millions", "All figures in USD thousands", "All figures in USD (actual dollars)"
- If mixed units are present, clearly indicate which sections use which units
- Place this unit information prominently at the very beginning of your response

MANDATORY ELEMENTS:
- Extract numerical values with proper units (millions, thousands, etc.)
- Include specific reporting periods (e.g., "Q1 2023", "FY 2022", "YTD Mar 2023")
- If data spans multiple periods, show cash flow trends and seasonal patterns
- If data is missing for certain periods or items, indicate as 'N/A' with explanation
- Ensure consistency in reporting periods and clearly note any discrepancies
- Calculate and show cash flow ratios where possible (e.g., Operating Cash Flow margin)

IMPORTANT NUMBER FORMATTING:
- Use standard positive/negative notation: positive numbers as "100", negative numbers as "-100"
- Handle parentheses carefully based on accounting conventions:
  * Single parentheses around dollar amounts like "($ 1,085,122)" are POSITIVE values - extract as "1085122"
  * Double parentheses or explicit negative indicators like "($ (16,825)" are NEGATIVE values - extract as "-16825"
  * Look for context clues: cash outflows, capital expenditures should be negative
  * Cash inflows, operating cash flow should be positive regardless of parentheses formatting
- Examples: 
  * "($ 1,085,122)" → "1085122" (positive cash flow)
  * "($ (16,825)" → "-16825" (negative cash flow)
  * "$ 891,257" → "891257" (positive)
- Cash outflows should be shown as negative numbers (e.g., Capital Expenditures: "-50,000")
- When in doubt, use cash flow statement context to determine if the value should be positive or negative

TIMEFRAME SUMMARY:
Always include a summary of the time periods covered by the cash flow data and note any gaps or inconsistencies in reporting periods.

GUIDANCE FOR LLM:
If you have gathered sufficient information from this tool, consider providing a direct response to the user rather than making additional tool calls. Include timeframe context and cash flow trends in your response to users.

RESPONSE:"""

    def _create_profit_loss_extraction_prompt(self, company: str, period: str, rag_results: str, format_output: str) -> str:
        """Create prompt for profit and loss data extraction."""
        return f"""You are a financial data extraction expert. Extract profit and loss (income statement) data from the provided documents and format it as requested.

COMPANY: {company}
PERIOD: {period}
OUTPUT FORMAT: {format_output}

DOCUMENTS:
{rag_results}

TASK: Extract ALL financial and business data from the documents. Do not limit yourself to traditional income statement categories - extract EVERYTHING you find.

CRITICAL INSTRUCTION: Extract all data present in the documents, even if it doesn't fit standard financial statement categories. Include any business metrics, KPIs, or non-traditional revenue/expense items mentioned.

COMPREHENSIVE DATA EXTRACTION:

REVENUE (extract ALL revenue types found):
- Total Revenue/Sales
- Product Revenue 
- Service Revenue
- Subscription Revenue
- License Revenue  
- Recurring Revenue (ARR, MRR, any SaaS metrics)
- Contract Revenue
- Recurring vs Non-recurring breakdowns
- **ANY OTHER REVENUE CATEGORIES MENTIONED IN THE DOCUMENTS**

EXPENSES (extract ALL expense types found):
- Cost of Goods Sold (COGS)
- Gross Profit
- Sales & Marketing
- Research & Development  
- General & Administrative
- Personnel Expenses
- Operating Expenses (total and any subcategories)
- Operating Income
- Interest Expense
- Other Income/Expenses
- Income Before Tax
- Tax Expense
- Net Income
- **ANY OTHER EXPENSE CATEGORIES MENTIONED IN THE DOCUMENTS**

REQUIRED OUTPUT FORMAT:
Structure your output as a table with periods as columns and financial items as rows:

| Metric               | Period_1 | Period_2 | Period_3 | Period_N |
|----------------------|----------|----------|----------|----------|
| Revenue_Item_1       | value    | value    | value    | value    |
| Revenue_Item_2       | value    | value    | value    | value    |
| Expense_Item_1       | value    | value    | value    | value    |
| Expense_Item_2       | value    | value    | value    | value    |

FORMATTING RULES:
1. Replace "Period_X" with actual period names from documents (Q1'24, Q2'24, FY 2024, etc.)
2. Replace "Revenue_Item_X" and "Expense_Item_X" with actual field names found
3. Add rows for ALL financial data found in the documents
4. Use "N/A" for missing data

FORMATTING INSTRUCTIONS:
- If format_output is 'timeseries', use the table structure above
- If format_output is 'json', convert to structured JSON with periods as keys
- If format_output is 'markdown', use markdown table format

REQUIRED HEADER INFORMATION:
- Always start your response with a clear statement of the monetary units used
- Examples: "All figures in USD millions", "All figures in USD thousands", "All figures in USD (actual dollars)"
- If mixed units are present, clearly indicate which sections use which units
- Place this unit information prominently at the very beginning of your response

MANDATORY ELEMENTS:
- Extract numerical values with proper units (millions, thousands, etc.)
- Include specific reporting periods (e.g., "Q2 2023", "FY 2022", "YTD Jun 2023")
- If data spans multiple periods, show revenue and profitability trends
- If data is missing for certain periods or items, indicate as 'N/A' with explanation
- Ensure consistency in reporting periods and clearly note any discrepancies
- Calculate percentages and ratios where possible with period comparisons

IMPORTANT NUMBER FORMATTING:
- Use standard positive/negative notation: positive numbers as "100", negative numbers as "-100"
- Handle parentheses carefully based on accounting conventions:
  * Single parentheses around dollar amounts like "($ 1,085,122)" are POSITIVE values - extract as "1085122"
  * Double parentheses or explicit negative indicators like "($ (16,825)" are NEGATIVE values - extract as "-16825"
  * Look for context clues: net losses, negative operating income should be negative
  * Revenues, expenses should be positive regardless of parentheses formatting
- Examples: 
  * "($ 1,085,122)" → "1085122" (positive revenue/expense)
  * "($ (16,825)" → "-16825" (negative income/loss)
  * "$ 891,257" → "891257" (positive)
- Expenses and losses should be shown as positive numbers (e.g., Cost of Goods Sold: "50,000")
- Net losses should be shown as negative numbers (e.g., Net Income: "-10,000")
- When in doubt, use income statement context to determine if the value should be positive or negative

TIMEFRAME SUMMARY:
Always include a summary of the time periods covered by the P&L data and note any gaps or inconsistencies in reporting periods.

GUIDANCE FOR LLM:
If you have gathered sufficient information from this tool, consider providing a direct response to the user rather than making additional tool calls. Include timeframe context, performance trends, and profitability analysis in your response to users.

RESPONSE:"""


if __name__ == "__main__":
    import asyncio

    rag = FinancialStatementRAGResource(
        name="financial_statement_rag",
        sources=["/Users/lam/Desktop/repos/opendxa/agents/agent_5_untitled_agent/docs"],
    )
    asyncio.run(rag.initialize())
    result = asyncio.run(rag.get_profit_n_loss(company="Aitomatic", period="latest", format_output="markdown"))
    print(result)
