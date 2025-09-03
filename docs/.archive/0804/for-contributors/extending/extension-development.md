# Extension Development Guide

*Comprehensive guide for building Dana extensions, capabilities, and resources*

---

## Overview

This guide provides detailed instructions for extending Dana through custom capabilities, resources, and functions. Learn how to build reusable, composable extensions that integrate seamlessly with the Dana ecosystem.

## Extension Types

### 1. Capabilities
Capabilities extend agent functionality with reusable, composable modules:
- **Definition**: Reusable agent functionality
- **Registration**: Register with Dana system
- **Integration**: Seamless agent integration

### 2. Resources
Resources provide external service integration:
- **Definition**: External service connectors
- **Registration**: Register with resource manager
- **Integration**: Available to all agents

### 3. Functions
Functions extend the Dana language:
- **Definition**: Custom Dana language functions
- **Registration**: Register with function registry
- **Integration**: Available in Dana code

## Creating Capabilities

### Basic Capability Structure

```python
from opendxa.agent.capability.base_capability import BaseCapability
from opendxa.common.mixins.configurable import Configurable
from opendxa.common.mixins.loggable import Loggable

class CustomAnalysisCapability(BaseCapability, Configurable, Loggable):
    """Custom capability for specialized data analysis."""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.analysis_model = self._load_model()
        self.info("CustomAnalysisCapability initialized")
    
    def get_functions(self) -> dict:
        """Return Dana functions provided by this capability."""
        return {
            "analyze_data": self.analyze_data,
            "generate_insights": self.generate_insights,
            "validate_data": self.validate_data
        }
    
    def analyze_data(self, data: list, analysis_type: str = "standard") -> dict:
        """Analyze data using custom algorithms."""
        self.info(f"Analyzing {len(data)} data points with {analysis_type} analysis")
        
        if analysis_type == "statistical":
            result = self._statistical_analysis(data)
        elif analysis_type == "ml":
            result = self._ml_analysis(data)
        else:
            result = self._standard_analysis(data)
        
        return {
            "analysis_type": analysis_type,
            "data_points": len(data),
            "result": result,
            "confidence": self._calculate_confidence(result)
        }
    
    def generate_insights(self, analysis_results: dict) -> list:
        """Generate insights from analysis results."""
        self.info("Generating insights from analysis results")
        
        insights = []
        if analysis_results.get("confidence", 0) > 0.8:
            insights.append("High confidence in analysis results")
        
        if analysis_results.get("data_points", 0) > 1000:
            insights.append("Large dataset provides robust analysis")
        
        return insights
    
    def validate_data(self, data: list) -> dict:
        """Validate data quality and structure."""
        self.info(f"Validating {len(data)} data points")
        
        validation_result = {
            "valid": True,
            "issues": [],
            "quality_score": 1.0
        }
        
        # Check for missing values
        missing_count = sum(1 for item in data if item is None)
        if missing_count > 0:
            validation_result["issues"].append(f"{missing_count} missing values")
            validation_result["quality_score"] -= 0.1 * (missing_count / len(data))
        
        # Check data types
        if not all(isinstance(item, (int, float)) for item in data if item is not None):
            validation_result["issues"].append("Non-numeric values found")
            validation_result["quality_score"] -= 0.2
        
        validation_result["valid"] = validation_result["quality_score"] > 0.7
        return validation_result
    
    def _load_model(self):
        """Load analysis model."""
        # Implementation for loading ML model or analysis tools
        return None
    
    def _statistical_analysis(self, data: list) -> dict:
        """Perform statistical analysis."""
        return {
            "mean": sum(data) / len(data),
            "median": sorted(data)[len(data) // 2],
            "std": self._calculate_std(data)
        }
    
    def _ml_analysis(self, data: list) -> dict:
        """Perform machine learning analysis."""
        # Implementation for ML analysis
        return {"ml_result": "placeholder"}
    
    def _standard_analysis(self, data: list) -> dict:
        """Perform standard analysis."""
        return {
            "min": min(data),
            "max": max(data),
            "count": len(data)
        }
    
    def _calculate_std(self, data: list) -> float:
        """Calculate standard deviation."""
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5
    
    def _calculate_confidence(self, result: dict) -> float:
        """Calculate confidence score for analysis."""
        # Simple confidence calculation
        return 0.85
```

### Advanced Capability Features

```python
class AdvancedAnalysisCapability(BaseCapability):
    """Advanced capability with async support and caching."""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.cache = {}
        self.cache_ttl = self.get_config("cache_ttl", 3600)
    
    async def async_analyze_data(self, data: list) -> dict:
        """Async data analysis for large datasets."""
        cache_key = hash(str(data))
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Perform async analysis
        result = await self._perform_async_analysis(data)
        
        # Cache result
        self.cache[cache_key] = result
        return result
    
    def get_metadata(self) -> dict:
        """Return capability metadata."""
        return {
            "name": "AdvancedAnalysisCapability",
            "version": "1.0.0",
            "description": "Advanced data analysis with async support",
            "author": "Your Name",
            "dependencies": ["numpy", "pandas"]
        }
```

## Creating Resources

### Basic Resource Structure

```python
from opendxa.common.resource.base_resource import BaseResource
from opendxa.common.mixins.configurable import Configurable
import requests
import json

class WeatherResource(BaseResource, Configurable):
    """Resource for weather data integration."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.weatherapi.com/v1"):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Dana-WeatherResource/1.0",
            "Accept": "application/json"
        })
    
    def get_functions(self) -> dict:
        """Return Dana functions for weather operations."""
        return {
            "get_current_weather": self.get_current_weather,
            "get_forecast": self.get_forecast,
            "get_weather_history": self.get_weather_history
        }
    
    def get_current_weather(self, location: str) -> dict:
        """Get current weather for a location."""
        try:
            response = self.session.get(
                f"{self.base_url}/current.json",
                params={
                    "key": self.api_key,
                    "q": location,
                    "aqi": "no"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "location": data["location"]["name"],
                "temperature": data["current"]["temp_c"],
                "condition": data["current"]["condition"]["text"],
                "humidity": data["current"]["humidity"],
                "wind_speed": data["current"]["wind_kph"]
            }
        except requests.RequestException as e:
            raise ResourceError(f"Weather API request failed: {e}")
    
    def get_forecast(self, location: str, days: int = 3) -> list:
        """Get weather forecast for multiple days."""
        try:
            response = self.session.get(
                f"{self.base_url}/forecast.json",
                params={
                    "key": self.api_key,
                    "q": location,
                    "days": days,
                    "aqi": "no"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            forecast = []
            
            for day in data["forecast"]["forecastday"]:
                forecast.append({
                    "date": day["date"],
                    "max_temp": day["day"]["maxtemp_c"],
                    "min_temp": day["day"]["mintemp_c"],
                    "condition": day["day"]["condition"]["text"],
                    "chance_of_rain": day["day"]["daily_chance_of_rain"]
                })
            
            return forecast
        except requests.RequestException as e:
            raise ResourceError(f"Weather forecast request failed: {e}")
    
    def get_weather_history(self, location: str, date: str) -> dict:
        """Get historical weather data."""
        try:
            response = self.session.get(
                f"{self.base_url}/history.json",
                params={
                    "key": self.api_key,
                    "q": location,
                    "dt": date
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "date": date,
                "max_temp": data["forecast"]["forecastday"][0]["day"]["maxtemp_c"],
                "min_temp": data["forecast"]["forecastday"][0]["day"]["mintemp_c"],
                "total_precip": data["forecast"]["forecastday"][0]["day"]["totalprecip_mm"]
            }
        except requests.RequestException as e:
            raise ResourceError(f"Weather history request failed: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        self.session.close()
```

## Creating Dana Functions

### Basic Function Registration

```python
from opendxa.dana.interpreter.function_registry import register_function

@register_function("custom_transform")
def custom_transform(data: list, transformation_type: str = "default") -> list:
    """Custom data transformation function for Dana."""
    if transformation_type == "normalize":
        return normalize_data(data)
    elif transformation_type == "aggregate":
        return aggregate_data(data)
    elif transformation_type == "filter":
        return filter_data(data)
    else:
        return apply_default_transform(data)

def normalize_data(data: list) -> list:
    """Normalize data to 0-1 range."""
    if not data:
        return []
    
    min_val = min(data)
    max_val = max(data)
    
    if max_val == min_val:
        return [0.5] * len(data)
    
    return [(x - min_val) / (max_val - min_val) for x in data]

def aggregate_data(data: list) -> dict:
    """Aggregate data with statistics."""
    if not data:
        return {"count": 0, "sum": 0, "mean": 0}
    
    return {
        "count": len(data),
        "sum": sum(data),
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data)
    }

def filter_data(data: list) -> list:
    """Filter out invalid data points."""
    return [x for x in data if x is not None and not (isinstance(x, float) and math.isnan(x))]

def apply_default_transform(data: list) -> list:
    """Apply default transformation."""
    return data
```

### Advanced Function Features

```python
@register_function("advanced_analysis")
def advanced_analysis(data: list, options: dict = None) -> dict:
    """Advanced data analysis with multiple algorithms."""
    if options is None:
        options = {}
    
    algorithms = options.get("algorithms", ["statistical", "outlier_detection"])
    result = {}
    
    if "statistical" in algorithms:
        result["statistical"] = statistical_analysis(data)
    
    if "outlier_detection" in algorithms:
        result["outliers"] = detect_outliers(data)
    
    if "trend_analysis" in algorithms:
        result["trends"] = analyze_trends(data)
    
    return result

def statistical_analysis(data: list) -> dict:
    """Perform comprehensive statistical analysis."""
    if not data:
        return {}
    
    n = len(data)
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    std = variance ** 0.5
    
    return {
        "count": n,
        "mean": mean,
        "median": sorted(data)[n // 2],
        "std": std,
        "variance": variance,
        "min": min(data),
        "max": max(data),
        "range": max(data) - min(data)
    }

def detect_outliers(data: list, threshold: float = 2.0) -> list:
    """Detect outliers using z-score method."""
    if len(data) < 3:
        return []
    
    mean = sum(data) / len(data)
    std = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
    
    outliers = []
    for i, value in enumerate(data):
        z_score = abs((value - mean) / std) if std > 0 else 0
        if z_score > threshold:
            outliers.append({"index": i, "value": value, "z_score": z_score})
    
    return outliers

def analyze_trends(data: list) -> dict:
    """Analyze trends in time series data."""
    if len(data) < 2:
        return {"trend": "insufficient_data"}
    
    # Simple linear trend analysis
    x_values = list(range(len(data)))
    n = len(data)
    
    sum_x = sum(x_values)
    sum_y = sum(data)
    sum_xy = sum(x * y for x, y in zip(x_values, data))
    sum_x2 = sum(x * x for x in x_values)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    
    if slope > 0.01:
        trend = "increasing"
    elif slope < -0.01:
        trend = "decreasing"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "slope": slope,
        "correlation": calculate_correlation(x_values, data)
    }

def calculate_correlation(x: list, y: list) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)
    sum_y2 = sum(yi * yi for yi in y)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
    
    return numerator / denominator if denominator != 0 else 0.0
```

## Using Capabilities in Dana Code

### Basic Usage

```dana
# Load and use custom capability
analysis_capability = load_capability("custom_analysis")

# Analyze data
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
result = analysis_capability.analyze_data(data, "statistical")

# Generate insights
insights = analysis_capability.generate_insights(result)
log(f"Analysis insights: {insights}", level="INFO")

# Validate data
validation = analysis_capability.validate_data(data)
if validation.valid:
    log("Data validation passed", level="INFO")
else:
    log(f"Data validation failed: {validation.issues}", level="ERROR")
```

### Advanced Usage with POET

```dana
# Use capability with POET enhancement
@poet(domain="data_analysis", timeout=60.0)
def comprehensive_analysis(data, analysis_type="comprehensive"):
    # Load capability
    analysis_cap = load_capability("custom_analysis")
    
    # Perform analysis with domain intelligence
    result = analysis_cap.analyze_data(data, analysis_type)
    
    # Generate AI-powered insights
    insights = reason(f"Analyze these results: {result}")
    
    return {
        "analysis": result,
        "ai_insights": insights,
        "confidence": result.confidence
    }

# Execute enhanced analysis
data = load_large_dataset()
analysis_result = comprehensive_analysis(data, "ml")
```

## Using Resources in Dana Code

### Weather Resource Example

```dana
# Load weather resource
weather = load_resource("weather", api_key="your_api_key")

# Get current weather
current = weather.get_current_weather("San Francisco")
log(f"Current weather in SF: {current.temperature}°C, {current.condition}", level="INFO")

# Get forecast
forecast = weather.get_forecast("San Francisco", 5)
for day in forecast:
    log(f"Forecast for {day.date}: {day.max_temp}°C, {day.condition}", level="INFO")

# Get historical data
history = weather.get_weather_history("San Francisco", "2024-01-15")
log(f"Historical weather: {history.max_temp}°C, {history.total_precip}mm rain", level="INFO")
```

### Resource Error Handling

```dana
# Robust resource usage
try:
    weather = load_resource("weather", api_key="your_api_key")
    current = weather.get_current_weather("San Francisco")
    return current
except ResourceError as error:
    log(f"Weather service unavailable: {error}", level="ERROR")
    return {"error": "weather_service_unavailable"}
except Exception as error:
    log(f"Unexpected error: {error}", level="ERROR")
    return {"error": "unexpected_error"}
```

## Using Custom Functions in Dana Code

### Basic Function Usage

```dana
# Use custom transformation function
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Normalize data
normalized = custom_transform(data, "normalize")
log(f"Normalized data: {normalized}", level="DEBUG")

# Aggregate data
aggregated = custom_transform(data, "aggregate")
log(f"Data summary: {aggregated}", level="INFO")

# Filter data
filtered = custom_transform(data, "filter")
log(f"Filtered data: {filtered}", level="DEBUG")
```

### Advanced Analysis Usage

```dana
# Use advanced analysis function
data = [10, 15, 20, 25, 30, 35, 40, 45, 50, 1000]  # Note the outlier

# Perform comprehensive analysis
analysis = advanced_analysis(data, {
    "algorithms": ["statistical", "outlier_detection", "trend_analysis"]
})

# Process results
if "outliers" in analysis:
    for outlier in analysis.outliers:
        log(f"Outlier detected at index {outlier.index}: {outlier.value}", level="WARNING")

if "trends" in analysis:
    log(f"Data trend: {analysis.trends.trend}", level="INFO")
    log(f"Trend slope: {analysis.trends.slope}", level="DEBUG")

# Use AI to interpret results
interpretation = reason(f"""
Analyze these statistical results:
- Statistical: {analysis.statistical}
- Outliers: {analysis.outliers}
- Trends: {analysis.trends}

Provide insights about this dataset.
""")

log(f"AI interpretation: {interpretation}", level="INFO")
```

## Packaging and Distribution

### Extension Package Structure

```
my-dana-extension/
├── setup.py
├── README.md
├── LICENSE
├── my_extension/
│   ├── __init__.py
│   ├── capabilities/
│   │   ├── __init__.py
│   │   └── analysis_capability.py
│   ├── resources/
│   │   ├── __init__.py
│   │   └── weather_resource.py
│   └── functions/
│       ├── __init__.py
│       └── custom_functions.py
└── tests/
    ├── __init__.py
    ├── test_capabilities.py
    ├── test_resources.py
    └── test_functions.py
```

### Setup Configuration

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="opendxa-my-extension",
    version="1.0.0",
    description="Custom Dana extension for specialized functionality",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "opendxa>=1.0.0",
        "requests>=2.25.0",
        "numpy>=1.20.0"
    ],
    entry_points={
        "opendxa.capabilities": [
            "my_analysis = my_extension.capabilities.analysis_capability:CustomAnalysisCapability",
        ],
        "opendxa.resources": [
            "weather = my_extension.resources.weather_resource:WeatherResource",
        ],
        "opendxa.functions": [
            "custom_transform = my_extension.functions.custom_functions:custom_transform",
            "advanced_analysis = my_extension.functions.custom_functions:advanced_analysis",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
```

## Testing Extensions

### Unit Tests

```python
# tests/test_capabilities.py
import pytest
from my_extension.capabilities.analysis_capability import CustomAnalysisCapability

class TestCustomAnalysisCapability:
    def test_initialization(self):
        """Test capability initialization."""
        capability = CustomAnalysisCapability()
        assert capability is not None
        assert "analyze_data" in capability.get_functions()
    
    def test_analyze_data(self):
        """Test data analysis functionality."""
        capability = CustomAnalysisCapability()
        data = [1, 2, 3, 4, 5]
        
        result = capability.analyze_data(data, "statistical")
        
        assert result["analysis_type"] == "statistical"
        assert result["data_points"] == 5
        assert "result" in result
        assert "confidence" in result
    
    def test_generate_insights(self):
        """Test insight generation."""
        capability = CustomAnalysisCapability()
        analysis_results = {"confidence": 0.9, "data_points": 1500}
        
        insights = capability.generate_insights(analysis_results)
        
        assert isinstance(insights, list)
        assert len(insights) > 0
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
from opendxa.agent import Agent

class TestExtensionIntegration:
    def test_capability_integration(self):
        """Test capability integration with agent."""
        agent = Agent("test_agent")
        agent.add_capability("my_analysis")
        
        # Test that capability functions are available
        functions = agent.get_available_functions()
        assert "analyze_data" in functions
    
    def test_resource_integration(self):
        """Test resource integration."""
        # Test resource loading and usage
        pass
    
    def test_function_integration(self):
        """Test function integration in Dana code."""
        # Test custom functions in Dana execution
        pass
```

## Best Practices

### 1. Error Handling
- Use appropriate exception types
- Provide meaningful error messages
- Implement graceful degradation

### 2. Configuration
- Make extensions configurable
- Use sensible defaults
- Validate configuration parameters

### 3. Logging
- Use appropriate log levels
- Include context in log messages
- Avoid logging sensitive information

### 4. Performance
- Optimize for common use cases
- Implement caching where appropriate
- Monitor resource usage

### 5. Documentation
- Document all public APIs
- Provide usage examples
- Include configuration options

## Publishing Extensions

### 1. Prepare for Release
- Update version numbers
- Write release notes
- Test thoroughly

### 2. Package and Distribute
- Build distribution packages
- Upload to PyPI
- Update documentation

### 3. Community Integration
- Submit extension to Dana community registry
- Maintain compatibility with Dana updates
- Respond to user feedback

---

*Ready to build your first extension? Start with our [Extension Template](https://github.com/aitomatic/opendxa-extension-template) or join our [Developer Community](https://discord.gg/opendxa) for support.*