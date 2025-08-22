"""
Example usage of ConversationMemory for an AI agent.

This demonstrates how an agent can use the memory system to maintain
context across a conversation with a human.
"""

from conversation_memory import ConversationMemory


class ConversationalAgent:
    """
    Example agent that uses ConversationMemory to maintain context.
    """

    def __init__(self, memory_file="agent_memory.json"):
        self.memory = ConversationMemory(filepath=memory_file, max_turns=20)
        print(f"Agent initialized. Session #{self.memory.metadata.get('session_count', 1)}")

        # Show any previous conversation info
        stats = self.memory.get_statistics()
        if stats["total_turns"] > 0:
            print(f"Resuming conversation with {stats['total_turns']} previous turns")

    def respond(self, user_input: str) -> str:
        """
        Process user input and generate a response using conversation context.

        In a real implementation, this would call an LLM with the context.
        """
        # Build context for the response
        context = self.memory.build_llm_context(user_input, max_turns=5)

        # Simulate different types of responses based on the input
        response = self._generate_response(user_input, context)

        # Save the turn to memory
        self.memory.add_turn(user_input, response)

        return response

    def _generate_response(self, user_input: str, context: str) -> str:
        """
        Simulate response generation (would use LLM in real implementation).
        """
        user_lower = user_input.lower()

        # Check for memory-related queries
        if "remember" in user_lower or "recall" in user_lower or "forgot" in user_lower:
            return self._handle_memory_query(user_input)

        # Check for conversation history queries
        if "talked about" in user_lower or "discussed" in user_lower or "said" in user_lower:
            return self._handle_history_query(user_input)

        # Check for name-related queries
        if "my name" in user_lower:
            return self._handle_name_query(user_input)

        # Default responses for demo
        responses = {
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! What would you like to talk about?",
            "help": "I can help you with various topics. I also remember our conversation history!",
            "bye": "Goodbye! Our conversation is saved and I'll remember it next time.",
        }

        for key, response in responses.items():
            if key in user_lower:
                return response

        return f"I understand you said: '{user_input}'. How can I help you with that?"

    def _handle_memory_query(self, user_input: str) -> str:
        """Handle queries about memory and recall."""
        recent = self.memory.get_recent_context(3)
        if not recent:
            return "We haven't talked about anything yet in this conversation."

        topics = []
        for turn in recent:
            # Extract key words from user inputs (simple approach)
            words = turn["user_input"].lower().split()
            topics.extend([w for w in words if len(w) > 4 and w not in ["about", "remember", "recall"]])

        if topics:
            unique_topics = list(set(topics))[:3]
            return f"I remember we discussed: {', '.join(unique_topics)}"
        else:
            return "I remember our recent conversation, though we haven't discussed specific topics yet."

    def _handle_history_query(self, user_input: str) -> str:
        """Handle queries about conversation history."""
        # Search for specific topics mentioned
        words = user_input.lower().split()
        search_terms = [w for w in words if len(w) > 3 and w not in ["what", "talked", "about", "discussed", "said"]]

        if search_terms:
            results = self.memory.search_history(search_terms[0])
            if results:
                turn = results[0]
                return f"Yes, you mentioned '{search_terms[0]}' when you said: '{turn['user_input']}'"

        # Give general history summary
        stats = self.memory.get_statistics()
        return f"We've had {stats['total_turns']} exchanges in our conversation so far."

    def _handle_name_query(self, user_input: str) -> str:
        """Handle name-related queries."""
        # Search for name introductions
        name_patterns = ["my name is", "i'm", "i am", "call me"]

        for pattern in name_patterns:
            results = self.memory.search_history(pattern)
            if results:
                # Extract name from the introduction
                intro = results[0]["user_input"]
                for p in name_patterns:
                    if p in intro.lower():
                        # Simple extraction (would be better with NLP)
                        parts = intro.lower().split(p)
                        if len(parts) > 1:
                            name = parts[1].strip().split()[0].title()
                            return f"Yes, I remember your name is {name}."

        return "I don't think you've told me your name yet."


def demo_conversation():
    """Run a demonstration conversation."""
    print("=== Conversational Agent Demo ===\n")

    agent = ConversationalAgent("demo_agent_memory.json")

    # Simulate a conversation
    conversations = [
        "Hi there!",
        "My name is Bob",
        "What's the weather like today?",
        "Can you remember my name?",
        "What have we talked about so far?",
        "I'm interested in learning Python",
        "Did I mention my name earlier?",
        "Tell me about Python functions",
        "What topics have we discussed?",
        "Goodbye!",
    ]

    for user_msg in conversations:
        print(f"\n👤 User: {user_msg}")
        response = agent.respond(user_msg)
        print(f"🤖 Agent: {response}")

    print("\n=== Conversation Statistics ===")
    stats = agent.memory.get_statistics()
    print(f"Total turns: {stats['total_turns']}")
    print(f"Session count: {stats['session_count']}")
    print("Memory file: demo_agent_memory.json")


def demo_multi_session():
    """Demonstrate conversation continuity across sessions."""
    print("\n=== Multi-Session Demo ===\n")

    # First session
    print("--- Session 1 ---")
    agent1 = ConversationalAgent("multi_session_memory.json")
    agent1.respond("Hi, my name is Sarah")
    agent1.respond("I'm learning about machine learning")
    agent1.respond("Bye for now")

    # Simulate closing the agent
    del agent1

    # Second session (simulating restart)
    print("\n--- Session 2 (After Restart) ---")
    agent2 = ConversationalAgent("multi_session_memory.json")

    # The agent should remember the previous conversation
    print("\n👤 User: Do you remember my name?")
    response = agent2.respond("Do you remember my name?")
    print(f"🤖 Agent: {response}")

    print("\n👤 User: What was I learning about?")
    response = agent2.respond("What was I learning about?")
    print(f"🤖 Agent: {response}")


def demo_context_building():
    """Demonstrate how context is built for LLM prompts."""
    print("\n=== Context Building Demo ===\n")

    memory = ConversationMemory("context_demo.json", max_turns=5)

    # Add some conversation
    memory.add_turn("What's the capital of France?", "The capital of France is Paris.")
    memory.add_turn("How about Italy?", "The capital of Italy is Rome.")
    memory.add_turn("And Spain?", "The capital of Spain is Madrid.")

    # Show how context would be built for an LLM
    print("Context for LLM when user asks 'What about Germany?':\n")
    print("-" * 60)
    context = memory.build_llm_context("What about Germany?")
    print(context)
    print("-" * 60)

    # Clean up
    import os

    os.remove("context_demo.json")


def main():
    """Run all demonstrations."""
    demo_conversation()
    demo_multi_session()
    demo_context_building()

    # Cleanup demo files
    import os

    for f in ["demo_agent_memory.json", "multi_session_memory.json"]:
        if os.path.exists(f):
            os.remove(f)

    print("\n✅ All demos completed!")


if __name__ == "__main__":
    main()
