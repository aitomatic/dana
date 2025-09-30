#!/usr/bin/env python3
"""
Example demonstrating the proper separation of concerns between AgentState and ContextEngineer.

This example shows how AgentState assembles its own ContextData and passes it to ContextEngineer,
maintaining clean separation of responsibilities.
"""

from dana.core.agent.context import ProblemContext
from dana.frameworks.ctxeng import ContextEngineer


def demonstrate_agent_state_context_assembly():
    """Demonstrate how AgentState assembles ContextData and passes it to ContextEngineer."""

    print("🏗️  Demonstrating AgentState -> ContextData -> ContextEngineer flow...")

    # Create a mock agent state (simplified for demonstration)
    class MockAgentState:
        def __init__(self):
            # Mock problem context
            self.problem_context = ProblemContext(
                problem_statement="How can I optimize my database performance?",
                objective="Reduce query response time by 50%",
                depth=0,
                constraints={"time_limit": "2 hours", "budget": "$500"},
                assumptions=["PostgreSQL database", "Read-heavy workload"],
            )

            # Mock mind with memory
            self.mind = MockAgentMind()

            # Mock execution context
            self.execution = MockExecutionContext()

            # Mock capabilities
            self.capabilities = MockCapabilities()

            # Mock timeline
            self.timeline = MockTimeline()

            # Session info
            self.session_id = "demo_session_123"

    class MockAgentMind:
        def recall_conversation(self, turns: int) -> str:
            return "Previous discussion about database performance issues and optimization strategies."

        def recall_relevant(self, problem_context) -> list[str]:
            return [
                "Similar optimization done 6 months ago for user table",
                "Previous index on product_category improved performance by 40%",
            ]

        def get_user_context(self) -> dict:
            return {"experience_level": "intermediate", "preferred_approach": "incremental_optimization", "risk_tolerance": "low"}

        def assess_context_needs(self, problem_context, depth: str) -> list[str]:
            return ["performance", "stability", "maintainability"]

        @property
        def world_model(self):
            return MockWorldModel()

    class MockWorldModel:
        def to_dict(self) -> dict:
            return {
                "database_trends": ["PostgreSQL adoption", "cloud_migration"],
                "performance_standards": {"web_app": "<1s", "api": "<500ms"},
            }

    class MockExecutionContext:
        def get_constraints(self) -> dict:
            return {
                "max_execution_time": 7200,  # 2 hours
                "max_memory_usage": 8.0,  # 8GB
                "allowed_downtime": 300,  # 5 minutes
            }

        @property
        def resource_limits(self):
            return MockResourceLimits()

        @property
        def current_metrics(self):
            return MockCurrentMetrics()

    class MockResourceLimits:
        def to_dict(self) -> dict:
            return {"max_indexes": 50, "max_connections": 100, "memory_limit": "8GB", "disk_space": "500GB"}

    class MockCurrentMetrics:
        def to_dict(self) -> dict:
            return {"current_connections": 45, "memory_usage": "6.2GB", "disk_usage": "320GB", "cpu_usage": "75%"}

    class MockCapabilities:
        def get_available_tools(self) -> dict:
            return {
                "database_analyzer": "Tool for analyzing database performance",
                "query_optimizer": "Tool for optimizing SQL queries",
                "index_advisor": "Tool for recommending database indexes",
            }

    class MockTimeline:
        def __init__(self):
            self.events = [
                MockEvent("analysis_started", "Started database performance analysis"),
                MockEvent("queries_identified", "Identified top 10 slowest queries"),
                MockEvent("indexes_created", "Created missing indexes for product search"),
            ]

    class MockEvent:
        def __init__(self, event_type: str, description: str):
            self.event_type = event_type
            self.data = {"description": description}

    # Add the assemble_context_data method to MockAgentState
    def assemble_context_data(self, query: str, template: str = "general"):
        """Assemble structured ContextData from agent state."""
        from dana.frameworks.ctxeng import (
            ContextData,
            ConversationContextData,
            ExecutionContextData,
            MemoryContextData,
            ProblemContextData,
            ResourceContextData,
        )

        # Create base context data
        context_data = ContextData.create_for_agent(query=query, template=template)

        # Extract problem context
        if self.problem_context:
            context_data.problem = ProblemContextData(
                problem_statement=self.problem_context.problem_statement,
                objective=self.problem_context.objective,
                original_problem=self.problem_context.original_problem,
                depth=self.problem_context.depth,
                constraints=self.problem_context.constraints,
                assumptions=self.problem_context.assumptions,
            )

        # Extract conversation context
        if self.mind:
            context_data.conversation = ConversationContextData(
                conversation_history=self.mind.recall_conversation(3),
                recent_events=self._get_recent_events(),
                user_preferences=self.mind.get_user_context(),
                context_depth="standard",
            )

        # Extract memory context
        if self.mind:
            context_data.memory = MemoryContextData(
                relevant_memories=self.mind.recall_relevant(self.problem_context) if self.problem_context else [],
                user_model=self.mind.get_user_context(),
                world_model=self.mind.world_model.to_dict() if self.mind.world_model else {},
                context_priorities=self.mind.assess_context_needs(self.problem_context, "standard") if self.problem_context else [],
            )

        # Extract execution context
        if self.execution:
            context_data.execution = ExecutionContextData(
                session_id=self.session_id,
                execution_constraints=self.execution.get_constraints(),
                environment_info={},
            )

        # Extract resource context
        if self.capabilities:
            context_data.resources = ResourceContextData(
                available_resources=list(self.capabilities.get_available_tools().keys()),
                resource_limits=self.execution.resource_limits.to_dict() if self.execution else {},
                resource_usage=self.execution.current_metrics.to_dict() if self.execution else {},
                resource_errors=[],
            )

        return context_data

    def _get_recent_events(self) -> list[str]:
        """Get recent events from timeline for context."""
        if not self.timeline or not self.timeline.events:
            return []

        try:
            events = self.timeline.events[-5:]  # Last 5 events
            return [f"{e.event_type}: {e.data.get('description', 'No description')}" for e in events]
        except Exception:
            return []

    # Add methods to MockAgentState
    MockAgentState.assemble_context_data = assemble_context_data
    MockAgentState._get_recent_events = _get_recent_events

    # Create mock agent state
    agent_state = MockAgentState()

    print("✅ Mock AgentState created with comprehensive context")

    # Step 1: AgentState assembles its own ContextData
    print("\n🔧 Step 1: AgentState assembles ContextData...")
    context_data = agent_state.assemble_context_data(query="How can I optimize my database performance?", template="problem_solving")

    print(f"✅ ContextData assembled with {len(context_data.get_available_context_keys())} context keys")
    print(f"📊 Context summary: {context_data.get_context_summary()}")

    # Step 2: ContextEngineer receives structured ContextData
    print("\n🔧 Step 2: ContextEngineer processes structured ContextData...")
    engineer = ContextEngineer(format_type="xml")
    rich_prompt = engineer.engineer_context_structured(context_data)

    print(f"✅ Rich prompt assembled: {len(rich_prompt)} characters")
    print("\n📄 Generated XML Prompt:")
    print("=" * 80)
    print(rich_prompt)
    print("=" * 80)

    # Demonstrate the clean separation
    print("\n🏗️  Architecture Benefits:")
    print("   • AgentState is responsible for assembling its own context")
    print("   • ContextEngineer focuses purely on prompt assembly")
    print("   • Clear separation of concerns")
    print("   • Type-safe context data flow")
    print("   • Easy to test and maintain")

    # Show context data structure
    print("\n📊 ContextData Structure:")
    print(f"   • Problem Context: {context_data.problem is not None}")
    print(f"   • Conversation Context: {context_data.conversation is not None}")
    print(f"   • Memory Context: {context_data.memory is not None}")
    print(f"   • Execution Context: {context_data.execution is not None}")
    print(f"   • Resource Context: {context_data.resources is not None}")


if __name__ == "__main__":
    print("🚀 AgentState Context Assembly Example")
    print("=" * 50)

    demonstrate_agent_state_context_assembly()

    print("\n🎉 Example completed successfully!")
    print("\n💡 Key Architecture Principles:")
    print("   • AgentState owns context assembly logic")
    print("   • ContextEngineer focuses on prompt generation")
    print("   • Structured data flow with type safety")
    print("   • Clean separation of responsibilities")
    print("   • Easy to extend and maintain")
