"""Finance domain expert.

This module provides functionality to create a specialized financial expert
resource capable of performing financial analysis, valuations, and investment
assessments. The expert combines quantitative analysis with qualitative insights
to provide comprehensive financial advice.

The finance expert can:
- Analyze financial statements and metrics
- Perform valuation calculations (DCF, multiples)
- Evaluate investment opportunities
- Assess risk-return profiles
- Model cash flows and projections
- Calculate key financial ratios and indicators

Example:
    >>> from dxa.experts import create_finance_expert
    >>> expert = create_finance_expert(api_key="your-api-key")
    >>> result = expert.analyze("Calculate the NPV for cash flows: -1000, 200, 300, 400")
    >>> print(result)
    Step 1: Let's use a discount rate of 10% for this calculation...

Notes:
    - Requires a valid API key for the underlying LLM service
    - Uses GPT-4 as the default model for complex financial analysis
    - Confidence threshold set to 0.7 to ensure reliable advice
    - Considers both quantitative data and market context
"""

from dxa.core.resource.expert import DomainExpertise, ExpertResource

def create_finance_expert(api_key: str) -> ExpertResource:
    """Create a finance expert resource."""
    expertise = DomainExpertise(
        name="finance",
        description="Expert in financial analysis and decision-making",
        capabilities=[
            "Analyze financial statements",
            "Calculate financial ratios",
            "Evaluate investments",
            "Assess risk and return",
            "Model cash flows",
            "Value assets and companies"
        ],
        keywords=[
            "finance", "investment", "valuation", "risk",
            "portfolio", "stock", "bond", "option", "derivative",
            "cash flow", "balance sheet", "income statement",
            "ratio", "NPV", "IRR", "ROI"
        ],
        requirements=[
            "Financial data or context",
            "Time period if applicable",
            "Required metrics or objectives"
        ],
        example_queries=[
            "Calculate the NPV of this investment with cash flows: -1000, 200, 300, 400",
            "Analyze these financial ratios: P/E 15, D/E 0.5, Current 1.2",
            "Value this stock using DCF with growth rate 5% and discount rate 10%",
            "Assess the risk-return profile of a portfolio with 60% stocks, 40% bonds"
        ]
    )
    
    return ExpertResource(
        name="finance_expert",
        expertise=expertise,
        config={
            "api_key": api_key,
            "model": "gpt-4"
        },
        system_prompt="""You are an expert financial analyst. When analyzing problems:
        1. Consider both quantitative and qualitative factors
        2. Show all calculations clearly
        3. Explain key assumptions
        4. Assess risks and limitations
        5. Provide actionable recommendations
        6. Consider market context and conditions""",
        confidence_threshold=0.7
    ) 