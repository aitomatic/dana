# Quick Start Templates: KNOWS MVP Implementation

**For immediate copy-paste implementation tonight**

## 1. Directory Structure Setup

```bash
# CTN: Create this structure
mkdir -p opendxa/knows/mvp/
mkdir -p opendxa/knows/mvp/knowledge/
mkdir -p opendxa/knows/mvp/composer/
mkdir -p tests/knows/mvp/
mkdir -p tests/comparison/
```

## 2. KnowledgeUnit Schema (CTN)

```python
# opendxa/knows/mvp/knowledge_unit.py
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class KnowledgeUnit:
    """Minimal knowledge unit with P-S-T metadata for MVP"""
    content: str
    phase: str  # "Prior" | "Documentary" | "Experiential"
    source: str  # "Human" | "Machine" | "Hybrid"
    type: str   # "Topical" | "Procedural"
    tags: List[str]
    confidence: float  # 0.0 to 1.0
    examples: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.phase not in ["Prior", "Documentary", "Experiential"]:
            raise ValueError(f"Invalid phase: {self.phase}")
        if self.source not in ["Human", "Machine", "Hybrid"]:
            raise ValueError(f"Invalid source: {self.source}")
        if self.type not in ["Topical", "Procedural"]:
            raise ValueError(f"Invalid type: {self.type}")

    def to_context_string(self) -> str:
        """Format for injection into LLM context"""
        return f"[{self.type}] {self.content} (confidence: {self.confidence})"
    
    def matches_tags(self, query_tags: List[str]) -> float:
        """Simple tag matching score"""
        if not query_tags:
            return 0.0
        matches = len(set(self.tags) & set(query_tags))
        return matches / len(query_tags) if query_tags else 0.0
```

## 3. Knowledge Composer (CTN)

```python
# opendxa/knows/mvp/composer/knowledge_composer.py
from typing import List, Dict
from ..knowledge_unit import KnowledgeUnit

class KnowledgeComposer:
    """Composes knowledge units into LLM context"""
    
    def __init__(self, knowledge_units: List[KnowledgeUnit]):
        self.knowledge_units = knowledge_units
    
    def compose_context(self, query: str, query_tags: List[str] = None, max_units: int = 5) -> str:
        """Build context from relevant knowledge units"""
        if not query_tags:
            query_tags = self._extract_tags_from_query(query)
        
        # Score and rank knowledge units
        scored_units = []
        for unit in self.knowledge_units:
            score = unit.matches_tags(query_tags) * unit.confidence
            scored_units.append((score, unit))
        
        # Sort by score, take top units
        scored_units.sort(key=lambda x: x[0], reverse=True)
        top_units = [unit for _, unit in scored_units[:max_units] if _ > 0]
        
        # Format for context
        if not top_units:
            return "No relevant knowledge found."
        
        context_parts = ["Relevant Knowledge:"]
        for unit in top_units:
            context_parts.append(f"- {unit.to_context_string()}")
        
        return "\n".join(context_parts)
    
    def _extract_tags_from_query(self, query: str) -> List[str]:
        """Simple keyword extraction from query"""
        # Basic implementation - can be improved
        keywords = query.lower().split()
        # Filter out common words
        stop_words = {"the", "is", "at", "which", "on", "and", "a", "an", "how", "what", "why"}
        return [word for word in keywords if word not in stop_words and len(word) > 2]
```

## 4. Dana Functions Template (Sang)

```python
# opendxa/dana/sandbox/interpreter/functions/core/knows_mvp_functions.py
"""Dana functions for KNOWS MVP integration"""

from typing import Any, Dict, List
from opendxa.knows.mvp.knowledge_unit import KnowledgeUnit
from opendxa.knows.mvp.composer.knowledge_composer import KnowledgeComposer

# Global knowledge store for MVP (simplified)
_knowledge_store: List[KnowledgeUnit] = []
_composer: KnowledgeComposer = None

def load_knowledge_units(units_data: List[Dict]) -> str:
    """Load knowledge units from data (called from Dana)"""
    global _knowledge_store, _composer
    
    _knowledge_store = []
    for unit_data in units_data:
        unit = KnowledgeUnit(**unit_data)
        _knowledge_store.append(unit)
    
    _composer = KnowledgeComposer(_knowledge_store)
    return f"Loaded {len(_knowledge_store)} knowledge units"

def get_relevant_knowledge(query: str, tags: List[str] = None, max_units: int = 5) -> str:
    """Get relevant knowledge for query (called from Dana)"""
    global _composer
    
    if not _composer:
        return "No knowledge loaded"
    
    return _composer.compose_context(query, tags, max_units)

def log_knowledge_usage(query: str, units_used: List[str], helpful: bool = True) -> str:
    """Log knowledge usage for feedback (MVP: simple logging)"""
    log_entry = {
        "query": query,
        "units_used": units_used,
        "helpful": helpful,
        "timestamp": str(datetime.now())
    }
    # For MVP: just log to console
    print(f"KNOWS Usage Log: {log_entry}")
    return "Usage logged"

# Register functions with Dana runtime
KNOWS_FUNCTIONS = {
    "load_knowledge": load_knowledge_units,
    "get_knowledge": get_relevant_knowledge,
    "log_usage": log_knowledge_usage
}
```

## 5. Sample Knowledge Units (William)

```json
# opendxa/knows/mvp/knowledge/sample_units.json
[
  {
    "content": "Python list comprehensions are more efficient than for loops for simple transformations",
    "phase": "Documentary",
    "source": "Human",
    "type": "Topical",
    "tags": ["python", "performance", "list", "optimization"],
    "confidence": 0.9,
    "examples": ["Use when converting list elements", "Performance-critical code"],
    "metadata": {
      "created": "2025-01-02",
      "validated": true,
      "domain": "programming"
    }
  },
  {
    "content": "To debug intermittent failures, first reproduce with minimal test case, then add logging",
    "phase": "Experiential",
    "source": "Human",
    "type": "Procedural",
    "tags": ["debugging", "testing", "troubleshooting", "methodology"],
    "confidence": 0.85,
    "examples": ["Debugging flaky tests", "Production issue investigation"],
    "metadata": {
      "created": "2025-01-02",
      "validated": true,
      "domain": "software-engineering"
    }
  },
  {
    "content": "LLM context windows have token limits; prioritize most relevant information first",
    "phase": "Prior",
    "source": "Machine",
    "type": "Topical", 
    "tags": ["llm", "context", "optimization", "ai"],
    "confidence": 0.95,
    "examples": ["Building RAG systems", "Prompt engineering"],
    "metadata": {
      "created": "2025-01-02",
      "validated": true,
      "domain": "ai-engineering"
    }
  }
]
```

## 6. Basic Dana Script Template

```dana
# examples/knows_mvp_demo.na
# Example Dana script using KNOWS MVP

# Load knowledge units
knowledge_data = load_json("opendxa/knows/mvp/knowledge/sample_units.json")
load_result = load_knowledge(knowledge_data)
log(f"Knowledge loading: {load_result}")

# Query for relevant knowledge
query = "How do I optimize Python performance?"
relevant_knowledge = get_knowledge(query, ["python", "performance"], 3)
log(f"Relevant knowledge: {relevant_knowledge}")

# Use knowledge in reasoning
enhanced_context = f"{query}\n\n{relevant_knowledge}"
answer = reason(enhanced_context)
log(f"Enhanced answer: {answer}")

# Log usage feedback
log_usage(query, ["python performance"], true)
```

## 7. Test Templates

```python
# tests/knows/mvp/test_knowledge_unit.py
import pytest
from opendxa.knows.mvp.knowledge_unit import KnowledgeUnit

def test_knowledge_unit_creation():
    unit = KnowledgeUnit(
        content="Test knowledge",
        phase="Documentary",
        source="Human",
        type="Topical",
        tags=["test"],
        confidence=0.8,
        examples=["testing"],
        metadata={}
    )
    assert unit.content == "Test knowledge"
    assert unit.confidence == 0.8

def test_knowledge_unit_validation():
    with pytest.raises(ValueError):
        KnowledgeUnit(
            content="Test",
            phase="Invalid",  # Should fail
            source="Human",
            type="Topical",
            tags=[],
            confidence=0.8,
            examples=[],
            metadata={}
        )

def test_tag_matching():
    unit = KnowledgeUnit(
        content="Test",
        phase="Documentary",
        source="Human", 
        type="Topical",
        tags=["python", "testing"],
        confidence=0.8,
        examples=[],
        metadata={}
    )
    
    assert unit.matches_tags(["python"]) == 0.5  # 1/2 match
    assert unit.matches_tags(["python", "testing"]) == 1.0  # 2/2 match
    assert unit.matches_tags(["java"]) == 0.0  # 0/1 match
```

## 8. Evaluation Framework Template (William)

```python
# tests/comparison/evaluation.py
from dataclasses import dataclass
from typing import List, Dict, Any
import time

@dataclass
class TestCase:
    input: str
    expected_keywords: List[str]
    success_criteria: List[str]
    metadata: Dict[str, Any]

@dataclass 
class AgentResult:
    output: str
    execution_time: float
    tokens_used: int
    knowledge_sources: List[str]
    metadata: Dict[str, Any]

class ComparisonEvaluator:
    def __init__(self, test_cases: List[TestCase]):
        self.test_cases = test_cases
    
    def evaluate_agent(self, agent_function, agent_name: str) -> Dict[str, Any]:
        """Evaluate agent performance on all test cases"""
        results = []
        total_time = 0
        total_tokens = 0
        
        for test_case in self.test_cases:
            start_time = time.time()
            result = agent_function(test_case.input)
            end_time = time.time()
            
            agent_result = AgentResult(
                output=result.get("output", ""),
                execution_time=end_time - start_time,
                tokens_used=result.get("tokens", 0),
                knowledge_sources=result.get("sources", []),
                metadata=result.get("metadata", {})
            )
            
            results.append(agent_result)
            total_time += agent_result.execution_time
            total_tokens += agent_result.tokens_used
        
        return {
            "agent_name": agent_name,
            "results": results,
            "summary": {
                "avg_time": total_time / len(results),
                "total_tokens": total_tokens,
                "test_cases": len(results)
            }
        }
    
    def compare_agents(self, knows_results: Dict, rag_results: Dict) -> Dict[str, Any]:
        """Compare results between KNOWS and RAG agents"""
        comparison = {
            "performance": {
                "knows_avg_time": knows_results["summary"]["avg_time"],
                "rag_avg_time": rag_results["summary"]["avg_time"],
                "time_improvement": (rag_results["summary"]["avg_time"] - knows_results["summary"]["avg_time"]) / rag_results["summary"]["avg_time"]
            },
            "efficiency": {
                "knows_tokens": knows_results["summary"]["total_tokens"],
                "rag_tokens": rag_results["summary"]["total_tokens"],
                "token_efficiency": (rag_results["summary"]["total_tokens"] - knows_results["summary"]["total_tokens"]) / rag_results["summary"]["total_tokens"]
            }
        }
        
        return comparison
```

## 9. Quick Test Cases (William)

```json
# tests/comparison/test_cases.json
[
  {
    "input": "How do I debug a Python performance issue?",
    "expected_keywords": ["debug", "performance", "python", "profiling"],
    "success_criteria": ["mentions profiling tools", "suggests systematic approach"],
    "metadata": {"domain": "programming", "difficulty": "medium"}
  },
  {
    "input": "What's the best way to optimize LLM context usage?",
    "expected_keywords": ["context", "optimization", "tokens", "relevant"],
    "success_criteria": ["mentions token limits", "suggests prioritization"],
    "metadata": {"domain": "ai", "difficulty": "medium"}
  },
  {
    "input": "How should I approach troubleshooting intermittent test failures?",
    "expected_keywords": ["troubleshooting", "intermittent", "reproduce", "logging"],
    "success_criteria": ["systematic methodology", "mentions reproduction"],
    "metadata": {"domain": "testing", "difficulty": "hard"}
  }
]
```

## 10. Quick Setup Script

```bash
#!/bin/bash
# setup_mvp.sh - Quick setup for MVP development

echo "Setting up KNOWS MVP structure..."

# Create directories
mkdir -p opendxa/knows/mvp/knowledge/
mkdir -p opendxa/knows/mvp/composer/
mkdir -p tests/knows/mvp/
mkdir -p tests/comparison/

# Create __init__.py files
touch opendxa/knows/mvp/__init__.py
touch opendxa/knows/mvp/composer/__init__.py
touch tests/knows/mvp/__init__.py
touch tests/comparison/__init__.py

echo "Structure created! Ready for implementation."
echo "Next steps:"
echo "1. CTN: Implement KnowledgeUnit and KnowledgeComposer"
echo "2. Sang: Create Dana functions"
echo "3. William: Create knowledge units and test cases"
```

**Ready to copy-paste and start building! 🏗️** 