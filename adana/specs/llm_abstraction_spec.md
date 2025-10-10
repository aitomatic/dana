# LLM Abstraction Layer Specification

## Overview

The LLM abstraction layer leverages the existing `adana/common/llm` implementation, which provides a unified interface for interacting with different Large Language Model providers. This ensures the agentic architecture remains LLM-agnostic while building on the proven foundation already in place.

## Existing LLM Implementation

The current implementation in `adana/common/llm` provides:

### Core Types
```python
from adana.common.llm.types import LLMProvider, LLMMessage, LLMResponse

@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str

@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to the LLM and get a response."""
        pass
```

### Main LLM Interface
```python
from adana.common.llm import LLM

class LLM:
    """
    Simple LLM interface - KISS principle applied.
    
    Essential methods:
    - chat() - for conversations with history
    - ask() - for single questions
    - stream() - for streaming responses
    - switch_provider() - to change LLM provider
    """
    
    def __init__(self, provider: str | LLMProvider | None = None, model: str | None = None):
        """Initialize LLM with a provider."""
        
    async def chat(self, message: str, role: str = "user", **kwargs) -> str:
        """Send a message and get a response with conversation history."""
        
    async def ask(self, question: str, system_prompt: str | None = None, **kwargs) -> str:
        """Ask a single question and get an answer."""
        
    async def stream(self, message: str, role: str = "user", **kwargs):
        """Stream a response from the LLM."""
        
    def clear_history(self):
        """Clear the conversation history."""
        
    def set_system_prompt(self, prompt: str):
        """Set a system prompt for the conversation."""
        
    def get_conversation_history(self) -> list[LLMMessage]:
        """Get the complete conversation history."""
        
    def switch_provider(self, provider: str, model: str | None = None):
        """Switch to a different LLM provider."""
```

### Supported Providers
The existing implementation supports multiple providers through `adana/common/llm/providers/`:

- **OpenAI**: GPT-3.5, GPT-4, GPT-4-turbo
- **Anthropic**: Claude-3-haiku, Claude-3-sonnet, Claude-3-opus
- **Ollama**: Local models (llama2, codellama, mistral)
- **Groq**: Fast inference (llama3, mixtral)
- **Azure OpenAI**: Enterprise OpenAI access
- **Moonshot**: Kimi models
- **Hugging Face**: Open source models
- **Qwen**: Alibaba Cloud models
- **DeepSeek**: Coding and general models
- **OpenRouter**: Multiple providers through one API

### Configuration Management
```python
from adana.common.config import config_manager

# Provider configuration is managed through adana/config.json
# Environment variables are automatically detected
# Priority-based provider selection
```

## Integration with Agentic Architecture

### Agent LLM Integration
```python
from adana.common.llm import LLM
from adana.common.llm.types import LLMMessage

class Agent:
    def __init__(self, agent_type: str, llm_provider: str | None = None, model: str | None = None, config: dict = None):
        # Use existing LLM implementation
        self.llm = LLM(provider=llm_provider, model=model)
        self.agent_type = agent_type
        self.config = config or {}
        
    async def chat(self, user_input: str) -> str:
        """Main conversational interface with tool execution loop."""
        # 1. Update state with user input
        self._add_to_conversation_history('user', user_input)
        
        # 2. Create prompts using PromptEngineer
        system_prompt = self.prompt_engineer.create_system_prompt(
            self.state, self.resources, self.workflows
        )
        
        # 3. Set system prompt if not already set
        if not self.llm.get_system_messages():
            self.llm.set_system_prompt(system_prompt)
        
        # 4. Generate response using existing LLM interface
        response = await self.llm.chat(user_input)
        
        # 5. Handle tool execution loop
        while self._has_tool_calls(response):
            tool_results = await self._execute_tools(response)
            # Add tool results to conversation
            for tool_result in tool_results:
                await self.llm.chat(tool_result, role="assistant")
            
            # Get next response
            response = await self.llm.chat("Continue with the tool results above.")
        
        # 6. Update state and return response
        self._add_to_conversation_history('assistant', response)
        return response
```

### Tool Integration
```python
def _get_available_tools(self) -> List[Dict[str, Any]]:
    """Get list of available tools for LLM."""
    tools = []
    
    # Add resource tools
    for name, resource in self.resources.items():
        for method_name, method_info in resource.methods.items():
            tools.append({
                'type': 'function',
                'function': {
                    'name': f"{name}_{method_name}",
                    'description': method_info.docstring,
                    'parameters': method_info.parameters
                }
            })
    
    # Add workflow tools
    for name, workflow in self.workflows.items():
        tools.append({
            'type': 'function',
            'function': {
                'name': name,
                'description': workflow.description,
                'parameters': workflow.get_parameters_schema()
            }
        })
    
    return tools
```

### Provider Management
```python
# Easy provider switching
agent = Agent('coding', llm_provider='anthropic', model='claude-3-sonnet')
agent.llm.switch_provider('openai', model='gpt-4')

# Check available providers
available = LLM.get_available_providers()
is_available = LLM.is_provider_available('anthropic')
models = LLM.get_provider_models('openai')
```

## Key Advantages of Existing Implementation

### 1. **Proven Foundation**
- Already tested and working across multiple providers
- Handles authentication, configuration, and error handling
- Supports both sync and async operations

### 2. **Conversation History Management**
- Built-in conversation history tracking
- System prompt management
- Message filtering by role

### 3. **Provider Abstraction**
- Unified interface across all providers
- Easy provider switching
- Configuration-driven setup

### 4. **Error Handling**
- Comprehensive error handling for each provider
- Graceful fallbacks
- Detailed logging

### 5. **Configuration Management**
- JSON-based configuration
- Environment variable support
- Priority-based provider selection

## Usage Examples

### Basic Agent Usage
```python
from adana.common.llm import LLM
from adana.core.agent import Agent

# Create agent with specific provider
agent = Agent('coding', llm_provider='anthropic', model='claude-3-sonnet')

# Chat with conversation history
response = await agent.chat("Help me debug this Python code")
response = await agent.chat("What about this error message?")

# Access conversation history
history = agent.llm.get_conversation_history()
```

### Provider Switching
```python
# Start with default provider
agent = Agent('financial_analyst')

# Switch to different provider
agent.llm.switch_provider('openai', model='gpt-4')

# Switch back
agent.llm.switch_provider('anthropic', model='claude-3-opus')
```

### Tool Integration
```python
# Agent automatically handles tool calls through conversation
response = await agent.chat("Analyze the stock data for AAPL")
# Agent will use market_data resource and financial_news resource
# Results are integrated into the conversation flow
```

This integration leverages the existing, proven LLM infrastructure while adding the agentic capabilities of resources, workflows, and adaptive learning.
```

## Concrete Provider Implementations

### Anthropic Provider

```python
import anthropic
from typing import Dict, List, Any, Optional

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.ANTHROPIC
    
    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize Anthropic client."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        return anthropic.Anthropic(api_key=api_key)
    
    def _get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        return [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ]
    
    def _get_default_model(self) -> str:
        return 'claude-3-5-sonnet-20241022'
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic Claude."""
        start_time = datetime.now()
        
        try:
            # Prepare messages for Anthropic
            messages = self._prepare_messages(request.messages)
            
            # Prepare tools if provided
            tools = self._prepare_tools(request.tools) if request.tools else None
            
            # Make API call
            response = self.client.messages.create(
                model=request.model or self.default_model,
                max_tokens=request.max_tokens or 4096,
                temperature=request.temperature or 0.7,
                messages=messages,
                tools=tools
            )
            
            # Extract content
            content = response.content[0].text if response.content else ""
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare usage information
            usage = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            # Prepare metadata
            metadata = {
                'model': response.model,
                'stop_reason': response.stop_reason,
                'tool_calls': self._extract_tool_calls(response.content)
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider_type.value,
                usage=usage,
                metadata=metadata,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate response asynchronously."""
        # Anthropic doesn't have async client, so we run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, request)
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream response from Anthropic."""
        try:
            messages = self._prepare_messages(request.messages)
            tools = self._prepare_tools(request.tools) if request.tools else None
            
            with self.client.messages.stream(
                model=request.model or self.default_model,
                max_tokens=request.max_tokens or 4096,
                temperature=request.temperature or 0.7,
                messages=messages,
                tools=tools
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            raise Exception(f"Anthropic streaming error: {str(e)}")
    
    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare messages for Anthropic API."""
        # Anthropic uses different message format
        prepared = []
        for msg in messages:
            if msg['role'] == 'system':
                # Anthropic doesn't have system messages, prepend to first user message
                if prepared and prepared[-1]['role'] == 'user':
                    prepared[-1]['content'] = f"System: {msg['content']}\n\nUser: {prepared[-1]['content']}"
                else:
                    # If no user message yet, create one
                    prepared.append({'role': 'user', 'content': f"System: {msg['content']}"})
            else:
                prepared.append(msg)
        
        return prepared
    
    def _prepare_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare tools for Anthropic API."""
        # Convert tools to Anthropic format
        anthropic_tools = []
        for tool in tools:
            anthropic_tool = {
                'name': tool['function']['name'],
                'description': tool['function']['description'],
                'input_schema': tool['function']['parameters']
            }
            anthropic_tools.append(anthropic_tool)
        
        return anthropic_tools
    
    def _extract_tool_calls(self, content: List[Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from response content."""
        tool_calls = []
        for item in content:
            if hasattr(item, 'type') and item.type == 'tool_use':
                tool_calls.append({
                    'id': item.id,
                    'name': item.name,
                    'input': item.input
                })
        
        return tool_calls
```

### OpenAI Provider

```python
import openai
from typing import Dict, List, Any, Optional

class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.OPENAI
    
    def _initialize_client(self) -> openai.OpenAI:
        """Initialize OpenAI client."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        return openai.OpenAI(api_key=api_key)
    
    def _get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        return [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo'
        ]
    
    def _get_default_model(self) -> str:
        return 'gpt-4o'
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI."""
        start_time = datetime.now()
        
        try:
            # Prepare messages
            messages = request.messages
            
            # Prepare tools if provided
            tools = request.tools if request.tools else None
            
            # Make API call
            response = self.client.chat.completions.create(
                model=request.model or self.default_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                tools=tools,
                stream=False
            )
            
            # Extract content
            content = response.choices[0].message.content or ""
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare usage information
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            # Prepare metadata
            metadata = {
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason,
                'tool_calls': self._extract_tool_calls(response.choices[0].message)
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider_type.value,
                usage=usage,
                metadata=metadata,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate response asynchronously."""
        start_time = datetime.now()
        
        try:
            # Prepare messages
            messages = request.messages
            
            # Prepare tools if provided
            tools = request.tools if request.tools else None
            
            # Make async API call
            response = await self.client.chat.completions.create(
                model=request.model or self.default_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                tools=tools,
                stream=False
            )
            
            # Extract content
            content = response.choices[0].message.content or ""
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare usage information
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            # Prepare metadata
            metadata = {
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason,
                'tool_calls': self._extract_tool_calls(response.choices[0].message)
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider_type.value,
                usage=usage,
                metadata=metadata,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        try:
            messages = request.messages
            tools = request.tools if request.tools else None
            
            stream = await self.client.chat.completions.create(
                model=request.model or self.default_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                tools=tools,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"OpenAI streaming error: {str(e)}")
    
    def _extract_tool_calls(self, message: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from response message."""
        tool_calls = []
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append({
                    'id': tool_call.id,
                    'type': tool_call.type,
                    'function': {
                        'name': tool_call.function.name,
                        'arguments': tool_call.function.arguments
                    }
                })
        
        return tool_calls
```

### Ollama Provider

```python
import requests
import json
from typing import Dict, List, Any, Optional

class OllamaProvider(LLMProvider):
    """Ollama local provider implementation."""
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.OLLAMA
    
    def _initialize_client(self) -> str:
        """Initialize Ollama client (base URL)."""
        return self.config.get('base_url', 'http://localhost:11434')
    
    def _get_available_models(self) -> List[str]:
        """Get available Ollama models."""
        try:
            response = requests.get(f"{self.client}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            else:
                return ['llama2', 'codellama', 'mistral', 'neural-chat']
        except:
            return ['llama2', 'codellama', 'mistral', 'neural-chat']
    
    def _get_default_model(self) -> str:
        return 'llama2'
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Ollama."""
        start_time = datetime.now()
        
        try:
            # Prepare messages for Ollama
            messages = self._prepare_messages(request.messages)
            
            # Prepare request payload
            payload = {
                'model': request.model or self.default_model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': request.temperature or 0.7,
                    'num_predict': request.max_tokens or 4096
                }
            }
            
            # Make API call
            response = requests.post(
                f"{self.client}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            
            # Extract content
            content = result.get('message', {}).get('content', '')
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare usage information
            usage = {
                'prompt_tokens': result.get('prompt_eval_count', 0),
                'completion_tokens': result.get('eval_count', 0),
                'total_tokens': result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
            }
            
            # Prepare metadata
            metadata = {
                'model': result.get('model', request.model or self.default_model),
                'done': result.get('done', True),
                'context': result.get('context', [])
            }
            
            return LLMResponse(
                content=content,
                model=result.get('model', request.model or self.default_model),
                provider=self.provider_type.value,
                usage=usage,
                metadata=metadata,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate response asynchronously."""
        # Ollama doesn't have async support, so we run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, request)
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream response from Ollama."""
        try:
            messages = self._prepare_messages(request.messages)
            
            payload = {
                'model': request.model or self.default_model,
                'messages': messages,
                'stream': True,
                'options': {
                    'temperature': request.temperature or 0.7,
                    'num_predict': request.max_tokens or 4096
                }
            }
            
            response = requests.post(
                f"{self.client}/api/chat",
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama streaming error: {response.status_code}")
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'message' in data and 'content' in data['message']:
                            yield data['message']['content']
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            raise Exception(f"Ollama streaming error: {str(e)}")
    
    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare messages for Ollama API."""
        # Ollama uses standard message format
        return messages
```

## Provider Factory

```python
class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.OLLAMA: OllamaProvider,
        # Add more providers as needed
    }
    
    @classmethod
    def create_provider(cls, provider_type: Union[str, LLMProviderType], config: Dict[str, Any]) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider to create
            config: Provider configuration
        
        Returns:
            LLM provider instance
        """
        if isinstance(provider_type, str):
            try:
                provider_type = LLMProviderType(provider_type)
            except ValueError:
                raise ValueError(f"Unknown provider type: {provider_type}")
        
        if provider_type not in cls._providers:
            raise ValueError(f"Provider {provider_type} not supported")
        
        provider_class = cls._providers[provider_type]
        return provider_class(config)
    
    @classmethod
    def register_provider(cls, provider_type: LLMProviderType, provider_class: type) -> None:
        """
        Register a new provider type.
        
        Args:
            provider_type: Provider type
            provider_class: Provider class
        """
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def get_supported_providers(cls) -> List[LLMProviderType]:
        """Get list of supported provider types."""
        return list(cls._providers.keys())
```

## Provider Manager

```python
class LLMProviderManager:
    """Manages multiple LLM providers and load balancing."""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider: Optional[str] = None
        self.load_balancer = LoadBalancer()
    
    def add_provider(self, name: str, provider: LLMProvider) -> None:
        """Add a provider to the manager."""
        self.providers[name] = provider
        if self.default_provider is None:
            self.default_provider = name
    
    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """Get a provider by name or default."""
        if name is None:
            name = self.default_provider
        
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found")
        
        return self.providers[name]
    
    def generate(self, request: LLMRequest, provider_name: Optional[str] = None) -> LLMResponse:
        """Generate response using specified or default provider."""
        provider = self.get_provider(provider_name)
        return provider.generate(request)
    
    def generate_with_fallback(self, request: LLMRequest, primary_provider: str, fallback_providers: List[str]) -> LLMResponse:
        """Generate response with fallback providers."""
        providers_to_try = [primary_provider] + fallback_providers
        
        for provider_name in providers_to_try:
            try:
                provider = self.get_provider(provider_name)
                return provider.generate(request)
            except Exception as e:
                if provider_name == providers_to_try[-1]:  # Last provider
                    raise e
                continue
        
        raise Exception("All providers failed")
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}
        for name, provider in self.providers.items():
            stats[name] = {
                'provider_type': provider.provider_type.value,
                'available_models': provider.available_models,
                'default_model': provider.default_model
            }
        
        return stats

class LoadBalancer:
    """Simple load balancer for LLM providers."""
    
    def __init__(self):
        self.provider_weights: Dict[str, float] = {}
        self.provider_usage: Dict[str, int] = {}
    
    def set_provider_weight(self, provider_name: str, weight: float) -> None:
        """Set weight for a provider."""
        self.provider_weights[provider_name] = weight
    
    def select_provider(self, available_providers: List[str]) -> str:
        """Select a provider based on weights and usage."""
        if not available_providers:
            raise ValueError("No providers available")
        
        # Simple round-robin for now
        # Could be enhanced with more sophisticated algorithms
        if available_providers:
            return available_providers[0]
        
        return available_providers[0]
```

## Configuration and Usage

```python
# Example configurations for different providers
anthropic_config = {
    'api_key': 'your_anthropic_api_key',
    'default_model': 'claude-3-5-sonnet-20241022',
    'max_tokens': 4096,
    'temperature': 0.7
}

openai_config = {
    'api_key': 'your_openai_api_key',
    'default_model': 'gpt-4o',
    'max_tokens': 4096,
    'temperature': 0.7
}

ollama_config = {
    'base_url': 'http://localhost:11434',
    'default_model': 'llama2',
    'max_tokens': 4096,
    'temperature': 0.7
}

# Create providers
anthropic_provider = LLMProviderFactory.create_provider('anthropic', anthropic_config)
openai_provider = LLMProviderFactory.create_provider('openai', openai_config)
ollama_provider = LLMProviderFactory.create_provider('ollama', ollama_config)

# Use with agent
from adana.core.agent import Agent

agent = Agent('coding', anthropic_provider)

# Or use provider manager for load balancing
provider_manager = LLMProviderManager()
provider_manager.add_provider('anthropic', anthropic_provider)
provider_manager.add_provider('openai', openai_provider)
provider_manager.add_provider('ollama', ollama_provider)

# Generate with specific provider
request = LLMRequest(
    messages=[{'role': 'user', 'content': 'Hello, world!'}],
    model='claude-3-5-sonnet-20241022',
    temperature=0.7
)

response = provider_manager.generate(request, 'anthropic')

# Generate with fallback
response = provider_manager.generate_with_fallback(
    request, 
    'anthropic', 
    ['openai', 'ollama']
)
```

## Error Handling

```python
class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMProviderError(LLMError):
    """Exception raised when provider operations fail."""
    pass

class LLMConfigurationError(LLMError):
    """Exception raised when provider configuration is invalid."""
    pass

class LLMRateLimitError(LLMError):
    """Exception raised when rate limit is exceeded."""
    pass

class LLMQuotaExceededError(LLMError):
    """Exception raised when quota is exceeded."""
    pass
```

## Testing and Validation

```python
class LLMProviderValidator:
    """Validates LLM provider implementations."""
    
    @staticmethod
    def validate_provider(provider: LLMProvider) -> bool:
        """Validate that a provider implements the interface correctly."""
        try:
            # Test basic generation
            request = LLMRequest(
                messages=[{'role': 'user', 'content': 'Test message'}],
                max_tokens=10
            )
            
            response = provider.generate(request)
            
            # Validate response structure
            assert isinstance(response, LLMResponse)
            assert isinstance(response.content, str)
            assert isinstance(response.model, str)
            assert isinstance(response.provider, str)
            assert isinstance(response.usage, dict)
            assert isinstance(response.metadata, dict)
            assert isinstance(response.response_time, float)
            assert isinstance(response.timestamp, datetime)
            
            return True
            
        except Exception as e:
            print(f"Provider validation failed: {e}")
            return False
    
    @staticmethod
    def test_provider_performance(provider: LLMProvider, num_requests: int = 10) -> Dict[str, Any]:
        """Test provider performance."""
        request = LLMRequest(
            messages=[{'role': 'user', 'content': 'Performance test message'}],
            max_tokens=100
        )
        
        response_times = []
        success_count = 0
        
        for _ in range(num_requests):
            try:
                start_time = datetime.now()
                response = provider.generate(request)
                end_time = datetime.now()
                
                response_times.append((end_time - start_time).total_seconds())
                success_count += 1
                
            except Exception as e:
                print(f"Request failed: {e}")
        
        return {
            'total_requests': num_requests,
            'successful_requests': success_count,
            'success_rate': success_count / num_requests,
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0
        }
```

This LLM abstraction layer provides a robust, extensible foundation for the agentic architecture, allowing seamless integration with various LLM providers while maintaining consistent behavior and error handling across the system.
