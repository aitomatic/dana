#!/bin/bash
# Test vLLM server using curl
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

set -e

# Configuration
HOST="${1:-localhost}"
PORT="${2:-8000}"
BASE_URL="http://$HOST:$PORT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing vLLM Server with curl${NC}"
echo -e "${BLUE}Server: $BASE_URL${NC}"
echo "="*50

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="${4:-}"
    
    echo -e "\n${CYAN}🔍 Testing: $name${NC}"
    echo "URL: $url"
    echo "Method: $method"
    
    if [[ -n "$data" ]]; then
        echo "Data: $data"
        echo ""
        curl -s -X "$method" "$url" \
             -H "Content-Type: application/json" \
             -d "$data" | jq '.' 2>/dev/null || curl -s -X "$method" "$url" -H "Content-Type: application/json" -d "$data"
    else
        echo ""
        curl -s -X "$method" "$url" | jq '.' 2>/dev/null || curl -s -X "$method" "$url"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Test completed${NC}"
}

# 1. Health Check
echo -e "\n${YELLOW}1. Health Check${NC}"
test_endpoint "Health Status" "$BASE_URL/health"

# 2. List Models
echo -e "\n${YELLOW}2. List Available Models${NC}"
test_endpoint "Available Models" "$BASE_URL/v1/models"

# 3. Simple Chat Completion
echo -e "\n${YELLOW}3. Simple Chat Completion${NC}"
chat_data='{
  "model": "facebook/opt-125m",
  "messages": [
    {"role": "user", "content": "Hello! How are you?"}
  ],
  "max_tokens": 50,
  "temperature": 0.7
}'
test_endpoint "Chat Completion" "$BASE_URL/v1/chat/completions" "POST" "$chat_data"

# 4. Coding Question
echo -e "\n${YELLOW}4. Coding Question${NC}"
code_data='{
  "model": "facebook/opt-125m",
  "messages": [
    {"role": "user", "content": "Write a Python function to reverse a string."}
  ],
  "max_tokens": 100,
  "temperature": 0.3
}'
test_endpoint "Code Generation" "$BASE_URL/v1/chat/completions" "POST" "$code_data"

# 5. Explanation Request
echo -e "\n${YELLOW}5. Explanation Request${NC}"
explain_data='{
  "model": "facebook/opt-125m",
  "messages": [
    {"role": "user", "content": "Explain machine learning in simple terms."}
  ],
  "max_tokens": 150,
  "temperature": 0.5
}'
test_endpoint "Explanation" "$BASE_URL/v1/chat/completions" "POST" "$explain_data"

echo ""
echo -e "${GREEN}🎉 All curl tests completed!${NC}"
echo ""
echo -e "${CYAN}💡 Tips:${NC}"
echo "• Install jq for better JSON formatting: brew install jq"
echo "• Change model name in JSON data to test different models"
echo "• Adjust temperature (0.0-1.0) to control randomness"
echo "• Modify max_tokens to control response length"
echo ""
echo -e "${CYAN}🔧 Custom usage:${NC}"
echo "  $0                    # Test localhost:8000"
echo "  $0 localhost 8080     # Test localhost:8080"
echo "  $0 192.168.1.100      # Test remote server" 