#!/bin/bash
# bin/ralph.sh - True Ralph implementation (fresh context each iteration)
# Works with: claude, codex, aider, or any CLI-based AI coder
#
# The key insight of Ralph: each iteration starts with FRESH context.
# Self-reference happens through FILES, not conversation history.
#
# ============================================================================
# WORKFLOW: PRD → RALPH → IMPLEMENTATION
# ============================================================================
#
# The Ralph workflow follows a strict process:
#
#   1. Write PRD (Product Requirements Document)
#      - Describes WHAT the feature does and WHY it's needed
#      - Human-authored or AI-assisted
#      - Location: specs/feature-prd.md
#
#   2. Generate RALPH spec from PRD
#      - Describes HOW to implement (technical specification)
#      - Generated using: ralph.sh --init specs/feature-prd.md
#      - Output: specs/feature-ralph.md
#
#   3. Run implementation loop
#      - Executes: ralph.sh specs/feature-ralph.md
#      - AI coder implements until:
#         <promise>TASK COMPLETE</promise>
#
#
# ============================================================================
# DIRECTORY CONVENTION
# ============================================================================
#
# All PRD and RALPH files should be placed in the specs/ directory:
#
#   specs/
#   ├── feature-a-prd.md      # PRD for feature A
#   ├── feature-a-ralph.md    # Generated RALPH spec for feature A
#   ├── feature-b-prd.md      # PRD for feature B
#   ├── feature-b-ralph.md    # Generated RALPH spec for feature B
#   └── ...
#
# Naming convention:
#   - PRD files:   <feature-name>-prd.md
#   - RALPH files: <feature-name>-ralph.md
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
#         <promise>TASK COMPLETE</promise>
#
#    j. References
#       - Link to PRD: `- PRD: [feature-prd.md](./feature-prd.md)`
#       - Link to parent/overview docs
#       - Dependencies on other ralph.md files (if applicable)
#
# 3. EXIT CONDITIONS
#    - Completion is signaled by writing:
#	    <promise>TASK COMPLETE</promise>
#    - This tag must appear in the spec file or any recently modified file
#    - The promise text can be customized via --promise flag
#    - Tests MUST pass before completion tag is written
#    - Do not output this tag at all if not complete. It may be detected by accident.
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
INIT_MODE=false
RUN_AFTER_INIT=false

usage() {
  cat <<EOF
Usage: ralph.sh [OPTIONS] FILE
       ralph.sh --init [OPTIONS] PRD_FILE

True Ralph loop - fresh context each iteration, self-reference via files only.

MODES:

  Implementation mode (default):
    ralph.sh specs/feature-ralph.md
    Runs the implementation loop on an existing ralph.md spec.

  Init mode (generate ralph.md from PRD):
    ralph.sh --init specs/feature-prd.md
    Generates specs/feature-ralph.md from the PRD using the AI coder.

  Init + Run mode:
    ralph.sh --init --run specs/feature-prd.md
    Generates ralph.md, then immediately runs implementation loop.

OPTIONS:

  -i, --init             Generate ralph.md from a PRD file
  -r, --run              After --init, immediately run implementation loop
  -c, --coder CODER      AI coder to use (default: ${RALPH_CODER:-claude})
                         Supported: claude, codex, aider, custom
  -n, --max-iterations N Max iterations (default: 20)
  -p, --promise TEXT     Completion promise (default: "TASK COMPLETE")
  -h, --help             Show this help

ENVIRONMENT:

  RALPH_CODER            Default coder (overridden by --coder)

WORKFLOW:

  1. Write PRD:           specs/feature-prd.md (WHAT and WHY)
  2. Generate RALPH:      ralph.sh --init specs/feature-prd.md
  3. Run implementation:  ralph.sh specs/feature-ralph.md

DIRECTORY CONVENTION:

  All specs should be in the specs/ directory:
    specs/feature-prd.md      # Product Requirements (human-written)
    specs/feature-ralph.md    # Implementation Spec (generated)

EXAMPLES:

  # Generate ralph.md from PRD
  ralph.sh --init specs/skill-integration-prd.md

  # Generate and immediately run implementation
  ralph.sh --init --run specs/skill-integration-prd.md

  # Run implementation on existing ralph.md
  ralph.sh specs/skill-integration-ralph.md

  # Use specific coder with custom iterations
  ralph.sh -c claude -n 10 specs/feature-ralph.md

HOW IT WORKS:

  Implementation loop:
    1. Each iteration invokes the coder with FRESH context (no history)
    2. Coder sees its previous work in FILES and git history
    3. Coder updates files, checks progress against spec
    4. Loop continues until <promise>TEXT</promise> found or max iterations

  To signal completion, the coder should write to any file:
    <promise>YOUR_PROMISE_TEXT</promise>

RALPH.MD REQUIREMENTS:

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
    -i|--init)
      INIT_MODE=true
      shift
      ;;
    -r|--run)
      RUN_AFTER_INIT=true
      shift
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

# Validate input file
if [[ -z "$SPEC_FILE" ]]; then
  echo "Error: No file provided" >&2
  echo "Usage: ralph.sh [OPTIONS] SPEC_FILE" >&2
  echo "       ralph.sh --init [OPTIONS] PRD_FILE" >&2
  exit 1
fi

if [[ ! -f "$SPEC_FILE" ]]; then
  echo "Error: File not found: $SPEC_FILE" >&2
  exit 1
fi

# Validate --run requires --init
if [[ "$RUN_AFTER_INIT" == "true" && "$INIT_MODE" != "true" ]]; then
  echo "Error: --run requires --init" >&2
  exit 1
fi

# ============================================================================
# INIT MODE: Generate ralph.md from PRD
# ============================================================================

# Derive ralph.md path from PRD path
get_ralph_path() {
  local prd_path="$1"
  local dir=$(dirname "$prd_path")
  local basename=$(basename "$prd_path")

  # Replace -prd.md with -ralph.md
  if [[ "$basename" =~ -prd\.md$ ]]; then
    echo "$dir/${basename%-prd.md}-ralph.md"
  elif [[ "$basename" == "prd.md" ]]; then
    echo "$dir/ralph.md"
  else
    # Fallback: just append -ralph before .md
    echo "$dir/${basename%.md}-ralph.md"
  fi
}

# Build prompt for generating ralph.md from PRD
build_init_prompt() {
  local prd_file="$1"
  local ralph_file="$2"
  cat <<'INIT_PROMPT_HEADER'
You are generating a RALPH implementation spec from a PRD (Product Requirements Document).

The PRD describes WHAT and WHY. Your job is to create a ralph.md that describes HOW.

OUTPUT REQUIREMENTS:
You MUST write the ralph.md file to the specified path. Do not just output it to the console.

RALPH.MD STRUCTURE:
The ralph.md file MUST contain these sections in order:

```markdown
# <Feature Name> - Implementation Spec

**Status: ⚠️ IN PROGRESS**

## Goal

<Clear statement of what will be implemented, derived from PRD>

## Demo

### Without <Feature> (The Problem)
<Show the current pain point>

### With <Feature> (The Solution)
<Show how it works after implementation>

### What You'll See
<Expected output/behavior>

## MVP Requirements

<Detailed technical requirements with checkboxes>
- [ ] Requirement 1
- [ ] Requirement 2
...

## Files Implemented

<List of files to create/modify>
- `path/to/file.py` ❌
- `path/to/other.py` ❌
...

## Tests Required

<Test specifications>
- [ ] Test case 1
- [ ] Test case 2
...

Command to run tests:
```bash
<test command>
```

## Success Criteria

1. <Criterion 1>
2. <Criterion 2>
...

## Before Marking Complete

- [ ] All tests pass
- [ ] Code follows existing patterns
- [ ] No unnecessary complexity (KISS)
- [ ] No over-engineering (YAGNI)
- [ ] Code is documented where non-obvious

## When Complete

Run these commands to verify:
```bash
<verification commands>
```

Only if ALL tests pass, write this line to the ralph.md file:
<promise>$task_complete$</promise>

except replace "$task_complete$" with "TASK COMPLETE".

## References

- PRD: [<feature>-prd.md](./<feature>-prd.md)
```

IMPORTANT:
- Be specific and actionable in requirements
- Include code snippets showing expected interfaces
- List ALL files that need to be created or modified
- Include specific test cases, not just "write tests"
- Success criteria should be measurable
- Reference the PRD in the References section

INIT_PROMPT_HEADER

  echo "---"
  echo ""
  echo "PRD FILE: $prd_file"
  echo "OUTPUT FILE: $ralph_file (you MUST write to this file)"
  echo ""
  echo "PRD CONTENT:"
  echo ""
  cat "$prd_file"
}

# Run init mode - generate ralph.md from PRD
run_init_coder() {
  local prd_file="$1"
  local ralph_file="$2"
  local prompt=$(build_init_prompt "$prd_file" "$ralph_file")

  case "$CODER" in
    claude)
      claude --dangerously-skip-permissions --print "$prompt"
      ;;
    codex)
      codex exec --full-auto "$prompt"
      ;;
    aider)
      aider --message "$prompt"
      ;;
    *)
      echo "$prompt" | $CODER
      ;;
  esac
}

# Handle init mode
if [[ "$INIT_MODE" == "true" ]]; then
  PRD_FILE="$SPEC_FILE"
  RALPH_FILE=$(get_ralph_path "$PRD_FILE")

  echo "═══════════════════════════════════════════════════════════"
  echo "  Ralph Init Mode"
  echo "═══════════════════════════════════════════════════════════"
  echo "  Coder:      $CODER"
  echo "  PRD:        $PRD_FILE"
  echo "  Output:     $RALPH_FILE"
  echo "═══════════════════════════════════════════════════════════"
  echo ""

  # Check if ralph.md already exists
  if [[ -f "$RALPH_FILE" ]]; then
    echo "⚠️  Warning: $RALPH_FILE already exists"
    read -p "   Overwrite? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Aborted."
      exit 1
    fi
  fi

  echo "🔄 Generating ralph.md from PRD..."
  echo ""

  run_init_coder "$PRD_FILE" "$RALPH_FILE"

  # Verify the file was created
  if [[ ! -f "$RALPH_FILE" ]]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ❌ Error: ralph.md was not created"
    echo "  Expected: $RALPH_FILE"
    echo "═══════════════════════════════════════════════════════════"
    exit 1
  fi

  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "  ✅ Generated: $RALPH_FILE"
  echo "═══════════════════════════════════════════════════════════"

  # If --run flag, continue to implementation
  if [[ "$RUN_AFTER_INIT" == "true" ]]; then
    echo ""
    echo "  Continuing to implementation loop..."
    echo ""
    SPEC_FILE="$RALPH_FILE"
  else
    echo ""
    echo "  Next step: ralph.sh $RALPH_FILE"
    echo ""
    exit 0
  fi
fi

# ============================================================================
# IMPLEMENTATION MODE: Run the Ralph loop
# ============================================================================

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

=============================================================================
CRITICAL: TEST-FIRST WORKFLOW (follow this sequence every iteration)
=============================================================================

1. RUN TESTS FIRST (before any implementation)
   - Find the test command in "Tests Required" or "When Complete" section
   - Run it BEFORE making any changes
   - This shows current state: what passes, what fails
   - If no tests exist yet, write them first

2. ANALYZE RESULTS
   - Which tests pass? (previous work is intact)
   - Which tests fail? (what needs implementation)
   - What are the error messages? (guides your implementation)

3. IMPLEMENT
   - Fix failing tests
   - Add missing functionality
   - Make targeted changes based on test failures

4. RUN TESTS AGAIN
   - Verify your changes fixed the failures
   - Ensure no regressions (previously passing tests still pass)

5. ASSESS COMPLETION
   - ALL tests pass (including live tests if specified)? → Write promise tag
   - Some tests fail? → Do NOT write promise, loop continues

TEST EXECUTION ORDER (gated - stop if any gate fails):
   Unit tests (fast) → Integration tests → Live tests (if specified)
Do NOT run live/expensive tests until unit and integration tests pass.

=============================================================================

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

CODEBASE CONVENTIONS:
- READ existing files before modifying - understand current patterns first
- FOLLOW existing code style (logging, error handling, naming) unless spec says otherwise
- REUSE existing utilities and base classes - don't reinvent
- MATCH existing patterns for similar functionality
- DON'T add new dependencies unless necessary
- DON'T change APIs/signatures unless the spec requires it

If the spec explicitly requires changing conventions (refactoring, migration, etc.),
then change them - but be consistent across the affected code.

TOOL USAGE:
- Use code search to find existing patterns before writing new code
- Use available tools/plugins to streamline implementation

SIMPLICITY:
- Prefer modifying existing code over creating new files
- Prefer simple solutions over clever ones
- Minimal, clean changes that meet the spec

COMPLETION INSTRUCTIONS:
When ALL tests pass (unit, integration, and live if specified), you MUST:
1. Verify all success criteria are met
2. Write this exact line to the spec file or any project file:
   <promise>$PROMISE</promise>

If ANY tests fail, do NOT write the promise tag. Make progress and the loop will continue.

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
    find . -type f -mmin -5 -exec grep -l "<promise>$PROMISE</promise>" {}
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
