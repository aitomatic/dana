"""
Agent utilities for Dana stdlib.

This module provides utility functions for working with agents that require
explicit imports. Core agent functionality is available automatically.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.agent.agent_struct_system import AgentStructInstance, AgentStructType, register_agent_struct_type


def create_agent_pool(agent_type: str, count: int, configs: list[dict[str, Any]] | None = None) -> list[AgentStructInstance]:
    """
    Create a pool of agent instances for parallel processing.

    Args:
        agent_type: The name of the agent type to create
        count: Number of agents to create
        configs: Optional list of configurations for each agent

    Returns:
        List of agent instances

    Example:
        import agent

        # Create 3 customer service agents
        agents = create_agent_pool("CustomerService", 3, [
            {"domain": "billing"},
            {"domain": "technical"},
            {"domain": "general"}
        ])
    """
    agents = []
    for i in range(count):
        config = configs[i] if configs and i < len(configs) else {}
        # Create agent instance directly using agent system
        agent_struct_type = AgentStructType(name=agent_type)
        register_agent_struct_type(agent_struct_type)
        agent_instance = AgentStructInstance(agent_struct_type, config)
        agents.append(agent_instance)
    return agents


def load_agent_config(filepath: str) -> dict[str, Any]:
    """
    Load agent configuration from a file.

    Args:
        filepath: Path to the configuration file

    Returns:
        Configuration dictionary

    Example:
        import agent

        config = load_agent_config("my_agent_config.json")
        my_agent = agent("MyAgent", config)
    """
    import json

    with open(filepath) as f:
        return json.load(f)


def save_agent_config(agent_instance: AgentStructInstance, filepath: str) -> bool:
    """
    Save agent configuration to a file.

    Args:
        agent_instance: The agent instance to save
        filepath: Path to save the configuration

    Returns:
        True if successful, False otherwise

    Example:
        import agent

        my_agent = agent("MyAgent", {"domain": "tech"})
        save_agent_config(my_agent, "agent_config.json")
    """
    import json

    try:
        config = {"type": agent_instance.agent_type.name, "fields": agent_instance._values}
        with open(filepath, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False


def agent_benchmark(agent_instance: AgentStructInstance, tasks: list[str]) -> dict[str, Any]:
    """
    Benchmark an agent's performance on a set of tasks.

    Args:
        agent_instance: The agent to benchmark
        tasks: List of tasks to test

    Returns:
        Benchmark results dictionary

    Example:
        import agent

        my_agent = agent("MyAgent", {"domain": "tech"})
        results = agent_benchmark(my_agent, [
            "Solve simple problem",
            "Plan complex task",
            "Recall previous information"
        ])
    """
    import time

    results = {"agent_type": agent_instance.agent_type.name, "tasks": len(tasks), "execution_times": [], "success_rate": 0}

    successful_tasks = 0
    for task in tasks:
        start_time = time.time()
        try:
            # Test plan method
            agent_instance.plan(task)
            successful_tasks += 1
        except Exception:
            pass
        execution_time = time.time() - start_time
        results["execution_times"].append(execution_time)

    results["success_rate"] = successful_tasks / len(tasks) if tasks else 0
    results["average_time"] = sum(results["execution_times"]) / len(results["execution_times"]) if results["execution_times"] else 0

    return results


def agent_metrics(agent_instance: AgentStructInstance) -> dict[str, Any]:
    """
    Get metrics about an agent's usage and performance.

    Args:
        agent_instance: The agent to get metrics for

    Returns:
        Metrics dictionary

    Example:
        import agent

        my_agent = agent("MyAgent", {"domain": "tech"})
        metrics = agent_metrics(my_agent)
        print(f"Memory entries: {metrics['memory_entries']}")
    """
    # Get conversation stats if available
    conversation_stats = {}
    try:
        conversation_stats = agent_instance.get_conversation_stats()
    except Exception:
        pass

    # Get memory info
    memory_entries = 0
    try:
        memory_entries = len(agent_instance._memory) if hasattr(agent_instance, "_memory") else 0
    except Exception:
        pass

    return {
        "agent_type": agent_instance.agent_type.name,
        "memory_entries": memory_entries,
        "conversation_stats": conversation_stats,
        "has_llm": hasattr(agent_instance, "llm") and agent_instance.llm is not None,
    }
