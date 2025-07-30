"""
Financial Statement Tools Resource
Unified tools for financial statement analysis with session management and CSV export.
"""

import hashlib
import json
import logging
import os
import re
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.rag.financial_statement_rag_resource import (
    FinancialStatementRAGResource,
)
from dana.common.resource.coding.coding_resource import CodingResource
from dana.common.resource.financial_resources.prompts import (
    create_liquidity_ratios_prompt,
    create_leverage_ratios_prompt,
    create_efficiency_ratios_prompt,
    create_profitability_ratios_prompt,
    create_market_value_ratios_prompt,
)

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
        **kwargs,
    ):
        super().__init__(
            name,
            description or "Financial statement analysis tools with markdown export",
        )
        self.debug = debug
        self.sessions = {}  # session_id -> FinancialSession
        
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

    async def initialize(self) -> None:
        """Initialize the financial tools resource."""
        await super().initialize()
        await self.financial_rag.initialize()
        await self.coding_resource.initialize()
        
        if self.debug:
            logger.info(f"Financial statement tools [{self.name}] initialized")
            logger.info(f"Markdown output directory: {self.output_dir}")

    def _create_session(self, company: str) -> str:
        """Create a new analysis session."""
        session_id = f"fin_session_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = FinancialSession(session_id, company)
        return session_id

    def _get_session(self, session_id: str) -> Optional[FinancialSession]:
        """Retrieve an existing session."""
        return self.sessions.get(session_id)

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
        
        if self.debug:
            logger.info(f"Saved {statement_type} to markdown: {filepath}")
            
        return str(filepath)


    @ToolCallable.tool
    async def load_financial_data(
        self,
        company: str,
        periods: str = "latest",  # "latest", "2023", "Q1-Q4 2023"
        source: str = "rag",  # Currently only "rag" is implemented
    ) -> Dict[str, Any]:
        """@description Loads all financial statements (balance sheet, income statement, cash flow) for a company. MUST be called FIRST before any ratio analysis. Returns ready-to-use tool calls for financial analysis."""
        # Always include all three financial statements
        statements = ["balance_sheet", "income_statement", "cash_flow"]
        # Create new session
        session_id = self._create_session(company)
        session = self._get_session(session_id)
        
        if self.debug:
            print(f"\n[FinancialTools] Creating session {session_id} for {company}")
            print(f"[FinancialTools] Requested statements: {statements}")
            print(f"[FinancialTools] Period: {periods}")

        results = {
            "session_id": session_id,
            "company": company,
            "periods_requested": periods,
            "statements_loaded": [],
            "markdown_files": {},
            "errors": [],
            "summary": {},
        }

        # Map statement types to RAG methods
        statement_extractors = {
            "balance_sheet": self.financial_rag.get_balance_sheet,
            "income_statement": self.financial_rag.get_profit_n_loss,
            "cash_flow": self.financial_rag.get_cash_flow,
        }

        # Extract each requested statement
        for statement_type in statements:
            if statement_type not in statement_extractors:
                results["errors"].append(f"Unknown statement type: {statement_type}")
                continue

            try:
                if self.debug:
                    print(f"\n[FinancialTools] Extracting {statement_type}...")

                # Get the extraction method
                extractor = statement_extractors[statement_type]
                
                # Extract data using RAG
                extracted_data = await extractor(
                    company=company,
                    period=periods,
                    format_output="timeseries"  # Request structured format
                )

                # Store in session
                session.store_statement(statement_type, extracted_data)
                
                # Save to markdown file
                md_path = self._save_to_markdown(extracted_data, session, statement_type)
                
                results["statements_loaded"].append(statement_type)
                results["markdown_files"][statement_type] = md_path
                
                # Add summary info
                results["summary"][statement_type] = {
                    "length": len(extracted_data),
                    "markdown_path": md_path,
                }
                
                if self.debug:
                    print(f"[FinancialTools] {statement_type} extracted successfully")
                    print(f"[FinancialTools] Content length: {len(extracted_data)} characters")
                    print(f"[FinancialTools] Markdown saved to: {md_path}")

            except Exception as e:
                error_msg = f"Failed to extract {statement_type}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        # Set data quality indicator and create LLM-friendly guidance
        if len(results["statements_loaded"]) == len(statements):
            results["data_quality"] = "complete"
            
            # Create LLM-friendly file references
            bs_file = results["markdown_files"].get("balance_sheet", "")
            is_file = results["markdown_files"].get("income_statement", "")
            cf_file = results["markdown_files"].get("cash_flow", "")
            
            results["available_tools"] = {
                "liquidity_ratios": f"calculate_liquidity_ratios(bs_file='{bs_file}', company_name='{company}')",
                "leverage_ratios": f"calculate_leverage_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company}')",
                "efficiency_ratios": f"calculate_efficiency_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company}')",
                "profitability_ratios": f"calculate_profitability_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company}')",
                "market_value_ratios": f"calculate_market_value_ratios(bs_file='{bs_file}', is_file='{is_file}', company_name='{company}', market_data='')"
            }
            
            results["guidance"] = f"SUCCESS: All financial data loaded for {company}. Available files:\n" + \
                                f"• Balance Sheet: {bs_file}\n" + \
                                f"• Income Statement: {is_file}\n" + \
                                f"• Cash Flow: {cf_file}\n\n" + \
                                f"Use load_file(file_path='<path>') to read file contents, or use these ratio analysis tools:\n" + \
                                f"• Liquidity analysis: {results['available_tools']['liquidity_ratios']}\n" + \
                                f"• Leverage analysis: {results['available_tools']['leverage_ratios']}\n" + \
                                f"• Efficiency analysis: {results['available_tools']['efficiency_ratios']}\n" + \
                                f"• Profitability analysis: {results['available_tools']['profitability_ratios']}\n" + \
                                f"• Market valuation: {results['available_tools']['market_value_ratios']}"
                                
        elif len(results["statements_loaded"]) > 0:
            results["data_quality"] = "partial"
            missing = set(statements) - set(results["statements_loaded"])
            results["guidance"] = f"PARTIAL: Data loaded for {results['statements_loaded']}. Missing: {list(missing)}. Some ratio analyses may not be available."
        else:
            results["data_quality"] = "failed"
            results["guidance"] = "FAILED: No financial data could be loaded. Check company name and document availability."

        return results

    @ToolCallable.tool
    async def load_file(
        self,
        file_path: str,  # Path to the markdown file to load
    ) -> Dict[str, Any]:
        """@description Loads the content of a financial statement markdown file. Use this to read file contents before analysis or when you need to see the actual financial data."""
        if self.debug:
            print(f"\n[FinancialTools] Loading file: {file_path}")
            
        results = {
            "file_path": file_path,
            "errors": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            results["content"] = content
            results["content_length"] = len(content)
            results["loaded_successfully"] = True
            
            if self.debug:
                print(f"[FinancialTools] Successfully loaded {len(content)} characters from {file_path}")
                
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            results["errors"].append(error_msg)
            results["content"] = ""
            results["loaded_successfully"] = False
            logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to load file {file_path}: {str(e)}"
            results["errors"].append(error_msg)
            results["content"] = ""
            results["loaded_successfully"] = False
            logger.error(error_msg)
        
        return results

    @ToolCallable.tool
    async def calculate_liquidity_ratios(
        self,
        bs_file: str,  # Path to balance sheet markdown file
        company_name: str = "Company",  # Company name for context
    ) -> Dict[str, Any]:
        """@description Analyzes company's ability to pay short-term debts and cash position. Use when user asks about liquidity, cash flow, or financial health. Returns calculated ratios with numerical results."""
        if self.debug:
            print(f"\n[FinancialTools] Generating liquidity ratios code for {company_name}")
            print(f"[FinancialTools] Balance Sheet file: {bs_file}")
            
        results = {
            "data_sources": {
                "balance_sheet": bs_file
            },
            "company": company_name,
            "errors": []
        }
        
        # Read balance sheet content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading balance sheet file: {bs_file}")
                
            with open(bs_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(content)} characters from balance sheet")
                
        except Exception as e:
            error_msg = f"Failed to read balance sheet file {bs_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        if not content.strip():
            results["errors"].append("Balance sheet file is empty")
            return results
        
        # Create the prompt using our template and execute directly with CodingResource
        prompt = create_liquidity_ratios_prompt(content, company_name)
        
        if self.debug:
            print(f"[FinancialTools] Generated prompt length: {len(prompt)} characters")
            print("[FinancialTools] Executing liquidity ratios calculation with CodingResource...")
        
        # Use CodingResource to generate AND execute Python code in one step
        try:
            execution_result = await self.coding_resource.execute_code(prompt)
            
            results["execution_result"] = execution_result
            results["executed_successfully"] = not execution_result.startswith("Error:") and not execution_result.startswith("Failed")
            
            if self.debug:
                print(f"[FinancialTools] Code execution result:")
                print(execution_result)
                
        except Exception as e:
            error_msg = f"Failed to execute liquidity ratios calculation: {str(e)}"
            results["errors"].append(error_msg)
            results["execution_result"] = error_msg
            results["executed_successfully"] = False
            logger.error(error_msg)
        
        return results

    @ToolCallable.tool
    async def calculate_leverage_ratios(
        self,
        bs_file: str,  # Path to balance sheet markdown file
        is_file: str,  # Path to income statement markdown file
        company_name: str = "Company",  # Company name for context
    ) -> Dict[str, Any]:
        """@description Analyzes company's debt levels and financial leverage using balance sheet and income statement. Use when user asks about debt, leverage, or financial risk. Returns calculated ratios with numerical results."""
        if self.debug:
            print(f"\n[FinancialTools] Generating leverage ratios code for {company_name}")
            print(f"[FinancialTools] Balance Sheet file: {bs_file}")
            print(f"[FinancialTools] Income Statement file: {is_file}")
            
        results = {
            "data_sources": {
                "balance_sheet": bs_file,
                "income_statement": is_file
            },
            "company": company_name,
            "errors": []
        }
        
        # Read balance sheet content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading balance sheet file: {bs_file}")
                
            with open(bs_file, 'r', encoding='utf-8') as f:
                bs_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(bs_content)} characters from balance sheet")
                
        except Exception as e:
            error_msg = f"Failed to read balance sheet file {bs_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        # Read income statement content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading income statement file: {is_file}")
                
            with open(is_file, 'r', encoding='utf-8') as f:
                is_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(is_content)} characters from income statement")
                
        except Exception as e:
            error_msg = f"Failed to read income statement file {is_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        if not bs_content.strip():
            results["errors"].append("Balance sheet file is empty")
            return results
            
        if not is_content.strip():
            results["errors"].append("Income statement file is empty")
            return results
        
        # Create the prompt using our template and execute directly with CodingResource
        prompt = create_leverage_ratios_prompt(bs_content, is_content, company_name)
        
        if self.debug:
            print(f"[FinancialTools] Generated prompt length: {len(prompt)} characters")
            print("[FinancialTools] Executing leverage ratios calculation with CodingResource...")
        
        # Use CodingResource to generate AND execute Python code in one step
        try:
            execution_result = await self.coding_resource.execute_code(prompt)
            
            results["execution_result"] = execution_result
            results["executed_successfully"] = not execution_result.startswith("Error:") and not execution_result.startswith("Failed")
            
            if self.debug:
                print(f"[FinancialTools] Code execution result:")
                print(execution_result)
                
        except Exception as e:
            error_msg = f"Failed to execute leverage ratios calculation: {str(e)}"
            results["errors"].append(error_msg)
            results["execution_result"] = error_msg
            results["executed_successfully"] = False
            logger.error(error_msg)
        
        return results

    @ToolCallable.tool
    async def calculate_efficiency_ratios(
        self,
        bs_file: str,  # Path to balance sheet markdown file
        is_file: str,  # Path to income statement markdown file
        company_name: str = "Company",  # Company name for context
    ) -> Dict[str, Any]:
        """@description Analyzes how efficiently company uses assets to generate revenue. Use when user asks about asset utilization, turnover ratios, or operational efficiency. Returns calculated ratios with numerical results."""
        if self.debug:
            print(f"\n[FinancialTools] Generating efficiency ratios code for {company_name}")
            print(f"[FinancialTools] Balance Sheet file: {bs_file}")
            print(f"[FinancialTools] Income Statement file: {is_file}")
            
        results = {
            "data_sources": {
                "balance_sheet": bs_file,
                "income_statement": is_file
            },
            "company": company_name,
            "errors": []
        }
        
        # Read balance sheet content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading balance sheet file: {bs_file}")
                
            with open(bs_file, 'r', encoding='utf-8') as f:
                bs_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(bs_content)} characters from balance sheet")
                
        except Exception as e:
            error_msg = f"Failed to read balance sheet file {bs_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        # Read income statement content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading income statement file: {is_file}")
                
            with open(is_file, 'r', encoding='utf-8') as f:
                is_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(is_content)} characters from income statement")
                
        except Exception as e:
            error_msg = f"Failed to read income statement file {is_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        if not bs_content.strip():
            results["errors"].append("Balance sheet file is empty")
            return results
            
        if not is_content.strip():
            results["errors"].append("Income statement file is empty")
            return results
        
        # Create the prompt using our template and execute directly with CodingResource
        prompt = create_efficiency_ratios_prompt(bs_content, is_content, company_name)
        
        if self.debug:
            print(f"[FinancialTools] Generated prompt length: {len(prompt)} characters")
            print("[FinancialTools] Executing efficiency ratios calculation with CodingResource...")
        
        # Use CodingResource to generate AND execute Python code in one step
        try:
            execution_result = await self.coding_resource.execute_code(prompt)
            
            results["execution_result"] = execution_result
            results["executed_successfully"] = not execution_result.startswith("Error:") and not execution_result.startswith("Failed")
            
            if self.debug:
                print(f"[FinancialTools] Code execution result:")
                print(execution_result)
                
        except Exception as e:
            error_msg = f"Failed to execute efficiency ratios calculation: {str(e)}"
            results["errors"].append(error_msg)
            results["execution_result"] = error_msg
            results["executed_successfully"] = False
            logger.error(error_msg)
        
        return results

    @ToolCallable.tool
    async def calculate_profitability_ratios(
        self,
        bs_file: str,  # Path to balance sheet markdown file
        is_file: str,  # Path to income statement markdown file
        company_name: str = "Company",  # Company name for context
    ) -> Dict[str, Any]:
        """@description Analyzes company's ability to generate profits from operations and investments. Use when user asks about margins, returns, ROA, ROE, or profitability. Returns calculated ratios with numerical results."""
        if self.debug:
            print(f"\n[FinancialTools] Generating profitability ratios code for {company_name}")
            print(f"[FinancialTools] Balance Sheet file: {bs_file}")
            print(f"[FinancialTools] Income Statement file: {is_file}")
            
        results = {
            "data_sources": {
                "balance_sheet": bs_file,
                "income_statement": is_file
            },
            "company": company_name,
            "errors": []
        }
        
        # Read balance sheet content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading balance sheet file: {bs_file}")
                
            with open(bs_file, 'r', encoding='utf-8') as f:
                bs_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(bs_content)} characters from balance sheet")
                
        except Exception as e:
            error_msg = f"Failed to read balance sheet file {bs_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        # Read income statement content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading income statement file: {is_file}")
                
            with open(is_file, 'r', encoding='utf-8') as f:
                is_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(is_content)} characters from income statement")
                
        except Exception as e:
            error_msg = f"Failed to read income statement file {is_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        if not bs_content.strip():
            results["errors"].append("Balance sheet file is empty")
            return results
            
        if not is_content.strip():
            results["errors"].append("Income statement file is empty")
            return results
        
        # Create the prompt using our template and execute directly with CodingResource
        prompt = create_profitability_ratios_prompt(bs_content, is_content, company_name)
        
        if self.debug:
            print(f"[FinancialTools] Generated prompt length: {len(prompt)} characters")
            print("[FinancialTools] Executing profitability ratios calculation with CodingResource...")
        
        # Use CodingResource to generate AND execute Python code in one step
        try:
            execution_result = await self.coding_resource.execute_code(prompt)
            
            results["execution_result"] = execution_result
            results["executed_successfully"] = not execution_result.startswith("Error:") and not execution_result.startswith("Failed")
            
            if self.debug:
                print(f"[FinancialTools] Code execution result:")
                print(execution_result)
                
        except Exception as e:
            error_msg = f"Failed to execute profitability ratios calculation: {str(e)}"
            results["errors"].append(error_msg)
            results["execution_result"] = error_msg
            results["executed_successfully"] = False
            logger.error(error_msg)
        
        return results

    @ToolCallable.tool
    async def calculate_market_value_ratios(
        self,
        bs_file: str,  # Path to balance sheet markdown file
        is_file: str,  # Path to income statement markdown file
        company_name: str = "Company",  # Company name for context
        market_data: str = "",  # Optional market data (stock price, shares, market cap)
    ) -> Dict[str, Any]:
        """@description Analyzes company's market valuation relative to financial metrics. Use when user asks about P/E, P/B, market multiples, or stock valuation. Returns calculated ratios with numerical results."""
        if self.debug:
            print(f"\n[FinancialTools] Generating market value ratios code for {company_name}")
            print(f"[FinancialTools] Balance Sheet file: {bs_file}")
            print(f"[FinancialTools] Income Statement file: {is_file}")
            print(f"[FinancialTools] Market data provided: {'Yes' if market_data.strip() else 'No'}")
            
        results = {
            "data_sources": {
                "balance_sheet": bs_file,
                "income_statement": is_file,
                "market_data": "provided" if market_data.strip() else "not_provided"
            },
            "company": company_name,
            "errors": []
        }
        
        # Read balance sheet content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading balance sheet file: {bs_file}")
                
            with open(bs_file, 'r', encoding='utf-8') as f:
                bs_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(bs_content)} characters from balance sheet")
                
        except Exception as e:
            error_msg = f"Failed to read balance sheet file {bs_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        # Read income statement content
        try:
            if self.debug:
                print(f"[FinancialTools] Reading income statement file: {is_file}")
                
            with open(is_file, 'r', encoding='utf-8') as f:
                is_content = f.read()
            
            if self.debug:
                print(f"[FinancialTools] Read {len(is_content)} characters from income statement")
                
        except Exception as e:
            error_msg = f"Failed to read income statement file {is_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results
        
        if not bs_content.strip():
            results["errors"].append("Balance sheet file is empty")
            return results
            
        if not is_content.strip():
            results["errors"].append("Income statement file is empty")
            return results
        
        # Create the prompt using our template and execute directly with CodingResource
        prompt = create_market_value_ratios_prompt(bs_content, is_content, company_name, market_data)
        
        if self.debug:
            print(f"[FinancialTools] Generated prompt length: {len(prompt)} characters")
            print("[FinancialTools] Executing market value ratios calculation with CodingResource...")
        
        # Use CodingResource to generate AND execute Python code in one step
        try:
            execution_result = await self.coding_resource.execute_code(prompt)
            
            results["execution_result"] = execution_result
            results["executed_successfully"] = not execution_result.startswith("Error:") and not execution_result.startswith("Failed")
            
            if self.debug:
                print(f"[FinancialTools] Code execution result:")
                print(execution_result)
                
        except Exception as e:
            error_msg = f"Failed to execute market value ratios calculation: {str(e)}"
            results["errors"].append(error_msg)
            results["execution_result"] = error_msg
            results["executed_successfully"] = False
            logger.error(error_msg)
        
        return results

    
    async def get_session_info(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get information about a session and its available data."""
        session = self._get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}

        return {
            "session_id": session_id,
            "company": session.company,
            "created_at": session.created_at.isoformat(),
            "available_statements": list(session.financial_data.keys()),
            "output_files": session.output_files,
            "metadata": session.metadata,
        }

    @ToolCallable.tool
    async def list_sessions(self) -> Dict[str, Any]:
        """List all available sessions."""
        sessions_info = []
        for session_id, session in self.sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "company": session.company,
                "created_at": session.created_at.isoformat(),
                "statements": list(session.financial_data.keys()),
            })
        
        return {
            "total_sessions": len(sessions_info),
            "sessions": sessions_info,
        }
    
if __name__ == "__main__":
    import asyncio
    finance_resource = FinancialStatementTools(description="Financial statement analysis tools with CSV export", debug=True, 
                                               sources=["/Users/lam/Desktop/repos/opendxa/agents/agent_5_untitled_agent/docs"])
    asyncio.run(finance_resource.initialize())
    # Test the improved load_financial_data output
    result = asyncio.run(finance_resource.load_financial_data(company="Aitomatic", periods="latest", source="rag"))
    print("=== load_financial_data output ===")
    print(f"Data quality: {result.get('data_quality')}")
    print(f"Guidance: {result.get('guidance')}")
    if 'available_tools' in result:
        print("\nAvailable tools:")
        for tool_name, tool_call in result['available_tools'].items():
            print(f"  {tool_name}: {tool_call}")
    print("="*50)
    
    # Test load_file tool with one of the generated files
    if result.get('data_quality') == 'complete' and 'markdown_files' in result:
        bs_file = result['markdown_files'].get('balance_sheet')
        if bs_file:
            print(f"\n=== Testing load_file with balance sheet ===")
            file_result = asyncio.run(finance_resource.load_file(file_path=bs_file))
            print(f"File loaded: {file_result.get('loaded_successfully')}")
            print(f"Content length: {file_result.get('content_length')} characters")
            if file_result.get('content'):
                # Show first 500 characters as preview
                preview = file_result['content'][:500] + "..." if len(file_result['content']) > 500 else file_result['content']
                print(f"Content preview:\n{preview}")
            print("="*50)
    
    # Test liquidity ratios
    # result = asyncio.run(finance_resource.calculate_liquidity_ratios(bs_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_balance_sheet_20250730_213444.md", company_name="Aitomatic"))
    # print(result)
    
    # Test leverage ratios
    # result = asyncio.run(finance_resource.calculate_leverage_ratios(
    #     bs_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_balance_sheet_20250730_212350.md", 
    #     is_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_income_statement_20250730_212419.md",
    #     company_name="Aitomatic"
    # ))
    # print(result)
    
    # Test efficiency ratios
    # result = asyncio.run(finance_resource.calculate_efficiency_ratios(
    #     bs_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_balance_sheet_20250730_212350.md", 
    #     is_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_income_statement_20250730_212419.md",
    #     company_name="Aitomatic"
    # ))
    # print(result)
    
    # Test profitability ratios
    # result = asyncio.run(finance_resource.calculate_profitability_ratios(
    #     bs_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_balance_sheet_20250730_212350.md", 
    #     is_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_income_statement_20250730_212419.md",
    #     company_name="Aitomatic"
    # ))
    # print(result)
    
    # Test market value ratios (without market data)
    # result = asyncio.run(finance_resource.calculate_market_value_ratios(
    #     bs_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_balance_sheet_20250730_212350.md", 
    #     is_file="/var/folders/v8/1y4wbb0942nb4fv3wjf5rm5m0000gn/T/financial_analysis/Aitomatic_income_statement_20250730_212419.md",
    #     company_name="Aitomatic",
    #     market_data=""  # No market data provided - will show per-share metrics and N/A for market ratios
    # ))
    # print(result)