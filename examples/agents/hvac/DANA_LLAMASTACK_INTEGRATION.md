# Dana ↔ LlamaStack Integration Diagrams

This document shows two integration patterns between Dana and LlamaStack.

## Diagram 1: Dana → LlamaStack (Inference API)

This diagram shows how the HVAC example uses LlamaStack as an LLM provider.

```mermaid
graph TD
    subgraph APP_GROUP["FastAPI Server"]
        APP[Uses Dana Library]
    end

    subgraph DANA_GROUP["Dana"]
        DANA[STAR Agent]
    end

    subgraph LS_GROUP["LlamaStack"]
        LS[Inference API]
    end

    LLM[LLM Providers<br/>OpenAI / Anthropic / Llama]

    APP -->|Uses| DANA
    DANA <-->|LLM Calls| LS
    LS <-->|Routes to| LLM

    %% Styling
    classDef app fill:#f8bbd0,stroke:#E91E63,stroke-width:2px,color:#000
    classDef dana fill:#a5d6a7,stroke:#4CAF50,stroke-width:2px,color:#000
    classDef llamastack fill:#90caf9,stroke:#1565C0,stroke-width:2px,color:#000
    classDef llm fill:#ffcc80,stroke:#E65100,stroke-width:2px,color:#000

    class APP app
    class DANA dana
    class LS llamastack
    class LLM llm
```

This diagram shows how LlamaStack can use Dana as an inline agent provider for its Agent API.

```mermaid
graph TD
    subgraph LS_GROUP["LlamaStack"]
        LS_API[Agent API]
        LS_APIS[Inference API<br>VectorIO API<br>Prompts API]
        LS_API --- LS_APIS
    end

    subgraph DANA_GROUP["Dana"]
        DANA_ENGINE[Dana Engine]
        STAR[STAR Agent]
        DANA_ENGINE --- STAR
    end

    LS_API -->|Calls| DANA_ENGINE
    STAR -->|Uses| LS_APIS
    STAR -.->|Returns| DANA_ENGINE
    DANA_ENGINE -.->|Returns| LS_API

    %% Styling
    classDef llamastack fill:#90caf9,stroke:#1565C0,stroke-width:2px,color:#000
    classDef dana fill:#a5d6a7,stroke:#4CAF50,stroke-width:2px,color:#000
    classDef star fill:#81c784,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef llm fill:#ffcc80,stroke:#E65100,stroke-width:2px,color:#000

    class LS_API,LS_APIS llamastack
    class DANA_ENGINE dana
    class STAR star
    class LLM llm
```
