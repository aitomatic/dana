#!/usr/bin/env python3
"""
Use Case 07: Dana Agent Deployment via A2A Protocol

This example demonstrates deploying and accessing Dana agents via the A2A (Agent-to-Agent) protocol.
Shows how to expose Dana AI capabilities as network-accessible services that can be consumed
by other applications and agents.

Business Value:
- Deploy Dana agents as scalable microservices
- Enable agent-to-agent communication
- Build AI service meshes with specialized Dana agents
- Access Dana AI capabilities over HTTP/network protocols

Prerequisites:
1. Deploy the Dana agent: dana deploy dana/manufacturing_qa_agent.na --protocol a2a
2. Ensure agent is running on localhost:8000 (default)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import argparse
import socket
import sys
import time

from python_a2a import A2AClient


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    try:
        import python_a2a  # noqa: F401

        print("✅ All dependencies installed correctly")
        return True
    except ImportError:
        print("❌ Missing dependency: python-a2a")
        print('Please install: pip install "python-a2a[server]"')
        return False


def find_available_port(start_port: int = 8000, max_tries: int = 10) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("localhost", port))
                return port
        except OSError:
            continue
    return start_port


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Dana A2A Client Example")
    parser.add_argument("--port", type=int, default=None, help="Port to connect to (default: 8000)")
    parser.add_argument("--external", type=str, default=None, help="External A2A endpoint URL")
    return parser.parse_args()


def get_agent_info(client: A2AClient) -> None:
    """Retrieve and display agent information."""
    try:
        print("=== Agent Information ===")
        print(f"Name: {client.agent_card.name}")
        print(f"Description: {client.agent_card.description}")
        print(f"Version: {client.agent_card.version}")

        if client.agent_card.skills:
            print("\nAvailable Skills:")
            for skill in client.agent_card.skills:
                print(f"- {skill.name}: {skill.description}")
    except Exception as e:
        print(f"⚠️ Could not retrieve agent card: {e}")
        print("The agent may not support the A2A discovery protocol.")


def test_agent_queries(client: A2AClient) -> None:
    """Test manufacturing quality queries."""
    test_queries = [
        "Analyze batch quality: defect rate 2.3%, Cpk=1.1, 5 dimensional failures out of 100 parts",
        "Equipment alert: CNC machine temperature 95°C, vibration 0.8mm/s, cycle time increased 15%",
        "Quality deviation investigation: adhesive bond strength dropped from 850N to 720N average",
        "Process optimization request: injection molding cycle 45s, 8% scrap rate, target <5%",
    ]

    print("\n🤖 Testing A2A Agent Communication")
    print("-" * 40)

    for i, query in enumerate(test_queries, 1):
        print(f"\n📤 Test {i}: {query}")
        try:
            response = client.ask(query)
            print(f"📥 Response: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")

        if i < len(test_queries):
            time.sleep(1)


def main() -> int:
    """Main execution function."""
    print("🎯 Use Case 07: Dana Agent Deployment via A2A Protocol")
    print("=" * 60)

    if not check_dependencies():
        return 1

    args = parse_arguments()
    port = args.port or 8000
    endpoint_url = args.external or f"http://localhost:{port}"

    print(f"🔌 Connecting to A2A agent at: {endpoint_url}")

    try:
        client = A2AClient(endpoint_url)
        get_agent_info(client)
        test_agent_queries(client)

        print("\n✅ Dana Agent Deployment via A2A Success!")
        print("💡 Key Benefits:")
        print("   - Dana agents deployed as scalable microservices")
        print("   - Distributed AI service mesh architecture")
        print("   - Language-agnostic access to Dana capabilities")
        print("   - Seamless integration with existing systems")
        return 0

    except Exception as e:
        print(f"\n❌ Error connecting to agent: {e}")
        print("\nPossible reasons:")
        print("- The endpoint URL is incorrect")
        print("- The manufacturing QA agent is not running")
        print("- Network connectivity issues")
        print("\n📋 To deploy the agent, run:")
        print("   dana deploy dana/manufacturing_qa_agent.na --protocol a2a")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)
