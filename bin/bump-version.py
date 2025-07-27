#!/usr/bin/env python3
"""
Simple Version Bumping Utility for Dana Agent

Usage:
    ./bin/bump-version.py patch     # 0.25.7.19 → 0.25.7.20
    ./bin/bump-version.py minor     # 0.25.7.19 → 0.25.8.0
    ./bin/bump-version.py major     # 0.25.7.19 → 0.26.0.0
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def get_current_version():
    """Get current version from pyproject.toml [project] section"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")

    content = pyproject_path.read_text()
    # Look specifically for version in [project] section
    project_section_match = re.search(r"\[project\](.*?)(?=\[|\Z)", content, re.DOTALL)
    if not project_section_match:
        raise ValueError("Could not find [project] section in pyproject.toml")

    project_content = project_section_match.group(1)
    version_match = re.search(r'version\s*=\s*"([^"]+)"', project_content)
    if not version_match:
        raise ValueError("Could not find version in [project] section")
    return version_match.group(1)


def set_version(new_version):
    """Update version in pyproject.toml [project] section only"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Find the [project] section and update only the version within it
    def replace_project_version(match):
        project_section = match.group(1)
        updated_section = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_version}"', project_section)
        return f"[project]{updated_section}"

    updated_content = re.sub(r"\[project\](.*?)(?=\[|\Z)", replace_project_version, content, flags=re.DOTALL)
    pyproject_path.write_text(updated_content)
    print(f"✅ Updated version to {new_version}")


def bump_version(current_version, bump_type):
    """Bump version based on type"""
    # Parse version (assumes X.Y.Z.W format)
    parts = current_version.split(".")
    if len(parts) != 4:
        raise ValueError(f"Expected version format: X.Y.Z.W, got: {current_version}")

    major, minor, patch, build = map(int, parts)

    if bump_type == "major":
        major += 1
        minor = patch = build = 0
    elif bump_type == "minor":
        minor += 1
        patch = build = 0
    elif bump_type == "patch":
        patch += 1
        build = 0
    elif bump_type == "build":
        build += 1
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")

    return f"{major}.{minor}.{patch}.{build}"


def commit_changes(version):
    """Commit the version change"""
    try:
        subprocess.run(["git", "add", "pyproject.toml"], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"Bump version to {version}"],
            check=True,
            capture_output=True,
        )
        print("✅ Committed version bump")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to commit: {e}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Simple version bumper for Dana Agent")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch", "build"],
        help="Type of version bump",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument("--commit", action="store_true", help="Commit the version change")

    args = parser.parse_args()

    try:
        current = get_current_version()
        new_version = bump_version(current, args.bump_type)

        print(f"Current version: {current}")
        print(f"New version: {new_version}")

        if args.dry_run:
            print("🔍 Dry run - no changes made")
            return

        # Update version
        set_version(new_version)

        # Commit if requested
        if args.commit:
            if not commit_changes(new_version):
                sys.exit(1)

        print(f"\n🎉 Version updated to {new_version}")
        print("\nNext step: git push origin release/pypi")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
