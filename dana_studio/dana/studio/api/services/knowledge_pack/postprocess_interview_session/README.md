# Interview Session Postprocessor

A service for aggregating and comparing expert insights across multiple interview sessions.

## Overview

This service processes multiple `interview_notes.md` files from different interview sessions and generates a comparative report that groups similar topics together, allowing you to see insights from different experts side-by-side.

## Features

- **LLM-Enhanced Analysis**: Uses GPT-4 to intelligently analyze expert insights and separate consensus from contradictions
- **Automatic Discovery**: Uses glob to find all interview notes within a template's session folders
- **Smart Topic Matching**: Combines BM25 semantic search and SequenceMatcher fuzzy matching to group similar topics across sessions
- **Consensus Detection**: Identifies areas where all or most experts agree
- **Contradiction Identification**: Flags conflicting viewpoints with severity levels (CRITICAL, HIGH, MEDIUM, LOW)
- **Actionable Recommendations**: Provides resolution strategies for contradictions
- **Dual Modes**: Can run with LLM (enhanced) or without LLM (basic side-by-side comparison)
- **Markdown Output**: Generates clean, readable markdown reports

## Usage

### Basic Usage (LLM-Enhanced)

```python
import asyncio
from dana_studio.dana.studio.api.services.knowledge_pack.postprocess_interview_session import aggregate_interview_insights

async def main():
    # Generate LLM-enhanced comparison report with consensus and contradictions
    template_path = "knowledge_packs/1/templates/template_3_test"
    report = await aggregate_interview_insights(template_path, use_llm=True)
    
    # Save to file
    with open("llm_analysis_report.md", "w") as f:
        f.write(report)
    
    print(report)

asyncio.run(main())
```

### Without LLM (Fallback Format)

```python
import asyncio
from dana_studio.dana.studio.api.services.knowledge_pack.postprocess_interview_session import aggregate_interview_insights

async def main():
    # Generate basic side-by-side comparison (no LLM analysis)
    template_path = "knowledge_packs/1/templates/template_2"
    report = await aggregate_interview_insights(template_path, use_llm=False)
    
    with open("comparison_report.md", "w") as f:
        f.write(report)

asyncio.run(main())
```

### Custom LLM Configuration

```python
import asyncio
from dana_studio.dana.studio.api.services.knowledge_pack.postprocess_interview_session import aggregate_interview_insights

async def main():
    template_path = "knowledge_packs/1/templates/template_3_test"
    
    # Custom LLM settings
    custom_config = {
        "model": "gpt-4o",
        "temperature": 0.2,  # More focused analysis
        "max_tokens": 4000   # Longer reports
    }
    
    report = await aggregate_interview_insights(
        template_path=template_path,
        use_llm=True,
        llm_config=custom_config
    )
    
    with open("custom_analysis.md", "w") as f:
        f.write(report)

asyncio.run(main())
```

### Running the Test Script

```bash
cd /path/to/opendxa
source .venv/bin/activate
python dana_studio/dana/studio/api/services/knowledge_pack/postprocess_interview_session/test_llm_analysis.py
```

## How It Works

### 1. Discovery
The service uses glob patterns to find all `interview_notes.md` files:
```
template_path/
└── sessions/
    ├── session_1/
    │   └── interview_notes.md
    ├── session_2/
    │   └── interview_notes.md
    └── session_3/
        └── interview_notes.md
```

### 2. Parsing
Each interview note is parsed using the existing `parse_interview_note` function from `interview_handler.utils`, extracting:
- Topic name
- Expert insights
- Status (not_started, in_progress, completed)
- Insights count

### 3. Topic Grouping
Topics are matched across sessions using a two-step process:

**Step 1: BM25 Semantic Search**
- All topic names are indexed with BM25
- For each topic, find the top N most similar topics

**Step 2: SequenceMatcher Fuzzy Matching**
- Filter BM25 candidates with SequenceMatcher
- Threshold: similarity ≥ 0.7
- Groups topics with minor variations (e.g., "Shutdown Procedures" matches "Shutdown Procedure")

### 4. LLM Analysis (Optional)
When `use_llm=True`, each topic is analyzed by GPT-4 to:
- Identify areas of expert consensus
- Detect contradictions and conflicts
- Classify contradiction severity
- Provide resolution recommendations
- Generate structured markdown per topic

### 5. Report Generation
The final markdown report format depends on mode:

**With LLM (Enhanced Format):**
- Summary statistics
- For each topic:
  * 🤝 Expert Consensus section (agreements)
  * ⚠️ Areas of Disagreement section (contradictions with severity)
  * 📊 Topic Statistics
  
**Without LLM (Basic Format):**
- Summary statistics
- Simple side-by-side comparison of all expert insights

## Output Formats

### LLM-Enhanced Format (use_llm=True)

```markdown
# Multi-Session Expert Insights Comparison

## Summary
- Total Topics: 6
- Sessions Analyzed: 3
- Topics with Multiple Expert Inputs: 6

---

## Topic: Shutdown Procedures and Safe Isolation

### 🤝 Expert Consensus (Areas of Agreement)

✅ **Personnel safety is the top priority**
- All 3 experts unanimously rank personnel safety as #1 during shutdown
- Session 1: "Priority order: (1) Personnel safety..."
- Session 2: "Priority order: (1) Personnel safety..."
- Session 3: "Priority order: (1) Personnel safety (always first)..."

✅ **LOTO procedures are mandatory**
- Universal agreement that lockout-tagout is required before maintenance

---

### ⚠️ Areas of Disagreement (Contradictions Identified)

#### 🔴 CRITICAL: Valve Isolation Sequence
**Status**: No consensus - requires immediate expert review

**Three fundamentally different approaches:**

**Position A: Inlet-First Method** [Session 1 - J. Martinez, 20 yrs]
> "Always isolate the inlet valve FIRST..."

- **Rationale**: Prevents backflow, avoids thermal shock
- **Risk**: May create pressure buildup

**Position B: Drain-First Method** [Session 2 - S. Chen, 15 yrs]
> "NEVER isolate the inlet valve first!..."

- **Rationale**: Prevents pressure buildup
- **Risk**: Potential backflow

**Position C: Simultaneous Closure** [Session 3 - M. Okonkwo, 10 yrs]
> "Safety protocol requires simultaneous closure..."

- **Rationale**: Eliminates unsafe transition states
- **Risk**: Requires automated system

**⚡ Impact**: CRITICAL - Safety and equipment integrity directly affected

**🔍 Analysis**: Fundamental disagreement with mutually exclusive methods...

**✅ Recommended Resolution**:
1. Consult equipment manufacturer specifications
2. Review historical incident data
3. Conduct engineering risk assessment
4. Establish single plant-wide SOP

---

### 📊 Topic Statistics
- **Total Expert Insights**: 15 (5 per session)
- **Consensus Items**: 3
- **Contradictions**: 2 (1 critical, 1 high)
- **Session Completion**: 3/3 completed

---

## Topic: [Next Topic]
...
```

### Basic Format (use_llm=False)

```markdown
# Multi-Session Expert Insights Comparison

## Summary
- Total Topics: 6
- Sessions Analyzed: 3
- Topics with Multiple Expert Inputs: 6

---

## Topic: Shutdown Procedures

### Session 1 (Status: completed, Insights: 5)
[Full expert insights from session 1...]

### Session 2 (Status: completed, Insights: 5)
[Full expert insights from session 2...]

### Session 3 (Status: completed, Insights: 5)
[Full expert insights from session 3...]

---

## Topic: [Next Topic]
...
```

## Future Enhancements

### ✅ Implemented (v2.0 - LLM Enhanced)
1. ✅ **Contradiction Detection**: Identifies when experts provide conflicting information with severity levels
2. ✅ **Consensus Analysis**: Highlights areas where all experts agree
3. ✅ **Semantic Analysis**: Uses GPT-4 to analyze and summarize conflicting insights

### 🔮 Potential Future Additions
1. **Completeness Tracking**: Show which topics have been covered by which experts
2. **Export Formats**: Support JSON, HTML, or other output formats beyond markdown
3. **Confidence Scoring**: Track and analyze expert confidence levels for each insight
4. **Visual Contradiction Matrix**: Interactive visualization of agreement/disagreement patterns
5. **Automatic SOP Generation**: Generate draft SOPs from consensus items
6. **Multi-Language Support**: Analyze interviews conducted in different languages
7. **Version Tracking**: Track how expert opinions evolve across multiple interview rounds

## Architecture

```
postprocess_interview_session/
├── __init__.py              # Package exports
├── postprocessor.py         # Main service implementation
├── example.py               # Usage example
└── README.md                # This file
```

### Key Functions

- `find_all_interview_notes(template_path)`: Discovers all interview notes
- `parse_all_sessions(notes_paths)`: Parses all interview files
- `group_topics_by_similarity(all_sessions_data)`: Groups similar topics using BM25 + SequenceMatcher
- `generate_markdown_report(grouped_topics)`: Creates the markdown output
- `aggregate_interview_insights(template_path)`: Main entry point

## Dependencies

- `glob` - File pattern matching
- `pathlib` - Path manipulation
- `difflib.SequenceMatcher` - Fuzzy string matching
- `dana.studio.api.services.search.bm25.BM25SearchEngine` - Semantic search
- `dana.studio.api.services.knowledge_pack.interview_handler.utils.parse_interview_note` - Interview parsing

## Testing

To test with your own data:

```python
# Test with different template paths
report1 = aggregate_interview_insights("knowledge_packs/1/templates/template_2")
report2 = aggregate_interview_insights("knowledge_packs/2/templates/default_template")

# Verify topic grouping
from dana_studio.dana.studio.api.services.knowledge_pack.postprocess_interview_session.postprocessor import (
    find_all_interview_notes,
    parse_all_sessions,
    group_topics_by_similarity
)

notes = find_all_interview_notes("knowledge_packs/1/templates/template_2")
sessions = parse_all_sessions(notes)
grouped = group_topics_by_similarity(sessions)

print(f"Found {len(grouped)} unique topics from {len(sessions)} sessions")
```

## License

Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

