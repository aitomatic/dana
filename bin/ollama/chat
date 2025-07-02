#!/bin/bash
#
# chat.sh: Starts an interactive chat session with a specified Ollama model.
#
# Usage:
#   ./bin/ollama/chat.sh --model <model_name>
#

MODEL_NAME="phi3:mini" # Default model

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model) MODEL_NAME="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$MODEL_NAME" ]; then
    echo "❌ Error: Model name not specified."
    echo "Usage: ./bin/ollama/chat.sh --model <model_name>"
    exit 1
fi

echo "💬 Starting chat with model: ${MODEL_NAME}"
echo "   (Type '/bye' to exit)"
echo "---"

ollama run "${MODEL_NAME}" 