# Expert Interview Application

A domain-agnostic expert interview application built on Dana's conversation and analysis resources.

## Overview

This application conducts structured expert interviews with real-time analysis:
- **Topic Extraction**: Identifies topics with exact terminology preservation
- **Insight Analysis**: Captures expert knowledge with original quotes
- **Gap Detection**: Identifies differences between expert knowledge and reference materials
- **Contextual Follow-ups**: Generates relevant next questions

## Built On

### Dana Library Resources
- `ConversationResource`: Topic extraction, intent detection, summarization
- `ExpertInsightAnalyzer`: Extract insights with quote preservation
- `KnowledgeGapDetector`: Identify knowledge gaps between sources

### Dana Library Workflows
- `SummarizeConversationWorkflow`: Generate conversation summaries
- `ExpertInterviewWorkflow`: Orchestrate parallel analysis

## Architecture

```
Expert Message
       ↓
ExpertInterviewWorkflow
       ↓
   ┌───────────────────────┐
   │   PHASE 1: Parallel   │
   │   ┌────────────────┐  │
   │   │ Topic Extract  │  │
   │   │ (Conversation  │  │
   │   │  Resource)     │  │
   │   └────────────────┘  │
   │          +            │
   │   ┌────────────────┐  │
   │   │ Insight Analyze│  │
   │   │ (Expert Insight│  │
   │   │  Analyzer)     │  │
   │   └────────────────┘  │
   └───────────────────────┘
       ↓
   ┌───────────────────────┐
   │   PHASE 2: Analysis   │
   │   ┌────────────────┐  │
   │   │ Gap Detection  │  │
   │   │ (Knowledge Gap │  │
   │   │  Detector)     │  │
   │   └────────────────┘  │
   │          +            │
   │   ┌────────────────┐  │
   │   │ Next Question  │  │
   │   │ Generation     │  │
   │   └────────────────┘  │
   └───────────────────────┘
       ↓
  Instant Context
```

## Installation

```bash
# From dana_agent directory
pip install -e .

# Ensure .env has LLM credentials
# ANTHROPIC_API_KEY=your_key_here
```

## Usage

### Simple CLI Interview

```bash
python contrib/expert_interview/examples/simple_interview.py \
  --expert-name "Dr. Smith" \
  --domain "Crystallization" \
  --years-experience 15
```

**Interactive Commands:**
- Type responses to answer questions
- `summary` - View conversation summary
- `context` - View current interview context
- `quit` - End and optionally save session

### Python API

```python
from contrib.expert_interview import ExpertInterviewWorkflow

# Create workflow
workflow = ExpertInterviewWorkflow(
    expert_profile={
        "name": "Dr. Smith",
        "role": "Process Engineer",
        "domain": "Crystallization",
        "years_experience": 15
    },
    reference_materials=["crystallization_handbook.txt"]
)

# Process expert message
result = workflow.execute(
    expert_message="We use PID controllers with cascade loops...",
    conversation_history=[]
)

# Access analysis
print(result["result"]["topics"])         # Extracted topics
print(result["result"]["insights"])       # Expert insights
print(result["result"]["gaps"])           # Knowledge gaps
print(result["result"]["next_question"])  # Suggested follow-up
print(result["result"]["instant_context"]) # Current snapshot
```

## Components

### Resources

#### `ExpertInsightAnalyzer`
Extracts expert insights with exact quote preservation.

**Features:**
- Original quote extraction
- Technical term identification
- Expertise indicator detection
- Domain-agnostic

**Example:**
```python
from contrib.expert_interview import ExpertInsightAnalyzer

analyzer = ExpertInsightAnalyzer()
result = analyzer.analyze_insights(
    message="The supersaturation must stay in the metastable zone",
    expert_profile={"years_experience": 15}
)

print(result["expert_insights_original"])
# [{"original_quote": "...", "key_terms": [...], "context": "..."}]
```

#### `KnowledgeGapDetector`
Identifies gaps between expert knowledge and reference materials.

**Features:**
- Source comparison
- Gap classification (missing, contradiction, enhancement)
- Severity assessment
- Recommendation generation

**Example:**
```python
from contrib.expert_interview import KnowledgeGapDetector

detector = KnowledgeGapDetector()
result = detector.detect_gaps(
    source1_content=[{"original_quote": "We use cascade loops"}],
    source2_content=["Standard PID controllers are used"],
    source1_label="Expert",
    source2_label="Documentation"
)

print(result["gaps"])
# [{"gap_type": "missing", "description": "...", ...}]
```

### Workflows

#### `ExpertInterviewWorkflow`
Orchestrates the interview process with parallel analysis.

**Phases:**
1. **Parallel Gathering**: Topic extraction + Insight analysis
2. **Gap Detection**: Compare with reference materials (if provided)
3. **Question Generation**: Create contextual follow-up

**Configuration:**
```python
workflow = ExpertInterviewWorkflow(
    expert_profile={...},           # Optional
    reference_materials=[...],      # Optional
)
```

## Use Cases

### Technical Interviews
Interview engineers, scientists, technicians about their processes and practices.

### Knowledge Capture
Document expert knowledge for training, onboarding, or knowledge bases.

### Process Documentation
Capture operational procedures and best practices from practitioners.

### Training Material Creation
Generate training content from expert conversations.

### Quality Assurance
Verify documentation matches actual expert practices.

## Domain Examples

The application is domain-agnostic and works for:

- **Manufacturing**: Capture process knowledge from operators
- **Software**: Document architectural decisions from senior developers
- **Medical**: Extract clinical knowledge from practitioners
- **Legal**: Capture case strategy from experienced attorneys
- **Finance**: Document trading strategies from analysts

## Customization

### Custom Next Question Generation

Override `_generate_next_question` in `ExpertInterviewWorkflow`:

```python
class CustomInterviewWorkflow(ExpertInterviewWorkflow):
    def _generate_next_question(self, topics, insights, gaps, history):
        # Your custom logic
        # Could use LLM for more sophisticated generation
        return "Custom question..."
```

### Custom Analysis Pipeline

Extend the workflow with additional analysis steps:

```python
class EnhancedInterviewWorkflow(ExpertInterviewWorkflow):
    def _do_execute(self, **kwargs):
        # Get base analysis
        result = super()._do_execute(**kwargs)

        # Add custom analysis
        result["sentiment"] = self._analyze_sentiment(...)
        result["confidence"] = self._assess_confidence(...)

        return result
```

## File Structure

```
contrib/expert_interview/
├── __init__.py                    # Package exports
├── README.md                      # This file
├── resources/
│   ├── __init__.py
│   ├── expert_insights.py         # ExpertInsightAnalyzer
│   └── knowledge_gaps.py          # KnowledgeGapDetector
├── workflows/
│   ├── __init__.py
│   └── expert_interview.py        # ExpertInterviewWorkflow
└── examples/
    └── simple_interview.py        # CLI application
```

## Comparison with bs-live-interview

| Feature | bs-live-interview | Expert Interview (Dana) |
|---------|-------------------|-------------------------|
| **Architecture** | Custom pipeline | Dana resources + workflows |
| **LOC** | ~10,000 | ~800 (90% reduction!) |
| **Domain** | British Sugar specific | Domain-agnostic |
| **Dependencies** | Custom everything | Dana library |
| **Reusability** | Low | High (composable) |
| **Extensibility** | Moderate | High (inherit/compose) |
| **UI** | Gradio | CLI (extensible) |

## Future Enhancements

### Planned
- [ ] Session persistence (save/resume interviews)
- [ ] Multi-expert interviews
- [ ] Document ingestion workflow
- [ ] Report generation workflow
- [ ] Gradio UI (optional)
- [ ] STARAgent integration (autonomous interviewing)

### Ideas
- Sentiment analysis during interviews
- Real-time knowledge graph construction
- Multi-language support
- Audio transcription integration
- Collaborative interviews (multiple interviewers)

## License

Same as Dana framework.

## Contributing

This is a contrib app demonstrating Dana's capabilities. Contributions welcome:
1. Fork the repo
2. Add features
3. Submit PR

## Credits

Built on:
- Dana framework conversation resources
- Dana workflow composition
- Extracted patterns from bs-live-interview project
