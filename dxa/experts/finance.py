"""Finance domain expert."""

from dxa.core.resources.expert import DomainExpertise, ExpertResource

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