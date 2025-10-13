# Template Fine-tuning Handler

A conversational handler for refining interview templates through natural language interactions.

## Simplified Toolset (5 Tools)

1. **ViewTemplateTool**: Display template sections
   - View entire template or specific topics/sections
   
2. **RefineTopicQuestionsTool**: Modify opening questions for existing topics
   - Add, remove, or refine questions with LLM assistance
   - Note: Topics are fixed by knowledge pack structure
   
3. **GenerateAdditionalQuestionsTool**: Generate new questions from knowledge summaries
   - Uses knowledge.json summaries to create relevant questions
   
4. **UpdateInterviewApproachTool**: Modify interview metadata
   - Update goal, style, duration, topics covered
   
5. **UpdateFrameworkTool**: Manage relationship prompts and follow-up questions
   - Add, remove, or replace items in framework sections

## Quick Start

### Test Individual Tools

Each tool has a `__main__` section for testing:

```bash
cd dana/api/services/knowledge_pack/template_handler/tools

# Test viewing templates
python view_template_tool.py

# Test refining questions
python refine_topic_questions_tool.py

# Test generating additional questions
python generate_additional_questions_tool.py

# Test updating approach
python update_interview_approach_tool.py

# Test updating framework
python update_framework_tool.py
```

### Test All Tools

Run the comprehensive test suite:

```bash
cd dana/api/services/knowledge_pack/template_handler
python test_all_tools.py
```

## Handler Usage

```python
from dana.lang.api.services.knowledge_pack.template_handler import TemplateFinetuneHandler

# Initialize handler
handler = TemplateFinetuneHandler(
    template_path="/path/to/master_interview_template.md",
    knowledge_pack_path="/path/to/knowledge_pack",
    domain="Food Manufacturing",
    role="Process Operator",
)

# Process refinement request
request = IntentDetectionRequest(
    user_message="Add questions about digital transformation to LOTO topic",
    chat_history=[],
)

result = await handler.handle(request)
```

## Key Features

- **Conversational Interface**: Natural language refinement requests
- **Preview & Approval**: All changes show previews requiring user approval
- **LLM Integration**: Intelligent question generation and refinement
- **Template Operations**: View, modify questions, update framework sections
- **Error Handling**: Graceful error recovery and user feedback

## Key Constraints

- **Topics are Fixed**: Topics map 1:1 to knowledge.json files and cannot be added, removed, or reordered
- **Question Refinement Only**: You can only modify questions for existing topics
- **Framework Flexibility**: Relationship prompts and follow-up questions can be freely modified

## File Structure

```
template_handler/
├── __init__.py
├── template_finetune_handler.py    # Main handler
├── utils.py                        # Template parsing utilities
├── prompts.py                      # System prompts
├── test_all_tools.py              # Comprehensive test suite
├── README.md                       # This file
└── tools/
    ├── __init__.py
    ├── view_template_tool.py
    ├── refine_topic_questions_tool.py
    ├── generate_additional_questions_tool.py
    ├── update_interview_approach_tool.py
    └── update_framework_tool.py
```

## Testing

Each tool includes a `__main__` section for individual testing. The test suite demonstrates:

1. **Template Viewing**: Display sections and topics
2. **Question Refinement**: Add/modify questions with LLM
3. **Question Generation**: Create new questions from knowledge summaries
4. **Approach Updates**: Modify interview metadata
5. **Framework Updates**: Manage relationship prompts and follow-up questions

All tools show previews and require user approval for changes, ensuring safe template modification.
