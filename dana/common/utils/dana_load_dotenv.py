"""Environment initialization utilities for Dana.

This module provides functions for loading environment variables and setting up
the Dana configuration environment during application startup.
"""

from pathlib import Path

from dotenv import load_dotenv


def dana_load_dotenv():
    """Load environment variables following Dana's search hierarchy.

    Searches for .env files in the following order:
    1. Current Working Directory (./.env) - project-specific
    2. Dana user directory (~/.dana/.env) - user global
    3. User home directory (~/.env) - system global

    """
    # 1. Current Working Directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        print(f"Loading environment variables from {cwd_env}")
        load_dotenv(dotenv_path=cwd_env, override=True, interpolate=True, encoding="utf-8")
        return

    # 2. Dana user directory
    dana_env = Path.home() / ".dana" / ".env"
    if dana_env.is_file():
        print(f"Loading environment variables from {dana_env}")
        load_dotenv(dotenv_path=dana_env, override=True, interpolate=True, encoding="utf-8")
        return

    # 3. User home directory
    home_env = Path.home() / ".env"
    if home_env.is_file():
        print(f"Loading environment variables from {home_env}")
        load_dotenv(dotenv_path=home_env, override=True, interpolate=True, encoding="utf-8")
        return
