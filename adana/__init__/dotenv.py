"""
Adana Library Initialization Module

This module handles all library startup and initialization tasks.
It can be run directly as: python -m adana.__init__

This module is automatically imported when the main adana library is imported.
"""

# Import startup functions directly
from pathlib import Path
import sys


# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import startup functions directly
from dotenv import find_dotenv, load_dotenv


def load_env():
    """
    Load environment variables from .env file.

    Searches for .env file up the directory tree until it finds one
    or reaches the home directory. This function is called automatically
    when the library is imported, but you can call it explicitly if needed.
    """
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()


def init():
    """
    Initialize the Adana library.

    This function handles all startup tasks including:
    - Loading environment variables from .env files
    - Any other library initialization tasks
    """
    load_env()
