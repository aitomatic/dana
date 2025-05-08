"""Tests for the Registerable mixin."""

import pytest

from opendxa.common.mixins.registerable import Registerable


# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
class TestRegisterable:
    """Test suite for the Registerable mixin."""

    def setup_method(self):
        """Clear the registry before each test."""
        Registerable._registry.clear()

    def test_add_to_registry(self):
        """Test adding an object to the registry."""

        class TestObject(Registerable):
            def __init__(self, the_id):
                super().__init__()
                self.id = the_id

        obj = TestObject("test1")
        obj.add_to_registry()
        assert "test1" in Registerable._registry
        assert Registerable._registry["test1"] is obj

    def test_remove_from_registry(self):
        """Test removing an object from the registry."""

        class TestObject(Registerable):
            def __init__(self, the_id):
                super().__init__()
                self.id = the_id

        obj = TestObject("test1")
        obj.add_to_registry()
        obj.remove_from_registry()
        assert "test1" not in Registerable._registry

    def test_get_from_registry(self):
        """Test retrieving an object from the registry."""

        class TestObject(Registerable):
            def __init__(self, the_id):
                super().__init__()
                self.id = the_id

        obj = TestObject("test1")
        obj.add_to_registry()
        retrieved = Registerable.get_from_registry("test1")
        assert retrieved is obj

    def test_get_nonexistent_object(self):
        """Test error when getting a non-existent object."""
        with pytest.raises(ValueError, match="Object nonexistent not found in registry"):
            Registerable.get_from_registry("nonexistent")

    def test_remove_nonexistent_object(self):
        """Test error when removing a non-existent object."""
        with pytest.raises(ValueError, match="Object nonexistent not found in registry"):
            Registerable.remove_object_from_registry("nonexistent")

    def test_duplicate_id_registration(self):
        """Test that registering an object with an existing ID overwrites the old one."""

        class TestObject(Registerable):
            def __init__(self, the_id):
                super().__init__()
                self.id = the_id

        obj1 = TestObject("test1")
        obj2 = TestObject("test1")
        obj1.add_to_registry()
        obj2.add_to_registry()
        assert Registerable._registry["test1"] is obj2

    def test_multiple_classes_in_registry(self):
        """Test that different classes can coexist in the same registry."""

        class TestObject1(Registerable):
            def __init__(self, the_id):
                super().__init__()
                self.id = the_id

        class TestObject2(Registerable):
            def __init__(self, the_id):
                super().__init__()
                self.id = the_id

        obj1 = TestObject1("test1")
        obj2 = TestObject2("test2")
        obj1.add_to_registry()
        obj2.add_to_registry()
        print(obj1)
        assert Registerable._registry["test1"] is obj1
        assert Registerable._registry["test2"] is obj2
