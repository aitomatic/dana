# Dana Initialization Library

The initialization library provides startup and bootstrap functionality for Dana applications.

## Purpose

This library contains utilities for:
- Environment variable loading and configuration
- Application startup initialization
- Configuration file setup
- Bootstrap utilities
- **Automatic startup sequence** - runs when module is imported

## Structure

```
dana/libs/initlib/
├── __init__.py      # Module exports and startup sequence
├── env.py           # Environment loading utilities
└── README.md        # This file
```

## Automatic Startup Sequence

The startup sequence is automatically triggered when the main Dana module is imported:

```python
import dana  # This automatically imports dana.libs.initlib and runs the startup sequence
```

The startup sequence performs essential startup activities:

### Phase 1: Essential Environment & Configuration Setup
- **Environment Loading**: Loads `.env` files and sets `DANA_CONFIG` environment variable
- **Configuration System**: Initializes `ConfigLoader` (singleton pattern)

### Phase 2: Core System Initialization (Conditional)
- **Module System**: Initializes Dana module system with default search paths
- **Logging System**: Configures logging with default settings
- **Test Mode**: Skips heavy initialization when `DANA_TEST_MODE=1` is set

### Phase 3: Deferred Initialization
- **Core Library Functions**: Registration deferred to `DanaInterpreter` creation
- **Heavy Resources**: LLMResource, DanaSandbox, API services remain lazy-loaded

## Functions

### `dana_load_dotenv()`

Loads environment variables and sets up Dana configuration.

**Parameters:**
- `dot_env_file_path`: Optional path to a .env file (Path or str)

**What it does:**
1. Loads environment variables from the specified .env file using python-dotenv
2. Sets the `DANA_CONFIG` environment variable to point to the default `dana_config.json` file if not already set

**Usage:**
```python
from dana.libs.initlib import dana_load_dotenv

# Load .env files from all locations in search order
dana_load_dotenv()
```

## Environment Variables

### `DANA_TEST_MODE=1`
When set, skips heavy initialization to improve test performance:
- Module system initialization
- Logging configuration
- Core library function registration

### `DANA_CONFIG`
Set automatically to point to the default `dana_config.json` file location.

## Integration

This library is designed to be used during application startup, typically in:
- CLI entry points
- Server startup scripts
- Application bootstrap code

**Automatic Usage**: The startup sequence runs automatically when you import Dana:
```python
import dana  # Startup sequence runs automatically
```

**Manual Usage**: You can also call functions manually if needed:
```python
from dana.libs.initlib import dana_load_dotenv
dana_load_dotenv()
```

**Direct Module Import**: You can also import the initlib module directly:
```python
import dana.libs.initlib  # Startup sequence runs immediately
```

## What's Deferred

The following components are intentionally NOT initialized during startup to maintain fast startup times:

1. **LLMResource** - Requires API keys and network connectivity
2. **DanaSandbox** - Heavy resource initialization
3. **API Services** - Network-dependent services
4. **Standard Library Functions** - Loaded on-demand
5. **Custom Module Search Paths** - Set per DanaSandbox instance
6. **Heavy Configuration Loading** - Lazy loading of `dana_config.json`

This design ensures critical systems are ready immediately while keeping heavy components lazy-loaded for optimal performance. 