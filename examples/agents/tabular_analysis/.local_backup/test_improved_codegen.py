#!/usr/bin/env python3
"""
Test improved code generator with column names containing special characters.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from resources.query_code_generator_resource import QueryCodeGeneratorResource


def test_column_with_dots():
    """Test that code generator handles column names with dots correctly."""

    print("=" * 80)
    print("Testing Code Generator with Columns Containing Dots")
    print("=" * 80)
    print()

    # Initialize code generator
    dataset_dir = Path(__file__).parent / "dataset"
    code_generator = QueryCodeGeneratorResource(workspace_root=str(dataset_dir), llm_model="gpt-4o-mini", debug=True)

    # Test case from the problem description
    analysis_text = """
To calculate the total revenue for ALABAMA and ARIZONA in the years 1993 and 1994,
we will read the `finance.csv` file and sum the values in the `Totals.Revenue` column
where the State is either 'ALABAMA' or 'ARIZONA' and the Year is in (1993, 1994).

Important: The column name is "Totals.Revenue" with a dot - it must be quoted in SQL.
Available columns: ['State', 'Year', 'Totals.Revenue']
"""

    print("Analysis Text:")
    print("-" * 80)
    print(analysis_text)
    print("-" * 80)
    print()

    print("Generating code...")
    print()

    # Generate code (don't execute since we don't have the actual file)
    result = code_generator.generate_and_execute(
        analysis_text=analysis_text,
        execute=False,  # Just generate, don't execute
    )

    if result["success"]:
        print("✅ Code Generation Successful!")
        print()
        print("Generated Code:")
        print("=" * 80)
        print(result["generated_code"])
        print("=" * 80)
        print()

        # Check for key improvements
        code = result["generated_code"]

        checks = {
            "Uses exact column name 'Totals.Revenue'": '"Totals.Revenue"' in code or "'Totals.Revenue'" in code,
            "Has column validation": "missing_cols" in code or "required_cols" in code,
            "Quotes column names in SQL": '"State"' in code or '"Year"' in code or '"Totals.Revenue"' in code,
            "Always assigns result variable": "result =" in code,
            "Includes error handling": "error" in code.lower(),
        }

        print("Code Quality Checks:")
        print("-" * 80)
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        print("-" * 80)
        print()

        all_passed = all(checks.values())
        if all_passed:
            print("🎉 All quality checks passed!")
        else:
            print("⚠️  Some quality checks failed. Review the generated code.")

    else:
        print(f"❌ Code Generation Failed: {result['error']}")

    print()
    print("=" * 80)


def test_simple_columns():
    """Test that code generator still works with simple column names."""

    print("\n")
    print("=" * 80)
    print("Testing Code Generator with Simple Column Names")
    print("=" * 80)
    print()

    # Initialize code generator
    dataset_dir = Path(__file__).parent / "dataset"
    code_generator = QueryCodeGeneratorResource(workspace_root=str(dataset_dir), llm_model="gpt-4o-mini", debug=False)

    # Test case with simple column names
    analysis_text = """
Count the number of unique SQL queries in the NL2SQL_Query_Dataset.csv file.
The file has a 'Query' column containing SQL queries.
Read the file and count the unique values in the Query column.
"""

    print("Analysis Text:")
    print("-" * 80)
    print(analysis_text)
    print("-" * 80)
    print()

    print("Generating code...")
    print()

    # Generate code (don't execute)
    result = code_generator.generate_and_execute(analysis_text=analysis_text, execute=False)

    if result["success"]:
        print("✅ Code Generation Successful!")
        print()
        print("Generated Code (first 500 chars):")
        print("=" * 80)
        print(result["generated_code"][:500] + "...")
        print("=" * 80)
    else:
        print(f"❌ Code Generation Failed: {result['error']}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    test_column_with_dots()
    test_simple_columns()

    print("\n")
    print("🎯 Testing Complete!")
    print()
    print("Summary:")
    print("- Updated code generator prompt with CRITICAL CODE GENERATION RULES")
    print("- Added requirements for exact column name preservation")
    print("- Added column validation pattern")
    print("- Added SQL quoting guidelines for special characters")
    print("- Improved error handling and result variable assignment")
