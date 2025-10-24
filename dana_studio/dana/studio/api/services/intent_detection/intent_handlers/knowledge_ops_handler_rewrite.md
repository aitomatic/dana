# Knowledge Operations Handler - Implementation Guide

## Objective
Create a stateless knowledge generation workflow handler with minimal, efficient tools that leverages LLM intelligence rather than complex tool logic.

## Critical Requirements

### Tool Architecture (EXACTLY 6 tools - no more!)

1. **ExploreKnowledgeTool**
   - Display full tree with visual status (✅ success, ⏳ pending, ❌ failed)
   - Show artifact counts: "Topic Name ✅ (5 artifacts)"
   - Footer must reference ask_question (not knowledge_approval)

2. **AskQuestionTool**  
   - Handle ALL user interactions (questions + approvals)
   - **CRITICAL**: Use `options: list[str] = None` NOT `[]` (mutable default bug!)
   - Auto-detect approval questions by keywords
   - Description must encourage use for knowledge generation decisions

3. **GenerateKnowledgeTool**
   - Two modes: "single" or "all_leaves"
   - Skip topics with status == "success"
   - Domain/role/tasks aware

4. **ModifyTreeTool**
   - Add/remove nodes
   - Auto-save and trigger reload

5. **ValidateTool**
   - Quality checks

6. **AttemptCompletionTool**
   - Detect completion vs information based on content
   - Handle "What can I do?" with direct answers

### Implementation Constraints

**DO NOT CREATE:**
- ❌ KnowledgeApprovalTool (redundant with AskQuestionTool)
- ❌ Separate approval/follow-up tools (merge into AskQuestionTool)
- ❌ CheckExistingTool (merge into ExploreKnowledgeTool)
- ❌ Any tool that duplicates existing functionality

**PARAMETER RULES:**
```python
# NEVER use mutable defaults
def _execute(self, options: list[str] = None):  # ✅ CORRECT
def _execute(self, options: list[str] = []):    # ❌ CAUSES FAILURES
```

**TOOL DESCRIPTIONS:**
- Never reference non-existent tools
- Guide toward next logical tool in workflow
- Include concrete usage examples

### Prompt Strategy

Use PRINCIPLES not RULES:
```python
TOOL_SELECTION_PROMPT = """
PRINCIPLES
- Efficiency First: Accomplish the user's request with minimal steps
- Smart Decisions: Choose tools based on context and previous results  
- User Focus: Ask questions only when genuinely needed

TOOL GUIDANCE
- "What can I do?" → attempt_completion OR explore_knowledge → ask_question
- After exploration → Use ask_question referencing what you learned
- LLM should craft questions that reference tool capabilities:
  "From GenerateKnowledgeTool: single topic (2-3min) or all_leaves (4-5min)"
"""
```

### Expected Workflows

**Knowledge Generation:**
```
explore_knowledge → Shows tree with ✅⏳❌
    ↓
ask_question → "Based on 6 topics shown, how to proceed? [options based on GenerateKnowledgeTool modes]"
    ↓
generate_knowledge → Execute user choice
```

**Direct Information:**
```
attempt_completion → Direct answer about capabilities
```

### File Structure

```
knowledge_ops_tools.py:
- AskQuestionTool (merged approval + questions)
- ExploreKnowledgeTool (with status indicators)
- GenerateKnowledgeTool (single/all_leaves modes)
- ModifyTreeTool
- ValidateTool  
- AttemptCompletionTool

knowledge_ops_handler.py:
- _initialize_tools() - Create all 6 tools
- _reload_tree() - Update tools after modifications
- Remove ALL references to removed tools

knowledge_ops_prompts.py:
- Principles-based guidance
- Reference ask_question not knowledge_approval
```

## Testing Requirements

1. **Parameter Test**: Verify options=None works, options=[] fails
2. **Tool Count**: Exactly 6 tools available
3. **Description Test**: No references to removed tools
4. **Workflow Test**: Full explore→ask→generate flow works
5. **Status Test**: ✅⏳❌ indicators display correctly

## Common Failure Patterns to Avoid

| Pattern | Why It Fails | Solution |
|---------|--------------|----------|
| Creating redundant tools | Confuses LLM selection | Merge similar tools |
| Mutable default arguments | Parameter validation errors | Always use None |
| Stale tool references | LLM avoids correct tools | Grep and update all |
| Rigid prompt rules | Inflexible workflows | Use principles |
| Missing status indicators | Can't see what needs generation | Add ✅⏳❌ to exploration |

## Implementation Checklist

- [ ] Merge AskApprovalTool + AskFollowUpQuestionTool → AskQuestionTool
- [ ] Remove KnowledgeApprovalTool completely
- [ ] Fix all mutable defaults to None
- [ ] Update all tool descriptions to remove stale references
- [ ] Add status indicators to ExploreKnowledgeTool
- [ ] Make AttemptCompletionTool handle both completion and info
- [ ] Update prompts to principles-based guidance
- [ ] Test full workflow end-to-end

## Success Criteria

✅ 6 tools total (no more, no less)
✅ No parameter validation failures  
✅ LLM confidently selects correct tools
✅ Efficient workflows with no redundancy
✅ Clear visual feedback with status indicators
✅ Handles both workflows and direct responses

## Key Insight

**The intelligence should come from the LLM's usage of simple tools, not from complex tool logic.** Keep tools minimal and let the LLM leverage its knowledge of tool capabilities when crafting questions and making decisions.