# vLLM Integration Guide

This guide shows you how to configure OpenDXA to use a local vLLM server instead of cloud-based LLM providers.

## Quick Start

### 1. Start vLLM Server
```bash
# Interactive model selection
./bin/vllm/start.sh

# Or specify a model directly
./bin/vllm/start.sh --model microsoft/Phi-4
```

### 2. Configure OpenDXA

#### Option A: Environment Variables (Recommended)
Add to your `.env` file:
```bash
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=not-needed-for-local
```

#### Option B: Provider Configuration in Code
```python
import aisuite as ai

provider_configs = {
    "openai": {
        "base_url": "http://localhost:8000/v1",
        "api_key": "not-needed-for-local"
    }
}

client = ai.Client(provider_configs=provider_configs)
```

#### Option C: OpenDXA Configuration File
Update `opendxa/opendxa_config.json`:
```json
{
  "llm": {
    "preferred_models": [
      {"name": "vllm:local-model", "required_api_keys": []}
    ],
    "provider_configs": {
      "vllm": {
        "base_url": "http://localhost:8000/v1",
        "api_key": "not-needed"
      }
    }
  }
}
```

### 3. Test the Integration
```bash
python examples/vllm_integration_example.py
```

## Using with OpenDXA LLMResource

```python
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest

# Configure LLMResource for vLLM
llm_resource = LLMResource(
    name="vllm_local",
    model="openai:microsoft/Phi-4",  # Use your loaded model name
    temperature=0.7,
    max_tokens=100
)

# Set provider config
llm_resource.provider_configs["openai"] = {
    "base_url": "http://localhost:8000/v1",
    "api_key": "not-needed-for-local"
}

# Query the model
request = BaseRequest(arguments={
    "messages": [
        {"role": "user", "content": "Hello! How are you?"}
    ]
})

response = await llm_resource.query(request)
print(response.content)
```

## Using with Direct aisuite

```python
import aisuite as ai

# Configure client
provider_configs = {
    "openai": {
        "base_url": "http://localhost:8000/v1",
        "api_key": "not-needed-for-local"
    }
}

client = ai.Client(provider_configs=provider_configs)

# Make request
response = client.chat.completions.create(
    model="openai:microsoft/Phi-4",  # Use your loaded model name
    messages=[
        {"role": "user", "content": "Tell me a joke"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response.choices[0].message.content)
```

## Important Notes

### Model Names
- Use the exact model name from your vLLM server
- Prefix with `openai:` for aisuite compatibility
- Example: `openai:microsoft/Phi-4`

### API Compatibility
- vLLM provides an OpenAI-compatible API
- No API key needed for local servers
- Default endpoint: `http://localhost:8000/v1`

### Common Issues

#### Connection Refused
```
✅ Solution: Ensure vLLM server is running
./bin/vllm/start.sh
```

#### Model Not Found
```
✅ Solution: Use exact model name from vLLM server
# Check available models
curl http://localhost:8000/v1/models
```

#### Port Conflicts
```
✅ Solution: Use different port
./bin/vllm/start.sh --port 8001

# Update base_url accordingly
OPENAI_BASE_URL=http://localhost:8001/v1
```

## Chat with Your Local Model

Once configured, use the interactive chat:
```bash
./bin/vllm/chat.sh
```

## Available Scripts

- `./bin/vllm/install.sh` - Install vLLM
- `./bin/vllm/start.sh` - Start vLLM server
- `./bin/vllm/chat.sh` - Interactive chat
- `./bin/vllm/uninstall.sh` - Remove vLLM

## Makefile Targets

```bash
make install-vllm    # Install vLLM
make start-vllm      # Start vLLM server
make chat-vllm       # Start chat interface
make uninstall-vllm  # Remove vLLM
```

## Benefits of Local vLLM

- 🔒 **Privacy**: Your data never leaves your machine
- 💸 **Cost**: No API fees for inference
- ⚡ **Speed**: No network latency
- 🎛️ **Control**: Full control over model parameters
- 🔄 **Offline**: Works without internet connection 