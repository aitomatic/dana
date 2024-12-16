<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Core Components

Core components provide the fundamental building blocks of the DXA framework.

## Overview

The core module contains:

- **Reasoning**: Decision-making strategies
- **Resources**: External tool integration
- **I/O**: Environment interaction
- **Capabilities**: Agent abilities

## Component Design

Each component follows:

1. Base abstract class defining interface
2. Standard implementations
3. Extension points for custom behavior
4. Comprehensive test coverage

## Usage

Components are typically accessed through the Agent interface:

```python
agent = Agent("assistant")\
    .with_reasoning("cot")\
    .with_resources({"llm": my_llm})\
    .with_capabilities(["research"])
```

See individual component READMEs for detailed documentation. 
