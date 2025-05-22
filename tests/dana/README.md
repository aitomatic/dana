# Testing Dana with LLM Mocking

## Overview

Dana tests, especially those involving the `reason` function, need to interact with LLMs. To avoid making real API calls during testing, we've implemented a mocking system.

## Mocking System

The mocking system has two layers:

1. **Environment Variable Control**:
   - `OPENDXA_MOCK_LLM=true` (default): Uses mock LLM responses
   - `OPENDXA_USE_REAL_LLM=true`: Forces real LLM calls

2. **Function Parameter Control**:
   - `reason_function(..., use_mock=True)`: Forces mock response
   - `reason_function(..., use_mock=False)`: Forces real LLM call
   - `reason_function(...)`: Uses environment variable setting

## Running Tests

### Regular Test Runs (No Real LLM Calls)

```bash
# Run normal tests (mocked LLM calls)
pytest tests/dana/
```

### Running with Real LLM Calls

```bash
# Run tests with real LLM calls
OPENDXA_USE_REAL_LLM=true pytest tests/dana/
```

### Running Live Tests

Some tests are marked with `@pytest.mark.live` and are skipped by default:

```bash
# Run only live tests
pytest -m live tests/dana/

# Run all tests including live ones
pytest --no-skip tests/dana/
```

## Implementation Details

1. The `reason_function` checks:
   - First: The `use_mock` parameter
   - Second: The `OPENDXA_MOCK_LLM` environment variable

2. When mocking is enabled, `LLMResource.with_mock_llm_call(True)` is used to create a mocked client.

3. Tests have been updated to respect this pattern and use mock LLM calls by default.

## Adding New Tests

When adding new tests that use the `reason` function:

1. Use `use_mock=True` parameter in the `reason_function` call, or
2. If using `LLMResource` directly, apply `llm_resource.with_mock_llm_call(True)`
3. Mark tests that must use real LLM calls with `@pytest.mark.live` 