# Knowledge Operations Handler

## Overview
Stateless handler for knowledge generation workflows that manages domain knowledge tree exploration, user interactions, and knowledge artifact generation.

## Core Design Principles

### 1. Tool Simplicity & Single Responsibility
- **Each tool has ONE clear purpose** - avoid feature creep
- **Tools are stateless** - all state comes from tree structure and status files
- **No redundant tools** - if two tools do similar things, merge them
- **Intelligence comes from LLM usage**, not complex tool logic

### 2. Workflow Efficiency
- **Minimize redundant operations** - if tree was just explored, don't re-analyze it
- **Direct responses when appropriate** - not everything needs a workflow
- **Smart tool selection** - LLM should pick the right tool based on context
- **User-centric interactions** - ask only when genuinely needed

### 3. Parameter Design
- **Zero parameters when possible** - tools auto-determine context
- **Avoid mutable defaults** - use `None` not `[]` for optional lists
- **Semantic clarity** - parameter names should be self-explanatory
- **No redundant parameters** - don't pass what the tool already knows

## Current Tool Architecture

### Core Tools (6 total - keep it minimal!)

1. **ExploreKnowledgeTool**
   - Shows full tree hierarchy with status indicators (✅/⏳/❌)
   - Includes artifact counts for each topic
   - Replaces check_existing functionality
   - Output guides toward using ask_question for next steps

2. **AskQuestionTool** 
   - Unified tool for ALL user interactions (questions + approvals)
   - Auto-detects approval questions and formats appropriately
   - LLM should reference available tool capabilities when asking
   - Example: "From GenerateKnowledgeTool, I can: generate single (2-3 min) or all_leaves (4-5 min)"

3. **GenerateKnowledgeTool**
   - Modes: "single" (one topic) or "all_leaves" (bulk generation)
   - Checks status before generating (skips if status == "success")
   - Handles persistence automatically
   - Domain/role/task aware for contextual generation

4. **ModifyTreeTool**
   - Add/remove/reorganize tree nodes
   - Saves changes to disk automatically
   - Triggers tree reload in handler

5. **ValidateTool**
   - Quality checks on generated knowledge
   - Ensures completeness and accuracy

6. **AttemptCompletionTool**
   - Handles BOTH workflow completion AND direct information responses
   - Detects completion vs info based on summary content
   - Use for "What can I do?" type questions

## Critical Implementation Details

### Avoid These Pitfalls

1. **Mutable Default Arguments**
   ```python
   # ❌ WRONG - causes parameter validation failures
   def _execute(self, question: str, options: list[str] = []):
   
   # ✅ CORRECT
   def _execute(self, question: str, options: list[str] = None):
   ```

2. **Redundant Tools**
   - Don't create KnowledgeApprovalTool when AskQuestionTool exists
   - Don't separate AskApprovalTool and AskFollowUpQuestionTool
   - Tools should be orthogonal, not overlapping

3. **Stale References**
   - When removing a tool, grep for ALL references and update them
   - Check tool descriptions, prompts, and inline documentation
   - Example: Removing knowledge_approval requires updating ExploreKnowledgeTool footer

4. **Over-rigid Prompts**
   ```python
   # ❌ WRONG - too prescriptive
   "RULE 1: Always use X before Y"
   
   # ✅ CORRECT - principles-based
   "PRINCIPLE: Accomplish the user's request efficiently"
   ```

## Typical Workflow Patterns

### Knowledge Generation Flow
```
User: "What can I do with you?"
  ↓
LLM: explore_knowledge(query="all", depth=3)
  ↓ (sees tree with status indicators)
LLM: ask_question(
  question="Based on 6 topics shown (3✅, 2⏳, 1❌), how to proceed?
            - Generate single topic (2-3 min)
            - Generate all pending (4-5 min)
            - Retry failed topics",
  options=["single", "all pending", "retry failed", "cancel"]
)
  ↓
User: "all pending"
  ↓
LLM: generate_knowledge(mode="all_leaves")
```

### Direct Information Flow
```
User: "What can I do with you?"
  ↓
LLM: attempt_completion(
  summary="You can explore domain knowledge, generate knowledge 
           artifacts (facts, procedures, heuristics), modify the 
           knowledge tree, and validate quality."
)
```

## Status Tracking

Knowledge generation status stored in `knowledge_status.json`:
```json
{
  "Topic Name": "success|failed|in_progress",
  "Current Ratio": "success",
  "Balance Sheet": "in_progress"
}
```

Visual indicators in exploration:
- ✅ = successfully generated
- ⏳ = in progress/pending
- ❌ = failed (needs retry)
- (N artifacts) = count of generated knowledge

## Handler Responsibilities

1. **Tree Management**
   - Load tree from domain_knowledge.json
   - Reload after modifications
   - Update tool references on reload

2. **Tool Orchestration**
   - Initialize tools with tree/status/storage paths
   - Run tool selection loop with LLM
   - Handle tool execution and result formatting

3. **Conversation Management**
   - Maintain stateless conversation history
   - Format tool results for LLM consumption
   - Detect completion conditions

## Best Practices

### For Tool Development

1. **Start with _execute method signature**
   - Define parameters clearly
   - Use type hints
   - Avoid mutable defaults

2. **Write comprehensive tool descriptions**
   - Include when to use AND when NOT to use
   - Reference other tools for workflow guidance
   - Provide concrete examples

3. **Handle edge cases gracefully**
   - Missing tree structure
   - Empty results
   - Invalid parameters

### For LLM Prompting

1. **Use principles over rules**
   - Guide toward efficiency and user satisfaction
   - Allow flexible decision-making
   - Trust LLM intelligence

2. **Leverage tool knowledge**
   - When using ask_question, reference other tool capabilities
   - Build on previous tool results (especially exploration)
   - Avoid redundant operations

3. **Provide context in questions**
   - Include counts, status indicators, time estimates
   - Reference specific tool parameters and modes
   - Give users clear, actionable options

## Common Issues & Solutions

| Issue | Root Cause | Solution |
|-------|------------|----------|
| Tool fails repeatedly | Mutable default arguments | Use `None` instead of `[]` |
| LLM picks wrong tool | Stale tool descriptions | Update descriptions when removing tools |
| Redundant tree analysis | Multiple similar tools | Merge tools, reference previous results |
| Rigid workflow | Over-prescriptive prompts | Use principles-based guidance |
| Parameter validation errors | Type mismatches | Ensure schema matches _execute signature |

## Testing Checklist

- [ ] All tools work with minimal parameters
- [ ] No references to removed tools
- [ ] Mutable defaults eliminated
- [ ] Tool descriptions accurate and current
- [ ] LLM can complete full workflow
- [ ] Direct responses work for info questions
- [ ] Status tracking updates correctly
- [ ] Tree reloads after modifications

## Future Considerations

- Keep tool count minimal (current: 6)
- Resist adding specialized tools - enhance existing ones
- Let LLM intelligence drive workflow, not rigid rules
- Monitor for redundant operations and eliminate them
- Maintain single responsibility principle