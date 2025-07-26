# Financial-Analysis Dana Workflows

This directory contains a comprehensive suite of Dana (`.na`) code examples and utilities for financial statement analysis and financial ratio workflows. The examples are organized to demonstrate how to extract, compute, and analyze key financial metrics from company financial statements using the Dana language.

## Structure and Contents

- **Core Financial Statement Modules (`fin_statements/`)**
  - `bal_sheet.na`, `income.na`, `cash_flow.na`:
    Dana modules for extracting items from the Balance Sheet, Income Statement, and Cash Flow Statement, respectively.
    Each provides functions to query values (e.g., total assets, revenue, operating cash flow) for a given company, period, and currency.
  - `util/`:
    Utility code for querying and structuring financial data, including type definitions and helper functions.

- **Financial Ratio and Metric Workflows**
  - `leverage.na`, `liquidity.na`, `cap_intens.na`, `margin_ratios.na`, `turnover_ratios.na`, `return_ratios.na`, `income_util_ratios.na`:
    Each file implements calculations for a specific class of financial ratios or metrics, such as leverage (debt/equity), liquidity, capital intensity, profit margins, turnover, returns, and income utilization.
  - These modules use the core statement extractors to compute ratios according to standard financial formulas.

- **Test and Example Scripts**
  - `test.na`:
    Main test harness for running and validating the extraction and calculation functions across the modules.
  - `test-*.na`:
    Individual test scripts for each metric or ratio class, demonstrating usage and validating results.
  - `test-assets/`:
    Contains sample financial statement documents (e.g., `AMD_2022_10K.pdf`) used as data sources for the tests.

## How to Use

- Review the test scripts (`test.na`, `test-*.na`) for examples of how to invoke each workflow.
- The modules are designed to be composable: you can import and combine them to build custom financial analysis pipelines.
- Utilities in `fin_statements/util/` help with querying and formatting data for use in the workflows.

## Purpose

These examples are intended to:
- Demonstrate best practices for financial data extraction and analysis in Dana.
- Serve as templates for building custom financial analysis agents or pipelines.
- Provide a reference for implementing standard financial ratios and metrics in a programmatic, auditable way.
