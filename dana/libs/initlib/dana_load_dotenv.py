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
    print("dana_load_dotenv: Starting .env file search...")

    # 1. Current Working Directory
    cwd_env = Path.cwd() / ".env"
    print(f"dana_load_dotenv: Checking CWD .env: {cwd_env}")
    if cwd_env.is_file():
        print(f"dana_load_dotenv: Found .env in CWD, loading: {cwd_env}")
        load_dotenv(dotenv_path=cwd_env, override=True, interpolate=True, encoding="utf-8")
        print("dana_load_dotenv: Successfully loaded .env from CWD")
        return
    else:
        print(f"dana_load_dotenv: No .env file found in CWD: {cwd_env}")

    # 2. Dana user directory
    dana_env = Path.home() / ".dana" / ".env"
    print(f"dana_load_dotenv: Checking Dana user .env: {dana_env}")
    if dana_env.is_file():
        print(f"dana_load_dotenv: Found .env in Dana user directory, loading: {dana_env}")
        load_dotenv(dotenv_path=dana_env, override=True, interpolate=True, encoding="utf-8")
        print("dana_load_dotenv: Successfully loaded .env from Dana user directory")
        return
    else:
        print(f"dana_load_dotenv: No .env file found in Dana user directory: {dana_env}")

    # 3. User home directory
    home_env = Path.home() / ".env"
    print(f"dana_load_dotenv: Checking user home .env: {home_env}")
    if home_env.is_file():
        print(f"dana_load_dotenv: Found .env in user home directory, loading: {home_env}")
        load_dotenv(dotenv_path=home_env, override=True, interpolate=True, encoding="utf-8")
        print("dana_load_dotenv: Successfully loaded .env from user home directory")
        return
    else:
        print(f"dana_load_dotenv: No .env file found in user home directory: {home_env}")

    print("dana_load_dotenv: .env file search completed")
