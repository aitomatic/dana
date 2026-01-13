"""Financial Conditional Logic Templates

Provides pre-built conditional logic patterns for financial decision making.
These templates work with Dana's case() function to provide structured
decision trees, routing logic, and business rule templates.
"""

from typing import Any
from dataclasses import dataclass
from enum import Enum


class ConditionType(Enum):
    """Types of conditional logic"""

    ROUTING = "routing"  # Route requests based on criteria
    THRESHOLD = "threshold"  # Apply thresholds and limits
    DECISION_TREE = "decision_tree"  # Multi-level decision logic
    BUSINESS_RULE = "business_rule"  # Business logic patterns


@dataclass
class ConditionalBranch:
    """Represents a conditional branch in financial logic"""

    condition_name: str
    description: str
    condition_logic: str  # Dana expression
    action_template: str  # Template for the action
    priority: int = 1  # Higher number = higher priority
    short_circuit: bool = False  # Stop evaluation after this branch


@dataclass
class ConditionalTemplate:
    """Base conditional template structure"""

    template_name: str
    condition_type: ConditionType
    description: str
    branches: list[ConditionalBranch]
    fallback_action: str
    metadata: dict[str, Any]


class RiskToleranceRouter(ConditionalTemplate):
    """Risk Tolerance Routing Template

    Routes investment decisions based on risk tolerance profiles.
    Integrates with Dana's case() function for clean conditional logic.
    """

    def __init__(self):
        super().__init__(
            template_name="risk_tolerance_router",
            condition_type=ConditionType.ROUTING,
            description="Route investment decisions based on client risk tolerance",
            branches=self._build_risk_tolerance_branches(),
            fallback_action="moderate_risk_strategy",
            metadata={
                "business_domain": "investment_advisory",
                "regulatory_impact": "fiduciary_duty",
                "optimization_hints": ["cache_risk_profiles", "short_circuit_conservative"],
            },
        )

    def _build_risk_tolerance_branches(self) -> list[ConditionalBranch]:
        """Build risk tolerance routing branches"""
        return [
            ConditionalBranch(
                condition_name="conservative_investor",
                description="Conservative risk profile with capital preservation focus",
                condition_logic="risk_tolerance == 'conservative' or (age > 65 and investment_horizon < 5)",
                action_template="conservative_investment_strategy",
                priority=3,
                short_circuit=True,
            ),
            ConditionalBranch(
                condition_name="aggressive_investor",
                description="Aggressive risk profile seeking maximum growth",
                condition_logic="risk_tolerance == 'aggressive' and (age < 40 and investment_horizon > 10)",
                action_template="aggressive_investment_strategy",
                priority=2,
            ),
            ConditionalBranch(
                condition_name="moderate_high_capacity",
                description="Moderate investor with high risk capacity",
                condition_logic="risk_tolerance == 'moderate' and (net_worth > 1000000 or annual_income > 200000)",
                action_template="moderate_plus_strategy",
                priority=1,
            ),
        ]

    def generate_dana_case_expression(self, context_vars: dict[str, str]) -> str:
        """Generate Dana case() expression for risk tolerance routing"""

        # Build case expression with proper Dana syntax
        case_branches = []

        for branch in sorted(self.branches, key=lambda b: b.priority, reverse=True):
            # Replace context variables in condition logic
            condition = branch.condition_logic
            for var, value in context_vars.items():
                condition = condition.replace(var, value)

            case_branches.append(f"({condition}, {branch.action_template})")

        # Add fallback
        case_expr = "case(\n    " + ",\n    ".join(case_branches) + f",\n    {self.fallback_action}\n)"

        return case_expr


class ComplianceThresholds(ConditionalTemplate):
    """Compliance Thresholds Template

    Applies regulatory and business thresholds for compliance decisions.
    Provides structured threshold logic for financial operations.
    """

    def __init__(self):
        super().__init__(
            template_name="compliance_thresholds",
            condition_type=ConditionType.THRESHOLD,
            description="Apply regulatory and business thresholds for compliance",
            branches=self._build_compliance_branches(),
            fallback_action="escalate_for_manual_review",
            metadata={
                "regulatory_frameworks": ["US_SEC", "EU_MIFID", "UK_FCA"],
                "threshold_types": ["transaction_limits", "concentration_limits", "exposure_limits"],
                "optimization_hints": ["cache_threshold_values", "parallel_evaluation"],
            },
        )

    def _build_compliance_branches(self) -> list[ConditionalBranch]:
        """Build compliance threshold branches"""
        return [
            ConditionalBranch(
                condition_name="large_transaction_alert",
                description="Transaction exceeds large transaction reporting threshold",
                condition_logic="transaction_amount > 10000 and transaction_type in ['cash', 'wire_transfer']",
                action_template="file_large_transaction_report",
                priority=5,
                short_circuit=False,
            ),
            ConditionalBranch(
                condition_name="concentration_limit_breach",
                description="Portfolio concentration exceeds risk limits",
                condition_logic="single_issuer_exposure > 0.1 or sector_exposure > 0.25",
                action_template="trigger_concentration_alert",
                priority=4,
                short_circuit=False,
            ),
            ConditionalBranch(
                condition_name="suspicious_activity_pattern",
                description="Transaction pattern indicates potential suspicious activity",
                condition_logic="rapid_transactions == true and (round_amounts == true or structured_amounts == true)",
                action_template="flag_for_aml_review",
                priority=5,
                short_circuit=True,
            ),
            ConditionalBranch(
                condition_name="position_limit_approach",
                description="Position approaching regulatory limits",
                condition_logic="position_size > (position_limit * 0.8)",
                action_template="position_limit_warning",
                priority=3,
                short_circuit=False,
            ),
            ConditionalBranch(
                condition_name="credit_limit_exceeded",
                description="Transaction would exceed credit limits",
                condition_logic="new_exposure > credit_limit",
                action_template="reject_transaction_credit_limit",
                priority=5,
                short_circuit=True,
            ),
        ]

    def get_threshold_values(self, jurisdiction: str = "US") -> dict[str, Any]:
        """Get threshold values for specific jurisdiction"""
        thresholds = {
            "US": {
                "large_transaction_threshold": 10000,
                "concentration_limit_single_issuer": 0.10,
                "concentration_limit_sector": 0.25,
                "position_limit_warning_ratio": 0.80,
                "suspicious_activity_amount": 3000,
            },
            "EU": {
                "large_transaction_threshold": 15000,  # EUR
                "concentration_limit_single_issuer": 0.05,
                "concentration_limit_sector": 0.20,
                "position_limit_warning_ratio": 0.75,
                "suspicious_activity_amount": 2500,
            },
            "UK": {
                "large_transaction_threshold": 8000,  # GBP
                "concentration_limit_single_issuer": 0.08,
                "concentration_limit_sector": 0.22,
                "position_limit_warning_ratio": 0.80,
                "suspicious_activity_amount": 2000,
            },
        }
        return thresholds.get(jurisdiction, thresholds["US"])


class InvestmentDecisionTree(ConditionalTemplate):
    """Investment Decision Tree Template

    Multi-level decision tree for investment recommendations.
    Provides structured decision logic for investment advisory.
    """

    def __init__(self):
        super().__init__(
            template_name="investment_decision_tree",
            condition_type=ConditionType.DECISION_TREE,
            description="Multi-level decision tree for investment recommendations",
            branches=self._build_investment_decision_branches(),
            fallback_action="request_additional_client_information",
            metadata={
                "decision_factors": ["risk_tolerance", "time_horizon", "liquidity_needs", "tax_situation"],
                "asset_classes": ["equity", "fixed_income", "alternatives", "cash"],
                "optimization_hints": ["branch_caching", "lazy_evaluation"],
            },
        )

    def _build_investment_decision_branches(self) -> list[ConditionalBranch]:
        """Build investment decision tree branches"""
        return [
            # Level 1: Risk and Time Horizon
            ConditionalBranch(
                condition_name="conservative_short_term",
                description="Conservative investor with short time horizon",
                condition_logic="risk_tolerance == 'conservative' and time_horizon < 3",
                action_template="recommend_cash_and_short_bonds",
                priority=10,
                short_circuit=True,
            ),
            ConditionalBranch(
                condition_name="aggressive_long_term",
                description="Aggressive investor with long time horizon",
                condition_logic="risk_tolerance == 'aggressive' and time_horizon >= 10",
                action_template="recommend_growth_equity_focus",
                priority=9,
            ),
            # Level 2: Liquidity and Tax Considerations
            ConditionalBranch(
                condition_name="high_liquidity_needs",
                description="Client has high liquidity requirements",
                condition_logic="liquidity_needs == 'high' or emergency_fund_ratio < 0.5",
                action_template="emphasize_liquid_investments",
                priority=8,
                short_circuit=False,
            ),
            ConditionalBranch(
                condition_name="tax_advantaged_focus",
                description="High tax bracket client prioritizing tax efficiency",
                condition_logic="tax_bracket > 0.32 and tax_sensitivity == 'high'",
                action_template="recommend_tax_efficient_portfolio",
                priority=7,
            ),
            # Level 3: Life Stage and Goals
            ConditionalBranch(
                condition_name="retirement_planning",
                description="Client in pre-retirement phase",
                condition_logic="age >= 50 and retirement_goal == true and time_to_retirement <= 15",
                action_template="balanced_retirement_strategy",
                priority=6,
            ),
            ConditionalBranch(
                condition_name="wealth_accumulation",
                description="Young professional in wealth accumulation phase",
                condition_logic="age <= 40 and income_growth_expected == true and debt_to_income < 0.3",
                action_template="growth_focused_accumulation_strategy",
                priority=5,
            ),
            # Level 4: Specific Circumstances
            ConditionalBranch(
                condition_name="inheritance_planning",
                description="Client focused on estate and inheritance planning",
                condition_logic="net_worth > 5000000 and estate_planning_priority == true",
                action_template="estate_planning_investment_strategy",
                priority=4,
            ),
            ConditionalBranch(
                condition_name="education_funding",
                description="Parent saving for children's education",
                condition_logic="education_goal == true and years_to_education <= 18",
                action_template="education_savings_strategy",
                priority=3,
            ),
        ]

    def generate_nested_case_expression(self) -> str:
        """Generate nested Dana case() expressions for complex decision tree"""

        # Group branches by priority levels for nested structure
        high_priority = [b for b in self.branches if b.priority >= 8]
        medium_priority = [b for b in self.branches if 5 <= b.priority < 8]
        low_priority = [b for b in self.branches if b.priority < 5]

        # Build nested case expression
        nested_expr = f"""case(
    // High Priority Decisions (Risk & Liquidity)
    {self._build_case_section(high_priority)},
    
    // Medium Priority Decisions (Tax & Life Stage)
    case(
        {self._build_case_section(medium_priority)},
        
        // Low Priority Decisions (Specific Circumstances)
        case(
            {self._build_case_section(low_priority)},
            {self.fallback_action}
        )
    )
)"""
        return nested_expr

    def _build_case_section(self, branches: list[ConditionalBranch]) -> str:
        """Build a section of case conditions"""
        case_lines = []
        for branch in branches:
            case_lines.append(f"({branch.condition_logic}, {branch.action_template})")
        return ",\n        ".join(case_lines)


class CreditRiskDecisionTree(ConditionalTemplate):
    """Credit Risk Decision Tree Template

    Structured decision tree for credit risk assessment and lending decisions.
    """

    def __init__(self):
        super().__init__(
            template_name="credit_risk_decision_tree",
            condition_type=ConditionType.DECISION_TREE,
            description="Credit risk assessment and lending decision tree",
            branches=self._build_credit_decision_branches(),
            fallback_action="refer_to_underwriter",
            metadata={
                "risk_factors": ["credit_score", "debt_to_income", "employment_history", "collateral"],
                "decision_outcomes": ["approve", "decline", "conditional_approval", "manual_review"],
                "optimization_hints": ["early_decline", "score_caching"],
            },
        )

    def _build_credit_decision_branches(self) -> list[ConditionalBranch]:
        """Build credit risk decision branches"""
        return [
            ConditionalBranch(
                condition_name="prime_borrower",
                description="Prime borrower meeting all criteria",
                condition_logic="credit_score >= 750 and debt_to_income <= 0.28 and employment_years >= 2",
                action_template="approve_prime_terms",
                priority=10,
                short_circuit=True,
            ),
            ConditionalBranch(
                condition_name="high_risk_decline",
                description="High risk borrower - automatic decline",
                condition_logic="credit_score < 580 or debt_to_income > 0.5 or bankruptcy_recent == true",
                action_template="decline_application",
                priority=9,
                short_circuit=True,
            ),
            ConditionalBranch(
                condition_name="near_prime_with_collateral",
                description="Near-prime borrower with good collateral",
                condition_logic="credit_score >= 680 and collateral_value > loan_amount * 1.2",
                action_template="approve_with_collateral_terms",
                priority=8,
            ),
            ConditionalBranch(
                condition_name="subprime_conditional",
                description="Subprime borrower requiring conditions",
                condition_logic="credit_score >= 620 and debt_to_income <= 0.35 and down_payment >= 0.2",
                action_template="conditional_approval_subprime",
                priority=7,
            ),
            ConditionalBranch(
                condition_name="insufficient_income",
                description="Income verification required",
                condition_logic="stated_income > verified_income * 1.2 or income_documentation == 'incomplete'",
                action_template="request_income_verification",
                priority=6,
                short_circuit=False,
            ),
        ]


class TradingRiskLimits(ConditionalTemplate):
    """Trading Risk Limits Template

    Real-time risk limit checking for trading operations.
    Provides fast threshold checking for trading systems.
    """

    def __init__(self):
        super().__init__(
            template_name="trading_risk_limits",
            condition_type=ConditionType.THRESHOLD,
            description="Real-time risk limit checking for trading operations",
            branches=self._build_trading_limit_branches(),
            fallback_action="allow_trade",
            metadata={
                "limit_types": ["position", "var", "notional", "concentration"],
                "asset_classes": ["equity", "fixed_income", "fx", "derivatives"],
                "latency_requirement": "sub_millisecond",
                "optimization_hints": ["pre_compute_limits", "parallel_checks", "circuit_breaker"],
            },
        )

    def _build_trading_limit_branches(self) -> list[ConditionalBranch]:
        """Build trading risk limit branches"""
        return [
            ConditionalBranch(
                condition_name="position_limit_breach",
                description="Position limit would be exceeded",
                condition_logic="new_position_size > position_limit",
                action_template="reject_trade_position_limit",
                priority=10,
                short_circuit=True,
            ),
            ConditionalBranch(
                condition_name="var_limit_breach",
                description="Portfolio VaR limit would be exceeded",
                condition_logic="new_portfolio_var > var_limit",
                action_template="reject_trade_var_limit",
                priority=9,
                short_circuit=True,
            ),
            ConditionalBranch(
                condition_name="concentration_warning",
                description="Trade increases concentration risk",
                condition_logic="sector_concentration > 0.15 or single_issuer_concentration > 0.08",
                action_template="flag_concentration_warning",
                priority=7,
                short_circuit=False,
            ),
            ConditionalBranch(
                condition_name="unusual_size",
                description="Trade size is unusually large",
                condition_logic="trade_size > historical_average * 5",
                action_template="require_senior_approval",
                priority=6,
                short_circuit=False,
            ),
            ConditionalBranch(
                condition_name="market_hours_restriction",
                description="Trade outside normal market hours",
                condition_logic="market_hours == false and trade_type == 'market_order'",
                action_template="convert_to_limit_order",
                priority=5,
                short_circuit=False,
            ),
        ]

    def get_optimized_case_expression(self) -> str:
        """Generate optimized case() expression for high-frequency trading"""

        # Sort by priority and group critical vs non-critical checks
        critical_checks = [b for b in self.branches if b.short_circuit and b.priority >= 8]
        warning_checks = [b for b in self.branches if not b.short_circuit]

        return f"""case(
    // Critical Checks (Short Circuit)
    {self._build_case_section(critical_checks)},
    
    // Warning Checks (Continue Processing)
    case(
        {self._build_case_section(warning_checks)},
        {self.fallback_action}
    )
)"""


# Utility functions for conditional template usage
def get_template_by_name(template_name: str) -> ConditionalTemplate | None:
    """Get conditional template by name"""
    templates = {
        "risk_tolerance_router": RiskToleranceRouter(),
        "compliance_thresholds": ComplianceThresholds(),
        "investment_decision_tree": InvestmentDecisionTree(),
        "credit_risk_decision_tree": CreditRiskDecisionTree(),
        "trading_risk_limits": TradingRiskLimits(),
    }
    return templates.get(template_name)


def list_available_templates() -> dict[str, str]:
    """List all available conditional templates"""
    return {
        "risk_tolerance_router": "Route investment decisions based on risk tolerance",
        "compliance_thresholds": "Apply regulatory and business thresholds",
        "investment_decision_tree": "Multi-level investment decision logic",
        "credit_risk_decision_tree": "Credit risk assessment decisions",
        "trading_risk_limits": "Real-time trading risk limit checks",
    }
