# SmartResearchAgent

A transparent research assistant that demonstrates the STAR framework's unique strengths through visible reasoning, adaptive strategy selection, and multi-dimensional confidence assessment.

## 🌟 Key Features

- **Transparent STAR Loop**: See exactly how the agent understands, strategizes, gathers, and synthesizes information
- **Adaptive Strategy**: Automatically selects optimal research approach based on query type (4 strategies)
- **Multi-Source Gathering**: Parallel searches across academic, news, documentation, and web sources
- **Source Quality Ranking**: Multi-factor scoring (relevance, authority, recency)
- **Synthesis & Cross-Reference**: Combines findings, identifies themes, detects conflicts
- **Knowledge Gap Detection**: Explicitly identifies what's missing from research
- **Multi-Dimensional Confidence**: Granular scoring with explanations
- **Magic Function Interface**: Natural method calls like `agent.research_quantum_computing()`

## 🚀 Quick Start

### Installation

```bash
# From repository root
cd examples/agents/smart-research

# Ensure Dana framework is installed
pip install -e ../../../dana_agent
```

### Basic Usage

```python
from agents.smart_research_agent import SmartResearchAgent

# Create agent
agent = SmartResearchAgent()

# Method 1: Programmatic interface
result = agent.query(caller_message="What are the latest advances in quantum computing?")
print(result["response"])

# Method 2: Conversational interface
agent.converse("What are the latest advances in quantum computing?")

# Method 3: Magic function interface (most natural!)
agent.research_quantum_computing_advances()
agent.compare_react_vs_vue()
agent.explain_transformer_architecture()
```

### Running Examples

```bash
# Simple quick fact lookup
python examples/run_simple_query.py

# Technical deep-dive research
python examples/run_technical_research.py

# Comparative analysis
python examples/run_comparative_analysis.py

# Interactive conversational research (NEW!)
python examples/run_interactive.py
```

## 📋 How It Works

### STAR Loop in Action

```
User Query: "What are the latest advances in quantum computing?"

SEE (Understanding)
├─ Query type: TECHNICAL + CURRENT_EVENTS
├─ Complexity: HIGH
└─ Recency emphasis: YES

THINK (Strategy Selection)
├─ Strategy: TECHNICAL_DEEP_DIVE
├─ Sources: Academic, news, technical blogs
├─ Max sources: 20
└─ Estimated time: 15-25s

ACT (Execution)
├─ Phase 1: Parallel Gathering (10s)
│   ├─ Search academic sources → 12 papers found
│   ├─ Search news sources → 8 articles found
│   ├─ Search tech blogs → 5 posts found
│   └─ Rank by quality → Top 15 selected
│
├─ Phase 2: Content Fetching (5s)
│   └─ Parallel fetch → 15 sources retrieved
│
└─ Phase 3: Synthesis (8s)
    ├─ Extract claims → 42 claims found
    ├─ Cross-reference → 28 verified, 3 conflicts
    ├─ Identify themes → 3 major themes
    ├─ Detect gaps → 2 gaps identified
    └─ Calculate confidence → 85% overall

REFLECT (Assessment)
├─ Confidence: 85% (High verification, Good recency, Minor gaps)
├─ Knowledge gaps: 2 identified
└─ Follow-up questions: 4 generated
```

## 🎯 Research Strategies

SmartResearchAgent automatically selects the optimal strategy:

| Strategy | Triggers | Sources | Depth | Time |
|----------|----------|---------|-------|------|
| **QUICK_FACT** | "what is", "define" | Google | Shallow | 2-5s |
| **TECHNICAL_DEEP_DIVE** | "explain", "how does", "architecture" | Academic, docs, tech blogs | Deep | 15-25s |
| **CURRENT_EVENTS** | "latest", "recent", "2024" | News, blogs, announcements | Medium | 8-15s |
| **COMPARATIVE_ANALYSIS** | "compare", "vs", "difference" | Reviews, benchmarks, docs | Deep | 20-35s |

## 📊 Output Format

```python
{
    "query": "What are the latest advances in quantum computing?",
    "strategy_used": "TECHNICAL_DEEP_DIVE",
    "processing_time": 18.3,

    "summary": {
        "overview": "Recent quantum computing advances focus on...",
        "key_findings": [
            {
                "finding": "Google's Willow chip achieves...",
                "source_url": "https://...",
                "source_title": "...",
                "significance": "high",
                "confidence": 0.95
            }
        ],
        "themes": [
            {
                "theme": "Error Correction Advances",
                "findings_count": 3,
                "description": "..."
            }
        ]
    },

    "knowledge_gaps": [
        {
            "gap": "Commercial application timeline",
            "severity": "high",
            "reason": "Limited information on...",
            "suggested_followup": "When will quantum computers..."
        }
    ],

    "confidence": {
        "overall": 0.85,
        "dimensions": {
            "verification": 0.90,  # Cross-reference score
            "recency": 0.95,       # Source freshness
            "completeness": 0.75   # Coverage score
        },
        "explanation": [
            "High verification (90% of claims from 2+ sources)",
            "Very recent sources (95% from 2024)"
        ]
    },

    "follow_up_questions": [
        "When will quantum computers become commercially viable?",
        "How do error correction techniques compare across platforms?"
    ],

    "sources_used": ["url1", "url2", ...]
}
```

## 🏗️ Architecture

### Component Hierarchy

```
SmartResearchAgent (STARAgent)
│
├─ Resources:
│  ├─ SearchResource (existing)
│  ├─ WebFetcher (existing)
│  ├─ ConversationResource (existing)
│  └─ SourceRankingResource (NEW)
│
└─ Workflows:
   ├─ ResearchStrategyWorkflow (NEW)
   ├─ ParallelGatheringWorkflow (NEW)
   ├─ SynthesisWorkflow (NEW)
   └─ GoogleLookupWorkflow (existing)
```

### File Structure

```
examples/agents/smart-research/
├── README.md (this file)
├── specs/
│   ├── design.md (complete design document)
│   └── implementation_tracker.md (progress tracking)
├── resources/
│   ├── __init__.py
│   └── source_ranking.py (SourceRankingResource)
├── workflows/
│   ├── __init__.py
│   ├── research_strategy.py (ResearchStrategyWorkflow)
│   ├── parallel_gathering.py (ParallelGatheringWorkflow)
│   └── synthesis.py (SynthesisWorkflow)
├── agents/
│   ├── __init__.py
│   └── smart_research_agent.py (SmartResearchAgent)
├── prompts/
│   └── SmartResearchAgent.xml (Agent identity)
├── tests/
│   ├── test_resources.py
│   ├── test_workflows.py
│   └── test_agent_integration.py
└── examples/
    ├── run_simple_query.py
    ├── run_technical_research.py
    └── run_comparative_analysis.py
```

## 🎓 Design Patterns Demonstrated

This agent showcases patterns from [`docs/ai-building-agents/`](../../../dana_agent/docs/ai-building-agents/):

1. **Single Specialist Agent** - Focused domain (research)
2. **Phased Orchestration** - Parallel gathering → Sequential synthesis
3. **Magic Function Interface** - Natural method calls
4. **Resource Reuse** - 80% existing resources
5. **LLM-Powered Resource** - ConversationResource for analysis
6. **Parallel Execution** - `asyncio.gather()` for source gathering
7. **Graceful Degradation** - Never fails completely
8. **Multi-Dimensional Confidence** - Granular quality assessment

## 🆚 Comparison with Existing Tools

| Feature | ChatGPT | Perplexity | SmartResearchAgent |
|---------|---------|------------|-------------------|
| **Shows reasoning** | ❌ | ❌ | ✅ Visible STAR loop |
| **Search strategy** | Hidden | Hidden | ✅ Explained & adaptive |
| **Source diversity** | Limited | Good | ✅ Multi-type (academic, news, docs) |
| **Confidence scores** | ❌ | ❌ | ✅ Multi-dimensional |
| **Gap identification** | ❌ | ❌ | ✅ Explicit gaps + follow-ups |
| **Transparency** | Low | Medium | ✅ High - see everything |
| **Customizable** | ❌ | ❌ | ✅ Modify workflows/strategy |

## 🔧 Extending the Agent

### Add New Source Types

Edit `workflows/parallel_gathering.py`:

```python
async def _parallel_search(self, query: str, source_types: list):
    tasks = []

    # Add your new source type
    if "github" in source_types:
        tasks.append(self._search_github(query))

    if "stackoverflow" in source_types:
        tasks.append(self._search_stackoverflow(query))

    # ... existing sources
```

### Customize Strategy Selection

Edit `workflows/research_strategy.py`:

```python
STRATEGIES = {
    # Add your custom strategy
    "ACADEMIC_ONLY": {
        "description": "Academic papers only",
        "sources": ["academic"],
        "depth": "deep",
        "max_sources": 30,
        "time_estimate": "30-45s",
        "indicators": ["academic", "papers", "research"]
    }
}
```

### Enhance Confidence Scoring

Edit `workflows/synthesis.py`:

```python
def _calculate_confidence(self, sources: list, gaps: list) -> dict:
    # Add custom dimensions
    authority = self._calculate_authority(sources)
    consistency = self._check_consistency(sources)

    overall = (
        verification * 0.3 +
        recency * 0.2 +
        completeness * 0.2 +
        authority * 0.15 +
        consistency * 0.15
    )
```

## 📝 Testing

```bash
# Run unit tests
pytest tests/test_resources.py
pytest tests/test_workflows.py

# Run integration tests
pytest tests/test_agent_integration.py

# Run all tests
pytest tests/
```

## 🐛 Known Limitations

1. **Source Types**: Currently supports Google search; academic/news sources use same backend
2. **LLM Synthesis**: Simplified synthesis logic; production should use more sophisticated LLM prompts
3. **Date Extraction**: Basic date parsing; could be enhanced with better regex patterns
4. **Authority Database**: Limited domain authority list; should be expanded
5. **Performance**: Sequential fetching after parallel search; could be fully parallelized

## 🚧 Future Enhancements

- [ ] Multi-modal research (images, videos, papers)
- [ ] Collaborative research (multiple agents)
- [ ] Research memory (avoid redundant searches)
- [ ] Domain specialization modes
- [ ] Citation management (BibTeX, EndNote)
- [ ] Interactive exploration (chat with findings)
- [ ] Monitoring mode (track topic over time)

## 📚 Related Documentation

- [Design Document](specs/design.md) - Complete design specification
- [Implementation Tracker](specs/implementation_tracker.md) - Progress and metrics
- [Agent Building Guides](../../../dana_agent/docs/ai-building-agents/) - Framework patterns

## 💡 Tips for Using

**For Quick Facts**:
```python
agent.what_is_quantum_computing()  # Fast, 2-5 seconds
```

**For Deep Understanding**:
```python
agent.explain_transformer_architecture_in_detail()  # 15-25 seconds
```

**For Current Events**:
```python
agent.latest_quantum_computing_breakthroughs_2024()  # 8-15 seconds
```

**For Comparisons**:
```python
agent.compare_react_vs_vue_in_2024()  # 20-35 seconds
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. **More source types**: Add GitHub, Stack Overflow, arXiv, PubMed
2. **Better synthesis**: Enhance LLM prompts for claim extraction
3. **Authority expansion**: Grow domain authority database
4. **Performance optimization**: Full parallelization
5. **Test coverage**: Expand unit and integration tests

## 📜 License

Part of the Dana framework. See repository root for license.

---

**Built with the Dana STAR Framework** - Demonstrates compositional AI agent architecture with transparent reasoning and deterministic workflow orchestration.

See [docs/ai-building-agents/](../../../dana_agent/docs/ai-building-agents/) for building your own agents!
