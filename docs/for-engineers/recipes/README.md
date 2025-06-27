# Dana Recipes - Agent-Native Patterns and Examples

*Real-world solutions for common development tasks using Dana's agent-native architecture and OpenDXA*

---

## Quick Navigation

### 🚀 Getting Started
- [First Agent](first-agent.md) - Build your first working agent in 10 minutes
- [Dana Language Basics](../reference/dana-syntax.md) - Essential agent-native syntax reference

### 🏗️ Application Patterns
- [Chatbot Development](chatbot/README.md) - Customer service, FAQ, conversational AI
- [Document Processor](document-processor/README.md) - Extract, analyze, transform content
- [Workflow Agent](workflow-agent/README.md) - Multi-step automated processes
- [API Integration](api-integration/README.md) - Connect external services

### 🤖 Multi-Agent Systems
- [**Multi-Agent Collaboration**](multi-agent-collaboration/README.md) - **A2A and module agents working together**

### 📚 Advanced Agent-Native Patterns
- [**Structs Cookbook**](structs-cookbook.md) - **Real-world struct patterns and examples**
- [MCP Integration](mcp-integration.md) - Model Context Protocol connections

---

## Recipe Categories

### Data Modeling & Business Logic
Use Dana's agent-native struct system to model your domain clearly and add AI-powered behavior:

```dana
struct Customer:
    id: str
    name: str
    email: str
    status: str

def analyze_engagement(customer: Customer) -> str:
    return reason("Analyze customer engagement patterns", context=customer)

# Method syntax sugar makes it natural
customer = Customer(id="C001", name="Alice", email="alice@example.com", status="active")
engagement = customer.analyze_engagement()
```

**See**: [Structs Cookbook](structs-cookbook.md) for complete business domain examples

### AI Integration Patterns
Seamlessly integrate AI reasoning into your application logic using agent-native features:

```dana
# Document analysis
def extract_insights(doc: Document) -> dict:
    key_points = reason("Extract key points", context=doc.content)
    sentiment = reason("Analyze sentiment", context=doc.content) 
    return {"points": key_points, "sentiment": sentiment}

# Risk assessment
def assess_portfolio_risk(portfolio: Portfolio) -> str:
    return reason("Assess investment risk", context=portfolio.positions)
```

### Configuration & Error Handling
Build robust, maintainable applications with proper configuration management:

```dana
struct AppConfig:
    database_url: str
    api_key: str
    debug_mode: bool

def validate_config(config: AppConfig) -> bool:
    if not config.api_key:
        log("API key is required", level="error")
        return false
    return true
```

### Performance Patterns
Understand Dana's performance characteristics and optimize when needed:

- **Struct Creation**: ~0.7x overhead (actually faster than Python dicts!)
- **Method Calls**: ~4x overhead (acceptable for added functionality)
- **Field Access**: ~9x overhead (cache frequently accessed data)

---

## How to Use These Recipes

### 1. Start with Your Use Case
Each recipe is self-contained and includes:
- **Problem Statement**: What you're trying to solve
- **Complete Working Code**: Copy-paste ready examples
- **Explanation**: Why the pattern works
- **Variations**: How to adapt for your needs

### 2. Copy and Adapt
All examples are designed to be:
- **Copy-paste ready**: Working code you can use immediately
- **Well-documented**: Clear explanations of each part
- **Extensible**: Easy to modify for your specific requirements

### 3. Build on Patterns
Start with simple patterns and combine them:
- Use struct patterns for data modeling
- Add AI integration for intelligent behavior
- Apply configuration patterns for maintainability
- Implement error handling for robustness

---

## Recipe Index

### Business Applications
| Recipe | Use Case | Complexity |
|--------|----------|------------|
| [CRM System](structs-cookbook.md#business-domain-models) | Customer relationship management | Intermediate |
| [Portfolio Manager](structs-cookbook.md#financial-portfolio-management) | Financial portfolio analysis | Advanced |
| [Order Processing](structs-cookbook.md#business-domain-models) | E-commerce order handling | Intermediate |

### Data Processing  
| Recipe | Use Case | Complexity |
|--------|----------|------------|
| [ETL Pipeline](structs-cookbook.md#data-processing-pipelines) | Extract, transform, load operations | Advanced |
| [Document Analysis](structs-cookbook.md#data-processing-pipelines) | AI-powered document processing | Intermediate |
| [Data Validation](structs-cookbook.md#error-handling-strategies) | Input validation and cleaning | Beginner |

### System Patterns
| Recipe | Use Case | Complexity |
|--------|----------|------------|
| [Configuration Management](structs-cookbook.md#configuration-management) | App config and environment handling | Intermediate |
| [Error Handling](structs-cookbook.md#error-handling-strategies) | Robust error management | Beginner |
| [Performance Optimization](structs-cookbook.md#performance-patterns) | Optimizing Dana applications | Advanced |

### Multi-Agent Systems
| Recipe | Use Case | Complexity |
|--------|----------|------------|
| [Multi-Agent Collaboration](multi-agent-collaboration/README.md) | A2A and module agent orchestration | Advanced |
| [Agent Pool Management](multi-agent-collaboration/README.md#agent-pool-management) | Dynamic agent selection | Intermediate |
| [Reason Function Integration](multi-agent-collaboration/README.md#reason-function-integration) | AI reasoning with agents | Intermediate |

### Integration
| Recipe | Use Case | Complexity |
|--------|----------|------------|
| [API Clients](api-integration/README.md) | REST API integration | Beginner |
| [MCP Services](mcp-integration.md) | Model Context Protocol | Intermediate |
| [Database Access](structs-cookbook.md#data-processing-pipelines) | Database operations | Intermediate |

---

## Contributing Recipes

Have a useful pattern or example? We'd love to include it!

### Recipe Template
Each recipe should include:

1. **Problem Statement** - What real-world problem does this solve?
2. **Complete Example** - Working, copy-paste ready code
3. **Explanation** - Step-by-step breakdown
4. **Variations** - Common adaptations
5. **Best Practices** - Do's and don'ts
6. **Performance Notes** - Any performance considerations

### Submission Process
1. Follow the template structure
2. Test all code examples
3. Include clear documentation
4. Submit via pull request

---

## Getting Help

### Quick Reference
- **Syntax Issues**: [Dana Language Reference](../reference/dana-syntax.md)
- **Function Questions**: [API Reference](../reference/api/README.md)
- **Debugging**: [Troubleshooting Guide](../troubleshooting/README.md)

### Community
- **Discord**: Join our [Discord community](https://discord.gg/6jGD4PYk)
- **GitHub**: [Report issues or contribute](https://github.com/aitomatic/opendxa)
- **Documentation**: [Complete docs](https://docs.aitomatic.com)

---

## Next Steps

1. **Start Simple**: Pick a recipe that matches your use case
2. **Experiment**: Modify examples to fit your needs  
3. **Build**: Combine patterns for larger applications
4. **Share**: Contribute back patterns you find useful

Ready to build? Start with [First Agent](first-agent.md) or dive into the [Structs Cookbook](structs-cookbook.md) for advanced patterns.

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>