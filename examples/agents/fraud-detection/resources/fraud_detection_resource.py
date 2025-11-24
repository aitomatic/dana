"""
FraudDetectionResource - Detects fraud patterns from normalized JSON data.

This resource handles:
- Pattern analysis for fraud indicators
- Risk score calculation (0-100)
- Anomaly detection
- LLM-powered fraud analysis
- Returns comprehensive fraud assessment
"""

import os
import sys
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class FraudDetectionResource(BaseResource):
    """
    Resource for detecting fraud patterns in normalized data.

    Features:
    - Multi-dimensional fraud analysis
    - Risk score calculation (0-100)
    - Pattern recognition for common fraud types
    - LLM-powered anomaly detection
    - Comprehensive fraud indicators
    """

    def __init__(self, resource_id: str | None = None, **kwargs):
        """Initialize the FraudDetectionResource."""
        super().__init__(resource_type="fraud-detection", resource_id=resource_id or "fraud-detection", **kwargs)

    @tool_use
    def detect(self, normalized_data: Dict[str, Any], **kwargs) -> DictParams:
        """
        Detect fraud patterns in normalized data.

        Args:
            normalized_data: Structured JSON data from normalization
            **kwargs: Additional parameters (thresholds, etc.)

        Returns:
            {
                "success": bool,
                "fraud_result": {
                    "risk_score": int (0-100),
                    "fraud_indicators": list,
                    "anomalies": list,
                    "recommendations": list,
                    "confidence": float
                },
                "error": str (if failed)
            }
        """
        try:
            if not normalized_data:
                return {"success": False, "fraud_result": {}, "error": "No normalized data provided for fraud detection"}

            # Use LLM for comprehensive fraud analysis
            fraud_analysis = self._analyze_fraud_with_llm(normalized_data)

            # Apply rule-based checks
            rule_based_indicators = self._apply_fraud_rules(normalized_data)

            # Combine LLM and rule-based results
            combined_result = self._combine_fraud_analysis(fraud_analysis, rule_based_indicators)

            return {"success": True, "fraud_result": combined_result, "error": None}

        except Exception as e:
            return {"success": False, "fraud_result": {}, "error": f"Fraud detection failed: {str(e)}"}

    def _analyze_fraud_with_llm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM for intelligent fraud analysis."""
        try:
            result = self.reason(
                {
                    "task": "Analyze document for fraud indicators and calculate risk score",
                    "input": {"normalized_data": data, "data_completeness": self._assess_data_completeness(data)},
                    "output_schema": {
                        "risk_score": "int (0-100, where 0=no risk, 100=high risk)",
                        "fraud_indicators": [
                            {
                                "indicator": "str (specific fraud indicator)",
                                "severity": "str (low, medium, high)",
                                "description": "str (explanation)",
                                "confidence": "float (0.0-1.0)",
                            }
                        ],
                        "anomalies": [
                            {
                                "anomaly": "str (description of anomaly)",
                                "type": "str (data_inconsistency, unusual_pattern, missing_data, etc.)",
                                "impact": "str (low, medium, high)",
                            }
                        ],
                        "recommendations": ["str (specific recommendation for investigation)"],
                        "overall_confidence": "float (0.0-1.0)",
                        "analysis_notes": "str (summary of findings)",
                    },
                    "context": {
                        "common_fraud_patterns": {
                            "invoice_fraud": ["duplicate_invoice_numbers", "unusual_amounts", "fake_vendors"],
                            "data_inconsistencies": ["mismatched_dates", "invalid_amounts", "missing_required_fields"],
                            "suspicious_patterns": ["round_numbers", "sequential_invoices", "unusual_timing"],
                        },
                        "risk_factors": {
                            "high_risk": ["missing_vendor_info", "unusual_amounts", "data_inconsistencies"],
                            "medium_risk": ["incomplete_data", "unusual_patterns"],
                            "low_risk": ["minor_inconsistencies", "format_issues"],
                        },
                    },
                }
            )

            return result

        except Exception as e:
            # Fallback to rule-based analysis
            return self._analyze_fraud_rule_based(data)

    def _apply_fraud_rules(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply rule-based fraud detection."""
        indicators = []

        # Check for missing critical fields
        critical_fields = ["invoice_id", "date", "amount", "vendor_name"]
        missing_fields = [field for field in critical_fields if not data.get(field)]
        if missing_fields:
            indicators.append(
                {
                    "indicator": f"Missing critical fields: {', '.join(missing_fields)}",
                    "severity": "high",
                    "description": "Document lacks essential information",
                    "confidence": 0.9,
                }
            )

        # Check for unusual amounts
        if "amount" in data and data["amount"]:
            amount = float(data["amount"])
            if amount <= 0:
                indicators.append(
                    {
                        "indicator": "Invalid or zero amount",
                        "severity": "high",
                        "description": "Amount is zero or negative",
                        "confidence": 0.95,
                    }
                )
            elif amount > 100000:  # Unusually high amount
                indicators.append(
                    {
                        "indicator": "Unusually high amount",
                        "severity": "medium",
                        "description": f"Amount ${amount:,.2f} is unusually high",
                        "confidence": 0.7,
                    }
                )

        # Check for data inconsistencies
        if "date" in data and data["date"]:
            if not self._is_valid_date(data["date"]):
                indicators.append(
                    {
                        "indicator": "Invalid date format",
                        "severity": "medium",
                        "description": "Date format is invalid or suspicious",
                        "confidence": 0.8,
                    }
                )

        # Check for suspicious patterns
        if "invoice_id" in data and data["invoice_id"]:
            invoice_id = str(data["invoice_id"])
            if len(invoice_id) < 3:
                indicators.append(
                    {
                        "indicator": "Suspiciously short invoice ID",
                        "severity": "medium",
                        "description": "Invoice ID is unusually short",
                        "confidence": 0.6,
                    }
                )

        return indicators

    def _combine_fraud_analysis(self, llm_analysis: Dict[str, Any], rule_indicators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine LLM and rule-based fraud analysis."""
        # Start with LLM analysis
        result = llm_analysis.copy()

        # Add rule-based indicators
        if "fraud_indicators" not in result:
            result["fraud_indicators"] = []

        result["fraud_indicators"].extend(rule_indicators)

        # Recalculate risk score based on all indicators
        risk_score = self._calculate_risk_score(result["fraud_indicators"])
        result["risk_score"] = risk_score

        # Add anomalies from rule-based checks
        if "anomalies" not in result:
            result["anomalies"] = []

        # Add recommendations
        if "recommendations" not in result:
            result["recommendations"] = []

        # Add specific recommendations based on risk level
        if risk_score >= 80:
            result["recommendations"].append("URGENT: Immediate investigation required")
        elif risk_score >= 60:
            result["recommendations"].append("HIGH PRIORITY: Detailed review recommended")
        elif risk_score >= 40:
            result["recommendations"].append("MEDIUM PRIORITY: Additional verification suggested")
        else:
            result["recommendations"].append("LOW RISK: Standard processing acceptable")

        return result

    def _calculate_risk_score(self, indicators: List[Dict[str, Any]]) -> int:
        """Calculate overall risk score (0-100) based on indicators."""
        if not indicators:
            return 0

        total_score = 0
        total_weight = 0

        for indicator in indicators:
            severity = indicator.get("severity", "low")
            confidence = indicator.get("confidence", 0.5)

            # Weight by severity
            if severity == "high":
                weight = 3
            elif severity == "medium":
                weight = 2
            else:
                weight = 1

            # Calculate score contribution
            score_contribution = weight * confidence * 100
            total_score += score_contribution
            total_weight += weight

        if total_weight == 0:
            return 0

        # Normalize to 0-100 range
        normalized_score = min(100, int(total_score / total_weight))
        return normalized_score

    def _assess_data_completeness(self, data: Dict[str, Any]) -> str:
        """Assess how complete the normalized data is."""
        critical_fields = ["invoice_id", "date", "amount", "vendor_name"]
        present_fields = sum(1 for field in critical_fields if data.get(field))
        completeness = present_fields / len(critical_fields)

        if completeness >= 0.8:
            return "complete"
        elif completeness >= 0.5:
            return "partial"
        else:
            return "incomplete"

    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid."""
        try:
            from datetime import datetime

            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _analyze_fraud_rule_based(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based fraud analysis."""
        indicators = self._apply_fraud_rules(data)
        risk_score = self._calculate_risk_score(indicators)

        return {
            "risk_score": risk_score,
            "fraud_indicators": indicators,
            "anomalies": [],
            "recommendations": ["Rule-based analysis completed"],
            "overall_confidence": 0.6,
            "analysis_notes": "Analysis based on rule-based detection only",
        }
