#!/usr/bin/env python3
"""
Script to help categorize tests into fast (CI) and deep (local) categories.

This script analyzes test files and suggests which tests should be marked as "deep"
based on various heuristics:
- Large test files (>300 lines)
- Integration/comprehensive test classes
- Tests with many test methods
- Tests that appear to be end-to-end or complex scenarios

Usage:
    python scripts/categorize_tests.py [--apply] [--dry-run]

    --apply: Actually add @pytest.mark.deep decorators to suggested tests
    --dry-run: Show what would be changed without making changes (default)
"""

import argparse
import ast
from pathlib import Path
from typing import List


class TestAnalyzer:
    """Analyzes test files to suggest categorization."""

    # Heuristics for identifying "deep" tests
    DEEP_INDICATORS = {
        "class_names": [
            "integration",
            "comprehensive",
            "advanced",
            "end_to_end",
            "e2e",
            "scenario",
            "workflow",
            "pipeline",
            "full",
            "complete",
            "real_world",
        ],
        "method_names": [
            "integration",
            "comprehensive",
            "end_to_end",
            "e2e",
            "scenario",
            "workflow",
            "pipeline",
            "full_",
            "complete_",
            "real_world",
        ],
        "file_patterns": ["integration", "comprehensive", "end_to_end", "e2e", "scenario"],
    }

    # Size thresholds
    LARGE_FILE_THRESHOLD = 300  # lines
    MANY_TESTS_THRESHOLD = 15  # test methods per class

    def __init__(self, test_dir: str = "tests"):
        self.test_dir = Path(test_dir)

    def find_test_files(self) -> List[Path]:
        """Find all test files."""
        return list(self.test_dir.rglob("test_*.py"))

    def analyze_file(self, file_path: Path) -> dict:
        """Analyze a single test file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()

            tree = ast.parse(content)

            analysis = {
                "file_path": file_path,
                "line_count": len(lines),
                "is_large": len(lines) > self.LARGE_FILE_THRESHOLD,
                "test_classes": [],
                "suggestions": [],
                "has_deep_markers": "@pytest.mark.deep" in content or "@pytest.mark.slow" in content,
            }

            # Analyze AST for test classes and methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    class_info = self._analyze_test_class(node, content)
                    analysis["test_classes"].append(class_info)

            # Generate suggestions
            analysis["suggestions"] = self._generate_suggestions(analysis)

            return analysis

        except Exception as e:
            return {"file_path": file_path, "error": str(e), "suggestions": []}

    def _analyze_test_class(self, class_node: ast.ClassDef, content: str) -> dict:
        """Analyze a test class."""
        test_methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]

        class_info = {
            "name": class_node.name,
            "line_number": class_node.lineno,
            "test_method_count": len(test_methods),
            "is_large": len(test_methods) > self.MANY_TESTS_THRESHOLD,
            "suggests_deep": False,
            "reasons": [],
        }

        # Check class name for deep indicators
        class_name_lower = class_node.name.lower()
        for indicator in self.DEEP_INDICATORS["class_names"]:
            if indicator in class_name_lower:
                class_info["suggests_deep"] = True
                class_info["reasons"].append(f"Class name contains '{indicator}'")

        # Check if it has many test methods
        if class_info["is_large"]:
            class_info["suggests_deep"] = True
            class_info["reasons"].append(f"Many test methods ({len(test_methods)})")

        # Check method names
        for method in test_methods:
            method_name_lower = method.name.lower()
            for indicator in self.DEEP_INDICATORS["method_names"]:
                if indicator in method_name_lower:
                    class_info["suggests_deep"] = True
                    class_info["reasons"].append(f"Method '{method.name}' suggests deep testing")
                    break

        return class_info

    def _generate_suggestions(self, analysis: dict) -> List[str]:
        """Generate suggestions for marking tests as deep."""
        suggestions = []

        # Skip if already marked
        if analysis.get("has_deep_markers"):
            return ["Already has deep/slow markers"]

        # Large file suggestion
        if analysis["is_large"]:
            suggestions.append(f"Large file ({analysis['line_count']} lines)")

        # File name pattern suggestion
        file_name_lower = analysis["file_path"].name.lower()
        for pattern in self.DEEP_INDICATORS["file_patterns"]:
            if pattern in file_name_lower:
                suggestions.append(f"File name contains '{pattern}'")

        # Class-based suggestions
        deep_classes = [cls for cls in analysis["test_classes"] if cls["suggests_deep"]]
        if deep_classes:
            for cls in deep_classes:
                suggestions.append(f"Class {cls['name']}: {', '.join(cls['reasons'])}")

        return suggestions

    def should_mark_as_deep(self, analysis: dict) -> bool:
        """Determine if a file should be marked as deep."""
        if analysis.get("has_deep_markers"):
            return False

        # Mark as deep if any suggestions exist
        return len(analysis["suggestions"]) > 0

    def apply_deep_markers(self, file_path: Path, dry_run: bool = True) -> bool:
        """Apply @pytest.mark.deep decorators to test classes."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()

            # Parse to find test classes that should be marked
            tree = ast.parse(content)
            analysis = self.analyze_file(file_path)

            if not self.should_mark_as_deep(analysis):
                return False

            # Find classes to mark
            classes_to_mark = [cls for cls in analysis["test_classes"] if cls["suggests_deep"]]

            if not classes_to_mark:
                # Mark the entire file if it's large or has deep indicators
                if analysis["is_large"] or any("file name" in s.lower() for s in analysis["suggestions"]):
                    # Add import and mark all test classes
                    modified_lines = self._add_deep_markers_to_file(lines, tree)
                else:
                    return False
            else:
                # Mark specific classes
                modified_lines = self._add_deep_markers_to_classes(lines, classes_to_mark)

            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(modified_lines))

            return True

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def _add_deep_markers_to_file(self, lines: List[str], tree: ast.AST) -> List[str]:
        """Add deep markers to all test classes in a file."""
        # Ensure pytest import
        modified_lines = self._ensure_pytest_import(lines)

        # Find all test classes and add markers
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                class_line_idx = node.lineno - 1

                # Check if already has a marker
                if class_line_idx > 0 and "@pytest.mark." in modified_lines[class_line_idx - 1]:
                    continue

                # Add the marker
                indent = len(modified_lines[class_line_idx]) - len(modified_lines[class_line_idx].lstrip())
                marker = " " * indent + "@pytest.mark.deep"
                modified_lines.insert(class_line_idx, marker)

        return modified_lines

    def _add_deep_markers_to_classes(self, lines: List[str], classes_to_mark: List[dict]) -> List[str]:
        """Add deep markers to specific classes."""
        modified_lines = self._ensure_pytest_import(lines)

        # Sort by line number in reverse order to avoid index shifting
        classes_to_mark.sort(key=lambda x: x["line_number"], reverse=True)

        for class_info in classes_to_mark:
            class_line_idx = class_info["line_number"] - 1

            # Check if already has a marker
            if class_line_idx > 0 and "@pytest.mark." in modified_lines[class_line_idx - 1]:
                continue

            # Add the marker
            indent = len(modified_lines[class_line_idx]) - len(modified_lines[class_line_idx].lstrip())
            marker = " " * indent + "@pytest.mark.deep"
            modified_lines.insert(class_line_idx, marker)

        return modified_lines

    def _ensure_pytest_import(self, lines: List[str]) -> List[str]:
        """Ensure pytest is imported."""
        # Check if pytest is already imported
        for line in lines[:20]:  # Check first 20 lines
            if "import pytest" in line:
                return lines[:]

        # Find where to insert import (after docstring, before first import or class)
        insert_idx = 0
        in_docstring = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                elif stripped.endswith('"""') or stripped.endswith("'''"):
                    in_docstring = False
                    insert_idx = i + 1
                continue

            if in_docstring:
                continue

            # Insert before first import or class
            if stripped.startswith(("import ", "from ", "class ", "@")) and stripped:
                insert_idx = i
                break

            if stripped:  # Non-empty line
                insert_idx = i + 1

        modified_lines = lines[:]
        modified_lines.insert(insert_idx, "import pytest")
        modified_lines.insert(insert_idx + 1, "")

        return modified_lines


def main():
    parser = argparse.ArgumentParser(description="Categorize tests into fast and deep categories")
    parser.add_argument("--apply", action="store_true", help="Apply changes to files")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show what would be changed (default)")
    parser.add_argument("--test-dir", default="tests", help="Test directory to analyze")

    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    analyzer = TestAnalyzer(args.test_dir)
    test_files = analyzer.find_test_files()

    print(f"Analyzing {len(test_files)} test files...")
    print("=" * 60)

    deep_candidates = []

    for file_path in test_files:
        analysis = analyzer.analyze_file(file_path)

        if "error" in analysis:
            print(f"ERROR: {file_path}: {analysis['error']}")
            continue

        if analyzer.should_mark_as_deep(analysis):
            deep_candidates.append(analysis)

    print(f"\nFound {len(deep_candidates)} files that should be marked as 'deep':")
    print("=" * 60)

    for analysis in deep_candidates:
        rel_path = analysis["file_path"].relative_to(Path(args.test_dir).parent)
        print(f"\n📁 {rel_path}")
        print(f"   Lines: {analysis['line_count']}")
        for suggestion in analysis["suggestions"]:
            print(f"   • {suggestion}")

    if deep_candidates and not args.dry_run:
        print(f"\nApplying deep markers to {len(deep_candidates)} files...")

        for analysis in deep_candidates:
            success = analyzer.apply_deep_markers(analysis["file_path"], dry_run=False)
            if success:
                rel_path = analysis["file_path"].relative_to(Path(args.test_dir).parent)
                print(f"✅ Marked {rel_path}")
            else:
                print(f"❌ Failed to mark {analysis['file_path']}")

    elif deep_candidates:
        print("\n💡 To apply these changes, run:")
        print("   python scripts/categorize_tests.py --apply")

    print("\n📊 Summary:")
    print(f"   Total test files: {len(test_files)}")
    print(f"   Files to mark as deep: {len(deep_candidates)}")
    print(f"   Estimated fast tests remaining: {len(test_files) - len(deep_candidates)}")


if __name__ == "__main__":
    main()
