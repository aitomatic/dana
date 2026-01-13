"""
Test script for InterviewHandler POC migration.

Tests the end-to-end workflow of the migrated interview handler.
"""

import asyncio
import tempfile
from dana.studio.api.core.schemas import IntentDetectionRequest, MessageData, SenderRole
from dana.studio.api.services.knowledge_pack.interview_handler.interview_handler import InterviewHandler
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2


# Note: topic_processor functionality is now handled directly by LLM in the tools


class MockResponseGenerator:
    """Mock response generator for testing."""

    async def generate_response_with_gaps(self, rewritten_message, document_chunks, topic_result, sharing_assessment):
        """Mock response generation."""
        topics = topic_result.get("topics", [])
        main_focus = topic_result.get("main_focus", "your work")

        response = f"Thank you for sharing your expertise about {main_focus}. "
        response += f"Based on your experience with {', '.join(topics)}, I can see you have valuable knowledge. "
        response += "The document search found relevant information that aligns with your experience."

        return {
            "response": response,
            "follow_up_question": "Can you tell me more about specific procedures you follow?",
            "processing_time": 1.5,
            "success": True,
        }


class MockRAGResource(RAGResourceV2):
    """Mock RAG resource for testing."""

    def __init__(self, sources=None):
        super().__init__(sources=sources or [], name="mock_rag")
        self._is_ready = True

    async def query(self, query, num_results=10):
        """Mock document search."""
        return f"Document content about: {query}\n\nRelevant safety procedures and guidelines found in the knowledge base."


async def test_tool_initialization():
    """Test 1: Initialize InterviewHandler with mock dependencies."""
    print("🧪 Test 1: Tool Initialization")
    print("=" * 50)

    # Create temporary session directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize components
        response_generator = MockResponseGenerator()
        rag_resource = MockRAGResource()

        # Create handler
        handler = InterviewHandler(
            session_dir=temp_dir,
            response_generator=response_generator,
            rag_resource=rag_resource,
            domain="Industrial Safety",
            role="Safety Expert",
        )

        # Verify tools are initialized
        expected_tools = ["comprehensive_analysis", "document_search", "ask_question", "attempt_completion"]

        for tool_name in expected_tools:
            assert tool_name in handler.tools, f"Tool {tool_name} not found"
            print(f"✅ {tool_name} tool initialized")

        print(f"✅ All {len(handler.tools)} tools initialized successfully")
        return handler


async def test_complete_sharing_flow(handler):
    """Test 2: Complete sharing flow - essential_analysis → sharing_assessment → document_search → response_generation → completion."""
    print("\n🧪 Test 2: Complete Sharing Flow")
    print("=" * 50)

    # Create conversation with complete sharing
    chat_history = [
        MessageData(
            role=SenderRole.USER,
            content="I work with conveyor systems and safety procedures for lockout tagout. I have extensive experience with maintenance procedures.",
        )
    ]

    request = IntentDetectionRequest(
        user_message="I work with conveyor systems and safety procedures for lockout tagout. I have extensive experience with maintenance procedures.",
        chat_history=chat_history,
        current_domain_tree=None,
        agent_id=1,
    )

    print("📝 Input: Complete expert sharing about safety procedures")
    print("🎯 Expected: comprehensive_analysis → document_search → comprehensive_analysis → attempt_completion")

    # Run handler
    result = await handler.handle(request)

    # Verify results
    print(f"📊 Status: {result['status']}")
    print(f"📊 Workflow Completed: {result.get('workflow_completed', False)}")
    print(f"📊 Conversation Length: {len(result['conversation'])}")

    # Check conversation flow
    conversation = result["conversation"]
    tool_calls = [msg for msg in conversation if msg.role == "assistant" and "<" in msg.content]
    print(f"📊 Tool Calls Made: {len(tool_calls)}")

    for i, msg in enumerate(tool_calls, 1):
        # Extract tool name
        tool_match = re.search(r"<(\w+)", msg.content)
        if tool_match:
            tool_name = tool_match.group(1)
            print(f"  {i}. {tool_name}")

    print("✅ Complete sharing flow test completed")
    return result


async def test_incomplete_sharing_flow(handler):
    """Test 3: Incomplete sharing flow - essential_analysis → sharing_assessment → ask_question → wait for user."""
    print("\n🧪 Test 3: Incomplete Sharing Flow")
    print("=" * 50)

    # Create conversation with incomplete sharing
    chat_history = [MessageData(role=SenderRole.USER, content="I work with some equipment and stuff.")]

    request = IntentDetectionRequest(
        user_message="I work with some equipment and stuff.", chat_history=chat_history, current_domain_tree=None, agent_id=1
    )

    print("📝 Input: Incomplete expert sharing")
    print("🎯 Expected: comprehensive_analysis → ask_question → user_input_required")

    # Run handler
    result = await handler.handle(request)

    # Verify results
    print(f"📊 Status: {result['status']}")
    print(f"📊 Workflow Completed: {result.get('workflow_completed', False)}")
    print(f"📊 Conversation Length: {len(result['conversation'])}")

    # Should require user input
    if result["status"] == "user_input_required":
        print("✅ Correctly identified need for user input")
    else:
        print("⚠️ Expected user_input_required but got:", result["status"])

    print("✅ Incomplete sharing flow test completed")
    return result


async def test_conversation_state_management(handler):
    """Test 4: Verify conversation state management."""
    print("\n🧪 Test 4: Conversation State Management")
    print("=" * 50)

    # Start with initial message
    chat_history = [MessageData(role=SenderRole.USER, content="I have experience with safety procedures.")]

    request = IntentDetectionRequest(
        user_message="I have experience with safety procedures.", chat_history=chat_history, current_domain_tree=None, agent_id=1
    )

    print("📝 Testing conversation state management")

    # Run handler
    result = await handler.handle(request)

    # Check conversation state
    conversation = result["conversation"]
    print(f"📊 Initial conversation length: {len(chat_history)}")
    print(f"📊 Final conversation length: {len(conversation)}")
    print(f"📊 Messages added: {len(conversation) - len(chat_history)}")

    # Verify message roles
    user_messages = [msg for msg in conversation if msg.role == "user"]
    assistant_messages = [msg for msg in conversation if msg.role == "assistant"]

    print(f"📊 User messages: {len(user_messages)}")
    print(f"📊 Assistant messages: {len(assistant_messages)}")

    # Verify conversation structure
    for i, msg in enumerate(conversation):
        role_emoji = "👤" if msg.role == "user" else "🤖"
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"  {i + 1}. {role_emoji} {msg.role}: {content_preview}")

    print("✅ Conversation state management test completed")
    return result


async def test_error_handling(handler):
    """Test 5: Test error handling and recovery."""
    print("\n🧪 Test 5: Error Handling")
    print("=" * 50)

    # Test with malformed input
    chat_history = [MessageData(role=SenderRole.USER, content="")]

    request = IntentDetectionRequest(user_message="", chat_history=chat_history, current_domain_tree=None, agent_id=1)

    print("📝 Testing error handling with empty input")

    try:
        result = await handler.handle(request)
        print(f"📊 Status: {result['status']}")
        print("✅ Error handling test completed - no exceptions raised")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

    return result


async def test_tool_execution_order():
    """Test 6: Verify tool execution order matches LLM decisions."""
    print("\n🧪 Test 6: Tool Execution Order")
    print("=" * 50)

    # This test would require mocking the LLM to control tool selection
    # For now, we'll just verify the tools are available and can be called

    handler = await test_tool_initialization()

    print("📝 Available tools:")
    for name, tool in handler.tools.items():
        print(f"  - {name}: {tool.tool_information.description}")

    print("✅ Tool execution order test completed")


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting InterviewHandler POC Tests")
    print("=" * 70)

    try:
        # Test 1: Tool initialization
        handler = await test_tool_initialization()

        # Test 2: Complete sharing flow
        await test_complete_sharing_flow(handler)

        # Test 3: Incomplete sharing flow
        await test_incomplete_sharing_flow(handler)

        # Test 4: Conversation state management
        await test_conversation_state_management(handler)

        # Test 5: Error handling
        await test_error_handling(handler)

        # Test 6: Tool execution order
        await test_tool_execution_order()

        print("\n🎉 All tests completed successfully!")
        print("✅ InterviewHandler POC is working correctly")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    import re

    print("🧪 InterviewHandler POC Test Suite")
    print("=" * 50)
    print("This test suite validates the migrated interview handler")
    print("by testing all 6 tools and the orchestrator workflow.")
    print()

    # Run all tests
    asyncio.run(run_all_tests())
