"""Finance Domain Pack Implementation

Provides financial domain-specific context engineering capabilities
for enhanced agent performance in financial applications.
"""

from typing import Any
from dataclasses import dataclass
from enum import Enum

from ..base import BaseDomainPack
from ...templates import ContextTemplate
from .workflow_templates import RiskAssessmentTemplate, ComplianceCheckTemplate, PortfolioAnalysisTemplate, ReportingTemplate
from .knowledge_assets import FinancialRegulations, RiskMetrics, ComplianceFrameworks, MarketDataStructures
from .conditional_templates import RiskToleranceRouter, ComplianceThresholds, InvestmentDecisionTree


class FinanceSpecialization(Enum):
    """Finance domain specializations"""

    RISK_MANAGEMENT = "risk_management"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    COMPLIANCE = "compliance"
    DERIVATIVES = "derivatives"
    CREDIT_ANALYSIS = "credit_analysis"
    INVESTMENT_BANKING = "investment_banking"
    WEALTH_MANAGEMENT = "wealth_management"
    REGULATORY_REPORTING = "regulatory_reporting"


@dataclass
class FinanceContextConfig:
    """Configuration for finance-specific context assembly"""

    specialization: FinanceSpecialization
    regulatory_framework: str  # "US", "EU", "UK", "GLOBAL"
    risk_tolerance: str  # "conservative", "moderate", "aggressive"
    compliance_level: str  # "basic", "enhanced", "strict"
    market_focus: list[str]  # ["equity", "fixed_income", "derivatives", "fx"]
    include_calculations: bool = True
    include_regulations: bool = True
    enable_risk_warnings: bool = True


class FinanceDomainPack(BaseDomainPack):
    """Finance Domain Pack for Context Engineering

    Provides financial domain expertise through:
    - Risk assessment workflow templates
    - Compliance checking templates
    - Portfolio analysis patterns
    - Financial knowledge assets
    - Regulatory frameworks
    - Decision trees for financial logic
    """

    def __init__(self):
        super().__init__(domain="finance")
        self._initialize_templates()
        self._initialize_knowledge_assets()
        self._initialize_conditional_templates()
        self._initialize_tool_guides()

    def _initialize_templates(self):
        """Initialize workflow templates"""
        self.workflow_templates = {
            "risk_assessment": RiskAssessmentTemplate(),
            "risk_assessment_derivatives": RiskAssessmentTemplate(variant="derivatives"),
            "compliance_check": ComplianceCheckTemplate(),
            "portfolio_analysis": PortfolioAnalysisTemplate(),
            "reporting": ReportingTemplate(),
        }

    def _initialize_knowledge_assets(self):
        """Initialize financial knowledge assets"""
        self.knowledge_assets = {
            "regulations": FinancialRegulations(),
            "risk_metrics": RiskMetrics(),
            "compliance_frameworks": ComplianceFrameworks(),
            "market_data_structures": MarketDataStructures(),
        }

    def _initialize_conditional_templates(self):
        """Initialize conditional logic templates"""
        self.conditional_templates = {
            "risk_tolerance_router": RiskToleranceRouter(),
            "compliance_thresholds": ComplianceThresholds(),
            "investment_decision_tree": InvestmentDecisionTree(),
        }

    def _initialize_tool_guides(self):
        """Initialize tool selection guides"""
        self.tool_guides = {
            "plan": {
                "retrieval_tools": ["bloomberg_search", "reuters_search", "sec_filings"],
                "analysis_tools": ["risk_calculator", "scenario_modeler"],
                "frameworks": ["monte_carlo", "value_at_risk", "stress_testing"],
            },
            "solve": {
                "calculation_engines": ["quantlib", "risk_metrics", "portfolio_optimizer"],
                "data_sources": ["market_data_api", "fundamental_data", "news_feeds"],
                "validators": ["compliance_checker", "risk_validator", "model_validator"],
            },
            "chat": {
                "glossaries": ["financial_terms", "regulatory_definitions"],
                "safety_tools": ["compliance_filter", "risk_disclosure"],
                "formatting": ["financial_formatter", "chart_generator"],
            },
            "use": {
                "read_only": ["market_data", "research_reports", "regulatory_filings"],
                "analytical": ["risk_calculator", "portfolio_analyzer", "scenario_engine"],
                "restricted": ["trading_systems", "client_data", "confidential_reports"],
            },
        }

    def get_context_template(self, method: str, config: FinanceContextConfig | None = None) -> ContextTemplate:
        """Get finance-specific context template for agent method

        Args:
            method: Agent method name (plan, solve, chat, use, remember)
            config: Finance-specific configuration

        Returns:
            Configured context template for the method
        """
        if config is None:
            config = FinanceContextConfig(
                specialization=FinanceSpecialization.RISK_MANAGEMENT,
                regulatory_framework="US",
                risk_tolerance="moderate",
                compliance_level="enhanced",
                market_focus=["equity", "fixed_income"],
            )

        template_config = self._build_template_config(method, config)
        return ContextTemplate(**template_config)

    def _build_template_config(self, method: str, config: FinanceContextConfig) -> dict[str, Any]:
        """Build template configuration for specific method and finance config"""

        from ...templates import KnowledgeSelector, TokenBudget

        # Create proper TokenBudget
        token_budgets = self._get_token_budgets(method)
        token_budget = TokenBudget(total=sum(token_budgets.values()))
        token_budget.sections = token_budgets

        # Create KnowledgeSelector
        knowledge_selector = KnowledgeSelector(
            domain="finance",
            task=f"{config.specialization.value}_{method}",
            trust_threshold=0.8 if config.compliance_level == "strict" else 0.7,
            freshness_days=7 if config.compliance_level == "strict" else 30,
            max_assets=10,
        )

        # Generate instructions template based on method and config
        instructions_template = self._generate_instructions_template(method, config)

        # Get method-specific examples
        example_templates = self._get_example_templates(method, config)

        # Create ContextTemplate-compatible config
        base_config = {
            "name": f"finance_{config.specialization.value}_{method}",
            "version": "1.0",
            "domain": "finance",
            "task": f"{config.specialization.value} {method} operations",
            "knowledge_selector": knowledge_selector,
            "token_budget": token_budget,
            "instructions_template": instructions_template,
            "example_templates": example_templates,
            "output_schema": self._get_output_schema(method, config),
        }

        return base_config

    def _get_token_budgets(self, method: str) -> dict[str, int]:
        """Get token budgets by method"""
        budgets = {
            "plan": {"frameworks": 800, "domain_knowledge": 600, "history": 400, "constraints": 200},
            "solve": {"knowledge": 1000, "examples": 600, "tools": 400, "validation": 200},
            "chat": {"vocabulary": 400, "safety": 200, "tone": 150, "history": 250},
            "use": {"tool_schemas": 600, "permissions": 200, "examples": 300, "safety": 200},
            "remember": {"context": 500, "indexing": 200, "relevance": 300},
        }
        return budgets.get(method, {"default": 1000})

    def _select_knowledge_assets(self, config: FinanceContextConfig) -> list[str]:
        """Select relevant knowledge assets based on configuration"""
        assets = []

        if config.include_regulations:
            assets.append("regulations")
            assets.append("compliance_frameworks")

        if config.include_calculations:
            assets.append("risk_metrics")
            assets.append("market_data_structures")

        # Add specialization-specific assets
        if config.specialization in [FinanceSpecialization.RISK_MANAGEMENT, FinanceSpecialization.DERIVATIVES]:
            assets.extend(["risk_metrics", "stress_testing_frameworks"])

        if config.specialization == FinanceSpecialization.COMPLIANCE:
            assets.extend(["regulatory_requirements", "audit_frameworks"])

        return assets

    def _get_safety_constraints(self, config: FinanceContextConfig) -> dict[str, Any]:
        """Get safety constraints based on configuration"""
        return {
            "compliance_level": config.compliance_level,
            "risk_warnings": config.enable_risk_warnings,
            "regulatory_framework": config.regulatory_framework,
            "disclosure_requirements": True,
            "data_sensitivity": "high",
        }

    def _get_plan_config(self, config: FinanceContextConfig) -> dict[str, Any]:
        """Get plan()-specific configuration"""
        return {
            "planning_frameworks": ["risk_assessment_checklist", "regulatory_compliance_checklist", "stakeholder_analysis"],
            "decomposition_patterns": [
                "data_collection -> analysis -> validation -> reporting",
                "risk_identification -> measurement -> mitigation -> monitoring",
            ],
            "constraints": ["regulatory_compliance_required", "risk_management_mandatory", "audit_trail_necessary"],
        }

    def _get_solve_config(self, config: FinanceContextConfig) -> dict[str, Any]:
        """Get solve()-specific configuration"""
        return {
            "calculation_libraries": ["quantitative_models", "risk_calculations", "valuation_methods"],
            "validation_rules": ["regulatory_compliance", "risk_limits", "data_quality_checks"],
            "evidence_requirements": ["data_sources", "methodology_documentation", "assumption_justification"],
        }

    def _get_chat_config(self, config: FinanceContextConfig) -> dict[str, Any]:
        """Get chat()-specific configuration"""
        return {
            "vocabulary": "financial_terminology",
            "tone": "professional_financial",
            "safety_filters": ["investment_advice_disclaimer", "regulatory_disclosure", "risk_warning"],
            "formatting_preferences": ["financial_notation", "regulatory_citations", "risk_disclosures"],
        }

    def _get_use_config(self, config: FinanceContextConfig) -> dict[str, Any]:
        """Get use()-specific configuration"""
        return {
            "tool_categories": {
                "data_sources": self.tool_guides["use"]["read_only"],
                "analytical_tools": self.tool_guides["use"]["analytical"],
                "restricted_access": self.tool_guides["use"]["restricted"],
            },
            "permission_model": "role_based",
            "audit_requirements": True,
            "data_classification": "financial_sensitive",
        }

    def _get_memory_config(self, config: FinanceContextConfig) -> dict[str, Any]:
        """Get remember/recall-specific configuration"""
        return {
            "memory_namespaces": [
                f"finance_{config.specialization.value}",
                f"regulatory_{config.regulatory_framework}",
                "risk_assessments",
                "compliance_decisions",
            ],
            "indexing_strategy": "domain_specific",
            "retention_policy": "regulatory_compliance",
            "privacy_constraints": "financial_data_protection",
        }

    def get_workflow_template(self, workflow_type: str, variant: str | None = None) -> Any:
        """Get workflow template by type and variant"""
        template_key = workflow_type
        if variant:
            template_key = f"{workflow_type}_{variant}"

        return self.workflow_templates.get(template_key)

    def get_conditional_template(self, template_name: str) -> Any:
        """Get conditional logic template"""
        return self.conditional_templates.get(template_name)

    def validate_configuration(self, config: FinanceContextConfig) -> bool:
        """Validate finance configuration"""
        # Add validation logic
        return True

    def _generate_instructions_template(self, method: str, config: FinanceContextConfig) -> str:
        """Generate method-specific instructions template"""

        base_context = f"""You are a {config.specialization.value} specialist operating under {config.regulatory_framework} regulations with {config.compliance_level} compliance requirements."""

        method_instructions = {
            "plan": f"""Your task is to create comprehensive plans for {config.specialization.value} operations.
Focus on regulatory compliance, risk management, and systematic approaches.
Consider {", ".join(config.market_focus)} market factors.""",
            "solve": f"""Your task is to solve {config.specialization.value} problems using quantitative methods and domain expertise.
Apply appropriate risk metrics, calculations, and validation procedures.
Ensure all solutions meet {config.regulatory_framework} regulatory requirements.""",
            "chat": f"""You are communicating about {config.specialization.value} topics.
Use professional financial terminology and maintain regulatory compliance.
Provide clear explanations suitable for the {config.risk_tolerance} risk tolerance context.""",
            "use": f"""You have access to financial tools and data sources for {config.specialization.value} analysis.
Select appropriate tools based on the task requirements and security constraints.
Ensure data usage complies with {config.regulatory_framework} regulations.""",
            "remember": f"""You are organizing and storing {config.specialization.value} information.
Structure memories by domain, regulatory framework, and risk categories.
Maintain audit trails for compliance purposes.""",
        }

        return f"{base_context}\n\n{method_instructions.get(method, 'Perform the requested financial operation.')}"

    def _get_example_templates(self, method: str, config: FinanceContextConfig) -> list[str]:
        """Get method-specific example templates"""

        examples = {
            "plan": [
                "Example: Create risk assessment plan for equity portfolio",
                "Example: Develop compliance monitoring framework",
                "Example: Design stress testing methodology",
            ],
            "solve": [
                "Example: Calculate Value-at-Risk for portfolio",
                "Example: Assess counterparty credit risk",
                "Example: Optimize asset allocation under constraints",
            ],
            "chat": [
                "Example: Explain derivatives pricing to client",
                "Example: Discuss regulatory compliance requirements",
                "Example: Summarize market risk analysis",
            ],
            "use": [
                "Example: Retrieve market data from Bloomberg",
                "Example: Run Monte Carlo risk simulation",
                "Example: Query regulatory filing database",
            ],
            "remember": [
                "Example: Store risk analysis for portfolio XYZ",
                "Example: Remember compliance decision rationale",
                "Example: Archive regulatory change impact",
            ],
        }

        return examples.get(method, [])

    def _get_output_schema(self, method: str, config: FinanceContextConfig) -> dict[str, Any] | None:
        """Get method-specific output schema"""

        schemas = {
            "plan": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string"},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "timeline": {"type": "string"},
                    "risk_factors": {"type": "array", "items": {"type": "string"}},
                    "compliance_requirements": {"type": "array", "items": {"type": "string"}},
                },
            },
            "solve": {
                "type": "object",
                "properties": {
                    "solution": {"type": "string"},
                    "methodology": {"type": "string"},
                    "calculations": {"type": "object"},
                    "confidence_level": {"type": "number", "minimum": 0, "maximum": 1},
                    "risk_assessment": {"type": "string"},
                    "regulatory_compliance": {"type": "boolean"},
                },
            },
            "chat": {
                "type": "object",
                "properties": {
                    "response": {"type": "string"},
                    "risk_disclosure": {"type": "string"},
                    "regulatory_notes": {"type": "array", "items": {"type": "string"}},
                    "follow_up_suggested": {"type": "boolean"},
                },
            },
        }

        return schemas.get(method)
