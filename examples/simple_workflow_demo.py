#!/usr/bin/env python3
"""
Simple Standalone Workflow Framework Demo

This demonstrates the Agent-Workflow FSM system without requiring
the full Dana environment or any external dependencies.
"""

import time
from typing import Any, Union


# Simple mock types for demonstration
class AgentType:
    def __init__(self, name):
        self.name = name
        self.memory_system = None
        self.reasoning_capabilities = []


class WorkflowType:
    def __init__(self, name, fields=None, field_order=None, field_defaults=None, docstring=None):
        self.name = name
        self.fields = fields or {}
        self.field_order = field_order or []
        self.field_defaults = field_defaults or {}
        self.docstring = docstring or ""


class ResourceType:
    def __init__(self, name, fields=None, field_order=None, field_defaults=None, docstring=None):
        self.name = name
        self.fields = fields or {}
        self.field_order = field_order or []
        self.field_defaults = field_defaults or {}
        self.docstring = docstring or ""
        self.has_lifecycle = True

    def has_method(self, method_name):
        return True


# Try to import IWorkflow from interface_system, fallback to mock for demonstration
try:
    from dana.builtin_types.interface_system import IWorkflow
except ImportError:
    # Mock interface types for demonstration
    class InterfaceType:
        def __init__(self, name, methods, embedded_interfaces=None, docstring=None):
            self.name = name
            self.methods = methods
            self.embedded_interfaces = embedded_interfaces or []
            self.docstring = docstring

    class InterfaceMethodSpec:
        def __init__(self, name, parameters, return_type=None, comment=None):
            self.name = name
            self.parameters = parameters
            self.return_type = return_type
            self.comment = comment

    class InterfaceParameterSpec:
        def __init__(self, name, type_name=None, has_default=False):
            self.name = name
            self.type_name = type_name
            self.has_default = has_default

    # Mock IWorkflow interface for demonstration
    IWorkflow = InterfaceType(
        name="IWorkflow",
        methods={
            "name": InterfaceMethodSpec(name="name", parameters=[], return_type="str", comment="Get the name of the workflow"),
            "execute": InterfaceMethodSpec(
                name="execute",
                parameters=[InterfaceParameterSpec(name="data", type_name="dict")],
                return_type="dict",
                comment="Execute the workflow with given data",
            ),
            "validate": InterfaceMethodSpec(
                name="validate",
                parameters=[InterfaceParameterSpec(name="data", type_name="dict")],
                return_type="bool",
                comment="Validate input data for the workflow",
            ),
            "get_status": InterfaceMethodSpec(name="get_status", parameters=[], return_type="str", comment="Get current execution status"),
        },
        docstring="Interface for workflow objects that can be used by agents",
    )


# Simplified workflow framework implementation
class WorkflowSpace:
    def __init__(self):
        self._workflows = {}

    def find_or_create_workflow(self, problem: str) -> WorkflowType:
        problem_lower = problem.lower()

        if any(keyword in problem_lower for keyword in ["health", "check", "maintenance"]):
            return self._get_or_create_health_check_workflow()
        elif any(keyword in problem_lower for keyword in ["analyze", "data", "sensor", "csv"]):
            return self._get_or_create_data_analysis_workflow()
        elif any(keyword in problem_lower for keyword in ["status", "equipment", "line", "temperature"]):
            return self._get_or_create_equipment_status_workflow()
        else:
            return self._create_generic_workflow(problem)

    def get_workflow(self, name: str) -> WorkflowType | None:
        """Get workflow by name."""
        return self._workflows.get(name)

    def _get_or_create_equipment_status_workflow(self) -> WorkflowType:
        name = "EquipmentStatusWorkflow"
        if name in self._workflows:
            return self._workflows[name]

        workflow = WorkflowType(
            name=name,
            fields={"equipment_id": "str", "status": "str", "temperature": "float", "last_check": "str"},
            field_order=["equipment_id", "status", "temperature", "last_check"],
            field_defaults={"equipment_id": "", "status": "unknown", "temperature": 0.0, "last_check": ""},
            docstring="Workflow for checking equipment status",
        )
        self._workflows[name] = workflow
        return workflow

    def _get_or_create_data_analysis_workflow(self) -> WorkflowType:
        name = "DataAnalysisWorkflow"
        if name in self._workflows:
            return self._workflows[name]

        workflow = WorkflowType(
            name=name,
            fields={"data_source": "str", "mean_temp": "float", "max_temp": "float", "anomalies": "int"},
            field_order=["data_source", "mean_temp", "max_temp", "anomalies"],
            field_defaults={"data_source": "", "mean_temp": 0.0, "max_temp": 0.0, "anomalies": 0},
            docstring="Workflow for analyzing sensor data",
        )
        self._workflows[name] = workflow
        return workflow

    def _get_or_create_health_check_workflow(self) -> WorkflowType:
        name = "HealthCheckWorkflow"
        if name in self._workflows:
            return self._workflows[name]

        workflow = WorkflowType(
            name=name,
            fields={"equipment_id": "str", "health": "str", "issues": "list", "recommendations": "list"},
            field_order=["equipment_id", "health", "issues", "recommendations"],
            field_defaults={"equipment_id": "", "health": "unknown", "issues": [], "recommendations": []},
            docstring="Workflow for checking equipment health",
        )
        self._workflows[name] = workflow
        return workflow

    def _create_generic_workflow(self, problem: str) -> WorkflowType:
        words = problem.split()[:3]
        name = "".join(word.capitalize() for word in words) + "Workflow"

        workflow = WorkflowType(
            name=name,
            fields={"problem": "str", "status": "str", "result": "dict"},
            field_order=["problem", "status", "result"],
            field_defaults={"problem": problem, "status": "created", "result": {}},
            docstring=f"Workflow for: {problem}",
        )
        self._workflows[name] = workflow
        return workflow


class ResourceSpace:
    def __init__(self):
        self._resources = {}
        self._create_default_resources()

    def select_best_resources(self, problem: str) -> list:
        problem_lower = problem.lower()
        selected = []

        for _, resource_type in self._resources.items():
            if self._is_resource_suitable(resource_type, problem_lower):
                selected.append(self._create_resource_instance(resource_type))

        return selected

    def _create_default_resources(self):
        equipment = ResourceType("EquipmentResource", docstring="Equipment status information")
        sensor = ResourceType("SensorResource", docstring="Sensor data information")
        file = ResourceType("FileResource", docstring="File system operations")
        database = ResourceType("DatabaseResource", docstring="Database operations")

        self._resources["EquipmentResource"] = equipment
        self._resources["SensorResource"] = sensor
        self._resources["FileResource"] = file
        self._resources["DatabaseResource"] = database

    def _is_resource_suitable(self, resource_type: ResourceType, problem: str) -> bool:
        if "equipment" in problem or "line" in problem or "status" in problem:
            return resource_type.name == "EquipmentResource"
        if "sensor" in problem or "data" in problem or "temperature" in problem:
            return resource_type.name in ["SensorResource", "FileResource", "DatabaseResource"]
        if "csv" in problem or "file" in problem:
            return resource_type.name == "FileResource"
        if "database" in problem or "db" in problem:
            return resource_type.name == "DatabaseResource"
        return True

    def _create_resource_instance(self, resource_type: ResourceType) -> Any:
        class ResourceInstance:
            def __init__(self, resource_type):
                self.resource_type = resource_type
                self.name = resource_type.name

        return ResourceInstance(resource_type)


class WorkflowInstance:
    def __init__(self, workflow_type: WorkflowType, values: dict):
        self.workflow_type = workflow_type
        self._execution_state = "created"

    def execute(self, data: dict) -> dict:
        self._execution_state = "executing"

        problem = data.get("problem", "")
        params = data.get("params", {})

        if self.workflow_type.name == "EquipmentStatusWorkflow":
            result = self._execute_equipment_status(problem, params)
        elif self.workflow_type.name == "DataAnalysisWorkflow":
            result = self._execute_data_analysis(problem, params)
        elif self.workflow_type.name == "HealthCheckWorkflow":
            result = self._execute_health_check(problem, params)
        else:
            result = self._execute_generic(problem, params)

        self._execution_state = "completed"
        return result

    def _execute_equipment_status(self, problem: str, params: dict) -> dict:
        equipment_id = params.get("equipment_id", "Line 3")
        current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "status": "operational",
            "temperature": 45.2,
            "last_check": current_time,
            "equipment_id": equipment_id,
            "workflow_type": "EquipmentStatusWorkflow",
        }

    def _execute_data_analysis(self, problem: str, params: dict) -> dict:
        data_source = params.get("data_source", "sensors.csv")

        return {"mean_temp": 42.1, "max_temp": 67.8, "anomalies": 3, "data_source": data_source, "workflow_type": "DataAnalysisWorkflow"}

    def _execute_health_check(self, problem: str, params: dict) -> dict:
        equipment_id = params.get("equipment_id", "Line 3")

        return {
            "health": "good",
            "issues": [],
            "recommendations": ["schedule maintenance in 2 weeks"],
            "equipment_id": equipment_id,
            "workflow_type": "HealthCheckWorkflow",
        }

    def _execute_generic(self, problem: str, params: dict) -> dict:
        return {"status": "completed", "problem": problem, "params": params, "workflow_type": self.workflow_type.name}

    def get_status(self) -> str:
        return self._execution_state


class Agent:
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self._workflow_space = WorkflowSpace()
        self._resource_space = ResourceSpace()
        self._execution_state = "ready"

    def plan(self, problem: str) -> WorkflowInstance:
        workflow_type = self._workflow_space.find_or_create_workflow(problem)
        return WorkflowInstance(workflow_type, {})

    def _plan_specific_workflow(self, workflow_name: str) -> WorkflowInstance:
        workflow_type = self._workflow_space.get_workflow(workflow_name)
        if not workflow_type:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        return WorkflowInstance(workflow_type, {})

    def solve(self, problem: str, use_workflow: Union[IWorkflow, None] = None, **params) -> dict:
        try:
            # Use provided workflow or plan one
            if use_workflow:
                workflow = use_workflow
            else:
                workflow = self.plan(problem)

            resources = self._resource_space.select_best_resources(problem)

            execution_data = {"params": params, "resources": resources, "problem": problem, "agent_type": self.agent_type.name}

            result = workflow.execute(execution_data)
            self._execution_state = "completed"
            return result

        except Exception as e:
            self._execution_state = "error"
            return {"error": str(e), "status": "failed", "problem": problem}

    def reason(self, question: str, context: dict) -> dict:
        return {
            "question": question,
            "context": context,
            "analysis": f"Analysis of '{question}' with context: {context}",
            "insights": ["Basic reasoning applied"],
            "confidence": 0.8,
        }

    def chat(self, message: str) -> str:
        return f"Agent response to: {message}"

    def get_status(self) -> str:
        return self._execution_state


def demo_equipment_status():
    """Demonstrate equipment status check."""
    print("🔧 Equipment Status Check")
    print("=" * 30)

    agent_type = AgentType("EquipmentAgent")
    agent = Agent(agent_type=agent_type)

    problem = "What is the current status of Line 3?"
    print(f"Problem: {problem}")

    start_time = time.time()
    result = agent.solve(problem)
    end_time = time.time()

    print(f"Result: {result}")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Temperature: {result.get('temperature', 'unknown')}")
    print(f"Execution time: {end_time - start_time:.3f}s")
    print()


def demo_data_analysis():
    """Demonstrate data analysis."""
    print("📊 Data Analysis")
    print("=" * 30)

    agent_type = AgentType("DataAnalystAgent")
    agent = Agent(agent_type=agent_type)

    problem = "Analyze the temperature data from sensors.csv"
    print(f"Problem: {problem}")

    result = agent.solve(problem)

    print(f"Result: {result}")
    print(f"Mean Temperature: {result.get('mean_temp', 'unknown')}")
    print(f"Max Temperature: {result.get('max_temp', 'unknown')}")
    print(f"Anomalies: {result.get('anomalies', 'unknown')}")
    print()


def demo_health_check():
    """Demonstrate health check."""
    print("🏥 Health Check")
    print("=" * 30)

    agent_type = AgentType("HealthCheckAgent")
    agent = Agent(agent_type=agent_type)

    problem = "Check equipment health for Line 3"
    print(f"Problem: {problem}")

    result = agent.solve(problem)

    print(f"Result: {result}")
    print(f"Health: {result.get('health', 'unknown')}")
    print(f"Issues: {result.get('issues', [])}")
    print(f"Recommendations: {result.get('recommendations', [])}")
    print()


def demo_workflow_planning():
    """Demonstrate workflow planning."""
    print("📋 Workflow Planning")
    print("=" * 30)

    agent_type = AgentType("EquipmentAgent")
    agent = Agent(agent_type=agent_type)

    problem = "What is the current status of Line 3?"
    workflow = agent.plan(problem)

    print(f"Problem: {problem}")
    print(f"Planned Workflow: {workflow.workflow_type.name}")
    print(f"Workflow Status: {workflow.get_status()}")
    print()


def demo_reasoning():
    """Demonstrate reasoning capability."""
    print("🧠 Reasoning")
    print("=" * 30)

    agent_type = AgentType("EquipmentAgent")
    agent = Agent(agent_type=agent_type)

    question = "Is the equipment operating normally?"
    context = {"equipment_id": "Line 3", "temperature": 45.2}

    result = agent.reason(question, context)

    print(f"Question: {question}")
    print(f"Context: {context}")
    print(f"Analysis: {result.get('analysis', 'No analysis available')}")
    print(f"Confidence: {result.get('confidence', 0.0)}")
    print()


def demo_chat():
    """Demonstrate chat capability."""
    print("💬 Chat")
    print("=" * 30)

    agent_type = AgentType("EquipmentAgent")
    agent = Agent(agent_type=agent_type)

    message = "Check equipment health for Line 3"
    response = agent.chat(message)

    print(f"Message: {message}")
    print(f"Response: {response}")
    print()


def demo_specific_workflow():
    """Demonstrate using a specific workflow."""
    print("🎯 Specific Workflow Usage")
    print("=" * 30)

    agent_type = AgentType("EquipmentAgent")
    agent = Agent(agent_type=agent_type)

    # Ensure workflows are created first
    agent.solve("What is the current status of Line 3?")  # Creates EquipmentStatusWorkflow
    agent.solve("Check equipment health for Line 3")  # Creates HealthCheckWorkflow

    # Get workflow instances
    equipment_workflow = agent.plan("What is the current status of Line 3?")
    health_workflow = agent.plan("Check equipment health for Line 3")

    # Use automatic discovery
    print("1. Automatic workflow discovery:")
    result1 = agent.solve("What is the current status of Line 3?")
    print(f"   Result: {result1.get('workflow_type', 'unknown')}")

    # Use specific workflow
    print("2. Specific workflow usage:")
    result2 = agent.solve("What is the current status of Line 3?", use_workflow=equipment_workflow)
    print(f"   Result: {result2.get('workflow_type', 'unknown')}")

    # Use different workflow for same problem
    print("3. Force different workflow:")
    result3 = agent.solve("What is the current status of Line 3?", use_workflow=health_workflow)
    print(f"   Result: {result3.get('workflow_type', 'unknown')}")
    print(f"   Health: {result3.get('health', 'unknown')}")

    print()


def main():
    """Run all demonstrations."""
    print("🚀 Simple Workflow Framework Demo")
    print("=" * 40)
    print("This demonstrates the Agent-Workflow FSM system")
    print("with a simple, standalone implementation.")
    print()

    try:
        demo_equipment_status()
        demo_data_analysis()
        demo_health_check()
        demo_workflow_planning()
        demo_reasoning()
        demo_chat()
        demo_specific_workflow()

        print("🎉 All demonstrations completed successfully!")
        print()
        print("Key Features Demonstrated:")
        print("✅ Simple interface (plan, solve, reason, chat)")
        print("✅ Automatic workflow discovery and creation")
        print("✅ Automatic resource selection")
        print("✅ Clean execution with rich results")
        print("✅ No external dependencies required")
        print("✅ Specific workflow selection via use_workflow parameter")
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
    exit(0 if success else 1)
