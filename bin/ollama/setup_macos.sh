#!/bin/bash
#
# setup_macos.sh: Unified Ollama installer + Dana configuration helper (macOS)
#
# Mirrors setup.sh but uses Homebrew to manage Ollama.
#
# Usage:
#   bash ./bin/ollama/setup_macos.sh
#

set -e
set -o pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}" )/../.." && pwd)"
PROJECT_ENV="${PROJECT_ROOT}/.env"
USER_ENV_DIR="$HOME/.dana"
USER_ENV="${USER_ENV_DIR}/.env"

ENV_FILES=()
CONFIGURE_LM=false
CONFIGURE_EMBEDDINGS=false

LM_MODEL=""
LM_API_KEY=""
LM_BASE_URL=""

EMBED_MODEL=""
EMBED_BASE_URL=""
EMBED_DIMENSIONS=""
EMBED_BATCH_SIZE=""
INSTALLED_MODELS=()

prompt_yes_no() {
    local prompt_message="$1"
    local default_answer="${2:-y}"
    local reply
    while true; do
        read -r -p "$prompt_message [y/n] (default: $default_answer): " reply
        reply=${reply:-$default_answer}
        case "$reply" in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) echo "Please answer y or n." ;;
        esac
    done
}

require_command() {
    local cmd="$1"
    local package_hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}❌ Required command '$cmd' not found.${NC}"
        if [[ -n "$package_hint" ]]; then
            echo -e "${YELLOW}Install hint: $package_hint${NC}"
        fi
        exit 1
    fi
}

update_env_var() {
    local file_path="$1"
    local key="$2"
    local value="$3"

    python3 - "$file_path" "$key" "$value" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
key = sys.argv[2]
value = sys.argv[3]

if not path.parent.exists():
    path.parent.mkdir(parents=True, exist_ok=True)

lines = []
if path.exists():
    with path.open("r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

updated = False
for idx, line in enumerate(lines):
    stripped = line.lstrip("#")
    if stripped.startswith(f"{key}="):
        lines[idx] = f"{key}={value}"
        updated = True
        break

if not updated:
    lines.append(f"{key}={value}")

with path.open("w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
    fh.write("\n")
PY
}

trim_trailing_slash() {
    local value="$1"
    value="${value%%/}"
    printf '%s' "$value"
}

derive_embedding_base() {
    local url="$1"
    [[ -z "$url" ]] && return
    local trimmed="${url%/}"
    if [[ "$trimmed" == */v1 ]]; then
        trimmed="${trimmed%/v1}"
    fi
    trim_trailing_slash "$trimmed"
}

load_installed_models() {
    INSTALLED_MODELS=()
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        if [[ "$line" == NAME* ]]; then
            continue
        fi
        local model
        model=$(echo "$line" | awk '{print $1}')
        if [[ -n "$model" ]]; then
            INSTALLED_MODELS+=("$model")
        fi
    done < <(ollama list 2>/dev/null || true)
}

install_ollama_macos() {
    echo -e "${BLUE}📦 Attempting to install Ollama via Homebrew...${NC}"
    if ! command -v brew >/dev/null 2>&1; then
        echo -e "${RED}Homebrew is required but not installed.${NC}"
        echo -e "${YELLOW}Visit https://brew.sh/ to install Homebrew, then rerun this script.${NC}"
        exit 1
    fi

    if brew list --formula | grep -q '^ollama$'; then
        echo -e "${YELLOW}Ollama is already installed via Homebrew. Reinstalling to ensure freshness...${NC}"
        brew reinstall ollama
    else
        brew install ollama
    fi

    echo -e "${GREEN}✅ Homebrew reported Ollama installed.${NC}"
}

verify_ollama() {
    if ! command -v ollama >/dev/null 2>&1; then
        echo -e "${YELLOW}Ollama is not installed on this system.${NC}"
        if prompt_yes_no "Would you like to install Ollama now?" "y"; then
            install_ollama_macos
        else
            echo -e "${RED}Ollama is required for local inference. Exiting.${NC}"
            exit 1
        fi
    fi

    local version
    version=$(ollama --version 2>/dev/null || true)
    if [[ -z "$version" ]]; then
        echo -e "${RED}❌ 'ollama --version' did not return a version string.${NC}"
        echo -e "${YELLOW}Please ensure the Ollama application is installed and running.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Ollama detected: ${version}${NC}"
    echo
}

choose_env_targets() {
    echo -e "${BLUE}Where should we store your Ollama settings?${NC}"
    echo "  1) Project-only (.env in repository root) — keep settings isolated to this project."
    echo "  2) User-wide (~/.dana/.env) — reuse across all Dana projects for this user."
    echo "  3) Both project and user scopes."

    local choice
    while true; do
        read -r -p "Select an option (1-3): " choice
        case "$choice" in
            1)
                ENV_FILES=("$PROJECT_ENV")
                break
                ;;
            2)
                ENV_FILES=("$USER_ENV")
                break
                ;;
            3)
                ENV_FILES=("$PROJECT_ENV" "$USER_ENV")
                break
                ;;
            *)
                echo "Please enter 1, 2, or 3." ;;
        esac
    done

    for env_path in "${ENV_FILES[@]}"; do
        local dir
        dir="$(dirname "$env_path")"
        mkdir -p "$dir"
        touch "$env_path"
    done

    echo -e "${GREEN}We'll update: ${ENV_FILES[*]}${NC}"
    echo
}

choose_usage_mode() {
    echo -e "${BLUE}How do you plan to use Ollama?${NC}"
    echo "  1) Local language model only (chat, completions)."
    echo "  2) Local embedding model only."
    echo "  3) Both language model and embeddings."

    local choice
    while true; do
        read -r -p "Select an option (1-3): " choice
        case "$choice" in
            1)
                CONFIGURE_LM=true
                CONFIGURE_EMBEDDINGS=false
                break
                ;;
            2)
                CONFIGURE_LM=false
                CONFIGURE_EMBEDDINGS=true
                break
                ;;
            3)
                CONFIGURE_LM=true
                CONFIGURE_EMBEDDINGS=true
                echo -e "${YELLOW}Configuring both. We'll start with the language model, then embeddings.${NC}"
                break
                ;;
            *)
                echo "Please enter 1, 2, or 3." ;;
        esac
    done

    echo
}

select_installed_model() {
    load_installed_models
    local count=${#INSTALLED_MODELS[@]}

    if (( count == 0 )); then
        echo -e "${YELLOW}No local models found yet.${NC}"
        return 1
    fi

    echo -e "${BLUE}Installed models detected:${NC}"
    for idx in "${!INSTALLED_MODELS[@]}"; do
        echo "  $((idx+1))) ${INSTALLED_MODELS[idx]}"
    done
    echo "  $((count+1))) Choose from recommended list"
    echo "  $((count+2))) Enter a custom model name"

    local choice
    while true; do
        read -r -p "Select an option (1-$((count+2))): " choice
        if [[ "$choice" =~ ^[0-9]+$ ]]; then
            if (( choice >=1 && choice <= count )); then
                LM_MODEL="${INSTALLED_MODELS[choice-1]}"
                return 0
            elif (( choice == count + 1 )); then
                return 1
            elif (( choice == count + 2 )); then
                read -r -p "Enter custom model name: " custom
                if [[ -n "$custom" ]]; then
                    LM_MODEL="$custom"
                    return 0
                fi
            fi
        fi
        echo "Please choose a valid option."
    done
}

choose_recommended_lm() {
    echo -e "${BLUE}Recommended Ollama models:${NC}"
    echo "  1) phi3:mini — speedy and lightweight"
    echo "  2) llama3 — larger, needs 16+ GB RAM"
    echo "  3) mistral — balanced general model"
    echo "  4) qwen:4b — multilingual option"
    echo "  5) Enter a different model"

    local choice
    while true; do
        read -r -p "Select a model (1-5): " choice
        case "$choice" in
            1) LM_MODEL="phi3:mini"; break ;;
            2) LM_MODEL="llama3"; break ;;
            3) LM_MODEL="mistral"; break ;;
            4) LM_MODEL="qwen:4b"; break ;;
            5)
                read -r -p "Enter custom model name: " custom
                if [[ -n "$custom" ]]; then
                    LM_MODEL="$custom"
                    break
                fi
                ;;
        esac
        echo "Please choose a valid option."
    done
}

ensure_model_present() {
    local model_name="$1"
    if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -q "^${model_name}$"; then
        return 0
    fi

    echo -e "${YELLOW}Downloading model '${model_name}' via ollama pull...${NC}"
    if ! ollama pull "$model_name"; then
        echo -e "${RED}Failed to pull model '${model_name}'.${NC}"
        exit 1
    fi
}

configure_language_model() {
    echo -e "${BLUE}--- Language model setup ---${NC}"

    if ! select_installed_model; then
        choose_recommended_lm
    fi

    ensure_model_present "$LM_MODEL"

    read -r -p "LOCAL_API_KEY (Enter for 'no_key_needed'): " LM_API_KEY
    LM_API_KEY=${LM_API_KEY:-no_key_needed}

    local default_base="http://localhost:11434/v1"
    read -r -p "Base URL for OpenAI-compatible endpoint [${default_base}]: " LM_BASE_URL
    LM_BASE_URL=${LM_BASE_URL:-$default_base}

    for env_path in "${ENV_FILES[@]}"; do
        update_env_var "$env_path" "LOCAL_API_KEY" "$LM_API_KEY"
        update_env_var "$env_path" "LOCAL_BASE_URL" "$LM_BASE_URL"
        update_env_var "$env_path" "LOCAL_MODEL_NAME" "$LM_MODEL"
    done

    echo -e "${GREEN}Language model configuration saved.${NC}"
    echo
}

choose_embedding_model() {
    echo -e "${BLUE}Embedding model options:${NC}"
    echo "  1) nomic-embed-text — fastest for smaller contexts"
    echo "  2) mxbai-embed-large — higher quality, large contexts"
    echo "  3) bge-m3 — great multilingual coverage"
    echo "  4) Enter a different model"

    local choice
    while true; do
        read -r -p "Select an embedding model (1-4): " choice
        case "$choice" in
            1)
                EMBED_MODEL="nomic-embed-text"
                EMBED_DIMENSIONS="768"
                break
                ;;
            2)
                EMBED_MODEL="mxbai-embed-large"
                EMBED_DIMENSIONS="1024"
                break
                ;;
            3)
                EMBED_MODEL="bge-m3"
                EMBED_DIMENSIONS="1024"
                break
                ;;
            4)
                read -r -p "Enter custom embedding model name: " custom
                if [[ -n "$custom" ]]; then
                    EMBED_MODEL="$custom"
                    read -r -p "Embedding dimensions (see Ollama model page): " EMBED_DIMENSIONS
                    if [[ -n "$EMBED_DIMENSIONS" ]]; then
                        break
                    fi
                    echo "Dimensions cannot be empty."
                fi
                ;;
        esac
        echo "Please choose a valid option."
    done
}

configure_embeddings() {
    echo -e "${BLUE}--- Embedding setup ---${NC}"

    choose_embedding_model
    ensure_model_present "$EMBED_MODEL"

    local base_from_lm=""
    if [[ -n "$LM_BASE_URL" ]]; then
        base_from_lm="$(derive_embedding_base "$LM_BASE_URL")"
    fi
    local default_base="${base_from_lm:-http://localhost:11434}"
    read -r -p "Embedding base URL [${default_base}]: " EMBED_BASE_URL
    EMBED_BASE_URL=${EMBED_BASE_URL:-$default_base}

    read -r -p "Embedding batch size (Enter for 32): " EMBED_BATCH_SIZE
    EMBED_BATCH_SIZE=${EMBED_BATCH_SIZE:-32}

    for env_path in "${ENV_FILES[@]}"; do
        update_env_var "$env_path" "LOCAL_EMBEDDING_BASE_URL" "$EMBED_BASE_URL"
        update_env_var "$env_path" "LOCAL_EMBEDDING_MODEL_NAME" "$EMBED_MODEL"
        update_env_var "$env_path" "EMBEDDING_DIMENSIONS" "$EMBED_DIMENSIONS"
        update_env_var "$env_path" "EMBEDDING_BATCH_SIZE" "$EMBED_BATCH_SIZE"
    done

    echo -e "${GREEN}Embedding configuration saved.${NC}"
    echo
}

require_curl() {
    if ! command -v curl >/dev/null 2>&1; then
        echo -e "${RED}curl is required but not installed.${NC}"
        echo -e "${YELLOW}Install with: brew install curl${NC}"
        exit 1
    fi
}

test_language_model() {
    require_curl

    local http_code
    local response_file
    response_file=$(mktemp)

    local payload
    payload=$(cat <<EOF
{
  "model": "${LM_MODEL}",
  "messages": [{"role": "user", "content": "Reply with the word ok."}],
  "max_tokens": 5
}
EOF
)

    local auth_header=()
    if [[ -n "$LM_API_KEY" && "$LM_API_KEY" != "no_key_needed" ]]; then
        auth_header=(-H "Authorization: Bearer ${LM_API_KEY}")
    fi

    http_code=$(curl -s -o "$response_file" -w "%{http_code}" -X POST \
        "${LM_BASE_URL}/chat/completions" \
        -H "Content-Type: application/json" \
        "${auth_header[@]}" \
        -d "$payload" || true)

    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}✅ Language model test succeeded.${NC}"
    else
        echo -e "${RED}❌ Language model test failed (HTTP $http_code).${NC}"
        echo "Response:"
        cat "$response_file"
    fi

    rm -f "$response_file"
}

test_embeddings() {
    require_curl

    local http_code
    local response_file
    response_file=$(mktemp)

    local base_url_trimmed
    base_url_trimmed="$(trim_trailing_slash "$EMBED_BASE_URL")"

    local payload
    payload=$(cat <<EOF
{
  "model": "${EMBED_MODEL}",
  "input": ["This is a quick Dana embedding test."]
}
EOF
)

    http_code=$(curl -s -o "$response_file" -w "%{http_code}" -X POST \
        "${base_url_trimmed}/api/embed" \
        -H "Content-Type: application/json" \
        -d "$payload" || true)

    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}✅ Embedding test succeeded.${NC}"
    else
        echo -e "${RED}❌ Embedding test failed (HTTP $http_code).${NC}"
        echo "Response:"
        cat "$response_file"
    fi

    rm -f "$response_file"
}

verify_ollama
require_command python3 "brew install python"
choose_env_targets
choose_usage_mode

if [[ "$CONFIGURE_LM" == true ]]; then
    configure_language_model
fi

if [[ "$CONFIGURE_EMBEDDINGS" == true ]]; then
    configure_embeddings
fi

echo -e "${BLUE}Running validation checks...${NC}"
if [[ "$CONFIGURE_LM" == true ]]; then
    test_language_model
fi
if [[ "$CONFIGURE_EMBEDDINGS" == true ]]; then
    test_embeddings
fi

echo -e "\n${GREEN}🎉 Dana + Ollama setup complete!${NC}"
echo -e "Updated environment file(s): ${ENV_FILES[*]}"
echo -e "You can now run ${YELLOW}dana-repl${NC} and call ${YELLOW}set_model(\"local\")${NC}."
