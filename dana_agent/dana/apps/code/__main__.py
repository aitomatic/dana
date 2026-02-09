#!/usr/bin/env python3
"""
Dana Code - Entry Point

Interactive coding agent with rich terminal UI powered by DanaCodingAgent
and RichCLIRenderer.
"""

import sys


def main():
    """Main entry point for Dana Code."""
    try:
        from dotenv import find_dotenv, load_dotenv

        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path, override=True)
        else:
            load_dotenv(override=True)

        from dana.apps.code.code_app import DanaCodeApp

        app = DanaCodeApp()
        app.run()

    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except Exception as e:
        print(f"Error starting Dana Code: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
