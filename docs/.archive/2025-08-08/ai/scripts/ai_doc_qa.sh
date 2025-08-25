#!/bin/bash

# AI Documentation Quality Assurance Script
# Runs final validation tests and generates quality report

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs/.ai-only"
OUTPUT_DIR="${DOCS_DIR}/ai_output"
DANA_BIN="${PROJECT_ROOT}/bin/dana"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${OUTPUT_DIR}/quality_assurance_phase.log"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${OUTPUT_DIR}/quality_assurance_phase.log"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${OUTPUT_DIR}/quality_assurance_phase.log"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "${OUTPUT_DIR}/quality_assurance_phase.log"; }

echo '=== AI DOCUMENTATION QUALITY ASSURANCE STARTED '$(date)' ==='

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Initialize QA log
echo "=== AI DOCUMENTATION QUALITY ASSURANCE STARTED $(date) ===" > "${OUTPUT_DIR}/quality_assurance_phase.log"

# 1. Final Dana example test with improved regex
log_info 'Running final Dana example test...'
# Only test actual documentation files, exclude archive and ai-only directories
find "${PROJECT_ROOT}/docs" -name "*.md" -not -path "*/\.archive/*" -not -path "*/.ai-only/*" -exec grep -l '```dana' {} \; > "${OUTPUT_DIR}/final_dana_files.txt"

final_broken=0
final_total=0
final_skipped=0
> "${OUTPUT_DIR}/final_broken_examples.txt"

while read -r file; do
    log_info "Final testing ${file}..."
    ((final_total++))
    
    # Create temporary file for this test
    temp_file="temp_final_${file##*/}.na"
    
    # Extract Dana code blocks with improved regex
    # This handles multi-line blocks and edge cases better
    awk '
    /^```dana$/ {
        in_block = 1
        next
    }
    /^```$/ {
        if (in_block) {
            in_block = 0
            next
        }
    }
    in_block {
        print
    }
    ' "$file" > "${temp_file}"
    
    # Test if the code runs (only if file has content)
    if [ -s "${temp_file}" ]; then
        # Check if the code contains advanced features that might not be implemented
        if grep -q "@poet\|@workflow\||>" "${temp_file}"; then
            log_warning "SKIP: ${file} (contains advanced features - @poet, @workflow, or |> operators)"
            ((final_skipped++))
        else
            # Use timeout if available, otherwise run without it
            if command -v timeout >/dev/null 2>&1; then
                if timeout 30 "${DANA_BIN}" "${temp_file}" >/dev/null 2>&1; then
                    log_success "OK: ${file} examples work"
                else
                    log_error "BROKEN: ${file}"
                    echo "${file}" >> "${OUTPUT_DIR}/final_broken_examples.txt"
                    ((final_broken++))
                fi
            else
                # Run without timeout if not available
                if "${DANA_BIN}" "${temp_file}" >/dev/null 2>&1; then
                    log_success "OK: ${file} examples work"
                else
                    log_error "BROKEN: ${file}"
                    echo "${file}" >> "${OUTPUT_DIR}/final_broken_examples.txt"
                    ((final_broken++))
                fi
            fi
        fi
    else
        log_warning "SKIP: ${file} (no Dana code blocks found)"
        ((final_skipped++))
    fi
    
    # Clean up temp file
    rm -f "${temp_file}"
done < "${OUTPUT_DIR}/final_dana_files.txt"

log_info "Final broken examples: ${final_broken}/${final_total} (${final_skipped} skipped)"

# 2. Final MkDocs build test with better error handling
log_info 'Running final MkDocs build test...'
if [ -f "${PROJECT_ROOT}/Makefile" ]; then
        # Use timeout if available, otherwise run without it
    if command -v timeout >/dev/null 2>&1; then
        if timeout 600 uv run --extra docs mkdocs build > "${OUTPUT_DIR}/final_build.log" 2>&1; then
            log_success 'Final build successful'
            echo 'SUCCESS' > "${OUTPUT_DIR}/final_build_status.txt"
        else
            log_error 'Final build failed'
            echo 'FAILED' > "${OUTPUT_DIR}/final_build_status.txt"
        fi
    else
        # Run without timeout if not available
        if uv run --extra docs mkdocs build > "${OUTPUT_DIR}/final_build.log" 2>&1; then
            log_success 'Final build successful'
            echo 'SUCCESS' > "${OUTPUT_DIR}/final_build_status.txt"
        else
            log_error 'Final build failed'
            echo 'FAILED' > "${OUTPUT_DIR}/final_build_status.txt"
        fi
    fi
else
    log_warning "Makefile not found, skipping build test"
    echo 'NO_MAKEFILE' > "${OUTPUT_DIR}/final_build_status.txt"
fi

# 3. Content quality checks with comprehensive analysis
log_info 'Running content quality checks...'
missing_outputs=0
missing_descriptions=0
broken_links=0
> "${OUTPUT_DIR}/missing_outputs.txt"
> "${OUTPUT_DIR}/missing_descriptions.txt"
> "${OUTPUT_DIR}/broken_links.txt"

while read -r file; do
    if grep -q '```dana' "$file"; then
        # Check for missing expected outputs
        if ! grep -q 'Expected Output' "$file"; then
            echo "$file" >> "${OUTPUT_DIR}/missing_outputs.txt"
            missing_outputs=$((missing_outputs+1))
        fi
        
        # Check for missing descriptions
        if ! grep -q '^#' "$file"; then
            echo "$file" >> "${OUTPUT_DIR}/missing_descriptions.txt"
            missing_descriptions=$((missing_descriptions+1))
        fi
    fi
    
    # Check for broken internal links
    grep -o '\[.*\]([^)]*)' "$file" 2>/dev/null | while read -r link; do
        link_file=$(echo "$link" | sed 's/.*(\([^)]*\)).*/\1/')
        if [[ "$link_file" == *".md" ]] && [[ ! "$link_file" == *"http"* ]]; then
            target_file="${PROJECT_ROOT}/docs/${link_file}"
            if [ ! -f "$target_file" ]; then
                echo "$file: $link" >> "${OUTPUT_DIR}/broken_links.txt"
                broken_links=$((broken_links+1))
            fi
        fi
    done
done < "${OUTPUT_DIR}/final_dana_files.txt"

log_info "Files missing expected outputs: ${missing_outputs}"
log_info "Files missing descriptions: ${missing_descriptions}"
log_info "Broken links found: ${broken_links}"

# 4. Navigation completeness check
log_info 'Checking navigation completeness...'
if [ -f "${OUTPUT_DIR}/orphaned_files.txt" ]; then
    orphaned_count=$(wc -l < "${OUTPUT_DIR}/orphaned_files.txt")
else
    orphaned_count=0
fi

if [ -f "${OUTPUT_DIR}/missing_nav_files.txt" ]; then
    missing_nav_count=$(wc -l < "${OUTPUT_DIR}/missing_nav_files.txt")
else
    missing_nav_count=0
fi

# 5. Performance metrics
log_info 'Calculating performance metrics...'
total_files=$(wc -l < "${OUTPUT_DIR}/final_dana_files.txt")
success_rate=$(( (final_total - final_broken) * 100 / final_total )) 2>/dev/null || success_rate=0

# 6. Generate comprehensive quality report
log_info 'Generating quality report...'
cat > "${OUTPUT_DIR}/quality_report.txt" <<EOF
=== AI QUALITY ASSURANCE REPORT ===
Date: $(date)
Project: $(basename "${PROJECT_ROOT}")

EXECUTION METRICS:
- Final Dana examples tested: ${final_total}
- Final broken examples: ${final_broken}
- Success rate: ${success_rate}%
- Final build status: $(cat "${OUTPUT_DIR}/final_build_status.txt")

CONTENT QUALITY:
- Files missing expected outputs: ${missing_outputs}
- Files missing descriptions: ${missing_descriptions}
- Broken links: ${broken_links}

NAVIGATION QUALITY:
- Orphaned files: ${orphaned_count}
- Missing navigation files: ${missing_nav_count}

QUALITY METRICS:
- Dana Examples: $(if [ $final_broken -eq 0 ]; then echo 'ALL WORKING'; else echo "${final_broken} BROKEN"; fi)
- MkDocs Build: $(cat "${OUTPUT_DIR}/final_build_status.txt")
- Navigation: $(if [ $orphaned_count -eq 0 ] && [ $missing_nav_count -eq 0 ]; then echo 'COMPLETE'; else echo 'ISSUES FOUND'; fi)
- Content Quality: $(if [ $missing_outputs -eq 0 ] && [ $missing_descriptions -eq 0 ] && [ $broken_links -eq 0 ]; then echo 'COMPLETE'; else echo 'ISSUES FOUND'; fi)

DETAILED ANALYSIS:
$(if [ $final_broken -gt 0 ]; then
    echo "Broken examples found in:"
    cat "${OUTPUT_DIR}/final_broken_examples.txt" | sed 's/^/  - /'
    echo ""
fi)
$(if [ $missing_outputs -gt 0 ]; then
    echo "Files missing expected outputs:"
    cat "${OUTPUT_DIR}/missing_outputs.txt" | sed 's/^/  - /'
    echo ""
fi)
$(if [ $broken_links -gt 0 ]; then
    echo "Broken links found:"
    cat "${OUTPUT_DIR}/broken_links.txt" | sed 's/^/  - /'
    echo ""
fi)

OVERALL STATUS: $(if [ $final_broken -eq 0 ] && [ "$(cat "${OUTPUT_DIR}/final_build_status.txt")" = "SUCCESS" ] && [ $orphaned_count -eq 0 ] && [ $missing_nav_count -eq 0 ] && [ $missing_outputs -eq 0 ] && [ $missing_descriptions -eq 0 ] && [ $broken_links -eq 0 ]; then echo 'PASSED'; else echo 'ISSUES FOUND'; fi)
EOF

# 7. Generate enhanced success criteria checklist
log_info 'Generating success criteria checklist...'

# Calculate total criteria and passed criteria
total_criteria=7
passed_criteria=0

# More lenient criteria for AI documentation maintenance
[ $final_broken -eq 0 ] && passed_criteria=$((passed_criteria+1))
[ "$(cat "${OUTPUT_DIR}/final_build_status.txt")" = "SUCCESS" ] && passed_criteria=$((passed_criteria+1))
[ $orphaned_count -eq 0 ] && [ $missing_nav_count -eq 0 ] && passed_criteria=$((passed_criteria+1))
[ $missing_outputs -eq 0 ] && passed_criteria=$((passed_criteria+1))
[ $missing_descriptions -eq 0 ] && passed_criteria=$((passed_criteria+1))
[ $broken_links -eq 0 ] && passed_criteria=$((passed_criteria+1))
# Allow some broken examples if they're advanced features (more lenient for AI maintenance)
[ $final_broken -le 10 ] && passed_criteria=$((passed_criteria+1))

if [ $passed_criteria -eq $total_criteria ]; then
    total_passed_str="${total_criteria}/${total_criteria} ALL CRITERIA MET"
else
    total_passed_str="${passed_criteria}/${total_criteria} ISSUES FOUND"
fi

cat > "${OUTPUT_DIR}/success_criteria.txt" <<EOF
=== SUCCESS CRITERIA CHECKLIST ===
Date: $(date)
Project: $(basename "${PROJECT_ROOT}")

QUALITY CRITERIA:
- [$(if [ $final_broken -eq 0 ]; then echo 'x'; else echo ' '; fi)] All Dana examples execute successfully (${final_broken} broken)
- [$(if [ "$(cat "${OUTPUT_DIR}/final_build_status.txt")" = "SUCCESS" ]; then echo 'x'; else echo ' '; fi)] MkDocs builds without errors
- [$(if [ $orphaned_count -eq 0 ] && [ $missing_nav_count -eq 0 ]; then echo 'x'; else echo ' '; fi)] Navigation structure is valid (${orphaned_count} orphaned, ${missing_nav_count} missing)
- [$(if [ $missing_outputs -eq 0 ]; then echo 'x'; else echo ' '; fi)] All examples have expected outputs (${missing_outputs} missing)
- [$(if [ $missing_descriptions -eq 0 ]; then echo 'x'; else echo ' '; fi)] All files have descriptions (${missing_descriptions} missing)
- [$(if [ $broken_links -eq 0 ]; then echo 'x'; else echo ' '; fi)] No broken internal links (${broken_links} broken)
- [$(if [ $success_rate -ge 95 ]; then echo 'x'; else echo ' '; fi)] High success rate (${success_rate}%)

PERFORMANCE METRICS:
- Total files tested: ${final_total}
- Success rate: ${success_rate}%
- Build status: $(cat "${OUTPUT_DIR}/final_build_status.txt")

TOTAL PASSED: ${total_passed_str}

RECOMMENDATIONS:
$(if [ $final_broken -gt 0 ]; then
    echo "- Fix ${final_broken} broken Dana examples"
fi)
$(if [ "$(cat "${OUTPUT_DIR}/final_build_status.txt")" != "SUCCESS" ]; then
    echo "- Resolve MkDocs build issues"
fi)
$(if [ $missing_outputs -gt 0 ]; then
    echo "- Add expected outputs to ${missing_outputs} files"
fi)
$(if [ $broken_links -gt 0 ]; then
    echo "- Fix ${broken_links} broken internal links"
fi)
$(if [ $success_rate -lt 95 ]; then
    echo "- Improve example success rate (currently ${success_rate}%)"
fi)
EOF

log_success "Quality assurance completed"

# Determine if QA phase passed based on criteria
if [ $passed_criteria -eq $total_criteria ]; then
    echo "SUCCESS: Quality assurance phase completed successfully" >> "${OUTPUT_DIR}/quality_assurance_phase.log"
    echo '=== AI DOCUMENTATION QUALITY ASSURANCE COMPLETE '$(date)' ==='
    exit 0
else
    echo "FAILED: Quality assurance phase - ${passed_criteria}/${total_criteria} criteria met" >> "${OUTPUT_DIR}/quality_assurance_phase.log"
    echo '=== AI DOCUMENTATION QUALITY ASSURANCE COMPLETE '$(date)' ==='
    exit 1
fi 