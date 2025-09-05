#!/usr/bin/env python3
"""
World Model Demo Script

This script demonstrates the world model functionality in action,
showing how agents can be aware of time, location, and system context.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime

from dana.core.agent.mind.agent_mind import AgentMind
from dana.core.agent.mind.models.world_model import DomainKnowledge


def demo_world_model_basics():
    """Demonstrate basic world model functionality."""
    print("🌍 World Model Basic Functionality Demo")
    print("=" * 50)

    # Create an agent mind with world model
    agent_mind = AgentMind()
    agent_mind.initialize_mind("demo_user")

    # Get current world context
    world_context = agent_mind.get_world_context()
    print(f"Current World State: {world_context.timestamp}")
    print()

    # Demonstrate temporal awareness
    print("⏰ Temporal Awareness:")
    time_context = agent_mind.get_temporal_context()
    print(f"  Current Time: {time_context.current_time}")
    print(f"  Timezone: {time_context.timezone}")
    print(f"  Day of Week: {time_context.day_of_week}")
    print(f"  Business Hours: {time_context.is_business_hours}")
    print(f"  Holiday: {time_context.is_holiday}")
    print(f"  Season: {time_context.season}")
    print(f"  Time Period: {time_context.time_period}")
    print()

    # Demonstrate location awareness
    print("📍 Location Awareness:")
    location_context = agent_mind.get_location_context()
    print(f"  Country: {location_context.country}")
    print(f"  Region: {location_context.region}")
    print(f"  City: {location_context.city}")
    print(f"  Timezone: {location_context.timezone}")
    print(f"  Environment: {location_context.environment}")
    print(f"  Network: {location_context.network}")
    print()

    # Demonstrate system awareness
    print("💻 System Awareness:")
    system_context = agent_mind.get_system_context()
    print(f"  System Load: {system_context.system_load}")
    print(f"  Memory Usage: {system_context.memory_usage:.1f}%")
    print(f"  Network Status: {system_context.network_status}")
    print(f"  System Health: {system_context.system_health}")
    print(f"  Maintenance Mode: {system_context.maintenance_mode}")
    print()


def demo_business_logic():
    """Demonstrate business logic based on world context."""
    print("🧠 Business Logic Demo")
    print("=" * 50)

    agent_mind = AgentMind()
    agent_mind.initialize_mind("demo_user")

    # Business hours logic
    print("⏰ Business Hours Logic:")
    is_business_hours = agent_mind.is_business_hours()
    is_holiday = agent_mind.is_holiday()

    if is_business_hours and not is_holiday:
        print("  ✅ Currently in business hours - normal processing available")
        processing_mode = "normal"
    else:
        print("  ⚠️  Outside business hours or holiday - limited processing")
        processing_mode = "limited"

    print(f"  Processing Mode: {processing_mode}")
    print()

    # System health logic
    print("💻 System Health Logic:")
    system_health = agent_mind.get_system_health()
    is_healthy = agent_mind.is_system_healthy()

    print(f"  System Health: {system_health}")
    print(f"  Is Healthy: {is_healthy}")

    if is_healthy:
        print("  ✅ System is healthy - full capabilities available")
        max_tasks = 5
    else:
        print("  ⚠️  System is stressed - using conservative settings")
        max_tasks = 1

    print(f"  Max Concurrent Tasks: {max_tasks}")
    print()

    # Resource optimization
    print("⚡ Resource Optimization:")
    should_use_lightweight = agent_mind.should_use_lightweight_processing()
    optimal_concurrency = agent_mind.get_optimal_concurrency_level()

    print(f"  Should Use Lightweight Processing: {should_use_lightweight}")
    print(f"  Optimal Concurrency Level: {optimal_concurrency}")

    if should_use_lightweight:
        print("  🚨 Using lightweight processing due to system stress")
    else:
        print("  ✅ Using normal processing - system has capacity")
    print()


def demo_localization():
    """Demonstrate localization based on location context."""
    print("🌐 Localization Demo")
    print("=" * 50)

    agent_mind = AgentMind()
    agent_mind.initialize_mind("demo_user")

    # Get localization settings
    settings = agent_mind.get_localization_settings()

    print("Localization Settings:")
    for key, value in settings.items():
        print(f"  {key}: {value}")

    print()

    # Show how this affects formatting
    from datetime import datetime

    now = datetime.now()

    print("Formatted Output Examples:")
    if settings["time_format"] == "12-hour":
        time_str = now.strftime("%I:%M %p")
    else:
        time_str = now.strftime("%H:%M")

    if settings["date_format"] == "MM/DD/YYYY":
        date_str = now.strftime("%m/%d/%Y")
    else:
        date_str = now.strftime("%d/%m/%Y")

    print(f"  Date: {date_str}")
    print(f"  Time: {time_str}")
    print(f"  Currency: {settings['currency']}")
    print()


def demo_domain_knowledge():
    """Demonstrate domain knowledge functionality."""
    print("🧠 Domain Knowledge Demo")
    print("=" * 50)

    agent_mind = AgentMind()
    agent_mind.initialize_mind("demo_user")

    # Create some sample domain knowledge
    semiconductor_knowledge = DomainKnowledge(
        domain="semiconductor",
        topics=["inspection", "quality_control", "defect_detection"],
        expertise_level="expert",
        last_updated=datetime.now(),
        confidence_score=0.95,
        sources=["training_data", "industry_experience", "research_papers"],
    )

    # Add it to the world model
    agent_mind.update_domain_knowledge("semiconductor", semiconductor_knowledge)

    # Retrieve and display
    retrieved_knowledge = agent_mind.get_domain_knowledge("semiconductor")
    if retrieved_knowledge:
        print("Semiconductor Domain Knowledge:")
        print(f"  Domain: {retrieved_knowledge.domain}")
        print(f"  Topics: {', '.join(retrieved_knowledge.topics)}")
        print(f"  Expertise Level: {retrieved_knowledge.expertise_level}")
        print(f"  Confidence Score: {retrieved_knowledge.confidence_score}")
        print(f"  Sources: {', '.join(retrieved_knowledge.sources)}")
        print()

    # Demonstrate shared patterns
    print("📊 Shared Patterns Demo:")

    # Add a successful pattern
    success_pattern = {
        "problem_type": "wafer_defect_detection",
        "strategy": "multi_layer_analysis",
        "success_rate": 0.98,
        "execution_time": 2.1,
        "user_satisfaction": 0.95,
    }

    agent_mind.add_shared_pattern("strategy", "wafer_defect_detection", success_pattern)

    # Retrieve patterns
    patterns = agent_mind.get_shared_patterns("strategy")
    if patterns:
        print("Available Strategy Patterns:")
        for pattern_id, pattern_data in patterns.items():
            print(f"  {pattern_id}: {pattern_data['strategy']} (Success: {pattern_data['success_rate']:.1%})")
    print()


def main():
    """Run all demos."""
    print("🚀 Dana World Model Demonstration")
    print("=" * 60)
    print()

    try:
        demo_world_model_basics()
        demo_business_logic()
        demo_localization()
        demo_domain_knowledge()

        print("🎉 All demos completed successfully!")
        print("\nThe world model provides agents with:")
        print("  • Temporal awareness (time, business hours, holidays)")
        print("  • Spatial awareness (location, timezone, environment)")
        print("  • System awareness (health, resources, performance)")
        print("  • Domain knowledge and shared patterns")
        print("  • Business logic and resource optimization")
        print("  • Localization and cultural adaptation")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
