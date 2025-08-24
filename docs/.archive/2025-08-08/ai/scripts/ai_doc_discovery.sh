#!/bin/bash

# AI Documentation Discovery Script
# Analyzes recent changes and identifies documentation needs

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs/.ai-only"
OUTPUT_DIR="${DOCS_DIR}/ai_output"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${OUTPUT_DIR}/discovery_phase.log"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${OUTPUT_DIR}/discovery_phase.log"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${OUTPUT_DIR}/discovery_phase.log"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "${OUTPUT_DIR}/discovery_phase.log"; }

echo "=== AI DOCUMENTATION DISCOVERY STARTED $(date) ==="

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Initialize discovery log
echo "=== AI DOCUMENTATION DISCOVERY STARTED $(date) ===" > "${OUTPUT_DIR}/discovery_phase.log"

# 1. Analyze recent changes (last 30 days)
log_info "Analyzing recent changes..."
if [ -d ".git" ]; then
    git log --since="30 days ago" --name-only --pretty=format: | grep -E '\.(py|md|na)$' | sort -u > "${OUTPUT_DIR}/recent_changes.txt"
    recent_changes_count=$(wc -l < "${OUTPUT_DIR}/recent_changes.txt")
    log_success "Recent changes found: ${recent_changes_count}"
else
    log_warning "Not a git repository, skipping recent changes analysis"
    echo "No git repository found" > "${OUTPUT_DIR}/recent_changes.txt"
fi

# 2. Identify new/modified functions with better path handling
log_info "Identifying new/modified functions..."
new_functions_count=0
> "${OUTPUT_DIR}/new_functions.txt"

# Check if dana directory exists
if [ -d "${PROJECT_ROOT}/dana" ]; then
    # Use a more reliable timestamp reference
    timestamp_file="${OUTPUT_DIR}/discovery_timestamp"
    touch "${timestamp_file}"
    
    # Find Python files in dana directory
    if find "${PROJECT_ROOT}/dana" -name "*.py" -newer "${timestamp_file}" >/dev/null 2>&1; then
        find "${PROJECT_ROOT}/dana" -name "*.py" -newer "${timestamp_file}" -exec echo "Modified: {}" \; > "${OUTPUT_DIR}/new_functions.txt"
        new_functions_count=$(wc -l < "${OUTPUT_DIR}/new_functions.txt")
        log_success "New functions found: ${new_functions_count}"
    else
        log_info "No new Python files found in dana directory"
    fi
else
    log_warning "dana/ directory not found"
fi

# 3. Check for new examples with better path handling
log_info "Checking for new examples..."
new_examples_count=0
> "${OUTPUT_DIR}/new_examples.txt"

# Check multiple possible example directories
example_dirs=("${PROJECT_ROOT}/examples" "${PROJECT_ROOT}/demos" "${PROJECT_ROOT}/docs/examples")
for example_dir in "${example_dirs[@]}"; do
    if [ -d "${example_dir}" ]; then
        if find "${example_dir}" -name "*.na" -newer "${timestamp_file}" >/dev/null 2>&1; then
            find "${example_dir}" -name "*.na" -newer "${timestamp_file}" >> "${OUTPUT_DIR}/new_examples.txt"
        fi
    fi
done

new_examples_count=$(wc -l < "${OUTPUT_DIR}/new_examples.txt")
log_success "New examples found: ${new_examples_count}"

# 4. Test MkDocs build with better error handling
log_info "Testing MkDocs build..."
if [ -f "${PROJECT_ROOT}/Makefile" ]; then
    if make -C "${PROJECT_ROOT}" docs-build > "${OUTPUT_DIR}/mkdocs_build.log" 2>&1; then
        log_success "MkDocs builds successfully"
        echo "SUCCESS" > "${OUTPUT_DIR}/build_status.txt"
    else
        log_error "MkDocs build failed - check mkdocs_build.log"
        echo "FAILED" > "${OUTPUT_DIR}/build_status.txt"
        # Don't exit here, continue with other checks
    fi
else
    log_warning "Makefile not found, skipping MkDocs build test"
    echo "NO_MAKEFILE" > "${OUTPUT_DIR}/build_status.txt"
fi

# 5. Count documentation files with better error handling
log_info "Counting documentation files..."
doc_files_count=0
dana_examples_count=0

if [ -d "${PROJECT_ROOT}/docs" ]; then
    doc_files_count=$(find "${PROJECT_ROOT}/docs" -name "*.md" 2>/dev/null | wc -l)
    dana_examples_count=$(grep -r '```dana' "${PROJECT_ROOT}/docs" 2>/dev/null | wc -l)
else
    log_warning "docs/ directory not found"
fi

echo "Documentation files: ${doc_files_count}" > "${OUTPUT_DIR}/doc_stats.txt"
echo "Dana examples: ${dana_examples_count}" >> "${OUTPUT_DIR}/doc_stats.txt"

log_success "Documentation files: ${doc_files_count}"
log_success "Dana examples: ${dana_examples_count}"

# 6. Check for documentation gaps
log_info "Checking for documentation gaps..."
> "${OUTPUT_DIR}/doc_gaps.txt"

    # Check for Python files without corresponding documentation
    if [ -d "${PROJECT_ROOT}/dana" ]; then
        find "${PROJECT_ROOT}/dana" -name "*.py" | while read -r py_file; do
            module_name=$(basename "${py_file}" .py)
            if ! find "${PROJECT_ROOT}/docs" -name "*.md" -exec grep -l "${module_name}" {} \; >/dev/null 2>&1; then
                echo "Missing docs for: ${py_file}" >> "${OUTPUT_DIR}/doc_gaps.txt"
            fi
        done
    fi

gaps_count=$(wc -l < "${OUTPUT_DIR}/doc_gaps.txt")
log_info "Documentation gaps found: ${gaps_count}"

# 7. Generate comprehensive discovery summary
log_info "Generating discovery summary..."
cat > "${OUTPUT_DIR}/discovery_summary.txt" << EOF
=== AI DOCUMENTATION DISCOVERY SUMMARY ===
Date: $(date)
Project: $(basename "${PROJECT_ROOT}")

STATISTICS:
- Recent changes: ${recent_changes_count}
- New functions: ${new_functions_count}
- New examples: ${new_examples_count}
- Documentation files: ${doc_files_count}
- Dana examples: ${dana_examples_count}
- Documentation gaps: ${gaps_count}

BUILD STATUS:
- MkDocs build: $(cat "${OUTPUT_DIR}/build_status.txt")

FILES ANALYZED:
- Recent changes: ${OUTPUT_DIR}/recent_changes.txt
- New functions: ${OUTPUT_DIR}/new_functions.txt
- New examples: ${OUTPUT_DIR}/new_examples.txt
- Documentation gaps: ${OUTPUT_DIR}/doc_gaps.txt
- Build log: ${OUTPUT_DIR}/mkdocs_build.log

RECOMMENDATIONS:
$(if [ "$new_functions_count" -gt 0 ]; then
    echo "- Update function documentation for ${new_functions_count} new/modified functions"
fi)
$(if [ "$new_examples_count" -gt 0 ]; then
    echo "- Review ${new_examples_count} new examples for documentation"
fi)
$(if [ "$gaps_count" -gt 0 ]; then
    echo "- Address ${gaps_count} documentation gaps"
fi)
$(if [ "$(cat "${OUTPUT_DIR}/build_status.txt")" != "SUCCESS" ]; then
    echo "- Fix MkDocs build issues"
fi)
EOF

log_success "Discovery summary generated: ${OUTPUT_DIR}/discovery_summary.txt"
echo "SUCCESS: Discovery phase completed successfully" >> "${OUTPUT_DIR}/discovery_phase.log"

echo "=== AI DOCUMENTATION DISCOVERY COMPLETE $(date) ===" 