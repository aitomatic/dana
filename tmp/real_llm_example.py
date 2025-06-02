#!/usr/bin/env python3
"""
Real LLM Integration Example

This shows how to connect the IPV prototype to real LLM providers.
"""

import os

from prototype_ipv import IPVPromptOptimizer


# Example 1: OpenAI Integration
class OpenAILLM:
    def __init__(self, model="gpt-4o-mini"):
        try:
            import openai

            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = model
            self.call_count = 0
        except ImportError:
            raise ImportError("Install openai: uv add openai")

    def call(self, prompt: str) -> str:
        self.call_count += 1
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}], temperature=0.1  # Low temperature for consistency
            )
            content = response.choices[0].message.content
            return content if content is not None else "Error: Empty response from LLM"
        except Exception as e:
            print(f"LLM call failed: {e}")
            return "Error: Could not get LLM response"


# Example 2: Anthropic Integration
class AnthropicLLM:
    def __init__(self, model="claude-3-haiku-20240307"):
        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = model
            self.call_count = 0
        except ImportError:
            raise ImportError("Install anthropic: uv add anthropic")

    def call(self, prompt: str) -> str:
        self.call_count += 1
        try:
            response = self.client.messages.create(model=self.model, max_tokens=1000, messages=[{"role": "user", "content": prompt}])
            return response.content[0].text
        except Exception as e:
            print(f"LLM call failed: {e}")
            return "Error: Could not get LLM response"


# Example 3: Local LLM (Ollama)
class OllamaLLM:
    def __init__(self, model="llama3.2"):
        try:
            import requests

            self.model = model
            self.call_count = 0
            self.base_url = "http://localhost:11434"
        except ImportError:
            raise ImportError("Install requests: uv add requests")

    def call(self, prompt: str) -> str:
        self.call_count += 1
        try:
            import requests

            response = requests.post(f"{self.base_url}/api/generate", json={"model": self.model, "prompt": prompt, "stream": False})
            return response.json()["response"]
        except Exception as e:
            print(f"LLM call failed: {e}")
            return "Error: Could not get LLM response"


def demo_with_real_llm():
    """Demo IPV with real LLM calls"""

    print("🚀 IPV with Real LLM Integration")
    print("=" * 50)

    # Choose your LLM provider
    llm_choice = input("Choose LLM (1=OpenAI, 2=Anthropic, 3=Ollama, 4=Mock): ")

    optimizer = IPVPromptOptimizer(verbose=True)  # Enable verbose mode to show prompts

    if llm_choice == "1":
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Set OPENAI_API_KEY environment variable")
            return
        optimizer.llm = OpenAILLM()
        print("✅ Using OpenAI GPT-4o-mini")

    elif llm_choice == "2":
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("❌ Set ANTHROPIC_API_KEY environment variable")
            return
        optimizer.llm = AnthropicLLM()
        print("✅ Using Anthropic Claude")

    elif llm_choice == "3":
        optimizer.llm = OllamaLLM()
        print("✅ Using Ollama (make sure it's running)")

    else:
        print("✅ Using Mock LLM (no real calls)")

    # Test IPV with real LLM
    print("\n" + "=" * 50)
    print("Testing IPV with Real LLM Responses")
    print("=" * 50)

    try:
        # Test 1: Price extraction
        print("\n1. Price extraction:")
        price = optimizer.reason("The invoice shows a total of $127.50 including tax. Extract the price.", expected_type=float)
        print(f"✅ Extracted price: {price} (type: {type(price).__name__})")

        # Test 2: Boolean classification
        print("\n2. Urgency classification:")
        urgent = optimizer.reason("URGENT: Server is down and customers can't access the site!", expected_type=bool)
        print(f"✅ Is urgent: {urgent} (type: {type(urgent).__name__})")

        # Test 3: Clean text extraction
        print("\n3. Clean text extraction:")
        summary = optimizer.reason("Summarize: Our Q4 results exceeded expectations with 25% growth.", expected_type=str)
        print(f"✅ Summary: {summary} (type: {type(summary).__name__})")

        print(f"\n📊 Total LLM calls made: {optimizer.llm.call_count}")
        print("🎉 IPV successfully handled real LLM responses!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure your API keys are set and LLM service is available")


def setup_instructions():
    """Show setup instructions for real LLM integration"""

    print("🔧 Setup Instructions for Real LLM Integration")
    print("=" * 60)

    print("\n1. OpenAI Setup:")
    print("   uv add openai")
    print("   export OPENAI_API_KEY='your-api-key'")

    print("\n2. Anthropic Setup:")
    print("   uv add anthropic")
    print("   export ANTHROPIC_API_KEY='your-api-key'")

    print("\n3. Ollama Setup (Local):")
    print("   # Install Ollama from https://ollama.ai")
    print("   ollama pull llama3.2")
    print("   ollama serve")
    print("   uv add requests")

    print("\n4. Then run this script to test with real LLMs!")


if __name__ == "__main__":
    choice = input("1=Demo with real LLM, 2=Show setup instructions: ")

    if choice == "1":
        demo_with_real_llm()
    else:
        setup_instructions()
