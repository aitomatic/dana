#!/usr/bin/env python3
"""
Adana REPL - Entry Point

This module serves as the entry point for the Adana interactive REPL.
"""

import sys


def main():
    """Main entry point for the Adana REPL."""
    try:
        from adana.apps.repl.repl_app import AdanaREPLApp

        app = AdanaREPLApp()
        app.run()

    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except Exception as e:
        print(f"Error starting Adana REPL: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
