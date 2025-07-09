from pathlib import Path

from dotenv import load_dotenv

import dana

from .dana import main

# if developer puts an .env file in the OpenDXA repo root directory, load it
DOTENV_PATH = Path(next(iter(dana.__path__))).parent / ".env"
if DOTENV_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_PATH, verbose=True, override=True, encoding="utf-8")

main()
