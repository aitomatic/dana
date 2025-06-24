#!/usr/bin/env python3
"""
Use Case 04: Enterprise System Enhancement

Add AI capabilities to **existing enterprise production systems**
without major rewrites. This demonstrates enhancing legacy infrastructure
while preserving all existing business logic and operational procedures.

Business Value: Enhance enterprise systems without risk
- Add AI to existing production systems with zero business logic changes
- Enhance legacy infrastructure without operational disruption
- Preserve existing monitoring, control, and safety systems
- Gradual AI integration path for critical enterprise systems
- Risk-free AI adoption for mission-critical operations

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import time

from opendxa.dana import dana

# ============================================================================
# Enterprise System Enhancement (Production Line)
# ============================================================================


class SensorArray:
    """LEGACY: Existing sensor reading system (DO NOT CHANGE)"""

    def read_all(self):
        # Simulate reading from actual hardware sensors
        return {
            "temperature_sensors": [85.2, 87.1, 89.3, 92.5],
            "pressure_sensors": [42.1, 43.8, 44.2, 45.0],
            "vibration_sensors": [0.25, 0.28, 0.30, 0.35],
            "flow_sensors": [125.5, 128.2, 130.1, 132.8],
            "timestamp": time.time(),
        }


class ControllerBank:
    """LEGACY: Existing control system (DO NOT CHANGE)"""

    def __init__(self):
        self.current_speed = 100
        self.current_pressure = 45

    def adjust_speed(self, new_speed):
        print(f"   🔧 Controller: Adjusting speed from {self.current_speed} to {new_speed}")
        self.current_speed = new_speed

    def adjust_pressure(self, new_pressure):
        print(f"   🔧 Controller: Adjusting pressure from {self.current_pressure} to {new_pressure}")
        self.current_pressure = new_pressure


class EnterpriseProductionLine:
    """
    ENTERPRISE SYSTEM: Existing production line (PRESERVE ALL EXISTING LOGIC)

    This represents a critical enterprise production system that:
    - Has been running for years in mission-critical operations
    - Cannot be taken offline for major rewrites
    - Must maintain all existing functionality and safety procedures
    - Needs AI enhancement without operational risk
    - Requires regulatory compliance and audit trails
    """

    def __init__(self):
        print("🏭 Initializing enterprise production line...")
        self.sensors = SensorArray()
        self.controllers = ControllerBank()
        self.cycles_completed = 0
        self.total_efficiency = 0.85  # Historical baseline

        # LEGACY: Original quality thresholds (DO NOT CHANGE)
        self.quality_thresholds = {"max_temperature": 95.0, "max_pressure": 50.0, "max_vibration": 0.4, "min_flow": 120.0}

    def check_legacy_thresholds(self, sensor_data):
        """LEGACY: Original threshold-based quality checks (PRESERVE)"""
        issues = []

        avg_temp = sum(sensor_data["temperature_sensors"]) / len(sensor_data["temperature_sensors"])
        if avg_temp > self.quality_thresholds["max_temperature"]:
            issues.append("High temperature detected")

        avg_pressure = sum(sensor_data["pressure_sensors"]) / len(sensor_data["pressure_sensors"])
        if avg_pressure > self.quality_thresholds["max_pressure"]:
            issues.append("High pressure detected")

        return issues

    def handle_ai_recommendations(self, predicted_issues):
        """NEW: Enhanced quality issue handling with AI insights"""
        print("\n🤖 Enhanced AI Quality Management:")

        for issue in predicted_issues:
            print(f"   🚨 AI Predicted Issue: {issue['type']}")
            print(f"   📊 Confidence: {issue['confidence']}%")
            print(f"   ⚡ Recommended Action: {issue['action']}")

            # Take intelligent action based on AI recommendations
            if issue["action"] == "reduce_speed":
                self.controllers.adjust_speed(max(80, self.controllers.current_speed - 10))
            elif issue["action"] == "adjust_pressure":
                self.controllers.adjust_pressure(max(40, self.controllers.current_pressure - 2))

    def run_enhanced_cycle(self):
        """
        ENHANCED: Original cycle logic + NEW AI oversight

        CRITICAL: All original logic preserved, AI only adds new capabilities
        """
        print(f"\n🔄 Running production cycle #{self.cycles_completed + 1}")

        # STEP 1: LEGACY sensor reading (unchanged)
        print("📊 Legacy: Reading sensor data...")
        sensor_data = self.sensors.read_all()

        # STEP 2: LEGACY quality checks (unchanged)
        print("🔍 Legacy: Running threshold-based quality checks...")
        legacy_issues = self.check_legacy_thresholds(sensor_data)

        if legacy_issues:
            print(f"   ⚠️  Legacy system detected {len(legacy_issues)} issues")
            for issue in legacy_issues:
                print(f"   🚨 {issue}")
        else:
            print("   ✅ Legacy checks: All parameters within normal ranges")

        # STEP 3: NEW AI enhancement (added intelligently)
        print("\n🤖 NEW: AI-powered predictive analysis...")
        dana.enable_module_imports()

        try:
            import quality_agent  # Dana module for intelligent quality assessment

            # AI predicts issues before they become critical
            quality_assessment = quality_agent.assess_production_quality(sensor_data)
            predicted_issues = quality_agent.predict_potential_issues(sensor_data)
            efficiency_recommendation = quality_agent.optimize_efficiency(sensor_data)

            print(f"   🧠 AI Quality Assessment: {quality_assessment}")
            print(f"   🔮 AI Predicted Issues: {len(predicted_issues)} potential problems")
            print(f"   📈 AI Efficiency Recommendation: {efficiency_recommendation}")

            # Only act on AI recommendations if they suggest problems
            if predicted_issues:
                self.handle_ai_recommendations(predicted_issues)

            # Update efficiency based on AI recommendations
            if efficiency_recommendation != "maintain current settings":
                print("   🎯 Applying AI efficiency optimization...")
                self.total_efficiency = min(0.98, self.total_efficiency + 0.02)

        finally:
            dana.disable_module_imports()

        # STEP 4: LEGACY cycle completion (unchanged)
        self.cycles_completed += 1
        print(f"✅ Cycle #{self.cycles_completed} completed")
        print(f"📊 Current efficiency: {self.total_efficiency:.1%}")


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================


def main():
    print("🎯 Use Case 04: Enterprise System Enhancement")
    print("=" * 50)

    print("🏭 Demonstrating AI enhancement of enterprise production system...")
    print("🔧 CRITICAL: Zero changes to existing business logic")

    # Initialize the enhanced enterprise system
    production_line = EnterpriseProductionLine()

    print("\n🔄 Running enhanced production cycles...")

    # Run multiple cycles to show AI learning and adaptation
    for _cycle in range(2):
        production_line.run_enhanced_cycle()
        time.sleep(0.5)  # Simulate cycle timing

    print("\n📈 Production Summary:")
    print(f"   🔢 Cycles completed: {production_line.cycles_completed}")
    print(f"   📊 Final efficiency: {production_line.total_efficiency:.1%}")
    print(f"   🚀 Efficiency improvement: +{((production_line.total_efficiency - 0.85) * 100):.1f}%")

    # SUMMARY
    print("\n" + "=" * 50)
    print("✅ Enterprise System Enhancement Success!")
    print("\n💡 Key Benefits:")
    print("   🛡️  ZERO changes to existing business logic")
    print("   🏭 Enhanced mission-critical production systems")
    print("   🤖 AI predictive capabilities complement traditional monitoring")
    print("   🔄 Gradual enhancement path for enterprise systems")
    print("   ⚡ Risk-free AI adoption for operational environments")
    print("   📊 Preserved existing control and safety systems")
    print("   🎯 Improved efficiency without operational disruption")


if __name__ == "__main__":
    main()
