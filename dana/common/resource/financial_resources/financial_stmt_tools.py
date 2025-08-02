"""
Financial Statement Tools Resource
Unified tools for financial statement analysis with session management and CSV export.
"""

import hashlib
import json
import logging
import re
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import os


from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.rag.financial_statement_rag_resource import (
    FinancialStatementRAGResource,
)
from dana.common.resource.coding.coding_resource import CodingResource
# from dana.common.resource.financial_resources.prompts import (
#     create_liquidity_ratios_prompt,
#     create_leverage_ratios_prompt,
#     create_efficiency_ratios_prompt,
#     create_profitability_ratios_prompt,
#     create_market_value_ratios_prompt,
# )

logger = logging.getLogger(__name__)


class FinancialSession:
    """Manages state for a financial analysis session."""

    def __init__(self, session_id: str, company: str):
        self.session_id = session_id
        self.company = company
        self.created_at = datetime.now()
        self.financial_data = {}
        self.output_files = {}
        self.metadata = {
            "company": company,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.created_at.isoformat(),
        }

    def store_statement(self, statement_type: str, data: Any) -> None:
        """Store financial statement data."""
        self.financial_data[statement_type] = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self.metadata["last_updated"] = datetime.now().isoformat()

    def get_statement(self, statement_type: str) -> Optional[Any]:
        """Retrieve stored financial statement data."""
        if statement_type in self.financial_data:
            return self.financial_data[statement_type]["data"]
        return None

    def add_output_file(self, statement_type: str, file_path: str) -> None:
        """Track output file created for a statement."""
        self.output_files[statement_type] = file_path


class FinancialStatementTools(BaseResource):
    """Unified financial statement analysis tools with session management."""

    def __init__(
        self,
        name: str = "financial_stmt_tools",
        description: str | None = None,
        debug: bool = True,
        output_dir: str = None,
        finance_rag: FinancialStatementRAGResource | None = None,
        company: str = "default",  # Company name for this instance
        **kwargs,
    ):
        super().__init__(
            name,
            description or "Financial statement analysis tools with markdown export",
        )
        self.debug = debug
        self.company = company
        self.cache = {}  # In-memory cache: company -> cached_data
        
        # Set output directory for markdown files
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(tempfile.gettempdir()) / "financial_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the RAG resource for financial statement extraction
        self.financial_rag = finance_rag or FinancialStatementRAGResource(
            name=f"{name}_rag",
            debug=debug,
            **kwargs,
        )
        
        # Initialize CodingResource for generating and executing code
        self.coding_resource = CodingResource(
            name=f"{name}_coding",
            debug=debug,
            **kwargs,
        )
        
        # Initialize session for this company
        self.session = FinancialSession(f"session_{company}", company)

    async def initialize(self) -> None:
        """Initialize the financial tools resource."""
        await super().initialize()
        await self.financial_rag.initialize()
        await self.coding_resource.initialize()
        
        # Initialization logging removed for brevity

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Retrieve data from cache."""
        cached_data = self.cache.get(cache_key)
        if cached_data:
            if self.debug:
                print(f"CACHE HIT: {cache_key}")
            return cached_data
        if self.debug:
            print(f"CACHE MISS: {cache_key}")
        return None

    def _store_in_cache(self, cache_key: str, data: Any) -> None:
        """Store data in cache."""
        self.cache[cache_key] = data
        # Cache storage logging removed for brevity

    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cached data."""
        cache_size = len(self.cache)
        self.cache.clear()
        return {
            "cache_cleared": True,
            "entries_removed": cache_size,
            "message": f"Cleared {cache_size} cache entries"
        }

    async def _execute_ratio_calculation_with_cache(
        self, 
        ratio_type: str, 
        prompt_generator, 
        bs_file: str, 
        is_file: str = "", 
        company_name: str = "Company", 
        market_data: str = ""
    ) -> str:
        """Execute ratio calculation with caching support."""
        # Simple cache key using company and ratio type
        cache_key = f"{self.company}_{ratio_type}"
        
        # Cache check logging removed for brevity
        
        # Try to get from cache first
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            # Use cached results
            # Using cached results
            return cached_result
        
        # Execute fresh calculation
        # Executing fresh calculation
        
        # Read file contents
        try:
            # Read balance sheet if provided
            bs_content = ""
            if bs_file:
                with open(bs_file, 'r', encoding='utf-8') as f:
                    bs_content = f.read()
                # File read successful
            
            # Read income statement if provided  
            is_content = ""
            if is_file:
                with open(is_file, 'r', encoding='utf-8') as f:
                    is_content = f.read()
                # File read successful
            
            # Check if files are empty
            if bs_file and not bs_content.strip():
                return "Error: Balance sheet file is empty"
            if is_file and not is_content.strip():
                return "Error: Income statement file is empty"
                
        except Exception as e:
            error_msg = f"Failed to read financial statement files: {str(e)}"
            logger.error(error_msg)
            return error_msg
        
        # Generate prompt using the provided generator function
        if market_data:
            prompt = prompt_generator(bs_content, is_content, company_name, market_data)
        elif is_content:
            prompt = prompt_generator(bs_content, is_content, company_name)
        else:
            prompt = prompt_generator(bs_content, company_name)
        
        # Executing calculation
        
        # Use CodingResource to generate AND execute Python code
        try:
            execution_result = await self.coding_resource.execute_code(prompt)
            
            is_successful = not execution_result.startswith("Error:") and not execution_result.startswith("Failed")
            
            # Calculation completed
            
            # Cache the results if successful
            if is_successful:
                self._store_in_cache(cache_key, execution_result)
                # Results cached
                
            # Return the text output directly
            return execution_result
                
        except Exception as e:
            error_msg = f"Failed to execute {ratio_type} calculation: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _save_to_markdown(self, statement_data: str, session: FinancialSession, statement_type: str) -> str:
        """Save financial statement data to markdown file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session.company}_{statement_type}_{timestamp}.md"
        filepath = self.output_dir / filename
        
        # Create markdown content with header
        markdown_content = f"# {statement_type.replace('_', ' ').title()}\n"
        markdown_content += f"**Company:** {session.company}\n"
        markdown_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content += "---\n\n"
        markdown_content += statement_data
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        session.add_output_file(statement_type, str(filepath))
        
        # File saved
            
        return str(filepath)


    @ToolCallable.tool
    async def load_financial_data(
        self,
        company: str = None,  # Optional - uses instance company if not provided
        periods: str = "latest",  # "latest", "2023", "Q1-Q4 2023"
        source: str = "rag",  # Currently only "rag" is implemented
    ) -> str:
        """@description: Loads all financial statements (balance sheet, income statement, cash flow) for a company. MUST be called FIRST before any ratio analysis. Returns ready-to-use tool calls for financial analysis."""
        # Use instance company if not provided
        if not company:
            company = self.company
            
        # Always include all three financial statements
        statements = ["balance_sheet", "income_statement", "cash_flow"]
        session = self.session
        
        if self.debug:
            print(f"\nCALL: load_financial_data(company='{company}', periods='{periods}', source='{source}')")

        markdown_files = {}
        statements_loaded = []
        errors = []

        # Map statement types to RAG methods
        statement_extractors = {
            "balance_sheet": self.financial_rag.get_balance_sheet,
            "income_statement": self.financial_rag.get_profit_n_loss,
            "cash_flow": self.financial_rag.get_cash_flow,
        }

        # Extract each requested statement
        for statement_type in statements:
            if statement_type not in statement_extractors:
                errors.append(f"Unknown statement type: {statement_type}")
                continue

            try:
                # Processing statement

                # Simple cache key
                cache_key = f"{company}_{statement_type}"
                
                # Try to get from cache first
                cached_data = self._get_from_cache(cache_key)
                
                if cached_data:
                    # Use cached data
                    extracted_data = cached_data["extracted_data"]
                    md_path = cached_data["md_path"]
                    
                    # Store in session
                    session.store_statement(statement_type, extracted_data)
                    
                    # Using cached data
                else:
                    # Extract fresh data using RAG
                    # Extracting fresh data
                    
                    extractor = statement_extractors[statement_type]
                    extracted_data = await extractor(
                        company=company,
                        period=periods,
                        format_output="timeseries"  # Request structured format
                    )

                    # Store in session
                    session.store_statement(statement_type, extracted_data)
                    
                    # Save to markdown file
                    md_path = self._save_to_markdown(extracted_data, session, statement_type)
                    
                    # Cache the results
                    cache_data = {
                        "extracted_data": extracted_data,
                        "md_path": md_path
                    }
                    self._store_in_cache(cache_key, cache_data)
                    
                    # Data extracted and cached
                
                statements_loaded.append(statement_type)
                markdown_files[statement_type] = md_path

            except Exception as e:
                error_msg = f"Failed to extract {statement_type}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Create markdown output for LLM consumption
        if len(statements_loaded) == len(statements):
            # Success - all data loaded
            bs_file = markdown_files.get("balance_sheet", "")
            is_file = markdown_files.get("income_statement", "")
            cf_file = markdown_files.get("cash_flow", "")
            
            markdown_output = f"""# Financial Data Loading Results ✅

**Company:** {company}  
**Status:** SUCCESS - All financial statements loaded  

## Available Financial Statements

| Statement Type | File Path |
|----------------|-----------|
| Balance Sheet | `{bs_file}` |
| Income Statement | `{is_file}` |
| Cash Flow | `{cf_file}` |

### 📄 File Access
To read the actual financial statement content:
```python
load_file(file_path='{bs_file}')  # Load balance sheet content
load_file(file_path='{is_file}')  # Load income statement content  
load_file(file_path='{cf_file}')  # Load cash flow content
```

## Summary
- ✅ All required financial data successfully loaded
- 🎯 Ready for comprehensive financial analysis
- ⚡ Cached results available for faster subsequent access
"""
            
        elif len(statements_loaded) > 0:
            # Partial success
            missing = list(set(statements) - set(statements_loaded))
            loaded_files = []
            
            for stmt_type in statements_loaded:
                file_path = markdown_files.get(stmt_type, "")
                loaded_files.append(f"- **{stmt_type.replace('_', ' ').title()}**: `{file_path}`")
            
            markdown_output = f"""# Financial Data Loading Results ⚠️

**Company:** {company}  
**Status:** PARTIAL - Some data missing  

## ✅ Successfully Loaded
{chr(10).join(loaded_files)}

## ❌ Missing Statements
{chr(10).join([f"- {stmt.replace('_', ' ').title()}" for stmt in missing])}

## ⚠️ Impact
Some financial ratio analyses may not be available due to missing data.

## Next Steps
- Check if missing statements exist in source documents
- Use available statements for partial analysis
- Consider re-running with different period parameters
"""
            
        else:
            # Complete failure
            error_list = "\n".join([f"- {error}" for error in errors]) if errors else "- Unknown error occurred"
            
            markdown_output = f"""# Financial Data Loading Results ❌

**Company:** {company}  
**Status:** FAILED - No data could be loaded  

## 🚫 Errors Encountered
{error_list}

## 🔧 Troubleshooting Steps
1. **Verify company name** - Check spelling and exact name format
2. **Check document availability** - Ensure financial documents exist in source
3. **Try different periods** - Use 'latest', specific year like '2023', or quarters like 'Q1-Q4 2023'
4. **Verify data source** - Confirm RAG system has access to company documents

## 📞 Support
If issues persist, check the document sources and RAG configuration.
"""

        return markdown_output

    async def get_cache_info(self) -> Dict[str, Any]:
        """@description: Shows cache statistics and information. Use to check cache performance and manage cached data."""
        return {
            "company": self.company,
            "cache_entries_count": len(self.cache),
            "cache_keys": list(self.cache.keys()),
            "cache_enabled": True,
            "actions": {
                "clear_cache": "Use clear_cache() to remove all cached data"
            }
        }

    @ToolCallable.tool
    async def load_file(
        self,
        file_path: str,  # Path to the markdown file to load
    ) -> str:
        """@description: Loads the content of a financial statement markdown file. Use this to read file contents before analysis or when you need to see the actual financial data."""
        if self.debug:
            print(f"\nCALL: load_file(file_path='{file_path}')")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if self.debug:
                print(f"RESPONSE: Loaded {len(content)} characters")
            
            return f'Content of `{file_path}` : \n {content}'
                
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"Failed to load file {file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg

    # @ToolCallable.tool
    # async def calculate_liquidity_ratios(
    #     self,
    #     bs_file: str,  # Path to balance sheet markdown file
    #     company_name: str = "Company",  # Company name for context
    # ) -> str:
    #     """@description: Calculates 12 liquidity ratios including Current Ratio, Quick Ratio, Cash Ratio, Working Capital, Super Quick Ratio, Cash Coverage, Operating CF Ratio, Net WC Ratio, Current Assets Ratio, Liquid Assets Ratio, Receivables Liquidity, and Inventory to WC. Use for analyzing short-term financial health, cash position, or ability to meet obligations."""
    #     if self.debug:
    #         print(f"\nCALL: calculate_liquidity_ratios(bs_file='{bs_file}', company_name='{company_name}')")
    #     result = await self._execute_ratio_calculation_with_cache(
    #         ratio_type="liquidity_ratios",
    #         prompt_generator=create_liquidity_ratios_prompt,
    #         bs_file=bs_file,
    #         company_name=company_name
    #     )
    #     if self.debug:
    #         cached = "CACHED" if self._get_from_cache(f"{self.company}_liquidity_ratios") is not None else "FRESH"
    #         print(f"RESPONSE: {cached} - {len(result)} characters")
    #     return result

    # @ToolCallable.tool
    # async def calculate_leverage_ratios(
    #     self,
    #     bs_file: str,  # Path to balance sheet markdown file
    #     is_file: str,  # Path to income statement markdown file
    #     company_name: str = "Company",  # Company name for context
    # ) -> str:
    #     """@description: Calculates 10 leverage ratios including Debt-to-Equity, Debt-to-Assets, Equity Ratio, LT Debt-to-Equity, Interest Coverage, Times Interest Earned, Equity Multiplier, LT Debt-to-Capital, Asset Coverage, and Financial Leverage. Use for analyzing debt levels, financial risk, or capital structure."""
    #     if self.debug:
    #         print(f"\nCALL: calculate_leverage_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company_name}')")
    #     result = await self._execute_ratio_calculation_with_cache(
    #         ratio_type="leverage_ratios",
    #         prompt_generator=create_leverage_ratios_prompt,
    #         bs_file=bs_file,
    #         is_file=is_file,
    #         company_name=company_name
    #     )
    #     if self.debug:
    #         cached = "CACHED" if self._get_from_cache(f"{self.company}_leverage_ratios") is not None else "FRESH"
    #         print(f"RESPONSE: {cached} - {len(result)} characters")
    #     return result

    # @ToolCallable.tool
    # async def calculate_efficiency_ratios(
    #     self,
    #     bs_file: str,  # Path to balance sheet markdown file
    #     is_file: str,  # Path to income statement markdown file
    #     company_name: str = "Company",  # Company name for context
    # ) -> str:
    #     """@description: Calculates 12 efficiency ratios including Asset Turnover, Fixed Asset Turnover, Current Asset Turnover, Inventory Turnover, Days Sales in Inventory, Receivables Turnover, Days Sales Outstanding, Payables Turnover, Days Payable Outstanding, Working Capital Turnover, and Cash Conversion Cycle. Use for analyzing operational efficiency or asset utilization."""
    #     if self.debug:
    #         print(f"\nCALL: calculate_efficiency_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company_name}')")
    #     result = await self._execute_ratio_calculation_with_cache(
    #         ratio_type="efficiency_ratios",
    #         prompt_generator=create_efficiency_ratios_prompt,
    #         bs_file=bs_file,
    #         is_file=is_file,
    #         company_name=company_name
    #     )
    #     if self.debug:
    #         cached = "CACHED" if self._get_from_cache(f"{self.company}_efficiency_ratios") is not None else "FRESH"
    #         print(f"RESPONSE: {cached} - {len(result)} characters")
    #     return result

    # @ToolCallable.tool
    # async def calculate_profitability_ratios(
    #     self,
    #     bs_file: str,  # Path to balance sheet markdown file
    #     is_file: str,  # Path to income statement markdown file
    #     company_name: str = "Company",  # Company name for context
    # ) -> str:
    #     """@description: Calculates 12 profitability ratios including Gross Margin, Operating Margin, Net Margin, EBITDA Margin, ROA (Return on Assets), ROE (Return on Equity), ROIC (Return on Invested Capital), ROCE (Return on Capital Employed), Asset Turnover, Equity Multiplier, Financial Leverage, and DuPont ROE. Use for analyzing profit margins, returns, or overall profitability."""
    #     if self.debug:
    #         print(f"\nCALL: calculate_profitability_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company_name}')")
    #     result = await self._execute_ratio_calculation_with_cache(
    #         ratio_type="profitability_ratios",
    #         prompt_generator=create_profitability_ratios_prompt,
    #         bs_file=bs_file,
    #         is_file=is_file,
    #         company_name=company_name
    #     )
    #     if self.debug:
    #         cached = "CACHED" if self._get_from_cache(f"{self.company}_profitability_ratios") is not None else "FRESH"
    #         print(f"RESPONSE: {cached} - {len(result)} characters")
    #     return result

    # @ToolCallable.tool
    # async def calculate_market_value_ratios(
    #     self,
    #     bs_file: str,  # Path to balance sheet markdown file
    #     is_file: str,  # Path to income statement markdown file
    #     company_name: str = "Company",  # Company name for context
    #     market_data: str = "",  # Optional market data (stock price, shares, market cap)
    # ) -> str:
    #     """@description: Calculates 12 market value ratios including EPS, Book Value per Share, Revenue per Share, Cash Flow per Share, P/E Ratio, P/B Ratio, P/S Ratio, P/CF Ratio, Market-to-Book, Enterprise Value, EV/Revenue, and EV/EBITDA. Use for analyzing stock valuation, market multiples, or investment metrics. Requires market data for full analysis."""
    #     if self.debug:
    #         print(f"\nCALL: calculate_market_value_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company_name}', market_data='{market_data[:50]}...')")
    #     result = await self._execute_ratio_calculation_with_cache(
    #         ratio_type="market_value_ratios",
    #         prompt_generator=create_market_value_ratios_prompt,
    #         bs_file=bs_file,
    #         is_file=is_file,
    #         company_name=company_name,
    #         market_data=market_data
    #     )
    #     if self.debug:
    #         cached = "CACHED" if self._get_from_cache(f"{self.company}_market_value_ratios") is not None else "FRESH"
    #         print(f"RESPONSE: {cached} - {len(result)} characters")
    #     return result

    async def query(self, query : str) -> str:
        pass
    
if __name__ == "__main__":
    import asyncio
    finance_resource = FinancialStatementTools(
        description="Financial statement analysis tools with simplified caching", 
        debug=True,
        company="Aitomatic",
        sources=["/Users/lam/Desktop/repos/opendxa/agents/agent_5_untitled_agent/docs"]
    )
    asyncio.run(finance_resource.initialize())
    
    # Test the simplified interface
    # print("=== First call (should cache data) ===")
    # markdown_result1 = asyncio.run(finance_resource.load_financial_data(periods="latest"))
    # print("MARKDOWN OUTPUT:")
    # print(markdown_result1)
    
    # print("\n=== Cache info after first call ===")
    # cache_info = asyncio.run(finance_resource.get_cache_info())
    # print(f"Company: {cache_info.get('company')}")
    # print(f"Cache entries: {cache_info.get('cache_entries_count')}")
    # print(f"Cache keys: {cache_info.get('cache_keys')}")
    
    # print("\n=== Second call (should use cache) ===")
    # markdown_result2 = asyncio.run(finance_resource.create_financial_forecast(
    #     forecast_request="Grow revenue by 20% annually, maintain 40% gross margin, and reduce operating expenses by 10% annually.", 
    #     bs_file="agents/financial_stmt_analysis/docs/[FI] FY21-25 Aitomatic Financials - FY24 BS.md",
    #     is_file="agents/financial_stmt_analysis/docs/[FI] FY21-25 Aitomatic Financials - FY24 P&L.md",
    #     cf_file="agents/financial_stmt_analysis/docs/[FI] FY21-25 Aitomatic Financials - FY24 CF.md"))
    # print("MARKDOWN OUTPUT (should use cached data):")
    # print(markdown_result2)
