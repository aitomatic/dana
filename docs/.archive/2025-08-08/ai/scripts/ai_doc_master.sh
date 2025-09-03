#!/bin/bash

# AI Documentation Master Automation Script
# Orchestrates complete documentation update process with robust error handling

set -euo pipefail  # Strict error handling

# Load configuration
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

# Pre-flight checks
check_prerequisites() {
    log_info "Running pre-flight checks..."
    
    if ! validate_paths; then
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Create output directory and initialize logging
initialize_environment() {
    log_info "Initializing environment..."
    
    # Create output directories
    create_output_dir
    
    # Start master log
    echo "=== AI DOCUMENTATION MASTER AUTOMATION $(date) ===" > "${OUTPUT_DIR}/ai_doc_master.log"
    echo "Project root: ${PROJECT_ROOT}" >> "${OUTPUT_DIR}/ai_doc_master.log"
    echo "Script directory: ${SCRIPT_DIR}" >> "${OUTPUT_DIR}/ai_doc_master.log"
    echo "Output directory: ${OUTPUT_DIR}" >> "${OUTPUT_DIR}/ai_doc_master.log"
    
    # Clean up any existing temp files
    cleanup_temp_files
    
    log_success "Environment initialized"
}

# Phase execution with error recovery
run_phase() {
    local phase_name="$1"
    local phase_script="$2"
    local phase_number="$3"
    local total_phases="$4"
    
    log_info "Progress: [${phase_number}/${total_phases}] ${phase_name} phase..."
    echo "Phase ${phase_number}: ${phase_name}" >> "${OUTPUT_DIR}/ai_doc_master.log"
    
    # Create phase-specific log (convert to lowercase safely)
    local phase_log="${OUTPUT_DIR}/$(echo "${phase_name}" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')_phase.log"
    echo "=== ${phase_name} PHASE STARTED $(date) ===" > "${phase_log}"
    
    # Run phase with optional timeout and detailed logging
    local timeout_value="${DISCOVERY_TIMEOUT}"
    case "${phase_script}" in
        *discovery*) timeout_value="${DISCOVERY_TIMEOUT}" ;;
        *content*) timeout_value="${CONTENT_UPDATE_TIMEOUT}" ;;
        *structure*) timeout_value="${STRUCTURE_VALIDATE_TIMEOUT}" ;;
        *qa*) timeout_value="${QA_TIMEOUT}" ;;
    esac
    
    # Use timeout if available, otherwise run without it
    if command -v timeout >/dev/null 2>&1; then
                if timeout "${timeout_value}" bash "${SCRIPT_DIR}/${phase_script}" >> "${phase_log}" 2>&1; then
            log_success "${phase_name} phase completed"
            echo "Phase ${phase_number}: ${phase_name} - SUCCESS" >> "${OUTPUT_DIR}/ai_doc_master.log"
            return 0
        else
            local exit_code=$?
            log_error "${phase_name} phase failed (exit code: ${exit_code})"
            echo "Phase ${phase_number}: ${phase_name} - FAILED (exit code: ${exit_code})" >> "${OUTPUT_DIR}/ai_doc_master.log"
            
            # Show last 10 lines of phase log for debugging
            log_error "Last 10 lines of ${phase_name} phase log:"
            tail -10 "${phase_log}" | sed 's/^/  /'
            
            return 1
        fi
    else
        # Run without timeout if not available
        if bash "${SCRIPT_DIR}/${phase_script}" >> "${phase_log}" 2>&1; then
            log_success "${phase_name} phase completed"
            echo "Phase ${phase_number}: ${phase_name} - SUCCESS" >> "${OUTPUT_DIR}/ai_doc_master.log"
            return 0
        else
            local exit_code=$?
            log_error "${phase_name} phase failed (exit code: ${exit_code})"
            echo "Phase ${phase_number}: ${phase_name} - FAILED (exit code: ${exit_code})" >> "${OUTPUT_DIR}/ai_doc_master.log"
            
            # Show last 10 lines of phase log for debugging
            log_error "Last 10 lines of ${phase_name} phase log:"
            tail -10 "${phase_log}" | sed 's/^/  /'
            
            return 1
        fi
    fi
}

# Generate comprehensive summary
generate_summary() {
    log_info "Generating master summary..."
    
    # Collect statistics
    discovery_status="$(grep -c "SUCCESS" "${OUTPUT_DIR}/discovery_phase.log" 2>/dev/null || echo "0")"
    content_status="$(grep -c "SUCCESS" "${OUTPUT_DIR}/content_update_phase.log" 2>/dev/null || echo "0")"
    structure_status="$(grep -c "SUCCESS" "${OUTPUT_DIR}/structure_validation_phase.log" 2>/dev/null || echo "0")"
    qa_status="$(grep -c "SUCCESS" "${OUTPUT_DIR}/quality_assurance_phase.log" 2>/dev/null || echo "0")"
    
    # Ensure variables are numeric
    discovery_status="${discovery_status:-0}"
    content_status="${content_status:-0}"
    structure_status="${structure_status:-0}"
    qa_status="${qa_status:-0}"
    
    # Determine overall status
    overall_status="PASSED"
    if [ "$discovery_status" -eq 0 ] || [ "$content_status" -eq 0 ] || [ "$structure_status" -eq 0 ] || [ "$qa_status" -eq 0 ]; then
        overall_status="FAILED"
    fi
    
    cat > "${OUTPUT_DIR}/master_summary.txt" << EOF
=== AI DOCUMENTATION MASTER AUTOMATION SUMMARY ===
Date: $(date)
Project: $(basename "${PROJECT_ROOT}")
Status: ${overall_status}

PHASE RESULTS:
- Discovery & Analysis: $(if [ "$discovery_status" -gt 0 ]; then echo "✅ COMPLETED"; else echo "❌ FAILED"; fi)
- Content Updates: $(if [ "$content_status" -gt 0 ]; then echo "✅ COMPLETED"; else echo "❌ FAILED"; fi)
- Structure Validation: $(if [ "$structure_status" -gt 0 ]; then echo "✅ COMPLETED"; else echo "❌ FAILED"; fi)
- Quality Assurance: $(if [ "$qa_status" -gt 0 ]; then echo "✅ COMPLETED"; else echo "❌ FAILED"; fi)

OUTPUT FILES:
- Master log: ${OUTPUT_DIR}/ai_doc_master.log
- Discovery summary: ${OUTPUT_DIR}/discovery_summary.txt
- Content update summary: ${OUTPUT_DIR}/content_update_summary.txt
- Structure validation summary: ${OUTPUT_DIR}/structure_validation_summary.txt
- Quality report: ${OUTPUT_DIR}/quality_report.txt
- Success criteria: ${OUTPUT_DIR}/success_criteria.txt

PHASE LOGS:
- Discovery: ${OUTPUT_DIR}/discovery_phase.log
- Content Update: ${OUTPUT_DIR}/content_update_phase.log
- Structure Validation: ${OUTPUT_DIR}/structure_validation_phase.log
- Quality Assurance: ${OUTPUT_DIR}/quality_assurance_phase.log

NEXT STEPS:
$(if [ "$overall_status" = "PASSED" ]; then
    echo "1. ✅ Review quality_report.txt for any minor issues"
    echo "2. ✅ Check success_criteria.txt for completion status"
    echo "3. ✅ Commit changes if all criteria are met"
    echo "4. ✅ Deploy updated documentation"
else
    echo "1. ❌ Review phase logs for error details"
    echo "2. ❌ Fix issues identified in quality_report.txt"
    echo "3. ❌ Re-run failed phases manually if needed"
    echo "4. ❌ Check system resources and dependencies"
fi)

AUTOMATION COMPLETE: $(date)
EOF

    log_success "Master summary generated: ${OUTPUT_DIR}/master_summary.txt"
}

# Main execution
main() {
    echo "=== AI DOCUMENTATION MASTER AUTOMATION STARTED $(date) ==="
    
    # Change to project root for consistent paths
    cd "${PROJECT_ROOT}"
    
    # Run checks and initialization
    check_prerequisites
    initialize_environment
    
    # Define phases
    local phases=(
        "Discovery:ai_doc_discovery.sh"
        "Content Update:ai_doc_content_update.sh"
        "Structure Validation:ai_doc_structure_validate.sh"
        "Quality Assurance:ai_doc_qa.sh"
    )
    
    local total_phases=${#phases[@]}
    local failed_phases=()
    
    # Execute phases
    for i in "${!phases[@]}"; do
        local phase_info="${phases[$i]}"
        local phase_name="${phase_info%:*}"
        local phase_script="${phase_info#*:}"
        local phase_number=$((i + 1))
        
        if ! run_phase "$phase_name" "$phase_script" "$phase_number" "$total_phases"; then
            failed_phases+=("$phase_name")
        fi
    done
    
    # Generate summary
    generate_summary
    
    # Final status
    if [ ${#failed_phases[@]} -eq 0 ]; then
        log_success "=== AI DOCUMENTATION MASTER AUTOMATION COMPLETE $(date) ==="
        echo "📊 Summary: ${OUTPUT_DIR}/master_summary.txt"
        echo "📋 Quality report: ${OUTPUT_DIR}/quality_report.txt"
        echo "✅ Success criteria: ${OUTPUT_DIR}/success_criteria.txt"
        exit 0
    else
        log_error "=== AI DOCUMENTATION MASTER AUTOMATION FAILED $(date) ==="
        echo "❌ Failed phases: ${failed_phases[*]}"
        echo "📊 Summary: ${OUTPUT_DIR}/master_summary.txt"
        echo "📋 Quality report: ${OUTPUT_DIR}/quality_report.txt"
        exit 1
    fi
}

# Trap for cleanup on exit
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Script exited with code $exit_code"
        echo "Check logs in ${OUTPUT_DIR}/ for details"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Run main function
main "$@" 