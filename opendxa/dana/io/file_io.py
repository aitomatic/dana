"""Input/Output helpers, initially just for reading program files."""

import os


def read_dana_program(file_path: str) -> str:
    """Reads a DANA program file and returns its content as a string."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DANA program file not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise OSError(f"Error reading DANA program file '{file_path}': {e}") from e
