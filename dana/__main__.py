"""
DANA Command Line Interface - Module Entry Point

This module serves as the entry point when running 'python -m dana'
It delegates to the main CLI handler in dana.apps.cli.dana
"""


def main():
    from dana.apps.cli.__main__ import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
