# Template Fine-tuning Handler

A conversational handler for refining interview templates through natural language interactions.

## Toolset (8 Tools)

**Core Workflow Tools:**
1. **AskQuestionTool**: Ask clarifying questions or get user approval
2. **AttemptCompletionTool**: Signal workflow completion

**Template Operations:**
3. **ViewTemplateTool**: Display template sections
   - View entire template or specific topics/sections
   
4. **ReadDocumentsTool**: Browse and read documents in the knowledge pack
   - Lists all documents with IDs, names, sizes, types (when no document_id provided)
   - Reads and previews specific document content using RAG (when document_id provided)
   - Use for: Discovering documents AND understanding their content
   
5. **RefineTopicQuestionsTool**: Modify opening questions for existing topics
   - Add, remove, or refine questions with LLM assistance
   - Note: Topics are fixed by knowledge pack structure
   
6. **GenerateAdditionalQuestionsTool**: Generate new questions from knowledge summaries or specific documents
   - Uses knowledge.json summaries to create relevant questions
   - Integrates RAG context from knowledge pack and documents
   - Optional: Generate questions from specific documents by providing document_ids
   
7. **UpdateInterviewApproachTool**: Modify interview metadata
   - Update goal, style, duration, topics covered
   
8. **ReplaceInFileTool**: Advanced search/replace editing
   - Supports exact text matching and regex patterns
   - Use for: modifying framework sections, bulk operations, pattern transformations

## Quick Start

### Test Individual Tools

Each tool has a `__main__` section for testing:

```bash
cd dana/api/services/knowledge_pack/template_handler/tools

# Test viewing templates
python view_template_tool.py

# Test listing/reading documents
python read_documents_tool.py

# Test refining questions
python refine_topic_questions_tool.py

# Test generating additional questions
python generate_additional_questions_tool.py

# Test updating approach
python update_interview_approach_tool.py

# Test advanced editing
python replace_in_file_tool.py
```

### Test All Tools

Run the comprehensive test suite:

```bash
cd dana/api/services/knowledge_pack/template_handler
python test_all_tools.py
```

## Handler Usage

```python
from dana.studio.api.services.knowledge_pack.template_handler import TemplateFinetuneHandler

# Initialize handler
handler = TemplateFinetuneHandler(
    template_path="path/to/template.md",
    knowledge_pack_path="path/to/knowledge_pack",
    kp_id=8,  # Knowledge pack ID
    doc_paths=None,  # Optional document paths
    domain="Manufacturing",
    role="Process Operator"
)

# Example: Generate questions from specific documents
user_message = "Generate 5 questions about safety procedures from document 45"
# Agent will:
# 1. Use list_documents to show available documents
# 2. Use generate_additional_questions with document_ids=[45]
# 3. Present questions for approval
```

## Document Reading and Question Generation

The handler now supports reading documents and generating questions based on specific documents:

1. **List Documents**: Use `read_documents` (no parameters) to browse available documents
2. **Read Document Content**: Use `read_documents` with `document_id` to preview document content via RAG
3. **Document-Specific Questions**: Use `generate_additional_questions` with `document_ids` parameter
4. **Important**: Document reading is standalone - agent won't auto-generate questions unless explicitly requested

Example workflows:
```python
# Workflow 1: List documents only
# User: "What documents are in this knowledge pack?"
# Agent uses: read_documents (no parameters)
# Result: Shows document list, STOPS and waits for next instruction

# Workflow 2: Read document content
# User: "What's in the safety manual?"
# Agent uses: read_documents(document_id=45)
# Result: Shows document overview/preview, STOPS and waits for next instruction

# Workflow 3: Generate questions from documents
# User: "Generate questions from the safety manual"
# Agent uses: read_documents to find ID, THEN generate_additional_questions(topic_name="Safety", document_ids=[45])
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
- **Question Refinement Only**: You can only modify questions within existing topics
- **Framework Flexibility**: Relationship prompts and follow-up questions can be freely modified using ReplaceInFileTool

## Framework Section Editing

Since there's no dedicated framework tool, use `ReplaceInFileTool` for framework edits:

```python
# Add relationship prompt
tool = ReplaceInFileTool(template_path="...")
result = await tool._execute(
    diff="""------- SEARCH
- If automation is discussed, ask about impact on production flow
=======
- If automation is discussed, ask about impact on production flow
- When expert mentions safety, explore connections to quality outcomes
++++++ REPLACE
""",
    mode="text"
)

# Bulk operation with regex
result = await tool._execute(
    diff=r"""------- SEARCH
(\d+)\. ([^\n]+)
=======
Question \1: \2
++++++ REPLACE
""",
    mode="regex"
)
```

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
    ├── ask_question_tool.py
    ├── attempt_completion_tool.py
    ├── view_template_tool.py
    ├── refine_topic_questions_tool.py
    ├── generate_additional_questions_tool.py
    ├── update_interview_approach_tool.py
    └── replace_in_file_tool.py
```

## Testing

Each tool includes a `__main__` section for individual testing. The test suite demonstrates:

1. **Template Viewing**: Display sections and topics
2. **Question Refinement**: Add/modify questions with LLM assistance
3. **Question Generation**: Create new questions from knowledge summaries with RAG context
4. **Approach Updates**: Modify interview metadata (goal, style, duration)
5. **Advanced Editing**: Use search/replace for framework sections and bulk operations

Tools that modify content (refine_topic_questions, generate_additional_questions, update_interview_approach) automatically show previews and require user approval for changes, ensuring safe template modification.

## Troubleshooting

### Template Corruption from Malformed Diffs

If you see diff markers (`------- SEARCH`, `=======`, `++++++ REPLACE`) in your template:

**Cause:** A malformed diff was somehow written to the template file

**Fix:**
1. Use `view_template` with `section='all'` to see the full template
2. Manually edit the template file to remove the markers
3. Or restore from backup (`.bak` file created automatically)

**Prevention:** The system now validates diff format and prevents this issue. If you encounter errors about "diff markers in wrong order" or "No valid search/replace blocks found", the system is correctly catching malformed diffs before they corrupt your template.
