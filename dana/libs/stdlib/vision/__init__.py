# Add local aicapture to Python path
import os
import sys
from pathlib import Path

# Get the directory where this module is located
try:
    vision_dir = Path(__file__).parent
except Exception:
    vision_dir = Path(os.path.dirname(__file__))

aicapture_path = str(vision_dir / "aicapture")

# Add to Python path if not already there
if str(vision_dir) not in sys.path:
    sys.path.insert(0, str(vision_dir))
