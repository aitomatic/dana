# Framework Specifications

Framework design specifications organized by functional categories.

## Organization

### **Knowledge Frameworks** (`knowledge/`)
Specifications for knowledge management and organization frameworks:

- **`knows_*.md`** - KNOWS (Knowledge Organization and Workflow System) specifications
  - `knows_proposal.md` - Main KNOWS framework proposal
  - `knows_proposals.md` - Additional KNOWS proposals and variations
  - `knows_ingestion.md` - Knowledge ingestion design
  - `knows_retrieval.md` - Knowledge retrieval mechanisms
  - `knows_workflow.md` - Workflow orchestration within KNOWS

- **`corral_*.md`** - CORRAL (Curate → Organize → Retrieve → Reason → Act → Learn) specifications
  - `corral_design.md` - CORRAL framework design
  - `corral_curation.md` - Knowledge curation lifecycle

### **Memory Frameworks** (`memory/`)
Specifications for memory management and context engineering frameworks:

- **`conversation_*.md`** - Conversation memory and context engineering
  - Linear conversation history with summaries
  - Context assembly for LLM interactions
  - Task-specific context engineering

### **Context Engineering Frameworks** (`ctxeng/`)
Specifications for intelligent context assembly and optimization:

- **`ctxeng.md`** - Context engineering framework specification
  - Relevance-first context assembly
  - Token optimization and length management
  - Multi-factor relevance scoring
  - Integration with agent solving system

### **Workflow Frameworks** (`workflow/`)
Specifications for workflow orchestration and function composition frameworks:

- **`pipeline_*.md`** - Function composition and pipeline specifications
  - Pipeline operator design and semantics
  - Workflow orchestration patterns

### **POET Frameworks** (`poet/`)
Specifications for function enhancement and intelligent processing frameworks:

- **`poet_*.md`** - POET (Perceive → Operate → Enforce → Train) specifications
  - `poet_design.md` - POET framework design
  - `poet_progress.md` - Development progress and milestones
  - `poet_use_cases.md` - Use cases and applications
  - `poet_*_example.md` - Domain-specific examples (financial, HVAC, ML, etc.)

## Design Philosophy

Each framework category addresses specific aspects of intelligent systems:

1. **Knowledge Frameworks** - How to organize, store, and retrieve information
2. **Memory Frameworks** - How to maintain context and conversation history
3. **Workflow Frameworks** - How to compose and orchestrate functions
4. **POET Frameworks** - How to add intelligence to existing functions

## Cross-Category Integration

These frameworks are designed to work together:

- **Knowledge** provides the foundation of information
- **Memory** maintains context and history
- **Context Engineering** optimizes context assembly and relevance
- **Workflow** orchestrates execution
- **POET** adds intelligence to each step

The combination creates a complete agentic system where knowledge flows into intelligent action and learning, with optimized context engineering ensuring efficient LLM interactions. 