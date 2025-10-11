| [← Frameworks Overview](../README.md) | [CORRAL →](./corral_design.md) |
|---|---|

# POET Framework - Simplified Directory Structure

**Author:** Dana Language Team
**Date:** 2025-01-22
**Version:** 1.0.0
**Status:** Implementation

**P**erceive → **O**perate → **E**nforce → **T**rain
*Simple, Focused Function Enhancement for Dana*

## 🎯 KISS Design Philosophy

Following KISS/YAGNI principles, this framework provides **only what's needed** for reliable function enhancement. No premature complexity, no over-engineering.

## 📁 Simplified Directory Structure

```
poet/
├── core/           # 🔧 Essential POET components (decorator, types, errors)
├── config/         # ⚙️ Simple domain configuration helpers
├── utils/          # 🛠️ Basic testing and debugging tools
├── domains/        # 🎯 Domain-specific templates (base only)
├── phases/         # 🔄 Simple P→O→E→T phase implementations
└── README.md       # 📖 This file
```

---

## 🔧 `core/` - Essential Components Only

**Purpose**: Core POET functionality without unnecessary complexity

### Files & Purpose:

- **`decorator.py`** - The `@poet` decorator
  - *Why needed*: Main entry point for POET enhancement
  - *Contains*: Simple decorator logic and function wrapping

- **`enhancer.py`** - Dana code generation for POET phases
  - *Why needed*: Generates Dana-native code for enhanced functions
  - *Contains*: Basic code generation logic

- **`types.py`** - Core data structures
  - *Why needed*: Shared types used across components
  - *Contains*: `POETConfig`, `POETResult`

- **`errors.py`** - Basic exception types
  - *Why needed*: Consistent error handling
  - *Contains*: `POETError`, `POETTranspilationError`

---

## ⚙️ `config/` - Simple Configuration

**Purpose**: Easy domain setup without complex abstractions

### Files & Purpose:

- **`domain_wizards.py`** - Quick setup functions for common domains
  - *Why needed*: Developers shouldn't configure everything manually
  - *Contains*: `financial_services()`, `healthcare()`, `data_processing()`, etc.

---

## 🛠️ `utils/` - Basic Development Tools

**Purpose**: Simple testing and debugging utilities

### Files & Purpose:

- **`testing.py`** - Testing and debugging utilities
  - *Why needed*: Developers need to test enhanced functions
  - *Contains*: `test_poet_function()`, `debug_poet_function()`, basic benchmarks

## 🎯 `domains/` - Domain Templates

**Purpose**: Simple templates for different problem domains

### Files & Purpose:

- **`base.py`** - Base domain template
  - *Why needed*: Common foundation for domain-specific enhancements
  - *Contains*: `DomainTemplate` base class, `BaseDomainTemplate`

- **`registry.py`** - Simple domain lookup
  - *Why needed*: Find available domains
  - *Contains*: `DomainRegistry` for managing domains

---

## 🔄 `phases/` - Simple P→O→E→T Implementation

**Purpose**: Core phases that enhance function execution

### Files & Purpose:

- **`perceive.py`** - Input validation
  - *Why needed*: Ensure inputs are valid before processing
  - *Contains*: `PerceivePhase` for basic input validation

- **`operate.py`** - Function execution with retry logic
  - *Why needed*: Add retry logic for reliability
  - *Contains*: `OperatePhase` for resilient function execution

- **`enforce.py`** - Output validation
  - *Why needed*: Ensure outputs meet basic quality standards
  - *Contains*: `EnforcePhase` for output validation

- **`train.py`** - Learning and feedback collection
  - *Why needed*: Complete the POET pattern with simple learning
  - *Contains*: `TrainPhase` for basic performance tracking and insights

---

## 🔗 Simple Import Pattern

```python
# ✅ Basic usage
from dana_lang.frameworks.poet import poet, POETConfig
from dana_lang.frameworks.poet import financial_services, healthcare
from dana_lang.frameworks.poet import debug_poet_function, test_poet_function
from dana_lang.frameworks.poet import perceive, operate, enforce, train  # Full P→O→E→T
```

---

## 🚀 Quick Start Examples

### Basic Enhancement
```python
from dana_lang.frameworks.poet import poet

@poet(domain="financial_services", retries=3, enable_training=True)
def calculate_portfolio_value(holdings, market_data):
    return sum(h.shares * market_data[h.symbol].price for h in holdings)
```

### Domain-Specific Setup
```python
from dana_lang.frameworks.poet import financial_services

# Quick domain configuration
config = financial_services(retries=5, timeout=30)
enhanced_func = poet(**config)(calculate_risk)
```

### Testing & Debugging
```python
from dana_lang.frameworks.poet import test_poet_function, debug_poet_function

# Test enhanced function
test_poet_function(enhanced_func, test_cases=[...])

# Debug phase execution
debug_poet_function(enhanced_func, phase="perceive")
```

---

## 🎯 KISS Design Principles

1. **Keep It Simple**: Only essential functionality
2. **No Premature Optimization**: Build what's needed today
3. **Clear Responsibility**: Each module has one clear purpose
4. **Easy to Understand**: Intuitive organization and naming
5. **Minimal Dependencies**: Reduce complexity and maintenance

---

## 🗑️ What We Removed (Following KISS)

**Removed over-engineered components:**
- ❌ `progressive.py` - Complex 4-level migration system
- ❌ `feedback.py` - Premature learning/training system
- ❌ `storage.py` - Complex file-based persistence
- ❌ `client.py` - Unused remote API client
- ❌ Domain-specific templates without proven use cases
- ❌ Complex phase result objects
- ❌ Elaborate debugging infrastructure

**Result**: ~70% reduction in complexity while maintaining core functionality.
