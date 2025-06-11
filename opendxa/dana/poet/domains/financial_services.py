"""
Financial Services Domain Plugin for POET

Provides domain-specific intelligence for financial services applications,
including data normalization, compliance validation, and risk assessment.
"""

import re
from typing import Any, Dict, Tuple
from dataclasses import dataclass


@dataclass
class CreditDecision:
    """Credit decision output."""
    approved: bool
    interest_rate: float = None
    reason: str = ""
    risk_score: float = None


class FinancialServicesPlugin:
    """Domain plugin for financial services with basic compliance and data normalization."""
    
    def __init__(self):
        self.validation_rules = {
            "credit_score": {"min": 300, "max": 850},
            "annual_income": {"min": 0, "max": 10000000},
            "debt_to_income": {"min": 0, "max": 1.0},
            "employment_years": {"min": 0, "max": 50}
        }
        self.audit_log = []
        
    def process_inputs(self, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
        """Process financial data with normalization and validation."""
        
        # Map positional args to named parameters for credit assessment
        if len(args) >= 4:
            credit_score, annual_income, debt_to_income, employment_years = args[:4]
        else:
            credit_score = kwargs.get('credit_score', args[0] if len(args) > 0 else None)
            annual_income = kwargs.get('annual_income', args[1] if len(args) > 1 else None)
            debt_to_income = kwargs.get('debt_to_income', args[2] if len(args) > 2 else None)
            employment_years = kwargs.get('employment_years', args[3] if len(args) > 3 else None)
        
        # Normalize financial data
        normalized = {
            "credit_score": self._normalize_credit_score(credit_score),
            "annual_income": self._normalize_income(annual_income),
            "debt_to_income": self._normalize_ratio(debt_to_income),
            "employment_years": self._normalize_years(employment_years)
        }
        
        # Validate normalized data
        self._validate_financial_data(normalized)
        
        return {
            "args": (
                normalized["credit_score"],
                normalized["annual_income"], 
                normalized["debt_to_income"],
                normalized["employment_years"]
            ),
            "kwargs": {}
        }
    
    def validate_output(self, operation_result: Dict, processed_input: Dict) -> Any:
        """Validate financial decision output with compliance checks."""
        
        result = operation_result["result"]
        
        # Basic compliance validation
        if hasattr(result, 'approved'):
            if result.approved and not hasattr(result, 'interest_rate'):
                raise ValueError("Approved loans must have interest rate specified")
                
            if result.approved and result.interest_rate is not None:
                if not (0.01 <= result.interest_rate <= 50.0):  # 1% to 50% APR
                    raise ValueError(f"Interest rate {result.interest_rate}% outside valid range")
        
        # Generate audit trail
        self._log_decision(result, processed_input)
        
        return result
    
    def _normalize_credit_score(self, score) -> int:
        """Normalize credit score from various formats."""
        if score is None:
            return 650  # Default middle score
            
        if isinstance(score, str):
            # Handle descriptive credit scores
            score_lower = score.lower().strip()
            if 'excellent' in score_lower or 'very good' in score_lower:
                return 780
            elif 'good' in score_lower:
                return 720
            elif 'fair' in score_lower:
                return 650
            elif 'poor' in score_lower or 'bad' in score_lower:
                return 580
            else:
                # Try to extract numeric value
                try:
                    numeric_score = re.findall(r'\d+', score)
                    if numeric_score:
                        return int(numeric_score[0])
                except:
                    pass
                return 650
        
        # Validate numeric range
        score = int(float(score))
        return max(300, min(850, score))
    
    def _normalize_income(self, income) -> float:
        """Normalize income from various formats."""
        if income is None:
            return 0.0
            
        if isinstance(income, str):
            # Handle formats like "$50,000", "50K", "50000", "2.5M"
            cleaned = income.replace(',', '').replace('$', '').replace(' ', '').strip()
            
            # Handle K (thousands) and M (millions)
            if cleaned.lower().endswith('k'):
                try:
                    return float(cleaned[:-1]) * 1000
                except:
                    return 0.0
            elif cleaned.lower().endswith('m'):
                try:
                    return float(cleaned[:-1]) * 1000000
                except:
                    return 0.0
            else:
                try:
                    return float(cleaned)
                except:
                    return 0.0
        
        return max(0.0, float(income))
    
    def _normalize_ratio(self, ratio) -> float:
        """Normalize debt-to-income ratio."""
        if ratio is None:
            return 0.0
            
        if isinstance(ratio, str):
            # Handle percentage format like "25%" or "0.25"
            cleaned = ratio.replace('%', '').strip()
            try:
                value = float(cleaned)
                # If value > 1, assume it's percentage form
                if value > 1:
                    return value / 100.0
                return value
            except:
                return 0.0
        
        ratio = float(ratio)
        # Convert percentage to decimal if needed
        if ratio > 1:
            ratio = ratio / 100.0
        
        return max(0.0, min(1.0, ratio))
    
    def _normalize_years(self, years) -> float:
        """Normalize employment years."""
        if years is None:
            return 0.0
            
        if isinstance(years, str):
            # Handle formats like "2.5 years", "30 months"
            if 'month' in years.lower():
                try:
                    months = float(re.findall(r'\d+\.?\d*', years)[0])
                    return months / 12.0
                except:
                    return 0.0
            else:
                try:
                    return float(re.findall(r'\d+\.?\d*', years)[0])
                except:
                    return 0.0
        
        return max(0.0, min(50.0, float(years)))
    
    def _validate_financial_data(self, data: Dict):
        """Validate normalized financial data against rules."""
        for field, value in data.items():
            if field in self.validation_rules:
                rules = self.validation_rules[field]
                if not (rules["min"] <= value <= rules["max"]):
                    raise ValueError(
                        f"{field} value {value} outside valid range "
                        f"({rules['min']} - {rules['max']})"
                    )
    
    def _log_decision(self, result: Any, processed_input: Dict):
        """Log financial decision for audit trail."""
        try:
            log_entry = {
                "timestamp": "now",  # Would use real timestamp in production
                "decision": "approved" if getattr(result, 'approved', False) else "denied",
                "interest_rate": getattr(result, 'interest_rate', None),
                "reason": getattr(result, 'reason', ''),
                "input_args": processed_input.get("args", [])
            }
            self.audit_log.append(log_entry)
        except Exception:
            # Don't fail the operation if logging fails
            pass