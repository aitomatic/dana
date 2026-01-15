from pathlib import Path
import sys


repo_root = Path(__file__).resolve().parents[1]
dana_agent_root = repo_root / "dana_agent"
if str(dana_agent_root) not in sys.path:
    sys.path.insert(0, str(dana_agent_root))
