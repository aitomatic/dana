#!/usr/bin/env python3
"""
Multi-Agent Conversational Defect Response Demo

Demonstrates deterministic autonomy with multi-agent coordination:
- ProductionManagerAgent (coordinator) interfaces with user
- DefectSpecialistAgent (specialist) conducts systematic investigation
- Workflow ensures ALL steps executed (can't skip)
- Human-in-the-loop at strategic approval points

Scenario: Novel defect pattern detected during production
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "dana_agent"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.production_manager_agent import ProductionManagerAgent
from agents.defect_specialist_agent import DefectSpecialistAgent
from workflows.novel_defect_investigation_workflow import NovelDefectInvestigationWorkflow


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}\n")


def print_defect_alert():
    """Display initial defect alert."""
    print("""
🚨 DEFECT ALERT - Inline Inspection System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Wafer Lot: ABC123
Product: CPU_7nm_A53
Defect Type: UNKNOWN (not in defect library)
Pattern: Circular clusters, ~5μm diameter
Location: Wafer edge, 120° sector, repeating
Frequency: 15% of wafers affected
Process Step: Resist spray, Chamber 3
Detected: 2025-01-15 14:30

Status: ⚠️  PRODUCTION CONTINUING
Action Required: Investigation needed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def run_demo():
    """Run the conversational defect response demo."""

    print_section("MULTI-AGENT DEFECT RESPONSE DEMO - Deterministic Autonomy")

    # Display defect alert
    print_defect_alert()

    # PHASE 1: Initialize agents and workflows
    print_section("PHASE 1: Initializing Multi-Agent System")

    print("🏗️  Creating ProductionManagerAgent (coordinator)...")
    production_manager = ProductionManagerAgent(
        agent_id="production-manager-001"
    )

    print("🏗️  Creating DefectSpecialistAgent (specialist)...")
    defect_specialist = DefectSpecialistAgent(
        agent_id="defect-specialist-001"
    )

    print("🏗️  Creating NovelDefectInvestigationWorkflow...")
    investigation_workflow = NovelDefectInvestigationWorkflow(
        workflow_id="investigation-001"
    )

    # Wire up agents and workflows
    print("\n🔗 Wiring agent relationships...")
    production_manager.with_agents(defect_specialist=defect_specialist)
    defect_specialist.with_workflows(investigation_workflow=investigation_workflow)

    print("✅ Multi-agent system initialized")

    # PHASE 2: User reports defect to ProductionManager
    print_section("PHASE 2: User Alert → ProductionManager")

    user_message = """We have an unknown defect pattern on lot ABC123.

Details:
- Circular clusters, ~5μm diameter
- Wafer edge, 120° sector
- 15% of wafers affected
- Resist spray process, Chamber 3

What should we do?"""

    print("👤 User (Fab Manager):")
    print(f"   {user_message}\n")

    print("💬 ProductionManager processing alert...")
    # In full version, this would use conversational interface
    # For now, we'll show the delegation directly

    # PHASE 3: ProductionManager delegates to DefectSpecialist
    print_section("PHASE 3: ProductionManager → DefectSpecialist Delegation")

    defect_alert = {
        "lot_id": "ABC123",
        "product": "CPU_7nm_A53",
        "defect_type": "UNKNOWN",
        "pattern": "Circular clusters, ~5μm diameter",
        "location": "Wafer edge, 120° sector, repeating",
        "frequency": "15%",
        "process_step": "Resist spray, Chamber 3",
        "detected": "2025-01-15 14:30"
    }

    print("🔄 ProductionManager: \"I'll engage our defect specialist for systematic investigation.\"")
    print("🔄 ProductionManager: \"This will take approximately 2-3 minutes.\"\n")

    findings = production_manager.delegate_investigation(defect_alert)

    # PHASE 4: Present findings to user
    print_section("PHASE 4: Investigation Findings → User")

    print("📊 ProductionManager presenting findings to user:\n")
    print("━" * 80)
    print("INVESTIGATION COMPLETE")
    print("━" * 80)

    result = findings.get("result", findings) if "result" in findings else findings

    if result.get("success"):
        print(f"\n🎯 ROOT CAUSE (Confidence: {result.get('confidence', 'UNKNOWN')})")
        hypotheses = result.get("hypotheses", [])
        if hypotheses:
            top_hypothesis = hypotheses[0]
            print(f"\nHypothesis #{top_hypothesis['rank']} ({top_hypothesis['confidence']} confidence):")
            print(f"   {top_hypothesis['root_cause']}")

            print(f"\n📋 SUPPORTING EVIDENCE:")
            for evidence in top_hypothesis.get('evidence', []):
                print(f"   • {evidence}")

        # Show correlations
        correlations = result.get("process_correlations", {})
        if correlations.get("correlations_found"):
            print(f"\n🔗 PROCESS CORRELATIONS:")
            primary = correlations.get("primary_correlation", {})
            print(f"   • {primary.get('change', 'Unknown')} ({primary.get('confidence', 'UNKNOWN')} confidence)")

        # Show historical matches
        historical = result.get("historical_matches", {})
        if historical.get("matches_found"):
            print(f"\n🔍 HISTORICAL MATCHES:")
            best_match = historical.get("best_match", {})
            print(f"   • Case {best_match.get('case_id', 'Unknown')} (similarity: {best_match.get('similarity_score', 0):.0%})")
            print(f"     Root cause: {best_match.get('root_cause', 'Unknown')}")

        # Show verification plan
        verification = result.get("verification_plan", {})
        if verification:
            print(f"\n✅ RECOMMENDED VERIFICATION:")
            primary_ver = verification.get("primary_verification", {})
            print(f"   Action: {primary_ver.get('action', 'Unknown')}")
            print(f"   Test: {primary_ver.get('test', 'Unknown')}")
            print(f"   Timeline: {primary_ver.get('timeline', 'Unknown')}")
            print(f"   Reversible: {primary_ver.get('reversible', False)}")

        print(f"\n⏱️  Investigation completed in {result.get('processing_time', 0):.2f}s")

    else:
        print("\n❌ Investigation failed")
        print(f"   Error: {findings.get('error', 'Unknown')}")

    # PHASE 5: Get user approval
    print_section("PHASE 5: User Approval Gate")

    print("💬 ProductionManager:")
    print("   \"Based on investigation findings, I recommend reducing resist spray\"")
    print("   \"pressure to 50 PSI baseline and running 5 monitor wafers to verify.\"")
    print()
    print("   \"This will take approximately 2 hours and cost ~$500 for monitor wafers.\"")
    print()
    print("   \"Risk if wrong: LOW (action is reversible)\"")
    print()
    print("   ❓ Should I proceed with corrective action?")
    print()

    # Simulate user approval
    print("👤 User: \"Yes, proceed\"")
    print()

    print("✅ ProductionManager: \"Approved. I'll coordinate the corrective action.\"")
    print("   (In full system: Would delegate to ProcessEngineerAgent)")

    # Summary
    print_section("DEMO COMPLETE - Key Takeaways")

    print("""
✅ DETERMINISTIC AUTONOMY DEMONSTRATED:

1. MULTI-AGENT COORDINATION:
   • ProductionManager coordinates (user-facing)
   • DefectSpecialist investigates (technical work)
   • Clear separation of concerns

2. SYSTEMATIC INVESTIGATION:
   • NovelDefectInvestigationWorkflow ensured ALL steps executed
   • Pattern characterization ✓
   • Process correlation ✓
   • Historical search ✓
   • Hypothesis generation ✓
   • Verification plan ✓

3. HUMAN-IN-THE-LOOP:
   • User approves production-impacting actions
   • Strategic decisions (approve/reject)
   • Not tactical details

4. PRODUCTION-READY QUALITY:
   • Consistent, systematic investigation every time
   • Workflow guarantees completeness
   • Intelligence at each decision point (WorkflowStepAgent)
   • Mirrors real fab organization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Compare with:
• AUTOMATION: Would just escalate "UNKNOWN_DEFECT" to human queue
• PROBABILISTIC: Might skip investigation, jump to conclusions, inconsistent

DETERMINISTIC AUTONOMY: Systematic + Intelligent + Human-guided = Production-ready
""")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Exiting...")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
