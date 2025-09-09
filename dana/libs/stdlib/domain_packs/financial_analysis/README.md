# Financial-Analysis Domain Expertise Module / Domain Knowledge Pack

This directory contains a comprehensive suite of Dana (`.na`) code examples and utilities for financial statement analysis and financial ratio workflows. The examples are organized to demonstrate how to extract, compute, and analyze key financial metrics from company financial statements using the Dana language.

## Structure and Contents

- **Core Financial Statement Modules (`fin_statements/`)**
  - `bal_sheet.na`, `income.na`, `cash_flow.na`:
    Dana modules for extracting items from the Balance Sheet, Income Statement, and Cash Flow Statement, respectively.
    Each provides functions to query values (e.g., total assets, revenue, operating cash flow) for a given company, period, and currency.
  - `utils/`:
    Utility code for querying and structuring financial data, including type definitions and helper functions.

- **Financial Ratio and Metric Workflows**
  - `leverage.na`, `liquidity.na`, `cap_intens.na`, `margin_ratios.na`, `turnover_ratios.na`, `return_ratios.na`, `income_util_ratios.na`, `adj_income.na`:
    Each file implements calculations for a specific class of financial ratios or metrics, such as leverage (debt/equity), liquidity, capital intensity, profit margins, turnover, returns, income utilization, and adjusted income measures (EBITDA).
  - These modules use the core statement extractors to compute ratios according to standard financial formulas.
  - **Workflow Composition**: The modules demonstrate Dana's workflow composition syntax using pipe (`|`) and parallel execution (`[]`) operators for building complex financial analysis pipelines.

- **Test and Example Scripts**
  - `tests.na`:
    Main test harness for running and validating the extraction and calculation functions across the modules.
  - `docs/`:
    Contains sample financial statement documents (e.g., `AMD_2022_10K.pdf`, `VERIZON_2022_10K.pdf`, `CVSHEALTH_2022_10K.pdf`) used as data sources for the tests.

## How to Use

- Review the test script (`tests.na`) for examples of how to invoke each workflow.
- **Try the Workflows**: Run `use_fin_analysis_workflows.na` (located in the parent directory) to see the financial analysis workflows in action. This script treats `financial_analysis/` as an importable package and demonstrates capital intensity and liquidity assessments across multiple companies.
- The modules are designed to be composable: you can import and combine them to build custom financial analysis pipelines using Dana's workflow composition syntax.
- Utilities in `utils/` help with querying and formatting data for use in the workflows.
- **Workflow Examples**: See how functions are composed using `[get_rev, get_cogs] | calc_margin_ratio` for parallel data extraction followed by calculation.

## Purpose

These examples are intended to:
- Demonstrate best practices for financial data extraction and analysis in Dana.
- Show how to use Dana's workflow composition features for building complex financial analysis pipelines.
- Serve as templates for building custom financial analysis agents or pipelines.
- Provide a reference for implementing standard financial ratios and metrics in a programmatic, auditable way.
