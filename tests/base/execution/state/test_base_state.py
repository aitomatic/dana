"""Unit tests for BaseState registry functionality."""

import pytest
from pydantic import BaseModel
from opendxa.base.execution.state.base_state import BaseState

# --- Fixtures ---

@pytest.fixture
def state() -> BaseState:
    """Provides a fresh BaseState instance for each test."""
    return BaseState()

# --- Test Pydantic Model ---

class SampleModel(BaseModel):
    id: int
    name: str

# --- Tests for Registry Access ---

def test_registry_set_get_simple(state: BaseState):
    state.registry["key1"] = "value1"
    assert state.registry["key1"] == "value1"
    assert state.registry.get("key1") == "value1"

def test_registry_set_get_dot_notation_key(state: BaseState):
    key = "a.b.c"
    state.registry[key] = 123
    assert state.registry[key] == 123
    assert state.registry.get(key) == 123
    # Ensure no nesting occurred
    assert "a" not in state.registry

def test_registry_overwrite_existing(state: BaseState):
    state.registry["key1"] = "value1"
    state.registry["key1"] = "value2"
    assert state.registry["key1"] == "value2"

def test_registry_different_value_types(state: BaseState):
    model_instance = SampleModel(id=1, name="test")
    state.registry["k_int"] = 1
    state.registry["k_bool"] = False
    state.registry["k_list"] = [1, 2]
    state.registry["k_dict"] = {"sub": "val"}
    state.registry["k_model"] = model_instance

    assert state.registry["k_int"] == 1
    assert state.registry["k_bool"] is False
    assert state.registry["k_list"] == [1, 2]
    assert state.registry["k_dict"] == {"sub": "val"}
    assert state.registry["k_model"] is model_instance
    assert state.registry.get("k_model").name == "test"

def test_registry_get_nonexistent_default_none(state: BaseState):
    assert state.registry.get("nonexistent") is None

def test_registry_get_nonexistent_custom_default(state: BaseState):
    assert state.registry.get("nonexistent", "fallback") == "fallback"

def test_registry_get_nonexistent_raises_keyerror(state: BaseState):
    with pytest.raises(KeyError):
        _ = state.registry["nonexistent"]

def test_registry_delete_simple_exists(state: BaseState):
    state.registry["key1"] = "value1"
    state.registry["key2"] = "value2"
    del state.registry["key1"]
    assert "key1" not in state.registry
    assert state.registry == {"key2": "value2"}

def test_registry_delete_dot_notation_key_exists(state: BaseState):
    key = "a.b.c"
    state.registry[key] = 123
    state.registry["other"] = 456
    del state.registry[key]
    assert key not in state.registry
    assert state.registry == {"other": 456}

def test_registry_delete_nonexistent_raises_keyerror(state: BaseState):
    with pytest.raises(KeyError):
        del state.registry["nonexistent"]

def test_registry_standard_dict_behavior(state: BaseState):
    # Keys can be empty or contain unusual characters (standard dict)
    state.registry[""] = "empty_key_value"
    state.registry["a..b"] = "double_dot_value"
    assert state.registry.get("") == "empty_key_value"
    assert state.registry.get("a..b") == "double_dot_value"
    del state.registry[""]
    assert "" not in state.registry

# --- Tests for BaseState Methods (reset/update) ---

def test_reset_clears_registry_and_artifacts(state: BaseState):
    state.registry["reg_key"] = "reg_val"
    state.artifacts["art_key"] = "art_val"
    assert state.registry  # Not empty
    assert state.artifacts  # Not empty
    
    state.reset()
    
    assert not state.registry  # Is empty dict
    assert not state.artifacts  # Is empty dict

def test_update_modifies_top_level_fields_only(state: BaseState):
    state.registry["reg_key"] = "original_reg"
    state.artifacts["art_key"] = "original_art"
    
    updates = {
        "registry": {"new_key": "new_val"},  # Should NOT replace the registry
        "artifacts": {"new_art": "new_art_val"},  # Should NOT replace artifacts
        "nonexistent_field": 123  # Should be ignored
    }
    
    state.update(updates)
    
    # Check that registry/artifacts were NOT replaced, only their contents would change
    # if they were explicitly updated via state.registry.update etc.
    # In this case, the update method ignores dict values for existing fields.
    assert state.registry == {"reg_key": "original_reg"} 
    assert state.artifacts == {"art_key": "original_art"}

def test_state_update_does_not_affect_registry(state: BaseState):
    """Tests that BaseState.update affects only specified top-level non-dict fields."""
    state.registry["a"] = 1
    state.artifacts["initial_art"] = "value"  # Add initial artifact value
    
    # Attempt to update artifacts via BaseState.update (which should be skipped)
    state.update({"artifacts": {"b": 2}})
    
    # Verify registry is untouched
    assert state.registry == {"a": 1}
    # Verify artifacts is also untouched by the update call (because update skips dict fields)
    assert state.artifacts == {"initial_art": "value"} 