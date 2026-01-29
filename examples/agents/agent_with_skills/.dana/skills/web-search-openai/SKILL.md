---
name: web-search-openai
description: Execute web searches using OpenAI's web search capability
context: main
allowed-tools: bash:execute
---

# OpenAI Web Search

Search the web for current information using OpenAI's web search tool.

## Usage

```bash
python examples/agents/agent_with_skills/.dana/skills/web-search-openai/scripts/openai_web_search.py \
  --query "your search query" \
  [--max-results 5]
```

## When to Use
- Finding current/recent information not in training data
- Researching technical specifications
- Looking up documentation or tutorials
- Verifying facts with authoritative sources

## Output Format
Returns JSON with:
- `success`: boolean
- `sources`: list of {url, title, content}
- `summary`: synthesized answer from OpenAI
- `error`: error message if failed
