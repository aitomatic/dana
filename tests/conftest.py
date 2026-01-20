from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DANA_AGENT_ROOT = REPO_ROOT / "dana_agent"
if str(DANA_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(DANA_AGENT_ROOT))
