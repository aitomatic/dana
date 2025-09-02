"""
Agent Implementation Methods

This module contains the implementation methods for agent functionality including
memory, reasoning, chat, and LLM resource management.
"""

from typing import Any, cast

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance


def build_agent_description(
    name: str,
    personality: str | None = None,
    expertise: str | None = None,
    background: str | None = None,
    goals: str | None = None,
    style: str | None = None,
    **kwargs: Any,
) -> str:
    """
    Build natural language description of agent for LLM system prompts.

    USED BY: agent.chat() → _build_agent_description()
    WHEN: Creating system prompt for conversational interactions

    Returns natural language description that serves as LLM system prompt.
    """
    description = f"You are {name}."

    characteristics = []
    if personality:
        characteristics.append(f"Your personality is {personality}")
    if expertise:
        characteristics.append(f"Your expertise includes {expertise}")
    if background:
        characteristics.append(f"Your background is {background}")
    if goals:
        characteristics.append(f"Your goals are {goals}")
    if style:
        characteristics.append(f"Your communication style is {style}")

    # Add any additional characteristics
    for field_name, field_value in kwargs.items():
        if field_value and field_name not in ["config", "_conversation_memory", "_llm_resource_instance", "_memory"]:
            characteristics.append(f"Your {field_name} is {field_value}")

    if characteristics:
        description += " " + " ".join(characteristics) + "."

    # Add general instructions for natural conversation
    description += " You should respond naturally and conversationally, as if you're having a friendly chat. Be helpful, engaging, and authentic in your responses."

    return description


class FallbackResponses:
    """
    Fallback response templates for when LLM is unavailable.

    USED BY: agent.chat() → _generate_fallback_response()
    WHEN: LLM is unavailable or fails to respond

    Provides graceful degradation when LLM resources are unavailable.
    """

    GREETING_RESPONSES = [
        "Hello! I'm {name}, ready to assist you.",
        "Hi there! {name} here, how can I help?",
        "Greetings! I'm {name}, at your service.",
    ]

    NAME_INQUIRY_RESPONSE = "I'm {name}, an AI agent here to help you with your tasks."

    HELP_RESPONSE = (
        "I'm {name}, and I can help you with various tasks including problem solving, "
        "code generation, and workflow creation. What would you like to work on?"
    )

    CAPABILITY_RESPONSE = (
        "I can assist with problem analysis, solution planning, code generation, workflow design, and more. How can I help you today?"
    )

    THANKS_RESPONSE = "You're welcome! Let me know if there's anything else I can help with."

    GOODBYE_RESPONSE = "Goodbye! Feel free to return if you need any assistance."

    DEFAULT_RESPONSE = (
        "I understand you're asking about '{topic}'. While I'm currently in fallback mode, "
        "I'm designed to help with problem solving, analysis, and planning. "
        "Please ensure I'm properly connected to an LLM for the best experience."
    )

    ERROR_RESPONSE = (
        "I apologize, but I'm currently unable to provide a full response as I'm not connected "
        "to an LLM service. I'm {name}, and once properly configured, I'll be able to help you "
        "with your request about '{topic}'."
    )

    @classmethod
    def get_greeting(cls, agent_name: str, index: int = 0) -> str:
        """Get a greeting response with agent name."""
        responses = cls.GREETING_RESPONSES
        return responses[index % len(responses)].format(name=agent_name)

    @classmethod
    def get_name_inquiry(cls, agent_name: str) -> str:
        """Get response for name inquiry."""
        return cls.NAME_INQUIRY_RESPONSE.format(name=agent_name)

    @classmethod
    def get_help(cls, agent_name: str) -> str:
        """Get help response."""
        return cls.HELP_RESPONSE.format(name=agent_name)

    @classmethod
    def get_default(cls, agent_name: str, topic: str) -> str:
        """Get default fallback response."""
        return cls.DEFAULT_RESPONSE.format(name=agent_name, topic=topic)

    @classmethod
    def get_error(cls, agent_name: str, topic: str) -> str:
        """Get error fallback response."""
        return cls.ERROR_RESPONSE.format(name=agent_name, topic=topic)


class AgentImplementationMixin:
    """Mixin class providing implementation methods for agent functionality."""

    def _initialize_conversation_memory(self):
        """Initialize conversation memory if not already done."""
        if self._conversation_memory is None:
            from pathlib import Path

            from dana.frameworks.memory.conversation_memory import ConversationMemory

            # Create memory file path under ~/.dana/chats/
            agent_name = getattr(self.agent_type, "name", "agent")
            home_dir = Path.home()
            dana_dir = home_dir / ".dana"
            memory_dir = dana_dir / "chats"
            memory_dir.mkdir(parents=True, exist_ok=True)
            memory_file = memory_dir / f"{agent_name}_conversation.json"

            self._conversation_memory = ConversationMemory(
                filepath=str(memory_file),
                max_turns=20,  # Keep last 20 turns in active memory
            )

    def _initialize_llm_resource(self):
        """Initialize LLM resource from agent's config if not already done."""
        if self._llm_resource_instance is None:
            # Check if we're in a test environment by looking for DANA_MOCK_LLM
            import os

            if os.getenv("DANA_MOCK_LLM", "false").lower() == "true":
                # Create a mock LLM resource for testing
                from tests.conftest import create_mock_llm_resource

                self._llm_resource_instance = create_mock_llm_resource()
                return

            from dana.core.resource.builtins.llm_resource_type import LLMResourceType

            # Get LLM parameters from agent's config field
            llm_params = {}
            if hasattr(self, "_values") and "config" in self._values:
                config = self._values["config"]
                if isinstance(config, dict):
                    # Extract LLM parameters from config
                    llm_params = {
                        "model": config.get("llm_model", config.get("model", "auto")),
                        "temperature": config.get("llm_temperature", config.get("temperature", 0.7)),
                        "max_tokens": config.get("llm_max_tokens", config.get("max_tokens", 2048)),
                        "provider": config.get("llm_provider", config.get("provider", "auto")),
                    }
                    # Add any other LLM-related config keys
                    for key, value in config.items():
                        if key.startswith("llm_") and key not in ["llm_model", "llm_temperature", "llm_max_tokens", "llm_provider"]:
                            llm_params[key[4:]] = value  # Remove "llm_" prefix

            # Create the LLM resource instance using the resource type system
            # This avoids direct dependency on LegacyLLMResource
            self._llm_resource_instance = LLMResourceType.create_instance_from_values(
                {
                    "name": f"{self.agent_type.name}_llm",
                    "model": llm_params.get("model", "auto"),
                    "provider": llm_params.get("provider", "auto"),
                    "temperature": llm_params.get("temperature", 0.7),
                    "max_tokens": llm_params.get("max_tokens", 2048),
                    **{k: v for k, v in llm_params.items() if k not in ["model", "temperature", "max_tokens", "provider"]},
                }
            )

            # Initialize the resource
            self._llm_resource_instance.initialize()
            self._llm_resource_instance.start()

    def get_llm_resource(self, sandbox_context: SandboxContext | None = None):
        """Get LLM resource - prioritize agent's own LLM resource, fallback to sandbox context."""
        try:
            # First, try to use the agent's own LLM resource
            if self._llm_resource_instance is None:
                self._initialize_llm_resource()

            if self._llm_resource_instance and self._llm_resource_instance.is_available:
                return self._llm_resource_instance

            # Fallback to sandbox context if agent's LLM is not available
            if sandbox_context is not None:
                # Use the system LLM resource from context
                system_llm = sandbox_context.get_system_llm_resource()
                if system_llm is not None:
                    return system_llm

                # Fallback to looking for any LLM resource in context
                try:
                    resources = sandbox_context.get_resources()
                    for _, resource in resources.items():
                        if hasattr(resource, "kind") and resource.kind == "llm":
                            return resource
                except Exception:
                    pass
            return None
        except Exception:
            return None

    def _build_agent_description(self) -> str:
        """Build a natural language description of the agent for LLM prompts."""
        # Extract field values from the agent instance
        kwargs = {}
        if hasattr(self, "_values") and self._values:
            for field_name, field_value in self._values.items():
                # Skip internal fields that shouldn't be part of the description
                if field_name not in ["config", "_conversation_memory", "_llm_resource_instance", "_memory"]:
                    kwargs[field_name] = field_value

        # Use the centralized prompt template
        return build_agent_description(
            name=self.agent_type.name,
            personality=kwargs.get("personality"),
            expertise=kwargs.get("expertise"),
            background=kwargs.get("background"),
            goals=kwargs.get("goals"),
            style=kwargs.get("style"),
            **{k: v for k, v in kwargs.items() if k not in ["name", "personality", "expertise", "background", "goals", "style"]},
        )

    def _generate_fallback_response(self, message: str, context: str) -> str:
        """Generate a fallback response when LLM is not available."""
        message_lower = message.lower()

        # Create YAML-formatted fallback response
        fallback_response = {
            "role": "assistant",
            "content": "",
            "agent_name": self.agent_type.name,
            "response_type": "fallback",
            "context": context,
        }

        # Check for greetings
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            fallback_response["content"] = FallbackResponses.get_greeting(self.agent_type.name)
            fallback_response["response_type"] = "greeting"

        # Check for name queries
        elif "your name" in message_lower or "who are you" in message_lower:
            fallback_response["content"] = FallbackResponses.get_name_inquiry(self.agent_type.name)
            fallback_response["response_type"] = "identity"

        # Check for memory-related queries
        elif "remember" in message_lower or "recall" in message_lower:
            assert self._conversation_memory is not None  # Should be initialized by now
            recent_turns = self._conversation_memory.get_recent_context(3)
            if recent_turns:
                topics = []
                for turn in recent_turns:
                    words = turn["user_input"].split()
                    topics.extend([w for w in words if len(w) > 4])
                if topics:
                    unique_topics = list(set(topics))[:3]
                    fallback_response["content"] = f"I remember we discussed: {', '.join(unique_topics)}"
                    fallback_response["response_type"] = "memory_recall"
                    fallback_response["topics"] = unique_topics
                else:
                    fallback_response["content"] = "We haven't discussed much yet in this conversation."
                    fallback_response["response_type"] = "memory_empty"
            else:
                fallback_response["content"] = "We haven't discussed much yet in this conversation."
                fallback_response["response_type"] = "memory_empty"

        # Check for help queries
        elif "help" in message_lower or "what can you do" in message_lower:
            fallback_response["content"] = FallbackResponses.get_help(self.agent_type.name)
            fallback_response["response_type"] = "help"
            fallback_response["capabilities"] = ["chat", "memory", "llm_integration"]

        # Default response
        else:
            # Extract a topic from the message for a more contextual response
            words = message.lower().split()
            # Simple topic extraction - get meaningful words
            meaningful_words = [
                word for word in words if len(word) > 3 and word not in ["what", "how", "why", "when", "where", "could", "would", "should"]
            ]
            topic = meaningful_words[0] if meaningful_words else "your request"

            fallback_response["content"] = FallbackResponses.get_default(self.agent_type.name, topic)
            fallback_response["response_type"] = "default"

        # Return YAML-formatted response
        return f"""```yaml
content: |
  {fallback_response["content"]}
agent_name: {fallback_response["agent_name"]}
response_type: {fallback_response["response_type"]}
context: {fallback_response["context"]}
```"""

    def _chat_impl(
        self, sandbox_context: SandboxContext | None = None, message: str = "", context: dict | None = None, max_context_turns: int = 5
    ) -> str:
        """Implementation of chat functionality that returns a string response."""
        # Initialize conversation memory if not already done
        self._initialize_conversation_memory()

        try:
            # Try to use LLM if available
            llm_resource = self.get_llm_resource(sandbox_context)
            if llm_resource is not None:
                # Build system prompt in YAML format
                system_prompt = self._build_agent_description()

                # Get conversation context if available
                conversation_context = []
                if self._conversation_memory:
                    recent_turns = self._conversation_memory.get_recent_context(max_context_turns)
                    for turn in recent_turns:
                        conversation_context.append({"role": "user", "content": turn["user_input"]})
                        conversation_context.append({"role": "assistant", "content": turn["agent_response"]})

                conversation_context.append({"role": "user", "content": message})

                # Call LLM
                response = llm_resource.chat_completion(conversation_context, system_prompt=system_prompt, context=context)
                return response
            else:
                # Fallback to simple responses when no LLM is available
                return self._generate_fallback_response(message, str(context) if context else "")
        except Exception as e:
            # Fallback to error response
            return f"I encountered an error while processing your message: {str(e)}"

    def _reason_impl(
        self,
        sandbox_context: SandboxContext,
        premise: str,
        context: dict | None = None,
        system_message: str | None = None,
        is_sync: bool = False,
    ) -> dict:
        """Implementation of reasoning functionality using py_reason() for LLM-powered analysis."""
        self.debug(f"REASON: Analyzing premise: '{premise}'")
        self.debug(f"Context: {context}")

        try:
            # Use py_reason() for LLM-powered reasoning
            from dana.libs.corelib.py_wrappers.py_reason import py_reason

            self.debug("Calling py_reason() for LLM-powered analysis...")
            self.debug(f"Premise length: {len(premise)}")
            self.debug(f"Sandbox context: {type(sandbox_context)}")

            options = {
                "temperature": 0.3,  # Lower temperature for more focused reasoning
                "max_tokens": 800,
            }
            if system_message:
                options["system_message"] = system_message

            py_reason_result = py_reason(
                sandbox_context,
                premise,
                options=options,
                llm_resource=cast(LLMResourceInstance, self.get_llm_resource(sandbox_context)),
            )
            self.debug("py_reason() call successful")
            self.debug(f"Response type: {type(py_reason_result)}")
            self.debug(f"py_reason result: {py_reason_result}")

            return py_reason_result

        except Exception as e:
            self.error(f"LLM reasoning failed: {e}")
            # Fallback to basic reasoning
            return {
                "analysis": f"Fallback analysis of: {premise}",
                "reasoning_chain": [
                    f"LLM reasoning failed: {e}",
                    f"Applied {self.__struct_type__.name} fallback reasoning",
                    "Used basic logical analysis",
                ],
                "confidence": 0.6,
                "conclusion": f"Reasoning completed with fallback for: {premise}",
                "methodology": "fallback_reasoning",
                "agent": self.__struct_type__.name,
                "error": str(e),
            }

    def _remember_impl(self, sandbox_context: SandboxContext, key: str, value: Any) -> str:
        """Implementation of memory storage functionality."""
        self.debug(f"REMEMBER: Storing key '{key}' with value: {value}")

        # Store in agent's memory
        self._memory[key] = value

        # Note: ConversationMemory doesn't have add_memory method
        # Memory is stored in agent's internal _memory dict
        # Conversation memory is used for conversation turns, not key-value storage

        return f"Stored '{key}' in memory"

    def _recall_impl(self, sandbox_context: SandboxContext, key: str) -> Any:
        """Implementation of memory retrieval functionality."""
        self.debug(f"RECALL: Retrieving key '{key}'")

        # Try agent's memory first
        if key in self._memory:
            self.debug(f"Found in agent memory: {self._memory[key]}")
            return self._memory[key]

        # Note: ConversationMemory doesn't have get_memory method
        # Memory is stored in agent's internal _memory dict
        # Conversation memory is used for conversation turns, not key-value storage

        self.debug(f"Key '{key}' not found in memory")
        return None
