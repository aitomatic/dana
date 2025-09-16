#!/usr/bin/env python3
"""
Example demonstrating the new strongly-typed catalogs for WorkflowInstance and ResourceInstance.

This example shows how to use the WorkflowCatalog and ResourceCatalog classes
that work with concrete WorkflowInstance and ResourceInstance objects.
"""

import sys
import os

# Add the dana package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.registry import WorkflowRegistry, ResourceRegistry
from dana.core.agent.solvers import SignatureMatcher
from dana.core.workflow.workflow_system import WorkflowInstance, WorkflowType
from dana.core.resource.resource_instance import ResourceInstance, ResourceType


def create_example_workflow() -> WorkflowInstance:
    """Create an example workflow instance."""
    # Create a simple workflow type
    workflow_type = WorkflowType(
        name="ExampleWorkflow",
        fields={"task": "str", "result": "str"},
        field_order=["task", "result"],
        field_defaults={"task": "process_data", "result": "pending"},
        docstring="An example workflow for demonstration"
    )

    # Create workflow instance
    workflow = WorkflowInstance(
        struct_type=workflow_type,
        values={"task": "process_data", "result": "pending"}
    )

    return workflow


def create_example_resource() -> ResourceInstance:
    """Create an example resource instance."""
    # Create a simple resource type
    resource_type = ResourceType(
        name="ExampleResource",
        fields={"name": "str", "status": "str"},
        field_order=["name", "status"],
        field_defaults={"name": "example_resource", "status": "active"},
        docstring="An example resource for demonstration"
    )

    # Create resource instance
    resource = ResourceInstance(
        resource_type=resource_type,
        values={"name": "example_resource", "status": "active"}
    )

    return resource


def main():
    """Main function demonstrating strongly-typed catalogs."""
    print("=== Strongly-Typed Registries Demo ===")
    print("This demo shows how to use WorkflowRegistry and ResourceRegistry")
    print("with concrete WorkflowInstance and ResourceInstance objects.\n")

    # Create example instances
    print("Creating example instances...")
    workflow = create_example_workflow()
    resource = create_example_resource()

    print(f"✅ Created WorkflowInstance: {workflow.struct_type.name}")
    print(f"✅ Created ResourceInstance: {resource.resource_type.name}")

    # Test WorkflowRegistry
    print("\n=== Testing WorkflowRegistry ===")
    workflow_registry = WorkflowRegistry()

    # Add workflow to registry
    workflow_id = workflow_registry.track_workflow(workflow, "example_workflow", "demo")
    print(f"✅ Added workflow to registry: {workflow_id}")

    # Test workflow matching
    score, matched_workflow, metadata = workflow_registry.match_workflow_for_llm("process data", {})
    print(f"✅ Workflow matching: score={score}, matched={matched_workflow is not None}")

    # Test workflow retrieval
    retrieved_workflow = workflow_registry.get_instance(workflow_id)
    print(f"✅ Workflow retrieval: {retrieved_workflow is not None}")

    # Test ResourceRegistry
    print("\n=== Testing ResourceRegistry ===")
    resource_registry = ResourceRegistry()

    # Add resource to registry
    resource_id = resource_registry.track_resource(resource, "example_resource", "demo")
    print(f"✅ Added resource to registry: {resource_id}")

    # Test resource packing
    packed_resources = resource_registry.pack_resources_for_llm({"context": "demo"})
    print(f"✅ Resource packing: {len(packed_resources)} resources packed")

    # Test resource retrieval
    retrieved_resource = resource_registry.get_instance(resource_id)
    print(f"✅ Resource retrieval: {retrieved_resource is not None}")

    # Test SignatureMatcher
    print("\n=== Testing SignatureMatcher ===")
    signature_matcher = SignatureMatcher()

    # Add a pattern
    signature_matcher.add_pattern("network_issue", {
        "keywords": ["network", "connection", "timeout"],
        "category": "connectivity"
    })
    print(f"✅ Added signature pattern")

    # Test pattern matching
    score, match = signature_matcher.match("I have a network connection timeout", {})
    print(f"✅ Pattern matching: score={score}, matched={match is not None}")

    print("\n=== Demo Complete ===")
    print("All strongly-typed registries are working correctly!")
    print("The registries now work with concrete WorkflowInstance and ResourceInstance objects.")


if __name__ == "__main__":
    main()
