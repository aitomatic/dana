# Document Exploration Handler

A conversational handler for exploring and analyzing documents within knowledge packs through natural language interactions.

## Overview

The Document Exploration Handler enables users to:
- Browse and discover documents in a knowledge pack
- Read and understand document content using RAG (Retrieval-Augmented Generation)
- Ask questions about documents and get contextual answers
- Identify opportunities to refine interview questions based on document insights
- Extract tacit operational knowledge and site-specific details

## Toolset (3 Tools)

**Core Workflow Tools:**
1. **ReadDocumentsTool**: Browse and read documents in the knowledge pack
   - **List Mode** (no document_id): Lists all documents with IDs, names, sizes, types
   - **Read Mode** (with document_id): Reads and previews specific document content using RAG
   - Use for: Discovering documents AND understanding their content

2. **AskQuestionTool**: Ask clarifying questions or get user approval
   - Used when agent needs more information from user
   - Used to confirm understanding before proceeding
   - Provides context and decision logic to help users respond

3. **AttemptCompletionTool**: Signal workflow completion
   - Present findings to the user
   - Answer user questions about documents
   - Summarize insights discovered

## Architecture

### Handler Class: `DocumentExplorationHandler`

Stateless handler that uses conversation history as state, following the same pattern as `TemplateFinetuneHandler`:
- LLM-orchestrated tool loop (max 15 iterations)
- Async tool execution with error handling
- Support for user input interruption
- RAG integration for document content retrieval

### Key Components

**Constructor Parameters:**
```python
DocumentExplorationHandler(
    kp_id: int,                    # Knowledge pack ID (required)
    doc_paths: list[str] | None,   # Optional document file paths for RAG
    llm: LLMResource | None,       # LLM instance (defaults to LegacyLLMResource)
    domain: str,                   # Domain context (e.g., "Manufacturing")
    role: str,                     # Role context (e.g., "Process Operator")
    notifier: Callable | None,     # Progress notification callback
)
```

**Return Value from `handle()`:**
```python
{
    "status": "success" | "user_input_required",
    "message": "...",              # Final message or question to user
    "conversation": [...],         # Full conversation history
}
```

## Quick Start

### Basic Usage

```python
from dana.studio.api.services.knowledge_pack.document_handler import DocumentExplorationHandler

# Initialize handler
handler = DocumentExplorationHandler(
    kp_id=8,
    doc_paths=[
        "/path/to/document1.pdf",
        "/path/to/document2.pdf",
    ],
    domain="Food Manufacturing",
    role="Process Operator"
)

# Set database session (injected by API route)
handler.db = db_session

# Process user request
request = IntentDetectionRequest(
    user_message="What documents are available in this knowledge pack?",
    chat_history=[],
)

result = await handler.handle(request)
```

### Example Workflows

#### Workflow 1: List Documents
```python
# User: "What documents are in this knowledge pack?"
# Agent uses: read_documents (no parameters)
# Result: Shows document list with IDs, names, sizes, types
# Status: Waits for next instruction
```

#### Workflow 2: Read Document Content
```python
# User: "What's in the safety manual?"
# Agent uses: 
#   1. read_documents (to find document ID)
#   2. read_documents(document_id=45) (to preview content)
# Result: Shows document overview and key content via RAG
# Status: Waits for next instruction
```

#### Workflow 3: Document Q&A
```python
# User: "What safety procedures are mentioned in document 45?"
# Agent uses: read_documents(document_id=45)
# Result: RAG retrieves relevant content about safety procedures
# Status: Answers question and waits for follow-up
```

#### Workflow 4: Knowledge Elicitation
```python
# User: "Help me understand the LOTO procedures in these documents"
# Agent uses:
#   1. read_documents (list documents)
#   2. read_documents(document_id=X) for relevant docs
#   3. ask_question (to clarify specific aspects)
#   4. attempt_completion (summarize findings)
# Result: Comprehensive understanding of LOTO procedures
```

## Integration

### Database Session

The handler requires a database session to access document metadata:

```python
# In your API route
handler = DocumentExplorationHandler(kp_id=kp_id, ...)
handler.db = db  # Inject database session
result = await handler.handle(request)
```

### RAG Configuration

RAG is initialized lazily on first use:
- Provide `doc_paths` during handler initialization
- RAG initializes automatically when `handle()` is called
- RAG provides document content for `ReadDocumentsTool`

### Progress Notifications

Optionally provide a notifier callback to track progress:

```python
async def notify(tool_name: str, content: str, status: str, progress: float | None):
    print(f"[{status}] {tool_name}: {content[:50]}...")

handler = DocumentExplorationHandler(
    kp_id=8,
    notifier=notify,
    ...
)
```

## Testing

### Interactive Testing

Run the handler directly for interactive testing:

```bash
cd dana/studio/api/services/knowledge_pack/document_handler
python document_exploration_handler.py
```

Commands:
- Type any document exploration request to test the workflow
- Type 'quit' or 'exit' to quit
- Type 'reset' to clear conversation history
- Type 'history' to view conversation
- Type 'tools' to list available tools

### Example Test Session

```
💬 User: What documents are available?
📊 Status: user_input_required
📄 Result: Lists all documents with metadata

💬 User: Read document 45
📊 Status: user_input_required  
📄 Result: Shows document preview with RAG content

💬 User: What safety procedures are mentioned?
📊 Status: success
📄 Result: Answers based on RAG retrieval
```

## Key Features

- **Conversational Interface**: Natural language document exploration
- **RAG-Powered Content**: Intelligent document content retrieval and understanding
- **Knowledge Elicitation Focus**: Designed to extract tacit knowledge and insights
- **Stateless Design**: All state managed through conversation history
- **Error Handling**: Graceful error recovery and user feedback
- **Interactive Workflow**: Supports back-and-forth dialogue with users

## Comparison with Template Handler

| Aspect | TemplateFinetuneHandler | DocumentExplorationHandler |
|--------|-------------------------|---------------------------|
| **Purpose** | Template modification | Document exploration & Q&A |
| **File Modification** | Yes (template updates) | No (read-only) |
| **Number of Tools** | 8 tools | 3 tools |
| **RAG Resources** | 2 (knows + docs) | 1 (docs only) |
| **Template Path** | Required | Not needed |
| **Workflow Outcome** | Modified template | User understanding |
| **Use Case** | Refining interview templates | Understanding document content |

## Limitations

- **Read-Only**: This handler does not modify documents or generate new content
- **Knowledge Pack Scoped**: Only accesses documents associated with a specific knowledge pack
- **RAG Dependency**: Document content retrieval requires RAG initialization with valid document paths
- **Database Required**: Needs database session to fetch document metadata

## Best Practices

1. **Initialize with Document Paths**: Always provide `doc_paths` for RAG functionality
2. **Inject Database Session**: Set `handler.db = db` before calling `handle()`
3. **Use Appropriate Domain/Role**: Provide specific domain and role context for better knowledge elicitation
4. **Monitor Conversation Length**: Handler automatically trims to last 10 messages to manage context
5. **Handle User Input States**: Check for `user_input_required` status and respond appropriately

## File Structure

```
document_handler/
├── __init__.py                       # Export DocumentExplorationHandler
├── document_exploration_handler.py   # Main handler implementation
├── prompts.py                        # System prompt for LLM agent
└── README.md                         # This file
```

## System Prompt

The handler uses a specialized system prompt (`DOCUMENT_EXPLORATION_PROMPT`) that:
- Defines the agent as a knowledge-elicitation specialist
- Provides clear tool usage guidelines
- Emphasizes tacit knowledge extraction (operator tricks, workarounds, informal SOPs)
- Guides the agent to focus on practical, experience-based insights
- Ensures proper XML formatting for tool calls

## Error Handling

The handler includes comprehensive error handling:
- Tool execution errors are caught and reported to user
- Invalid tool calls are caught with helpful error messages
- RAG initialization failures are handled gracefully
- Database connection issues are reported clearly
- Notifier errors don't stop workflow execution

## Future Enhancements

Potential additions for future versions:
- Document annotation and tagging
- Document comparison and diff analysis
- Knowledge extraction workflows (generate structured knowledge from documents)
- Multi-document question answering
- Document summarization tools
- Integration with knowledge generation workflows

