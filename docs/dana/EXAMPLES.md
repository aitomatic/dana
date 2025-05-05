<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DANA Example Code

## Proposed Syntax for reason()

### Basic Invocation

```python
result = reason("What is the optimal approach given the current situation?")
```

### With F-string Integration

```python
analysis = reason(f"Analyze these temperature readings: {private.temp_readings}")
```

### With Context Passing

```python
decision = reason("Should we alert the operator?",
                context=[private.temp_readings, global.alert_thresholds])
```

### Scope References

```python
summary = reason("Summarize the system state", context=global.system)
```

### Mixed Context

```python
plan = reason("Develop a maintenance plan",
            context=[global.equipment, private.readings, execution.last_error])
```

### Parameter Options

#### Output Format

```python
json_result = reason("Analyze performance metrics", format="json")
```

#### LLM Parameters

```python
detailed_analysis = reason("Provide detailed failure analysis", 
                        temperature=0.2, 
                        max_tokens=1000)
```

#### Statement Form (No Assignment)

```python
reason("Log your observations about the current state", context=global)
```

#### Advanced: Multi-turn Reasoning

```python
conversation = group.new_conversation()
conversation.add("What trends do you see in the data?", context=private.metrics)
conversation.add("What might be causing the anomaly at timestamp 15:30?")
solution = conversation.add("What actions should we take?")
```

## Implementation Considerations

1. Context Resolution: Use DANA's existing scoping mechanism to resolve variables referenced in context
2. F-string Integration: Process f-strings first, then do reasoning (preserving the existing f-string behavior)
3. Return Value Handling: For JSON/structured formats, auto-convert to DANA's data structures
4. Assignment Semantics: Support optional assignment pattern (result = reason() vs reason())
5. Error Integration: Surface LLM errors through DANA's error handling system

## Examples In Context

### Monitor a temperature system and reason about anomalies

```python
private.temp = 75.5
private.previous_readings = [73.2, 74.1, 74.8, 75.1]
private.equipment = {"type": "hvac", "model": "XC-2000", "last_service": "2025-03-15"}
```

### Using the system data directly in the prompt

```python
analysis = reason(f"The current temperature is {private.temp}°F with recent readings of
{private.previous_readings}. Is this pattern normal?")
log(f"Analysis: {analysis}")
```

### Using context passing for complex objects
```python
if private.temp > 80:
    action = reason("What action should be taken for the equipment?", 
                    context=[private.temp, private.previous_readings, private.equipment],
                    format="json")

    if action.requires_maintenance:
        log_warning(f"Maintenance required: {action.reason}")
        global.alert = {"type": "maintenance", "reason": action.reason}
```

This design leverages DANA's existing strengths (f-strings, scoping, native data structures)
while adding powerful reasoning capabilities that feel native to the language.

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
