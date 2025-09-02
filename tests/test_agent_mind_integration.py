"""
Test AgentMind Integration with World Model

This test file verifies that the AgentMind class properly integrates
with the world model functionality.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from dana.core.agent.mind.agent_mind import AgentMind
from dana.core.agent.mind.world_model import LocationContext, SystemContext, TimeContext


class TestAgentMindWorldModelIntegration:
    """Test AgentMind integration with world model."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_home = Path.home()

        # Mock home directory for testing
        # This is a simplified test - in a real scenario you'd use proper mocking
        self.test_home = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_mind_initialization_with_world_model(self):
        """Test that AgentMind properly initializes with world model."""
        agent_mind = AgentMind()

        # Check that world model is created
        assert agent_mind.world_model is not None
        assert hasattr(agent_mind.world_model, "get_current_state")
        assert hasattr(agent_mind.world_model, "get_temporal_context")
        assert hasattr(agent_mind.world_model, "get_location_context")
        assert hasattr(agent_mind.world_model, "get_system_context")

    def test_world_context_access_methods(self):
        """Test that AgentMind provides access to world context methods."""
        agent_mind = AgentMind()

        # Test world context access methods
        assert hasattr(agent_mind, "get_world_context")
        assert hasattr(agent_mind, "get_temporal_context")
        assert hasattr(agent_mind, "get_location_context")
        assert hasattr(agent_mind, "get_system_context")
        assert hasattr(agent_mind, "get_domain_knowledge")
        assert hasattr(agent_mind, "update_domain_knowledge")
        assert hasattr(agent_mind, "get_shared_patterns")
        assert hasattr(agent_mind, "add_shared_pattern")

    def test_business_logic_helper_methods(self):
        """Test that AgentMind provides business logic helper methods."""
        agent_mind = AgentMind()

        # Test business logic helper methods
        assert hasattr(agent_mind, "is_business_hours")
        assert hasattr(agent_mind, "is_holiday")
        assert hasattr(agent_mind, "get_current_season")
        assert hasattr(agent_mind, "get_time_period")
        assert hasattr(agent_mind, "get_system_health")
        assert hasattr(agent_mind, "is_system_healthy")
        assert hasattr(agent_mind, "get_available_resources")
        assert hasattr(agent_mind, "get_location_info")

    def test_resource_optimization_methods(self):
        """Test that AgentMind provides resource optimization methods."""
        agent_mind = AgentMind()

        # Test resource optimization methods
        assert hasattr(agent_mind, "should_use_lightweight_processing")
        assert hasattr(agent_mind, "get_optimal_concurrency_level")
        assert hasattr(agent_mind, "get_localization_settings")

    def test_world_model_initialization_in_initialize_mind(self):
        """Test that world model is initialized when initialize_mind is called."""
        agent_mind = AgentMind()

        # Initialize mind (this should initialize the world model)
        agent_mind.initialize_mind("test_user")

        # Check that world model has been initialized
        assert agent_mind.world_model.current_state is not None
        assert agent_mind.world_model.last_update is not None

    def test_temporal_context_integration(self):
        """Test temporal context integration."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Get temporal context
        time_context = agent_mind.get_temporal_context()

        # Verify temporal context properties
        assert isinstance(time_context, TimeContext)
        assert isinstance(time_context.current_time, datetime)
        assert isinstance(time_context.timezone, str)
        assert isinstance(time_context.is_business_hours, bool)
        assert isinstance(time_context.is_holiday, bool)
        assert isinstance(time_context.season, str)
        assert isinstance(time_context.time_period, str)

    def test_location_context_integration(self):
        """Test location context integration."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Get location context
        location_context = agent_mind.get_location_context()

        # Verify location context properties
        assert isinstance(location_context, LocationContext)
        assert isinstance(location_context.timezone, str)
        assert isinstance(location_context.country, str)
        assert isinstance(location_context.region, str)
        assert isinstance(location_context.city, str)
        assert isinstance(location_context.environment, str)
        assert isinstance(location_context.network, str)

    def test_system_context_integration(self):
        """Test system context integration."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Get system context
        system_context = agent_mind.get_system_context()

        # Verify system context properties
        assert isinstance(system_context, SystemContext)
        assert isinstance(system_context.system_load, float)
        assert isinstance(system_context.memory_usage, float)
        assert isinstance(system_context.network_status, str)
        assert isinstance(system_context.system_health, str)
        assert isinstance(system_context.maintenance_mode, bool)
        assert isinstance(system_context.last_maintenance, datetime)

    def test_business_hours_detection(self):
        """Test business hours detection through AgentMind."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Test business hours detection
        is_business_hours = agent_mind.is_business_hours()
        assert isinstance(is_business_hours, bool)

        # Test holiday detection
        is_holiday = agent_mind.is_holiday()
        assert isinstance(is_holiday, bool)

        # Test season detection
        season = agent_mind.get_current_season()
        assert isinstance(season, str)
        assert season in ["winter", "spring", "summer", "autumn"]

        # Test time period detection
        time_period = agent_mind.get_time_period()
        assert isinstance(time_period, str)
        assert time_period in ["morning", "afternoon", "evening", "night"]

    def test_system_health_detection(self):
        """Test system health detection through AgentMind."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Test system health detection
        system_health = agent_mind.get_system_health()
        assert isinstance(system_health, str)
        assert system_health in ["healthy", "degraded", "critical", "unknown"]

        # Test system health boolean check
        is_healthy = agent_mind.is_system_healthy()
        assert isinstance(is_healthy, bool)

        # Test available resources
        resources = agent_mind.get_available_resources()
        assert isinstance(resources, dict)

    def test_location_info_integration(self):
        """Test location info integration through AgentMind."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Get location info
        location_info = agent_mind.get_location_info()

        # Verify location info structure
        assert isinstance(location_info, dict)
        expected_keys = ["country", "region", "city", "timezone", "environment", "network"]
        for key in expected_keys:
            assert key in location_info
            assert isinstance(location_info[key], str)

    def test_resource_optimization_integration(self):
        """Test resource optimization through AgentMind."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Test lightweight processing detection
        should_use_lightweight = agent_mind.should_use_lightweight_processing()
        assert isinstance(should_use_lightweight, bool)

        # Test optimal concurrency level
        concurrency_level = agent_mind.get_optimal_concurrency_level()
        assert isinstance(concurrency_level, int)
        assert concurrency_level >= 1

        # Test localization settings
        localization_settings = agent_mind.get_localization_settings()
        assert isinstance(localization_settings, dict)
        expected_keys = ["date_format", "time_format", "currency", "language"]
        for key in expected_keys:
            assert key in localization_settings
            assert isinstance(localization_settings[key], str)

    def test_domain_knowledge_integration(self):
        """Test domain knowledge integration through AgentMind."""
        agent_mind = AgentMind()
        agent_mind.initialize_mind("test_user")

        # Test getting domain knowledge
        knowledge = agent_mind.get_domain_knowledge("test_domain")
        # Should return None for non-existent domain
        assert knowledge is None

        # Test shared patterns
        patterns = agent_mind.get_shared_patterns()
        assert isinstance(patterns, dict)

        # Test adding shared patterns
        test_pattern = {"test_key": "test_value", "timestamp": datetime.now().isoformat()}
        agent_mind.add_shared_pattern("test_type", "test_id", test_pattern)

        # Verify pattern was added
        patterns = agent_mind.get_shared_patterns("test_type")
        assert "test_id" in patterns
        assert patterns["test_id"]["test_key"] == "test_value"


if __name__ == "__main__":
    # Run basic integration tests
    print("Testing AgentMind World Model Integration...")

    test_integration = TestAgentMindWorldModelIntegration()
    test_integration.setup_method()

    try:
        test_integration.test_agent_mind_initialization_with_world_model()
        print("✅ AgentMind initialization test passed")

        test_integration.test_world_context_access_methods()
        print("✅ World context access methods test passed")

        test_integration.test_business_logic_helper_methods()
        print("✅ Business logic helper methods test passed")

        test_integration.test_resource_optimization_methods()
        print("✅ Resource optimization methods test passed")

        test_integration.test_world_model_initialization_in_initialize_mind()
        print("✅ World model initialization test passed")

        test_integration.test_temporal_context_integration()
        print("✅ Temporal context integration test passed")

        test_integration.test_location_context_integration()
        print("✅ Location context integration test passed")

        test_integration.test_system_context_integration()
        print("✅ System context integration test passed")

        test_integration.test_business_hours_detection()
        print("✅ Business hours detection test passed")

        test_integration.test_system_health_detection()
        print("✅ System health detection test passed")

        test_integration.test_location_info_integration()
        print("✅ Location info integration test passed")

        test_integration.test_resource_optimization_integration()
        print("✅ Resource optimization integration test passed")

        test_integration.test_domain_knowledge_integration()
        print("✅ Domain knowledge integration test passed")

        print("\n🎉 All AgentMind World Model integration tests passed!")

    finally:
        test_integration.teardown_method()
