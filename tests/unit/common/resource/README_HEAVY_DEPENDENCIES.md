# Testing with Heavy Dependencies

## Problem

Some embedding providers require heavy ML dependencies like:
- **HuggingFace**: `sentence-transformers` (~2GB with PyTorch), `torch` (~1GB+), `transformers` (~500MB+)

Other providers use lightweight packages that are already installed:
- **Cohere**: `cohere` (~few MB), `llama-index-embeddings-cohere` (~10KB) 
- **OpenAI**: `openai` (~few MB), `llama-index-embeddings-openai` (~10KB)

Heavy packages are too large to include in the default project setup, but our tests need to verify the integration logic works correctly.

## Solution

We use **different testing strategies** based on the dependency weight:

### 1. Heavy Dependencies (HuggingFace) - Mock-Based Testing

For providers with heavy ML dependencies, we use mock-based testing that tests the integration logic without requiring heavy dependencies to be installed.

### 2. Lightweight Dependencies (Cohere, OpenAI) - Simple Testing  

For providers with lightweight packages already in the project, we use simple direct testing with minimal mocking.

### Key Components for Heavy Dependencies

#### 1. `mock_heavy_dependencies()` Helper Method

```python
@staticmethod
def mock_heavy_dependencies():
    """Context manager to mock heavy ML dependencies for testing.
    
    This prevents tests from requiring sentence-transformers, torch, etc.
    to be installed while still testing the integration logic.
    """
    return patch.dict('sys.modules', {
        'sentence_transformers': MagicMock(),
        'torch': MagicMock(),
        'transformers': MagicMock(),
    })
```

#### 2. Usage Pattern for Heavy Dependencies (HuggingFace)

```python
def test_huggingface_embedding_creation(self):
    """Test HuggingFace embedding creation."""
    # Mock heavy ML dependencies to avoid requiring them for tests
    with self.mock_heavy_dependencies():
        try:
            with patch('llama_index.embeddings.huggingface.HuggingFaceEmbedding') as mock_hf:
                create_llamaindex_embedding("huggingface:BAAI/bge-small-en-v1.5")
                mock_hf.assert_called_once_with(...)
        except ImportError:
            self.skipTest("llama-index-embeddings-huggingface not installed")
```

#### 3. Usage Pattern for Lightweight Dependencies (Cohere)

```python
def test_cohere_embedding_creation(self):
    """Test Cohere embedding creation."""
    # Cohere packages are lightweight and already installed - simple mocking is sufficient
    with patch('llama_index.embeddings.cohere.CohereEmbedding') as mock_cohere:
        create_llamaindex_embedding("cohere:embed-english-v2.0")
        mock_cohere.assert_called_once_with(...)
```

### How It Works

#### Heavy Dependencies (HuggingFace):
1. **Module Mocking**: We mock the heavy dependencies in `sys.modules` before any import attempts
2. **Integration Testing**: We test the configuration passing, error handling, and API calls 
3. **Graceful Fallback**: Tests are skipped if even the lightweight integration packages aren't installed

#### Lightweight Dependencies (Cohere, OpenAI):
1. **Direct Testing**: Simple patching of the provider classes
2. **No Heavy Mocking**: Dependencies are already available and lightweight
3. **Standard Test Patterns**: Use normal unittest patterns

### Benefits

- ✅ Tests run without 3GB+ of heavy ML dependencies for HuggingFace
- ✅ Simple, fast tests for lightweight providers like Cohere and OpenAI
- ✅ Integration logic is thoroughly tested for all providers
- ✅ CI/CD remains fast and lightweight  
- ✅ Developers can run tests locally without heavy downloads
- ✅ Production code paths are validated for all providers

### Provider Categories

| Provider | Category | Dependencies | Testing Strategy |
|----------|----------|--------------|------------------|
| **HuggingFace** | Heavy | `sentence-transformers`, `torch`, `transformers` | Mock-based with `mock_heavy_dependencies()` |
| **Cohere** | Lightweight | `cohere`, `llama-index-embeddings-cohere` | Simple direct testing |
| **OpenAI** | Lightweight | `openai`, `llama-index-embeddings-openai` | Simple direct testing |

### Adding New Tests

#### For Heavy Dependency Providers:
1. Use the `mock_heavy_dependencies()` helper method
2. Mock the specific provider's classes/functions  
3. Add graceful ImportError handling with `skipTest()`
4. Test the configuration passing and error cases

#### For Lightweight Providers:
1. Use simple `patch()` for provider classes
2. Test configuration passing directly
3. No need for heavy mocking or skipTest logic

### Running Tests

All embedding tests run without heavy dependencies:

```bash
# These work without sentence-transformers, torch, etc.
pytest tests/unit/common/resource/test_*embedding*.py -v
```

The tests validate:
- Configuration loading and validation
- Error handling for missing API keys
- Provider initialization logic
- Parameter passing to underlying libraries