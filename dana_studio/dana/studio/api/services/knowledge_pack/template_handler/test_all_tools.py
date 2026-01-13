#!/usr/bin/env python3
"""
Simple test runner for all template fine-tuning tools.
Run this to see what each tool does.
"""

import asyncio
import tempfile
import os

# Test template
TEST_TEMPLATE = """# Master Interview Template: Food Manufacturing - Process Operator

## Interview Approach
- **Goal**: Capture expert knowledge about process operations
- **Style**: Conversational and open-ended
- **Duration**: 60-90 minutes
- **Topics Covered**: Safety, Quality, Equipment, Training

---

## Topic Opening Questions

### Lockout/Tagout (LOTO) Procedures
**Background**: Focuses on safety protocols for equipment isolation
**Opening Questions**:
1. How do you approach LOTO procedures in your daily work?
2. What are the most critical LOTO steps you follow?
3. How do you verify equipment is properly isolated?

---

### Quality Control Processes
**Background**: Covers quality assurance and inspection procedures
**Opening Questions**:
1. How do you ensure product quality in your processes?
2. What quality metrics do you track regularly?
3. How do you handle quality deviations?

---

### Equipment Operation
**Background**: Focuses on machinery operation and maintenance
**Opening Questions**:
1. How do you operate your main equipment?
2. What maintenance procedures do you follow?
3. How do you troubleshoot equipment issues?

---

## Relationship Exploration Prompts
1. When expert mentions safety, explore connection to quality processes
2. If they discuss equipment, ask about maintenance and safety procedures
3. When they talk about training, explore connections to safety and quality

## Follow-up Framework
1. Can you tell me more about that specific situation?
2. What's an example of when that happened?
3. How do you typically handle that?
4. What would you do differently next time?
"""


async def test_tool(tool_name, tool_class, test_func):
    """Test a single tool and display results."""
    print(f"\n{'=' * 60}")
    print(f"🧪 Testing {tool_name}")
    print(f"{'=' * 60}")

    try:
        await test_func()
        print(f"✅ {tool_name} test completed successfully!")
    except Exception as e:
        print(f"❌ {tool_name} test failed: {e}")
        import traceback

        traceback.print_exc()


async def test_view_template():
    """Test ViewTemplateTool."""
    from tools.view_template_tool import ViewTemplateTool

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(TEST_TEMPLATE)
        temp_path = f.name

    try:
        tool = ViewTemplateTool()

        # Test viewing all sections
        result = await tool._execute(section="all", template_path=temp_path)
        print("📄 Full Template (first 300 chars):")
        print(result.result[:300] + "..." if len(result.result) > 300 else result.result)
        print()

        # Test viewing specific topic
        result = await tool._execute(section="topic:Lockout/Tagout (LOTO) Procedures", template_path=temp_path)
        print("🎯 LOTO Topic:")
        print(result.result)

    finally:
        os.unlink(temp_path)


async def test_refine_questions():
    """Test RefineTopicQuestionsTool."""
    from tools.refine_topic_questions_tool import RefineTopicQuestionsTool

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(TEST_TEMPLATE)
        temp_path = f.name

    try:
        tool = RefineTopicQuestionsTool()

        # Test refining questions
        result = await tool._execute(
            topic_name="Lockout/Tagout (LOTO) Procedures",
            refinement_instruction="Add questions about digital LOTO systems and automation",
            preserve_existing=True,
            template_path=temp_path,
            domain="Food Manufacturing",
            role="Process Operator",
        )

        print("📝 Refined Questions Preview:")
        print(result.result)

    finally:
        os.unlink(temp_path)


async def test_update_approach():
    """Test UpdateInterviewApproachTool."""
    from tools.update_interview_approach_tool import UpdateInterviewApproachTool

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(TEST_TEMPLATE)
        temp_path = f.name

    try:
        tool = UpdateInterviewApproachTool()

        # Test updating duration
        result = await tool._execute(
            field="duration", new_value="90-120 minutes total, with breaks every 30 minutes", template_path=temp_path
        )

        print("⏱️ Duration Update Preview:")
        print(result.result)

    finally:
        os.unlink(temp_path)


async def test_update_framework():
    """Test UpdateFrameworkTool."""
    from tools.update_framework_tool import UpdateFrameworkTool

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(TEST_TEMPLATE)
        temp_path = f.name

    try:
        tool = UpdateFrameworkTool(template_path=temp_path)

        # Test adding relationship prompt
        result = await tool._execute(
            section="relationships", action="add", content="When expert discusses automation, ask about safety implications"
        )
        print("🔗 Add Relationship Prompt:")
        print(result.result)
        print()

        # Test adding follow-up question
        result = await tool._execute(section="followup", action="add", content="What would you do differently next time?")
        print("❓ Add Follow-up Question:")
        print(result.result)

    finally:
        os.unlink(temp_path)


async def main():
    """Run all tool tests."""
    print("🚀 Template Fine-tuning Tools Test Suite (Simplified)")
    print("=" * 60)
    print("This will test each tool to show you what it does.")
    print("Each tool shows a preview requiring user approval.")
    print("=" * 60)

    # Test each tool
    await test_tool("ViewTemplateTool", None, test_view_template)
    await test_tool("RefineTopicQuestionsTool", None, test_refine_questions)
    await test_tool("UpdateInterviewApproachTool", None, test_update_approach)
    await test_tool("UpdateFrameworkTool", None, test_update_framework)

    print(f"\n{'=' * 60}")
    print("✅ All tool tests completed!")
    print("💡 Each tool shows previews and requires user approval for changes.")
    print("🔧 Toolset reduced from 10 to 5 tools (50% simpler)")
    print("📝 Use these tools in the TemplateFinetuneHandler for conversational template refinement.")


if __name__ == "__main__":
    asyncio.run(main())
