#!/usr/bin/env python3
"""
Example demonstrating the structured ContextData approach for context engineering.

This example shows how to use the new structured data classes to create
rich, type-safe context for LLM prompt assembly.
"""

from dana.frameworks.ctxeng import (
    ContextData,
    ContextEngineer,
    ConversationContextData,
    ExecutionContextData,
    MemoryContextData,
    ProblemContextData,
    ResourceContextData,
    WorkflowContextData,
)


def create_database_optimization_context():
    """Create a comprehensive context for database optimization problem."""

    # Create the main context data structure
    context_data = ContextData(query="How can I optimize my database performance?", template="problem_solving", use_case="analysis")

    # Add structured problem context
    context_data.problem = ProblemContextData(
        problem_statement="Database performance optimization for e-commerce platform",
        objective="Reduce average query response time from 2.5s to 1.25s",
        original_problem="Slow database queries affecting user experience",
        depth=0,
        constraints={
            "time_limit": "2 hours",
            "budget": "$500",
            "downtime": "minimal",
            "database_type": "PostgreSQL",
            "read_write_ratio": "80/20",
        },
        assumptions=[
            "Current database is PostgreSQL 13+",
            "Application is read-heavy (80% reads, 20% writes)",
            "Can modify indexes and queries",
            "Have access to query execution plans",
            "Can implement connection pooling",
        ],
    )

    # Add workflow context
    context_data.workflow = WorkflowContextData(
        current_workflow="DatabaseOptimizer_v2",
        workflow_state="analyzing_slow_queries",
        workflow_values={"queries_analyzed": 15, "slow_queries_found": 3, "indexes_created": 2, "queries_optimized": 1},
        execution_progress=0.4,
        error_count=0,
        retry_count=0,
    )

    # Add conversation context
    context_data.conversation = ConversationContextData(
        conversation_history="User reported slow page load times on product search. Initial analysis shows database queries taking 2-3 seconds. Need to optimize without affecting existing functionality.",
        recent_events=[
            "Started performance analysis",
            "Identified top 10 slowest queries",
            "Created missing indexes for product search",
            "Optimized user authentication query",
            "Currently analyzing product recommendation queries",
        ],
        user_preferences={
            "technical_level": "intermediate",
            "preferred_solutions": ["indexing", "query_optimization"],
            "avoid_changes": ["schema_modifications", "application_code"],
        },
        conversation_tone="technical",
        context_depth="comprehensive",
    )

    # Add resource context
    context_data.resources = ResourceContextData(
        available_resources=[
            "PostgreSQL 13.4",
            "pg_stat_statements extension",
            "EXPLAIN ANALYZE access",
            "Database monitoring tools",
            "Query profiling tools",
        ],
        resource_limits={"max_indexes": 50, "max_connections": 100, "memory_limit": "8GB", "disk_space": "500GB"},
        resource_usage={"current_connections": 45, "memory_usage": "6.2GB", "disk_usage": "320GB", "cpu_usage": "75%"},
        resource_errors=[],
    )

    # Add memory context
    context_data.memory = MemoryContextData(
        relevant_memories=[
            "Similar optimization done 6 months ago for user table",
            "Previous index on product_category improved performance by 40%",
            "Connection pooling reduced query time by 15% last year",
        ],
        learned_patterns=[
            "Composite indexes work well for multi-column WHERE clauses",
            "Partial indexes effective for filtered queries",
            "Query rewriting often better than adding indexes",
        ],
        user_model={"experience_level": "intermediate", "preferred_approach": "incremental_optimization", "risk_tolerance": "low"},
        world_model={
            "database_trends": ["PostgreSQL adoption", "cloud_migration"],
            "performance_standards": {"web_app": "<1s", "api": "<500ms"},
            "common_issues": ["missing_indexes", "n_plus_one_queries"],
        },
        context_priorities=["performance", "stability", "maintainability"],
    )

    # Add execution context
    context_data.execution = ExecutionContextData(
        session_id="db_opt_session_2024_001",
        execution_time=45.2,
        memory_usage=2.1,
        cpu_usage=35.0,
        execution_constraints={
            "max_execution_time": 7200,  # 2 hours
            "max_memory_usage": 8.0,  # 8GB
            "allowed_downtime": 300,  # 5 minutes
        },
        environment_info={
            "os": "Ubuntu 20.04",
            "postgresql_version": "13.4",
            "hardware": "8 CPU cores, 16GB RAM",
            "environment": "production",
        },
    )

    # Add additional context
    context_data.additional_context = {
        "database_type": "PostgreSQL",
        "current_performance": "avg 2.5s response time",
        "target_performance": "avg 1.25s response time",
        "critical_queries": ["product_search", "user_authentication", "order_processing"],
        "performance_metrics": {"slow_query_threshold": "1s", "current_slow_queries": 12, "avg_connections": 45, "cache_hit_ratio": 0.85},
    }

    return context_data


def demonstrate_context_assembly():
    """Demonstrate how to assemble context into rich prompts."""

    print("🏗️  Creating structured context data...")
    context_data = create_database_optimization_context()

    print(f"✅ Context created with {len(context_data.get_available_context_keys())} context keys")
    print(f"📊 Context summary: {context_data.get_context_summary()}")

    # Create context engineer
    engineer = ContextEngineer(format_type="xml")

    print("\n🔧 Assembling rich prompt using structured data...")

    # Method 1: Using structured data directly (recommended)
    rich_prompt = engineer.engineer_context_structured(context_data)

    print(f"✅ Rich prompt assembled: {len(rich_prompt)} characters")
    print("\n📄 Generated XML Prompt:")
    print("=" * 80)
    print(rich_prompt)
    print("=" * 80)

    # Method 2: Using traditional dictionary approach
    print("\n🔧 Assembling prompt using traditional dictionary approach...")
    context_dict = context_data.to_dict()
    traditional_prompt = engineer.engineer_context(context_data.query, context_dict, template=context_data.template)

    print(f"✅ Traditional prompt assembled: {len(traditional_prompt)} characters")
    print("📊 Both methods produce identical results:", rich_prompt == traditional_prompt)

    # Demonstrate text format
    print("\n🔧 Assembling prompt in text format...")
    text_engineer = ContextEngineer(format_type="text")
    text_prompt = text_engineer.engineer_context_structured(context_data)

    print(f"✅ Text prompt assembled: {len(text_prompt)} characters")
    print("\n📄 Generated Text Prompt:")
    print("=" * 80)
    print(text_prompt)
    print("=" * 80)


def demonstrate_factory_methods():
    """Demonstrate factory methods for creating context data."""

    print("\n🏭 Demonstrating factory methods...")

    # Create context from dictionary
    context_dict = {
        "query": "Test query",
        "template": "problem_solving",
        "problem_statement": "Test problem",
        "objective": "Test objective",
        "current_depth": 1,
        "constraints": {"time": "1 hour"},
        "assumptions": ["Test assumption"],
        "conversation_history": "Test conversation",
        "recent_events": ["Event 1", "Event 2"],
        "additional_context": {"key": "value"},
    }

    # Reconstruct from dictionary
    reconstructed_context = ContextData.from_dict(context_dict)
    print(f"✅ Reconstructed from dict: {reconstructed_context.query}")
    print(f"📊 Has problem context: {reconstructed_context.problem is not None}")
    print(f"📊 Has conversation context: {reconstructed_context.conversation is not None}")

    # Test serialization round-trip
    original_dict = reconstructed_context.to_dict()
    print(f"📊 Round-trip successful: {len(original_dict)} keys")


if __name__ == "__main__":
    print("🚀 Structured Context Data Example")
    print("=" * 50)

    demonstrate_context_assembly()
    demonstrate_factory_methods()

    print("\n🎉 Example completed successfully!")
    print("\n💡 Key Benefits of Structured ContextData:")
    print("   • Type safety and validation")
    print("   • Clear separation of context concerns")
    print("   • Easy serialization/deserialization")
    print("   • Factory methods for common use cases")
    print("   • Rich metadata and context summaries")
    print("   • Backward compatibility with dictionary approach")
