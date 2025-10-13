"""Financial Tool Selection Guides

Provides intelligent tool selection and curation for financial agents.
Integrates with Agent.use() to provide contextual tool recommendations
based on domain expertise, security policies, and task requirements.
"""

from typing import Any
from dataclasses import dataclass
from enum import Enum


class ToolCategory(Enum):
    """Categories of financial tools"""

    MARKET_DATA = "market_data"
    RISK_CALCULATION = "risk_calculation"
    COMPLIANCE_CHECK = "compliance_check"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    REGULATORY_FILING = "regulatory_filing"
    PRICING_MODEL = "pricing_model"
    RESEARCH = "research"
    NOTIFICATION = "notification"


class AccessLevel(Enum):
    """Tool access levels for security"""

    READ_ONLY = "read_only"
    ANALYTICAL = "analytical"
    TRANSACTIONAL = "transactional"
    RESTRICTED = "restricted"


@dataclass
class ToolMetadata:
    """Metadata for financial tools"""

    tool_name: str
    category: ToolCategory
    access_level: AccessLevel
    description: str
    cost_estimate: str  # "low", "medium", "high"
    latency_estimate: str  # "low", "medium", "high"
    data_sensitivity: str  # "public", "sensitive", "confidential"
    regulatory_impact: bool
    audit_required: bool
    supported_regions: list[str]
    rate_limits: dict[str, int] | None = None


@dataclass
class ToolRecommendation:
    """Tool recommendation with context"""

    tool_name: str
    confidence_score: float  # 0.0 to 1.0
    reason: str
    prerequisites: list[str]
    alternatives: list[str]
    cost_benefit_ratio: float


class FinancialToolSelector:
    """Intelligent tool selection for financial operations"""

    def __init__(self):
        self.tool_catalog = self._build_tool_catalog()
        self.method_tool_mapping = self._build_method_mappings()
        self.security_policies = self._build_security_policies()

    def _build_tool_catalog(self) -> dict[str, ToolMetadata]:
        """Build comprehensive financial tool catalog"""
        return {
            # Market Data Tools
            "bloomberg_api": ToolMetadata(
                tool_name="bloomberg_api",
                category=ToolCategory.MARKET_DATA,
                access_level=AccessLevel.READ_ONLY,
                description="Real-time and historical market data from Bloomberg Terminal",
                cost_estimate="high",
                latency_estimate="low",
                data_sensitivity="sensitive",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["US", "EU", "APAC"],
                rate_limits={"requests_per_minute": 1000, "data_points_per_hour": 100000},
            ),
            "refinitiv_eikon": ToolMetadata(
                tool_name="refinitiv_eikon",
                category=ToolCategory.MARKET_DATA,
                access_level=AccessLevel.READ_ONLY,
                description="Financial data and analytics from Refinitiv Eikon",
                cost_estimate="high",
                latency_estimate="medium",
                data_sensitivity="sensitive",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
            "yahoo_finance": ToolMetadata(
                tool_name="yahoo_finance",
                category=ToolCategory.MARKET_DATA,
                access_level=AccessLevel.READ_ONLY,
                description="Free financial data for basic analysis",
                cost_estimate="low",
                latency_estimate="medium",
                data_sensitivity="public",
                regulatory_impact=False,
                audit_required=False,
                supported_regions=["GLOBAL"],
            ),
            # Risk Calculation Tools
            "quantlib": ToolMetadata(
                tool_name="quantlib",
                category=ToolCategory.RISK_CALCULATION,
                access_level=AccessLevel.ANALYTICAL,
                description="Open-source quantitative finance library for pricing and risk",
                cost_estimate="low",
                latency_estimate="medium",
                data_sensitivity="sensitive",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
            "riskmetrics_engine": ToolMetadata(
                tool_name="riskmetrics_engine",
                category=ToolCategory.RISK_CALCULATION,
                access_level=AccessLevel.ANALYTICAL,
                description="Professional risk measurement and portfolio analytics",
                cost_estimate="high",
                latency_estimate="low",
                data_sensitivity="confidential",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["US", "EU"],
            ),
            "monte_carlo_simulator": ToolMetadata(
                tool_name="monte_carlo_simulator",
                category=ToolCategory.RISK_CALCULATION,
                access_level=AccessLevel.ANALYTICAL,
                description="Monte Carlo simulation engine for risk analysis",
                cost_estimate="medium",
                latency_estimate="high",
                data_sensitivity="sensitive",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
            # Compliance Tools
            "aml_screening_engine": ToolMetadata(
                tool_name="aml_screening_engine",
                category=ToolCategory.COMPLIANCE_CHECK,
                access_level=AccessLevel.RESTRICTED,
                description="Anti-money laundering screening and monitoring",
                cost_estimate="high",
                latency_estimate="low",
                data_sensitivity="confidential",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["US", "EU", "UK"],
            ),
            "sanctions_checker": ToolMetadata(
                tool_name="sanctions_checker",
                category=ToolCategory.COMPLIANCE_CHECK,
                access_level=AccessLevel.RESTRICTED,
                description="Real-time sanctions list screening",
                cost_estimate="medium",
                latency_estimate="low",
                data_sensitivity="confidential",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
            "trade_surveillance": ToolMetadata(
                tool_name="trade_surveillance",
                category=ToolCategory.COMPLIANCE_CHECK,
                access_level=AccessLevel.RESTRICTED,
                description="Market abuse and insider trading detection",
                cost_estimate="high",
                latency_estimate="low",
                data_sensitivity="confidential",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["US", "EU"],
            ),
            # Portfolio Analysis Tools
            "portfolio_optimizer": ToolMetadata(
                tool_name="portfolio_optimizer",
                category=ToolCategory.PORTFOLIO_ANALYSIS,
                access_level=AccessLevel.ANALYTICAL,
                description="Mean-variance and multi-factor portfolio optimization",
                cost_estimate="medium",
                latency_estimate="medium",
                data_sensitivity="sensitive",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
            "attribution_engine": ToolMetadata(
                tool_name="attribution_engine",
                category=ToolCategory.PORTFOLIO_ANALYSIS,
                access_level=AccessLevel.ANALYTICAL,
                description="Performance attribution and factor analysis",
                cost_estimate="medium",
                latency_estimate="low",
                data_sensitivity="sensitive",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
            # Research Tools
            "financial_news_feed": ToolMetadata(
                tool_name="financial_news_feed",
                category=ToolCategory.RESEARCH,
                access_level=AccessLevel.READ_ONLY,
                description="Real-time financial news and market commentary",
                cost_estimate="medium",
                latency_estimate="low",
                data_sensitivity="public",
                regulatory_impact=False,
                audit_required=False,
                supported_regions=["GLOBAL"],
            ),
            "sec_edgar_filings": ToolMetadata(
                tool_name="sec_edgar_filings",
                category=ToolCategory.RESEARCH,
                access_level=AccessLevel.READ_ONLY,
                description="SEC regulatory filings and corporate disclosures",
                cost_estimate="low",
                latency_estimate="medium",
                data_sensitivity="public",
                regulatory_impact=False,
                audit_required=False,
                supported_regions=["US"],
            ),
            "analyst_research": ToolMetadata(
                tool_name="analyst_research",
                category=ToolCategory.RESEARCH,
                access_level=AccessLevel.READ_ONLY,
                description="Professional analyst research reports and ratings",
                cost_estimate="high",
                latency_estimate="low",
                data_sensitivity="sensitive",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
            # Notification Tools
            "regulatory_alert_system": ToolMetadata(
                tool_name="regulatory_alert_system",
                category=ToolCategory.NOTIFICATION,
                access_level=AccessLevel.TRANSACTIONAL,
                description="Automated regulatory reporting and alerts",
                cost_estimate="medium",
                latency_estimate="low",
                data_sensitivity="confidential",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["US", "EU"],
            ),
            "client_notification_service": ToolMetadata(
                tool_name="client_notification_service",
                category=ToolCategory.NOTIFICATION,
                access_level=AccessLevel.RESTRICTED,
                description="Secure client communication and reporting",
                cost_estimate="low",
                latency_estimate="low",
                data_sensitivity="confidential",
                regulatory_impact=True,
                audit_required=True,
                supported_regions=["GLOBAL"],
            ),
        }

    def _build_method_mappings(self) -> dict[str, dict[str, list[str]]]:
        """Build mappings of agent methods to recommended tools"""
        return {
            "plan": {
                "primary_tools": ["bloomberg_api", "refinitiv_eikon", "sec_edgar_filings", "financial_news_feed"],
                "analytical_tools": ["portfolio_optimizer", "riskmetrics_engine", "quantlib"],
                "research_tools": ["analyst_research", "sec_edgar_filings", "financial_news_feed"],
            },
            "solve": {
                "calculation_engines": ["quantlib", "riskmetrics_engine", "monte_carlo_simulator", "portfolio_optimizer"],
                "data_sources": ["bloomberg_api", "refinitiv_eikon"],
                "validators": ["aml_screening_engine", "sanctions_checker", "trade_surveillance"],
            },
            "chat": {
                "safe_tools": ["yahoo_finance", "financial_news_feed", "sec_edgar_filings"],
                "formatting_tools": ["client_notification_service"],
            },
            "use": {
                "read_only": ["yahoo_finance", "financial_news_feed", "sec_edgar_filings"],
                "analytical": ["quantlib", "portfolio_optimizer", "attribution_engine", "monte_carlo_simulator"],
                "restricted": [
                    "bloomberg_api",
                    "refinitiv_eikon",
                    "aml_screening_engine",
                    "sanctions_checker",
                    "trade_surveillance",
                    "regulatory_alert_system",
                ],
            },
        }

    def _build_security_policies(self) -> dict[str, Any]:
        """Build security policies for tool access"""
        return {
            "access_control": {
                "read_only": {"requires_auth": False, "audit_level": "minimal", "rate_limiting": True},
                "analytical": {"requires_auth": True, "audit_level": "standard", "rate_limiting": True, "input_validation": True},
                "transactional": {
                    "requires_auth": True,
                    "audit_level": "detailed",
                    "rate_limiting": True,
                    "input_validation": True,
                    "output_monitoring": True,
                    "approval_required": True,
                },
                "restricted": {
                    "requires_auth": True,
                    "audit_level": "comprehensive",
                    "rate_limiting": True,
                    "input_validation": True,
                    "output_monitoring": True,
                    "approval_required": True,
                    "time_based_access": True,
                    "ip_restriction": True,
                },
            },
            "data_classification": {
                "public": {"encryption_required": False, "retention_policy": "standard"},
                "sensitive": {"encryption_required": True, "retention_policy": "regulatory", "access_logging": True},
                "confidential": {
                    "encryption_required": True,
                    "retention_policy": "regulatory",
                    "access_logging": True,
                    "data_masking": True,
                    "geographic_restrictions": True,
                },
            },
        }

    def get_tools_for_method(
        self, method: str, specialization: str | None = None, risk_level: str = "medium", regulatory_framework: str = "US"
    ) -> list[ToolRecommendation]:
        """Get tool recommendations for a specific agent method"""

        if method not in self.method_tool_mapping:
            return []

        method_tools = self.method_tool_mapping[method]
        recommendations = []

        # Get tools for each category
        for category, tools in method_tools.items():
            for tool_name in tools:
                if tool_name in self.tool_catalog:
                    tool = self.tool_catalog[tool_name]

                    # Check if tool is suitable for the context
                    if self._is_tool_suitable(tool, specialization, risk_level, regulatory_framework):
                        recommendation = self._create_recommendation(tool, method, category)
                        recommendations.append(recommendation)

        # Sort by confidence score
        recommendations.sort(key=lambda r: r.confidence_score, reverse=True)
        return recommendations

    def _is_tool_suitable(self, tool: ToolMetadata, specialization: str | None, risk_level: str, regulatory_framework: str) -> bool:
        """Check if tool is suitable for the given context"""

        # Check regional support
        if regulatory_framework not in tool.supported_regions and "GLOBAL" not in tool.supported_regions:
            return False

        # Risk-based filtering
        if risk_level == "low" and tool.cost_estimate == "high":
            return False

        # Specialization-based filtering
        if specialization:
            suitable_tools = self._get_specialization_tools(specialization)
            if tool.tool_name not in suitable_tools:
                return False

        return True

    def _get_specialization_tools(self, specialization: str) -> set[str]:
        """Get tools suitable for specific financial specialization"""

        specialization_mappings = {
            "risk_management": {
                "quantlib",
                "riskmetrics_engine",
                "monte_carlo_simulator",
                "bloomberg_api",
                "refinitiv_eikon",
                "trade_surveillance",
            },
            "portfolio_management": {
                "portfolio_optimizer",
                "attribution_engine",
                "bloomberg_api",
                "refinitiv_eikon",
                "analyst_research",
                "quantlib",
            },
            "compliance": {
                "aml_screening_engine",
                "sanctions_checker",
                "trade_surveillance",
                "regulatory_alert_system",
                "sec_edgar_filings",
            },
            "derivatives": {"quantlib", "monte_carlo_simulator", "bloomberg_api", "riskmetrics_engine", "trade_surveillance"},
            "wealth_management": {
                "portfolio_optimizer",
                "client_notification_service",
                "analyst_research",
                "refinitiv_eikon",
                "aml_screening_engine",
            },
        }

        return specialization_mappings.get(specialization, set())

    def _create_recommendation(self, tool: ToolMetadata, method: str, category: str) -> ToolRecommendation:
        """Create tool recommendation with scoring"""

        # Calculate confidence score based on multiple factors
        confidence = 0.5  # Base confidence

        # Method-specific bonuses
        method_bonuses = {
            "plan": {"market_data": 0.3, "research": 0.2},
            "solve": {"risk_calculation": 0.4, "portfolio_analysis": 0.3},
            "chat": {"research": 0.3},
            "use": {"market_data": 0.2, "risk_calculation": 0.2},
        }

        if method in method_bonuses and tool.category.value in method_bonuses[method]:
            confidence += method_bonuses[method][tool.category.value]

        # Cost efficiency bonus
        if tool.cost_estimate == "low":
            confidence += 0.1
        elif tool.cost_estimate == "high":
            confidence -= 0.1

        # Latency bonus
        if tool.latency_estimate == "low":
            confidence += 0.1

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        # Generate reason
        reason = self._generate_recommendation_reason(tool, method, category)

        # Get alternatives
        alternatives = self._find_alternative_tools(tool)

        # Calculate cost-benefit ratio
        cost_benefit = self._calculate_cost_benefit_ratio(tool)

        return ToolRecommendation(
            tool_name=tool.tool_name,
            confidence_score=confidence,
            reason=reason,
            prerequisites=self._get_tool_prerequisites(tool),
            alternatives=alternatives,
            cost_benefit_ratio=cost_benefit,
        )

    def _generate_recommendation_reason(self, tool: ToolMetadata, method: str, category: str) -> str:
        """Generate human-readable reason for tool recommendation"""

        reasons = {
            ("plan", "market_data"): f"Essential for market research and planning: {tool.description}",
            ("solve", "risk_calculation"): f"Quantitative analysis capability: {tool.description}",
            ("chat", "research"): f"Safe information source for client communication: {tool.description}",
            ("use", "analytical"): f"Analytical tool for complex calculations: {tool.description}",
        }

        key = (method, tool.category.value)
        return reasons.get(key, f"Recommended {tool.category.value} tool: {tool.description}")

    def _find_alternative_tools(self, tool: ToolMetadata) -> list[str]:
        """Find alternative tools in the same category"""
        alternatives = []

        for tool_name, other_tool in self.tool_catalog.items():
            if other_tool.category == tool.category and tool_name != tool.tool_name and other_tool.access_level == tool.access_level:
                alternatives.append(tool_name)

        return alternatives[:3]  # Limit to top 3 alternatives

    def _get_tool_prerequisites(self, tool: ToolMetadata) -> list[str]:
        """Get prerequisites for using a tool"""
        prerequisites = []

        if tool.access_level in [AccessLevel.RESTRICTED, AccessLevel.TRANSACTIONAL]:
            prerequisites.append("authentication_required")
            prerequisites.append("authorization_approval")

        if tool.regulatory_impact:
            prerequisites.append("regulatory_compliance_check")

        if tool.audit_required:
            prerequisites.append("audit_logging_enabled")

        if tool.data_sensitivity == "confidential":
            prerequisites.append("data_encryption_enabled")
            prerequisites.append("secure_network_connection")

        return prerequisites

    def _calculate_cost_benefit_ratio(self, tool: ToolMetadata) -> float:
        """Calculate cost-benefit ratio for tool usage"""

        # Simple cost-benefit scoring (in practice, this would be more sophisticated)
        cost_scores = {"low": 1.0, "medium": 2.0, "high": 3.0}
        latency_scores = {"low": 3.0, "medium": 2.0, "high": 1.0}

        cost = cost_scores.get(tool.cost_estimate, 2.0)
        benefit = latency_scores.get(tool.latency_estimate, 2.0)

        # Add regulatory benefit
        if tool.regulatory_impact:
            benefit += 1.0

        return benefit / cost

    def get_tool_security_policy(self, tool_name: str) -> dict[str, Any]:
        """Get security policy for a specific tool"""

        if tool_name not in self.tool_catalog:
            return {}

        tool = self.tool_catalog[tool_name]
        access_policy = self.security_policies["access_control"][tool.access_level.value]
        data_policy = self.security_policies["data_classification"][tool.data_sensitivity]

        return {
            "tool_name": tool_name,
            "access_level": tool.access_level.value,
            "access_policy": access_policy,
            "data_policy": data_policy,
            "audit_required": tool.audit_required,
            "regulatory_impact": tool.regulatory_impact,
        }

    def get_method_tool_summary(self, method: str) -> dict[str, Any]:
        """Get summary of available tools for a method"""

        tools = self.get_tools_for_method(method)

        summary = {
            "method": method,
            "total_tools": len(tools),
            "by_category": {},
            "by_access_level": {},
            "high_confidence": [t for t in tools if t.confidence_score > 0.7],
            "cost_efficient": [t for t in tools if t.cost_benefit_ratio > 1.5],
        }

        # Group by category
        for tool_name in [t.tool_name for t in tools]:
            if tool_name in self.tool_catalog:
                tool = self.tool_catalog[tool_name]
                category = tool.category.value
                access_level = tool.access_level.value

                if category not in summary["by_category"]:
                    summary["by_category"][category] = []
                summary["by_category"][category].append(tool_name)

                if access_level not in summary["by_access_level"]:
                    summary["by_access_level"][access_level] = []
                summary["by_access_level"][access_level].append(tool_name)

        return summary
