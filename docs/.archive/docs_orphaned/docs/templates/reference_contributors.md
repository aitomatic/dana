# [Feature Name] - Contributor Reference

<!--
Version: 1.0
Date: [Today's Date]
Status: [Draft | Review | Final]
-->

## Overview
**Brief Description**: [1-2 sentence summary of contribution opportunities]

## Extension Points

### [Extension Point 1]
**Purpose**: [What this extension point enables]
**Location**: `opendxa/contrib/[module]/[file].py`
**Extension Pattern**:
```python
from opendxa.common.mixins import Loggable

class CustomExtension(Loggable):
    """Custom extension implementation."""
    
    def __init__(self):
        super().__init__()
        # Initialize your extension
        
    def method(self):
        """Implement extension method."""
        self.logger.info("Extension method called")
        # Your implementation
```

### [Extension Point 2]
**Purpose**: [What this extension point enables]
**Location**: `opendxa/contrib/[module]/[file].py`
**Extension Pattern**:
```python
from opendxa.common.mixins import Loggable

class CustomExtension(Loggable):
    """Custom extension implementation."""
    
    def __init__(self):
        super().__init__()
        # Initialize your extension
        
    def method(self):
        """Implement extension method."""
        self.logger.info("Extension method called")
        # Your implementation
```

## Contribution Guidelines

### Code Style
- Follow PEP 8 style guide
- Use type hints for all functions
- Use f-strings for string formatting
- Use DXA_LOGGER for logging
- Apply Loggable mixin to classes

### Testing Requirements
```python
# tests/[module]/test_[feature].py
import pytest
from opendxa.[module] import [Component]

def test_extension():
    """Test extension functionality."""
    # Arrange
    extension = CustomExtension()
    
    # Act
    result = extension.method()
    
    # Assert
    assert result == expected_value
```

### Documentation Requirements
```python
def method(self, param1: type, param2: type) -> return_type:
    """Method description.
    
    Args:
        param1: Parameter description
        param2: Parameter description
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why this exception occurs
    """
    pass
```

## Development Workflow

### Local Development
```bash
# Setup development environment
cd opendxa/
uv run pip install -e .

# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check . && uv run ruff format .
```

### PR Process
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Run linter
6. Create PR

## Extension Patterns

### [Pattern 1]
**Use Case**: [When to use this pattern]
**Implementation**:
```python
from opendxa.common.mixins import Loggable

class PatternImplementation(Loggable):
    """Pattern implementation."""
    
    def __init__(self):
        super().__init__()
        # Pattern-specific initialization
        
    def method(self):
        """Pattern method implementation."""
        self.logger.info("Pattern method called")
        # Pattern implementation
```

### [Pattern 2]
**Use Case**: [When to use this pattern]
**Implementation**:
```python
from opendxa.common.mixins import Loggable

class PatternImplementation(Loggable):
    """Pattern implementation."""
    
    def __init__(self):
        super().__init__()
        # Pattern-specific initialization
        
    def method(self):
        """Pattern method implementation."""
        self.logger.info("Pattern method called")
        # Pattern implementation
```

## Common Pitfalls

### [Pitfall 1]
**Description**: [What to avoid]
**Solution**: [How to avoid it]
**Example**:
```python
# ❌ Wrong way
def method():
    print("Don't use print")
    
# ✅ Correct way
from opendxa.common.utils.logging import DXA_LOGGER

def method():
    DXA_LOGGER.info("Use DXA_LOGGER")
```

### [Pitfall 2]
**Description**: [What to avoid]
**Solution**: [How to avoid it]
**Example**:
```python
# ❌ Wrong way
def method():
    return "Value: " + str(var)
    
# ✅ Correct way
def method():
    return f"Value: {var}"
```

## Performance Guidelines

### [Guideline 1]
**Impact**: [Performance consideration]
**Implementation**:
```python
# Performance-optimized implementation
def optimized_method():
    # Implementation details
    pass
```

### [Guideline 2]
**Impact**: [Performance consideration]
**Implementation**:
```python
# Performance-optimized implementation
def optimized_method():
    # Implementation details
    pass
```

## Security Guidelines

### [Guideline 1]
**Requirement**: [Security requirement]
**Implementation**:
```python
# Secure implementation
def secure_method():
    # Security implementation
    pass
```

### [Guideline 2]
**Requirement**: [Security requirement]
**Implementation**:
```python
# Secure implementation
def secure_method():
    # Security implementation
    pass
```

## Resources

### Documentation
- [Link to style guide]
- [Link to testing guide]
- [Link to contribution guide]

### Examples
- [Link to example implementations]
- [Link to pattern examples]
- [Link to best practices]

### Tools
- [Link to development tools]
- [Link to testing tools]
- [Link to debugging tools]

## Support

### Getting Help
- **GitHub Issues**: [Link to issue tracker]
- **Contributor Documentation**: [Link to docs]
- **Community Support**: [Link to community]

### Mentoring
- **Code Review**: [Link to review process]
- **Mentorship Program**: [Link to program]
- **Office Hours**: [Link to schedule] 