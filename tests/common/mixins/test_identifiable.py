"""Tests for the Identifiable mixin."""

import uuid
import pytest
from opendxa.common.mixins.identifiable import Identifiable

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
class TestIdentifiable:
    """Test suite for the Identifiable mixin."""
    
    def test_default_initialization(self):
        """Test initialization with no parameters."""
        obj = Identifiable()
        assert isinstance(obj.id, str)
        assert uuid.UUID(obj.id)  # Verify it's a valid UUID
        assert obj.name is not None
        assert obj.name.startswith(obj.__class__.__name__)
        assert obj.description is None
    
    def test_initialization_with_name(self):
        """Test initialization with name parameter."""
        obj = Identifiable(name="test_name")
        assert isinstance(obj.id, str)
        assert uuid.UUID(obj.id)
        assert obj.name == "test_name"
        assert obj.description is None
    
    def test_initialization_with_description(self):
        """Test initialization with description parameter."""
        obj = Identifiable(description="test_description")
        assert isinstance(obj.id, str)
        assert uuid.UUID(obj.id)
        assert obj.name is not None
        assert obj.name.startswith(obj.__class__.__name__)
        assert obj.description == "test_description"
    
    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        obj = Identifiable(name="test_name", description="test_description")
        assert isinstance(obj.id, str)
        assert uuid.UUID(obj.id)
        assert obj.name == "test_name"
        assert obj.description == "test_description"
    
    def test_unique_ids(self):
        """Test that different instances have different IDs."""
        obj1 = Identifiable()
        obj2 = Identifiable()
        assert obj1.id != obj2.id
    
    def test_id_mutability(self):
        """Test that the ID can be changed after initialization."""
        obj = Identifiable()
        original_id = obj.id
        obj.id = "new_id"
        assert obj.id == "new_id"
        obj.id = original_id
        assert obj.id == original_id