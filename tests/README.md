# Dana Monorepo Tests

This directory contains pytest test orchestration for running tests across all Dana packages.

## Structure

```
tests/
└── test_all_packages.py   # Pytest test that runs all package suites
```

The actual test files are located in each package:
- `dana_agent/tests/` - Agent framework tests
- `dana_lang/tests/` - Language runtime tests
- `dana_studio/tests/` - Studio/UI tests

## Configuration

Each package has its own pytest configuration in its `pyproject.toml`:
- `dana_agent/pyproject.toml` → `[tool.pytest.ini_options]`
- `dana_lang/pyproject.toml` → `[tool.pytest.ini_options]`
- `dana_studio/pyproject.toml` → `[tool.pytest.ini_options]`

This allows each package to have:
- Custom test markers
- Different test filtering rules
- Package-specific pytest plugins
- Independent test configurations

## Usage

### Run All Tests

```bash
# Via Makefile (recommended)
make test

# Or directly with pytest
pytest tests/test_all_packages.py
pytest tests/test_all_packages.py -v

# Filter by package
pytest tests/test_all_packages.py -k agent      # Only dana_agent
pytest tests/test_all_packages.py -k lang       # Only dana_lang
pytest tests/test_all_packages.py -k studio     # Only dana_studio
```

### Run Individual Package Tests

```bash
# Dana Agent tests
make test-agent
# or
cd dana_agent && pytest tests/

# Dana Lang tests
make test-lang
# or
cd dana_lang && pytest tests/

# Dana Studio tests
make test-studio
# or
cd dana_studio && pytest tests/
```

## How It Works

The `test_all_packages.py` file contains pytest tests that:

1. **Run pytest sequentially** for each package in its own directory
2. **Each package uses its own** `pyproject.toml` pytest configuration
3. **Fail-fast behavior** - if one package fails, the test fails
4. **Environment variables** - sets `DANA_MOCK_LLM=true` for consistent testing
5. **Exit codes** - returns 0 if all pass, non-zero if any fail

Each test class (`TestDanaAgent`, `TestDanaLang`, `TestDanaStudio`) runs the full test suite for that package as a subprocess.

## Benefits

✅ **Pure pytest** - Works with all standard pytest features
✅ **Package independence** - Each package maintains its own test config
✅ **Easy to filter** - Use `-k` to run specific packages
✅ **Clear failures** - Know exactly which package failed
✅ **Maintainable** - Config lives with the package it tests
✅ **No magic** - Just straightforward pytest tests

## Test Markers

Each package defines its own markers in `pyproject.toml`. Common markers:

### dana_agent markers:
- `unit` - Unit tests
- `integration` - Integration tests
- `live` - Tests requiring live API access
- `windows_console` - Windows-specific tests
- `provider` - LLM provider-specific tests

### dana_lang markers:
- `unit` - Unit tests
- `integration` - Integration tests
- `live` - Tests requiring external services
- `deep` - Comprehensive tests
- `slow` - Slow tests
- `na_file` - Tests executing .na files
- `poet` - POET-related tests
- `dana` - Dana language tests
- `real_api` - Tests using real API keys

### dana_studio markers:
- `unit` - Unit tests
- `integration` - Integration tests
- `studio` - Studio-specific tests

## Examples

```bash
# Run all tests
make test

# Run with verbose output
pytest tests/test_all_packages.py -v

# Run only dana_agent tests
pytest tests/test_all_packages.py -k agent

# Run only dana_lang tests
pytest tests/test_all_packages.py -k lang

# Run individual package with its own markers
cd dana_agent && pytest tests/ -m "unit and not slow"
cd dana_lang && pytest tests/ -m "not live and not deep"
```
