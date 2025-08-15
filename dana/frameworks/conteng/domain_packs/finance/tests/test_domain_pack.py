"""Unit tests for Finance Domain Pack core functionality"""

import unittest
from ..domain_pack import FinanceDomainPack, FinanceSpecialization, FinanceContextConfig


class TestFinanceDomainPack(unittest.TestCase):
    """Test Finance Domain Pack core functionality"""

    def setUp(self):
        self.domain_pack = FinanceDomainPack()

    def test_initialization(self):
        """Test domain pack initialization"""
        self.assertEqual(self.domain_pack.domain, "finance")
        self.assertIsInstance(self.domain_pack.workflow_templates, dict)
        self.assertIsInstance(self.domain_pack.knowledge_assets, dict)
        self.assertIsInstance(self.domain_pack.conditional_templates, dict)
        self.assertIsInstance(self.domain_pack.tool_guides, dict)

    def test_context_template_generation(self):
        """Test context template generation for different methods"""
        config = FinanceContextConfig(
            specialization=FinanceSpecialization.RISK_MANAGEMENT,
            regulatory_framework="US",
            risk_tolerance="moderate",
            compliance_level="enhanced",
            market_focus=["equity"],
        )

        methods = ["plan", "solve", "chat", "use", "remember"]

        for method in methods:
            with self.subTest(method=method):
                template = self.domain_pack.get_context_template(method, config)
                self.assertIsNotNone(template)
                self.assertEqual(template.domain, "finance")
                self.assertEqual(template.specialization, "risk_management")

    def test_workflow_template_retrieval(self):
        """Test workflow template retrieval"""
        # Test standard workflow
        risk_template = self.domain_pack.get_workflow_template("risk_assessment")
        self.assertIsNotNone(risk_template)
        self.assertEqual(risk_template.name, "risk_assessment")

        # Test workflow variant
        derivatives_template = self.domain_pack.get_workflow_template("risk_assessment", "derivatives")
        self.assertIsNotNone(derivatives_template)
        self.assertEqual(derivatives_template.variant, "derivatives")

    def test_configuration_validation(self):
        """Test configuration validation"""
        valid_config = FinanceContextConfig(
            specialization=FinanceSpecialization.COMPLIANCE,
            regulatory_framework="EU",
            risk_tolerance="conservative",
            compliance_level="strict",
            market_focus=["fixed_income"],
        )

        self.assertTrue(self.domain_pack.validate_configuration(valid_config))


if __name__ == "__main__":
    unittest.main()
