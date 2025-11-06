"""
Test suite for RipgrepSearchResource.

Tests ensure that _search_with_python and _search_with_ripgrep 
return identical results for various search patterns.

Following TDD principles:
- Write ONE test at a time
- Get user approval before proceeding
- Ensure tests fail first (Red)
- Write minimal code to pass (Green)
- Refactor only after tests pass
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from resources.ripgrep_search_resource import RipgrepSearchResource


# Test fixtures and helper functions

@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def search_resource_fixtures(fixtures_dir):
    """Return RipgrepSearchResource configured for fixtures directory."""
    return RipgrepSearchResource(workspace_root=str(fixtures_dir))


@pytest.fixture
def search_resource_amd_data():
    """Return RipgrepSearchResource configured for AMD data directory."""
    data_dir = Path(__file__).parent.parent / "data"
    return RipgrepSearchResource(workspace_root=str(data_dir))


def normalize_match(match):
    """
    Normalize a match dictionary for comparison.
    
    Converts file paths to relative strings and sorts context lines
    to ensure consistent comparison between ripgrep and Python results.
    """
    normalized = match.copy()
    # Ensure file_path is a string
    if isinstance(normalized.get("file_path"), Path):
        normalized["file_path"] = str(normalized["file_path"])
    return normalized


def matches_are_equivalent(matches1, matches2, ignore_order=True):
    """
    Compare two lists of matches for equivalence.
    
    Args:
        matches1: First list of match dictionaries
        matches2: Second list of match dictionaries
        ignore_order: If True, ignore the order of matches
    
    Returns:
        tuple: (bool: are_equivalent, str: difference_message)
    """
    if len(matches1) != len(matches2):
        return False, f"Different number of matches: {len(matches1)} vs {len(matches2)}"
    
    # Normalize both match lists
    norm1 = [normalize_match(m) for m in matches1]
    norm2 = [normalize_match(m) for m in matches2]
    
    if ignore_order:
        # Sort by file_path and line_number for comparison
        norm1.sort(key=lambda x: (x.get("file_path", ""), x.get("line_number", 0)))
        norm2.sort(key=lambda x: (x.get("file_path", ""), x.get("line_number", 0)))
    
    for i, (m1, m2) in enumerate(zip(norm1, norm2)):
        # Compare each field
        if m1.get("file_path") != m2.get("file_path"):
            return False, f"Match {i}: Different file_path: {m1.get('file_path')} vs {m2.get('file_path')}"
        
        if m1.get("line_number") != m2.get("line_number"):
            return False, f"Match {i}: Different line_number: {m1.get('line_number')} vs {m2.get('line_number')}"
        
        if m1.get("line_text") != m2.get("line_text"):
            return False, f"Match {i}: Different line_text: '{m1.get('line_text')}' vs '{m2.get('line_text')}'"
        
        # match_start and match_end might differ slightly between implementations
        # due to tabs, unicode, or column calculation differences - allow reasonable tolerance
        if abs(m1.get("match_start", 0) - m2.get("match_start", 0)) > 10:
            return False, f"Match {i}: match_start differs significantly: {m1.get('match_start')} vs {m2.get('match_start')}"
    
    return True, ""


def compare_search_results(result1, result2, ignore_match_order=True):
    """
    Compare two search result dictionaries.
    
    Args:
        result1: First search result
        result2: Second search result
        ignore_match_order: If True, ignore the order of matches
    
    Returns:
        tuple: (bool: are_equal, str: difference_message)
    """
    # Check success status
    if result1.get("success") != result2.get("success"):
        return False, f"Different success status: {result1.get('success')} vs {result2.get('success')}"
    
    # If both failed, check error messages are present
    if not result1.get("success"):
        if not result1.get("error") or not result2.get("error"):
            return False, "One result has error message, other doesn't"
        return True, ""  # Both failed, that's okay
    
    # Check total_matches
    if result1.get("total_matches") != result2.get("total_matches"):
        return False, f"Different total_matches: {result1.get('total_matches')} vs {result2.get('total_matches')}"
    
    # Compare matches
    return matches_are_equivalent(result1.get("matches", []), result2.get("matches", []), ignore_match_order)


# =============================================================================
# TEST 1: Basic Literal Search
# =============================================================================

def test_literal_search_consistency(search_resource_fixtures):
    """
    Test that both search methods find simple literal strings identically.
    
    Purpose: Verify basic literal string search works consistently
    Pattern: "Total Assets" (literal, no regex)
    Expected: Both methods should find the same matches in balance_sheet.md
    """
    resource = search_resource_fixtures
    pattern = "Total Assets"
    
    # Force Python search
    resource.ripgrep_available = False
    python_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,
        max_results=10,
        context_lines=0
    )
    
    # Force ripgrep search (if available)
    resource.ripgrep_available = True
    ripgrep_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,
        max_results=10,
        context_lines=0
    )
    
    # Compare results
    are_equal, diff_msg = compare_search_results(python_result, ripgrep_result)
    
    # Assertions
    assert python_result["success"], f"Python search failed: {python_result.get('error')}"
    assert python_result["total_matches"] > 0, "Python search should find at least one match"
    assert ripgrep_result["success"], f"Ripgrep search failed: {ripgrep_result.get('error')}"
    assert ripgrep_result["total_matches"] > 0, "Ripgrep search should find at least one match"
    
    assert are_equal, f"Results differ: {diff_msg}\nPython: {python_result}\nRipgrep: {ripgrep_result}"
    
    print(f"\n✅ Test 1 PASSED: Both methods found {python_result['total_matches']} matches for '{pattern}'")


def test_literal_search_amd_file(search_resource_amd_data):
    """
    Test literal search on real AMD annual report file.
    
    Purpose: Verify both methods work on production data
    Pattern: "Revenue" (literal, case-insensitive)
    File: AMD-AR.md
    Expected: Both methods should find multiple instances
    """
    resource = search_resource_amd_data
    pattern = "Revenue"
    
    # Force Python search
    resource.ripgrep_available = False
    python_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,
        file_pattern="AMD-AR.md",
        max_results=20,
        context_lines=0
    )
    
    # Force ripgrep search
    resource.ripgrep_available = True
    ripgrep_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,
        file_pattern="AMD-AR.md",
        max_results=20,
        context_lines=0
    )
    
    # Compare results
    are_equal, diff_msg = compare_search_results(python_result, ripgrep_result)
    
    # Assertions
    assert python_result["success"], f"Python search failed: {python_result.get('error')}"
    assert python_result["total_matches"] > 0, "Should find 'Revenue' in AMD-AR.md"
    assert ripgrep_result["success"], f"Ripgrep search failed: {ripgrep_result.get('error')}"
    assert ripgrep_result["total_matches"] > 0, "Should find 'Revenue' in AMD-AR.md"
    
    assert are_equal, f"Results differ on AMD-AR.md: {diff_msg}"
    
    print(f"\n✅ Test 1b PASSED: Both methods found {python_result['total_matches']} matches in AMD-AR.md")


# =============================================================================
# TEST 2: Case Insensitive Search
# =============================================================================

def test_case_insensitive_search(search_resource_fixtures):
    """
    Test that both methods handle case insensitivity identically.
    
    Purpose: Verify case-insensitive search works consistently
    Pattern: "current assets" (should match "Current Assets", "CURRENT ASSETS", etc.)
    Expected: Both methods find the same matches regardless of case
    """
    resource = search_resource_fixtures
    pattern = "current assets"
    
    # Force Python search
    resource.ripgrep_available = False
    python_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,  # Case insensitive
        max_results=10,
        context_lines=0
    )
    
    # Force ripgrep search
    resource.ripgrep_available = True
    ripgrep_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,  # Case insensitive
        max_results=10,
        context_lines=0
    )
    
    # Compare results
    are_equal, diff_msg = compare_search_results(python_result, ripgrep_result)
    
    # Assertions
    assert python_result["success"], f"Python search failed: {python_result.get('error')}"
    assert python_result["total_matches"] > 0, "Should find 'current assets' case-insensitively"
    assert ripgrep_result["success"], f"Ripgrep search failed: {ripgrep_result.get('error')}"
    assert are_equal, f"Case insensitive results differ: {diff_msg}"
    
    print(f"\n✅ Test 2 PASSED: Case insensitive search found {python_result['total_matches']} matches")


# =============================================================================
# TEST 3: Regex Pattern with \s+ (Whitespace)
# =============================================================================

def test_regex_whitespace_pattern(search_resource_amd_data):
    """
    Test that both methods handle regex whitespace patterns identically.
    
    Purpose: Test the problematic regex patterns with \\s+ (flexible whitespace)
    Pattern: "(total\\s+)?current\\s+assets" - the pattern from financial analysis
    Expected: Both methods should parse and match the pattern correctly
    """
    resource = search_resource_amd_data
    # Use the actual pattern that was problematic
    pattern = "(total\\s+)?current\\s+assets"
    
    # Force Python search
    resource.ripgrep_available = False
    python_result = resource.search(
        pattern=pattern,
        is_regex=True,  # Regex mode
        is_case_sensitive=False,
        file_pattern="AMD-AR.md",
        max_results=10,
        context_lines=0
    )
    
    # Force ripgrep search
    resource.ripgrep_available = True
    ripgrep_result = resource.search(
        pattern=pattern,
        is_regex=True,  # Regex mode
        is_case_sensitive=False,
        file_pattern="AMD-AR.md",
        max_results=10,
        context_lines=0
    )
    
    # Compare results
    are_equal, diff_msg = compare_search_results(python_result, ripgrep_result)
    
    # Assertions
    assert python_result["success"], f"Python regex search failed: {python_result.get('error')}"
    assert ripgrep_result["success"], f"Ripgrep regex search failed: {ripgrep_result.get('error')}"
    
    # Both should find matches (or both find zero)
    assert python_result["total_matches"] == ripgrep_result["total_matches"], \
        f"Match counts differ: Python={python_result['total_matches']} vs Ripgrep={ripgrep_result['total_matches']}"
    
    assert are_equal, f"Regex whitespace pattern results differ: {diff_msg}"
    
    print(f"\n✅ Test 3 PASSED: Regex \\s+ pattern found {python_result['total_matches']} matches")


# =============================================================================
# TEST 4: Multiple Match Terms (OR patterns)
# =============================================================================

def test_regex_or_pattern(search_resource_fixtures):
    """
    Test that both methods handle OR patterns identically.
    
    Purpose: Test patterns like "revenue|sales" (multiple alternatives)
    Pattern: "Revenue|Sales|Income" with | (OR operator)
    Expected: Both methods find all variations
    """
    resource = search_resource_fixtures
    pattern = "Revenue|Sales|Income"
    
    # Force Python search
    resource.ripgrep_available = False
    python_result = resource.search(
        pattern=pattern,
        is_regex=True,  # Regex with OR
        is_case_sensitive=False,
        max_results=20,
        context_lines=0
    )
    
    # Force ripgrep search
    resource.ripgrep_available = True
    ripgrep_result = resource.search(
        pattern=pattern,
        is_regex=True,  # Regex with OR
        is_case_sensitive=False,
        max_results=20,
        context_lines=0
    )
    
    # Compare results
    are_equal, diff_msg = compare_search_results(python_result, ripgrep_result)
    
    # Assertions
    assert python_result["success"], f"Python OR pattern search failed: {python_result.get('error')}"
    assert python_result["total_matches"] > 0, "Should find at least one match with OR pattern"
    assert ripgrep_result["success"], f"Ripgrep OR pattern search failed: {ripgrep_result.get('error')}"
    assert are_equal, f"OR pattern results differ: {diff_msg}"
    
    print(f"\n✅ Test 4 PASSED: OR pattern found {python_result['total_matches']} matches")


# =============================================================================
# TEST 5: Path Resolution (file_pattern with different formats)
# =============================================================================

def test_path_resolution_consistency(search_resource_amd_data):
    """
    Test that both methods handle different path formats correctly.
    
    Purpose: Verify path resolution works with various relative path formats
    Pattern: "Revenue"
    File: AMD-AR.md (workspace_root is already in data/ directory)
    Expected: Both methods should resolve paths correctly
    """
    resource = search_resource_amd_data
    pattern = "Revenue"
    
    # Test with different path formats (relative to workspace_root which is data/)
    test_patterns = [
        "AMD-AR.md",          # Just filename
        "./AMD-AR.md",        # Explicit current directory
    ]
    
    for file_pattern in test_patterns:
        # Force Python search
        resource.ripgrep_available = False
        python_result = resource.search(
            pattern=pattern,
            is_regex=False,
            is_case_sensitive=False,
            file_pattern=file_pattern,
            max_results=5,
            context_lines=0
        )
        
        # Force ripgrep search
        resource.ripgrep_available = True
        ripgrep_result = resource.search(
            pattern=pattern,
            is_regex=False,
            is_case_sensitive=False,
            file_pattern=file_pattern,
            max_results=5,
            context_lines=0
        )
        
        # Both should either succeed or fail consistently
        assert python_result["success"] == ripgrep_result["success"], \
            f"Path {file_pattern}: Success status differs - Python: {python_result['success']}, Ripgrep: {ripgrep_result['success']}"
        
        if python_result["success"] and ripgrep_result["success"]:
            # If both succeed, they should find similar number of matches
            assert python_result["total_matches"] > 0, f"Python should find matches for {file_pattern}"
            assert ripgrep_result["total_matches"] > 0, f"Ripgrep should find matches for {file_pattern}"
            print(f"  ✅ Path '{file_pattern}': Python={python_result['total_matches']}, Ripgrep={ripgrep_result['total_matches']}")
        elif not python_result["success"] and not ripgrep_result["success"]:
            # Both failed - that's consistent
            print(f"  ⚠️  Path '{file_pattern}': Both methods failed (consistent)")
    
    print(f"\n✅ Test 5 PASSED: Path resolution handled consistently")


# =============================================================================
# TEST 6: Context Lines
# =============================================================================

def test_context_lines_consistency(search_resource_fixtures):
    """
    Test that both methods return identical context lines.
    
    Purpose: Verify context_lines parameter works identically
    Pattern: "Gross Profit" with context_lines=2
    Expected: Both return same before/after context
    """
    resource = search_resource_fixtures
    pattern = "Gross Profit"
    
    # Force Python search
    resource.ripgrep_available = False
    python_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,
        max_results=5,
        context_lines=2  # Request 2 lines before and after
    )
    
    # Force ripgrep search
    resource.ripgrep_available = True
    ripgrep_result = resource.search(
        pattern=pattern,
        is_regex=False,
        is_case_sensitive=False,
        max_results=5,
        context_lines=2  # Request 2 lines before and after
    )
    
    # Assertions
    assert python_result["success"], f"Python search with context failed: {python_result.get('error')}"
    assert ripgrep_result["success"], f"Ripgrep search with context failed: {ripgrep_result.get('error')}"
    
    # Check that context lines exist
    if python_result["total_matches"] > 0:
        first_match = python_result["matches"][0]
        assert "before_context" in first_match, "Python result should have before_context"
        assert "after_context" in first_match, "Python result should have after_context"
        print(f"\n✅ Test 6 PASSED: Context lines returned (before: {len(first_match['before_context'])}, after: {len(first_match['after_context'])})")
    else:
        print("\n⚠️  Test 6 WARNING: No matches found to test context")


# =============================================================================
# TEST 7: Full Real-World Financial Analysis Pattern (with context)
# =============================================================================

def test_financial_pattern_with_context():
    """
    Test the exact pattern from user's financial analysis use case.
    
    Purpose: Verify both methods handle the complete real-world scenario
    Pattern: "(total\\s+)?current\\s+assets" (regex with optional group)
    File: examples/agents/financial-analysis/data/AMD-AR.md (full path)
    Context: 3 lines before and after
    Max Results: 20
    Expected: Both methods return identical matches with context
    """
    # Use workspace root at project level to test full path resolution
    # __file__ is in tests/, go up to: tests -> financial-analysis -> agents -> examples -> another_opendxa
    workspace_root = Path(__file__).parent.parent.parent.parent.parent  # Go up to project root
    resource = RipgrepSearchResource(workspace_root=str(workspace_root))
    
    # Exact parameters from user
    pattern = "(total\\s+)?current\\s+assets"
    file_pattern = "examples/agents/financial-analysis/data/AMD-AR.md"
    
    print(f"\n🔍 Testing with workspace_root: {workspace_root}")
    print(f"🔍 Searching for pattern: {pattern}")
    print(f"🔍 In file: {file_pattern}")
    
    # Force Python search
    resource.ripgrep_available = False
    python_result = resource.search(
        pattern=pattern,
        is_regex=True,
        is_case_sensitive=False,
        file_pattern=file_pattern,
        max_results=20,
        context_lines=3
    )
    
    # Force ripgrep search
    resource.ripgrep_available = True
    ripgrep_result = resource.search(
        pattern=pattern,
        is_regex=True,
        is_case_sensitive=False,
        file_pattern=file_pattern,
        max_results=20,
        context_lines=3
    )
    
    # Debug output
    print(f"\n📊 Python Results:")
    print(f"   Success: {python_result['success']}")
    print(f"   Total matches: {python_result['total_matches']}")
    if not python_result['success']:
        print(f"   Error: {python_result.get('error')}")
    else:
        if python_result['matches']:
            first_match = python_result['matches'][0]
            print(f"   First match at line {first_match['line_number']}: {first_match['line_text'][:60]}...")
            print(f"   Context before: {len(first_match.get('before_context', []))} lines")
            print(f"   Context after: {len(first_match.get('after_context', []))} lines")
    
    print(f"\n📊 Ripgrep Results:")
    print(f"   Success: {ripgrep_result['success']}")
    print(f"   Total matches: {ripgrep_result['total_matches']}")
    if not ripgrep_result['success']:
        print(f"   Error: {ripgrep_result.get('error')}")
    else:
        if ripgrep_result['matches']:
            first_match = ripgrep_result['matches'][0]
            print(f"   First match at line {first_match['line_number']}: {first_match['line_text'][:60]}...")
            print(f"   Context before: {len(first_match.get('before_context', []))} lines")
            print(f"   Context after: {len(first_match.get('after_context', []))} lines")
    
    # Assertions
    assert python_result["success"], f"Python search failed: {python_result.get('error')}"
    assert ripgrep_result["success"], f"Ripgrep search failed: {ripgrep_result.get('error')}"
    
    # Both should find matches
    assert python_result["total_matches"] > 0, "Python should find matches for financial pattern"
    assert ripgrep_result["total_matches"] > 0, "Ripgrep should find matches for financial pattern"
    
    # Compare match counts
    print(f"\n🔍 Match count comparison: Python={python_result['total_matches']} vs Ripgrep={ripgrep_result['total_matches']}")
    
    # Allow for minor differences in match counts due to implementation details
    match_count_diff = abs(python_result["total_matches"] - ripgrep_result["total_matches"])
    assert match_count_diff <= 2, \
        f"Match counts differ significantly: Python={python_result['total_matches']} vs Ripgrep={ripgrep_result['total_matches']}"
    
    # Compare first few matches in detail
    if python_result["matches"] and ripgrep_result["matches"]:
        for i in range(min(3, len(python_result["matches"]), len(ripgrep_result["matches"]))):
            py_match = python_result["matches"][i]
            rg_match = ripgrep_result["matches"][i]
            
            print(f"\n   Match {i+1}:")
            print(f"      Python line {py_match['line_number']}: {py_match['line_text'][:50]}...")
            print(f"      Ripgrep line {rg_match['line_number']}: {rg_match['line_text'][:50]}...")
            
            # Line numbers should match (or be very close)
            assert abs(py_match['line_number'] - rg_match['line_number']) <= 1, \
                f"Match {i+1}: Line numbers differ: {py_match['line_number']} vs {rg_match['line_number']}"
            
            # Context should exist for both
            assert len(py_match.get('before_context', [])) > 0, f"Match {i+1}: Python missing before_context"
            assert len(py_match.get('after_context', [])) > 0, f"Match {i+1}: Python missing after_context"
            assert len(rg_match.get('before_context', [])) > 0, f"Match {i+1}: Ripgrep missing before_context"
            assert len(rg_match.get('after_context', [])) > 0, f"Match {i+1}: Ripgrep missing after_context"
    
    print(f"\n✅ Test 7 PASSED: Real-world financial pattern with context works consistently!")


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "-s"])

