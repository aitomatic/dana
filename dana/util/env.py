"""This module is used to load the .env file and the dana_config.json file."""

import os
from pathlib import Path

from dotenv import load_dotenv

import dana

__all__ = ['load_dana_env']

DANA_CONFIG_KEY = 'DANA_CONFIG'

def load_dana_env(dot_env_file_path: Path | str | None = None):
    load_dotenv(dotenv_path=dot_env_file_path,
                stream=None,
                verbose=False,
                override=False,
                interpolate=True,
                encoding='utf-8')

    if DANA_CONFIG_KEY not in os.environ:
        os.environ[DANA_CONFIG_KEY] = os.path.join(dana.__path__[0], 'dana_config.json')
