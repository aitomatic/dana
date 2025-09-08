#!/usr/bin/env python3
"""
Entry point for running the PromptEngineer Web App as a module.

Usage:
    python -m dana.frameworks.prteng.webapp
"""

import sys
from pathlib import Path

# Add the dana package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dana.frameworks.prteng.webapp.prompt_engineer_webapp import app

if __name__ == "__main__":
    print("Starting PromptEngineer Web App...")
    print("Open your browser and go to: http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)
