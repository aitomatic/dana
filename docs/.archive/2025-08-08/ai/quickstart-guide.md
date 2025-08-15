# Quickstart Content Guide

Objective: A new user achieves a working Dana agent in under 5 minutes.

Requirements:
- Lead with a real AI task (e.g., model call, small tool use) – not Hello World.
- ≤ 3 steps from install to first success.
- First code block runnable in <30 seconds; include expected output.
- All code blocks copy-paste-run without edits.
- Validate against current PyPI: `pip install dana-lang --upgrade`.

Structure:
1) Install Dana (pip; any env prerequisites).
2) Minimal working agent (.na file) with instructions to run.
3) Verification output with a short explanation of what happened.

Do:
- Use realistic model identifiers (e.g., `gpt-4o`, `claude-3-5`).
- Show one small production-grade touch (timeout or basic error handling).
- Add version badge and compatibility comment to the page.

Don’t:
- Introduce unreleased features or internal tools.
- Require reading other pages before success.
- Bury the first runnable example below the fold.

Checklist before commit:
- Runs end-to-end via copy/paste on a clean machine.
- Output screenshot/snippet matches actual output.
- Works with latest `dana-lang` on PyPI.
- No references to `docs/.archive`.



