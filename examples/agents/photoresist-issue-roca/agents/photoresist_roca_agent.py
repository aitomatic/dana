"""
PhotoresistROCAgent - Agent specialized in photoresist root cause analysis.

This agent demonstrates the use of structured data resources for semiconductor chemistry:
- RecipeDataResource: Access photoresist formulation data from CSV files
- PolymerDataResource: Query polymer composition and monomer breakdowns from Excel
- MonomerDataResource: Analyze chemical properties and molecular characteristics

The agent can perform complex photoresist analysis workflows like:
- Hierarchical chemical composition analysis
- Root cause analysis of performance issues
- Component compatibility assessment
- Historical pattern matching
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from dana.common.protocols import Notifiable, DictParams
from resources.recipe_data_resource import RecipeDataResource
from resources.polymer_data_resource import PolymerDataResource
from resources.monomer_data_resource import MonomerDataResource


class BroadcastNotificationHandler(Notifiable):
    """Notification handler that prints all broadcast messages."""

    def __init__(self, agent_name: str = "PhotoresistROCAgent", verbose: bool = True):
        """
        Initialize the notification handler.

        Args:
            agent_name: Name of the agent for display purposes
            verbose: Whether to print notifications
        """
        self.agent_name = agent_name
        self.verbose = verbose
        self.message_count = 0

    def notify(self, notifier: object, message: DictParams) -> None:
        """
        Receive and print notification messages.

        Args:
            notifier: The object sending the notification
            message: The notification message
        """
        self.message_count += 1

        # Only print if verbose is enabled
        if not self.verbose:
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Extract notifier information
        notifier_id = getattr(notifier, "object_id", "unknown")
        notifier_type = getattr(notifier, "agent_type", getattr(notifier, "__class__.__name__", "unknown"))

        print(f"\n{'=' * 80}")
        print(f"🔔 NOTIFICATION #{self.message_count} [{timestamp}]")
        print(f"📡 From: {notifier_type} (ID: {notifier_id})")
        print(f"🎯 To: {self.agent_name}")
        print(f"{'=' * 80}")

        # Print message content
        for key, value in message.items():
            if key.startswith("trace_"):
                phase = key.replace("trace_", "").upper()
                print(f"\n📋 {phase} PHASE:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")
            else:
                print(f"\n📝 {key.upper()}:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")

        print(f"{'=' * 80}\n")


class PhotoresistROCAgent(STARAgent):
    """
    Agent specialized in photoresist root cause analysis.

    This agent has access to three structured data resources:
    1. RecipeDataResource - Access photoresist formulation data from CSV files
    2. PolymerDataResource - Query polymer composition and monomer breakdowns from Excel
    3. MonomerDataResource - Analyze chemical properties and molecular characteristics

    The agent can perform complex photoresist analysis workflows like:
    - Hierarchical chemical composition analysis (4-level decomposition)
    - Root cause analysis of performance issues and defects
    - Component compatibility assessment and failure mode analysis
    - Historical pattern matching and correlation analysis
    - Evidence-based problem diagnosis and resolution recommendations
    """

    def __init__(
        self,
        agent_id: str | None = None,
        data_root: str | None = None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1-nano",
        **kwargs,
    ):
        """
        Initialize the PhotoresistROCAgent.

        Args:
            agent_id: Unique identifier for this agent
            data_root: Root directory for data files (defaults to resources directory)
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="photoresist-roca",
            agent_id=agent_id or "photoresist-roca-001",
            llm_provider=llm_provider,
            model=model,
            **kwargs,
        )

        # Set up data paths
        if data_root is None:
            current_dir = Path(__file__).parent
            data_root = current_dir.parent / "resources"

        self.data_root = Path(data_root)

        # Register all structured data resources
        self.with_resources(
            RecipeDataResource(
                resource_id="recipe-data",
                data_path=str(self.data_root / "Recipe_example_data.csv")
            ),
            PolymerDataResource(
                resource_id="polymer-data",
                data_path=str(self.data_root / "Polymer_example_data.xlsx")
            ),
            MonomerDataResource(
                resource_id="monomer-data",
                data_path=str(self.data_root / "Monomer_example_data.xlsx")
            ),
        )

        # Add notification handler
        self.notification_handler = BroadcastNotificationHandler("PhotoresistROCAgent")
        self.with_notifiable(self.notification_handler)

    def enable_notifications(self, verbose: bool = True) -> None:
        """
        Enable or disable notification printing.

        Args:
            verbose: Whether to print notifications
        """
        self.notification_handler.verbose = verbose

    def get_notification_count(self) -> int:
        """
        Get the total number of notifications received.

        Returns:
            Number of notifications received
        """
        return getattr(self.notification_handler, "message_count", 0)

    def analyze_sample(self, sample_name: str) -> DictParams:
        """
        Perform comprehensive analysis of a photoresist sample.

        This method demonstrates the 4-level hierarchical analysis:
        1. Sample ID → Recipe Information
        2. Recipe → Polymer Composition
        3. Polymer → Monomer Breakdown
        4. Monomer → Chemical Properties

        Args:
            sample_name: Name of the sample to analyze (e.g., "AB01", "TEF0001")

        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            print(f"🔬 Starting comprehensive analysis of sample: {sample_name}")
            print("=" * 80)

            # Step 1: Get recipe information
            print("📋 Step 1: Retrieving recipe information...")
            recipe_result = self.get_resource("recipe-data").search_by_sample_name(sample_name)

            if not recipe_result.get("success") or not recipe_result.get("results"):
                return {
                    "success": False,
                    "error": f"No recipe data found for sample: {sample_name}",
                    "analysis_steps": []
                }

            recipe_data = recipe_result["results"][0]
            print(f"   ✅ Found recipe: {recipe_data['sample_name']} ({recipe_data['submitted_name']})")
            print(f"   📅 Created: {recipe_data['creation_date']} by {recipe_data['creator']}")
            print(f"   🎯 Theme: {recipe_data['theme']}")
            print(f"   🧪 Purpose: {recipe_data['preparation_purpose']}")

            # Step 2: Analyze polymer compositions
            print("\n🔬 Step 2: Analyzing polymer compositions...")
            polymer_analyses = []

            for resin in recipe_data.get("resins", []):
                if resin.get("name"):
                    print(f"   🔍 Analyzing resin: {resin['name']}")

                    # Search for polymer data
                    polymer_result = self.get_resource("polymer-data").search_by_composition(resin["name"])

                    if polymer_result.get("success") and polymer_result.get("results"):
                        polymer_data = polymer_result["results"][0]
                        print(f"      ✅ Found polymer: {polymer_data['lot_number']}")
                        print(f"      🧬 Monomers: {polymer_data['monomers']}")
                        print(f"      📊 Ratios: {polymer_data['ratios']}")

                        polymer_analyses.append({
                            "resin_name": resin["name"],
                            "polymer_data": polymer_data,
                            "concentration_phr": resin.get("phr", "N/A")
                        })
                    else:
                        print(f"      ⚠️  No polymer data found for: {resin['name']}")
                        polymer_analyses.append({
                            "resin_name": resin["name"],
                            "polymer_data": None,
                            "concentration_phr": resin.get("phr", "N/A")
                        })

            # Step 3: Analyze monomer properties
            print("\n🧬 Step 3: Analyzing monomer properties...")
            monomer_analyses = []

            for polymer_analysis in polymer_analyses:
                if polymer_analysis["polymer_data"]:
                    polymer_data = polymer_analysis["polymer_data"]

                    for monomer_name in polymer_data["monomers"]:
                        print(f"   🔍 Analyzing monomer: {monomer_name}")

                        # Search for monomer data
                        monomer_result = self.get_resource("monomer-data").search_by_name(monomer_name)

                        if monomer_result.get("success") and monomer_result.get("results"):
                            monomer_data = monomer_result["results"][0]
                            print(f"      ✅ Found monomer: {monomer_data['name']}")
                            print(f"      ⚗️  Type: {monomer_data['type']}")
                            print(f"      ⚖️  MW: {monomer_data['molecular_weight']} g/mol")
                            print(f"      🏢 Team: {monomer_data['team']}")

                            if monomer_data.get("has_properties"):
                                print(f"      📈 Properties: A={monomer_data['prop_a']}, B={monomer_data['prop_b']}")

                            monomer_analyses.append({
                                "monomer_name": monomer_name,
                                "monomer_data": monomer_data,
                                "resin_context": polymer_analysis["resin_name"]
                            })
                        else:
                            print(f"      ⚠️  No monomer data found for: {monomer_name}")
                            monomer_analyses.append({
                                "monomer_name": monomer_name,
                                "monomer_data": None,
                                "resin_context": polymer_analysis["resin_name"]
                            })

            # Step 4: Generate comprehensive analysis report
            print("\n📊 Step 4: Generating comprehensive analysis report...")

            analysis_report = {
                "sample_name": sample_name,
                "recipe_data": recipe_data,
                "polymer_analyses": polymer_analyses,
                "monomer_analyses": monomer_analyses,
                "analysis_summary": {
                    "total_resins": len(recipe_data.get("resins", [])),
                    "total_polymers_found": len([p for p in polymer_analyses if p["polymer_data"]]),
                    "total_monomers_found": len([m for m in monomer_analyses if m["monomer_data"]]),
                    "analysis_completeness": f"{len([m for m in monomer_analyses if m['monomer_data']])}/{len(monomer_analyses)} monomers analyzed"
                }
            }

            print(f"   ✅ Analysis complete!")
            print(f"   📊 Summary: {analysis_report['analysis_summary']['total_resins']} resins, "
                  f"{analysis_report['analysis_summary']['total_polymers_found']} polymers, "
                  f"{analysis_report['analysis_summary']['total_monomers_found']} monomers analyzed")

            return {
                "success": True,
                "analysis_report": analysis_report,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "analysis_report": None
            }

    def diagnose_issue(self, sample_name: str, issue_description: str) -> DictParams:
        """
        Diagnose a specific issue with a photoresist sample.

        This method combines sample analysis with issue-specific diagnosis.

        Args:
            sample_name: Name of the sample with issues
            issue_description: Description of the observed issue

        Returns:
            Dictionary with diagnosis results and recommendations
        """
        try:
            print(f"🔍 Diagnosing issue for sample: {sample_name}")
            print(f"📝 Issue description: {issue_description}")
            print("=" * 80)

            # First, perform comprehensive analysis
            analysis_result = self.analyze_sample(sample_name)

            if not analysis_result.get("success"):
                return analysis_result

            analysis_report = analysis_result["analysis_report"]

            # Analyze the issue in context of the sample composition
            print("\n🔬 Analyzing issue in context of sample composition...")

            # Extract key components for issue analysis
            key_components = []

            # Add resins and their monomers
            for polymer_analysis in analysis_report["polymer_analyses"]:
                if polymer_analysis["polymer_data"]:
                    key_components.append({
                        "type": "resin",
                        "name": polymer_analysis["resin_name"],
                        "monomers": polymer_analysis["polymer_data"]["monomers"],
                        "concentration": polymer_analysis["concentration_phr"]
                    })

            # Add photosensitizers
            for ps in analysis_report["recipe_data"].get("photosensitizers", []):
                if ps.get("name"):
                    key_components.append({
                        "type": "photosensitizer",
                        "name": ps["name"],
                        "concentration": ps.get("phr", "N/A")
                    })

            # Add amines
            for amine in analysis_report["recipe_data"].get("amines", []):
                if amine.get("name"):
                    key_components.append({
                        "type": "amine",
                        "name": amine["name"],
                        "concentration": amine.get("phr", "N/A")
                    })

            # Add additives
            for additive in analysis_report["recipe_data"].get("additives", []):
                if additive.get("name"):
                    key_components.append({
                        "type": "additive",
                        "name": additive["name"],
                        "concentration": additive.get("phr", "N/A")
                    })

            # Generate diagnosis report
            diagnosis_report = {
                "sample_name": sample_name,
                "issue_description": issue_description,
                "key_components": key_components,
                "analysis_report": analysis_report,
                "diagnosis_summary": {
                    "total_components": len(key_components),
                    "component_types": list(set([c["type"] for c in key_components])),
                    "potential_issues": self._identify_potential_issues(issue_description, key_components)
                }
            }

            print(f"   ✅ Diagnosis complete!")
            print(f"   🔍 Identified {len(key_components)} key components")
            print(f"   ⚠️  Potential issues: {len(diagnosis_report['diagnosis_summary']['potential_issues'])}")

            return {
                "success": True,
                "diagnosis_report": diagnosis_report,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Diagnosis failed: {str(e)}",
                "diagnosis_report": None
            }

    def _identify_potential_issues(self, issue_description: str, components: list) -> list:
        """
        Identify potential issues based on issue description and components.

        This is a simplified version - in a real implementation, this would use
        more sophisticated pattern matching and historical data correlation.
        """
        potential_issues = []

        # Simple keyword-based issue identification
        issue_lower = issue_description.lower()

        if "adhesion" in issue_lower or "sticking" in issue_lower:
            potential_issues.append("Adhesion failure - check resin compatibility and surface treatment")

        if "development" in issue_lower or "develop" in issue_lower:
            potential_issues.append("Development issues - check photosensitizer concentration and amine quencher balance")

        if "resolution" in issue_lower or "pattern" in issue_lower:
            potential_issues.append("Resolution problems - check molecular weight distribution and polymer composition")

        if "defect" in issue_lower or "contamination" in issue_lower:
            potential_issues.append("Defect formation - check additive purity and solvent quality")

        if "roughness" in issue_lower or "surface" in issue_lower:
            potential_issues.append("Surface roughness - check surfactant concentration and film formation")

        return potential_issues


if __name__ == "__main__":
    """
    Demo usage of PhotoresistROCAgent.

    This demonstrates the agent's ability to perform comprehensive photoresist analysis
    using structured data resources.
    """
    print("=" * 80)
    print("PhotoresistROCAgent Demo")
    print("=" * 80)
    print()

    # Initialize the agent
    print("🤖 Initializing PhotoresistROCAgent with structured data resources...")
    agent = PhotoresistROCAgent(model="gpt-4.1-mini")

    # Disable notifications for cleaner output in demo
    agent.enable_notifications(verbose=False)

    print("\n🔬 Available analysis capabilities:")
    print("   • Comprehensive sample analysis (4-level hierarchical decomposition)")
    print("   • Root cause analysis of performance issues")
    print("   • Component compatibility assessment")
    print("   • Historical pattern matching")
    print("   • Evidence-based problem diagnosis")
    print()

    # Interactive conversation
    agent.converse(input("Agent: Hello! I'm your Photoresist ROCA specialist. What sample would you like me to analyze?\n\nYou: "))
