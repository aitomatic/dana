"""
Minimal finance domain pack to populate the registry with one template
and a few knowledge assets for a simple risk assessment task.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from ..templates import ContextTemplate, KnowledgeSelector, TokenBudget
from ..registry import DomainRegistry, KnowledgeAsset


def register_simple_finance(reg: DomainRegistry) -> None:
    # Template: finance:risk_assessment
    tpl = ContextTemplate(
        name="finance_risk_assessment",
        version="0.1.0",
        domain="finance",
        task="risk_assessment",
        instructions_template=(
            "You are a finance risk assistant. Use the knowledge to assess portfolio risk."
            " Provide concise, auditable reasoning and include key metrics."
        ),
        example_templates=[
            "Q: Assess risk for a diversified equity portfolio. A: Summarize VaR, beta, sector concentration.",
        ],
        knowledge_selector=KnowledgeSelector(domain="finance", task="risk_assessment", trust_threshold=0.5, max_assets=5),
        token_budget=TokenBudget(total=2000),
    )
    reg.register_template(tpl)

    # Assets (toy content)
    now = datetime.now()
    reg.register_asset(
        KnowledgeAsset(
            domain="finance",
            tasks=["risk_assessment"],
            source="regulations.us.sec",
            content="US SEC disclosure rules require risk disclosures for material exposures.",
            trust_score=0.9,
            created_at=now - timedelta(days=2),
        )
    )
    reg.register_asset(
        KnowledgeAsset(
            domain="finance",
            tasks=["risk_assessment"],
            source="risk.var.guide",
            content=(
                "Value at Risk (VaR) estimates maximum potential loss at a given confidence level."
                " Methods: parametric, historical, Monte Carlo."
            ),
            trust_score=0.8,
            created_at=now - timedelta(days=10),
        )
    )
    reg.register_asset(
        KnowledgeAsset(
            domain="finance",
            tasks=["risk_assessment"],
            source="risk.concentration",
            content="Concentration risk arises when positions are heavily weighted in a single issuer or sector.",
            trust_score=0.75,
            created_at=now - timedelta(days=5),
        )
    )
