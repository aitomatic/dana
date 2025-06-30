#!/bin/bash
#
# start.sh: Starts the Ollama service, pulls a model, and configures environment variables.
#
# Usage:
#   ./bin/ollama/start.sh [--model <model_name>]
#
# The script performs the following actions:
# 1. Checks if Ollama is installed.
# 2. Ensures the Ollama background service is running.
# 3. Provides an interactive menu to select and pull a model.
# 4. Exports LOCAL_LLM_URL and LOCAL_LLM_NAME for OpenDXA integration.
#

set -e
set -o pipefail

# --- Configuration ---
DEFAULT_MODEL="phi3:mini"
OLLAMA_HOST="localhost"
OLLAMA_PORT="11434"
MODEL_SELECTED=""

# --- Color Codes ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- Helper Functions ---
function check_ollama_installed() {
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}❌ Error: 'ollama' command not found.${NC}"
        echo -e "${YELLOW}Please install Ollama first by running: ./bin/ollama/install.sh${NC}"
        exit 1
    fi
}

function ensure_service_running() {
    echo -e "${BLUE}🔄 Checking Ollama service status...${NC}"
    # On macOS, launchd handles the service. `ollama ps` is a reliable way to check if the server is responsive.
    if ollama ps >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama service is already running.${NC}"
    else
        echo -e "${YELLOW}Ollama service is not running. Starting it now...${NC}"
        # This will start the app and its associated background service.
        open -a Ollama
        # Wait for the service to start
        echo -e "${BLUE}⌛ Waiting for Ollama service to initialize...${NC}"
        sleep 5
        if ! ollama ps >/dev/null 2>&1; then
            echo -e "${RED}❌ Failed to start Ollama service.${NC}"
            echo -e "${YELLOW}Try starting the Ollama app manually from your Applications folder.${NC}"
            exit 1
        else
            echo -e "${GREEN}✅ Ollama service started successfully.${NC}"
        fi
    fi
}

function show_model_menu() {
    echo -e "\n${BLUE}🤖 Select a model to run:${NC}"
    echo "   1) Phi-3 Mini (3.8B) - Microsoft's efficient model (default)"
    echo "   2) Llama 3 (8B) - Meta's powerful model"
    echo "   3) Qwen (4B) - Alibaba's compact powerhouse"
    echo "   4) Gemma (2B) - Google's lightweight model"
    echo "   5) Mistral (7B) - Mistral AI's popular model"
    echo "   ---"
    echo "   6) Enter custom model name"
    echo "   0) Exit"
}

function pull_model() {
    local model_name=$1
    echo -e "\n${BLUE}🔍 Checking for model '${model_name}'...${NC}"
    if ollama list | grep -q "^${model_name}"; then
        echo -e "${GREEN}✅ Model '${model_name}' is already available locally.${NC}"
    else
        echo -e "${YELLOW}Model '${model_name}' not found locally. Pulling from Ollama Hub...${NC}"
        if ! ollama pull "${model_name}"; then
            echo -e "${RED}❌ Failed to pull model '${model_name}'.${NC}"
            echo -e "${YELLOW}Please check the model name and your internet connection.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Successfully pulled model '${model_name}'.${NC}"
    fi
    MODEL_SELECTED="${model_name}"
}

# --- Main Script ---

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model) MODEL_SELECTED="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

check_ollama_installed
ensure_service_running

if [ -z "$MODEL_SELECTED" ]; then
    while true; do
        show_model_menu
        read -p "Enter your choice (1-6): " choice
        case $choice in
            1) pull_model "phi3:mini"; break ;;
            2) pull_model "llama3"; break ;;
            3) pull_model "qwen:4b"; break ;;
            4) pull_model "gemma:2b"; break ;;
            5) pull_model "mistral"; break ;;
            6)
                read -p "Enter custom model name (e.g., codellama:7b): " custom_model
                if [ -n "$custom_model" ]; then
                    pull_model "$custom_model"
                    break
                else
                    echo -e "${RED}Invalid name. Please try again.${NC}"
                fi
                ;;
            0) echo "👋 Exiting."; exit 0 ;;
            *) echo -e "${RED}Invalid choice. Please try again.${NC}" ;;
        esac
    done
else
    pull_model "$MODEL_SELECTED"
fi

# --- Configure Environment for OpenDXA ---
export LOCAL_LLM_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}/v1"
export LOCAL_LLM_NAME="${MODEL_SELECTED}"

echo -e "\n${GREEN}✅ Configuration complete!${NC}"
echo -e "Ollama is running with model: ${YELLOW}${MODEL_SELECTED}${NC}"
echo -e "\nEnvironment variables have been set for this shell session:"
echo -e "  - ${BLUE}LOCAL_LLM_URL${NC}=${YELLOW}${LOCAL_LLM_URL}${NC}"
echo -e "  - ${BLUE}LOCAL_LLM_NAME${NC}=${YELLOW}${LOCAL_LLM_NAME}${NC}"
echo -e "\nThese variables allow OpenDXA to connect to the local Ollama server."
echo -e "To start an interactive chat session, run: ${YELLOW}./bin/ollama/chat.sh --model ${MODEL_SELECTED}${NC}"
echo -e "\n${BLUE}You can now run your OpenDXA applications in this terminal.${NC}" 