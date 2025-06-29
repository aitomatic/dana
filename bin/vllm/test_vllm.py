#!/usr/bin/env python3
"""
Test and interact with local vLLM server
Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

This script provides multiple ways to test your vLLM installation:
1. Health check and server validation
2. Single query testing
3. Interactive chat mode
4. Batch testing with sample prompts
5. Model information and capabilities

Usage:
    python bin/vllm/test_vllm.py --help
    python bin/vllm/test_vllm.py --health
    python bin/vllm/test_vllm.py --chat
    python bin/vllm/test_vllm.py --query "What is machine learning?"
    python bin/vllm/test_vllm.py --batch
"""

import argparse
import json
import sys
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library not found.")
    print("Please install it: pip install requests")
    sys.exit(1)


@dataclass
class VLLMConfig:
    """Configuration for vLLM server connection."""
    host: str = "localhost"
    port: int = 8000
    timeout: int = 30
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def completions_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"
    
    @property
    def models_url(self) -> str:
        return f"{self.base_url}/v1/models"
    
    @property
    def health_url(self) -> str:
        return f"{self.base_url}/health"


class VLLMTester:
    """Test and interact with vLLM server."""
    
    def __init__(self, config: VLLMConfig):
        self.config = config
        self.session = requests.Session()
        self.session.timeout = config.timeout
        
    def check_health(self) -> bool:
        """Check if vLLM server is healthy and responding."""
        print(f"🏥 Checking vLLM server health at {self.config.base_url}...")
        
        try:
            # Try health endpoint first
            response = self.session.get(self.config.health_url)
            if response.status_code == 200:
                print("✅ Health endpoint responded successfully")
                return True
        except requests.exceptions.RequestException:
            pass
        
        try:
            # Fallback to models endpoint
            response = self.session.get(self.config.models_url)
            if response.status_code == 200:
                print("✅ Server is responding (via models endpoint)")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to vLLM server at {self.config.base_url}")
            print("💡 Make sure vLLM server is running:")
            print("   ./bin/start_vllm.sh")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ Connection timed out after {self.config.timeout} seconds")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def get_models(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of available models from the server."""
        try:
            response = self.session.get(self.config.models_url)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('data', [])
            
            print(f"📋 Available models ({len(models)}):")
            for i, model in enumerate(models, 1):
                model_id = model.get('id', 'Unknown')
                created = model.get('created', 0)
                created_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created)) if created else 'Unknown'
                print(f"   {i}. {model_id} (created: {created_str})")
            
            return models
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get models: {e}")
            return None
    
    def send_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
        stream: bool = False
    ) -> Optional[str]:
        """Send a completion request to vLLM server."""
        
        # Get model if not specified
        if not model:
            models = self.get_models()
            if not models:
                return None
            model = models[0]['id']  # Use first available model
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            print(f"🤖 Sending request to model: {model}")
            print(f"💭 Query: {message}")
            print("⏳ Waiting for response...")
            
            start_time = time.time()
            response = self.session.post(
                self.config.completions_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            response.raise_for_status()
            
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                usage = data.get('usage', {})
                
                print(f"\n✅ Response received in {end_time - start_time:.2f} seconds")
                print("🤖 AI Response:")
                print("-" * 50)
                print(content)
                print("-" * 50)
                
                # Show usage statistics if available
                if usage:
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                    total_tokens = usage.get('total_tokens', 0)
                    
                    print(f"📊 Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")
                    
                    if completion_tokens > 0 and end_time > start_time:
                        tokens_per_sec = completion_tokens / (end_time - start_time)
                        print(f"⚡ Speed: {tokens_per_sec:.1f} tokens/second")
                
                return content
            else:
                print("❌ No response content received")
                print(f"Response data: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {e.response.text}")
            return None
    
    def interactive_chat(self, model: Optional[str] = None):
        """Start an interactive chat session."""
        print("🗣️  Starting interactive chat mode")
        print("💡 Type 'quit', 'exit', or 'bye' to stop")
        print("💡 Type 'clear' to clear conversation history")
        print("💡 Type 'help' for more commands")
        print("=" * 50)
        
        # Get model if not specified
        if not model:
            models = self.get_models()
            if not models:
                return
            model = models[0]['id']
        
        conversation_history = []
        
        while True:
            try:
                user_input = input(f"\n🧑 You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                    
                if user_input.lower() == 'clear':
                    conversation_history.clear()
                    print("🧹 Conversation history cleared")
                    continue
                    
                if user_input.lower() == 'help':
                    print("🆘 Available commands:")
                    print("   quit/exit/bye - Exit chat")
                    print("   clear - Clear conversation history")
                    print("   help - Show this help")
                    print("   Just type normally to chat!")
                    continue
                
                # Add user message to conversation
                conversation_history.append({"role": "user", "content": user_input})
                
                # Prepare payload with full conversation
                payload = {
                    "model": model,
                    "messages": conversation_history.copy(),
                    "temperature": 0.7,
                    "max_tokens": 300,
                    "stream": False
                }
                
                print("🤖 AI is thinking...")
                
                start_time = time.time()
                response = self.session.post(
                    self.config.completions_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                end_time = time.time()
                
                response.raise_for_status()
                data = response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    ai_response = data['choices'][0]['message']['content']
                    
                    # Add AI response to conversation
                    conversation_history.append({"role": "assistant", "content": ai_response})
                    
                    print(f"🤖 AI ({end_time - start_time:.1f}s): {ai_response}")
                else:
                    print("❌ No response received")
                    
            except KeyboardInterrupt:
                print("\n👋 Chat interrupted. Goodbye!")
                break
            except requests.exceptions.RequestException as e:
                print(f"❌ Request failed: {e}")
                print("💡 Check if vLLM server is still running")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
    
    def run_batch_tests(self, model: Optional[str] = None):
        """Run a series of test prompts to validate the model."""
        test_prompts = [
            "What is the capital of France?",
            "Explain machine learning in simple terms.",
            "Write a short Python function to calculate factorial.",
            "What are the benefits of renewable energy?",
            "Tell me a short joke about programming."
        ]
        
        print("🧪 Running batch tests...")
        print(f"📝 Testing {len(test_prompts)} prompts")
        print("=" * 50)
        
        successful_tests = 0
        total_time = 0
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🔬 Test {i}/{len(test_prompts)}: {prompt[:50]}...")
            
            start_time = time.time()
            response = self.send_completion(prompt, model, max_tokens=100)
            end_time = time.time()
            
            if response:
                successful_tests += 1
                total_time += (end_time - start_time)
                print(f"✅ Test {i} passed")
            else:
                print(f"❌ Test {i} failed")
        
        print("=" * 50)
        print(f"📊 Batch test results:")
        print(f"   ✅ Successful: {successful_tests}/{len(test_prompts)}")
        print(f"   ❌ Failed: {len(test_prompts) - successful_tests}/{len(test_prompts)}")
        
        if successful_tests > 0:
            avg_time = total_time / successful_tests
            print(f"   ⏱️  Average response time: {avg_time:.2f} seconds")
        
        if successful_tests == len(test_prompts):
            print("🎉 All tests passed! Your vLLM server is working perfectly.")
        elif successful_tests > 0:
            print("⚠️  Some tests failed. Check server logs for details.")
        else:
            print("💥 All tests failed. Check your vLLM server configuration.")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test and interact with local vLLM server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --health                           # Check server health
    %(prog)s --models                           # List available models
    %(prog)s --query "What is AI?"              # Single query
    %(prog)s --chat                             # Interactive chat
    %(prog)s --batch                            # Run batch tests
    %(prog)s --host localhost --port 8080       # Custom server location
        """
    )
    
    parser.add_argument(
        "--host", 
        default="localhost", 
        help="vLLM server host (default: localhost)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="vLLM server port (default: 8000)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=30, 
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--model", 
        help="Specific model to use (default: use first available)"
    )
    
    # Action arguments
    parser.add_argument(
        "--health", 
        action="store_true", 
        help="Check server health and connectivity"
    )
    parser.add_argument(
        "--models", 
        action="store_true", 
        help="List available models"
    )
    parser.add_argument(
        "--query", 
        help="Send a single query to the model"
    )
    parser.add_argument(
        "--chat", 
        action="store_true", 
        help="Start interactive chat mode"
    )
    parser.add_argument(
        "--batch", 
        action="store_true", 
        help="Run batch tests with sample prompts"
    )
    
    args = parser.parse_args()
    
    # If no action specified, show help
    if not any([args.health, args.models, args.query, args.chat, args.batch]):
        parser.print_help()
        return
    
    # Create configuration and tester
    config = VLLMConfig(host=args.host, port=args.port, timeout=args.timeout)
    tester = VLLMTester(config)
    
    print(f"🎯 Connecting to vLLM server at {config.base_url}")
    print(f"⏱️  Timeout: {config.timeout} seconds")
    print()
    
    # Always check health first
    if not tester.check_health():
        print("\n💡 Start your vLLM server first:")
        print("   ./bin/start_vllm.sh")
        print("   # Then run this test script again")
        sys.exit(1)
    
    print()
    
    # Execute requested actions
    if args.health:
        print("✅ Health check completed successfully!")
    
    if args.models:
        tester.get_models()
    
    if args.query:
        tester.send_completion(args.query, args.model)
    
    if args.chat:
        tester.interactive_chat(args.model)
    
    if args.batch:
        tester.run_batch_tests(args.model)


if __name__ == "__main__":
    main() 