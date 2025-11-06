# Semiconductor Yield Analysis Demos

## 🚀 Quick Start

### **NEW: Interactive Conversational Demo** ⭐ (Recommended)

```bash
python run_interactive_demo.py
```

Start a natural conversation with the AI yield analyst. Ask questions, request analysis, explore data interactively.

See [INTERACTIVE_DEMO_GUIDE.md](./INTERACTIVE_DEMO_GUIDE.md) for full guide.

---

### Automated Pattern Comparison Demos

Run all three demos with the same task to see the differences:

```bash
# (A) Automation - No intelligence, fixed sequence
python run_a_automation_demo.py

# (B) Probabilistic Autonomy - Agent decides, might skip steps
python run_b_probabilistic_autonomy_demo.py

# (C) Deterministic Autonomy - Agent decides, workflows guarantee completeness ⭐
python run_c_deterministic_autonomy_demo.py
```

## What Each Demo Shows

### (A) `run_a_automation_demo.py` - AUTOMATION
**Key characteristic**: Fixed sequence, no decisions

Shows pure automation:
- Runs Pareto → Correlation → ROI (always, in order)
- No LLM makes decisions
- Fast and predictable
- ❌ No adaptation, might waste effort

### (B) `run_b_probabilistic_autonomy_demo.py` - PROBABILISTIC AUTONOMY
**Key characteristic**: Agent decides, but might skip important steps

Shows flexible but risky approach:
- Agent decides: "Do I need correlation?" → Might say NO
- Agent decides: "Do I need ROI?" → Might say NO
- ⚠️ Results are incomplete if steps are skipped
- ✅ Flexible, ❌ Unreliable

### (C) `run_c_deterministic_autonomy_demo.py` - DETERMINISTIC AUTONOMY ⭐
**Key characteristic**: Agent decides + workflows guarantee completeness = STRONGEST

Shows best of both worlds:
- Agent decides: "I need Pareto first" → Runs complete Pareto workflow
- Agent reviews complete data: "I see systematic patterns" → Runs complete Correlation workflow
- Agent reviews complete data: "Now prioritize by ROI" → Runs complete ROI workflow
- ✅ Intelligent, ✅ Flexible, ✅ Complete, ✅ Reliable

## The Key Difference

**What makes (C) STRONGEST:**

```
(A) Automation:          Fixed → Fixed → Fixed
                         No intelligence

(B) Probabilistic:       Agent → Maybe? → Maybe?
                         Intelligence but unreliable

(C) Deterministic:       Agent → Complete → Agent → Complete → Agent → Complete
                         Intelligence + Systematic quality ⭐
```

## Architecture Pattern

### (C) Deterministic Autonomy Architecture:

1. **Calling Agent** (LLM) makes high-level decisions
   - "I need failure distribution" → Invokes Pareto workflow
   - "I need root causes" → Invokes Correlation workflow
   - "I need priorities" → Invokes ROI workflow

2. **Workflows** execute deterministically (ALL steps)
   - Can't skip data collection
   - Can't skip calculations
   - Can't skip analysis
   - **Uses WorkflowStepAgent** for intelligence at decision points

3. **WorkflowStepAgent** provides intelligence within workflows
   - Classifies patterns
   - Analyzes correlations
   - Generates recommendations
   - Returns structured data (not just text)

4. **Agent gets complete, reliable data** to decide next step

## Interactive vs Automated

### Interactive Demo (`run_interactive_demo.py`) ⭐
- **Interface**: Natural conversation
- **Control**: You guide the analysis through questions
- **Flexibility**: Unlimited exploration
- **Best for**: Real analysis, learning, exploration
- **Pattern**: ULTIMATE Deterministic Autonomy with conversational UI

### Automated Demos (A/B/C)
- **Interface**: Script runs and shows output
- **Control**: Pre-programmed sequence
- **Flexibility**: Fixed demonstration
- **Best for**: Understanding pattern differences
- **Pattern**: Demonstrates automation vs autonomy patterns

**Recommendation**: Start with the interactive demo to experience the agent's capabilities, then review the automated demos to understand the architectural patterns.

## See More

- [INTERACTIVE_DEMO_GUIDE.md](./INTERACTIVE_DEMO_GUIDE.md) - Full guide for conversational demo
- [DEMO_COMPARISON.md](./DEMO_COMPARISON.md) - Detailed comparison of A/B/C patterns
- [ULTIMATE_DETERMINISTIC_AUTONOMY.md](./ULTIMATE_DETERMINISTIC_AUTONOMY.md) - Architecture deep dive
- [ULTIMATE_IMPLEMENTATION_SUMMARY.md](./ULTIMATE_IMPLEMENTATION_SUMMARY.md) - Implementation details
