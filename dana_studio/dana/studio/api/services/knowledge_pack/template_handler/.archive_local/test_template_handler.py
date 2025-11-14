"""
Simple test to verify TemplateFinetuneHandler implementation.
"""

import asyncio
import tempfile
import os
from dana.studio.api.core.schemas import IntentDetectionRequest
from template_finetune_handler import TemplateFinetuneHandler


def create_test_template():
    """Create a test template file."""
    template_content = """# Master Interview Template: Test Domain

## Interview Approach
- **Goal**: Capture expert knowledge
- **Style**: Conversational
- **Duration**: 60 minutes
- **Topics Covered**: 2 topics

---

## Topic Opening Questions

### Safety Procedures
**Background**: Focuses on safety protocols and procedures
**Opening Questions**:
1. How do you approach safety in your daily work?
2. What safety procedures are most important?

---

### Quality Control
**Background**: Covers quality assurance processes
**Opening Questions**:
1. How do you ensure quality in your processes?
2. What quality metrics do you track?

---

## Relationship Exploration Prompts
- When expert mentions safety, explore connection to quality
- If they discuss processes, ask about documentation

## Follow-up Framework
- "Can you tell me more about that?"
- "What's an example of when that happened?"
"""

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    temp_file.write(template_content)
    temp_file.close()

    return temp_file.name


async def test_view_template():
    """Test ViewTemplateTool."""
    print("🧪 Testing ViewTemplateTool...")

    # Create test template
    template_path = create_test_template()
    knowledge_pack_path = "/tmp/test_kp"

    try:
        # Create handler
        handler = TemplateFinetuneHandler(
            template_path=template_path,
            knowledge_pack_path=knowledge_pack_path,
            kp_id=1,
            domain="Test Domain",
            role="Test Expert",
        )

        # Test viewing all sections
        request = IntentDetectionRequest(user_message="Show me the current template", chat_history=[], current_domain_tree=None, agent_id=1)

        result = await handler.handle(request)
        print(f"✅ View template test passed: {result['status']}")

    except Exception as e:
        print(f"❌ View template test failed: {e}")
    finally:
        # Cleanup
        os.unlink(template_path)


async def test_refine_questions():
    """Test RefineTopicQuestionsTool."""
    print("🧪 Testing RefineTopicQuestionsTool...")

    # Create test template
    template_path = create_test_template()
    knowledge_pack_path = "/tmp/test_kp"

    try:
        # Create handler
        handler = TemplateFinetuneHandler(
            template_path=template_path,
            knowledge_pack_path=knowledge_pack_path,
            kp_id=1,
            domain="Test Domain",
            role="Test Expert",
        )

        # Test refining questions
        request = IntentDetectionRequest(
            user_message="Add questions about digital tools to the Safety Procedures topic",
            chat_history=[],
            current_domain_tree=None,
            agent_id=1,
        )

        result = await handler.handle(request)
        print(f"✅ Refine questions test passed: {result['status']}")

    except Exception as e:
        print(f"❌ Refine questions test failed: {e}")
    finally:
        # Cleanup
        os.unlink(template_path)


async def test_handler_initialization():
    """Test handler initialization and tool loading."""
    print("🧪 Testing handler initialization...")

    # Create test template
    template_path = create_test_template()
    knowledge_pack_path = "/tmp/test_kp"

    try:
        # Create handler
        handler = TemplateFinetuneHandler(
            template_path=template_path,
            knowledge_pack_path=knowledge_pack_path,
            kp_id=1,
            domain="Test Domain",
            role="Test Expert",
        )

        # Check tools are loaded
        expected_tools = [
            "ask_question",
            "attempt_completion",
            "view_template",
            "read_documents",
            "refine_topic_questions",
            "generate_additional_questions",
            "update_interview_approach",
            "replace_in_template",
        ]

        for tool_name in expected_tools:
            if tool_name not in handler.tools:
                raise Exception(f"Tool {tool_name} not found in handler")

        print(f"✅ Handler initialization test passed: {len(handler.tools)} tools loaded")

    except Exception as e:
        print(f"❌ Handler initialization test failed: {e}")
    finally:
        # Cleanup
        os.unlink(template_path)


async def main():
    """Run all tests."""
    print("🚀 Starting TemplateFinetuneHandler Tests")
    print("=" * 50)

    await test_handler_initialization()
    await test_view_template()
    await test_refine_questions()

    print("=" * 50)
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
