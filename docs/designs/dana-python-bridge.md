<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[▲ Main Designs](./README.md) | [◀ Interpreter](./interpreter.md) | [Sandbox ▶](./sandbox.md)

# Dana-in-Python

**Status**: Design Phase  
**Module**: `opendxa.dana`

Seamless Dana-Python integration through a unified runtime architecture. Dana and Python share the same runtime, objects, and memory space - feeling like one unified language.

## Overview

Dana and Python operate as a **unified runtime** where objects, functions, and variables are shared transparently across language boundaries with zero overhead.

### Design Principles

1. **Module Integration**: Import Dana modules like Python modules and vice versa
2. **Transparent Interop**: Objects flow between languages without explicit conversion
3. **Unified Memory Model**: Variables exist simultaneously in both environments  
4. **Shared Runtime**: Dana and Python execute in the same process space
5. **Zero Overhead**: Cross-language calls are as fast as native calls


## Integration Patterns

### Step 1: Creating a Dana Module

```dana
# File: dana/trip_planner.na

def plan_trip(destination, budget, days):
    return reason(f"Plan a trip for {destination} with budget ${budget} in {days} days")

def get_weather_advice(destination, travel_date):
    return reason("Weather advice for travel to {destination} on {travel_date}")
```

### Step 2: Using Dana Module in Python

```python
# Dana modules are imported exactly like Python modules
import dana.trip_planner as trip_planner

# Call Dana functions directly - no special syntax
destination = "Tokyo"
budget = 3000
days = 7

# Dana function called like any Python function
trip_plan = trip_planner.plan_trip(destination, budget, days)
weather_advice = trip_planner.get_weather_advice(destination, "2025-06-15")

print(f"Trip to {destination}:")
print(f"Estimated cost: ${trip_plan['estimated_cost']}")
print(f"Weather advice: {weather_advice}")

# Use results in Python logic
if trip_plan['estimated_cost'] > budget:
    print("⚠️  Trip exceeds budget, consider adjustments")
else:
    print("✅ Trip fits within budget!")
```

## Unified Runtime Model

### Shared Object Space

```python
# Variables exist in both environments simultaneously
temperature = 98.6  # Python variable
# Automatically available as Dana variable (no bridging needed)

# Dana code sees Python objects directly
import dana.analyze_temp  # Dana module imported like Python module
result = analyze_temp(temperature)  # Direct function call, no conversion
```

### Module Integration

```python
# Import Dana modules exactly like Python modules
import dana.weather_analysis as weather
import dana.risk_assessment as risk

# Use Dana functions as if they were Python functions  
forecast = weather.analyze_conditions(temperature=72, humidity=0.6)
risk_level = risk.evaluate_scenario(forecast)
```

## Runtime Integration Features

### Unified Memory Space

```python
# Variables exist in both environments with zero overhead
class UserProfile:
    def __init__(self, name, preferences):
        self.name = name
        self.preferences = preferences

# Python object creation
user = UserProfile("Alice", {"risk_tolerance": "low"})

# Dana module sees the same object reference - no copying
import dana.personalization as personal
greeting = personal.create_greeting(user)  # Direct object access

# Modifications are visible in both environments
personal.update_preferences(user, {"new_pref": "value"})
print(user.preferences)  # Shows updated preferences
```

### Automatic Type Bridging

```python
# Python types automatically become Dana types
temperatures = [98.6, 99.1, 98.8, 101.2]  # Python list
sensor_config = {"threshold": 100.0, "alert_enabled": True}  # Python dict

# Dana functions accept Python types directly
import dana.monitoring as monitor
alerts = monitor.check_thresholds(temperatures, sensor_config)

# Return types flow back seamlessly
for alert in alerts:  # alerts is a Dana list, but works as Python list
    print(f"Alert: {alert.message} at {alert.timestamp}")
```

### Resource Pool Sharing

```python
# Resources automatically shared across runtime
from opendxa.common.resource.llm_resource import LLMResource

# Create resources in Python
llm = LLMResource(model="gpt-4")
database = DatabaseConnection("postgresql://...")

# Dana modules automatically access same resource instances
import dana.analysis as analysis
result = analysis.perform_reasoning()  # Uses same LLM instance

# No resource duplication or bridging overhead
import dana.data_processing as processing  
data = processing.query_sensors()  # Uses same database connection
```

## Advanced Features

### Context Managers

```python
from opendxa.dana import dana

# Set temporary context
with dana.context(user_id="123", session="active"):
    analysis = dana("reason('User behavior analysis')")
    # user_id and session available in Dana scope
```

### Async Support

```python
from opendxa.dana import dana_async

async def analyze_data():
    result = await dana_async("""
        analysis = reason("Analyze this data")
        return analysis
    """)
    return result
```


## Real-World Example

```python
# File: monitor_system.py
import pandas as pd
import dana.temperature_analysis as temp_analysis  # Dana module imported normally
import dana.alerting as alerting                  # Another Dana module

class TemperatureMonitor:
    def __init__(self):
        self.threshold = 100.0
        self.sensor_data = pd.read_csv('sensors.csv')
    
    def load_recent_readings(self):
        """Python method for data loading."""
        return self.sensor_data['temperature'].tail(10).tolist()
    
    def monitor_continuous(self):
        """Mixed Python/Dana monitoring system."""
        
        # Python data processing
        recent_temps = self.load_recent_readings()
        avg_temp = sum(recent_temps) / len(recent_temps)
        
        # Dana reasoning - called like any Python function
        risk_assessment = temp_analysis.assess_temperature_risk(
            average=avg_temp,
            readings=recent_temps,
            threshold=self.threshold
        )
        
        # Python control flow with Dana decisions
        if risk_assessment.risk_level > 0.7:
            # Dana alerting system
            alert_message = alerting.generate_alert(
                risk_assessment=risk_assessment,
                context={"monitor_id": "TEMP_001", "location": "server_room"}
            )
            
            # Python notification system
            self._send_notification(alert_message)
            
            return {
                "status": "alert_sent",
                "risk_level": risk_assessment.risk_level,
                "message": alert_message.content
            }
        
        return {"status": "normal", "average": avg_temp}
    
    def _send_notification(self, alert):
        """Python method for sending notifications."""
        print(f"🚨 ALERT: {alert.content}")
        print(f"📧 Sent to: {alert.recipients}")

# File: dana/temperature_analysis.na (Dana module)
def assess_temperature_risk(average, readings, threshold):
    # This is Dana code that can access Python objects directly
    trend_analysis = reason("Analyze temperature trend", {
        "recent_average": average,
        "all_readings": readings,
        "safety_threshold": threshold
    })
    
    risk_level = reason("Calculate risk level 0-1", {
        "trend": trend_analysis,
        "current_avg": average,
        "threshold": threshold
    })
    
    return {
        "risk_level": risk_level,
        "trend_analysis": trend_analysis,
        "recommendation": reason("What should we do?", {
            "risk": risk_level,
            "trend": trend_analysis
        })
    }

# File: dana/alerting.na (Dana module)  
def generate_alert(risk_assessment, context):
    alert_content = reason("Create alert message", {
        "risk": risk_assessment,
        "context": context,
        "urgency": "high" if risk_assessment.risk_level > 0.8 else "medium"
    })
    
    recipients = reason("Who should be notified?", {
        "risk_level": risk_assessment.risk_level,
        "location": context["location"]
    })
    
    return {
        "content": alert_content,
        "recipients": recipients,
        "timestamp": system:current_time,
        "priority": "high" if risk_assessment.risk_level > 0.8 else "medium"
    }

# Usage - seamless integration
monitor = TemperatureMonitor()
result = monitor.monitor_continuous()
print(f"System status: {result['status']}")
```

## Benefits of Unified Runtime Approach

### For Python Developers
- **Familiar Import System**: `import dana.module` just works
- **No New APIs**: Use Dana functions like Python functions
- **Transparent Types**: Python objects work in Dana, Dana objects work in Python
- **Gradual Adoption**: Add Dana reasoning to existing Python codebases incrementally

### For Dana Features
- **Full AI Reasoning**: Complete access to `reason()`, agent capabilities
- **Preserved Security**: Dana's scope model enforced at runtime level
- **Resource Efficiency**: Single LLM instance shared across both environments
- **Agent Workflows**: Dana's structured reasoning integrated into Python applications

## Trade-offs vs. Traditional Bridging

### Advantages over Bridge Pattern
- **Performance**: No serialization/deserialization overhead
- **Simplicity**: No special bridge APIs to learn
- **Memory Efficiency**: Single object instances, not copies
- **Developer Experience**: Feels like one language, not two

### Complexity Considerations
- **Runtime Integration**: More complex interpreter/compiler integration required
- **Debugging**: Stack traces span both languages
- **Error Handling**: Need unified error model across languages
- **Module System**: Custom import system implementation needed

## Implementation Phases

### Phase 1: Core Runtime Integration
```python
# Basic import system working
import dana.simple_module
result = simple_module.reason_about("hello world")
```

### Phase 2: Advanced Object Sharing
```python
# Complex object sharing, memory model integration
import dana.data_analysis
python_dataframe = pd.DataFrame(...)
dana_result = data_analysis.process(python_dataframe)  # Direct object passing
```

### Phase 3: Tooling & Developer Experience  
```python
# IDE support, debugging across languages, error integration
# Jupyter notebooks with mixed Python/Dana cells
# Performance profiling for cross-language calls
```

### Phase 4: Production & Performance
```python
# Compiler optimizations for cross-language calls
# Advanced debugging tools
# Enterprise monitoring and observability
```

## Comparison: Bridge vs. Unified Runtime

| Aspect | Traditional Bridge | Unified Runtime (This Design) |
|--------|-------------------|-------------------------------|
| **Import Style** | `from bridge import dana; dana("code")` | `import dana.module; module.function()` |
| **Object Passing** | Serialization/copying | Direct references |
| **Performance** | Overhead for conversions | Near-zero overhead |
| **Developer Model** | Two separate languages | One unified environment |
| **Learning Curve** | Bridge APIs to learn | Just import and use |
| **Memory Usage** | Duplicate objects | Shared objects |
| **Debugging** | Separate debug contexts | Unified stack traces |

## Conclusion

This **unified runtime design** creates a shared execution environment where Dana and Python feel like one language. Instead of bridging between separate environments, we create a **shared execution space** where:

- Dana modules import like Python modules
- Objects flow transparently without conversion
- Function calls have zero overhead
- Memory is shared, not duplicated
- Development feels natural and unified

This approach maximizes both **developer productivity** and **runtime performance** while preserving Dana's unique AI reasoning capabilities and security model.

---

**Related Documents:**
- [Dana Language Specification](./dana/language.md)
- [Interpreter Design](./interpreter.md)
- [Sandbox Security](./sandbox.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 