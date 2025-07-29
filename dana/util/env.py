"""This module is used to load the .env file and the dana_config.json file."""

import os
from pathlib import Path

from dotenv import load_dotenv

import dana

__all__ = ["load_dana_env"]

DANA_CONFIG_KEY = "DANA_CONFIG"
DANA_CONFIG_FILE_NAME = "dana_config.json"


def load_dana_env(dot_env_file_path: Path | str | None = None):
    load_dotenv(
        dotenv_path=dot_env_file_path,
        stream=None,
        verbose=False,
        override=True,  # if environment variables are already set, they WILL be overridden
        interpolate=True,
        encoding="utf-8",
    )

    if DANA_CONFIG_KEY not in os.environ:
        # if DANA_CONFIG is not set, set it to the path of the default dana_config.json file
        os.environ[DANA_CONFIG_KEY] = os.path.join(dana.__path__[0], DANA_CONFIG_FILE_NAME)
