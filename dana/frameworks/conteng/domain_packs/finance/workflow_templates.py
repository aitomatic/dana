"""Finance Workflow Templates

Pre-built workflow templates for common financial processes.
These provide structured patterns for risk assessment, compliance checking,
portfolio analysis, and reporting workflows.
"""


class WorkflowStep:
    """Represents a step in a financial workflow"""

    def __init__(
        self,
        name: str,
        function_type: str,  # "symbolic" or "neural"
        description: str,
        inputs: list[str],
        outputs: list[str],
        tools: list[str] | None = None,
        validation: list[str] | None = None,
        cost_estimate: str = "medium",  # "low", "medium", "high"
        latency_estimate: str = "medium",  # "low", "medium", "high"
    ):
        self.name = name
        self.function_type = function_type
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.tools = tools or []
        self.validation = validation or []
        self.cost_estimate = cost_estimate
        self.latency_estimate = latency_estimate


class WorkflowTemplate:
    """Base class for financial workflow templates"""

    def __init__(self, name: str, description: str, variant: str = "standard"):
        self.name = name
        self.description = description
        self.variant = variant
        self.steps: list[WorkflowStep] = []
        self.conditional_branches: dict[str, list[WorkflowStep]] = {}
        self.success_criteria: list[str] = []
        self.failure_conditions: list[str] = []

    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)

    def add_conditional_branch(self, condition: str, steps: list[WorkflowStep]):
        """Add a conditional branch to the workflow"""
        self.conditional_branches[condition] = steps

    def get_signature(self) -> str:
        """Get workflow signature for caching and telemetry"""
        step_types = [step.function_type for step in self.steps]
        tools = [tool for step in self.steps for tool in step.tools]
        return f"{self.name}_{self.variant}:{'-'.join(step_types)}:{'-'.join(sorted(set(tools)))}"


class RiskAssessmentTemplate(WorkflowTemplate):
    """Risk Assessment Workflow Template

    Provides structured workflows for:
    - Standard risk assessment
    - Derivatives risk assessment
    - Credit risk assessment
    - Market risk assessment
    """

    def __init__(self, variant: str = "standard"):
        super().__init__(
            name="risk_assessment",
            description="Comprehensive risk assessment workflow for financial instruments and portfolios",
            variant=variant,
        )
        self._build_workflow(variant)

    def _build_workflow(self, variant: str):
        """Build the risk assessment workflow based on variant"""

        if variant == "standard":
            self._build_standard_workflow()
        elif variant == "derivatives":
            self._build_derivatives_workflow()
        elif variant == "credit":
            self._build_credit_workflow()
        elif variant == "market":
            self._build_market_workflow()
        else:
            self._build_standard_workflow()

    def _build_standard_workflow(self):
        """Build standard risk assessment workflow"""

        # Step 1: Data Collection (Symbolic)
        self.add_step(
            WorkflowStep(
                name="collect_data",
                function_type="symbolic",
                description="Gather required financial data and market information",
                inputs=["instrument_id", "portfolio_data"],
                outputs=["market_data", "fundamental_data", "historical_data"],
                tools=["bloomberg_api", "market_data_service", "fundamental_data_api"],
                validation=["data_completeness_check", "data_freshness_check"],
                cost_estimate="medium",
                latency_estimate="low",
            )
        )

        # Step 2: Risk Identification (Neural)
        self.add_step(
            WorkflowStep(
                name="identify_risks",
                function_type="neural",
                description="Identify and categorize potential risks using AI analysis",
                inputs=["market_data", "fundamental_data", "historical_data"],
                outputs=["risk_categories", "risk_factors", "risk_weights"],
                tools=["risk_analyzer", "pattern_recognition"],
                validation=["risk_completeness_check"],
                cost_estimate="high",
                latency_estimate="medium",
            )
        )

        # Step 3: Risk Quantification (Symbolic)
        self.add_step(
            WorkflowStep(
                name="quantify_risks",
                function_type="symbolic",
                description="Calculate risk metrics using established models",
                inputs=["risk_factors", "market_data", "historical_data"],
                outputs=["var_estimates", "expected_shortfall", "risk_metrics"],
                tools=["quantlib", "risk_calculator", "monte_carlo_engine"],
                validation=["model_validation", "parameter_validation"],
                cost_estimate="medium",
                latency_estimate="medium",
            )
        )

        # Step 4: Risk Aggregation (Symbolic)
        self.add_step(
            WorkflowStep(
                name="aggregate_risks",
                function_type="symbolic",
                description="Aggregate individual risks into portfolio-level measures",
                inputs=["var_estimates", "risk_metrics", "correlation_data"],
                outputs=["portfolio_var", "diversification_benefit", "concentration_risk"],
                tools=["portfolio_aggregator", "correlation_calculator"],
                validation=["aggregation_validation"],
                cost_estimate="low",
                latency_estimate="low",
            )
        )

        # Step 5: Risk Reporting (Neural + Symbolic)
        self.add_step(
            WorkflowStep(
                name="generate_report",
                function_type="neural",
                description="Generate comprehensive risk assessment report",
                inputs=["portfolio_var", "risk_metrics", "risk_categories"],
                outputs=["risk_report", "executive_summary", "recommendations"],
                tools=["report_generator", "chart_creator"],
                validation=["report_completeness_check", "regulatory_compliance_check"],
                cost_estimate="medium",
                latency_estimate="medium",
            )
        )

        # Conditional Branches
        self.add_conditional_branch(
            "high_risk_detected",
            [
                WorkflowStep(
                    name="escalate_high_risk",
                    function_type="symbolic",
                    description="Escalate high-risk findings to risk management",
                    inputs=["risk_metrics", "thresholds"],
                    outputs=["escalation_alert", "mitigation_suggestions"],
                    tools=["alert_system", "risk_mitigation_engine"],
                    validation=["escalation_validation"],
                    cost_estimate="low",
                    latency_estimate="low",
                )
            ],
        )

        self.success_criteria = [
            "all_risk_categories_assessed",
            "quantitative_metrics_calculated",
            "regulatory_requirements_met",
            "report_generated_successfully",
        ]

        self.failure_conditions = ["insufficient_data_quality", "model_validation_failed", "regulatory_compliance_violation"]

    def _build_derivatives_workflow(self):
        """Build derivatives-specific risk assessment workflow"""

        # Enhanced workflow for derivatives with additional complexity
        self._build_standard_workflow()

        # Add derivatives-specific steps
        greeks_step = WorkflowStep(
            name="calculate_greeks",
            function_type="symbolic",
            description="Calculate option Greeks and sensitivity measures",
            inputs=["option_data", "market_data"],
            outputs=["delta", "gamma", "theta", "vega", "rho"],
            tools=["options_pricer", "greeks_calculator"],
            validation=["greeks_validation"],
            cost_estimate="medium",
            latency_estimate="low",
        )

        # Insert after risk quantification
        self.steps.insert(3, greeks_step)

        # Add counterparty risk assessment
        counterparty_step = WorkflowStep(
            name="assess_counterparty_risk",
            function_type="neural",
            description="Assess counterparty credit risk for derivatives positions",
            inputs=["counterparty_data", "exposure_data"],
            outputs=["counterparty_ratings", "cvr_estimates", "wrong_way_risk"],
            tools=["credit_analyzer", "exposure_calculator"],
            validation=["counterparty_validation"],
            cost_estimate="high",
            latency_estimate="medium",
        )

        self.steps.insert(4, counterparty_step)


class ComplianceCheckTemplate(WorkflowTemplate):
    """Compliance Check Workflow Template"""

    def __init__(self):
        super().__init__(name="compliance_check", description="Automated compliance checking for financial operations")
        self._build_workflow()

    def _build_workflow(self):
        """Build compliance check workflow"""

        # Step 1: Gather Compliance Requirements (Symbolic)
        self.add_step(
            WorkflowStep(
                name="gather_requirements",
                function_type="symbolic",
                description="Retrieve applicable regulatory requirements",
                inputs=["jurisdiction", "asset_type", "operation_type"],
                outputs=["regulatory_rules", "compliance_checklist"],
                tools=["regulatory_database", "compliance_library"],
                validation=["requirements_completeness"],
                cost_estimate="low",
                latency_estimate="low",
            )
        )

        # Step 2: Data Collection for Compliance (Symbolic)
        self.add_step(
            WorkflowStep(
                name="collect_compliance_data",
                function_type="symbolic",
                description="Collect data required for compliance verification",
                inputs=["compliance_checklist", "transaction_data"],
                outputs=["verification_data", "documentation"],
                tools=["data_collector", "document_retriever"],
                validation=["data_completeness"],
                cost_estimate="medium",
                latency_estimate="low",
            )
        )

        # Step 3: Automated Compliance Checks (Symbolic)
        self.add_step(
            WorkflowStep(
                name="run_automated_checks",
                function_type="symbolic",
                description="Run automated rule-based compliance checks",
                inputs=["regulatory_rules", "verification_data"],
                outputs=["compliance_results", "violations", "warnings"],
                tools=["compliance_engine", "rule_validator"],
                validation=["check_completeness"],
                cost_estimate="medium",
                latency_estimate="low",
            )
        )

        # Step 4: Manual Review Assessment (Neural)
        self.add_step(
            WorkflowStep(
                name="assess_manual_review",
                function_type="neural",
                description="Determine if manual review is required",
                inputs=["compliance_results", "complexity_indicators"],
                outputs=["review_required", "priority_level", "review_scope"],
                tools=["complexity_analyzer", "priority_ranker"],
                validation=["assessment_validation"],
                cost_estimate="high",
                latency_estimate="medium",
            )
        )

        # Step 5: Generate Compliance Report (Symbolic + Neural)
        self.add_step(
            WorkflowStep(
                name="generate_compliance_report",
                function_type="neural",
                description="Generate comprehensive compliance report",
                inputs=["compliance_results", "violations", "review_scope"],
                outputs=["compliance_report", "action_items", "certifications"],
                tools=["report_generator", "certification_engine"],
                validation=["report_validation", "regulatory_format_check"],
                cost_estimate="medium",
                latency_estimate="medium",
            )
        )

        # Conditional branches
        self.add_conditional_branch(
            "violations_detected",
            [
                WorkflowStep(
                    name="escalate_violations",
                    function_type="symbolic",
                    description="Escalate compliance violations",
                    inputs=["violations", "severity_levels"],
                    outputs=["escalation_alerts", "remediation_plan"],
                    tools=["alert_system", "remediation_engine"],
                    validation=["escalation_validation"],
                    cost_estimate="low",
                    latency_estimate="low",
                )
            ],
        )


class PortfolioAnalysisTemplate(WorkflowTemplate):
    """Portfolio Analysis Workflow Template"""

    def __init__(self):
        super().__init__(name="portfolio_analysis", description="Comprehensive portfolio analysis and optimization")
        self._build_workflow()

    def _build_workflow(self):
        """Build portfolio analysis workflow"""

        # Step 1: Portfolio Data Assembly (Symbolic)
        self.add_step(
            WorkflowStep(
                name="assemble_portfolio_data",
                function_type="symbolic",
                description="Gather and organize portfolio holdings and market data",
                inputs=["portfolio_id", "as_of_date"],
                outputs=["holdings_data", "market_prices", "corporate_actions"],
                tools=["portfolio_service", "market_data_api", "corporate_actions_feed"],
                validation=["data_completeness", "price_validation"],
                cost_estimate="medium",
                latency_estimate="low",
            )
        )

        # Step 2: Performance Calculation (Symbolic)
        self.add_step(
            WorkflowStep(
                name="calculate_performance",
                function_type="symbolic",
                description="Calculate portfolio performance metrics",
                inputs=["holdings_data", "market_prices", "benchmark_data"],
                outputs=["returns", "volatility", "sharpe_ratio", "tracking_error"],
                tools=["performance_calculator", "benchmark_analyzer"],
                validation=["calculation_validation"],
                cost_estimate="low",
                latency_estimate="low",
            )
        )

        # Step 3: Risk Analysis (Symbolic + Neural)
        self.add_step(
            WorkflowStep(
                name="analyze_portfolio_risk",
                function_type="neural",
                description="Analyze portfolio risk characteristics and exposures",
                inputs=["holdings_data", "returns", "market_data"],
                outputs=["risk_exposures", "concentration_analysis", "stress_test_results"],
                tools=["risk_analyzer", "stress_testing_engine", "factor_model"],
                validation=["risk_validation"],
                cost_estimate="high",
                latency_estimate="medium",
            )
        )

        # Step 4: Attribution Analysis (Symbolic)
        self.add_step(
            WorkflowStep(
                name="performance_attribution",
                function_type="symbolic",
                description="Decompose portfolio performance by factors",
                inputs=["returns", "benchmark_data", "factor_exposures"],
                outputs=["security_selection", "sector_allocation", "style_factors"],
                tools=["attribution_engine", "factor_analyzer"],
                validation=["attribution_validation"],
                cost_estimate="medium",
                latency_estimate="low",
            )
        )

        # Step 5: Generate Analysis Report (Neural)
        self.add_step(
            WorkflowStep(
                name="generate_analysis_report",
                function_type="neural",
                description="Generate comprehensive portfolio analysis report",
                inputs=["performance_metrics", "risk_exposures", "attribution_results"],
                outputs=["analysis_report", "key_insights", "recommendations"],
                tools=["report_generator", "insight_engine", "chart_creator"],
                validation=["report_completeness"],
                cost_estimate="medium",
                latency_estimate="medium",
            )
        )


class ReportingTemplate(WorkflowTemplate):
    """Financial Reporting Workflow Template"""

    def __init__(self):
        super().__init__(name="reporting", description="Automated financial reporting and notification workflow")
        self._build_workflow()

    def _build_workflow(self):
        """Build reporting workflow"""

        # Step 1: Data Aggregation (Symbolic)
        self.add_step(
            WorkflowStep(
                name="aggregate_report_data",
                function_type="symbolic",
                description="Aggregate data from multiple sources for reporting",
                inputs=["report_specification", "data_sources"],
                outputs=["aggregated_data", "data_lineage"],
                tools=["data_aggregator", "etl_engine"],
                validation=["aggregation_validation", "data_quality_check"],
                cost_estimate="medium",
                latency_estimate="medium",
            )
        )

        # Step 2: Calculation Engine (Symbolic)
        self.add_step(
            WorkflowStep(
                name="perform_calculations",
                function_type="symbolic",
                description="Perform required calculations for the report",
                inputs=["aggregated_data", "calculation_rules"],
                outputs=["calculated_metrics", "derived_values"],
                tools=["calculation_engine", "formula_processor"],
                validation=["calculation_validation"],
                cost_estimate="low",
                latency_estimate="low",
            )
        )

        # Step 3: Regulatory Formatting (Symbolic)
        self.add_step(
            WorkflowStep(
                name="format_for_regulations",
                function_type="symbolic",
                description="Format data according to regulatory requirements",
                inputs=["calculated_metrics", "regulatory_template"],
                outputs=["formatted_report", "compliance_annotations"],
                tools=["regulatory_formatter", "template_engine"],
                validation=["format_validation", "regulatory_compliance"],
                cost_estimate="medium",
                latency_estimate="low",
            )
        )

        # Step 4: Quality Assurance (Symbolic + Neural)
        self.add_step(
            WorkflowStep(
                name="quality_assurance",
                function_type="neural",
                description="Perform quality checks on the generated report",
                inputs=["formatted_report", "historical_reports"],
                outputs=["qa_results", "anomalies", "approval_status"],
                tools=["qa_engine", "anomaly_detector", "trend_analyzer"],
                validation=["qa_validation"],
                cost_estimate="high",
                latency_estimate="medium",
            )
        )

        # Step 5: Distribution (Symbolic)
        self.add_step(
            WorkflowStep(
                name="distribute_report",
                function_type="symbolic",
                description="Distribute report to stakeholders and regulators",
                inputs=["formatted_report", "distribution_list"],
                outputs=["delivery_confirmations", "audit_trail"],
                tools=["distribution_engine", "notification_service"],
                validation=["delivery_validation"],
                cost_estimate="low",
                latency_estimate="low",
            )
        )

        # Conditional branches
        self.add_conditional_branch(
            "qa_failed",
            [
                WorkflowStep(
                    name="handle_qa_failure",
                    function_type="neural",
                    description="Handle quality assurance failures",
                    inputs=["qa_results", "anomalies"],
                    outputs=["corrective_actions", "escalation_alert"],
                    tools=["error_handler", "escalation_engine"],
                    validation=["correction_validation"],
                    cost_estimate="medium",
                    latency_estimate="low",
                )
            ],
        )

        self.add_conditional_branch(
            "regulatory_deadline",
            [
                WorkflowStep(
                    name="expedite_delivery",
                    function_type="symbolic",
                    description="Expedite delivery for regulatory deadlines",
                    inputs=["formatted_report", "priority_distribution"],
                    outputs=["expedited_delivery", "priority_confirmation"],
                    tools=["priority_delivery_service"],
                    validation=["expedite_validation"],
                    cost_estimate="low",
                    latency_estimate="low",
                )
            ],
        )
