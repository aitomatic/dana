# Extension Development Guide

*Comprehensive guide for building OpenDXA extensions, capabilities, and resources*

---

## Overview

This guide provides detailed instructions for extending OpenDXA through custom capabilities, resources, and functions. Learn how to build reusable, composable extensions that integrate seamlessly with the OpenDXA ecosystem.

## 🏗️ Extension Architecture

### Extension Types

**Capabilities**: Modular functionality that agents can use
```python
# Example: Custom analysis capability
class DataAnalysisCapability(BaseCapability):
    def get_functions(self):
        return {"analyze": self.analyze_data}
```

**Resources**: External service integrations
```python
# Example: Custom API resource
class WeatherAPIResource(BaseResource):
    def get_functions(self):
        return {"get_weather": self.fetch_weather}
```

**Functions**: Custom Dana language functions
```python
# Example: Custom transformation function
@register_function("transform_data")
def transform_data(data, method="normalize"):
    return apply_transformation(data, method)
```

### Extension Lifecycle
1. **Development**: Build and test extension locally
2. **Registration**: Register with OpenDXA system
3. **Distribution**: Package and share with community
4. **Maintenance**: Update and support extension

## 🔧 Developing Capabilities

### Basic Capability Structure

```python
from opendxa.agent.capability.base_capability import BaseCapability
from opendxa.common.mixins.configurable import Configurable
from opendxa.common.mixins.loggable import Loggable

class CustomAnalysisCapability(BaseCapability, Configurable, Loggable):
    """Custom capability for specialized data analysis."""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.setup_logging()
        
        # Initialize capability-specific resources
        self.models = self._load_analysis_models()
        self.cache = self._setup_cache()
    
    def get_functions(self) -> dict:
        """Return Dana functions provided by this capability."""
        return {
            "analyze_trends": self.analyze_trends,
            "detect_anomalies": self.detect_anomalies,
            "generate_forecast": self.generate_forecast,
        }
    
    def get_metadata(self) -> dict:
        """Return capability metadata for discovery."""
        return {
            "name": "custom_analysis",
            "version": "1.0.0",
            "description": "Advanced data analysis and forecasting",
            "author": "Your Organization",
            "tags": ["analysis", "forecasting", "anomaly-detection"],
            "requirements": ["numpy>=1.21.0", "pandas>=1.3.0"]
        }
    
    def analyze_trends(self, data, window_size=30, method="linear"):
        """Analyze trends in time series data."""
        self.log_info(f"Analyzing trends with method: {method}")
        
        try:
            # Implement trend analysis logic
            trends = self._calculate_trends(data, window_size, method)
            
            self.log_info(f"Trend analysis complete: {len(trends)} trends found")
            return {
                "trends": trends,
                "method": method,
                "confidence": self._calculate_confidence(trends)
            }
        except Exception as e:
            self.log_error(f"Trend analysis failed: {e}")
            raise
    
    def detect_anomalies(self, data, threshold=2.0, method="zscore"):
        """Detect anomalies in data using statistical methods."""
        self.log_info(f"Detecting anomalies with threshold: {threshold}")
        
        anomalies = self._detect_anomalies(data, threshold, method)
        
        return {
            "anomalies": anomalies,
            "count": len(anomalies),
            "threshold": threshold,
            "method": method
        }
    
    def generate_forecast(self, data, periods=30, confidence_level=0.95):
        """Generate forecasts based on historical data."""
        self.log_info(f"Generating forecast for {periods} periods")
        
        forecast = self._generate_forecast(data, periods, confidence_level)
        
        return {
            "forecast": forecast,
            "periods": periods,
            "confidence_level": confidence_level,
            "model_info": self._get_model_info()
        }
    
    # Private helper methods
    def _load_analysis_models(self):
        """Load pre-trained analysis models."""
        # Implementation here
        pass
    
    def _setup_cache(self):
        """Set up caching for expensive operations."""
        # Implementation here
        pass
    
    def _calculate_trends(self, data, window_size, method):
        """Core trend calculation logic."""
        # Implementation here
        pass
```

### Advanced Capability Features

**State Management**:
```python
class StatefulCapability(BaseCapability):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.state = {}
    
    def get_functions(self):
        return {
            "store_state": self.store_state,
            "retrieve_state": self.retrieve_state,
        }
    
    def store_state(self, key, value):
        """Store state for later retrieval."""
        self.state[key] = value
        return f"Stored {key}"
    
    def retrieve_state(self, key):
        """Retrieve previously stored state."""
        return self.state.get(key, None)
```

**Configuration Management**:
```python
class ConfigurableCapability(BaseCapability):
    def __init__(self, config: dict = None):
        super().__init__(config)
        
        # Set default configuration
        self.default_config = {
            "api_timeout": 30,
            "retry_attempts": 3,
            "cache_ttl": 3600
        }
        
        # Merge with user configuration
        self.effective_config = {**self.default_config, **(config or {})}
    
    def validate_config(self, config: dict) -> bool:
        """Validate configuration parameters."""
        required_keys = ["api_key", "base_url"]
        return all(key in config for key in required_keys)
```

## 🌐 Developing Resources

### Basic Resource Structure

```python
from opendxa.common.resource.base_resource import BaseResource
from opendxa.common.mixins.configurable import Configurable

class WeatherAPIResource(BaseResource, Configurable):
    """Resource for weather data integration."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.weather.com"):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()
    
    def get_functions(self) -> dict:
        """Return Dana functions for weather operations."""
        return {
            "get_current_weather": self.get_current_weather,
            "get_forecast": self.get_forecast,
            "get_historical": self.get_historical_weather,
        }
    
    def get_metadata(self) -> dict:
        """Return resource metadata."""
        return {
            "name": "weather_api",
            "version": "1.0.0",
            "description": "Weather data API integration",
            "provider": "WeatherAPI.com",
            "endpoints": ["current", "forecast", "historical"]
        }
    
    def get_current_weather(self, location: str, units: str = "metric"):
        """Get current weather for a location."""
        try:
            response = self.client.get(
                f"{self.base_url}/current",
                params={
                    "key": self.api_key,
                    "q": location,
                    "units": units
                }
            )
            return self._process_response(response)
        except Exception as e:
            self.log_error(f"Weather API error: {e}")
            raise
    
    def get_forecast(self, location: str, days: int = 7):
        """Get weather forecast for a location."""
        response = self.client.get(
            f"{self.base_url}/forecast",
            params={
                "key": self.api_key,
                "q": location,
                "days": days
            }
        )
        return self._process_response(response)
    
    def _initialize_client(self):
        """Initialize HTTP client with proper configuration."""
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": "OpenDXA-WeatherResource/1.0",
            "Accept": "application/json"
        })
        return session
    
    def _process_response(self, response):
        """Process API response and handle errors."""
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
```

### Resource Best Practices

**Error Handling**:
```python
class RobustResource(BaseResource):
    def api_call_with_retry(self, func, *args, **kwargs):
        """Make API calls with automatic retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.log_warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
```

**Caching**:
```python
class CachedResource(BaseResource):
    def __init__(self):
        super().__init__()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def cached_call(self, key, func, *args, **kwargs):
        """Make cached function calls."""
        if key in self.cache and not self._is_expired(key):
            return self.cache[key]["data"]
        
        result = func(*args, **kwargs)
        self.cache[key] = {
            "data": result,
            "timestamp": time.time()
        }
        return result
```

## ⚙️ Developing Dana Functions

### Function Registration

```python
from opendxa.dana.interpreter.function_registry import register_function

@register_function("custom_transform")
def custom_transform(data, transformation_type="normalize", options=None):
    """Custom data transformation function for Dana."""
    
    # Validate inputs
    if not data:
        raise ValueError("Data cannot be empty")
    
    options = options or {}
    
    # Apply transformation based on type
    if transformation_type == "normalize":
        return normalize_data(data, **options)
    elif transformation_type == "standardize":
        return standardize_data(data, **options)
    elif transformation_type == "scale":
        return scale_data(data, **options)
    else:
        raise ValueError(f"Unknown transformation type: {transformation_type}")

@register_function("batch_process")
def batch_process(items, processor_func, batch_size=10, parallel=False):
    """Process items in batches with optional parallelization."""
    
    results = []
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    
    if parallel:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_batch = {
                executor.submit(processor_func, batch): batch 
                for batch in batches
            }
            for future in concurrent.futures.as_completed(future_to_batch):
                results.extend(future.result())
    else:
        for batch in batches:
            results.extend(processor_func(batch))
    
    return results
```

### Advanced Function Features

**Type Validation**:
```python
from typing import Union, List, Dict, Any

@register_function("typed_function")
def typed_function(
    data: Union[List[int], List[float]], 
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Function with explicit type hints for better validation."""
    
    # Runtime type validation
    if not isinstance(data, list):
        raise TypeError(f"Expected list, got {type(data)}")
    
    if not all(isinstance(x, (int, float)) for x in data):
        raise TypeError("All data elements must be numeric")
    
    # Function implementation
    return {"processed": True, "count": len(data)}
```

**Documentation Integration**:
```python
@register_function("documented_function")
def documented_function(input_data, mode="default"):
    """
    Process input data with specified mode.
    
    Args:
        input_data: The data to process (any type)
        mode: Processing mode - "default", "advanced", or "minimal"
    
    Returns:
        dict: Processing results with metadata
    
    Examples:
        >>> result = documented_function([1, 2, 3], mode="advanced")
        >>> print(result["summary"])
        
    Raises:
        ValueError: If mode is not supported
    """
    # Implementation here
    pass
```

## 📦 Extension Packaging

### Package Structure
```
my_extension/
├── setup.py
├── README.md
├── requirements.txt
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
│       └── transform_functions.py
└── tests/
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
    description="Custom OpenDXA extension for specialized functionality",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "opendxa>=1.0.0",
        "requests>=2.25.0",
        "pandas>=1.3.0",
    ],
    entry_points={
        "opendxa.capabilities": [
            "analysis = my_extension.capabilities:AnalysisCapability",
        ],
        "opendxa.resources": [
            "weather = my_extension.resources:WeatherResource",
        ],
        "opendxa.functions": [
            "transforms = my_extension.functions:register_functions",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
```

## 🧪 Testing Extensions

### Unit Testing
```python
import pytest
from my_extension.capabilities import AnalysisCapability

class TestAnalysisCapability:
    def setup_method(self):
        """Set up test fixtures."""
        self.capability = AnalysisCapability()
    
    def test_analyze_trends(self):
        """Test trend analysis functionality."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = self.capability.analyze_trends(data)
        
        assert "trends" in result
        assert result["confidence"] > 0
        assert len(result["trends"]) > 0
    
    def test_invalid_data_handling(self):
        """Test handling of invalid data."""
        with pytest.raises(ValueError):
            self.capability.analyze_trends([])
```

### Integration Testing
```python
from opendxa.agent import Agent
from my_extension.capabilities import AnalysisCapability

def test_agent_integration():
    """Test capability integration with agents."""
    # Create agent with custom capability
    agent = Agent()
    agent.add_capability(AnalysisCapability())
    
    # Test Dana code execution
    result = agent.execute("""
    data = [1, 2, 3, 4, 5]
    trends = analyze_trends(data, method="linear")
    log(f"Found {len(trends['trends'])} trends", level="INFO")
    """)
    
    assert result.success
    assert "trends" in agent.context
```

## 📚 Extension Documentation

### API Documentation
```python
class DocumentedCapability(BaseCapability):
    """
    A well-documented capability for demonstration purposes.
    
    This capability provides advanced analysis functions that can be used
    in Dana programs for data processing and insight generation.
    
    Configuration:
        api_key (str): API key for external services
        cache_size (int): Maximum cache size (default: 1000)
        timeout (int): Request timeout in seconds (default: 30)
    
    Available Functions:
        - analyze_data: Perform comprehensive data analysis
        - generate_report: Create formatted analysis reports
        - validate_results: Validate analysis results for quality
    
    Examples:
        >>> from my_extension import DocumentedCapability
        >>> capability = DocumentedCapability(config={"api_key": "key123"})
        >>> agent.add_capability(capability)
    """
    
    def analyze_data(self, data, analysis_type="comprehensive"):
        """
        Perform data analysis with specified type.
        
        Args:
            data (list): Input data for analysis
            analysis_type (str): Type of analysis to perform
                - "comprehensive": Full statistical analysis
                - "basic": Simple descriptive statistics
                - "advanced": Advanced statistical modeling
        
        Returns:
            dict: Analysis results containing:
                - summary: Statistical summary
                - insights: Key findings
                - recommendations: Actionable recommendations
                - confidence: Confidence score (0-1)
        
        Raises:
            ValueError: If data is empty or invalid
            RuntimeError: If analysis fails due to computation errors
        
        Examples:
            >>> result = analyze_data([1, 2, 3, 4, 5])
            >>> print(result["summary"])
            >>> print(f"Confidence: {result['confidence']}")
        """
        # Implementation here
        pass
```

## 🚀 Extension Distribution

### Publishing to PyPI
```bash
# Build distribution packages
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

### Community Registry
- Submit extension to OpenDXA community registry
- Provide comprehensive documentation
- Include usage examples and tutorials
- Maintain compatibility with OpenDXA updates

### Best Practices
- Follow semantic versioning
- Maintain backward compatibility
- Provide migration guides for breaking changes
- Include comprehensive test suites
- Document configuration options thoroughly

---

*Ready to build your first extension? Start with our [Extension Template](https://github.com/aitomatic/opendxa-extension-template) or join our [Developer Community](https://discord.gg/opendxa) for support.*