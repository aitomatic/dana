"""Financial Knowledge Assets

Domain-specific knowledge assets for financial applications.
These provide pre-structured financial knowledge including regulations,
risk metrics, compliance frameworks, and market data structures.
"""

from typing import Any
from dataclasses import dataclass
from enum import Enum


class AssetType(Enum):
    """Types of knowledge assets"""

    DOCUMENTARY = "documentary"  # DK - Facts, regulations, definitions
    CONTEXTUAL = "contextual"  # CK - Frameworks, methodologies, patterns
    AUXILIARY = "auxiliary"  # AK - Supporting data, examples, templates


@dataclass
class KnowledgeAsset:
    """Base knowledge asset structure"""

    asset_id: str
    name: str
    asset_type: AssetType
    domain: str
    version: str
    description: str
    content: dict[str, Any]
    metadata: dict[str, Any]
    freshness_ttl: int  # Time-to-live in hours
    trust_tier: str  # "high", "medium", "low"
    provenance: list[str]  # Source citations


class FinancialRegulations(KnowledgeAsset):
    """Financial Regulations Knowledge Asset"""

    def __init__(self):
        super().__init__(
            asset_id="fin_reg_v1",
            name="Financial Regulations",
            asset_type=AssetType.DOCUMENTARY,
            domain="finance",
            version="1.0",
            description="Comprehensive financial regulatory requirements by jurisdiction",
            content=self._build_regulations_content(),
            metadata={
                "jurisdictions": ["US", "EU", "UK", "APAC"],
                "asset_classes": ["equity", "fixed_income", "derivatives", "alternatives"],
                "regulatory_bodies": ["SEC", "CFTC", "FINRA", "FCA", "ESMA", "ECB"],
            },
            freshness_ttl=168,  # 1 week
            trust_tier="high",
            provenance=["sec.gov", "cftc.gov", "finra.org", "fca.org.uk", "esma.europa.eu"],
        )

    def _build_regulations_content(self) -> dict[str, Any]:
        """Build comprehensive financial regulations content"""
        return {
            "us_regulations": {
                "securities_act_1933": {
                    "summary": "Regulates the offering and sale of securities to the public",
                    "key_provisions": [
                        "Registration requirements for new securities",
                        "Disclosure obligations for issuers",
                        "Anti-fraud provisions",
                        "Private placement exemptions",
                    ],
                    "applicability": ["public_offerings", "private_placements"],
                    "penalties": "Civil and criminal penalties for violations",
                },
                "securities_exchange_act_1934": {
                    "summary": "Regulates secondary trading of securities and market participants",
                    "key_provisions": [
                        "Broker-dealer registration and regulation",
                        "Market manipulation prohibitions",
                        "Insider trading restrictions",
                        "Periodic reporting requirements",
                    ],
                    "applicability": ["broker_dealers", "investment_advisers", "public_companies"],
                },
                "dodd_frank_act": {
                    "summary": "Post-2008 financial reform legislation",
                    "key_provisions": [
                        "Volcker Rule restrictions on proprietary trading",
                        "Derivatives clearing and reporting requirements",
                        "Systemically important financial institutions oversight",
                        "Consumer protection regulations",
                    ],
                    "applicability": ["banks", "derivatives_dealers", "swap_dealers"],
                },
            },
            "eu_regulations": {
                "mifid_ii": {
                    "summary": "Markets in Financial Instruments Directive II",
                    "key_provisions": [
                        "Best execution requirements",
                        "Client categorization and protection",
                        "Transaction reporting obligations",
                        "Research unbundling rules",
                    ],
                    "applicability": ["investment_firms", "trading_venues", "data_providers"],
                },
                "emir": {
                    "summary": "European Market Infrastructure Regulation",
                    "key_provisions": [
                        "Derivatives clearing obligations",
                        "Risk mitigation for non-cleared derivatives",
                        "Trade repository reporting",
                        "Central counterparty authorization",
                    ],
                    "applicability": ["derivatives_counterparties", "ccps", "trade_repositories"],
                },
            },
            "risk_management_requirements": {
                "basel_iii": {
                    "capital_requirements": {
                        "common_equity_tier_1": "4.5% minimum ratio",
                        "tier_1_capital": "6% minimum ratio",
                        "total_capital": "8% minimum ratio",
                        "capital_conservation_buffer": "2.5% additional requirement",
                    },
                    "liquidity_requirements": {"lcr": "Liquidity Coverage Ratio >= 100%", "nsfr": "Net Stable Funding Ratio >= 100%"},
                },
                "var_requirements": {
                    "model_approval": "Regulatory approval required for internal models",
                    "backtesting": "Daily backtesting with traffic light system",
                    "stress_testing": "Regular stress testing and scenario analysis",
                },
            },
            "compliance_frameworks": {
                "aml_kyc": {
                    "customer_identification": [
                        "Identity verification procedures",
                        "Beneficial ownership identification",
                        "PEP screening requirements",
                    ],
                    "transaction_monitoring": ["Suspicious activity detection", "Transaction pattern analysis", "Cross-border reporting"],
                    "record_keeping": ["5-year minimum retention", "Audit trail requirements", "Regulatory access provisions"],
                },
                "fiduciary_duty": {
                    "investment_advisers": [
                        "Duty of care in investment decisions",
                        "Duty of loyalty to clients",
                        "Full disclosure of conflicts of interest",
                    ],
                    "broker_dealers": ["Suitability obligations", "Best execution requirements", "Fair dealing principles"],
                },
            },
        }


class RiskMetrics(KnowledgeAsset):
    """Risk Metrics Knowledge Asset"""

    def __init__(self):
        super().__init__(
            asset_id="risk_metrics_v1",
            name="Risk Metrics and Models",
            asset_type=AssetType.CONTEXTUAL,
            domain="finance",
            version="1.0",
            description="Comprehensive risk measurement methodologies and models",
            content=self._build_risk_metrics_content(),
            metadata={
                "risk_types": ["market", "credit", "operational", "liquidity"],
                "methodologies": ["var", "expected_shortfall", "monte_carlo", "historical_simulation"],
                "time_horizons": ["1_day", "10_day", "1_month", "1_year"],
            },
            freshness_ttl=24,  # 1 day
            trust_tier="high",
            provenance=["risk_management_association", "basel_committee", "academic_research"],
        )

    def _build_risk_metrics_content(self) -> dict[str, Any]:
        """Build risk metrics and models content"""
        return {
            "value_at_risk": {
                "definition": "Maximum potential loss at a given confidence level over a specific time horizon",
                "methodologies": {
                    "parametric": {
                        "description": "Assumes normal distribution of returns",
                        "formula": "VaR = μ + σ × z_α × √t",
                        "pros": ["Fast computation", "Simple to understand"],
                        "cons": ["Normality assumption", "Fat tail underestimation"],
                        "use_cases": ["linear_portfolios", "quick_estimates"],
                    },
                    "historical_simulation": {
                        "description": "Uses historical return distribution",
                        "formula": "VaR = Percentile(historical_returns, α)",
                        "pros": ["No distribution assumptions", "Captures fat tails"],
                        "cons": ["Limited by historical data", "Assumes stationarity"],
                        "use_cases": ["non_linear_portfolios", "complex_instruments"],
                    },
                    "monte_carlo": {
                        "description": "Simulates future portfolio values using random sampling",
                        "formula": "VaR = Percentile(simulated_returns, α)",
                        "pros": ["Flexible modeling", "Handles complex portfolios"],
                        "cons": ["Computationally intensive", "Model risk"],
                        "use_cases": ["exotic_derivatives", "path_dependent_instruments"],
                    },
                },
                "confidence_levels": {
                    "95%": "Standard for internal risk management",
                    "99%": "Regulatory requirement for market risk capital",
                    "99.9%": "Stress testing and capital planning",
                },
            },
            "expected_shortfall": {
                "definition": "Expected loss beyond the VaR threshold",
                "formula": "ES = E[Loss | Loss > VaR]",
                "advantages": ["Coherent risk measure", "Tail risk sensitivity", "Optimization friendly"],
                "calculation_methods": {
                    "analytical": "For normal distributions: ES = σ × φ(z_α) / α",
                    "empirical": "Average of losses beyond VaR in historical/simulated data",
                },
            },
            "stress_testing": {
                "scenario_types": {
                    "historical_scenarios": [
                        "1987 Black Monday",
                        "2008 Financial Crisis",
                        "COVID-19 Pandemic",
                        "European Sovereign Debt Crisis",
                    ],
                    "hypothetical_scenarios": [
                        "Interest rate shock",
                        "Credit spread widening",
                        "Equity market crash",
                        "Currency devaluation",
                    ],
                },
                "stress_test_types": {
                    "sensitivity_analysis": "Impact of single factor movements",
                    "scenario_analysis": "Impact of multiple correlated factor movements",
                    "reverse_stress_testing": "Scenarios that would cause specific loss levels",
                },
            },
            "credit_risk_metrics": {
                "probability_of_default": {
                    "structural_models": {
                        "merton_model": "Default when asset value < debt value",
                        "kmv_model": "Distance-to-default based approach",
                    },
                    "reduced_form_models": {
                        "hazard_rate_models": "Intensity-based default modeling",
                        "credit_migration_models": "Rating transition probability matrices",
                    },
                },
                "loss_given_default": {
                    "recovery_rates": {
                        "senior_secured": "Typically 60-80%",
                        "senior_unsecured": "Typically 40-60%",
                        "subordinated": "Typically 20-40%",
                    },
                    "factors": ["Collateral quality", "Seniority ranking", "Industry sector", "Economic cycle"],
                },
                "exposure_at_default": {
                    "committed_facilities": "Include undrawn amounts with credit conversion factors",
                    "derivatives": "Potential future exposure calculations",
                    "securities_financing": "Mark-to-market plus add-ons",
                },
            },
            "liquidity_risk_metrics": {
                "liquidity_coverage_ratio": {
                    "formula": "LCR = High Quality Liquid Assets / Net Cash Outflows (30 days)",
                    "minimum_requirement": "100%",
                    "components": {
                        "hqla": ["central_bank_reserves", "government_bonds", "covered_bonds"],
                        "outflows": ["retail_deposits", "wholesale_funding", "derivatives"],
                    },
                },
                "net_stable_funding_ratio": {
                    "formula": "NSFR = Available Stable Funding / Required Stable Funding",
                    "minimum_requirement": "100%",
                    "time_horizon": "1 year",
                },
            },
        }


class ComplianceFrameworks(KnowledgeAsset):
    """Compliance Frameworks Knowledge Asset"""

    def __init__(self):
        super().__init__(
            asset_id="compliance_fw_v1",
            name="Compliance Frameworks",
            asset_type=AssetType.CONTEXTUAL,
            domain="finance",
            version="1.0",
            description="Structured compliance frameworks and checklists",
            content=self._build_compliance_content(),
            metadata={
                "framework_types": ["aml", "kyc", "fiduciary", "market_conduct"],
                "jurisdictions": ["US", "EU", "UK", "GLOBAL"],
                "business_lines": ["investment_management", "banking", "brokerage"],
            },
            freshness_ttl=720,  # 30 days
            trust_tier="high",
            provenance=["regulatory_authorities", "industry_associations", "compliance_standards"],
        )

    def _build_compliance_content(self) -> dict[str, Any]:
        """Build compliance frameworks content"""
        return {
            "aml_framework": {
                "risk_assessment": {
                    "customer_risk_factors": [
                        "Geographic location",
                        "Business activities",
                        "Expected transaction patterns",
                        "Delivery channels used",
                    ],
                    "product_risk_factors": ["Complexity of product", "Cash intensity", "Cross-border nature", "Anonymous features"],
                    "geographic_risk_factors": [
                        "FATF blacklisted countries",
                        "High-risk jurisdictions",
                        "Sanctions lists",
                        "Tax haven status",
                    ],
                },
                "customer_due_diligence": {
                    "standard_cdd": [
                        "Identity verification",
                        "Address verification",
                        "Source of funds understanding",
                        "Purpose of relationship",
                    ],
                    "enhanced_cdd": [
                        "Senior management approval",
                        "Enhanced monitoring",
                        "Source of wealth verification",
                        "Ongoing relationship reviews",
                    ],
                    "simplified_cdd": ["Lower risk customers only", "Reduced verification requirements", "Periodic reviews sufficient"],
                },
            },
            "kyc_framework": {
                "individual_customers": {
                    "required_information": [
                        "Full legal name",
                        "Date of birth",
                        "Residential address",
                        "Identification number",
                        "Occupation",
                    ],
                    "verification_methods": [
                        "Government-issued photo ID",
                        "Utility bill for address",
                        "Bank statements",
                        "Employment verification",
                    ],
                },
                "corporate_customers": {
                    "required_information": [
                        "Company name and registration",
                        "Business address",
                        "Nature of business",
                        "Ownership structure",
                        "Authorized signatories",
                    ],
                    "beneficial_ownership": [
                        "25% ownership threshold",
                        "Control through voting rights",
                        "Ultimate controlling persons",
                        "Complex structures analysis",
                    ],
                },
            },
            "fiduciary_framework": {
                "investment_advisers": {
                    "duty_of_care": [
                        "Reasonable investment advice",
                        "Adequate research and analysis",
                        "Monitoring of investments",
                        "Timely communication",
                    ],
                    "duty_of_loyalty": [
                        "Client interests first",
                        "Conflict disclosure",
                        "Fair allocation of opportunities",
                        "Prohibition on self-dealing",
                    ],
                },
                "suitability_framework": {
                    "customer_profile": [
                        "Investment objectives",
                        "Risk tolerance",
                        "Time horizon",
                        "Financial situation",
                        "Investment experience",
                    ],
                    "product_analysis": ["Risk characteristics", "Complexity level", "Cost structure", "Liquidity features"],
                },
            },
            "market_conduct": {
                "best_execution": {
                    "execution_factors": ["Price", "Speed of execution", "Likelihood of execution", "Size of order", "Market impact"],
                    "venue_selection": [
                        "Regular venue assessments",
                        "Execution quality monitoring",
                        "Client disclosure requirements",
                        "Order routing policies",
                    ],
                },
                "market_abuse_prevention": {
                    "insider_dealing": [
                        "Inside information identification",
                        "Chinese walls",
                        "Personal account dealing",
                        "Information barriers",
                    ],
                    "market_manipulation": [
                        "Price manipulation detection",
                        "Volume manipulation monitoring",
                        "False information prohibition",
                        "Layering and spoofing prevention",
                    ],
                },
            },
        }


class MarketDataStructures(KnowledgeAsset):
    """Market Data Structures Knowledge Asset"""

    def __init__(self):
        super().__init__(
            asset_id="market_data_v1",
            name="Market Data Structures",
            asset_type=AssetType.AUXILIARY,
            domain="finance",
            version="1.0",
            description="Standard market data structures and schemas for financial analysis",
            content=self._build_market_data_content(),
            metadata={
                "asset_classes": ["equity", "fixed_income", "derivatives", "fx", "commodities"],
                "data_types": ["prices", "volumes", "fundamentals", "corporate_actions"],
                "formats": ["json", "xml", "csv", "fixml"],
            },
            freshness_ttl=1,  # 1 hour
            trust_tier="medium",
            provenance=["market_data_vendors", "exchanges", "industry_standards"],
        )

    def _build_market_data_content(self) -> dict[str, Any]:
        """Build market data structures content"""
        return {
            "equity_data": {
                "price_data": {
                    "fields": {
                        "symbol": "Ticker symbol",
                        "last_price": "Most recent trade price",
                        "bid_price": "Best bid price",
                        "ask_price": "Best ask price",
                        "volume": "Trading volume",
                        "timestamp": "Data timestamp",
                    },
                    "example": {
                        "symbol": "AAPL",
                        "last_price": 150.25,
                        "bid_price": 150.24,
                        "ask_price": 150.26,
                        "volume": 1234567,
                        "timestamp": "2024-01-15T15:30:00Z",
                    },
                },
                "fundamental_data": {
                    "fields": {
                        "market_cap": "Market capitalization",
                        "pe_ratio": "Price-to-earnings ratio",
                        "dividend_yield": "Annual dividend yield",
                        "book_value": "Book value per share",
                        "revenue": "Annual revenue",
                        "earnings": "Annual earnings",
                    }
                },
            },
            "fixed_income_data": {
                "bond_data": {
                    "fields": {
                        "isin": "International Securities Identification Number",
                        "cusip": "CUSIP identifier",
                        "price": "Clean price",
                        "yield": "Yield to maturity",
                        "duration": "Modified duration",
                        "convexity": "Convexity measure",
                        "maturity_date": "Maturity date",
                        "coupon_rate": "Coupon rate",
                    }
                }
            },
            "derivatives_data": {
                "options_data": {
                    "fields": {
                        "underlying": "Underlying asset symbol",
                        "strike": "Strike price",
                        "expiry": "Expiration date",
                        "option_type": "Call or Put",
                        "premium": "Option premium",
                        "implied_volatility": "Implied volatility",
                        "delta": "Delta",
                        "gamma": "Gamma",
                        "theta": "Theta",
                        "vega": "Vega",
                    }
                }
            },
            "risk_data_schemas": {
                "portfolio_risk": {
                    "fields": {
                        "portfolio_id": "Portfolio identifier",
                        "var_1d": "1-day Value at Risk",
                        "var_10d": "10-day Value at Risk",
                        "expected_shortfall": "Expected Shortfall",
                        "maximum_drawdown": "Maximum drawdown",
                        "sharpe_ratio": "Sharpe ratio",
                        "volatility": "Portfolio volatility",
                    }
                }
            },
        }
