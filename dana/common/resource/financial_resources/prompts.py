"""
Prompts for financial analysis and ratio calculations
"""


def create_liquidity_ratios_prompt(markdown_content: str, company_name: str = "Company") -> str:
    """
    Create a prompt for LLM to generate Python code that calculates liquidity ratios.

    Args:
        markdown_content: Full markdown content of financial statement files
        company_name: Name of the company being analyzed

    Returns:
        Formatted prompt string for LLM
    """

    prompt = f"""You are a financial analyst expert. Generate Python code to calculate liquidity ratios from the provided financial statement data.

COMPANY: {company_name}

FINANCIAL STATEMENT DATA (MARKDOWN):
```
{markdown_content}
```

YOUR TASK:
Generate complete, executable Python code that calculates ALL the following liquidity ratios for all available periods found in the data:

## CORE LIQUIDITY RATIOS:
1. **Current Ratio** = Current Assets ÷ Current Liabilities
2. **Quick Ratio (Acid-Test)** = (Current Assets - Inventory - Prepaid Expenses) ÷ Current Liabilities  
3. **Cash Ratio** = (Cash + Cash Equivalents + Marketable Securities) ÷ Current Liabilities
4. **Working Capital** = Current Assets - Current Liabilities

## EXTENDED LIQUIDITY RATIOS:
5. **Super Quick Ratio** = (Cash + Cash Equivalents + Marketable Securities) ÷ Current Liabilities
6. **Cash Coverage Ratio** = (Cash + Cash Equivalents) ÷ Current Liabilities
7. **Operating Cash Flow Ratio** = Operating Cash Flow ÷ Current Liabilities (if cash flow data available)
8. **Net Working Capital Ratio** = Net Working Capital ÷ Total Assets
9. **Current Assets to Total Assets** = Current Assets ÷ Total Assets
10. **Liquid Assets Ratio** = (Cash + Marketable Securities + Accounts Receivable) ÷ Current Liabilities
11. **Receivables Turnover Liquidity** = Accounts Receivable ÷ Current Liabilities
12. **Inventory to Working Capital** = Inventory ÷ Working Capital (if Working Capital > 0)

REQUIREMENTS:
- Parse the markdown table data into a Python dictionary
- IMPORTANT: Fix sign convention - if all values appear negative, convert them to positive (common extraction artifact)
- Handle negative numbers in parentheses format like ($1,000) → -1,000 (true negatives)
- Handle missing data gracefully (use 0 or return None)
- Handle division by zero appropriately
- Use absolute values for ratio calculations where appropriate
- Calculate ratios for ALL periods present in the data
- DO NOT include interpretations, ratings, or commentary - just calculate the numbers
- Return clean numerical results only

DATA EXTRACTION GUIDELINES:
- Parse markdown tables to extract numerical data
- Look for "Total Current Assets" or sum current asset line items
- Look for "Total Assets" for ratio calculations
- Look for current liabilities (may be individual items like "Accounts Payable", "Deferred Revenue", etc.)
- Look for "Cash", "Cash and Cash Equivalents", "Cash and Equivalents"
- Look for "Marketable Securities", "Short-term Investments", "Trading Securities"
- Look for "Accounts Receivable", "Trade Receivables", "Receivables"
- Look for "Inventory", "Inventories" (if present)
- Look for "Prepaid Expenses", "Prepaid Assets", "Other Current Assets"
- Look for "Operating Cash Flow" in cash flow statement (if available)
- Extract all time periods from table headers

OUTPUT FORMAT:
Generate Python code following this EXACT template structure. Fill in the periods and values from the markdown data.
The final output will be transposed to show periods as columns and ratios as rows:

```python
import pandas as pd

# Company information
company_name = "ACTUAL COMPANY NAME"

# Extract data from markdown and create pandas Series
# IMPORTANT: Apply sign correction if needed (common extraction artifact makes all values negative)
raw_current_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})
raw_current_liabilities = pd.Series({{"period_1": value1, "period_2": value2, ...}})
raw_total_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})
raw_cash = pd.Series({{"period_1": value1, "period_2": value2, ...}})
raw_cash_equivalents = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
raw_marketable_securities = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
raw_accounts_receivable = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
raw_inventories = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
raw_prepaid_expenses = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
raw_operating_cash_flow = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available

# Apply sign correction - if assets appear negative, flip signs (common extraction issue)
sign_correction = -1 if raw_total_assets.mean() < 0 else 1

current_assets = raw_current_assets * sign_correction
current_liabilities = raw_current_liabilities * sign_correction  
total_assets = raw_total_assets * sign_correction
cash = raw_cash * sign_correction
cash_equivalents = raw_cash_equivalents * sign_correction
marketable_securities = raw_marketable_securities * sign_correction
accounts_receivable = raw_accounts_receivable * sign_correction
inventories = raw_inventories * sign_correction
prepaid_expenses = raw_prepaid_expenses * sign_correction
operating_cash_flow = raw_operating_cash_flow * sign_correction

# Calculate comprehensive liquidity ratios
current_ratios = current_assets / current_liabilities
quick_ratios = (current_assets - inventories - prepaid_expenses) / current_liabilities
cash_ratios = (cash + cash_equivalents + marketable_securities) / current_liabilities
working_capital = current_assets - current_liabilities
super_quick_ratios = (cash + cash_equivalents + marketable_securities) / current_liabilities
cash_coverage_ratios = (cash + cash_equivalents) / current_liabilities
operating_cf_ratios = operating_cash_flow / current_liabilities
net_wc_ratios = working_capital / total_assets
current_assets_ratios = current_assets / total_assets
liquid_assets_ratios = (cash + marketable_securities + accounts_receivable) / current_liabilities
receivables_liquidity = accounts_receivable / current_liabilities
inventory_to_wc = inventories / working_capital.where(working_capital > 0)

# Combine all ratios into a comprehensive DataFrame
liquidity_df = pd.DataFrame({{
    'Current Ratio': current_ratios,
    'Quick Ratio': quick_ratios,
    'Cash Ratio': cash_ratios,
    'Super Quick Ratio': super_quick_ratios,
    'Cash Coverage Ratio': cash_coverage_ratios,
    'Operating CF Ratio': operating_cf_ratios,
    'Net WC Ratio': net_wc_ratios,
    'Current Assets Ratio': current_assets_ratios,
    'Liquid Assets Ratio': liquid_assets_ratios,
    'Receivables Liquidity': receivables_liquidity,
    'Inventory to WC': inventory_to_wc,
    'Working Capital': working_capital
}})

# Display results in markdown format with periods as columns
print("# Liquidity Ratios Analysis")
print(f"**Company:** {{company_name}}")
print()
# Transpose to have periods as columns and ratios as rows
print(liquidity_df.T.to_markdown(floatfmt='.2f'))
```

IMPORTANT:
- Replace "period_1", "period_2", etc. with actual period names from the markdown (e.g., "Q1'24", "Q2'24")
- Replace value1, value2, etc. with actual numerical values extracted from the markdown
- Handle negative numbers in parentheses: ($1,000) → -1000
- Use absolute values for the denominators in ratio calculations

Generate the complete Python code now:"""

    return prompt


def create_leverage_ratios_prompt(bs_content: str, is_content: str, company_name: str = "Company") -> str:
    """
    Create a prompt for LLM to generate Python code that calculates leverage ratios.

    Args:
        bs_content: Balance sheet markdown content
        is_content: Income statement markdown content
        company_name: Name of the company being analyzed

    Returns:
        Formatted prompt string for LLM
    """

    prompt = f"""You are a financial analyst expert. Generate Python code to calculate leverage ratios from the provided financial statement data.

COMPANY: {company_name}

BALANCE SHEET DATA (MARKDOWN):
```
{bs_content}
```

INCOME STATEMENT DATA (MARKDOWN):
```
{is_content}
```

YOUR TASK:
Generate complete, executable Python code that calculates ALL the following leverage ratios for all available periods found in the data:

## CORE LEVERAGE RATIOS:
1. **Debt-to-Equity Ratio** = Total Debt ÷ Total Equity
2. **Debt-to-Assets Ratio** = Total Debt ÷ Total Assets
3. **Equity Ratio** = Total Equity ÷ Total Assets
4. **Long-term Debt to Equity** = Long-term Debt ÷ Total Equity

## COVERAGE RATIOS:
5. **Interest Coverage Ratio** = EBIT ÷ Interest Expense (if interest expense available)
6. **Times Interest Earned** = Operating Income ÷ Interest Expense (if available)
7. **EBITDA Coverage Ratio** = EBITDA ÷ (Interest + Principal Payments) (if available)

## ADDITIONAL LEVERAGE RATIOS:
8. **Equity Multiplier** = Total Assets ÷ Total Equity
9. **Long-term Debt to Total Capital** = Long-term Debt ÷ (Long-term Debt + Total Equity)
10. **Asset Coverage Ratio** = (Total Assets - Current Liabilities - Intangible Assets) ÷ Total Debt
11. **Debt Service Coverage** = Operating Income ÷ Total Debt Service (if available)
12. **Financial Leverage** = Average Total Assets ÷ Average Total Equity

REQUIREMENTS:
- Parse both balance sheet and income statement markdown tables
- Handle negative numbers in parentheses format like ($1,000) → -1,000
- Handle missing data gracefully (use 0 or return None for ratios requiring unavailable data)
- Handle division by zero appropriately
- Use absolute values for ratio calculations where appropriate
- Calculate ratios for ALL periods present in the data
- DO NOT include interpretations, ratings, or commentary - just calculate the numbers
- Return clean numerical results only

DATA EXTRACTION GUIDELINES:
BALANCE SHEET:
- Look for "Total Liabilities" or sum all liability line items for Total Debt
- Look for "Notes/Bonds Payable", "Long-term Debt" for long-term debt
- Look for "Total Equity", "Stockholders' Equity", "Shareholders' Equity"
- Look for "Total Assets"
- Look for "Current Liabilities" 
- Look for "Intangible Assets" (use 0 if not available)

INCOME STATEMENT:
- Look for "Operating Income", "EBIT", "Earnings Before Interest and Tax"
- Look for "Interest Expense", "Interest Payments"
- Look for "EBITDA" or calculate as Operating Income + Depreciation + Amortization
- Extract all time periods from table headers

OUTPUT FORMAT:
Generate Python code following this EXACT template structure. Fill in the periods and values from the markdown data.
The final output will be transposed to show periods as columns and ratios as rows:

```python
import pandas as pd

# Company information
company_name = "ACTUAL COMPANY NAME"

# Extract balance sheet data
total_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})
total_liabilities = pd.Series({{"period_1": value1, "period_2": value2, ...}})
total_equity = pd.Series({{"period_1": value1, "period_2": value2, ...}})
current_liabilities = pd.Series({{"period_1": value1, "period_2": value2, ...}})
long_term_debt = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
intangible_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available

# Extract income statement data
operating_income = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
interest_expense = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
ebit = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use operating_income if EBIT not available

# Calculate comprehensive leverage ratios
debt_to_equity = total_liabilities / total_equity.where(total_equity != 0)
debt_to_assets = total_liabilities / total_assets
equity_ratio = total_equity / total_assets
long_term_debt_to_equity = long_term_debt / total_equity.where(total_equity != 0)

# Coverage ratios (handle zero interest expense)
interest_coverage = ebit / interest_expense.where(interest_expense != 0)
times_interest_earned = operating_income / interest_expense.where(interest_expense != 0)

# Additional leverage ratios
equity_multiplier = total_assets / total_equity.where(total_equity != 0)
long_term_debt_to_capital = long_term_debt / (long_term_debt + total_equity)
asset_coverage = (total_assets - current_liabilities - intangible_assets) / total_liabilities.where(total_liabilities != 0)
financial_leverage = total_assets / total_equity.where(total_equity != 0)

# Combine all ratios into a comprehensive DataFrame
leverage_df = pd.DataFrame({{
    'Debt-to-Equity': debt_to_equity,
    'Debt-to-Assets': debt_to_assets,
    'Equity Ratio': equity_ratio,
    'LT Debt-to-Equity': long_term_debt_to_equity,
    'Interest Coverage': interest_coverage,
    'Times Interest Earned': times_interest_earned,
    'Equity Multiplier': equity_multiplier,
    'LT Debt-to-Capital': long_term_debt_to_capital,
    'Asset Coverage': asset_coverage,
    'Financial Leverage': financial_leverage
}})

# Display results in markdown format with periods as columns
print("# Leverage Ratios Analysis")
print(f"**Company:** {{company_name}}")
print()
# Transpose to have periods as columns and ratios as rows
print(leverage_df.T.to_markdown(floatfmt='.2f'))
```

IMPORTANT:
- Replace "period_1", "period_2", etc. with actual period names from the markdown (e.g., "Q1'24", "Q2'24")
- Replace value1, value2, etc. with actual numerical values extracted from the markdown
- Handle negative numbers in parentheses: ($1,000) → -1000
- Use absolute values for the denominators in ratio calculations
- For missing interest expense data, ratios like Interest Coverage will show NaN - this is acceptable

Generate the complete Python code now:"""

    return prompt


def create_efficiency_ratios_prompt(bs_content: str, is_content: str, company_name: str = "Company") -> str:
    """
    Create a prompt for LLM to generate Python code that calculates efficiency ratios.

    Args:
        bs_content: Balance sheet markdown content
        is_content: Income statement markdown content
        company_name: Name of the company being analyzed

    Returns:
        Formatted prompt string for LLM
    """

    prompt = f"""You are a financial analyst expert. Generate Python code to calculate efficiency ratios from the provided financial statement data.

COMPANY: {company_name}

BALANCE SHEET DATA (MARKDOWN):
```
{bs_content}
```

INCOME STATEMENT DATA (MARKDOWN):
```
{is_content}
```

YOUR TASK:
Generate complete, executable Python code that calculates ALL the following efficiency ratios for all available periods found in the data:

## ASSET UTILIZATION RATIOS:
1. **Asset Turnover Ratio** = Total Revenue ÷ Average Total Assets
2. **Fixed Asset Turnover** = Total Revenue ÷ Average Fixed Assets
3. **Current Asset Turnover** = Total Revenue ÷ Average Current Assets
4. **Total Asset Turnover** = Total Revenue ÷ Total Assets

## WORKING CAPITAL RATIOS:
5. **Inventory Turnover** = Cost of Goods Sold ÷ Average Inventory (if inventory available)
6. **Days Sales in Inventory** = 365 ÷ Inventory Turnover (if applicable)
7. **Receivables Turnover** = Total Revenue ÷ Average Accounts Receivable
8. **Days Sales Outstanding** = 365 ÷ Receivables Turnover
9. **Payables Turnover** = COGS ÷ Average Accounts Payable
10. **Days Payable Outstanding** = 365 ÷ Payables Turnover

## EFFICIENCY METRICS:
11. **Working Capital Turnover** = Total Revenue ÷ Average Working Capital
12. **Cash Conversion Cycle** = DSO + DSI - DPO (Days Sales Outstanding + Days Sales in Inventory - Days Payable Outstanding)

REQUIREMENTS:
- Parse both balance sheet and income statement markdown tables
- Handle negative numbers in parentheses format like ($1,000) → -1,000
- Handle missing data gracefully (use 0 or return None for ratios requiring unavailable data)
- Handle division by zero appropriately
- Use absolute values for ratio calculations where appropriate
- Calculate ratios for ALL periods present in the data
- For average calculations, use current period if only one period available
- DO NOT include interpretations, ratings, or commentary - just calculate the numbers
- Return clean numerical results only

DATA EXTRACTION GUIDELINES:
BALANCE SHEET:
- Look for "Total Assets", "Fixed Assets", "Current Assets"
- Look for "Accounts Receivable", "Trade Receivables", "Receivables"
- Look for "Inventory", "Inventories" (use 0 if not available)
- Look for "Accounts Payable", "Trade Payables"
- Calculate Working Capital = Current Assets - Current Liabilities

INCOME STATEMENT:
- Look for "Total Revenue", "Net Sales", "Sales", "Revenue"
- Look for "Cost of Goods Sold", "COGS", "Cost of Sales"
- Extract all time periods from table headers

OUTPUT FORMAT:
Generate Python code following this EXACT template structure. Fill in the periods and values from the markdown data.
The final output will be transposed to show periods as columns and ratios as rows:

```python
import pandas as pd

# Company information
company_name = "ACTUAL COMPANY NAME"

# Extract balance sheet data
total_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})
current_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})
fixed_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use total_assets - current_assets if not available
accounts_receivable = pd.Series({{"period_1": value1, "period_2": value2, ...}})
inventory = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
accounts_payable = pd.Series({{"period_1": value1, "period_2": value2, ...}})
current_liabilities = pd.Series({{"period_1": value1, "period_2": value2, ...}})

# Extract income statement data
total_revenue = pd.Series({{"period_1": value1, "period_2": value2, ...}})
cogs = pd.Series({{"period_1": value1, "period_2": value2, ...}})

# Calculate working capital
working_capital = current_assets - current_liabilities

# Calculate average values for turnover ratios (use current value if only one period)
avg_total_assets = total_assets.rolling(window=2, min_periods=1).mean()
avg_current_assets = current_assets.rolling(window=2, min_periods=1).mean()
avg_fixed_assets = fixed_assets.rolling(window=2, min_periods=1).mean()
avg_accounts_receivable = accounts_receivable.rolling(window=2, min_periods=1).mean()
avg_inventory = inventory.rolling(window=2, min_periods=1).mean()
avg_accounts_payable = accounts_payable.rolling(window=2, min_periods=1).mean()
avg_working_capital = working_capital.rolling(window=2, min_periods=1).mean()

# Calculate comprehensive efficiency ratios
asset_turnover = total_revenue / avg_total_assets
fixed_asset_turnover = total_revenue / avg_fixed_assets.where(avg_fixed_assets != 0)
current_asset_turnover = total_revenue / avg_current_assets
total_asset_turnover_simple = total_revenue / total_assets

# Working capital ratios
inventory_turnover = cogs / avg_inventory.where(avg_inventory != 0)
days_sales_inventory = 365 / inventory_turnover.where(inventory_turnover != 0)
receivables_turnover = total_revenue / avg_accounts_receivable.where(avg_accounts_receivable != 0)
days_sales_outstanding = 365 / receivables_turnover.where(receivables_turnover != 0)
payables_turnover = cogs / avg_accounts_payable.where(avg_accounts_payable != 0)
days_payable_outstanding = 365 / payables_turnover.where(payables_turnover != 0)

# Efficiency metrics
working_capital_turnover = total_revenue / avg_working_capital.where(avg_working_capital != 0)
cash_conversion_cycle = days_sales_outstanding + days_sales_inventory - days_payable_outstanding

# Combine all ratios into a comprehensive DataFrame
efficiency_df = pd.DataFrame({{
    'Asset Turnover': asset_turnover,
    'Fixed Asset Turnover': fixed_asset_turnover,
    'Current Asset Turnover': current_asset_turnover,
    'Total Asset Turnover': total_asset_turnover_simple,
    'Inventory Turnover': inventory_turnover,
    'Days Sales in Inventory': days_sales_inventory,
    'Receivables Turnover': receivables_turnover,
    'Days Sales Outstanding': days_sales_outstanding,
    'Payables Turnover': payables_turnover,
    'Days Payable Outstanding': days_payable_outstanding,
    'Working Capital Turnover': working_capital_turnover,
    'Cash Conversion Cycle': cash_conversion_cycle
}})

# Display results in markdown format with periods as columns
print("# Efficiency Ratios Analysis")
print(f"**Company:** {{company_name}}")
print()
# Transpose to have periods as columns and ratios as rows
print(efficiency_df.T.to_markdown(floatfmt='.2f'))
```

IMPORTANT:
- Replace "period_1", "period_2", etc. with actual period names from the markdown (e.g., "Q1'24", "Q2'24")
- Replace value1, value2, etc. with actual numerical values extracted from the markdown
- Handle negative numbers in parentheses: ($1,000) → -1000
- Use absolute values for the denominators in ratio calculations
- For inventory-related ratios, if inventory is 0 or unavailable, ratios will show NaN - this is acceptable
- Average calculations use rolling window for multi-period analysis

Generate the complete Python code now:"""

    return prompt


def create_profitability_ratios_prompt(bs_content: str, is_content: str, company_name: str = "Company") -> str:
    """
    Create a prompt for LLM to generate Python code that calculates profitability ratios.

    Args:
        bs_content: Balance sheet markdown content
        is_content: Income statement markdown content
        company_name: Name of the company being analyzed

    Returns:
        Formatted prompt string for LLM
    """

    prompt = f"""You are a financial analyst expert. Generate Python code to calculate profitability ratios from the provided financial statement data.

COMPANY: {company_name}

BALANCE SHEET DATA (MARKDOWN):
```
{bs_content}
```

INCOME STATEMENT DATA (MARKDOWN):
```
{is_content}
```

YOUR TASK:
Generate complete, executable Python code that calculates ALL the following profitability ratios for all available periods found in the data:

## MARGIN RATIOS:
1. **Gross Profit Margin** = (Revenue - COGS) ÷ Revenue × 100
2. **Operating Profit Margin** = Operating Income ÷ Revenue × 100
3. **Net Profit Margin** = Net Income ÷ Revenue × 100
4. **EBITDA Margin** = EBITDA ÷ Revenue × 100 (if available)

## RETURN RATIOS:
5. **Return on Assets (ROA)** = Net Income ÷ Average Total Assets × 100
6. **Return on Equity (ROE)** = Net Income ÷ Average Total Equity × 100
7. **Return on Invested Capital (ROIC)** = Net Operating Profit After Tax ÷ Invested Capital × 100
8. **Return on Capital Employed (ROCE)** = EBIT ÷ Capital Employed × 100

## EFFICIENCY PROFITABILITY:
9. **Asset Turnover** = Revenue ÷ Average Total Assets
10. **Equity Multiplier** = Average Total Assets ÷ Average Total Equity
11. **Financial Leverage** = Average Total Assets ÷ Average Total Equity
12. **DuPont ROE** = Net Profit Margin × Asset Turnover × Equity Multiplier

REQUIREMENTS:
- Parse both balance sheet and income statement markdown tables
- Handle negative numbers in parentheses format like ($1,000) → -1,000
- Handle missing data gracefully (use 0 or return None for ratios requiring unavailable data)
- Handle division by zero appropriately
- Use absolute values for ratio calculations where appropriate
- Calculate ratios for ALL periods present in the data
- For average calculations, use current period if only one period available
- Express margins and returns as percentages (multiply by 100)
- DO NOT include interpretations, ratings, or commentary - just calculate the numbers
- Return clean numerical results only

DATA EXTRACTION GUIDELINES:
BALANCE SHEET:
- Look for "Total Assets"
- Look for "Total Equity", "Stockholders' Equity", "Shareholders' Equity"
- Look for "Total Liabilities"
- Calculate Invested Capital = Total Equity + Interest-bearing Debt
- Calculate Capital Employed = Total Assets - Current Liabilities

INCOME STATEMENT:
- Look for "Total Revenue", "Net Sales", "Sales", "Revenue"
- Look for "Cost of Goods Sold", "COGS", "Cost of Sales"
- Look for "Gross Profit" or calculate as Revenue - COGS
- Look for "Operating Income", "Operating Profit", "EBIT"
- Look for "Net Income", "Net Profit", "Profit After Tax"
- Look for "EBITDA" or estimate as Operating Income + Depreciation
- Look for "Interest Expense" for tax shield calculations
- Extract all time periods from table headers

OUTPUT FORMAT:
Generate Python code following this EXACT template structure. Fill in the periods and values from the markdown data.
The final output will be transposed to show periods as columns and ratios as rows:

```python
import pandas as pd

# Company information
company_name = "ACTUAL COMPANY NAME"

# Extract balance sheet data
total_assets = pd.Series({{"period_1": value1, "period_2": value2, ...}})
total_equity = pd.Series({{"period_1": value1, "period_2": value2, ...}})
total_liabilities = pd.Series({{"period_1": value1, "period_2": value2, ...}})
current_liabilities = pd.Series({{"period_1": value1, "period_2": value2, ...}})

# Extract income statement data
total_revenue = pd.Series({{"period_1": value1, "period_2": value2, ...}})
cogs = pd.Series({{"period_1": value1, "period_2": value2, ...}})
gross_profit = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use revenue - cogs if not available
operating_income = pd.Series({{"period_1": value1, "period_2": value2, ...}})
net_income = pd.Series({{"period_1": value1, "period_2": value2, ...}})
interest_expense = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use 0 if not available
ebitda = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use operating_income if not available

# Calculate derived metrics
capital_employed = total_assets - current_liabilities
invested_capital = total_equity + total_liabilities  # Approximation when debt breakdown unavailable

# Calculate average values for return ratios (use current value if only one period)
avg_total_assets = total_assets.rolling(window=2, min_periods=1).mean()
avg_total_equity = total_equity.rolling(window=2, min_periods=1).mean()
avg_invested_capital = invested_capital.rolling(window=2, min_periods=1).mean()
avg_capital_employed = capital_employed.rolling(window=2, min_periods=1).mean()

# Calculate profitability ratios (expressed as percentages)
gross_margin = (gross_profit / total_revenue * 100).where(total_revenue != 0)
operating_margin = (operating_income / total_revenue * 100).where(total_revenue != 0)
net_margin = (net_income / total_revenue * 100).where(total_revenue != 0)
ebitda_margin = (ebitda / total_revenue * 100).where(total_revenue != 0)

# Return ratios (expressed as percentages)
roa = (net_income / avg_total_assets * 100).where(avg_total_assets != 0)
roe = (net_income / avg_total_equity * 100).where(avg_total_equity != 0)
roic = (operating_income / avg_invested_capital * 100).where(avg_invested_capital != 0)  # Simplified ROIC
roce = (operating_income / avg_capital_employed * 100).where(avg_capital_employed != 0)

# Efficiency ratios for DuPont analysis
asset_turnover_ratio = total_revenue / avg_total_assets.where(avg_total_assets != 0)
equity_multiplier = avg_total_assets / avg_total_equity.where(avg_total_equity != 0)
financial_leverage = avg_total_assets / avg_total_equity.where(avg_total_equity != 0)

# DuPont ROE breakdown
dupont_roe = (net_margin / 100) * asset_turnover_ratio * equity_multiplier * 100

# Combine all ratios into a comprehensive DataFrame
profitability_df = pd.DataFrame({{
    'Gross Margin (%)': gross_margin,
    'Operating Margin (%)': operating_margin,
    'Net Margin (%)': net_margin,
    'EBITDA Margin (%)': ebitda_margin,
    'ROA (%)': roa,
    'ROE (%)': roe,
    'ROIC (%)': roic,
    'ROCE (%)': roce,
    'Asset Turnover': asset_turnover_ratio,
    'Equity Multiplier': equity_multiplier,
    'Financial Leverage': financial_leverage,
    'DuPont ROE (%)': dupont_roe
}})

# Display results in markdown format with periods as columns
print("# Profitability Ratios Analysis")
print(f"**Company:** {{company_name}}")
print()
# Transpose to have periods as columns and ratios as rows
print(profitability_df.T.to_markdown(floatfmt='.2f'))
```

IMPORTANT:
- Replace "period_1", "period_2", etc. with actual period names from the markdown (e.g., "Q1'24", "Q2'24")
- Replace value1, value2, etc. with actual numerical values extracted from the markdown
- Handle negative numbers in parentheses: ($1,000) → -1000
- Use absolute values for the denominators in ratio calculations
- Margins and returns are expressed as percentages (already multiplied by 100 in template)
- For companies with losses, negative margins/returns are acceptable and informative
- Average calculations use rolling window for multi-period analysis

Generate the complete Python code now:"""

    return prompt


def create_market_value_ratios_prompt(bs_content: str, is_content: str, company_name: str = "Company", market_data: str = "") -> str:
    """
    Create a prompt for LLM to generate Python code that calculates market value ratios.

    Args:
        bs_content: Balance sheet markdown content
        is_content: Income statement markdown content
        company_name: Name of the company being analyzed
        market_data: Optional market data (stock price, shares outstanding, market cap)

    Returns:
        Formatted prompt string for LLM
    """

    prompt = f"""You are a financial analyst expert. Generate Python code to calculate market value ratios from the provided financial statement data.

COMPANY: {company_name}

BALANCE SHEET DATA (MARKDOWN):
```
{bs_content}
```

INCOME STATEMENT DATA (MARKDOWN):
```
{is_content}
```

MARKET DATA (if available):
```
{market_data if market_data else "No market data provided - use placeholders for market-dependent ratios"}
```

YOUR TASK:
Generate complete, executable Python code that calculates ALL the following market value ratios for all available periods found in the data:

## VALUATION RATIOS (require market data):
1. **Price-to-Earnings (P/E) Ratio** = Market Price per Share ÷ Earnings per Share
2. **Price-to-Book (P/B) Ratio** = Market Price per Share ÷ Book Value per Share
3. **Price-to-Sales (P/S) Ratio** = Market Cap ÷ Total Revenue
4. **Price-to-Cash Flow Ratio** = Market Cap ÷ Operating Cash Flow

## EARNINGS-BASED RATIOS:
5. **Earnings per Share (EPS)** = Net Income ÷ Shares Outstanding
6. **Book Value per Share** = Total Equity ÷ Shares Outstanding
7. **Revenue per Share** = Total Revenue ÷ Shares Outstanding
8. **Cash Flow per Share** = Operating Cash Flow ÷ Shares Outstanding

## MARKET EFFICIENCY RATIOS:
9. **Market-to-Book Ratio** = Market Cap ÷ Total Book Value of Equity
10. **Enterprise Value** = Market Cap + Total Debt - Cash and Equivalents
11. **EV/Revenue** = Enterprise Value ÷ Total Revenue
12. **EV/EBITDA** = Enterprise Value ÷ EBITDA

REQUIREMENTS:
- Parse both balance sheet and income statement markdown tables
- Handle negative numbers in parentheses format like ($1,000) → -1,000
- Handle missing market data gracefully (use placeholder values and mark as "N/A - Market Data Required")
- Handle division by zero appropriately
- Use absolute values for ratio calculations where appropriate
- Calculate ratios for ALL periods present in the data
- If market data is unavailable, show formulas with placeholder values
- DO NOT include interpretations, ratings, or commentary - just calculate the numbers
- Return clean numerical results only

DATA EXTRACTION GUIDELINES:
BALANCE SHEET:
- Look for "Total Equity", "Stockholders' Equity", "Shareholders' Equity"
- Look for "Cash", "Cash and Cash Equivalents"
- Look for "Total Liabilities" or "Total Debt"
- Look for number of shares outstanding (may be in notes or separate section)

INCOME STATEMENT:
- Look for "Total Revenue", "Net Sales", "Sales", "Revenue"
- Look for "Net Income", "Net Profit", "Profit After Tax"
- Look for "Operating Cash Flow" (if available, else use operating income as proxy)
- Look for "EBITDA" or estimate as Operating Income + Depreciation
- Extract all time periods from table headers

MARKET DATA (if provided):
- Look for "Stock Price", "Share Price", "Market Price"
- Look for "Market Capitalization", "Market Cap"
- Look for "Shares Outstanding", "Outstanding Shares"
- If not provided, use placeholder values

OUTPUT FORMAT:
Generate Python code following this EXACT template structure. Fill in the periods and values from the markdown data.
The final output will be transposed to show periods as columns and ratios as rows:

```python
import pandas as pd

# Company information
company_name = "ACTUAL COMPANY NAME"

# Market data (use placeholders if not available)
market_data_available = {{market_data_available}}  # True if market data provided, False otherwise

# If market data available, extract it; otherwise use placeholders
if market_data_available:
    market_cap = pd.Series({{"period_1": value1, "period_2": value2, ...}})
    stock_price = pd.Series({{"period_1": value1, "period_2": value2, ...}})
    shares_outstanding = pd.Series({{"period_1": value1, "period_2": value2, ...}})
else:
    # Placeholder values - marked as requiring market data
    market_cap = pd.Series({{"period_1": 0, "period_2": 0, ...}})  # Placeholder
    stock_price = pd.Series({{"period_1": 0, "period_2": 0, ...}})  # Placeholder
    shares_outstanding = pd.Series({{"period_1": 1000000, "period_2": 1000000, ...}})  # Assume 1M shares

# Extract balance sheet data
total_equity = pd.Series({{"period_1": value1, "period_2": value2, ...}})
cash_and_equivalents = pd.Series({{"period_1": value1, "period_2": value2, ...}})
total_debt = pd.Series({{"period_1": value1, "period_2": value2, ...}})

# Extract income statement data
total_revenue = pd.Series({{"period_1": value1, "period_2": value2, ...}})
net_income = pd.Series({{"period_1": value1, "period_2": value2, ...}})
operating_cash_flow = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use operating income if unavailable
ebitda = pd.Series({{"period_1": value1, "period_2": value2, ...}})  # Use operating income if unavailable

# Calculate per-share metrics
eps = net_income / shares_outstanding.where(shares_outstanding != 0)
book_value_per_share = total_equity / shares_outstanding.where(shares_outstanding != 0)
revenue_per_share = total_revenue / shares_outstanding.where(shares_outstanding != 0)
cash_flow_per_share = operating_cash_flow / shares_outstanding.where(shares_outstanding != 0)

# Calculate valuation ratios (only meaningful if market data available)
if market_data_available:
    pe_ratio = stock_price / eps.where(eps > 0)  # Only positive EPS
    pb_ratio = stock_price / book_value_per_share.where(book_value_per_share > 0)
    ps_ratio = market_cap / total_revenue.where(total_revenue > 0)
    pcf_ratio = market_cap / operating_cash_flow.where(operating_cash_flow > 0)
    
    # Enterprise value calculations
    enterprise_value = market_cap + total_debt - cash_and_equivalents
    ev_revenue = enterprise_value / total_revenue.where(total_revenue > 0)
    ev_ebitda = enterprise_value / ebitda.where(ebitda > 0)
    market_to_book = market_cap / total_equity.where(total_equity > 0)
else:
    # Mark as requiring market data
    pe_ratio = pd.Series(index=eps.index, data="N/A - Market Data Required")
    pb_ratio = pd.Series(index=eps.index, data="N/A - Market Data Required")
    ps_ratio = pd.Series(index=eps.index, data="N/A - Market Data Required")
    pcf_ratio = pd.Series(index=eps.index, data="N/A - Market Data Required")
    enterprise_value = pd.Series(index=eps.index, data="N/A - Market Data Required")
    ev_revenue = pd.Series(index=eps.index, data="N/A - Market Data Required")
    ev_ebitda = pd.Series(index=eps.index, data="N/A - Market Data Required")
    market_to_book = pd.Series(index=eps.index, data="N/A - Market Data Required")

# Combine all ratios into a comprehensive DataFrame
market_value_df = pd.DataFrame({{
    'EPS ($)': eps,
    'Book Value per Share ($)': book_value_per_share,
    'Revenue per Share ($)': revenue_per_share,
    'Cash Flow per Share ($)': cash_flow_per_share,
    'P/E Ratio': pe_ratio,
    'P/B Ratio': pb_ratio,
    'P/S Ratio': ps_ratio,
    'P/CF Ratio': pcf_ratio,
    'Market-to-Book': market_to_book,
    'Enterprise Value': enterprise_value,
    'EV/Revenue': ev_revenue,
    'EV/EBITDA': ev_ebitda
}})

# Display results in markdown format with periods as columns
print("# Market Value Ratios Analysis")
print(f"**Company:** {company_name}")
if not market_data_available:
    print("**Note:** Market data not provided. Valuation ratios marked as N/A.")
print()
# Transpose to have periods as columns and ratios as rows
print(market_value_df.T.to_markdown(floatfmt='.2f'))
```

IMPORTANT:
- Replace "period_1", "period_2", etc. with actual period names from the markdown (e.g., "Q1'24", "Q2'24")
- Replace value1, value2, etc. with actual numerical values extracted from the markdown
- Handle negative numbers in parentheses: ($1,000) → -1000
- Set market_data_available = True only if actual market data is provided
- For market-dependent ratios without data, show "N/A - Market Data Required"
- Use absolute values for the denominators in ratio calculations
- Per-share calculations assume shares outstanding data is available

Generate the complete Python code now:"""

    return prompt
