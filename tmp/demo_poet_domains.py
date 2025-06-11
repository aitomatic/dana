#!/usr/bin/env python3
"""
POET Domain Plugins Demonstration

This script demonstrates all four POET domain plugins working with their respective
use cases as outlined in the MVP implementation plan.
"""

from dataclasses import dataclass
from opendxa.dana.poet import poet


# Building Management Use Case
@dataclass
class HVACCommand:
    heating_output: float
    cooling_output: float
    fan_speed: float
    status: str


@poet(domain="building_management")
def control_hvac_zone(current_temp: float, setpoint: float, 
                     occupancy: bool, outdoor_temp: float) -> HVACCommand:
    """Simple HVAC control with POET building intelligence."""
    
    # Simple control logic - POET provides building expertise
    temp_error = current_temp - setpoint
    
    if abs(temp_error) <= 1.0:
        return HVACCommand(0, 0, 20, "Maintaining temperature")
    elif temp_error < -1.0:
        heating_level = min(100, abs(temp_error) * 30)
        return HVACCommand(heating_level, 0, 60, "Heating")
    else:
        cooling_level = min(100, temp_error * 30)
        return HVACCommand(0, cooling_level, 60, "Cooling")


# Financial Services Use Case
@dataclass
class CreditDecision:
    approved: bool
    interest_rate: float = None
    reason: str = ""


@poet(domain="financial_services")
def assess_credit_risk(credit_score: int, annual_income: float, 
                      debt_to_income: float, employment_years: int) -> CreditDecision:
    """Simple credit risk assessment with POET financial intelligence."""
    
    # Simple risk calculation - POET provides normalization and compliance
    risk_score = (
        (credit_score / 850) * 0.4 +
        (min(annual_income / 100000, 1)) * 0.3 +
        (max(0, 1 - debt_to_income / 0.4)) * 0.2 +
        (min(employment_years / 10, 1)) * 0.1
    )
    
    if risk_score >= 0.7:
        return CreditDecision(True, 3.5, "Prime candidate")
    elif risk_score >= 0.5:
        return CreditDecision(True, 5.2, "Standard rate")
    elif risk_score >= 0.3:
        return CreditDecision(True, 7.8, "Subprime rate")
    else:
        return CreditDecision(False, None, "High risk")


# Semiconductor Use Case
@poet(domain="semiconductor")
def analyze_rie_process_issue(pressure: float, power: float, gas_flow_rate: float, 
                             temperature: float, etch_rate: float) -> dict:
    """RIE etching process root cause analysis with POET semiconductor intelligence."""
    
    # Simple root cause analysis - POET provides process expertise
    issues = []
    
    # Basic process analysis
    if etch_rate < 50:  # nm/min
        if pressure > 5.0:
            issues.append("High pressure reducing etch rate")
        if power < 500:
            issues.append("Low power insufficient for etching")
        if gas_flow_rate < 20:
            issues.append("Low gas flow affecting chemistry")
    
    if temperature > 150:
        issues.append("High temperature may cause resist damage")
    
    # Determine root cause
    if issues:
        root_cause = issues[0]  # Primary issue
        confidence = 0.8 if len(issues) == 1 else 0.6
    else:
        root_cause = "Process within normal parameters"
        confidence = 0.9
    
    return {
        "root_cause": root_cause,
        "confidence": confidence,
        "all_issues": issues,
        "recommendations": generate_recommendations(issues)
    }


def generate_recommendations(issues):
    """Generate process recommendations based on identified issues."""
    recommendations = []
    for issue in issues:
        if "pressure" in issue.lower():
            recommendations.append("Check vacuum pump performance and gas leaks")
        elif "power" in issue.lower():
            recommendations.append("Increase RF power gradually and monitor plasma")
        elif "gas flow" in issue.lower():
            recommendations.append("Check MFC calibration and gas supply")
        elif "temperature" in issue.lower():
            recommendations.append("Verify thermal control system operation")
    
    return recommendations if recommendations else ["Process optimization may be needed"]


# Enhanced reason function
@poet(domain="llm_optimization", timeout=10.0)
def enhanced_reasoning(prompt: str) -> str:
    """Enhanced reasoning with POET LLM optimization."""
    # Mock LLM response for demonstration
    if len(prompt) < 20:
        return f"Enhanced response to: {prompt}"
    else:
        return f"Optimized analysis: {prompt[:50]}..."


def demo_building_management():
    """Demonstrate building management POET domain."""
    print("🏢 Building Management Domain Demo")
    print("-" * 40)
    
    # Normal operation
    result = control_hvac_zone(72.0, 72.0, True, 70.0)
    print(f"✅ Normal operation: {result}")
    
    # Heating needed
    result = control_hvac_zone(68.0, 72.0, True, 60.0)
    print(f"🔥 Heating mode: {result}")
    
    # Cooling needed, unoccupied (energy optimization)
    result = control_hvac_zone(76.0, 72.0, False, 85.0)
    print(f"❄️  Cooling with optimization: {result}")


def demo_financial_services():
    """Demonstrate financial services POET domain."""
    print("\n💰 Financial Services Domain Demo")
    print("-" * 40)
    
    # Excellent credit
    result = assess_credit_risk("excellent", "$75,000", "25%", "5 years")
    print(f"✅ Excellent credit: {result}")
    
    # Fair credit with mixed data formats
    result = assess_credit_risk(650, "45K", 0.35, 2.5)
    print(f"⚠️  Fair credit: {result}")
    
    # Poor credit
    result = assess_credit_risk("poor", 25000, 0.65, 0.5)
    print(f"❌ Poor credit: {result}")


def demo_semiconductor():
    """Demonstrate semiconductor POET domain."""
    print("\n🔬 Semiconductor Domain Demo")
    print("-" * 40)
    
    # Normal process
    result = analyze_rie_process_issue(2.0, 800, 50, 100, 75)
    print(f"✅ Normal process: {result}")
    
    # Low etch rate issue
    result = analyze_rie_process_issue(6.0, 400, 15, 120, 25)
    print(f"⚠️  Process issue: {result}")
    
    # High temperature warning
    result = analyze_rie_process_issue(3.0, 1000, 60, 180, 85)
    print(f"🌡️  Temperature warning: {result}")


def demo_llm_optimization():
    """Demonstrate LLM optimization POET domain."""
    print("\n🤖 LLM Optimization Domain Demo")
    print("-" * 40)
    
    # Short prompt optimization
    result = enhanced_reasoning("Help")
    print(f"✅ Short prompt: {result}")
    
    # Complex prompt
    result = enhanced_reasoning("Analyze the quarterly financial performance and provide recommendations")
    print(f"✅ Complex prompt: {result}")


def main():
    """Run all POET domain demonstrations."""
    print("🚀 POET Domain Plugins Demonstration")
    print("=" * 50)
    
    try:
        demo_building_management()
        demo_financial_services() 
        demo_semiconductor()
        demo_llm_optimization()
        
        print("\n🎉 All POET domain demos completed successfully!")
        print("✅ Building Management: HVAC optimization with thermal intelligence")
        print("✅ Financial Services: Data normalization and compliance validation")
        print("✅ Semiconductor: Process validation and root cause analysis")
        print("✅ LLM Optimization: Prompt enhancement and response validation")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()