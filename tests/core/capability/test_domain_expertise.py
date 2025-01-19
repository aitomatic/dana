"""Tests for DomainExpertise class."""

from pathlib import Path
import pytest
from dxa.core.capability.domain_expertise import DomainExpertise

def test_domain_expertise_basic():
    """Test basic DomainExpertise functionality."""
    expertise = DomainExpertise(
        name="planning",
        description="Planning system expertise",
        capabilities=["workflow planning", "task decomposition"],
        keywords=["plan", "sequence", "workflow"],
        requirements=["objective", "constraints"],
        example_queries=["Plan a sequence of steps to achieve X"]
    )
    
    assert expertise.name == "planning"
    assert "workflow planning" in expertise.capabilities
    assert "plan" in expertise.keywords
    assert len(expertise.notes) == 0

def test_domain_expertise_add_notes_from_file():
    """Test adding notes from README file."""
    # Create expertise instance
    expertise = DomainExpertise(
        name="planning",
        description="Planning system expertise"
    )
    
    # Get path to root README.md relative to test file
    test_dir = Path(__file__).parent
    readme_path = test_dir.parent.parent.parent / "README.md"
    
    # Add README content as note
    expertise.add_notes_from_file(readme_path)
    
    # Verify note was added
    assert len(expertise.notes) == 1
    readme_note = next(iter(expertise.notes))
    # Update assertions to match content from root README
    assert "DXA" in readme_note  # Assuming root README mentions DXA
    assert "Aitomatic" in readme_note  # Assuming root README mentions company name

def test_domain_expertise_empty_notes():
    """Test handling of empty notes."""
    expertise = DomainExpertise(name="test")
    
    # Empty string should not be added
    expertise.add_note("")
    expertise.add_note("   ")
    assert len(expertise.notes) == 0
    
    # Valid note should be added
    expertise.add_note("Valid note")
    assert len(expertise.notes) == 1
    assert "Valid note" in expertise.notes

def test_domain_expertise_duplicate_notes():
    """Test handling of duplicate notes."""
    expertise = DomainExpertise(name="test")
    
    # Add same note multiple times
    expertise.add_note("Note 1")
    expertise.add_note("Note 1")
    expertise.add_note("Note 1")
    
    # Should only be stored once
    assert len(expertise.notes) == 1
    assert "Note 1" in expertise.notes

def test_domain_expertise_long_description():
    """Test long_description property."""
    expertise = DomainExpertise(
        name="test",
        description="Test description",
        capabilities=["cap1", "cap2"],
        keywords=[],  # Empty list should be omitted
        requirements=["req1"],
        example_queries=["query1"]
    )
    
    desc = expertise.long_description
    assert "Domain: test" in desc
    assert "Description: Test description" in desc
    assert "Capabilities:" in desc
    assert "- cap1" in desc
    assert "Keywords:" not in desc  # Empty section should be omitted
    assert "Requirements:" in desc
    assert "Example Queries:" in desc

def test_domain_expertise_file_not_found():
    """Test error handling for non-existent files."""
    expertise = DomainExpertise(name="test")
    
    with pytest.raises(FileNotFoundError):
        expertise.add_notes_from_file("nonexistent.txt")
