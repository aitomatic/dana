#!/bin/bash

# AI Documentation Automation Configuration
# Centralized configuration for all AI documentation scripts

# Script and project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs/.ai-only"
OUTPUT_DIR="${DOCS_DIR}/ai_output"

# Essential binaries and files
DANA_BIN="${PROJECT_ROOT}/bin/dana"
MKDOCS_CONFIG="${PROJECT_ROOT}/mkdocs.yml"
MAKEFILE="${PROJECT_ROOT}/Makefile"

# Timeout settings (in seconds)
DISCOVERY_TIMEOUT=1800      # 30 minutes
CONTENT_UPDATE_TIMEOUT=1800 # 30 minutes
STRUCTURE_VALIDATE_TIMEOUT=900  # 15 minutes
QA_TIMEOUT=1800            # 30 minutes
DANA_EXAMPLE_TIMEOUT=30    # 30 seconds per example
BUILD_TIMEOUT=600          # 10 minutes for builds

# Quality thresholds
MIN_SUCCESS_RATE=95        # Minimum success rate percentage
MAX_BROKEN_EXAMPLES=0      # Maximum allowed broken examples
MAX_MISSING_OUTPUTS=0      # Maximum allowed missing outputs
MAX_BROKEN_LINKS=0         # Maximum allowed broken links

# File patterns
PYTHON_FILES="*.py"
MARKDOWN_FILES="*.md"
DANA_FILES="*.na"
DOCUMENTATION_FILES="*.md"

# Directories to scan
EXAMPLE_DIRS=("${PROJECT_ROOT}/examples" "${PROJECT_ROOT}/demos" "${PROJECT_ROOT}/docs/examples")
SOURCE_DIRS=("${PROJECT_ROOT}/dana" "${PROJECT_ROOT}/examples" "${PROJECT_ROOT}/demos")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${OUTPUT_DIR}/ai_doc_master.log"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${OUTPUT_DIR}/ai_doc_master.log"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${OUTPUT_DIR}/ai_doc_master.log"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "${OUTPUT_DIR}/ai_doc_master.log"; }
log_debug() { echo -e "${PURPLE}[DEBUG]${NC} $1" | tee -a "${OUTPUT_DIR}/ai_doc_master.log"; }

# Validation functions
validate_paths() {
    local missing_items=()
    
    # Check essential files and directories
    [ -f "${MKDOCS_CONFIG}" ] || missing_items+=("mkdocs.yml")
    [ -f "${MAKEFILE}" ] || missing_items+=("Makefile")
    [ -d "${PROJECT_ROOT}/dana" ] || missing_items+=("dana/ directory")
    [ -d "${PROJECT_ROOT}/docs" ] || missing_items+=("docs/ directory")
    
    # Check Dana runtime
    if [ ! -x "${DANA_BIN}" ]; then
        missing_items+=("Dana runtime (${DANA_BIN})")
    fi
    
    # Check required commands
    command -v git >/dev/null 2>&1 || missing_items+=("git")
    command -v make >/dev/null 2>&1 || missing_items+=("make")
    command -v find >/dev/null 2>&1 || missing_items+=("find")
    command -v grep >/dev/null 2>&1 || missing_items+=("grep")
    command -v awk >/dev/null 2>&1 || missing_items+=("awk")
    # timeout is optional - we'll handle it gracefully if not available
    
    if [ ${#missing_items[@]} -gt 0 ]; then
        log_error "Missing prerequisites:"
        printf '%s\n' "${missing_items[@]}" | sed 's/^/  - /'
        return 1
    fi
    
    return 0
}

# Utility functions
create_output_dir() {
    mkdir -p "${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}/backup"
    mkdir -p "${OUTPUT_DIR}/logs"
}

cleanup_temp_files() {
    find /tmp -name "temp_*_*.na" -delete 2>/dev/null || true
}

# Export configuration for use in other scripts
export SCRIPT_DIR PROJECT_ROOT DOCS_DIR OUTPUT_DIR
export DANA_BIN MKDOCS_CONFIG MAKEFILE
export DISCOVERY_TIMEOUT CONTENT_UPDATE_TIMEOUT STRUCTURE_VALIDATE_TIMEOUT QA_TIMEOUT
export DANA_EXAMPLE_TIMEOUT BUILD_TIMEOUT
export MIN_SUCCESS_RATE MAX_BROKEN_EXAMPLES MAX_MISSING_OUTPUTS MAX_BROKEN_LINKS
export RED GREEN YELLOW BLUE PURPLE CYAN NC 