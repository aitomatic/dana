#!/usr/bin/env python3
"""CLI tool for managing database migrations."""

import argparse
import sys

from .migrations import MigrationRunner, show_migration_status


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Dana Database Migration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("name", help="Migration name (e.g., 'add_user_roles')")
    create_parser.add_argument("--content", help="SQL content for the migration")

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # Run command
    subparsers.add_parser("run", help="Run pending migrations")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "create":
            create_migration_cmd(args.name, args.content)
        elif args.command == "status":
            show_status_cmd()
        elif args.command == "run":
            run_migrations_cmd()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def create_migration_cmd(name: str, content: str | None = None) -> None:
    """Create a new migration file."""
    runner = MigrationRunner()
    file_path = runner.create_migration(name, content or "")
    print(f"✅ Created migration: {file_path}")
    print("💡 Edit the file to add your SQL statements")


def show_status_cmd() -> None:
    """Show migration status."""
    status = show_migration_status()

    print("📊 Migration Status:")
    print(f"  Applied: {status['applied_count']}")
    print(f"  Pending: {status['pending_count']}")

    if status["applied_migrations"]:
        print("\n✅ Applied migrations:")
        for migration in status["applied_migrations"]:
            print(f"  - {migration}")

    if status["pending_migrations"]:
        print("\n⏳ Pending migrations:")
        for migration in status["pending_migrations"]:
            print(f"  - {migration}")
    else:
        print("\n✅ All migrations are up to date!")


def run_migrations_cmd() -> None:
    """Run pending migrations."""
    from .migrations import run_migrations

    print("🚀 Running pending migrations...")
    run_migrations()
    print("✅ Migration run completed!")


if __name__ == "__main__":
    main()
