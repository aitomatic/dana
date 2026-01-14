#!/bin/bash
# bin/ralph.sh - True Ralph implementation (fresh context each iteration)
# Works with: claude, codex, aider, or any CLI-based AI coder
#
# The key insight of Ralph: each iteration starts with FRESH context.
# Self-reference happens through FILES, not conversation history.
#
# ============================================================================
# RALPH.MD FILE PATTERN AND REQUIREMENTS
# ============================================================================
#
# Every ralph.md file must follow a strict pattern to ensure consistency
# and completeness. This section documents the required structure.
#
# 1. SOURCE PRD REQUIREMENT
#    - Every ralph.md MUST have a corresponding prd.md file
#    - The PRD (Product Requirements Document) describes WHAT and WHY
#    - The ralph.md (Implementation Spec) describes HOW
#    - Naming convention: if ralph.md is "feature-ralph.md", 
#      the PRD must be "feature-prd.md" in the same directory
#
# 2. REQUIRED SECTIONS IN RALPH.MD
#
#    a. Status (at top)
#       - Format: **Status: ✅ COMPLETE** or **Status: ⚠️ IN PROGRESS**
#       - Indicates current implementation state
#
#    b. Goal
#       - Clear statement of what will be implemented
#       - Should align with PRD's problem statement
#
#    c. Demo
#       - Shows "Without X (The Problem)" and "With X (The Solution)"
#       - Demonstrates the value and usage
#       - Includes "What You'll See" section showing expected output
#
#    d. MVP Requirements
#       - Detailed implementation specifications
#       - Code snippets showing expected interfaces
#       - Checkbox lists for each requirement: `- [ ]` or `- [x]`
#
#    e. Files Implemented
#       - List of files that should be created/modified
#       - Format: `- \`path/to/file.py\` ✅` or `- \`path/to/file.py\` ❌`
#
#    f. Tests Required
#       - Test file specifications with test cases
#       - Checkbox lists for each test: `- [ ]` or `- [x]`
#       - Command to run tests
#
#    g. Success Criteria
#       - Numbered list of conditions that must be met
#       - All must be satisfied before marking complete
#
#    h. Before Marking Complete
#       - Checklist for code review
#       - KISS/YAGNI compliance checks
#       - Code quality requirements
#
#    i. When Complete
#       - Test commands that MUST be run
#       - Instructions for outputting completion tag
#       - Format: Only if ALL tests pass, output:
#         `<promise>` + `TASK COMPLETE` + `</promise>`
#
#    j. References
#       - Link to PRD: `- PRD: [feature-prd.md](./feature-prd.md)`
#       - Link to parent/overview docs
#       - Dependencies on other ralph.md files (if applicable)
#
# 3. EXIT CONDITIONS
#    - Completion is signaled by writing: <promise>TASK COMPLETE</promise>
#    - This tag must appear in the spec file or any recently modified file
#    - The promise text can be customized via --promise flag
#    - Tests MUST pass before completion tag is written
#
# 4. DEPENDENCIES
#    - If implementation depends on other ralph.md specs, list them
#    - Format: `- Depends on: [other-ralph.md](./other-ralph.md)`
#    - Ensure dependencies are completed first
#
# 5. IMPLEMENTATION GUIDANCE
#    - The ralph.md should encourage the coder to use any available tools,
#      plugins, or capabilities that can streamline or simplify the implementation
#    - Examples include:
#      * Code generation tools or templates
#      * Automated refactoring capabilities
#      * Built-in testing frameworks or test generators
#      * Code analysis or linting tools
#      * Any other features that reduce manual work or improve code quality
#    - Prefer simpler, more maintainable solutions over complex ones
#    - Use established patterns and libraries when appropriate
#    - The goal is efficient, clean implementation that meets the spec requirements
#
# 6. VALIDATION
#    - ralph.sh validates that:
#      * Corresponding PRD file exists
#      * Required sections are present
#      * Status section exists at top
#      * References section links to PRD
#
# ============================================================================

set -euo pipefail

# Selected coder (claude, codex, aider, etc.)
RALPH_CODER="codex"

# Defaults
CODER="${RALPH_CODER:-claude}"
SPEC_FILE=""
MAX_ITER=20
PROMISE="TASK COMPLETE"

usage() {
  cat <<EOF
Usage: ralph.sh [OPTIONS] SPEC_FILE

True Ralph loop - fresh context each iteration, self-reference via files only.

Options:
  -c, --coder CODER      AI coder to use (default: claude)
                         Supported: claude, codex, aider, custom
  -n, --max-iterations N Max iterations (default: 20)
  -p, --promise TEXT     Completion promise (default: "TASK COMPLETE")
  -h, --help             Show this help

Environment:
  RALPH_CODER            Default coder (overridden by --coder)

Examples:
  ralph.sh specs/rlm.md
  ralph.sh -c codex -n 10 specs/rlm.md
  ralph.sh --coder aider --promise "ALL TESTS PASS" specs/rlm.md

How it works:
  1. Each iteration invokes the coder with FRESH context (no history)
  2. Coder sees its previous work in FILES and git history
  3. Coder updates files, checks progress against spec
  4. Loop continues until <promise>TEXT</promise> found or max iterations

To signal completion, the coder should output in any file:
  <promise>YOUR_PROMISE_TEXT</promise>

RALPH.MD FILE REQUIREMENTS:
  - Must have corresponding prd.md file (describes WHAT/WHY)
  - Required sections: Goal, Demo, MVP Requirements, Files Implemented,
    Tests Required, Success Criteria, Before Marking Complete, When Complete,
    References
  - Status section at top (✅ COMPLETE or ⚠️ IN PROGRESS)
  - References section must link to PRD
  - See script header for full documentation
EOF
  exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      usage
      ;;
    -c|--coder)
      CODER="$2"
      shift 2
      ;;
    -n|--max-iterations)
      MAX_ITER="$2"
      shift 2
      ;;
    -p|--promise)
      PROMISE="$2"
      shift 2
      ;;
    *)
      if [[ -z "$SPEC_FILE" ]]; then
        SPEC_FILE="$1"
      else
        echo "Error: Unexpected argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

# Validate spec file
if [[ -z "$SPEC_FILE" ]]; then
  echo "Error: No spec file provided" >&2
  echo "Usage: ralph.sh [OPTIONS] SPEC_FILE" >&2
  exit 1
fi

if [[ ! -f "$SPEC_FILE" ]]; then
  echo "Error: Spec file not found: $SPEC_FILE" >&2
  exit 1
fi

# Validate ralph.md file structure
validate_ralph_spec() {
  local spec="$1"
  local errors=0
  local warnings=0

  echo "🔍 Validating ralph.md structure..."
  echo ""

  # Check if corresponding PRD exists
  local spec_dir=$(dirname "$spec")
  local spec_basename=$(basename "$spec")
  local prd_file=""
  
  if [[ "$spec_basename" =~ -ralph\.md$ ]]; then
    # Replace -ralph.md with -prd.md
    prd_file="${spec_basename%-ralph.md}-prd.md"
    prd_path="$spec_dir/$prd_file"
  elif [[ "$spec_basename" =~ ralph\.md$ ]]; then
    # If just "ralph.md", look for "prd.md" in same dir
    prd_path="$spec_dir/prd.md"
  else
    # Try common patterns
    prd_path="$spec_dir/${spec_basename%.md}-prd.md"
  fi

  if [[ ! -f "$prd_path" ]]; then
    echo "  ⚠️  WARNING: Corresponding PRD not found: $prd_path" >&2
    echo "     Expected: PRD file should exist for every ralph.md" >&2
    warnings=$((warnings + 1))
  else
    echo "  ✅ PRD file found: $prd_path"
  fi

  # Check for required sections
  local required_sections=(
    "## Goal"
    "## Demo"
    "## MVP Requirements"
    "## Files Implemented"
    "## Tests Required"
    "## Success Criteria"
    "## Before Marking Complete"
    "## When Complete"
    "## References"
  )

  for section in "${required_sections[@]}"; do
    if grep -q "^${section}" "$spec" 2>/dev/null; then
      echo "  ✅ Found: $section"
    else
      echo "  ❌ Missing: $section" >&2
      errors=$((errors + 1))
    fi
  done

  # Check for Status at top (should be in first 10 lines)
  if head -n 10 "$spec" | grep -qiE "^\*\*Status:"; then
    echo "  ✅ Found: Status section at top"
  else
    echo "  ⚠️  WARNING: Status section not found in first 10 lines" >&2
    warnings=$((warnings + 1))
  fi

  # Check for PRD reference in References section
  if grep -A 20 "^## References" "$spec" 2>/dev/null | grep -qiE "prd\.md|PRD"; then
    echo "  ✅ Found: PRD reference in References section"
  else
    echo "  ⚠️  WARNING: PRD reference not found in References section" >&2
    warnings=$((warnings + 1))
  fi

  # Check for promise tag instructions in "When Complete" section
  if grep -A 10 "^## When Complete" "$spec" 2>/dev/null | grep -qiE "<promise>|promise tag"; then
    echo "  ✅ Found: Promise tag instructions"
  else
    echo "  ⚠️  WARNING: Promise tag instructions not found in 'When Complete' section" >&2
    warnings=$((warnings + 1))
  fi

  echo ""
  if [[ $errors -gt 0 ]]; then
    echo "  ❌ Validation failed: $errors error(s), $warnings warning(s)" >&2
    echo "     Please fix the required sections before running Ralph loop." >&2
    return 1
  elif [[ $warnings -gt 0 ]]; then
    echo "  ⚠️  Validation passed with $warnings warning(s)" >&2
    echo "     Continuing, but consider addressing warnings." >&2
    return 0
  else
    echo "  ✅ Validation passed: All required sections present"
    return 0
  fi
}

# Run validation
if ! validate_ralph_spec "$SPEC_FILE"; then
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "  Validation failed. Please fix the spec file structure."
  echo "  See documentation at top of this script for requirements."
  echo "═══════════════════════════════════════════════════════════"
  exit 1
fi

# Build prompt with Ralph instructions prepended
build_prompt() {
  local spec="$1"
  cat <<EOF
You are running inside a Ralph loop (iteration $i of $MAX_ITER).

RALPH.MD FILE STRUCTURE REQUIREMENTS:
This spec file should follow the established ralph.md pattern:
1. Must have corresponding prd.md file (describes WHAT/WHY, this file describes HOW)
2. Required sections:
   - Status (at top): **Status: ✅ COMPLETE** or **Status: ⚠️ IN PROGRESS**
   - Goal: Clear statement of what will be implemented
   - Demo: Shows "Without X (The Problem)" and "With X (The Solution)"
   - MVP Requirements: Detailed implementation specs with checkboxes
   - Files Implemented: List of files with ✅/❌ status
   - Tests Required: Test specifications with checkboxes
   - Success Criteria: Numbered list of completion conditions
   - Before Marking Complete: Code review checklist
   - When Complete: Test commands and promise tag instructions
   - References: Must link to PRD file and parent docs
3. Exit condition: Write <promise>$PROMISE</promise> when ALL tests pass

IMPLEMENTATION GUIDANCE:
- If this coder has tools, plugins, or capabilities that can streamline or simplify
  the implementation, you SHOULD use them. For example:
  * Code generation tools or templates
  * Automated refactoring capabilities
  * Built-in testing frameworks or test generators
  * Code analysis or linting tools
  * Any other features that reduce manual work or improve code quality
- Prefer simpler, more maintainable solutions over complex ones
- Use established patterns and libraries when appropriate
- The goal is efficient, clean implementation that meets the spec requirements

COMPLETION INSTRUCTIONS:
When the task described below is FULLY COMPLETE, you MUST:
1. Run all required tests (see "When Complete" section)
2. Verify all success criteria are met
3. Only if ALL tests pass, write this exact line to the spec file or any project file:
   <promise>$PROMISE</promise>

If the task is NOT yet complete, do NOT write the promise tag. Just make progress and the loop will continue.

---

$(cat "$spec")
EOF
}

# Coder-specific invocation
run_coder() {
  local spec="$1"
  case "$CODER" in
    claude)
      #build_prompt "$spec" | claude --dangerously-skip-permissions --print
      claude --dangerously-skip-permissions --print "$(build_prompt "$spec")"
      ;;
    codex)
      codex exec --full-auto "$(build_prompt "$spec")"
      ;;
    aider)
      aider --message "$(build_prompt "$spec")"
      ;;
    *)
      # Custom: assume it's a command that accepts stdin
      build_prompt "$spec" | $CODER
      ;;
  esac
}

# Check for completion promise in tracked files
check_promise() {
  # Check in spec file itself
  if grep -q "<promise>$PROMISE</promise>" "$SPEC_FILE" 2>/dev/null; then
    return 0
  fi
  # Check in recently modified files (last 5 minutes)
  if find . -type f -mmin -5 -exec grep -l "<promise>$PROMISE</promise>" {} \; 2>/dev/null | head -1 | grep -q .; then
    return 0
  fi
  return 1
}

echo "═══════════════════════════════════════════════════════════"
echo "  True Ralph Loop"
echo "═══════════════════════════════════════════════════════════"
echo "  Coder:      $CODER"
echo "  Spec:       $SPEC_FILE"
echo "  Max iter:   $MAX_ITER"
echo "  Promise:    $PROMISE"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Main loop
for i in $(seq 1 $MAX_ITER); do
  echo ""
  echo "🔄 ═══ Ralph iteration $i/$MAX_ITER ═══"
  echo ""

  run_coder "$SPEC_FILE"

  # Check for completion
  if check_promise; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ✅ Promise detected: $PROMISE"
    echo "  Completed in $i iteration(s)"
    echo "═══════════════════════════════════════════════════════════"
    exit 0
  fi

  echo ""
  echo "── Iteration $i complete, promise not yet fulfilled ──"
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ⚠️  Max iterations ($MAX_ITER) reached without completion"
echo "═══════════════════════════════════════════════════════════"
exit 1
