#!/usr/bin/env python3
"""
Demonstration of the Agent-Workflow FSM Framework

This script demonstrates how to use the new workflow framework
to solve problems with a simple, clean interface.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the core agent system
from dana.builtin_types.agent_system import AgentInstance, AgentType
from dana.core.lang.sandbox_context import SandboxContext


def demo_equipment_status_check():
    """Demonstrate equipment status check problem."""
    print("🔧 Equipment Status Check Demo")
    print("=" * 40)

    # Create agent using existing Dana AgentType
    agent_type = AgentType("EquipmentAgent", fields={}, field_order=[])
    agent = AgentInstance(agent_type, {})

    # Create sandbox context
    _ = SandboxContext()

    # Problem statement
    problem = "What is the current status of Line 3?"
    print(f"Problem: {problem}")

    # Solve the problem with simple interface
    result = agent.solve(problem)

    print(f"Result: {result}")

    # Handle result based on type
    if isinstance(result, dict):
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Temperature: {result.get('temperature', 'unknown')}")
        print(f"Last Check: {result.get('last_check', 'unknown')}")
    else:
        print(f"Result Type: {type(result)}")
        print(f"Result Content: {result}")
    print()


def demo_workflow_planning():
    """Demonstrate workflow planning capability."""
    print("📋 Workflow Planning Demo")
    print("=" * 40)

    agent_type = AgentType("EquipmentAgent", fields={}, field_order=[])
    agent = AgentInstance(agent_type, {})

    # Plan workflow for a problem
    problem = "What is the current status of Line 3?"
    workflow = agent.plan(problem)

    print(f"Problem: {problem}")
    print(f"Planned Workflow: {workflow.name}")
    print(f"Workflow Status: {workflow.get_status()}")
    print()


def demo_reasoning():
    """Demonstrate reasoning capability."""
    print("🧠 Reasoning Demo")
    print("=" * 40)

    agent_type = AgentType("EquipmentAgent", fields={}, field_order=[])
    agent = AgentInstance(agent_type, {})

    # Create sandbox context
    _ = SandboxContext()

    # Reason about equipment status
    question = "Is the equipment operating normally?"
    context = {"equipment_id": "Line 3", "temperature": 45.2}

    result = agent.reason(question, context)

    print(f"Question: {question}")
    print(f"Context: {context}")

    # Handle result based on type
    if isinstance(result, dict):
        print(f"Analysis: {result.get('analysis', 'No analysis available')}")
        print(f"Confidence: {result.get('confidence', 0.0)}")
    else:
        print(f"Result: {result}")
    print()


def demo_chat():
    """Demonstrate chat capability."""
    print("💬 Chat Demo")
    print("=" * 40)

    agent_type = AgentType("EquipmentAgent", fields={}, field_order=[])
    agent = AgentInstance(agent_type, {})

    # Chat with the agent
    message = "Check equipment health for Line 3"
    response = agent.chat(message)

    print(f"Message: {message}")
    print(f"Response: {response}")
    print()


def demo_data_analysis():
    """Demonstrate data analysis problem."""
    print("📊 Data Analysis Demo")
    print("=" * 40)

    agent_type = AgentType("DataAnalystAgent", fields={}, field_order=[])
    agent = AgentInstance(agent_type, {})

    # Problem statement
    problem = "Analyze the temperature data from sensors.csv"
    print(f"Problem: {problem}")

    # Solve the problem
    result = agent.solve(problem)

    print(f"Result: {result}")

    # Handle result based on type
    if isinstance(result, dict):
        print(f"Mean Temperature: {result.get('mean_temp', 'unknown')}")
        print(f"Max Temperature: {result.get('max_temp', 'unknown')}")
        print(f"Anomalies: {result.get('anomalies', 'unknown')}")
    else:
        print(f"Result Type: {type(result)}")
    print()


def demo_health_check():
    """Demonstrate health check problem."""
    print("🏥 Health Check Demo")
    print("=" * 40)

    agent_type = AgentType("HealthCheckAgent", fields={}, field_order=[])
    agent = AgentInstance(agent_type, {})

    # Problem statement
    problem = "Check equipment health for Line 3"
    print(f"Problem: {problem}")

    # Solve the problem
    result = agent.solve(problem)

    print(f"Result: {result}")

    # Handle result based on type
    if isinstance(result, dict):
        print(f"Health: {result.get('health', 'unknown')}")
        print(f"Issues: {result.get('issues', [])}")
        print(f"Recommendations: {result.get('recommendations', [])}")
    else:
        print(f"Result Type: {type(result)}")
    print()


def demo_pipeline_workflow():
    """Demonstrate pipeline workflow problem."""
    print("🔄 Pipeline Workflow Demo")
    print("=" * 40)

    agent_type = AgentType("PipelineAgent", fields={}, field_order=[])
    agent = AgentInstance(agent_type, {})

    # Plan the workflow
    problem = "Load data, analyze it, and save results"
    workflow = agent.plan(problem)

    print(f"Problem: {problem}")
    print(f"Planned Workflow: {workflow.name}")

    # Execute the workflow
    result = workflow.execute()

    print(f"Execution Result: {result}")

    # Handle result based on type
    if isinstance(result, dict):
        print(f"Processed: {result.get('processed', False)}")
        print(f"Anomalies Found: {result.get('anomalies_found', 0)}")
        print(f"Output File: {result.get('output_file', 'unknown')}")
    else:
        print(f"Result Type: {type(result)}")
    print()


def main():
    """Run all demonstrations."""
    print("🚀 Agent-Workflow FSM Framework Demo")
    print("=" * 50)
    print("This demo shows how the new workflow framework provides")
    print("a simple interface for solving complex problems.")
    print()

    try:
        # Run all demos
        demo_equipment_status_check()
        demo_workflow_planning()
        demo_reasoning()
        demo_chat()
        demo_data_analysis()
        demo_health_check()
        demo_pipeline_workflow()

        print("🎉 All demonstrations completed successfully!")
        print()
        print("Key Features Demonstrated:")
        print("✅ Simple interface (plan, solve, reason, chat)")
        print("✅ Automatic workflow discovery and creation")
        print("✅ Automatic resource selection")
        print("✅ Clean execution with rich results")
        print("✅ Integration with Dana's type system")
        print()
        print("The framework provides a powerful yet simple way to")
        print("solve problems using workflow and resource spaces.")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
