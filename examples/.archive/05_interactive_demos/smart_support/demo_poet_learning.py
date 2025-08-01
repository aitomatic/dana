#!/usr/bin/env python3
"""
POET Smart Customer Support Learning Demonstration

This script demonstrates the refactored POET-enhanced customer support agent
with clean decorator syntax and modular design.

Run this script to see:
- Real POET learning in action with @poet() decorator
- Prompt optimization based on customer feedback
- Learning progression over multiple interactions
- Comparison between basic and POET-enhanced responses
"""

import time
from typing import Any

from smart_support_agent import SmartSupportAgent
from support_systems import (
    CustomerTier,
    IssueType,
    SentimentLevel,
    basic_customer_support,
    generate_demo_customers,
    generate_demo_tickets,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_response_comparison(basic_response, poet_response, ticket):
    """Print a comparison between basic and POET responses."""
    print(f"\n🎫 Ticket: {ticket.subject}")
    print(f"👤 Customer: {ticket.customer.name} ({ticket.customer.tier.value})")
    print(f"😟 Sentiment: {ticket.sentiment.value}")

    print("\n📝 BASIC Response:")
    print(f"   Text: {basic_response.response_text[:150]}...")
    print(f"   Confidence: {basic_response.confidence_score:.2f}")
    print(f"   Escalation: {basic_response.escalation_recommended}")

    print("\n🎭 POET Response:")
    print(f"   Text: {poet_response.response_text[:150]}...")
    print(f"   Confidence: {poet_response.confidence_score:.2f}")
    print(f"   Escalation: {poet_response.escalation_recommended}")
    print(f"   Reasoning: {poet_response.reasoning}")


def simulate_customer_feedback(response, ticket) -> dict[str, Any]:
    """Simulate realistic customer feedback based on response quality."""
    # Simulate satisfaction based on response characteristics
    base_satisfaction = 3.0

    # Positive factors
    if ticket.customer.name.lower() in response.response_text.lower():
        base_satisfaction += 0.5  # Personalization

    if ticket.customer.tier == CustomerTier.ENTERPRISE and "enterprise" in response.response_text.lower():
        base_satisfaction += 0.3  # Tier recognition

    if ticket.sentiment in [SentimentLevel.FRUSTRATED, SentimentLevel.VERY_ANGRY]:
        if any(word in response.response_text.lower() for word in ["sorry", "apologize"]):
            base_satisfaction += 0.4  # Appropriate empathy
        else:
            base_satisfaction -= 0.5  # Missed empathy opportunity

    # Simulate resolution time (hours)
    if response.escalation_recommended:
        resolution_time = 1.5 + (0.5 if ticket.customer.tier == CustomerTier.ENTERPRISE else 1.0)
    else:
        resolution_time = 4.0 + (2.0 if ticket.issue_type == IssueType.TECHNICAL else 0.0)

    # Was escalation actually needed?
    escalation_factors = [
        ticket.customer.tier == CustomerTier.ENTERPRISE,
        ticket.sentiment in [SentimentLevel.VERY_ANGRY, SentimentLevel.FRUSTRATED],
        ticket.urgency in ["high", "critical"],
        ticket.customer.previous_contacts > 3,
    ]
    actual_escalation_needed = sum(escalation_factors) >= 2

    # Adjust satisfaction based on escalation accuracy
    if response.escalation_recommended == actual_escalation_needed:
        base_satisfaction += 0.2
    else:
        base_satisfaction -= 0.3

    return {
        "satisfaction": max(1.0, min(5.0, base_satisfaction)),
        "resolution_time": resolution_time,
        "escalation_needed": actual_escalation_needed,
    }


def demonstrate_poet_learning():
    """Demonstrate POET learning capabilities."""
    print_section("POET Smart Customer Support Learning Demo")

    # Create agent instance
    agent = SmartSupportAgent()

    print("\n🤖 Created POET Smart Support Agent")
    print("📊 Initial Learning Status:")
    initial_status = agent.get_learning_status()
    for key, value in initial_status.items():
        print(f"   {key}: {value}")

    # Generate demo data
    customers = generate_demo_customers()
    tickets = generate_demo_tickets(customers)

    print(f"\n📋 Generated {len(tickets)} demo support tickets")

    # Process tickets and provide feedback for learning
    print_section("Processing Tickets with Learning Feedback")

    for i, ticket in enumerate(tickets, 1):
        print(f"\n🎫 Processing Ticket {i}/{len(tickets)}: {ticket.subject}")

        # Generate POET response
        poet_response = agent.generate_support_response(ticket)

        # Handle POET result wrapper (mock decorator returns dict wrapper)
        if isinstance(poet_response, dict) and "result" in poet_response:
            poet_response = poet_response["result"]

        # Simulate customer feedback
        feedback = simulate_customer_feedback(poet_response, ticket)

        print(f"   📝 Response generated (confidence: {poet_response.confidence_score:.2f})")
        print(f"   🎭 Tone: {poet_response.tone}")
        print(f"   ⏱️  Estimated resolution: {poet_response.estimated_resolution_time}")
        print(f"   📈 Escalation recommended: {poet_response.escalation_recommended}")

        # Provide feedback to POET for learning
        agent.provide_learning_feedback(
            response=poet_response,
            ticket=ticket,
            actual_satisfaction=feedback["satisfaction"],
            actual_resolution_time=feedback["resolution_time"],
            actual_escalation_needed=feedback["escalation_needed"],
        )

        print(f"   ✅ Feedback provided: satisfaction={feedback['satisfaction']:.1f}/5.0")

        # Show learning progress every few tickets
        if i % 2 == 0:
            status = agent.get_learning_status()
            print(f"   📊 Learning progress: {status.get('status', 'Learning...')}")

        time.sleep(0.1)  # Brief pause for readability

    # Show final learning status
    print_section("Final Learning Status")
    final_status = agent.get_learning_status()
    for key, value in final_status.items():
        print(f"   {key}: {value}")

    # Compare responses before and after learning
    print_section("Learning Impact Demonstration")

    test_ticket = tickets[0]  # Use first ticket as test case
    print(f"\n🧪 Testing with: {test_ticket.subject}")

    # Generate new responses (should be improved after learning)
    basic_response = basic_customer_support(test_ticket)
    final_poet_response = agent.generate_support_response(test_ticket)

    # Handle POET result wrapper
    if isinstance(final_poet_response, dict) and "result" in final_poet_response:
        final_poet_response = final_poet_response["result"]

    print_response_comparison(basic_response, final_poet_response, test_ticket)

    print("\n🎯 Key Improvements:")
    print(f"   • Confidence: {final_poet_response.confidence_score:.2f} vs {basic_response.confidence_score:.2f}")
    print(
        f"   • Personalization: {'Name used' if test_ticket.customer.name.lower() in final_poet_response.response_text.lower() else 'Generic'}"
    )
    print(f"   • Context awareness: {final_poet_response.reasoning}")

    return agent


def demonstrate_decorator_syntax():
    """Demonstrate the clean @poet decorator syntax."""
    print_section("Clean @poet() Decorator Syntax")

    print("\n✨ Before refactoring (awkward):")
    print("```python")
    print("# Old approach - awkward variable assignment")
    print("poet_decorator = poet(domain='...', enable_training=True)")
    print("@poet_decorator")
    print("def my_function():")
    print("    pass")
    print("```")

    print("\n🎉 After refactoring (clean):")
    print("```python")
    print("# New approach - direct decorator with parameters")
    print("@poet(")
    print("    domain='enhanced_llm_optimization',")
    print("    enable_training=True,")
    print("    learning_algorithm='statistical',")
    print("    learning_rate=0.1,")
    print("    performance_tracking=True")
    print(")")
    print("def generate_support_response(self, ticket, context=None):")
    print("    # POET automatically optimizes this function")
    print("    return optimized_response")
    print("```")

    print("\n🏗️  Architecture Benefits:")
    print("   • Clean, standard Python decorator syntax")
    print("   • Modular design with separate agent class")
    print("   • Conditional POET configuration based on availability")
    print("   • Proper separation of concerns")
    print("   • Easy testing and maintenance")


def main():
    """Run the complete demonstration."""
    demonstrate_decorator_syntax()
    agent = demonstrate_poet_learning()

    print_section("Summary")
    print("\n🎊 Demonstration Complete!")
    print("\n✅ What we've shown:")
    print("   • Clean @poet() decorator syntax (no more awkward variables)")
    print("   • Modular SmartSupportAgent class design")
    print("   • Real POET learning from customer feedback")
    print("   • Prompt optimization based on satisfaction scores")
    print("   • Progressive improvement over multiple interactions")
    print("   • Proper separation of POET agent from utility functions")

    print("\n🚀 Next Steps:")
    print("   • Run with real LLM API keys to see actual prompt optimization")
    print("   • Add more sophisticated feedback metrics")
    print("   • Implement A/B testing between prompt variants")
    print("   • Scale to production customer support scenarios")

    return agent


if __name__ == "__main__":
    main()
