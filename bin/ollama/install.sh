#!/bin/bash
#
# install.sh: Installs Ollama for Dana on macOS and Linux
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
#
# Usage:
#   ./bin/ollama/install.sh
#
# The script performs the following actions:
# 1. Detects the operating system
# 2. Installs Ollama using the appropriate method for each OS
# 3. Verifies the installation
#

set -e
set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            echo "ubuntu"
        elif command -v yum &> /dev/null; then
            echo "rhel"
        else
            echo "linux"
        fi
    else
        echo "unknown"
    fi
}

OS_TYPE=$(detect_os)

case "$OS_TYPE" in
    "macos")
        echo -e "${BLUE}🚀 Starting Ollama Installation for Dana (macOS)...${NC}"
        ;;
    "ubuntu"|"linux")
        echo -e "${BLUE}🚀 Starting Ollama Installation for Dana (Linux)...${NC}"
        ;;
    "rhel")
        echo -e "${BLUE}🚀 Starting Ollama Installation for Dana (RHEL/CentOS)...${NC}"
        ;;
    *)
        echo -e "${RED}❌ Error: Unsupported operating system: $OSTYPE${NC}"
        echo -e "${YELLOW}💡 Supported systems: macOS, Ubuntu/Debian, RHEL/CentOS${NC}"
        exit 1
        ;;
esac

# OS-specific installation
install_ollama() {
    case "$OS_TYPE" in
        "macos")
            # --- Check for Homebrew ---
            if ! command -v brew &> /dev/null; then
                echo -e "${RED}❌ Error: Homebrew is not installed.${NC}"
                echo -e "${YELLOW}Please install Homebrew first by following the instructions at https://brew.sh/${NC}"
                exit 1
            fi
            
            echo -e "${GREEN}✅ Homebrew is installed.${NC}"
            
            # --- Install Ollama ---
            echo -e "${BLUE}📦 Installing Ollama via Homebrew...${NC}"
            if brew list ollama &>/dev/null; then
                echo -e "${YELLOW}Ollama is already installed. If you face issues, consider running 'brew reinstall ollama'.${NC}"
            else
                if ! brew install ollama; then
                    echo -e "${RED}❌ Ollama installation failed.${NC}"
                    exit 1
                fi
                echo -e "${GREEN}✅ Ollama installed successfully.${NC}"
            fi
            ;;
        "ubuntu"|"linux")
            # Check if Ollama is already installed
            if command -v ollama &> /dev/null; then
                echo -e "${YELLOW}Ollama is already installed.${NC}"
                OLLAMA_VERSION=$(ollama --version)
                echo -e "${GREEN}Current version: ${OLLAMA_VERSION}${NC}"
                return 0
            fi
            
            # Check for curl
            if ! command -v curl &> /dev/null; then
                echo -e "${YELLOW}📦 Installing curl...${NC}"
                sudo apt-get update && sudo apt-get install -y curl
            fi
            
            echo -e "${BLUE}📦 Installing Ollama for Linux...${NC}"
            echo -e "${YELLOW}Using official Ollama installation script...${NC}"
            
            # Download and run the official Ollama installation script
            if curl -fsSL https://ollama.com/install.sh | sh; then
                echo -e "${GREEN}✅ Ollama installed successfully.${NC}"
            else
                echo -e "${RED}❌ Ollama installation failed.${NC}"
                echo -e "${YELLOW}💡 You can try manual installation:${NC}"
                echo -e "${YELLOW}   curl -fsSL https://ollama.com/install.sh | sh${NC}"
                exit 1
            fi
            ;;
        "rhel")
            # Check if Ollama is already installed
            if command -v ollama &> /dev/null; then
                echo -e "${YELLOW}Ollama is already installed.${NC}"
                OLLAMA_VERSION=$(ollama --version)
                echo -e "${GREEN}Current version: ${OLLAMA_VERSION}${NC}"
                return 0
            fi
            
            # Check for curl
            if ! command -v curl &> /dev/null; then
                echo -e "${YELLOW}📦 Installing curl...${NC}"
                sudo yum install -y curl
            fi
            
            echo -e "${BLUE}📦 Installing Ollama for RHEL/CentOS...${NC}"
            echo -e "${YELLOW}Using official Ollama installation script...${NC}"
            
            # Download and run the official Ollama installation script
            if curl -fsSL https://ollama.com/install.sh | sh; then
                echo -e "${GREEN}✅ Ollama installed successfully.${NC}"
            else
                echo -e "${RED}❌ Ollama installation failed.${NC}"
                echo -e "${YELLOW}💡 You can try manual installation:${NC}"
                echo -e "${YELLOW}   curl -fsSL https://ollama.com/install.sh | sh${NC}"
                exit 1
            fi
            ;;
    esac
}

install_ollama

# --- Verify Installation ---
echo -e "${BLUE}🔍 Verifying Ollama installation...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Verification failed. 'ollama' command not found in PATH.${NC}"
    exit 1
fi

OLLAMA_VERSION=$(ollama --version)
echo -e "${GREEN}✅ Verification successful. ${OLLAMA_VERSION} is ready for Dana.${NC}"

# --- OS-specific post-installation instructions ---
show_post_installation_instructions() {
    echo -e "\n${BLUE}🎉 Ollama setup for Dana is complete!${NC}"
    
    case "$OS_TYPE" in
        "macos")
            echo -e "Ollama will now run as a background service."
            echo -e "You can start using it with the following commands:"
            echo -e "  - To start the server and run a model: ${YELLOW}ollama run phi3${NC}"
            echo -e "  - To see a list of downloaded models: ${YELLOW}ollama list${NC}"
            echo -e "  - To use the custom start script: ${YELLOW}./bin/ollama/start.sh${NC}"
            ;;
        "ubuntu"|"linux"|"rhel")
            echo -e "Ollama has been installed and can run as a systemd service."
            echo -e "\n${BLUE}💡 Service Management:${NC}"
            echo -e "  - To start the service: ${YELLOW}sudo systemctl start ollama${NC}"
            echo -e "  - To enable auto-start: ${YELLOW}sudo systemctl enable ollama${NC}"
            echo -e "  - To check service status: ${YELLOW}sudo systemctl status ollama${NC}"
            echo -e "\n${BLUE}🚀 Usage Commands:${NC}"
            echo -e "  - To run a model: ${YELLOW}ollama run phi3${NC}"
            echo -e "  - To see downloaded models: ${YELLOW}ollama list${NC}"
            echo -e "  - To use the custom start script: ${YELLOW}./bin/ollama/start.sh${NC}"
            echo -e "\n${BLUE}🔧 Optional: Start service now${NC}"
            echo -e "  ${YELLOW}sudo systemctl start ollama${NC}"
            echo -e "  ${YELLOW}sudo systemctl enable ollama${NC}"
            ;;
    esac
    
    echo -e "\n${GREEN}✨ Happy modeling with Ollama and Dana!${NC}"
}

show_post_installation_instructions

exit 0 