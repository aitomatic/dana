#!/usr/bin/env python3
"""
ConversationResource Example - Unified Resource for Conversation Analysis

Demonstrates all three methods of ConversationResource:
1. summarize() - Generate structured conversation summaries
2. detect_intent() - Classify message intent with context
3. extract_topics() - Extract topics with terminology preservation

Usage:
    python conversation_resource_example.py
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

import dana
from dana.lib.resources.conversation import ConversationResource

# Load environment variables
load_dotenv(dotenv_path=Path(dana.__path__[0]).parent / ".env", verbose=True, override=True)


async def example_unified_resource_basic():
    """Example: Using all methods on the same resource"""
    print("\n" + "=" * 70)
    print("Example 1: Unified Resource - All Methods")
    print("=" * 70)

    # Create ONE resource for all conversation analysis
    conversation = ConversationResource(llm_provider="anthropic")

    history = [
        {"role": "user", "content": "Our centrifuge is experiencing vibration at 3000 RPM"},
        {"role": "assistant", "content": "Have you checked the balance weights?"},
        {"role": "user", "content": "Yes, and the bearing temperature is elevated to 85°C"},
    ]

    new_message = "Could this be related to the recent maintenance?"

    # Use all three methods
    print("\n📊 Method 1: Summarize conversation")
    summary = await conversation.summarize(conversation_history=history)
    print(f"   Topics: {summary['key_topics']}")
    print(f"   Stage: {summary['conversation_stage']}")

    print("\n🎯 Method 2: Detect intent of new message")
    intent = await conversation.detect_intent(message=new_message, conversation_history=history)
    print(f"   Intent: {intent['intent']}")
    print(f"   Rewritten: {intent['rewritten_message']}")

    print("\n🔍 Method 3: Extract topics from new message")
    topics = await conversation.extract_topics(message=new_message, conversation_history=history)
    print(f"   Focus: {topics['current_focus']}")
    print(f"   Topics: {topics['active_topics']}")


async def example_custom_intent_types():
    """Example: Configuring custom intent types for domain-specific routing"""
    print("\n" + "=" * 70)
    print("Example 2: Custom Intent Types for Support Tickets")
    print("=" * 70)

    # Create resource with custom intent types
    conversation = ConversationResource(llm_provider="anthropic", intent_types=["bug_report", "feature_request", "question", "feedback"])

    messages = ["The login button doesn't work on mobile", "Can you add dark mode?", "How do I reset my password?", "The new UI is great!"]

    for msg in messages:
        result = await conversation.detect_intent(message=msg)
        print(f"   Message: '{msg[:50]}'")
        print(f"   → Intent: {result['intent']}\n")


async def example_interview_scenario():
    """Example: Expert interview with all methods"""
    print("\n" + "=" * 70)
    print("Example 3: Expert Interview - Comprehensive Analysis")
    print("=" * 70)

    conversation = ConversationResource(llm_provider="anthropic")

    history = [
        {"role": "assistant", "content": "Can you describe your experience with crystallization?"},
        {
            "role": "user",
            "content": "I've been working with crystallizers for 15 years. The key is maintaining supersaturation within the metastable zone.",
        },
        {"role": "assistant", "content": "What are the main challenges?"},
        {"role": "user", "content": "Temperature control is critical. We use a PID controller with cascade loops."},
    ]

    new_message = "Seasonal variations affect cooling water temperature, so we adjust setpoints"

    # Extract topics with terminology preservation
    print("\n🔬 Extracting topics (preserving exact terminology)")
    topics = await conversation.extract_topics(message=new_message, conversation_history=history, preserve_terminology=True)
    print(f"   Focus: {topics['current_focus']}")
    print(f"   Terminology preserved: {topics['terminology']}")

    # Get conversation summary
    print("\n📝 Summarizing interview progress")
    summary = await conversation.summarize(conversation_history=history, current_message=new_message)
    print(f"   Expert insights: {summary['expert_insights']}")
    print(f"   Expertise level: {summary['expertise_level']}")
    print(f"   Summary: {summary['conversation_summary']}")


async def example_customer_support():
    """Example: Customer support with intent routing"""
    print("\n" + "=" * 70)
    print("Example 4: Customer Support - Intent-Based Routing")
    print("=" * 70)

    conversation = ConversationResource(
        llm_provider="anthropic", intent_types=["account_issue", "technical_problem", "billing_question", "general_inquiry"]
    )

    history = [
        {"role": "user", "content": "I can't log into my account"},
        {"role": "assistant", "content": "Let me help you with that. Have you tried resetting your password?"},
    ]

    new_message = "I'm also being charged twice this month"

    # Detect context switch
    print("\n🔄 Detecting intent and context switches")
    intent = await conversation.detect_intent(message=new_message, conversation_history=history)
    print(f"   Intent: {intent['intent']}")
    print(f"   Context switch detected: {intent.get('context_switch_detected', False)}")
    print(f"   Keywords: {intent.get('search_keywords', [])}")

    # Update history and summarize
    history.append({"role": "user", "content": new_message})
    summary = await conversation.summarize(conversation_history=history)
    print("\n📊 Session summary:")
    print(f"   Topics covered: {summary['key_topics']}")
    print(f"   Context switches: {summary.get('context_switches', [])}")


async def example_minimal_conversation():
    """Example: Fast path for minimal conversations"""
    print("\n" + "=" * 70)
    print("Example 5: Minimal Conversation (Fast Path - No LLM)")
    print("=" * 70)

    conversation = ConversationResource(llm_provider="anthropic")

    # Very short conversation triggers fast path
    history = [{"role": "user", "content": "Hello!"}]

    summary = await conversation.summarize(conversation_history=history)
    print(f"   Stage: {summary['conversation_stage']}")
    print(f"   Processing time: {summary['processing_time']:.6f}s (no LLM call)")
    print("   ✨ Fast path automatically used for short conversations")


async def example_terminology_preservation():
    """Example: Exact terminology preservation in topic extraction"""
    print("\n" + "=" * 70)
    print("Example 6: Terminology Preservation")
    print("=" * 70)

    conversation = ConversationResource(llm_provider="anthropic")

    technical_message = """Our HPLC system shows retention time drift.
    The C18 column efficiency dropped from 10,000 to 7,500 theoretical plates.
    We're running a gradient elution with ACN/water mobile phase."""

    print("\n🔬 Extracting with terminology preservation")
    topics = await conversation.extract_topics(message=technical_message, preserve_terminology=True)

    print(f"   Technical terms preserved: {topics['terminology']}")
    print("   ✨ Exact acronyms and terms retained (HPLC, C18, ACN)")


async def main():
    """Run all examples"""
    print("\n🚀 ConversationResource Examples")
    print("=" * 70)
    print("Unified resource for: summarize, detect_intent, extract_topics")

    await example_unified_resource_basic()
    await example_custom_intent_types()
    await example_interview_scenario()
    await example_customer_support()
    await example_minimal_conversation()
    await example_terminology_preservation()

    print("\n" + "=" * 70)
    print("✅ All examples completed!")
    print("=" * 70)
    print("\n💡 Key Takeaway: One resource, three powerful methods!")
    print("   - Create once: conversation = ConversationResource()")
    print("   - Use anywhere: summarize(), detect_intent(), extract_topics()")


if __name__ == "__main__":
    asyncio.run(main())
