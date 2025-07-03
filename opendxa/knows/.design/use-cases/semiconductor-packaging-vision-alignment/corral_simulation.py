#!/usr/bin/env python3
"""
KNOWS CORRAL Simulation: Semiconductor Packaging Vision Alignment

This simulation demonstrates the complete CORRAL lifecycle for setting up
vision system calibration for a customer BGA package with non-standard fiducial patterns.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from act import ActPhase
from curate import CuratePhase
from learn import LearnPhase
from organize import OrganizePhase
from reason import ReasonPhase
from retrieve import RetrievePhase


class SemiconductorPackagingSimulation:
    """Simulates the complete CORRAL lifecycle for semiconductor packaging vision alignment."""

    def __init__(self):
        self.use_case = {
            "topic": "Vision System Calibration",
            "procedure": "Non-Standard Pattern Setup",
            "customer": "Advanced Semiconductor Packaging (ASP)",
            "requirements": {
                "package_type": "BGA (Ball Grid Array)",
                "specifications": "324 balls, 0.4mm pitch",
                "accuracy": "±0.1mm",
                "material": "High-Tg FR4",
                "volume": "10,000 units/month",
            },
        }

        # Initialize phases
        self.curate = CuratePhase()
        self.organize = OrganizePhase()
        self.retrieve = RetrievePhase()
        self.reason = ReasonPhase()
        self.act = ActPhase()
        self.learn = LearnPhase()

        # Knowledge base state
        self.knowledge_base = {}
        self.performance_metrics = {}

    def run_simulation(self):
        """Execute the complete CORRAL lifecycle simulation."""

        print("🔧 KNOWS CORRAL Simulation: Semiconductor Packaging Vision Alignment")
        print("=" * 80)

        # Phase 1: Curate
        print("\n📚 PHASE 1: CURATE")
        print("-" * 40)
        knowledge_requirements = self.curate.analyze_use_case(self.use_case)
        knowledge_content = self.curate.generate_knowledge_content(knowledge_requirements)
        storage_decisions = self.curate.determine_storage_structures(knowledge_requirements)

        # Phase 2: Organize
        print("\n🗂️  PHASE 2: ORGANIZE")
        print("-" * 40)
        knowledge_units = self.organize.create_knowledge_units(knowledge_content, storage_decisions)
        self.knowledge_base = self.organize.store_knowledge(knowledge_units)

        # Phase 3: Retrieve
        print("\n🔍 PHASE 3: RETRIEVE")
        print("-" * 40)
        current_task = "Calibrate vision system for customer BGA package with non-standard fiducial pattern"
        retrieved_knowledge = self.retrieve.select_knowledge(current_task, self.knowledge_base)

        # Phase 4: Reason
        print("\n🧠 PHASE 4: REASON")
        print("-" * 40)
        composed_knowledge = self.reason.compose_knowledge(retrieved_knowledge, current_task)

        # Phase 5: Act
        print("\n⚡ PHASE 5: ACT")
        print("-" * 40)
        execution_results = self.act.execute_task(composed_knowledge, current_task)

        # Phase 6: Learn
        print("\n📈 PHASE 6: LEARN")
        print("-" * 40)
        learning_outcomes = self.learn.analyze_outcomes(execution_results)
        self.learn.update_knowledge_base(self.knowledge_base, learning_outcomes)

        # Summary
        print("\n🎯 SIMULATION SUMMARY")
        print("=" * 80)
        self.print_summary()

    def print_summary(self):
        """Print simulation summary and key metrics."""

        print(f"Use Case: {self.use_case['topic']} - {self.use_case['procedure']}")
        print(f"Customer: {self.use_case['customer']}")
        print(f"Requirements: {self.use_case['requirements']['package_type']} with {self.use_case['requirements']['accuracy']} accuracy")

        print(f"\nKnowledge Base Size: {len(self.knowledge_base)} units")
        print(f"Retrieved Knowledge: {len(self.retrieve.last_retrieval)} units")
        print(f"Execution Success: {self.act.last_execution.get('overall_success', False)}")
        print(f"Setup Time: {self.act.last_execution.get('setup_time', 'N/A')} hours")
        print(f"Accuracy Achieved: {self.act.last_execution.get('accuracy', 'N/A')}")

        print(f"\nNew Knowledge Generated: {len(self.learn.last_learning.get('new_units', []))} units")
        print(f"Knowledge Promoted: {len(self.learn.last_learning.get('promoted_units', []))} units")


if __name__ == "__main__":
    simulation = SemiconductorPackagingSimulation()
    simulation.run_simulation()
