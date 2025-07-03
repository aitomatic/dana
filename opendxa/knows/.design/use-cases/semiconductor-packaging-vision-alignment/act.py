"""
Act Phase: Task Execution and Action

Input: Composed knowledge + current task
Output: Execution results + performance metrics
"""

import random
from datetime import datetime
from typing import Any


class ActPhase:
    """Implements the Act phase of the CORRAL lifecycle."""

    def __init__(self):
        self.last_execution = {}
        self.execution_strategy = "structured_execution"

    def execute_task(self, composed_knowledge: dict[str, Any], current_task: str) -> dict[str, Any]:
        """Execute the task using composed knowledge."""

        print("⚡ Executing task with composed knowledge...")

        # Extract action recommendations
        action_recommendations = composed_knowledge.get("action_recommendations", [])
        confidence_assessment = composed_knowledge.get("confidence_assessment", {})

        print(f"📋 Executing {len(action_recommendations)} action recommendations")

        # Execute each action recommendation
        execution_results = []
        for i, recommendation in enumerate(action_recommendations, 1):
            result = self._execute_action(recommendation, i, len(action_recommendations))
            execution_results.append(result)
            print(f"  {i}. {recommendation['action']} - {result['status']}")

        # Simulate overall task execution
        overall_result = self._simulate_overall_execution(composed_knowledge, execution_results)

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(execution_results, overall_result)

        # Create execution summary
        execution_summary = {
            "task": current_task,
            "execution_time": datetime.now(),
            "overall_success": overall_result["success"],
            "action_results": execution_results,
            "performance_metrics": performance_metrics,
            "lessons_learned": self._extract_lessons_learned(execution_results),
            "next_steps": self._determine_next_steps(overall_result, execution_results),
        }

        self.last_execution = execution_summary
        print(f"✅ Task execution completed - Success: {overall_result['success']}")

        return execution_summary

    def _execute_action(self, recommendation: dict[str, str], action_num: int, total_actions: int) -> dict[str, Any]:
        """Execute a single action recommendation."""

        action = recommendation["action"]
        priority = recommendation["priority"]

        # Simulate action execution with realistic outcomes
        if "Configure vision system" in action:
            return self._simulate_vision_configuration(action, priority)
        elif "Follow non-standard pattern calibration" in action:
            return self._simulate_calibration_workflow(action, priority)
        elif "Implement ±0.1mm accuracy validation" in action:
            return self._simulate_accuracy_validation(action, priority)
        elif "Apply parameter optimization" in action:
            return self._simulate_parameter_optimization(action, priority)
        else:
            return self._simulate_generic_action(action, priority)

    def _simulate_vision_configuration(self, action: str, priority: str) -> dict[str, Any]:
        """Simulate vision system configuration."""

        # Simulate configuration process
        setup_time = random.uniform(2.0, 4.0)  # hours
        success_probability = 0.85 if priority == "high" else 0.75

        success = random.random() < success_probability

        if success:
            return {
                "action": action,
                "status": "completed",
                "setup_time": setup_time,
                "accuracy": "±0.08mm",  # Better than required
                "notes": "Vision system configured for High-Tg FR4 with 650nm lighting",
                "challenges": [],
                "optimizations_applied": ["Optimal lighting wavelength", "Contrast threshold adjustment"],
            }
        else:
            return {
                "action": action,
                "status": "failed",
                "setup_time": setup_time,
                "accuracy": "±0.15mm",  # Below requirement
                "notes": "Configuration failed due to substrate reflectivity variations",
                "challenges": ["Substrate material variations", "Lighting configuration complexity"],
                "optimizations_applied": [],
            }

    def _simulate_calibration_workflow(self, action: str, priority: str) -> dict[str, Any]:
        """Simulate calibration workflow execution."""

        # Simulate calibration process
        setup_time = random.uniform(3.0, 6.0)  # hours
        success_probability = 0.80 if priority == "high" else 0.70

        success = random.random() < success_probability

        if success:
            return {
                "action": action,
                "status": "completed",
                "setup_time": setup_time,
                "accuracy": "±0.09mm",  # Meets requirement
                "notes": "Non-standard pattern calibration completed successfully",
                "challenges": ["Pattern recognition complexity"],
                "optimizations_applied": ["Custom fiducial detection algorithm"],
            }
        else:
            return {
                "action": action,
                "status": "failed",
                "setup_time": setup_time,
                "accuracy": "±0.12mm",  # Below requirement
                "notes": "Calibration failed due to pattern recognition issues",
                "challenges": ["Non-standard pattern complexity", "Fiducial detection failures"],
                "optimizations_applied": [],
            }

    def _simulate_accuracy_validation(self, action: str, priority: str) -> dict[str, Any]:
        """Simulate accuracy validation process."""

        # Simulate validation process
        setup_time = random.uniform(1.0, 2.0)  # hours
        success_probability = 0.90 if priority == "critical" else 0.80

        success = random.random() < success_probability

        if success:
            return {
                "action": action,
                "status": "completed",
                "setup_time": setup_time,
                "accuracy": "±0.095mm",  # Validated requirement
                "notes": "Accuracy validation passed with statistical process control",
                "challenges": [],
                "optimizations_applied": ["Statistical validation methods"],
            }
        else:
            return {
                "action": action,
                "status": "failed",
                "setup_time": setup_time,
                "accuracy": "±0.11mm",  # Failed validation
                "notes": "Accuracy validation failed - exceeds ±0.1mm requirement",
                "challenges": ["Accuracy requirement too stringent", "Measurement system limitations"],
                "optimizations_applied": [],
            }

    def _simulate_parameter_optimization(self, action: str, priority: str) -> dict[str, Any]:
        """Simulate parameter optimization process."""

        # Simulate optimization process
        setup_time = random.uniform(1.5, 3.0)  # hours
        success_probability = 0.75 if priority == "medium" else 0.65

        success = random.random() < success_probability

        if success:
            return {
                "action": action,
                "status": "completed",
                "setup_time": setup_time,
                "accuracy": "±0.07mm",  # Improved accuracy
                "notes": "Parameter optimization improved accuracy by 30%",
                "challenges": ["Optimization complexity"],
                "optimizations_applied": ["Genetic algorithm optimization", "Response surface methodology"],
            }
        else:
            return {
                "action": action,
                "status": "failed",
                "setup_time": setup_time,
                "accuracy": "±0.13mm",  # No improvement
                "notes": "Parameter optimization did not achieve desired results",
                "challenges": ["Optimization algorithm limitations", "Parameter space complexity"],
                "optimizations_applied": [],
            }

    def _simulate_generic_action(self, action: str, priority: str) -> dict[str, Any]:
        """Simulate generic action execution."""

        setup_time = random.uniform(1.0, 3.0)
        success = random.random() < 0.8

        return {
            "action": action,
            "status": "completed" if success else "failed",
            "setup_time": setup_time,
            "accuracy": "±0.10mm" if success else "±0.15mm",
            "notes": f"Generic action {action} executed",
            "challenges": [] if success else ["Generic execution challenges"],
            "optimizations_applied": [],
        }

    def _simulate_overall_execution(self, composed_knowledge: dict[str, Any], action_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Simulate overall task execution outcome."""

        # Handle empty action_results case
        if not action_results:
            return {
                "success": False,
                "accuracy": "±0.00mm",
                "setup_time": 0.0,
                "success_rate": 0.0,
                "critical_actions_completed": 0,
            }

        # Determine overall success based on action results
        successful_actions = [r for r in action_results if r["status"] == "completed"]
        success_rate = len(successful_actions) / len(action_results)

        # Overall success if >70% of actions succeed
        overall_success = success_rate >= 0.7

        # Calculate overall accuracy
        accuracies = [float(r["accuracy"].replace("±", "").replace("mm", "")) for r in action_results]
        overall_accuracy = f"±{sum(accuracies) / len(accuracies):.3f}mm"

        # Calculate total setup time
        total_setup_time = sum(r["setup_time"] for r in action_results)

        return {
            "success": overall_success,
            "accuracy": overall_accuracy,
            "setup_time": total_setup_time,
            "success_rate": success_rate,
            "critical_actions_completed": len(
                [r for r in action_results if r.get("priority") == "critical" and r["status"] == "completed"]
            ),
        }

    def _calculate_performance_metrics(self, action_results: list[dict[str, Any]], overall_result: dict[str, Any]) -> dict[str, Any]:
        """Calculate performance metrics from execution results."""

        # Handle empty action_results case
        if not action_results:
            return {
                "overall_success_rate": 0.0,
                "average_accuracy": "±0.00mm",
                "total_setup_time": 0.0,
                "actions_completed": 0,
                "actions_failed": 0,
                "average_action_time": 0.0,
                "optimization_effectiveness": 0.0,
            }

        metrics = {
            "overall_success_rate": overall_result["success_rate"],
            "average_accuracy": overall_result["accuracy"],
            "total_setup_time": overall_result["setup_time"],
            "actions_completed": len([r for r in action_results if r["status"] == "completed"]),
            "actions_failed": len([r for r in action_results if r["status"] == "failed"]),
            "average_action_time": sum(r["setup_time"] for r in action_results) / len(action_results),
            "optimization_effectiveness": len([r for r in action_results if r["optimizations_applied"]]) / len(action_results),
        }

        return metrics

    def _extract_lessons_learned(self, action_results: list[dict[str, Any]]) -> list[str]:
        """Extract lessons learned from execution results."""

        lessons = []

        # Analyze successful actions
        successful_actions = [r for r in action_results if r["status"] == "completed"]
        if successful_actions:
            lessons.append(f"{len(successful_actions)} actions completed successfully")

            # Extract successful optimizations
            all_optimizations = []
            for action in successful_actions:
                all_optimizations.extend(action.get("optimizations_applied", []))

            if all_optimizations:
                lessons.append(f"Successful optimizations: {', '.join(set(all_optimizations))}")

        # Analyze failed actions
        failed_actions = [r for r in action_results if r["status"] == "failed"]
        if failed_actions:
            lessons.append(f"{len(failed_actions)} actions failed and need improvement")

            # Extract challenges
            all_challenges = []
            for action in failed_actions:
                all_challenges.extend(action.get("challenges", []))

            if all_challenges:
                lessons.append(f"Key challenges: {', '.join(set(all_challenges))}")

        return lessons

    def _determine_next_steps(self, overall_result: dict[str, Any], action_results: list[dict[str, Any]]) -> list[str]:
        """Determine next steps based on execution results."""

        next_steps = []

        if overall_result["success"]:
            next_steps.append("Proceed with production setup")
            next_steps.append("Document successful configuration for future reference")
            next_steps.append("Schedule regular accuracy validation")
        else:
            next_steps.append("Review and revise calibration approach")
            next_steps.append("Consult with senior engineers for optimization")
            next_steps.append("Consider alternative vision system configurations")

        # Add specific next steps based on failed actions
        failed_actions = [r for r in action_results if r["status"] == "failed"]
        for action in failed_actions:
            next_steps.append(f"Retry {action['action']} with modified approach")

        return next_steps
