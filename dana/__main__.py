"""
DANA Command Line Interface - Module Entry Point

This module serves as the entry point when running 'python -m dana'
It delegates to the main CLI handler in dana.apps.cli.dana
"""

from dana.apps.cli.dana import main

if __name__ == "__main__":
    main()
