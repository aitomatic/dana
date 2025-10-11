#!/usr/bin/env python3
"""
Dana Conversational Agent - Entry Point

Dana is a conversational agent that can manage and orchestrate other agents,
resources, and workflows through natural conversation.
"""

import sys


def main():
    """Main entry point for the Dana conversational agent."""
    try:
        from adana.apps.dana.dana_app import DanaApp

        app = DanaApp()
        app.run()

    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except Exception as e:
        print(f"Error starting Dana: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
