"""
Domain-specific technical support components for ReactiveSupportSolverMixin.

This module provides mock implementations of the required dependencies
for the ReactiveSupportSolverMixin to demonstrate its intended behavior.
"""

from typing import Any
from dataclasses import dataclass
from .prompts import get_diagnostic_workflow_prompt


@dataclass
class DiagnosticWorkflow:
    """A diagnostic workflow for technical support."""

    name: str
    description: str
    checklist: list[str]
    resources: list[str]

    def execute_with_llm(self, issue_description: str, artifacts: dict[str, Any], llm_resource) -> dict[str, Any]:
        """Execute the workflow using LLM to generate dynamic diagnostic steps."""
        # Use the extracted prompt template
        prompt = get_diagnostic_workflow_prompt(issue_description, self.name, artifacts, self.resources)

        try:
            # Create LLM request
            from dana.common.types import BaseRequest

            request = BaseRequest(
                arguments={
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a technical support expert specializing in {self.name.lower()}. Provide clear, actionable diagnostic steps and solutions.",
                        },
                        {"role": "user", "content": prompt},
                    ]
                }
            )

            response = llm_resource.query_sync(request)

            # Parse the response
            if hasattr(response, "content") and isinstance(response.content, str):
                response_text = response.content
            elif hasattr(response, "content") and isinstance(response.content, dict):
                if "choices" in response.content and len(response.content["choices"]) > 0:
                    choice = response.content["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        response_text = choice["message"]["content"]
                    else:
                        response_text = str(response.content)
                else:
                    response_text = str(response.content)
            else:
                response_text = str(response)

            # Parse the structured response
            return self._parse_llm_response(response_text)

        except Exception as e:
            return {
                "diagnosis": f"Error generating diagnostic plan: {e}",
                "checklist": self.checklist,  # Fallback to static checklist
                "solution": "Please contact technical support for assistance.",
            }

    def _parse_llm_response(self, response_text: str) -> dict[str, Any]:
        """Parse the LLM response into structured components."""
        lines = response_text.split("\n")

        diagnosis = "Issue identified"
        checklist = []
        solution = "Follow the diagnostic steps above"

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("DIAGNOSIS:"):
                diagnosis = line.replace("DIAGNOSIS:", "").strip()
                current_section = "diagnosis"
            elif line.startswith("CHECKLIST:"):
                current_section = "checklist"
            elif line.startswith("SOLUTION:"):
                solution = line.replace("SOLUTION:", "").strip()
                current_section = "solution"
            elif current_section == "checklist" and (
                line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) or line.startswith("-")
            ):
                # Extract checklist item
                item = line
                if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                    item = line[2:].strip()
                elif line.startswith("-"):
                    item = line[1:].strip()
                checklist.append(item)

        # If no checklist was parsed, use the static one
        if not checklist:
            checklist = self.checklist

        return {"diagnosis": diagnosis, "checklist": checklist, "solution": solution}


@dataclass
class SignatureMatch:
    """A signature match for known technical issues."""

    id: str
    title: str
    score: float
    workflow_id: str
    patterns: list[str]


class LLMPoweredWorkflowCatalog:
    """LLM-powered workflow catalog for technical support workflows."""

    def __init__(self):
        self.workflows = {
            "network_connectivity": DiagnosticWorkflow(
                name="Network Connectivity Diagnostic",
                description="Diagnose network connection issues using LLM",
                checklist=[
                    "Check physical network connections",
                    "Verify network adapter is enabled",
                    "Test with different network cable",
                    "Check firewall and antivirus settings",
                    "Verify DNS settings",
                    "Test with different network (mobile hotspot)",
                ],
                resources=["ping", "traceroute", "network_adapter_check", "dns_test"],
            ),
            "hardware_device": DiagnosticWorkflow(
                name="Hardware Device Diagnostic",
                description="Diagnose hardware device issues using LLM",
                checklist=[
                    "Check device power connections",
                    "Verify device is recognized in Device Manager",
                    "Test with different USB port/cable",
                    "Check device drivers and updates",
                    "Test device on different computer",
                    "Check for hardware conflicts",
                ],
                resources=["device_manager", "driver_checker", "hardware_diagnostics", "usb_tester"],
            ),
            "software_application": DiagnosticWorkflow(
                name="Software Application Diagnostic",
                description="Diagnose software application issues using LLM",
                checklist=[
                    "Check application system requirements",
                    "Verify application is up to date",
                    "Check for conflicting software",
                    "Run application as administrator",
                    "Check application logs for errors",
                    "Reinstall application if necessary",
                ],
                resources=["system_requirements", "application_logs", "compatibility_checker", "installer"],
            ),
            "performance_system": DiagnosticWorkflow(
                name="System Performance Diagnostic",
                description="Diagnose system performance issues using LLM",
                checklist=[
                    "Check CPU and memory usage",
                    "Close unnecessary applications",
                    "Check for malware and viruses",
                    "Verify system has adequate free disk space",
                    "Check for memory leaks in running processes",
                    "Consider system restart",
                ],
                resources=["task_manager", "performance_monitor", "antivirus_scanner", "disk_cleanup"],
            ),
            "uart_communication": DiagnosticWorkflow(
                name="UART Communication Diagnostic",
                description="Diagnose UART/serial communication issues using LLM",
                checklist=[
                    "Verify TX/RX pin connections",
                    "Check baud rate matches on both ends",
                    "Verify ground connection",
                    "Test with known working configuration",
                    "Check for electrical interference",
                    "Verify UART driver installation",
                ],
                resources=["serial_monitor", "baud_rate_checker", "pin_tester", "oscilloscope"],
            ),
        }

    def get_workflow(self, workflow_id: str) -> DiagnosticWorkflow | None:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> list[str]:
        """List all available workflow IDs."""
        return list(self.workflows.keys())


class MockSignatureMatcher:
    """Mock signature matcher for technical support patterns."""

    def __init__(self):
        self.patterns = {
            "network_connectivity": {
                "patterns": ["network", "connection", "timeout", "unreachable", "internet", "wifi", "ethernet", "can't connect"],
                "workflow_id": "network_connectivity",
            },
            "hardware_device": {
                "patterns": ["hardware", "device", "not working", "broken", "usb", "peripheral", "hardware failure"],
                "workflow_id": "hardware_device",
            },
            "software_application": {
                "patterns": ["software", "application", "app", "crashing", "error", "bug", "software issue"],
                "workflow_id": "software_application",
            },
            "performance_system": {
                "patterns": ["slow", "lagging", "performance", "memory", "cpu", "freezing", "hanging"],
                "workflow_id": "performance_system",
            },
            "uart_communication": {
                "patterns": [
                    "uart",
                    "serial",
                    "communication",
                    "pinned up",
                    "logic lines",
                    "pin outs",
                    "ones",
                    "zeros",
                    "baud",
                    "timeout",
                    "9600",
                ],
                "workflow_id": "uart_communication",
            },
        }

    def match(self, message: str, entities: dict[str, Any]) -> tuple[float, SignatureMatch | None]:
        """
        Match a message against known technical support patterns.

        Returns:
            tuple: (score, signature_match) where score is 0.0-1.0
        """
        message_lower = message.lower()

        best_score = 0.0
        best_match = None

        for pattern_id, pattern_data in self.patterns.items():
            patterns = pattern_data["patterns"]
            workflow_id = pattern_data["workflow_id"]

            # Count matching patterns
            matches = sum(1 for pattern in patterns if pattern in message_lower)

            if matches > 0:
                # Calculate score based on number of matches and pattern specificity
                score = min(0.3 + (matches * 0.2), 1.0)

                if score > best_score:
                    best_score = score
                    best_match = SignatureMatch(
                        id=pattern_id,
                        title=f"{pattern_id.replace('_', ' ').title()} Issue",
                        score=score,
                        workflow_id=workflow_id,
                        patterns=patterns,
                    )

        return best_score, best_match


class MockResourceIndex:
    """Mock resource index for technical support resources."""

    def __init__(self):
        self.resources = {
            "network_tools": ["ping", "traceroute", "network_adapter_check", "dns_test"],
            "hardware_tools": ["device_manager", "driver_checker", "hardware_diagnostics", "usb_tester"],
            "software_tools": ["system_requirements", "application_logs", "compatibility_checker", "installer"],
            "performance_tools": ["task_manager", "performance_monitor", "antivirus_scanner", "disk_cleanup"],
            "uart_tools": ["serial_monitor", "baud_rate_checker", "pin_tester", "oscilloscope"],
        }

    def get_resources(self, category: str) -> list[str]:
        """Get resources for a specific category."""
        return self.resources.get(category, [])

    def pack(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Pack resources based on entities."""
        packed = {}
        for category, tools in self.resources.items():
            packed[category] = tools
        return packed


def create_llm_powered_support_components():
    """Create LLM-powered support components for testing."""
    return {
        "workflow_catalog": LLMPoweredWorkflowCatalog(),
        "signature_matcher": MockSignatureMatcher(),
        "resource_index": MockResourceIndex(),
    }
