# Dana Studio - Architecture & Component Design

## Metadata

| Field | Value |
|-------|-------|
| **Document Title** | Dana Studio Architecture & Component Design |
| **Version** | 1.0 |
| **Date** | 2025-12-08 |
| **Author** | Lam Nguyen |
| **Status** | Draft - AS-IS Documentation |
| **Scope** | v2 and v3 API Endpoints |
| **Deployment Model** | Docker Compose (single-node containerized) |

---

## 1. Context Diagram

### System Overview

Dana Studio is a web-based IDE for building and managing domain-aware neurosymbolic agents. The system provides a React-based frontend interface and a FastAPI backend that orchestrates knowledge capture, agent training, and document processing workflows.

### Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Dana Studio System                       │
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────────────────┐  │
│  │   Frontend UI    │◄───────►│      API Server (FastAPI)   │  │
│  │   (React SPA)    │  HTTP  │                              │  │
│  └──────────────────┘         │  ┌──────────────────────┐  │  │
│                                │  │   v2 API Routers     │  │  │
│                                │  │   - Knowledge Pack   │  │  │
│                                │  │   - Documents        │  │  │
│                                │  │   - Agents           │  │  │
│                                │  └──────────────────────┘  │  │
│                                │  ┌──────────────────────┐  │  │
│                                │  │   v3 API Routers     │  │  │
│                                │  │   - Settings         │  │  │
│                                │  │   - Prompt Mgmt      │  │  │
│                                │  └──────────────────────┘  │  │
│                                │  ┌──────────────────────┐  │  │
│                                │  │  Background Task      │  │  │
│                                │  │  Manager             │  │  │
│                                │  └──────────────────────┘  │  │
│                                │  ┌──────────────────────┐  │  │
│                                │  │  Knowledge Pack       │  │  │
│                                │  │  Services             │  │  │
│                                │  └──────────────────────┘  │  │
│                                │  ┌──────────────────────┐  │  │
│                                │  │  Repository Layer    │  │  │
│                                │  └──────────────────────┘  │  │
│                                │  ┌──────────────────────┐  │  │
│                                │  │  Database (SQLite)   │  │  │
│                                │  └──────────────────────┘  │  │
│                                └──────────────────────────────┘  │
│                                         │                        │
└─────────────────────────────────────────┼────────────────────────┘
                                          │
                                          │ API Calls
                                          │
                          ┌───────────────▼───────────────┐
                          │      Azure OpenAI API         │
                          │  (LLM Orchestration)          │
                          └───────────────────────────────┘
```

**Placeholder Image**: `[Context Diagram Image: diagrams/context-diagram.png]`

**Description**: The context diagram shows Dana Studio as a self-contained system with a React frontend communicating with a FastAPI backend. The backend orchestrates workflows using Azure OpenAI for LLM-based tool orchestration. The system uses SQLite for persistent storage and includes background task processing for long-running operations like knowledge generation and document extraction.

**External Actors**:
- **Users**: Interact with the system via web browser
- **Azure OpenAI**: Provides LLM capabilities for tool orchestration and knowledge generation

---

## 2. Component Model

The following table describes the major components of Dana Studio, organized by architectural layer:

| Component | Type | Description | Key Responsibilities | Key Files |
|-----------|------|-------------|---------------------|-----------|
| **Frontend (React SPA)** | Presentation | Single-page application for user interaction | UI rendering, state management, API communication, WebSocket connections | `contrib/ui/src/` |
| **API Server (FastAPI)** | Application | Main HTTP/WebSocket server | Request routing, middleware, static file serving, WebSocket management | `api/server/server.py` |
| **API v2 Routers** | Application | REST API endpoints for core functionality | Knowledge pack management, document operations, agent-KP associations | `api/routers/v2/` |
| **API v3 Routers** | Application | REST API endpoints for settings and configuration | Prompt settings management, knowledge pack prompt overrides | `api/routers/v3/` |
| **Knowledge Pack Services** | Business Logic | Domain logic for knowledge capture workflows | Interview orchestration, template generation, knowledge generation, structuring | `api/services/knowledge_pack/` |
| **Background Task Manager** | Infrastructure | Asynchronous task processing | Task queuing, worker management, status tracking, concurrency control | `api/background/task_manager.py` |
| **Repository Layer** | Data Access | Data persistence abstraction | CRUD operations, query abstraction, transaction management | `api/repositories/` |
| **Database (SQLite)** | Data | Persistent storage | Data persistence, relationships, migrations | `api/core/database.py`, `api/core/models.py` |
| **LLM Resource** | External Integration | Azure OpenAI client | LLM API calls, tool orchestration, response handling | Via `dana.lang.common.sys_resource.llm` |
| **RAG Resource** | Infrastructure | Retrieval-Augmented Generation | Document indexing, semantic search, context retrieval | Via `dana.lang.common.sys_resource.rag` |
| **WebSocket Manager** | Infrastructure | Real-time communication | Status updates, progress notifications, knowledge status broadcasting | `api/core/ws_manager.py`, `api/server/server.py` |

### Component Relationships

- **Frontend** → **API Server**: HTTP REST calls and WebSocket connections
- **API Server** → **v2/v3 Routers**: Request routing and dependency injection
- **v2/v3 Routers** → **Services**: Business logic delegation
- **Services** → **Repository Layer**: Data access abstraction
- **Repository Layer** → **Database**: SQLAlchemy ORM operations
- **Services** → **LLM Resource**: Azure OpenAI API calls
- **Services** → **RAG Resource**: Document search and retrieval
- **Background Task Manager** → **Services**: Async task execution
- **API Server** → **WebSocket Manager**: Real-time status updates

---

## 3. Runtime View

This section describes the end-to-end workflows for the three main phases of knowledge capture in Dana Studio: Knowledge Pack Creation and Generation, Template Finetuning, and Interview Sessions.

---

### 3.1 Phase 1: Knowledge Pack Creation and Generation

This phase covers the creation of knowledge packs, structuring of domain knowledge trees, and generation of knowledge content from questions.

#### Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Phase 1: Knowledge Pack Workflow                   │
│                                                                 │
│  ┌──────────────┐                                               │
│  │     User     │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         │ 1. Create KP (parse doc/text)                         │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   KnowledgePackDialog (Frontend)    │                        │
│  │   - Parse document specialization   │                        │
│  │   - Create knowledge pack           │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ POST /api/v2/knowledge/create                         │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   KP Managing Router                │                        │
│  │   - Create KP in database           │                        │
│  │   - Initialize folder structure     │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ 2. Structure domain tree                               │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   KnowledgePackChatSidebar           │                        │
│  │   - Chat with KPStructuringOrch.     │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ POST /api/v2/knowledge/structure/{id}/chat            │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   KPStructuringOrchestrator         │                        │
│  │   - LLM Tool Loop (max 15 iter)     │                        │
│  │   - Tools: ExploreKnowledge,         │                        │
│  │     ModifyTree, ProposeStructure,   │                        │
│  │     QuestionBankGeneration          │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ 3. Generate knowledge                                  │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   POST /api/v2/knowledge/gen/        │                        │
│  │   {id}/generate-knowledge            │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ Background Task                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   TaskManager (KNOWLEDGE_GEN queue) │                        │
│  │   - Worker thread picks task         │                        │
│  │   - KnowledgeGenerationTool          │                        │
│  │   - LLM generates knowledge          │                        │
│  │   - Updates knowledge.json files     │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ WebSocket Status Updates                               │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   Frontend (DomainKnowledgeTree)     │                        │
│  │   - Real-time status visualization   │                        │
│  └──────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

#### Detailed Sequence

**Step 1: Knowledge Pack Creation**

1. **User Input** (`KnowledgePackDialog`)
   - User uploads document (PDF/DOCX) or enters text description
   - Frontend calls `parseDocumentSpecialization()` or `parseTextSpecialization()`
   - LLM extracts specialization: domain, role, task

2. **Knowledge Pack Creation** (`api/routers/v2/knowledge_pack/kp_managing.py`)
   - Frontend calls `POST /api/v2/knowledge/create` with specialization and document IDs
   - Router creates `KnowledgePack` record in database
   - Initializes folder structure: `{kp_folder}/domain_knowledge.json`, `{kp_folder}/knows/`
   - Returns knowledge pack ID

**Step 2: Domain Tree Structuring**

3. **Chat-Based Structuring** (`api/routers/v2/knowledge_pack/kp_structuring.py`)
   - User navigates to knowledge pack detail page
   - Frontend loads `KnowledgePackChatSidebar` component
   - User sends messages to refine domain knowledge structure

4. **LLM Tool Loop** (`api/services/knowledge_pack/structuring_handler/orchestrator.py`)
   - Router calls `POST /api/v2/knowledge/structure/{id}/chat`
   - `KPStructuringOrchestrator` initializes with domain knowledge path
   - LLM analyzes user intent and selects tools:
     - `explore_knowledge`: View current tree structure
     - `propose_knowledge_structure`: Generate new topic structure
     - `refine_knowledge_structure`: Modify proposed structure
     - `modify_tree`: Add/remove/rename nodes in `domain_knowledge.json`
     - `question_bank_generation`: Generate questions for topics
     - `preview_knowledge_topic`: Preview knowledge content
   - Tool loop runs up to 15 iterations
   - Each tool result added to conversation history
   - WebSocket notifies frontend of tree modifications

5. **Tree Visualization** (`DomainKnowledgeTree` component)
   - Frontend receives WebSocket updates
   - Reactively updates tree visualization
   - Shows topic status (draft, pending, question_generated)

**Step 3: Knowledge Generation**

6. **Trigger Generation** (`api/routers/v2/knowledge_pack/kp_generation.py`)
   - User clicks "Generate Knowledge" button
   - Frontend calls `POST /api/v2/knowledge/gen/{id}/generate-knowledge`
   - Router validates:
     - Knowledge pack exists
     - Questions exist in `knowledge.json` files (checks `knows/` folder)
     - Associated documents available

7. **Background Task Creation** (`api/background/task_manager.py`)
   - Router creates task data:
     - Knowledge pack ID
     - Storage paths (`knows/` folder, domain knowledge path)
     - Document file paths
     - Domain, role, tasks metadata
     - Template generation prompt override (from KP metadata)
   - `TaskManager.add_knowledge_gen_task()` adds to `KNOWLEDGE_GEN` queue
   - Returns task ID to frontend

8. **Background Processing**
   - Worker thread (1 concurrent worker) picks task from queue
   - Updates task status to `RUNNING` in database
   - Instantiates `KnowledgeGenerationTool` with task data

9. **Knowledge Generation** (`api/services/knowledge_pack/generation_handler/tools/knowledge_generation_tool.py`)
   - Tool loads domain knowledge tree from `domain_knowledge.json`
   - Iterates through leaf topics with questions
   - For each topic:
     - Reads questions from `knowledge.json` file
     - Calls Azure OpenAI with:
       - Question text
       - Document context (RAG search)
       - Domain/role context
     - Generates knowledge entries
     - Updates `knowledge_status.json` with status
     - Writes/updates `knowledge.json` file
   - Updates knowledge pack status to `COMPLETED`

10. **Status Updates**
    - Task status updated to `COMPLETED` in database
    - WebSocket broadcasts status updates (`kp_generation_ws_notifier`)
    - Frontend receives real-time progress via `useKnowledgePackWebSocket` hook
    - `DomainKnowledgeTree` component updates node statuses

**Key Design Decisions**:
- **Conversational Structuring**: LLM-driven tool loop allows natural language interaction for tree refinement
- **Asynchronous Generation**: Background tasks prevent API timeouts for long-running knowledge generation
- **Dual State Tracking**: Both database (task status) and file system (`knowledge_status.json`) track progress
- **Concurrency Control**: Single worker for knowledge generation prevents resource exhaustion
- **WebSocket Integration**: Real-time status updates improve UX for long-running operations
- **Question-First Approach**: Knowledge generation requires pre-generated questions, ensuring structured output

**Component Interactions**:
- **Frontend**: `KnowledgePackDialog` → `KnowledgePackDetailPage` → `KnowledgePackChatSidebar` + `DomainKnowledgeTree`
- **Backend**: `kp_managing.py` → `kp_structuring.py` → `kp_generation.py`
- **Services**: `KPStructuringOrchestrator` (LLM tool loop) → `KnowledgeGenerationTool` (background processing)
- **Infrastructure**: `TaskManager` (queue management) → WebSocket managers (status broadcasting)

---

### 3.2 Phase 2: Template Finetuning

This phase covers the creation and refinement of interview templates used for knowledge capture sessions.

#### Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│            Phase 2: Template Finetuning Workflow               │
│                                                                 │
│  ┌──────────────┐                                               │
│  │     User     │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         │ 1. Create template from KP                            │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   ContributionTemplatesTab          │                        │
│  │   - Create/duplicate template        │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ POST /api/v2/knowledge/template/create                 │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   KP Interview Template Router      │                        │
│  │   - Duplicate from master template  │                        │
│  │   - Copy folder structure           │                        │
│  │   - Create template record          │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ 2. Finetune template                                   │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   ContributionTemplatePage           │                        │
│  │   - Chat sidebar (left panel)         │                        │
│  │   - Template panel (right panel)     │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ POST /api/v2/knowledge/template/{id}/chat             │
│         │ (mode: chat | editor | auto)                           │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   Mode Detection (LLM)               │                        │
│  │   - Analyze user intent              │                        │
│  │   - Detect: chat vs editor mode       │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│    ┌────┴───────────────┐                                        │
│    │                    │                                        │
│    ▼                    ▼                                       │
│  ┌──────────┐ ┌──────────────────────────┐                     │
│  │   CHAT   │ │        EDITOR            │                     │
│  │   Mode   │ │        Mode              │                     │
│  └────┬─────┘ └──────────┬───────────────┘                     │
│       │                  │                                      │
│       │                  │                                      │
│       ▼                  ▼                                      │
│  ┌──────────────────┐ ┌──────────────────────────┐             │
│  │ DocumentExplor.  │ │ TemplateModification     │             │
│  │ Handler          │ │ Handler                 │             │
│  │ - ReadDocuments  │ │ - ViewTemplate          │             │
│  │ - AskQuestion    │ │ - ReplaceInFile         │             │
│  │ - AttemptCompl.  │ │ - AskQuestion           │             │
│  └──────────────────┘ │ - AttemptCompletion     │             │
│                       └──────────┬───────────────┘             │
│                                  │                              │
│                                  │ Updates README.md            │
│                                  ▼                              │
│                       ┌──────────────────────────┐             │
│                       │   Template File System   │             │
│                       │   - README.md            │             │
│                       │   - system_prompt.prompt │             │
│                       └──────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

#### Detailed Sequence

**Step 1: Template Creation**

1. **Template Creation** (`api/routers/v2/knowledge_pack/kp_interview_template.py`)
   - User navigates to knowledge pack's "Capture Templates" tab
   - Frontend calls `POST /api/v2/knowledge/template/create`
   - Router duplicates from master template (or existing template if `source_template_id` provided)
   - Copies folder structure: `{template_folder}/README.md`, `{template_folder}/system_prompt.prompt`
   - Creates `InterviewTemplate` record in database
   - Returns template ID

**Step 2: Template Finetuning**

2. **Open Template** (`ContributionTemplatePage`)
   - User navigates to template detail page (`/contribution-template/{templateId}`)
   - Frontend loads template data via `GET /api/v2/knowledge/template/{id}`
   - Loads conversation history via `GET /api/v2/knowledge/template/{id}/conversation`
   - Displays split view: chat sidebar (left) + template preview (right)

3. **Mode Detection** (`api/routers/v2/knowledge_pack/kp_interview_template.py`)
   - User sends message via chat input
   - Router calls `detect_chat_mode()` function (if mode is `auto`)
   - LLM analyzes user intent:
     - **CHAT mode**: User wants to explore documents, ask questions, refine drafts
     - **EDITOR mode**: User explicitly wants to modify template file
   - Returns detected mode: `"chat"` or `"editor"`

4. **Chat Mode - Document Exploration** (`api/services/knowledge_pack/document_handler/document_exploration_handler.py`)
   - If mode is `chat`, router instantiates `DocumentExplorationHandler`
   - Handler initializes RAG resource from knowledge pack documents
   - LLM tool loop (max 15 iterations):
     - `read_documents`: List or read document content via RAG
     - `ask_question`: Ask clarifying questions
     - `attempt_completion`: Provide insights and suggestions
   - Handler returns conversation with document insights
   - Frontend displays response in chat sidebar

5. **Editor Mode - Template Modification** (`api/services/knowledge_pack/template_handler/template_modification_handler.py`)
   - If mode is `editor`, router instantiates `TemplateModificationHandler`
   - Handler reads current template content (`README.md`)
   - LLM tool loop (max 15 iterations):
     - `view_template`: View template sections
     - `replace_in_file`: Modify template content (search/replace operations)
     - `ask_question`: Request user approval for changes
     - `attempt_completion`: Signal completion
   - Handler writes modified content to `README.md`
   - Returns `template_modified=True` and `template_diff` (if changes made)
   - Frontend animates template changes using diff visualization

6. **System Prompt Management**
   - User can edit system prompt via `SystemPromptPanel`
   - Frontend calls `PATCH /api/v2/knowledge/template/{id}/system-prompt`
   - Router writes content to `system_prompt.prompt` file
   - System prompt used during interview sessions

**Step 3: Template Completion**

7. **Mark Template Complete**
   - User marks template as "completed" when ready
   - Frontend calls `PUT /api/v2/knowledge/template/{id}` with `template_metadata.status='completed'`
   - Template becomes available for creating interview sessions

**Key Design Decisions**:
- **Dual Handler Pattern**: Separate handlers for document exploration vs template modification
- **Mode Auto-Detection**: LLM analyzes user intent to route to appropriate handler
- **Stateless Handlers**: Both handlers use conversation history as state (no complex state management)
- **File-Based Templates**: Templates stored as markdown files (`README.md`) for easy versioning
- **Diff Visualization**: Frontend shows animated diffs when template modified in editor mode
- **Conversation Persistence**: All template conversations stored in database for context

**Component Interactions**:
- **Frontend**: `ContributionTemplatePage` → `ChatSidebar` + `TemplatePanel` + `SystemPromptPanel`
- **Backend**: `kp_interview_template.py` → `detect_chat_mode()` → `DocumentExplorationHandler` or `TemplateModificationHandler`
- **Services**: Handlers use LLM tool loop with specialized tools
- **Storage**: Template files (`README.md`, `system_prompt.prompt`) + database records

---

### 3.3 Phase 3: Interview Session

This phase covers the execution of knowledge capture interviews using LLM-driven question generation and expert insight extraction.

#### Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Phase 3: Interview Session Workflow               │
│                                                                 │
│  ┌──────────────┐                                               │
│  │     User     │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         │ 1. Create session from template                       │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   ContributionTemplatePage           │                        │
│  │   - "Start Expert Interview" button  │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ POST /api/v2/knowledge/session/create                 │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   KP Interview Session Router        │                        │
│  │   - Create session record            │                        │
│  │   - Initialize interview_notes.md    │                        │
│  │   - Create conversation              │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ 2. Conduct interview                                   │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   CaptureKnowledgePage               │                        │
│  │   - Chat sidebar (left panel)         │                        │
│  │   - Summary panel (right panel)       │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ POST /api/v2/knowledge/session/{id}/chat              │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   InterviewQuestionHandler          │                        │
│  │   - LLM analyzes note state          │                        │
│  │   - Generates next question          │                        │
│   │   - Updates question statuses        │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ Background Tasks                                      │
│         │                                                        │
│    ┌────┴────┐                                                  │
│    │         │                                                  │
│    ▼         ▼                                                  │
│  ┌──────────┐ ┌──────────────────────────┐                     │
│  │ Document │ │  Expert Insights Update  │                     │
│  │ Answer   │ │                         │                     │
│  │ Precomp. │ │  - Analyze conversation  │                     │
│  │          │ │  - Extract insights       │                     │
│  │          │ │  - Update note            │                     │
│  └──────────┘ └──────────────────────────┘                     │
│         │                                                        │
│         │ 3. Track progress                                     │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   GET /api/v2/knowledge/session/     │                        │
│  │   {id}/progress                      │                        │
│  │   - Parse interview_notes.md         │                        │
│  │   - Calculate topic completeness     │                        │
│  │   - Return progress data             │                        │
│  └──────┬───────────────────────────────┘                        │
│         │                                                        │
│         │ 4. Export notes                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                        │
│  │   GET /api/v2/knowledge/session/    │                        │
│  │   {id}/download-interview-note      │                        │
│  │   - Returns markdown file            │                        │
│  └──────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

#### Detailed Sequence

**Step 1: Session Creation**

1. **Create Session** (`api/routers/v2/knowledge_pack/kp_interview_session.py`)
   - User clicks "Start Expert Interview" on completed template
   - Frontend calls `POST /api/v2/knowledge/session/create`
   - Router:
     - Creates `InterviewSession` record in database
     - Creates session folder: `{template_folder}/sessions/session_{id}/`
     - Calls `_initialize_interview_session()`:
       - Reads template `README.md`
       - Uses LLM to generate structured `interview_notes.md` from template
       - Filters topics to only include those with numbered questions
       - Creates note with topics, questions, and status tracking
     - Creates conversation record (type: `INTERVIEW_SESSION`)
     - Returns session ID

**Step 2: Interview Execution**

2. **Initialize RAG** (`kp_interview_session.py`)
   - Router calls `_initialize_rag_from_kp()`:
     - Collects sources: `knows/` folder + associated documents
     - Initializes `RAGResourceV2` with all sources
     - Returns RAG resource for document search

3. **Chat Endpoint** (`POST /api/v2/knowledge/session/{id}/chat`)
   - User sends message (answer to question or new query)
   - Router:
     - Loads session and template data
     - Gets or creates conversation
     - Reads current `interview_notes.md` content
     - Initializes `InterviewQuestionHandler`:
       - `kp_id`: Knowledge pack ID
       - `template_path`: Template README.md path
       - `rag_docs`: RAG resource for document search
       - `domain`, `role`: From template metadata

4. **Question Generation** (`api/services/knowledge_pack/interview_question_handler/interview_question_handler.py`)
   - Handler receives `current_note_content` (interview notes markdown)
   - LLM analyzes:
     - Current note state (topics, question statuses)
     - Conversation history (last 10 messages)
     - User's latest response
   - Handler uses tools:
     - `ask_question`: Generate next question (category: `interview_note`, `followup`, or `normal`)
     - `attempt_completion`: Signal interview completion
   - LLM selects appropriate question based on:
     - Topic completion status
     - Question statuses (`[not_asked]`, `[asking]`, `[clarifying]`, `[completed]`)
     - Template coverage
   - Handler returns question with category and metadata

5. **Question Status Updates** (`kp_interview_session.py`)
   - Router uses `InterviewNoteProcessor` to update question statuses:
     - `mark_question_as_asking`: When question first asked
     - `mark_question_as_clarifying`: When followup question asked
     - `mark_question_as_completed`: When user answers and next question asked
   - Updates `interview_notes.md` with status markers
   - Recalculates topic progress (completeness percentage)

6. **Background Tasks**

   **Document Answer Precomputation**:
   - When `interview_note` question asked, router triggers background task
   - `_precompute_document_answer_background()`:
     - Uses `ReadDocumentsTool` to search documents via RAG
     - Uses LLM to synthesize answer from document results
     - Stores answer in message metadata
   - Answer available for followup questions

   **Expert Insights Update**:
   - When question marked as completed, router triggers background task
   - `_update_expert_insights_background()`:
     - Analyzes conversation messages for topic
     - Uses LLM to extract expert insights
     - Merges with existing insights (preserves existing, adds new)
     - Updates `interview_notes.md` with consolidated insights

7. **Progress Tracking** (`GET /api/v2/knowledge/session/{id}/progress`)
   - Frontend polls progress endpoint periodically
   - Router:
     - Parses `interview_notes.md` using `parse_interview_note()`
     - Analyzes conversation messages for question statuses
     - Calculates topic completeness percentages
     - Returns `InterviewProgressData`:
       - Topics with completion status
       - Question statuses per topic
       - Overall completeness percentage
   - Frontend displays progress in `SummaryPanel` component

**Step 3: Session Completion**

8. **Workflow Completion**
   - Handler detects completion via `attempt_completion` tool
   - Router updates session status to `"completed"` in database
   - Frontend shows completion message

9. **Export Interview Notes** (`GET /api/v2/knowledge/session/{id}/download-interview-note`)
   - User clicks download button
   - Router:
     - Reads `interview_notes.md` file
     - Removes sections from "## Documents Found" onwards
     - Returns markdown file as download
   - User receives clean interview notes for review

**Key Design Decisions**:
- **Note-Based State**: Interview notes (`interview_notes.md`) serve as persistent state between tool calls
- **Question Status Tracking**: Bracket notation (`[completed]`, `[asking]`) tracks question lifecycle
- **Background Processing**: Document answers and expert insights computed asynchronously to avoid blocking
- **RAG Integration**: Documents searched via RAG to provide context for questions
- **Category-Based Questions**: Questions categorized as `interview_note`, `followup`, or `normal` for different purposes
- **Progress Calculation**: Topic completeness calculated from question statuses and conversation analysis
- **Stateless Handler**: Handler receives note content as parameter, no complex state management

**Component Interactions**:
- **Frontend**: `CaptureKnowledgePage` → `ChatSidebar` + `SummaryPanel` + `EnhancedProgressNotes`
- **Backend**: `kp_interview_session.py` → `InterviewQuestionHandler` + background tasks
- **Services**: Handler uses LLM to generate questions based on note state
- **Infrastructure**: RAG resource (document search) + background tasks (answer precomputation, insights update)
- **Storage**: Interview notes (`interview_notes.md`) + conversation messages (database)

---

## 4. Multi-Agent Orchestration Overview

### Pattern: LLM Tool Loop

Dana Studio uses an **LLM Tool Loop** orchestration pattern where a single LLM (via Azure OpenAI) orchestrates workflows through tool calls. This pattern is implemented in handlers like `InterviewHandler` and `KnowledgeGenerationTool`.

### Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Tool Loop Pattern                     │
│                                                              │
│  ┌──────────────┐                                            │
│  │   LLM Agent  │  (Azure OpenAI)                           │
│  │  Orchestrator│                                            │
│  └──────┬───────┘                                            │
│         │                                                     │
│         │ XML Tool Calls                                      │
│         │                                                     │
│    ┌────▼──────────────────────────────────────┐            │
│    │         Available Tools                   │            │
│    │  ┌────────────────────────────────────┐  │            │
│    │  │ ViewNoteTool                       │  │            │
│    │  │ UpdateNoteTool                     │  │            │
│    │  │ DocumentSearchTool                 │  │            │
│    │  │ AskQuestionTool                    │  │            │
│    │  │ AttemptCompletionTool               │  │            │
│    │  └────────────────────────────────────┘  │            │
│    └──────────────────────────────────────────┘            │
│                                                              │
│  Loop:                                                       │
│  1. LLM analyzes conversation context                       │
│  2. LLM selects and calls appropriate tool                  │
│  3. Tool executes and returns result                       │
│  4. Result added to conversation                           │
│  5. Repeat until completion or max iterations              │
└──────────────────────────────────────────────────────────────┘
```

### Communication Channels

1. **Tool Call Format**: XML-based tool invocation
   ```xml
   <thinking>Analysis of current state...</thinking>
   <tool_name>
     <param1>value1</param1>
     <param2>value2</param2>
   </tool_name>
   ```

2. **Tool Execution**: Tools execute synchronously and return structured results
   - Success: Tool result with content
   - User Input Required: Tool result with `require_user=True` flag
   - Error: Error message in conversation

3. **Conversation Context**: Full conversation history maintained for LLM decision-making
   - Last 10 messages used for context (configurable)
   - Includes user messages, tool calls, and tool results

### Termination Conditions

The LLM Tool Loop terminates when:

1. **Completion Tool Called**: `AttemptCompletionTool` indicates workflow completion
2. **Max Iterations Reached**: Default limit of 15 iterations prevents infinite loops
3. **User Input Required**: Tool sets `require_user=True`, pausing workflow until user responds
4. **Error Condition**: Unrecoverable error in tool execution

### Example: Interview Handler Workflow

The `InterviewHandler` (`api/services/knowledge_pack/interview_handler/interview_handler.py`) demonstrates this pattern:

1. **Initialization**: Creates interview note from template using LLM
2. **Tool Loop**: LLM orchestrates interview by:
   - Viewing current interview note state
   - Searching documents for context
   - Updating note with expert insights
   - Asking questions when needed
   - Attempting completion when sufficient knowledge captured
3. **State Management**: Interview note (`interview_notes.md`) persists state between tool calls
4. **Completion**: `AttemptCompletionTool` signals successful knowledge capture

### Key Characteristics

- **Single Orchestrator**: One LLM makes all decisions
- **Tool-Based Actions**: All actions performed through tool calls
- **Stateful Workflows**: Tools maintain state (files, notes) between calls
- **Flexible Termination**: Multiple termination conditions support different workflow types
- **Error Handling**: Errors are captured in conversation and can be recovered

### Advantages

- **Simplicity**: Single LLM simplifies orchestration logic
- **Flexibility**: LLM can adapt tool selection based on context
- **Transparency**: Tool calls visible in conversation for debugging
- **Extensibility**: New tools can be added without changing orchestration logic

### Limitations

- **Latency**: Multiple LLM calls increase response time
- **Cost**: Each tool decision requires LLM API call
- **Consistency**: LLM decisions may vary between runs
- **Max Iterations**: Hard limit prevents very long workflows

---

## 5. Technology Stack

The following table details the technology stack used in Dana Studio:

| Layer | Technology | Version | Purpose | Notes |
|-------|------------|---------|---------|-------|
| **Frontend Framework** | React | 19.1.0 | UI framework | Modern React with hooks |
| **Frontend Build** | Vite | 7.0.0 | Build tool | Fast build and HMR |
| **UI Components** | Radix UI | Latest | Accessible components | Headless UI primitives |
| **Styling** | Tailwind CSS | 4.1.5 | Utility-first CSS | Responsive design |
| **State Management** | Zustand | 5.0.6 | State management | Lightweight store |
| **HTTP Client** | Axios | 1.10.0 | API communication | REST API calls |
| **WebSocket** | react-use-websocket | 4.13.0 | Real-time communication | WebSocket hooks |
| **Backend Framework** | FastAPI | Latest | Web framework | Async Python framework |
| **ASGI Server** | Uvicorn | Latest | Application server | ASGI-compliant server |
| **ORM** | SQLAlchemy | Latest | Database ORM | Object-relational mapping |
| **Database** | SQLite | Latest | Relational database | File-based database |
| **Migrations** | Alembic | 1.16.5+ | Schema migrations | Database versioning |
| **LLM Integration** | Azure OpenAI | Latest | LLM provider | GPT models via Azure |
| **LLM SDK** | OpenAI SDK | 1.55.3+ | OpenAI client | Azure OpenAI support |
| **RAG Framework** | LlamaIndex | Latest | RAG capabilities | Document indexing/search |
| **Document Processing** | PyMuPDF | 1.25.3+ | PDF processing | PDF text extraction |
| **Document Processing** | docx2txt | 0.9+ | DOCX processing | Word document extraction |
| **Image Processing** | Pillow | 11.1.0+ | Image manipulation | Image handling |
| **Computer Vision** | OpenCV | 4.11.0.86+ | Image processing | Advanced image ops |
| **Logging** | Python logging | Built-in | Application logging | Basic Python logging |
| **Configuration** | python-dotenv | Latest | Environment config | .env file support |
| **Data Validation** | Pydantic | Latest | Data validation | Request/response models |
| **WebSocket Server** | FastAPI WebSocket | Built-in | WebSocket support | Real-time updates |
| **Background Tasks** | Threading | Built-in | Async processing | Python threading |
| **Package Management** | uv | Latest | Dependency management | Fast Python package manager |

### Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| **Type Checking** | TypeScript 5.8.3 | Frontend type safety |
| **Linting** | ESLint 9.29.0 | Frontend code quality |
| **Linting** | Ruff 0.13.0+ | Python code quality |
| **Testing** | Vitest 3.2.4 | Frontend testing |
| **Testing** | pytest | Python testing |
| **Code Formatting** | Prettier 3.6.2 | Frontend formatting |
| **Code Formatting** | Black | Python formatting |

### Deployment

| Component | Technology | Notes |
|-----------|------------|-------|
| **Containerization** | Docker | Single-node deployment |
| **Orchestration** | Docker Compose | Local/development deployment |
| **Process Manager** | Uvicorn | ASGI server for FastAPI |
| **Static Files** | FastAPI StaticFiles | Serves React build |

### External Services

| Service | Provider | Purpose |
|---------|----------|---------|
| **LLM API** | Azure OpenAI | Language model inference |
| **Embeddings** | Azure OpenAI | Vector embeddings for RAG |

---

## 6. Architectural Constraints & Decisions

### Deployment Model

- **Current**: Docker Compose for single-node containerized deployment
- **Database**: SQLite file-based database (suitable for single-node)
- **Scaling**: Vertical scaling within single container (not designed for horizontal scaling)

### External Dependencies

- **Azure OpenAI**: Required for LLM orchestration and knowledge generation
- **No External Vector DB**: Uses LlamaIndex with local/embedded vector storage
- **No Cloud Storage**: Documents stored in local file system

### Non-Functional Requirements

- **Latency**: Optimized for low-latency chat interactions (primary driver)
- **Concurrency**: Background tasks limit concurrency (1 worker per task type)
- **Observability**: Basic Python logging (no structured logging or APM)
- **Resilience**: Error handling in tool execution, retry logic in background tasks

### Design Decisions

1. **SQLite over PostgreSQL**: Chosen for simplicity and single-node deployment
2. **Background Tasks over Async Workers**: Python threading for background processing (simpler than Celery/RQ)
3. **File-based State**: Knowledge packs stored in file system alongside database metadata
4. **LLM Tool Loop**: Single LLM orchestrator simplifies workflow management
5. **v2/v3 API Versioning**: Clear separation of concerns, v3 focuses on settings/configuration

---

## 7. Future Considerations

### Potential Improvements

- **Horizontal Scaling**: Migrate to PostgreSQL and Redis for multi-node deployment
- **Structured Logging**: Implement JSON logging with correlation IDs
- **Observability**: Add OpenTelemetry for distributed tracing
- **Vector Database**: External vector DB (Pinecone/Weaviate) for production RAG
- **Cloud Storage**: S3/GCS integration for document storage
- **Message Queue**: Replace threading with proper message queue (RabbitMQ/Kafka)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-08 | Lam Nguyen | Initial AS-IS documentation for v2/v3 endpoints |

