#!/usr/bin/env python3
"""
Examples of the improved YAML structure for different problem types.

This demonstrates how the LLM should respond with comprehensive,
well-formed YAML that includes confidence, reasoning, and detailed metadata.
"""

import yaml


def show_yaml_examples():
    """Show examples of the improved YAML structure for different approaches."""

    print("📋 Improved YAML Structure Examples")
    print("=" * 60)

    examples = {
        "DIRECT_SOLUTION": {
            "description": "Simple arithmetic or factual questions",
            "problem": "What is 15 * 23?",
            "yaml": {
                "approach": "DIRECT_SOLUTION",
                "confidence": 0.98,
                "reasoning": "This is a simple arithmetic calculation that can be solved directly without additional tools or code generation.",
                "solution": "345",
                "details": {
                    "complexity": "SIMPLE",
                    "estimated_duration": "immediate",
                    "required_resources": ["basic_calculation"],
                    "risks": "None - straightforward arithmetic",
                },
            },
        },
        "TYPE_CODE": {
            "description": "Problems requiring code generation or data processing",
            "problem": "Calculate the factorial of 10",
            "yaml": {
                "approach": "TYPE_CODE",
                "confidence": 0.95,
                "reasoning": "This requires mathematical computation that is best handled with Python code using the math module.",
                "solution": "import math\nresult = math.factorial(10)\nprint(f'Factorial of 10 is: {result}')\nreturn result",
                "details": {
                    "complexity": "MODERATE",
                    "estimated_duration": "immediate",
                    "required_resources": ["python_math_module", "code_execution_environment"],
                    "risks": "Potential integer overflow for very large numbers",
                },
            },
        },
        "TYPE_WORKFLOW": {
            "description": "Complex processes requiring multiple steps",
            "problem": "Check the health status of equipment sensors",
            "yaml": {
                "approach": "TYPE_WORKFLOW",
                "confidence": 0.87,
                "reasoning": "This requires multiple steps: data collection, analysis, comparison with thresholds, and reporting.",
                "solution": "1. Collect sensor readings from all equipment\n2. Compare readings against normal ranges\n3. Identify sensors outside acceptable limits\n4. Generate health report with recommendations\n5. Alert maintenance team if critical issues found",
                "details": {
                    "complexity": "COMPLEX",
                    "estimated_duration": "minutes",
                    "required_resources": ["sensor_data_access", "threshold_database", "reporting_system"],
                    "risks": "Data access issues, sensor failures, false positives",
                },
            },
        },
        "TYPE_DELEGATE": {
            "description": "Problems needing specialized agents",
            "problem": "Analyze complex financial data patterns for investment decisions",
            "yaml": {
                "approach": "TYPE_DELEGATE",
                "confidence": 0.92,
                "reasoning": "This requires specialized financial analysis expertise and access to financial data sources that a dedicated financial analyst agent would have.",
                "solution": "agent:financial_analyst",
                "details": {
                    "complexity": "COMPLEX",
                    "estimated_duration": "hours",
                    "required_resources": ["financial_data_sources", "analysis_tools", "market_knowledge"],
                    "risks": "Market volatility, data quality issues, regulatory compliance",
                },
            },
        },
        "TYPE_ESCALATE": {
            "description": "Problems too complex for current capabilities",
            "problem": "Coordinate emergency response across multiple departments during a critical system failure",
            "yaml": {
                "approach": "TYPE_ESCALATE",
                "confidence": 0.89,
                "reasoning": "This requires real-time coordination across multiple departments, emergency protocols, and human decision-making that cannot be automated safely.",
                "solution": "This requires immediate human intervention due to the critical nature of the system failure and the need for cross-departmental coordination that involves safety protocols and emergency procedures.",
                "details": {
                    "complexity": "CRITICAL",
                    "estimated_duration": "hours",
                    "required_resources": ["emergency_protocols", "department_coordinators", "safety_systems"],
                    "risks": "System downtime, safety hazards, regulatory violations",
                },
            },
        },
    }

    for approach, example in examples.items():
        print(f"\n🔹 {approach}: {example['description']}")
        print(f"   Problem: {example['problem']}")
        print("   YAML Response:")
        print("   " + "─" * 50)

        # Pretty print the YAML
        yaml_str = yaml.dump(example["yaml"], default_flow_style=False, indent=2)
        for line in yaml_str.split("\n"):
            if line.strip():
                print(f"   {line}")

        print()

    print("=" * 60)
    print("✅ Key Improvements in YAML Structure:")
    print("1. 📊 Confidence score (0.0-1.0) for decision quality")
    print("2. 🧠 Detailed reasoning for approach selection")
    print("3. 📋 Comprehensive metadata in 'details' section")
    print("4. ⏱️  Estimated duration for planning")
    print("5. 🛠️  Required resources for execution")
    print("6. ⚠️  Risk assessment for mitigation")
    print("7. 🎯 Actual solution/code provided directly")


if __name__ == "__main__":
    show_yaml_examples()
