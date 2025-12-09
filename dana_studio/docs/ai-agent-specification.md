# Dana Studio - AI / Agent Specification

## Metadata

| Field | Value |
|-------|-------|
| **Document Title** | Dana Studio AI / Agent Specification |
| **Version** | 1.0 |
| **Date** | 2025-12-08 |
| **Author** | Lam Nguyen |
| **Status** | Draft - AS-IS Documentation |
| **Scope** | v2 API Endpoints - Chat and Knowledge Generation Agents |

---

## 1. Agent List Overview

The following table provides an overview of all AI agents/handlers used in Dana Studio's v2 endpoints:

| Agent Name | Role | Main Purpose | Endpoint | Handler Class | Phase |
|------------|------|--------------|----------|---------------|-------|
| **KPStructuringOrchestrator** | Knowledge Structure Builder | Helps users systematically build and refine domain knowledge tree structures through conversational interactions | `POST /api/v2/knowledge/structure/{id}/chat` | `KPStructuringOrchestrator` | Knowledge generation |
| **KnowledgeGenerationTool** | Knowledge Generator | Generates structured knowledge (facts, procedures, heuristics) from pre-generated questions using RAG and LLM | `POST /api/v2/knowledge/gen/{id}/generate-knowledge` | `KnowledgeGenerationTool` | Knowledge generation |
| **DocumentExplorationHandler** | Document Analyst | Helps users explore and analyze knowledge pack documents to discover insights and refine interview questions | `POST /api/v2/knowledge/template/{id}/chat` (chat mode) | `DocumentExplorationHandler` | Template finetuning |
| **TemplateModificationHandler** | Template Editor | Enables users to modify interview template files (README.md) through natural language search/replace operations | `POST /api/v2/knowledge/template/{id}/chat` (editor mode) | `TemplateModificationHandler` | Template finetuning |
| **InterviewQuestionHandler** | Interview Conductor | Generates next interview questions based on conversation history and interview note state, guiding knowledge capture sessions | `POST /api/v2/knowledge/session/{id}/chat` | `InterviewQuestionHandler` | Interview |

---

## 2. Agent Details

### 2.1 KPStructuringOrchestrator

**Agent Role**: Knowledge Structure Builder

**Main Purpose**: Helps users systematically build and enhance AI agent knowledge bases by exploring, editing, and generating domain knowledge via specialized tools. Focuses on creating and refining hierarchical knowledge tree structures.

#### Inputs

| Input | Source | Format | Description |
|-------|--------|--------|-------------|
| User Message | Frontend (via API) | `BaseMessage` (content: string) | Natural language request from user to explore, modify, or generate knowledge structure |
| Conversation History | Database (Conversation) | `HandlerConversation` (messages: list[HandlerMessage]) | Previous messages in structuring conversation (last 10 messages used) |
| Domain Knowledge Tree | File System | `domain_knowledge.json` (DomainKnowledgeTreeV2) | Current state of knowledge tree structure |
| Knowledge Status | File System | `knowledge_status.json` (JSON) | Status tracking for knowledge generation progress |
| Domain/Role/Tasks | Knowledge Pack Metadata | String/String/List[String] | Specialization information (domain, role, tasks) |
| Knowledge Pack ID | URL Parameter | Integer | Knowledge pack identifier for WebSocket notifications |

#### Outputs

| Output | Consumer | Format | Description |
|--------|----------|--------|-------------|
| Agent Response | Frontend | `KnowledgePackResponse` (agent_response: string) | Final message explaining what was accomplished |
| Internal Conversation | Frontend | `HandlerConversation` (messages: list[HandlerMessage]) | Full conversation including tool calls and results |
| Tree Modified Flag | Frontend | Boolean (`is_tree_modified`) | Indicates if domain_knowledge.json was modified |
| Updated Tree | Frontend (if modified) | `DomainKnowledgeTreeV2` | Updated tree structure (optional) |
| WebSocket Notifications | Frontend (real-time) | JSON message | Progress updates for tool execution |

#### Allowed Tools

| Tool Name | Description | Key Parameters |
|-----------|------------|----------------|
| `explore_knowledge` | View current knowledge tree structure, topic statuses, and question generation progress | `query`, `path`, `depth` |
| `propose_knowledge_structure` | Generate comprehensive knowledge structure proposal for a new topic | `topic`, `domain`, `role` |
| `refine_knowledge_structure` | Modify a proposed structure based on user feedback | `current_structure`, `refinements` |
| `modify_tree` | Add, remove, or rename nodes in the knowledge tree | `action`, `path`, `node_name`, `bulk_operations` |
| `preview_knowledge_topic` | Preview knowledge content for a topic before adding to tree | `path_parts` |
| `question_bank_generation` | Generate questions for topics in the knowledge tree | `topics`, `mode` |
| `ask_question` | Ask user for approval, clarification, or input | `question`, `context`, `options` |
| `attempt_completion` | Signal workflow completion and provide summary | `summary`, `options` |

#### Base Prompt

```
SYSTEM: Knowledge Operations Handler 

CORE IDENTITY & MISSION
You are a Knowledge Operations Assistant that explores, edits, and generates domain knowledge via specialized tools. Your mission: help users systematically build and enhance AI agent knowledge bases with maximum safety and efficiency.

Priorities: Safety → Accuracy → User Experience → Efficiency

CRITICAL SAFETY PROTOCOL
⚠️ MANDATORY APPROVAL GATE: question_bank_generation requires explicit approval via ask_question - BUT only ask ONCE per generation request. If user confirms or chooses a generation option, proceed immediately without re-asking.

AREA AND TOPIC FOR KNOWLEDGE OPERATIONS:
Role: {role}
Domain: {domain}
Tasks: 
{tasks}

TOOLS (schema injected)
{tools_str}

RESPONSE CONTRACT
Output exactly TWO XML blocks per message:

<thinking>
<!-- 50-100 words max:
Intent: [What user wants]
Context: [Current state/findings] 
Decision: [Tool choice + why]
Approval: [If needed, what requires confirmation]
User Message: [What the user needs to understand - acknowledge their request, explain findings in their context, address their concerns]
-->
</thinking>

<tool_name>
  <param>value</param>
</tool_name>

Rules:
- ONE tool per message
- NO prose outside these blocks
- Use exact tool schemas and parameter names
- Ask approvals/clarifications ONLY via ask_question

[Full prompt continues with decision trees, workflow patterns, approval protocols, context management rules, error handling, and quality checklist - see structuring_handler/prompts.py for complete prompt]
```

#### Behavior Guidelines

1. **Intent Recognition**: Classify user requests into categories (Guidance Seeking, Information Request, Structure Display, Structure Operation, Question Generation, Tree Modification, Status Check)
2. **Tool Selection**: Use decision matrix to select appropriate tool based on intent and current state
3. **Approval Protocol**: Always seek approval for destructive operations (tree modifications) and question bank generation
4. **Context Management**: Show current state before asking for decisions; never hide context from user
5. **Workflow Patterns**: Follow established patterns (Guidance Response, Safe Exploration, Structure Addition, Question Generation, Preview-to-Addition)
6. **Conversation Continuity**: Use last 10 messages for context; maintain conversation flow naturally
7. **Error Recovery**: Acknowledge errors, explain what happened, offer alternatives

#### Guardrails

1. **Never modify tree without approval**: Always use `ask_question` to confirm destructive operations
2. **Never generate questions without approval**: Question bank generation requires explicit user confirmation
3. **Never skip explore_knowledge**: Always check current state before proposing changes
4. **Never propose structures without context**: Must understand existing tree structure first
5. **Never use vague patterns**: Search/replace operations must include sufficient context for uniqueness
6. **Never proceed without user input**: If `require_user=True`, stop and wait for response
7. **Never exceed 15 iterations**: Tool loop terminates after 15 iterations to prevent infinite loops

#### Known Limitations

1. **Conversation History**: Only uses last 10 messages for context (may lose earlier context in long conversations)
2. **Tree Reload**: Tree structure reloaded after `modify_tree` operations (may cause slight delay)
3. **WebSocket Dependency**: Real-time notifications require WebSocket connection (falls back gracefully if unavailable)
4. **File System State**: Relies on file system for tree state (potential race conditions in concurrent access)
5. **Tool Loop Limit**: Maximum 15 iterations per request (complex operations may require multiple requests)
6. **Question Generation**: Requires topics to exist in tree before generating questions

#### Example

**Input (API Request)**:
```json
{
  "user_message": "Add a topic about sugar crystallization under Process Operations",
  "kp_id": 42
}
```

**Context (from file system and database)**:
- Domain: "Sugar Manufacturing"
- Role: "Process Operator"
- Current tree has root "Sugar Manufacturing" with child "Process Operations"

**Agent Processing (tool loop)**:

*Iteration 1 - Explore current state:*
```xml
<thinking>
Intent: User wants to add sugar crystallization topic under Process Operations
Context: Need to verify Process Operations exists and check current structure
Decision: explore_knowledge to view current tree state
</thinking>

<explore_knowledge>
  <path>Process Operations</path>
  <depth>2</depth>
</explore_knowledge>
```

*Iteration 2 - Propose structure:*
```xml
<thinking>
Intent: Process Operations exists, now propose crystallization structure
Context: Topic doesn't exist yet, need comprehensive proposal
Decision: propose_knowledge_structure to generate topic outline
</thinking>

<propose_knowledge_structure>
  <topic>Sugar Crystallization</topic>
  <domain>Sugar Manufacturing</domain>
  <role>Process Operator</role>
</propose_knowledge_structure>
```

*Iteration 3 - Ask for approval:*
```xml
<thinking>
Intent: Show proposed structure and get user approval
Context: Generated 5 subtopics for Sugar Crystallization
Decision: ask_question to confirm before modifying tree
</thinking>

<ask_question>
  <question>I've prepared a Sugar Crystallization structure with 5 subtopics: Supersaturation Control, Crystal Growth Monitoring, Seed Addition Procedures, Pan Temperature Management, and Crystal Size Distribution. Would you like me to add this to the tree?</question>
  <options>["Yes, add this structure", "Modify the structure first", "Cancel"]</options>
</ask_question>
```

**Output (API Response)**:
```json
{
  "agent_response": "I've prepared a Sugar Crystallization structure with 5 subtopics: Supersaturation Control, Crystal Growth Monitoring, Seed Addition Procedures, Pan Temperature Management, and Crystal Size Distribution. Would you like me to add this to the tree?",
  "internal_conversation": [...],
  "is_tree_modified": false,
  "require_user_input": true
}
```

---

### 2.2 KnowledgeGenerationTool

**Agent Role**: Knowledge Generator

**Main Purpose**: Generates structured knowledge (facts, procedures, heuristics) from pre-generated questions stored in knowledge.json files. Processes all leaf nodes in the knowledge tree, uses RAG for document context, and creates knowledge summaries and master interview templates.

#### Inputs

| Input | Source | Format | Description |
|-------|--------|--------|-------------|
| Knowledge Pack ID | Task Data | Integer | Knowledge pack identifier |
| Storage Path | Task Data | String | Path to `knows/` folder containing knowledge.json files |
| Domain Knowledge Path | Task Data | String | Path to `domain_knowledge.json` tree structure |
| Knowledge Status Path | Task Data | String | Path to `knowledge_status.json` for progress tracking |
| Document Paths | Task Data | List[String] | File paths to associated documents for RAG |
| Domain/Role/Tasks | Task Data | String/String/List[String] | Specialization information |
| Template Generation Prompt | Task Data (optional) | String | Knowledge pack-specific prompt override for template generation |
| Question Batch Size | Configuration | Integer | Number of questions to process per batch (default: 1) |
| Allow Outside Document | Configuration | Boolean | Whether to generate knowledge without document context (default: False) |

#### Outputs

| Output | Consumer | Format | Description |
|--------|----------|--------|-------------|
| Knowledge JSON Files | File System | JSON | Updated `knowledge.json` files with generated facts, procedures, heuristics |
| Knowledge Status | File System | JSON | Updated `knowledge_status.json` with generation progress |
| Domain Knowledge Tree | File System | JSON | Updated `domain_knowledge.json` with node statuses |
| Knowledge Summaries | File System | JSON | Summary field added to each `knowledge.json` file |
| Master Interview Template | File System | Markdown | Generated `template/README.md` master interview template |
| WebSocket Notifications | Frontend (real-time) | JSON message | Progress updates for each topic processed |

#### Process Flow

1. **Extract Leaf Paths**: Recursively extract all leaf node paths from domain knowledge tree
2. **Process Each Leaf**:
   - Read existing `knowledge.json` file
   - Extract questions from knowledge entries
   - Query RAG for relevant document chunks (if documents available)
   - Generate knowledge from questions using LLM (with retry logic and timeout protection)
   - Transform raw knowledge into structured format (facts, procedures, heuristics)
   - Update `knowledge.json` file with generated content
   - Update status manager and tree structure
3. **Generate Summaries**: For each successfully processed topic, generate summary and add to `knowledge.json`
4. **Generate Master Template**: Read all summaries, generate master interview template, save to `template/README.md`

#### Allowed Tools

| Tool Name | Description | Key Parameters |
|-----------|------------|----------------|
| RAG Resource (internal) | Query documents for relevant chunks | `query`, `num_results` |
| LLM Resource (internal) | Generate knowledge from questions | `prompt`, `temperature`, `max_tokens` |
| Knowledge Status Manager (internal) | Track generation progress | `path`, `status`, `file_path` |
| File System I/O (internal) | Read/write knowledge.json files | File paths |

#### Base Prompt (Knowledge Extraction)

```
[Knowledge Extraction Prompt - used when documents available]
Based on the following document chunks and question, extract structured knowledge:

Path: {path}
Question: {question}
Chunks:
{chunks}

Generate knowledge in the following format:
## Facts
- [Factual knowledge from documents]

## Procedures
- Overview 1: [Step-by-step procedure]
- Overview 2: [Another procedure]

## Heuristics
- [Rule-of-thumb or judgment-based knowledge]

Include chunk references [Chunk N] for facts/procedures/heuristics derived from specific chunks.
```

#### Base Prompt (Knowledge Generation - No Documents)

```
[Knowledge Generation Prompt - used when no documents or allow_outside_document=True]
Based on your expertise as a {role} in {domain}, generate knowledge for:

Path: {path}
Question: {question}

Generate knowledge in the following format:
## Facts
- [Factual knowledge]

## Procedures
- Overview 1: [Step-by-step procedure]
- Overview 2: [Another procedure]

## Heuristics
- [Rule-of-thumb or judgment-based knowledge]
```

#### Behavior Guidelines

1. **Resumable Processing**: Checks status manager to skip already-completed topics
2. **Batch Processing**: Processes questions in batches (configurable batch size)
3. **RAG Integration**: Queries RAG for document chunks before generating knowledge (if documents available)
4. **Retry Logic**: Implements exponential backoff retry for failed LLM calls (max 2 retries)
5. **Timeout Protection**: Uses configurable timeouts for LLM calls, RAG queries, and batch operations
6. **Status Tracking**: Updates knowledge_status.json and domain_knowledge.json with progress
7. **WebSocket Notifications**: Sends real-time progress updates via WebSocket
8. **Error Handling**: Continues processing other topics if one fails (doesn't stop entire pipeline)
9. **Summary Generation**: Generates summaries for all successfully processed topics
10. **Template Generation**: Creates master interview template from all summaries using prompt hierarchy (KP override > Global default > Hardcoded fallback)

#### Guardrails

1. **Never skip questions**: Must process all questions found in knowledge.json files
2. **Never overwrite without backup**: Preserves existing knowledge entries when updating files
3. **Never proceed without questions**: Skips topics that don't have questions in knowledge.json
4. **Never exceed timeouts**: Respects configured timeouts for LLM calls and RAG queries
5. **Never modify tree structure**: Only updates node statuses, doesn't modify tree hierarchy
6. **Never generate without approval**: Requires pre-generated questions (user must approve question generation first)
7. **Never process same topic twice**: Checks status manager before processing (resumable)

#### Known Limitations

1. **Question Dependency**: Requires pre-generated questions in knowledge.json files (must run question bank generation first)
2. **Document Dependency**: Knowledge quality depends on document availability and RAG quality
3. **Timeout Constraints**: Long-running operations may timeout (configurable but may need adjustment)
4. **Retry Limits**: Maximum 5 retry attempts per LLM call (may fail permanently if LLM consistently times out)
5. **Batch Size**: Default batch size of 1, each batch contains 5 questions (may be slow for topics with many questions)
6. **File System Dependency**: Direct file I/O operations (potential race conditions in concurrent access)
7. **Memory Usage**: Loads entire tree structure and processes all leaves (may be memory-intensive for large trees)
8. **Template Generation**: Template generation depends on summary quality (may produce poor templates if summaries incomplete)

#### Example

**Input (API Request)**:
```json
{
  "kp_id": 42
}
```

**Context (from task data and file system)**:
- Knowledge Pack ID: 42
- Storage Path: `/data/kp_42/knows/`
- Domain Knowledge Path: `/data/kp_42/domain_knowledge.json`
- Document Paths: ["/data/kp_42/docs/Operating_Manual.pdf", "/data/kp_42/docs/Safety_Guidelines.pdf"]
- Domain: "Sugar Manufacturing"
- Role: "Process Operator"

**Tree Structure (domain_knowledge.json)**:
```json
{
  "root": {
    "topic": "Sugar Manufacturing",
    "children": [
      {
        "topic": "Centrifuge Operations",
        "children": [],
        "status": "pending"
      },
      {
        "topic": "Filtration Systems",
        "children": [],
        "status": "pending"
      }
    ]
  }
}
```

**Pre-existing knowledge.json (for Centrifuge Operations)**:
```json
{
  "path_parts": ["Sugar Manufacturing", "Centrifuge Operations"],
  "knowledges": [
    {"question": "What are the standard operating parameters for centrifuges?", "facts": [], "procedures": [], "heuristics": []},
    {"question": "How do operators handle high-brix campaigns?", "facts": [], "procedures": [], "heuristics": []}
  ]
}
```

**Processing Flow**:

1. **Extract Leaf Paths**:
   - Found 2 leaves: `["Sugar Manufacturing", "Centrifuge Operations"]`, `["Sugar Manufacturing", "Filtration Systems"]`

2. **Process Leaf 1 (Centrifuge Operations)**:
   - Read `knows/Centrifuge_Operations/knowledge.json`
   - Extract questions: 2 questions found
   - Query RAG for relevant chunks (Operating Manual mentions centrifuge parameters)
   - LLM generates knowledge:

```markdown
## Facts
- [Chunk 1, Chunk 3] Standard centrifuge speed is 1200 RPM with max recommended 1350 RPM
- [Chunk 2] Basket temperature should be maintained below 85°C

## Procedures
- Overview 1: [Chunk 4] Pre-startup inspection includes checking basket balance, seal integrity, and lubrication levels

## Heuristics
- [Chunk 5] During high-brix campaigns, experienced operators increase speed to 1400 RPM accepting 15% higher bearing wear for throughput gains
```

3. **Update knowledge.json**:
```json
{
  "path_parts": ["Sugar Manufacturing", "Centrifuge Operations"],
  "knowledges": [
    {
      "question": "What are the standard operating parameters for centrifuges?",
      "facts": [
        {"content": "Standard centrifuge speed is 1200 RPM with max recommended 1350 RPM", "references": [{"source": "Operating_Manual.pdf", "page_number": 23}]},
        {"content": "Basket temperature should be maintained below 85°C", "references": [{"source": "Operating_Manual.pdf", "page_number": 24}]}
      ],
      "procedures": [
        {"content": "Pre-startup inspection includes checking basket balance, seal integrity, and lubrication levels", "references": [{"source": "Operating_Manual.pdf", "page_number": 25}]}
      ],
      "heuristics": []
    },
    {
      "question": "How do operators handle high-brix campaigns?",
      "facts": [],
      "procedures": [],
      "heuristics": [
        {"content": "During high-brix campaigns, experienced operators increase speed to 1400 RPM accepting 15% higher bearing wear for throughput gains", "references": [{"source": "Operating_Manual.pdf", "page_number": 28}]}
      ]
    }
  ]
}
```

4. **Generate Summary** (added to knowledge.json):
```markdown
# Summary
Centrifuge Operations covers the core operating parameters and campaign-specific adjustments for sugar centrifuges. Standard operation is at 1200 RPM with temperature limits of 85°C. During high-brix campaigns, operators trade bearing life for throughput by exceeding normal speed limits.

# Key Concepts
- Standard RPM: 1200
- Max recommended RPM: 1350
- High-brix campaign speed: 1400 RPM
- Temperature limit: 85°C
- Bearing wear trade-off

# Referenced Documents
- Operating_Manual.pdf
```

5. **Generate Master Interview Template** (after all leaves processed):
   - Reads all summaries
   - Creates `template/README.md` with opening questions for each topic

**Output (WebSocket notifications during processing)**:
```json
{"tool_name": "generate_knowledge", "content": "Starting knowledge generation for 2 topics", "status": "in_progress", "progression": 0.0}
{"tool_name": "generate_knowledge", "content": "Processing Centrifuge Operations (1/2)", "status": "in_progress", "progression": 0.25, "path_parts": ["Sugar Manufacturing", "Centrifuge Operations"]}
{"tool_name": "generate_question_bank", "content": "Completed Centrifuge Operations - 1/2 done", "status": "completed", "progression": 0.5, "path_parts": ["Sugar Manufacturing", "Centrifuge Operations"]}
{"tool_name": "generate_knowledge", "content": "Processing Filtration Systems (2/2)", "status": "in_progress", "progression": 0.75, "path_parts": ["Sugar Manufacturing", "Filtration Systems"]}
{"tool_name": "generate_question_bank", "content": "Completed Filtration Systems - 2/2 done", "status": "completed", "progression": 1.0, "path_parts": ["Sugar Manufacturing", "Filtration Systems"]}
```

**Final Output (ToolResult)**:
```json
{
  "name": "generate_knowledge",
  "result": "I understand you want to generate comprehensive knowledge for all topics in the tree structure. This will create detailed facts, procedures, and heuristics to enhance the agent's capabilities.\n\n✅ Knowledge generation pipeline complete.",
  "require_user": false
}
```

---

### 2.3 DocumentExplorationHandler

**Agent Role**: Document Analyst

**Main Purpose**: Helps users explore and analyze knowledge pack documents to discover insights, answer questions, and identify opportunities to refine interview questions. Uses RAG for document content retrieval.

#### Inputs

| Input | Source | Format | Description |
|-------|--------|--------|-------------|
| User Message | Frontend (via API) | `BaseMessage` (content: string) | Natural language query about documents |
| Conversation History | Database (Conversation) | `IntentDetectionRequest` (chat_history: list[MessageData]) | Previous messages in conversation (last 4 messages used) |
| Document Paths | Knowledge Pack Metadata | List[String] | File paths to associated documents |
| Template Path | Template Metadata | String (optional) | Path to interview template README.md for context |
| Domain/Role | Knowledge Pack Metadata | String/String | Domain and role for context |
| Knowledge Pack ID | Template Metadata | Integer | Knowledge pack identifier |
| Database Session | API Route | SQLAlchemy Session | Database session for document queries |
| Custom System Prompt | Template Folder | String (optional) | Custom system prompt from `system_prompt.prompt` file |

#### Outputs

| Output | Consumer | Format | Description |
|--------|----------|--------|-------------|
| Agent Response | Frontend | `TemplateFinetuneChannelResponse` (agent_response: string) | Final message with document insights or answers |
| Internal Conversation | Frontend | `HandlerConversation` (messages: list[HandlerMessage]) | Full conversation including tool calls and results |
| Document List | Agent (internal) | List[Document] | List of documents associated with knowledge pack |

#### Allowed Tools

| Tool Name | Description | Key Parameters |
|-----------|------------|----------------|
| `read_documents` | Search and read document content using RAG | `query` (required), `document_id` (optional) |
| `ask_question` | Ask user for clarification or gather more information | `question`, `context`, `options` |
| `attempt_completion` | Provide summary of findings or answer user questions | `result`, `options` |

#### Base Prompt

```
You are a knowledge-elicitation agent specialized in analyzing documents to understand and refine interview questions for {domain} - {role}.

Your purpose is to:
1. Help users explore and understand documents in the knowledge pack
2. Answer questions about document content using RAG
3. Identify opportunities to refine interview questions based on document insights
4. Extract tacit operational knowledge and site-specific details

Your Capabilities (Tools Available):
{tools_str}

{document_context}

Workflow Guidelines:
- Use read_documents with a query parameter to search for information in documents. Always provide a specific question or search term.
- Use read_documents with both query and document_id to search within a specific document
- Use ask_question to clarify user intent, gather more information, or get approval before proceeding
- Use attempt_completion when:
  * User's questions have been answered
  * Document exploration is complete
  * User asks about document status or structure
  * Workflow has reached a natural conclusion
- Focus on practical, experience-based insights from documents
- Be conversational, helpful, and guide users toward valuable knowledge discovery
- When querying documents, look for tacit knowledge like:
  * Operator tricks and workarounds
  * Common failure patterns
  * Unofficial procedures and informal SOPs
  * Site-specific control strategies
  * Historical context and legacy constraints

Context:
- Domain: {domain}
- Role: {role}

Response Format:
Always respond with TWO XML blocks in this order:

1) Planning (thinking tag):
<thinking>
Explain your reasoning:
- What the user is asking for
- Which tool to use and why
- What parameters to provide
- What the expected outcome is
</thinking>

2) Tool call (use exact tool name and parameter tags as defined in tool schema):
<tool_name>
  <param1>value1</param1>
  <param2>value2</param2>
</tool_name>

Remember: You're helping elicit tacit knowledge, not just factual information. Guide users to discover insights that reveal practical experience and operational wisdom.
```

#### Behavior Guidelines

1. **RAG Initialization**: Lazy initialization of RAG resource when first needed (if document paths provided)
2. **Document Context**: Builds document list context (shows IDs and names if ≤10 documents, otherwise instructs to use queries)
3. **Template Integration**: Includes template content in system prompt if template_path provided
4. **Custom Prompt Support**: Loads and prepends custom system prompt from `system_prompt.prompt` file if exists
5. **Conversation Continuity**: Uses last 4 messages for context (shorter than other handlers)
6. **Query-First Approach**: Encourages users to query documents rather than listing all documents
7. **Tacit Knowledge Focus**: Emphasizes discovering practical experience, workarounds, and site-specific details

#### Guardrails

1. **Never list all documents if >10**: Refuse to list all documents if knowledge pack has more than 10 documents
2. **Never proceed without query**: Always require a specific query when using `read_documents` tool
3. **Never modify documents**: Read-only access to documents (cannot edit document content)
4. **Never modify template**: Cannot modify interview template (that's TemplateModificationHandler's job)
5. **Never exceed 15 iterations**: Tool loop terminates after 15 iterations
6. **Never proceed without user input**: If `require_user=True`, stop and wait for response
7. **Never access documents outside knowledge pack**: Only access documents associated with the knowledge pack

#### Known Limitations

1. **RAG Initialization**: RAG resource initialized on first use (may cause delay on first query)
2. **Document Limit**: Refuses to list documents if >10 (may frustrate users with large document sets)
3. **Conversation History**: Only uses last 4 messages (may lose context in longer conversations)
4. **No Document Editing**: Read-only access (cannot modify document content)
5. **RAG Dependency**: Requires RAG resource to be initialized (fails gracefully if documents unavailable)
6. **Template Context**: Template content included but cannot be modified through this handler

#### Example

**Input (API Request)**:
```json
{
  "user_message": "What safety procedures are mentioned in the operating manual?",
  "template_id": 15,
  "mode": "chat"
}
```

**Context (from knowledge pack)**:
- Domain: "Sugar Manufacturing"
- Role: "Process Operator"
- Associated documents: ["Operating_Manual_v3.pdf", "Safety_Guidelines.pdf"]
- Document context: "2 documents available"

**Agent Processing (tool loop)**:

*Iteration 1 - Query documents:*
```xml
<thinking>
What the user is asking for: Safety procedures from operating manual
Which tool to use: read_documents with safety-focused query
Parameters: query about safety procedures
Expected outcome: Relevant chunks about safety from documents
</thinking>

<read_documents>
  <query>What safety procedures and protocols are described in the operating manual?</query>
</read_documents>
```

*Tool Result (RAG returns relevant chunks):*
```
Found 5 relevant chunks:

[Chunk 1 - Operating_Manual_v3.pdf, Page 23]
"Lockout/Tagout (LOTO) Procedure: Before any maintenance work, operators must:
1. Notify supervisor and affected personnel
2. Isolate energy sources (electrical, pneumatic, hydraulic)
3. Apply personal locks and tags..."

[Chunk 2 - Operating_Manual_v3.pdf, Page 45]
"Emergency Shutdown Protocol: In case of equipment malfunction:
1. Press emergency stop button (red mushroom)
2. Clear personnel from affected area..."
```

*Iteration 2 - Provide answer:*
```xml
<thinking>
What the user is asking for: Summary of safety procedures found
Which tool to use: attempt_completion to deliver findings
Expected outcome: User receives comprehensive answer about safety procedures
</thinking>

<attempt_completion>
  <result>Based on the Operating Manual, I found several key safety procedures:

**Lockout/Tagout (LOTO) Procedure** (Page 23):
- Notify supervisor and affected personnel before maintenance
- Isolate all energy sources (electrical, pneumatic, hydraulic)
- Apply personal locks and tags to isolation points
- Verify zero energy state before beginning work

**Emergency Shutdown Protocol** (Page 45):
- Press the red emergency stop button (mushroom type)
- Clear all personnel from the affected area
- Follow the evacuation route posted at each station

Would you like me to explore any of these procedures in more detail, or search for other safety-related information?</result>
</attempt_completion>
```

**Output (API Response)**:
```json
{
  "agent_response": "Based on the Operating Manual, I found several key safety procedures:\n\n**Lockout/Tagout (LOTO) Procedure** (Page 23):\n- Notify supervisor and affected personnel before maintenance\n- Isolate all energy sources (electrical, pneumatic, hydraulic)\n- Apply personal locks and tags to isolation points\n- Verify zero energy state before beginning work\n\n**Emergency Shutdown Protocol** (Page 45):\n- Press the red emergency stop button (mushroom type)\n- Clear all personnel from the affected area\n- Follow the evacuation route posted at each station\n\nWould you like me to explore any of these procedures in more detail, or search for other safety-related information?",
  "internal_conversation": [...],
  "status": "success"
}
```

---

### 2.4 TemplateModificationHandler

**Agent Role**: Template Editor

**Main Purpose**: Enables users to modify interview template files (README.md) through natural language interactions. Focuses on search/replace operations to update template content while preserving structure.

#### Inputs

| Input | Source | Format | Description |
|-------|--------|--------|-------------|
| User Message | Frontend (via API) | `BaseMessage` (content: string) | Natural language request to modify template content |
| Conversation History | Database (Conversation) | `IntentDetectionRequest` (chat_history: list[MessageData]) | Previous messages in template conversation (last 10 messages, filtered by mode) |
| Template File Path | Template Metadata | String | Path to `README.md` file in template folder |
| Knowledge Pack ID | Template Metadata | Integer | Knowledge pack identifier for context |
| Database Session | API Route | SQLAlchemy Session | Database session for tools that need DB access |

#### Outputs

| Output | Consumer | Format | Description |
|--------|----------|--------|-------------|
| Agent Response | Frontend | `TemplateFinetuneChannelResponse` (agent_response: string) | Final message explaining modifications made |
| Internal Conversation | Frontend | `HandlerConversation` (messages: list[HandlerMessage]) | Full conversation including tool calls and results |
| Template Modified Flag | Frontend | Boolean (`template_modified`) | Indicates if README.md was modified |
| Template Diff | Frontend (if modified) | `TemplateDiff` (sections: list[TemplateDiffSection]) | Line-by-line diff showing changes made |

#### Allowed Tools

| Tool Name | Description | Key Parameters |
|-----------|------------|----------------|
| `view_template` | Read and display template sections or entire template | `section` (all, specific section name) |
| `replace_in_template` | Perform search/replace operations on template content | `diff` (SEARCH/REPLACE blocks) |
| `ask_question` | Ask user for clarification or approval before modifications | `question`, `context`, `options` |
| `attempt_completion` | Signal workflow completion | `summary`, `options` |

#### Base Prompt

```
You are a Template Modification Assistant that helps users edit interview templates via search/replace operations.

## CONTEXT
- UI: Split screen - left side (chat), right side (template preview)
- Template content is already visible in the conversation (from view_template tool result)
- Your job: Parse user intent → Create accurate SEARCH/REPLACE patterns → Update template
- Template Path: {template_path}

## AVAILABLE TOOLS
{tools_str}

## RESPONSE FORMAT
Output exactly TWO XML blocks per message:

<thinking>
<!-- 50-80 words:
Intent: [What user wants to change]
Current state: [What conversation shows vs what template contains]
Changes needed: [Specific edits required]
Batching: [Single change / N independent changes - batch together / Changes need sequence]
Pattern strategy: [What context to include for unique matching]
User message: [Acknowledge request and explain action]
--->
</thinking>

<tool_name>
  <param>value</param>
</tool_name>

Rules:
- ONE tool call per message
- NO prose outside XML blocks
- Use exact tool schemas

## CORE TASK: SEARCH/REPLACE PATTERN CREATION

### Operating Principle
You create SEARCH patterns that match the current template and REPLACE patterns that represent the desired state. The key is **preserving structure while modifying content**.

### Rule 1: Structure Preservation (Most Important)
- Locate the target section in view_template result
- Identify ALL sub-sections present (Background, Questions, Notes, Examples, etc.)
- Create pattern that includes ALL identified sub-sections
- Modify only what user requested, keep everything else identical

### Rule 2: Uniqueness Strategy
- Ensure SEARCH pattern appears exactly once in the template
- Minimum safety: Include topic header + section marker + line(s) being modified
- Add more context for generic phrasing or short patterns

### Rule 3: Multi-Block Batching
- Use single tool call with multiple SEARCH/REPLACE blocks when changes are independent
- Batch changes that don't depend on each other

[Full prompt continues with examples, edge cases, and error handling - see template_handler/prompts.py for complete prompt]
```

#### Behavior Guidelines

1. **Auto-View Template**: Automatically calls `view_template` with `section="all"` if not already called
2. **Structure Preservation**: Always preserve all sections when modifying content (Background, Questions, Notes, etc.)
3. **Uniqueness Strategy**: Include sufficient context (headers, section markers) to ensure unique pattern matching
4. **Batching**: Batch independent changes into single tool call with multiple SEARCH/REPLACE blocks
5. **Mode Filtering**: Filters conversation history to exclude editor/auto mode messages for cleaner context
6. **Conversation Continuity**: Uses last 10 messages (filtered) for context
7. **Error Recovery**: Handles pattern matching failures gracefully, asks for clarification if needed

#### Guardrails

1. **Never modify without viewing**: Always call `view_template` first to understand current structure
2. **Never omit sections**: SEARCH patterns must include ALL sections present in target area
3. **Never use generic patterns**: Avoid patterns that could match multiple locations
4. **Never modify structure**: Only modify content, preserve markdown structure and formatting
5. **Never proceed without approval**: Ask for confirmation before major modifications
6. **Never exceed 15 iterations**: Tool loop terminates after 15 iterations
7. **Never modify master templates**: Master templates are read-only (enforced at API level)

#### Known Limitations

1. **Search/Replace Only**: Limited to text-based search/replace operations (cannot perform complex transformations)
2. **Pattern Matching**: Relies on exact text matching (whitespace-sensitive)
3. **No Undo**: Modifications are immediate (no built-in undo mechanism)
4. **File System Dependency**: Direct file I/O operations (potential race conditions)
5. **Conversation Filtering**: Filters out editor/auto mode messages (may lose some context)
6. **Single File Focus**: Only modifies README.md (cannot modify other template files)

#### Example

**Input (API Request)**:
```json
{
  "user_message": "Change question 2 in the Filtration topic to ask about common failure modes",
  "template_id": 15,
  "mode": "editor"
}
```

**Context (current template content from view_template)**:
```markdown
### Filtration

**Background**: Filtration is critical for product quality...

**Opening Questions**:
1. What filtration methods do you currently use?
2. How do you monitor filter performance?
3. What triggers a filter change decision?
```

**Agent Processing (tool loop)**:

*Iteration 1 - Auto-view template (if not already viewed):*
```xml
<thinking>
Intent: User wants to modify question 2 in Filtration topic
Current state: Need to see template structure first
Decision: view_template to get current content
</thinking>

<view_template>
  <section>all</section>
</view_template>
```

*Iteration 2 - Perform replacement:*
```xml
<thinking>
Intent: Replace question 2 about monitoring with failure modes question
Current state: Found Filtration section with 3 questions
Changes needed: Replace line "2. How do you monitor filter performance?"
Pattern strategy: Include topic header + Opening Questions marker + all 3 questions for uniqueness
</thinking>

<replace_in_template>
<diff>
-------- SEARCH
### Filtration

**Background**: Filtration is critical for product quality...

**Opening Questions**:
1. What filtration methods do you currently use?
2. How do you monitor filter performance?
3. What triggers a filter change decision?
=======
### Filtration

**Background**: Filtration is critical for product quality...

**Opening Questions**:
1. What filtration methods do you currently use?
2. What are the most common failure modes you encounter with your filtration systems?
3. What triggers a filter change decision?
++++++ REPLACE
</diff>
</replace_in_template>
```

*Iteration 3 - Confirm completion:*
```xml
<thinking>
Intent: Replacement successful, confirm to user
Decision: attempt_completion to summarize change
</thinking>

<attempt_completion>
  <result>I've updated question 2 in the Filtration topic. It now asks "What are the most common failure modes you encounter with your filtration systems?" instead of the previous monitoring question.</result>
</attempt_completion>
```

**Output (API Response)**:
```json
{
  "agent_response": "I've updated question 2 in the Filtration topic. It now asks \"What are the most common failure modes you encounter with your filtration systems?\" instead of the previous monitoring question.",
  "internal_conversation": [...],
  "template_modified": true,
  "template_diff": {
    "sections": [
      {
        "old_lines": ["2. How do you monitor filter performance?"],
        "new_lines": ["2. What are the most common failure modes you encounter with your filtration systems?"],
        "line_start": 8
      }
    ]
  }
}
```

---



### 2.5 InterviewQuestionHandler

**Agent Role**: Interview Conductor

**Main Purpose**: Generates next interview questions based on conversation history and current interview note state. Guides knowledge capture sessions by asking informed questions that explore domain expertise while tracking question statuses and template coverage.

#### Inputs

| Input | Source | Format | Description |
|-------|--------|--------|-------------|
| User Message | Frontend (via API) | `BaseMessage` (content: string) | User's answer to previous question or new query |
| Conversation History | Database (Conversation) | `IntentDetectionRequest` (chat_history: list[MessageData]) | Previous messages in interview session (last 4 messages used, filtered from last interview_note question) |
| Current Note Content | File System | String (Markdown) | Current state of `interview_notes.md` file (read-only) |
| Template Content | File System | String (Markdown) | Interview template README.md content |
| Document Answer | Message Metadata (optional) | String | Precomputed answer from documents for comparison with user's answer |
| Knowledge Pack ID | Session Metadata | Integer | Knowledge pack identifier |
| Domain/Role | Template Metadata | String/String | Domain and role for context |
| RAG Resource | Session Initialization | `RAGResourceV2` | RAG resource for document search (initialized from knows folder + documents) |
| Database Session | API Route | SQLAlchemy Session | Database session for ReadDocumentsTool |

#### Outputs

| Output | Consumer | Format | Description |
|--------|----------|--------|-------------|
| Agent Response | Frontend | `InterviewChatResponse` (agent_response: string) | Generated question or completion message |
| Internal Conversation | Frontend | `HandlerConversation` (messages: list[HandlerMessage]) | Full conversation including tool calls and results |
| Workflow Completed Flag | Frontend | Boolean (`workflow_completed`) | Indicates if interview is complete |
| Question Category | Message Metadata | String | Category of question (`interview_note`, `followup`, `normal`) |

#### Allowed Tools

| Tool Name | Description | Key Parameters |
|-----------|------------|----------------|
| `ask_question` | Generate and ask next interview question | `preface`, `question`, `category`, `workflow_phase` |
| `attempt_completion` | Signal interview completion and provide summary | `result`, `options` |

#### Base Prompt

```
SYSTEM: Expert Interview Question Generator

CORE IDENTITY & MISSION
You are an Expert Interview Question Generator focused on generating next interview questions based on conversation history and current note state. Your mission: ask informed questions that guide the knowledge extraction interview while demonstrating genuine understanding.

Your approach balances technical rigor with natural conversation - you demonstrate genuine understanding through a natural preface that acknowledges the user's response and provides context, then asks questions that explore domain expertise.

Priorities: Conversational Quality → Template Coverage → User Experience → Efficiency

CRITICAL SAFETY PROTOCOL
⚠️ MANDATORY PROTOCOL: Use the current note state (provided in system context) to inform your questions. You have read-only access to the note - do NOT update it (that's the note handler's job).

⚠️ QUESTION STATUS ENFORCEMENT:
The interview note tracks question statuses using bracket notation: [not_asked], [asking], [clarifying], [completed]

⚠️ TOPIC IDENTIFICATION PROTOCOL:
Before suggesting next topics, you MUST:
1. **READ the "## Topics to Cover" section** in the provided note
2. **IDENTIFY all topics** by looking for "### [Topic_Name]" headings
3. **CHECK each topic's Status** (Not Started, In Progress, Completed)
4. **COUNT total topics** to understand interview scope
5. **NEVER suggest topics that don't exist** in the current note
6. **NEVER hallucinate topic names** from memory or other sessions

STRICT RULES FOR QUESTION SELECTION:
1. **NEVER re-ask questions marked as [completed]** - these have already been answered and captured
2. **When revisiting a topic**: Only ask questions that are NOT [completed]
3. **When continuing a topic**: Start with the first question that is NOT [completed]
4. **If user wants to go back to a fully finished topic**: Use attempt_completion or ask_question with category: normal to guide user to other topics
5. **Question Status Priority**: [completed] → SKIP, [asking] → Continue, [clarifying] → Continue, [not_asked] or unmarked → Can be asked

ANSWER COMPARISON LOGIC:
When a document_answer is provided, compare the USER'S ANSWER with the DOCUMENT ANSWER:
- If answers align: Continue with next interview_note question
- If significant differences: Ask followup question (category: followup) to clarify
- If user adds valuable detail: Acknowledge and continue with next question
- If document answer is incomplete: Continue with user's answer

RESPONSE CONTRACT
Output exactly TWO XML blocks per message:

<thinking>
<!-- 50-100 words max:
Intent: [What user wants to share/discuss/query]
Context: [Current note state/template coverage - list all topics found in note]
Topic Count: [How many topics exist in this note? Are there more topics after current one?]
Question Status Check: [If asking interview_note question, confirm it's NOT [completed]]
Decision: [Tool choice + why + category if using ask_question]
Next Topic Verification: [If suggesting next topic, confirm it EXISTS in note's "## Topics to Cover"]
Understanding: [What you comprehended from their last response - this will inform the preface]
-->
</thinking>

<tool_name>
  <param>value</param>
</tool_name>

Rules:
- ONE tool per message
- NO prose outside these blocks
- Use exact tool schemas and parameter names
- Ask clarifications ONLY via ask_question
- Every ask_question MUST include a preface (combining acknowledgment and context)
- Every ask_question MUST specify the category parameter (interview_note, followup, or normal)

⚠️ CRITICAL INTERVIEWING RULE: ONE QUESTION AT A TIME
- ALWAYS ask exactly ONE question per ask_question tool call
- Wait for user's answer before asking the next question
- NEVER list multiple questions in the <question> parameter
- <options> are for suggesting ANSWER DIRECTIONS, not additional questions

[Full prompt continues with intent recognition, tool selection matrix, workflow patterns, enhanced tool usage examples, context management rules, error handling, and quality checklist - see interview_question_handler/prompts.py for complete prompt]
```

#### Behavior Guidelines

1. **Note State Awareness**: Always reads current note state to understand topics, question statuses, and progress
2. **Question Status Tracking**: Respects question statuses ([not_asked], [asking], [clarifying], [completed]) and never re-asks completed questions
3. **Topic Navigation**: Verifies topic names exist in note before suggesting them; never hallucinates topics
4. **Preface Protocol**: Every question includes a natural preface that acknowledges user's response and provides context
5. **Category Selection**: Categorizes questions as `interview_note` (template questions), `followup` (clarification), or `normal` (meta-questions)
6. **Document Answer Comparison**: Compares user's answer with precomputed document answer to identify differences
7. **Conversation Filtering**: Uses messages from last interview_note question onwards for relevant context
8. **One Question at a Time**: Never asks multiple questions in a single tool call

#### Guardrails

1. **Never re-ask completed questions**: Questions marked [completed] must never be asked again
2. **Never hallucinate topics**: Only suggest topics that exist in the current note's "## Topics to Cover" section
3. **Never update note directly**: Read-only access to note (note updates handled by InterviewNoteProcessor)
4. **Never ask multiple questions**: Always ask exactly one question per tool call
5. **Never skip preface**: Every question must include a natural preface combining acknowledgment and context
6. **Never use wrong category**: Must correctly categorize questions (interview_note, followup, normal)
7. **Never exceed 15 iterations**: Tool loop terminates after 15 iterations
8. **Never proceed without user input**: If `require_user=True`, stop and wait for response

#### Known Limitations

1. **Note Read-Only**: Cannot update interview notes directly (updates handled separately by InterviewNoteProcessor)
2. **Conversation History**: Only uses last 4 messages (may lose context in longer conversations)
3. **Topic Verification**: Must parse note markdown to verify topics exist (may fail if note format changes)
4. **Document Answer Dependency**: Document answer comparison requires precomputed answer in message metadata
5. **Template Dependency**: Requires template content to be available (may fail if template file missing)
6. **Single Question Limit**: Can only ask one question per iteration (may slow down interview progress)

#### Example

**Input (API Request)**:
```json
{
  "user_message": "We typically run the centrifuges at 1200 RPM, but during high-brix campaigns we sometimes push to 1400 RPM to maintain throughput.",
  "session_id": 28
}
```

**Context (from interview note - read-only)**:
```markdown
## Interview Progress
- Current Topic: Centrifuge_Operations
- Status: In Progress
- Questions Completed: 1/3

## Topics to Cover

### Centrifuge_Operations
**Status**: In Progress

**Questions**:
1. [completed] What are the standard operating parameters for the centrifuges?
2. [asking] How do you adjust operations during different campaign conditions?
3. [not_asked] What are the common failure modes and how do you prevent them?
```

**Document Answer (precomputed, in message metadata)**:
```
"Standard centrifuge speed is 1200 RPM. Manual recommends not exceeding 1350 RPM to prevent bearing wear."
```

**Agent Processing (tool loop)**:

*Iteration 1 - Analyze answer and decide next action:*
```xml
<thinking>
Intent: User shared operational knowledge about centrifuge speeds
Context: Current topic is Centrifuge_Operations, 2 topics total in note. Question 2 [asking] about campaign adjustments.
Topic Count: 1 topic (Centrifuge_Operations) with 3 questions
Question Status Check: Question 2 is [asking], not [completed] - valid to continue
Decision: User mentioned 1400 RPM during high-brix, document says max 1350 RPM - significant difference, ask followup
Understanding: User operates at 1200 RPM normally, increases to 1400 RPM for high-brix campaigns
</thinking>

<ask_question>
  <preface>So you normally run at 1200 RPM but push to 1400 RPM during high-brix campaigns to maintain throughput. That's interesting because it exceeds the documented 1350 RPM limit - this suggests there's operational experience here that goes beyond the manual.</preface>
  <question>When you run at 1400 RPM, have you noticed any impact on bearing life or maintenance frequency?</question>
  <category>followup</category>
  <workflow_phase>knowledge_capture</workflow_phase>
</ask_question>
```

**Output (API Response)**:
```json
{
  "agent_response": "So you normally run at 1200 RPM but push to 1400 RPM during high-brix campaigns to maintain throughput. That's interesting because it exceeds the documented 1350 RPM limit - this suggests there's operational experience here that goes beyond the manual.\n\nWhen you run at 1400 RPM, have you noticed any impact on bearing life or maintenance frequency?",
  "internal_conversation": [...],
  "workflow_completed": false,
  "metadata": {
    "question_category": "followup",
    "current_topic": "Centrifuge_Operations",
    "questions_completed": 1,
    "questions_total": 3
  }
}
```

**Subsequent Turn - After user answers followup, continue with next template question:**

*User Input*: "Yes, we do see about 15% more bearing replacements, but the throughput gain justifies it during peak season."

*Agent Response (moves to question 3)*:
```xml
<thinking>
Intent: User confirmed bearing impact but justified by throughput gain
Context: Question 2 followup answered, should move to question 3 [not_asked]
Topic Count: 1 topic, question 3 remaining
Question Status Check: Question 3 is [not_asked] - valid to ask
Decision: ask_question with category interview_note for question 3
Understanding: 15% more bearing replacements accepted as trade-off for throughput
</thinking>

<ask_question>
  <preface>That's a valuable trade-off insight - 15% more bearing replacements is a known cost for maintaining peak season throughput. We've captured the operating parameters and campaign adjustments for centrifuges.</preface>
  <question>What are the common failure modes you encounter with the centrifuges, and what preventive measures do you take?</question>
  <category>interview_note</category>
  <workflow_phase>knowledge_capture</workflow_phase>
</ask_question>
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-08 | Lam Nguyen | Initial AS-IS documentation for v2 endpoint agents |

