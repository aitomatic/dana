from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


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


class ChatMixin:
    def chat_sync(
        self,
        message: str,
        context: dict | None = None,
        max_context_turns: int = 5,
        sandbox_context: SandboxContext | None = None,
    ) -> Any:
        # Get the next turn number
        turn_number = len(self.state.timeline.get_events_by_type("conversation")) + 1

        # Get the response
        response = self._chat_impl(sandbox_context or SandboxContext(), message, context, max_context_turns)

        # Add conversation turn to timeline
        self.state.timeline.add_conversation_turn(message, str(response), turn_number)

        return response

    def _chat_impl(
        self, sandbox_context: SandboxContext | None = None, message: str = "", context: dict | None = None, max_context_turns: int = 5
    ) -> str:
        """Implementation of chat functionality. Returns the response string directly."""
        # Build conversation context from centralized state
        try:
            conversation_context = self.state.timeline.get_conversation_context(
                max_turns=max_context_turns
            )
        except Exception:
            # Fallback if centralized state fails
            conversation_context = ""

        # Try to get LLM resource - prioritize agent's own LLM resource
        llm_resource = self.get_llm_resource(sandbox_context)

        if llm_resource:
            try:
                # Build system prompt with agent description
                system_prompt = self._build_agent_description()

                # Add conversation context if available
                if conversation_context.strip():
                    system_prompt += f"\n\nPrevious conversation:\n{conversation_context}"

                # Prepare messages
                messages = [{"role": "user", "content": message}]

                # Use the simplified chat completion method
                result = llm_resource.chat_completion(messages=messages, system_prompt=system_prompt, context=context)

            except Exception as e:
                result = f"I encountered an error while processing your message: {str(e)}"
        else:
            # For fallback response, execute synchronously
            result = self._generate_fallback_response(message, conversation_context)

        return result

    def _build_agent_description(self) -> str:
        """Build a natural language description of the agent for LLM prompts."""
        # Extract field values from the agent instance
        kwargs = {}
        if hasattr(self, "_values") and self._values:
            for field_name, field_value in self._values.items():
                # Skip internal fields that shouldn't be part of the description
                if field_name not in ["config", "_conversation_memory", "_llm_resource_instance", "_memory"]:
                    kwargs[field_name] = field_value

        # Build the description
        description = f"You are {self.agent_type.name}."

        characteristics = []
        if kwargs.get("personality"):
            characteristics.append(f"Your personality is {kwargs['personality']}")
        if kwargs.get("expertise"):
            characteristics.append(f"Your expertise includes {kwargs['expertise']}")
        if kwargs.get("background"):
            characteristics.append(f"Your background is {kwargs['background']}")
        if kwargs.get("goals"):
            characteristics.append(f"Your goals are {kwargs['goals']}")
        if kwargs.get("style"):
            characteristics.append(f"Your communication style is {kwargs['style']}")

        # Add any additional characteristics
        for field_name, field_value in kwargs.items():
            if field_value and field_name not in ["personality", "expertise", "background", "goals", "style"]:
                characteristics.append(f"Your {field_name} is {field_value}")

        if characteristics:
            description += " " + " ".join(characteristics) + "."

        # Add general instructions for natural conversation
        description += " You should respond naturally and conversationally, as if you're having a friendly chat. Be helpful, engaging, and authentic in your responses."

        return description

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
            try:
                conversations = self.state.timeline.get_events_by_type("conversation")
                recent_turns = conversations[-3:] if conversations else []
            except Exception:
                recent_turns = []
            if recent_turns:
                topics = []
                for turn in recent_turns:
                    words = turn.user_input.split()
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
