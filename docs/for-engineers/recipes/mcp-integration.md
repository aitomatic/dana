# MCP Integration Patterns

This guide demonstrates how to integrate with MCP (Model Context Protocol) services using Dana's new object method call syntax.

> **Design Reference**: For detailed implementation of resource acquisition patterns, see the [Use Statement Design Document](../../../design/03_core_capabilities_resources/use_statement.md).

## Overview

Dana now supports calling methods on objects returned by `use()` statements, enabling seamless integration with MCP services and A2A agents. This provides a more natural, object-oriented programming experience while maintaining Dana's simplicity.

---

## Basic MCP Connection

### Simple Service Connection
```python
# Connect to MCP service
websearch = use("mcp", url="http://localhost:8880/websearch")

# Call methods on the service
tools = websearch.list_tools()
log.info(f"Available tools: {tools}")

# Perform operations
search_results = websearch.search("Dana programming language")
log.info(f"Found {len(search_results)} search results")
```

### Named Service Connection  
```python
# Connect to named MCP service
database = use("mcp.database", "https://db.company.com/mcp")
weather_api = use("mcp.weather")

# Use services with method calls
db_status = database.health_check()
current_weather = weather_api.get_current("San Francisco")
```

---

## Object Method Call Patterns

### Method Calls with Arguments
```python
# MCP service with various argument types
api_client = use("mcp.weather")

# Positional arguments
forecast = api_client.get_forecast("New York", 7)

# Mixed arguments (positional + keyword-style)
detailed_forecast = api_client.get_detailed_forecast(
    "San Francisco", 
    days=5, 
    include_hourly=true,
    metric_units=true
)

# Process results
for day in detailed_forecast:
    summary = reason("Create weather summary", context=day)
    log.info(f"Weather: {summary}")
```

### Conditional Method Calls
```python
# Health checks and conditional operations
websearch = use("mcp", url="http://localhost:8880/websearch")

if websearch.health_check():
    # Service is healthy, proceed with operations
    tools = websearch.list_tools()
    
    if "search" in tools:
        results = websearch.search("market trends 2024")
        analysis = reason("Analyze market trends", context=results)
        log.info(f"Market analysis: {analysis}")
    else:
        log.warn("Search tool not available")
else:
    log.error("WebSearch service is not responding")
```

### Method Calls in Loops
```python
# Process multiple queries
database = use("mcp.database")
queries = [
    "SELECT * FROM users WHERE active = true",
    "SELECT COUNT(*) FROM orders WHERE status = 'pending'", 
    "SELECT * FROM products WHERE inventory < 10"
]

results = {}
for query in queries:
    try:
        result = database.execute_query(query)
        results[query] = result
        log.info(f"Query executed successfully: {query}")
    except Exception as e:
        log.error(f"Query failed: {query} - {e}")
        results[query] = none
```

---

## Resource Management with 'with' Statements

> **⚠️ Current Limitation**: `with` statements currently support only a single `as` clause. 
> Multiple resources require nested `with` statements.

### Scoped Resource Management
```python
# Automatic resource cleanup
with use("mcp.database", "https://db.company.com") as database:
    # Database connection active within this block
    users = database.query("SELECT * FROM users WHERE last_login > '2024-01-01'")
    
    for user in users:
        activity = database.get_user_activity(user.id)
        analysis = reason("Analyze user engagement patterns", context=activity)
        
        if "inactive" in analysis:
            database.update_user_status(user.id, "needs_reengagement")
    
    # Connection automatically closed after this block
```

### Multiple Resource Management
```python
# Manage multiple MCP services together - use nested statements
with use("mcp", url="http://localhost:8880/websearch") as websearch:
    with use("mcp.database") as database:
        with use("mcp.notifications") as notification_service:
            # Coordinate between services
            search_results = websearch.search("customer feedback analysis")
            
            # Store results in database
            storage_result = database.store_search_results(search_results)
            
            # Send notifications
            if storage_result.success:
                notification_service.send_alert(
                    "Search results processed and stored successfully",
                    channel="analytics"
                )
            
            # All services automatically cleaned up
```

---

## A2A Agent Integration

### Basic Agent Communication
```python
# Connect to specialized agents
research_agent = use("a2a.research-agent", "https://agents.company.com")
planning_agent = use("a2a.workflow-coordinator")

# Agents handle async operations automatically
market_data = research_agent.collect_market_data("technology sector")
analysis = research_agent.analyze_trends(market_data)

# Pass results between agents
action_plan = planning_agent.create_strategy(analysis)
execution_status = planning_agent.execute_plan(action_plan)

log.info(f"Strategy execution status: {execution_status}")
```

### Agent Coordination Workflow
```python
# Multi-agent coordination - use nested statements
with use("a2a.data-collector") as data_agent:
    with use("a2a.market-analyst") as analysis_agent:
        with use("a2a.report-generator") as reporting_agent:
            # Step 1: Data collection
            raw_data = data_agent.collect_from_sources([
                "financial_feeds",
                "news_apis", 
                "social_sentiment"
            ])
            
            # Step 2: Analysis
            market_analysis = analysis_agent.analyze_comprehensive(raw_data)
            risk_assessment = analysis_agent.assess_risks(market_analysis)
            
            # Step 3: Report generation
            executive_summary = reporting_agent.create_executive_summary([
                market_analysis,
                risk_assessment
            ])
            
            detailed_report = reporting_agent.generate_full_report(
                data=raw_data,
                analysis=market_analysis,
                risks=risk_assessment,
                summary=executive_summary
            )
            
            log.info("Multi-agent workflow completed successfully")
```

---

## Error Handling and Resilience

### Graceful Error Handling
```python
# Handle MCP service errors gracefully
websearch = use("mcp", url="http://localhost:8880/websearch")

try:
    # Attempt primary operation
    search_results = websearch.search("quarterly earnings reports")
    
    if len(search_results) > 0:
        analysis = reason("Analyze earnings trends", context=search_results)
        log.info(f"Analysis completed: {analysis}")
    else:
        log.warn("No search results found")
        
except Exception as error:
    log.error(f"Search operation failed: {error}")
    
    # Fallback to alternative approach
    log.info("Attempting fallback data source")
    fallback_data = load_cached_earnings_data()
    
    if fallback_data:
        analysis = reason("Analyze cached earnings data", context=fallback_data)
        log.info(f"Fallback analysis: {analysis}")
```

### Service Health Monitoring
```python
# Monitor multiple services
services = [
    use("mcp", url="http://localhost:8880/websearch"),
    use("mcp.database"),
    use("mcp.weather")
]

service_status = {}
for service in services:
    try:
        health = service.health_check()
        service_status[service.name] = health
        
        if health:
            log.info(f"Service {service.name} is healthy")
        else:
            log.warn(f"Service {service.name} reported unhealthy status")
            
    except Exception as e:
        log.error(f"Failed to check health for {service.name}: {e}")
        service_status[service.name] = false

# Overall system health assessment
healthy_services = [name for name, status in service_status if status]
log.info(f"Healthy services: {len(healthy_services)}/{len(services)}")
```

---

## Advanced Patterns

### Dynamic Service Discovery
```python
# Discover and use MCP services dynamically
service_registry = use("mcp.service-registry")
available_services = service_registry.list_services()

for service_info in available_services:
    if service_info.type == "data-processor":
        # Connect to discovered service
        processor = use("mcp", url=service_info.endpoint)
        
        # Check capabilities
        capabilities = processor.get_capabilities()
        
        if "financial_analysis" in capabilities:
            # Use the service
            result = processor.analyze_financial_data(market_data)
            log.info(f"Analysis from {service_info.name}: {result}")
```

### Pipeline Processing
```python
# Create processing pipeline with MCP services - use nested statements
with use("mcp.data-extractor") as extractor:
    with use("mcp.data-transformer") as transformer:
        with use("mcp.data-loader") as loader:
            # Pipeline step 1: Extract
            raw_data = extractor.extract_from_source("financial_reports")
            log.info(f"Extracted {len(raw_data)} records")
            
            # Pipeline step 2: Transform  
            clean_data = transformer.clean_and_normalize(raw_data)
            enriched_data = transformer.enrich_with_metadata(clean_data)
            log.info(f"Transformed {len(enriched_data)} records")
            
            # Pipeline step 3: Load
            load_result = loader.load_to_warehouse(enriched_data)
```

---

## Best Practices

### 1. Resource Management
- Always use `with` statements for services that need cleanup
- Check service health before performing operations
- Handle connection failures gracefully

### 2. Error Handling
- Wrap MCP calls in try/catch blocks for resilience
- Implement fallback strategies for critical operations
- Log errors with sufficient context for debugging

### 3. Performance
- Reuse service connections when possible
- Use async-capable agents for long-running operations
- Monitor service response times and implement timeouts

### 4. Security
- Validate service URLs and endpoints
- Use secure connection methods when available
- Implement proper authentication for sensitive services

---

## Troubleshooting

### Common Issues

**Service Connection Failures**
```python
# Debug connection issues
try:
    service = use("mcp", url="http://localhost:8880/websearch")
    health = service.health_check()
    log.info(f"Service health: {health}")
except Exception as e:
    log.error(f"Connection failed: {e}")
    # Check if service is running, URL is correct, etc.
```

**Method Call Errors**
```python
# Debug method call issues
websearch = use("mcp", url="http://localhost:8880/websearch")

# Check available methods
try:
    tools = websearch.list_tools()
    log.info(f"Available methods: {tools}")
except AttributeError as e:
    log.error(f"Method not available: {e}")
except Exception as e:
    log.error(f"Method call failed: {e}")
```

**Async Method Issues**  
```python
# Dana handles async automatically, but for debugging:
agent = use("a2a.research-agent")

try:
    # This may be async internally - Dana handles it
    result = agent.analyze_data(dataset)
    log.info(f"Analysis completed: {type(result)}")
except Exception as e:
    log.error(f"Async operation failed: {e}")
```

---

## Next Steps

- **Integration Testing**: Set up test environments for MCP services
- **Service Development**: Create custom MCP services for your use cases  
- **Agent Networks**: Build multi-agent systems using A2A patterns
- **Monitoring**: Implement comprehensive service monitoring and alerting

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 