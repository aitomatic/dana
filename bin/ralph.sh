#!/bin/bash -
# bin/ralph.sh - True Ralph implementation (fresh context each iteration)
# Works with: claude, codex, aider, or any CLI-based AI coder
#
# The key insight of Ralph: each iteration starts with FRESH context.
# Self-reference happens through FILES, not conversation history.

set -euo pipefail

# Defaults
CLAUDE="claude --dangerously-skip-permissions"
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

# Coder-specific invocation
run_coder() {
  local spec="$1"
  case "$CODER" in
    claude)
	$CLAUDE --print < "$spec"
	;;
    claude-json)
      # Stream output with JSON parsing for real-time display
      cat "$spec" | claude --print --output-format stream-json --verbose 2>&1 | while IFS= read -r line; do
        # Extract text from assistant messages
        if echo "$line" | jq -e '.type == "assistant"' >/dev/null 2>&1; then
          echo "$line" | jq -r '.message.content[]? | select(.type == "text") | .text // empty' 2>/dev/null
        # Show tool use
        elif echo "$line" | jq -e '.type == "tool_use"' >/dev/null 2>&1; then
          tool_name=$(echo "$line" | jq -r '.tool // "unknown"' 2>/dev/null)
          echo "[Tool: $tool_name]"
        # Show final result
        elif echo "$line" | jq -e '.type == "result"' >/dev/null 2>&1; then
          echo ""
          echo "--- Result ---"
          echo "$line" | jq -r '.result // empty' 2>/dev/null
        fi
      done
      ;;
    codex)
      codex < "$spec"
      ;;
    aider)
      aider --message "$(cat "$spec")"
      ;;
    *)
      # Custom: assume it's a command that accepts stdin
      $CODER < "$spec"
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
