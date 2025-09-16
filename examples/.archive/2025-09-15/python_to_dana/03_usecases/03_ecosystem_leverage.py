#!/usr/bin/env python3
"""
Use Case 03: Ecosystem Leverage

Dana programs can **indirectly benefit** from Python's rich ecosystem.
This demonstrates integration with AWS, databases, ML frameworks via Python.

Business Value: Access Python's vast library ecosystem
- Integrate with AWS, databases, ML frameworks
- Dana benefits from Python's mature tooling
- Complex system integrations made simple

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import time

from dana.dana import dana

# dana.set_debug(True)


def simulate_aws_data():
    """
    Python Excellence: Cloud service integration
    (In real world: boto3.client('s3').get_object(...))
    """
    return {
        "metrics": [
            {"instance_id": "i-1234", "cpu_usage": 85.2, "memory_usage": 72.1},
            {"instance_id": "i-5678", "cpu_usage": 45.8, "memory_usage": 63.4},
            {"instance_id": "i-9012", "cpu_usage": 92.7, "memory_usage": 89.3},
        ],
        "timestamp": time.time(),
        "region": "us-east-1",
    }


def simulate_database_query():
    """
    Python Excellence: Database integration
    (In real world: sqlalchemy query or MongoDB aggregation)
    """
    return {
        "performance_history": [
            {"day": "monday", "avg_response_time": 120},
            {"day": "tuesday", "avg_response_time": 145},
            {"day": "wednesday", "avg_response_time": 200},
        ],
        "cost_data": {"monthly_cost": 2500, "projected_cost": 3200},
    }


def main():
    print("🎯 Use Case 03: Ecosystem Leverage")
    print("=" * 40)

    # Python excels at complex integrations
    print("🐍 Python: Fetching AWS cloud metrics...")
    aws_data = simulate_aws_data()

    print("🐍 Python: Querying performance database...")
    db_data = simulate_database_query()

    print("🐍 Python: Preparing data for AI analysis...")
    combined_data = {"cloud_metrics": aws_data, "performance_data": db_data, "analysis_timestamp": time.time()}

    print(f"   📊 Analyzed {len(aws_data['metrics'])} instances")
    print(f"   💰 Monthly cost: ${db_data['cost_data']['monthly_cost']}")

    # Dana excels at intelligent optimization
    print("\n🤖 Dana: AI-powered cloud optimization...")
    dana.enable_module_imports()

    try:
        import aws_optimizer  # Dana module

        # Dana provides intelligent insights
        optimization = aws_optimizer.optimize_infrastructure(combined_data)
        cost_savings = aws_optimizer.calculate_savings(str(optimization))

        print(f"   🎯 Optimization Strategy: {optimization}")
        print(f"   💵 Projected Savings: {cost_savings}")

    finally:
        dana.disable_module_imports()

    print("\n✅ Success! Leveraged Python's ecosystem + Dana's AI intelligence")
    print("💡 Key Insight: Python handles complex integrations, Dana optimizes decisions")


if __name__ == "__main__":
    main()
