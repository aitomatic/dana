#!/bin/bash
# Chat with vLLM Server
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/vllm/chat.sh [OPTIONS]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_HOST="localhost"
DEFAULT_PORT="8000"
DEFAULT_TIMEOUT="30"

# Parse command line arguments
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
TIMEOUT="$DEFAULT_TIMEOUT"
MODEL=""

show_help() {
    echo "Chat with vLLM Server"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --host HOST          vLLM server host (default: $DEFAULT_HOST)"
    echo "  --port PORT          vLLM server port (default: $DEFAULT_PORT)"
    echo "  --timeout TIMEOUT    Request timeout in seconds (default: $DEFAULT_TIMEOUT)"
    echo "  --model MODEL        Specific model to use (default: first available)"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Chat with default server"
    echo "  $0 --port 8080                       # Chat with server on port 8080"
    echo "  $0 --model microsoft/Phi-4           # Chat with specific model"
    echo ""
    echo "Chat Commands:"
    echo "  quit, exit, bye      Exit chat"
    echo "  clear               Clear conversation history"
    echo "  help                Show chat help"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

BASE_URL="http://$HOST:$PORT"
COMPLETIONS_URL="$BASE_URL/v1/chat/completions"
MODELS_URL="$BASE_URL/v1/models"

echo -e "${BLUE}💬 vLLM Chat Interface${NC}"
echo -e "${BLUE}Server: $BASE_URL${NC}"
echo ""

# Check if server is responding
echo -e "${YELLOW}🔍 Checking server connection...${NC}"
if ! curl -s --max-time 5 "$BASE_URL/health" >/dev/null 2>&1 && ! curl -s --max-time 5 "$MODELS_URL" >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to vLLM server at $BASE_URL${NC}"
    echo -e "${YELLOW}💡 Make sure vLLM server is running:${NC}"
    echo "   ./bin/vllm/start.sh"
    exit 1
fi

echo -e "${GREEN}✅ Connected to server${NC}"

# Get available models and select one
echo -e "${YELLOW}📋 Getting available models...${NC}"
if [[ -z "$MODEL" ]]; then
    MODELS_RESPONSE=$(curl -s --max-time "$TIMEOUT" "$MODELS_URL")
    if [[ $? -eq 0 ]]; then
        MODEL=$(echo "$MODELS_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    models = data.get('data', [])
    if models:
        print(models[0]['id'])
    else:
        print('facebook/opt-125m')
except:
    print('facebook/opt-125m')
" 2>/dev/null)
    fi
    
    if [[ -z "$MODEL" ]]; then
        MODEL="facebook/opt-125m"
    fi
fi

echo -e "${GREEN}🤖 Using model: $MODEL${NC}"
echo ""
echo -e "${CYAN}💡 Chat Commands:${NC}"
echo "  • Type naturally to chat with the AI"
echo "  • 'quit', 'exit', or 'bye' to stop"
echo "  • 'clear' to clear conversation history"
echo "  • 'help' for more commands"
echo "=" * 50

# Initialize conversation
conversation_file=$(mktemp)
echo "[]" > "$conversation_file"

# Chat loop
while true; do
    echo -ne "\n${CYAN}🧑 You: ${NC}"
    read -r user_input
    
    if [[ -z "$user_input" ]]; then
        continue
    fi
    
    case "${user_input,,}" in
        quit|exit|bye)
            echo -e "${YELLOW}👋 Goodbye!${NC}"
            break
            ;;
        clear)
            echo "[]" > "$conversation_file"
            echo -e "${GREEN}🧹 Conversation history cleared${NC}"
            continue
            ;;
        help)
            echo -e "${CYAN}🆘 Available commands:${NC}"
            echo "   quit/exit/bye - Exit chat"
            echo "   clear - Clear conversation history"
            echo "   help - Show this help"
            echo "   Just type naturally to chat!"
            continue
            ;;
    esac
    
    # Add user message to conversation
    conversation=$(cat "$conversation_file")
    new_conversation=$(echo "$conversation" | python3 -c "
import json, sys
conversation = json.load(sys.stdin)
conversation.append({'role': 'user', 'content': '''$user_input'''})
json.dump(conversation, sys.stdout)
")
    echo "$new_conversation" > "$conversation_file"
    
    # Prepare API request
    request_data=$(cat "$conversation_file" | python3 -c "
import json, sys
conversation = json.load(sys.stdin)
request = {
    'model': '''$MODEL''',
    'messages': conversation,
    'temperature': 0.7,
    'max_tokens': 300,
    'stream': False
}
json.dump(request, sys.stdout)
")
    
    echo -e "${YELLOW}🤖 AI is thinking...${NC}"
    
    # Send request to vLLM
    start_time=$(date +%s.%N)
    response=$(curl -s --max-time "$TIMEOUT" -X POST "$COMPLETIONS_URL" \
        -H "Content-Type: application/json" \
        -d "$request_data")
    end_time=$(date +%s.%N)
    
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}❌ Request failed. Check if server is still running.${NC}"
        continue
    fi
    
    # Extract AI response
    ai_response=$(echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'choices' in data and len(data['choices']) > 0:
        print(data['choices'][0]['message']['content'])
    else:
        print('No response received')
except Exception as e:
    print(f'Error parsing response: {e}')
" 2>/dev/null)
    
    if [[ -z "$ai_response" || "$ai_response" == "No response received" ]]; then
        echo -e "${RED}❌ No response received from AI${NC}"
        echo -e "${YELLOW}Raw response: $response${NC}"
        continue
    fi
    
    # Calculate response time
    response_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "?")
    
    # Add AI response to conversation
    conversation=$(cat "$conversation_file")
    new_conversation=$(echo "$conversation" | python3 -c "
import json, sys
conversation = json.load(sys.stdin)
conversation.append({'role': 'assistant', 'content': '''$ai_response'''})
json.dump(conversation, sys.stdout)
")
    echo "$new_conversation" > "$conversation_file"
    
    # Display AI response
    echo -e "${GREEN}🤖 AI (${response_time}s): ${NC}$ai_response"
done

# Cleanup
rm -f "$conversation_file" 