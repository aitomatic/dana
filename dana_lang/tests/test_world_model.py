"""
Test World Model Functionality

This test file verifies that the basic world model components work correctly.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from dana.core.agent.mind.models.world_model import (
    DomainKnowledge,
    LocationContext,
    LocationProvider,
    SystemContext,
    SystemProvider,
    TimeContext,
    TimeProvider,
    WorldModel,
    WorldState,
)


class TestTimeContext:
    """Test TimeContext functionality."""

    def test_time_context_creation(self):
        """Test creating a TimeContext instance."""
        now = datetime.now()
        time_context = TimeContext(current_time=now, timezone="UTC")

        assert time_context.current_time == now
        assert time_context.timezone == "UTC"
        assert time_context.day_of_week == now.strftime("%A")
        assert isinstance(time_context.is_business_hours, bool)
        assert isinstance(time_context.is_holiday, bool)
        assert time_context.season in ["winter", "spring", "summer", "autumn"]
        assert time_context.time_period in ["morning", "afternoon", "evening", "night"]

    def test_business_hours_detection(self):
        """Test business hours detection."""
        # Test business hours (Monday 10 AM)
        business_time = datetime(2024, 1, 22, 10, 0, 0)  # Monday 10 AM
        time_context = TimeContext(current_time=business_time, timezone="UTC")
        assert time_context.is_business_hours is True

        # Test after hours (Monday 8 PM)
        after_hours = datetime(2024, 1, 22, 20, 0, 0)  # Monday 8 PM
        time_context = TimeContext(current_time=after_hours, timezone="UTC")
        assert time_context.is_business_hours is False

        # Test weekend (Saturday 10 AM)
        weekend = datetime(2024, 1, 27, 10, 0, 0)  # Saturday 10 AM
        time_context = TimeContext(current_time=weekend, timezone="UTC")
        assert time_context.is_business_hours is False

    def test_holiday_detection(self):
        """Test holiday detection."""
        # Test New Year's Day
        new_year = datetime(2024, 1, 1, 12, 0, 0)
        time_context = TimeContext(current_time=new_year, timezone="UTC")
        assert time_context.is_holiday is True

        # Test regular day
        regular_day = datetime(2024, 1, 15, 12, 0, 0)
        time_context = TimeContext(current_time=regular_day, timezone="UTC")
        assert time_context.is_holiday is False

    def test_season_detection(self):
        """Test season detection."""
        # Test winter
        winter = datetime(2024, 1, 15, 12, 0, 0)
        time_context = TimeContext(current_time=winter, timezone="UTC")
        assert time_context.season == "winter"

        # Test spring
        spring = datetime(2024, 4, 15, 12, 0, 0)
        time_context = TimeContext(current_time=spring, timezone="UTC")
        assert time_context.season == "spring"

        # Test summer
        summer = datetime(2024, 7, 15, 12, 0, 0)
        time_context = TimeContext(current_time=summer, timezone="UTC")
        assert time_context.season == "summer"

        # Test autumn
        autumn = datetime(2024, 10, 15, 12, 0, 0)
        time_context = TimeContext(current_time=autumn, timezone="UTC")
        assert time_context.season == "autumn"

    def test_time_period_detection(self):
        """Test time period detection."""
        # Test morning
        morning = datetime(2024, 1, 15, 8, 0, 0)
        time_context = TimeContext(current_time=morning, timezone="UTC")
        assert time_context.time_period == "morning"

        # Test afternoon
        afternoon = datetime(2024, 1, 15, 14, 0, 0)
        time_context = TimeContext(current_time=afternoon, timezone="UTC")
        assert time_context.time_period == "afternoon"

        # Test evening
        evening = datetime(2024, 1, 15, 19, 0, 0)
        time_context = TimeContext(current_time=evening, timezone="UTC")
        assert time_context.time_period == "evening"

        # Test night
        night = datetime(2024, 1, 15, 23, 0, 0)
        time_context = TimeContext(current_time=night, timezone="UTC")
        assert time_context.time_period == "night"


class TestLocationContext:
    """Test LocationContext functionality."""

    def test_location_context_creation(self):
        """Test creating a LocationContext instance."""
        location = LocationContext(
            coordinates=(37.7749, -122.4194), timezone="America/Los_Angeles", country="US", region="CA", city="San Francisco"
        )

        assert location.coordinates == (37.7749, -122.4194)
        assert location.timezone == "America/Los_Angeles"
        assert location.country == "US"
        assert location.region == "CA"
        assert location.city == "San Francisco"
        assert location.environment == "office"  # Default
        assert location.network == "local"  # Default

    def test_location_context_defaults(self):
        """Test LocationContext with default values."""
        location = LocationContext()

        assert location.coordinates is None
        assert location.timezone == "UTC"
        assert location.country == "Unknown"
        assert location.region == "Unknown"
        assert location.city == "Unknown"
        assert location.environment == "office"
        assert location.network == "local"


class TestSystemContext:
    """Test SystemContext functionality."""

    def test_system_context_creation(self):
        """Test creating a SystemContext instance."""
        system = SystemContext(system_load=0.5, memory_usage=65.2, network_status="connected", system_health="healthy")

        assert system.system_load == 0.5
        assert system.memory_usage == 65.2
        assert system.network_status == "connected"
        assert system.system_health == "healthy"
        assert system.maintenance_mode is False
        assert isinstance(system.last_maintenance, datetime)

    def test_system_context_defaults(self):
        """Test SystemContext with default values."""
        system = SystemContext()

        assert system.system_load == 0.0
        assert system.memory_usage == 0.0
        assert system.network_status == "unknown"
        assert system.system_health == "unknown"
        assert system.maintenance_mode is False
        assert isinstance(system.last_maintenance, datetime)


class TestDomainKnowledge:
    """Test DomainKnowledge functionality."""

    def test_domain_knowledge_creation(self):
        """Test creating a DomainKnowledge instance."""
        knowledge = DomainKnowledge(
            domain="semiconductor",
            topics=["inspection", "quality_control"],
            expertise_level="intermediate",
            last_updated=datetime.now(),
            confidence_score=0.8,
            sources=["training_data", "user_feedback"],
        )

        assert knowledge.domain == "semiconductor"
        assert knowledge.topics == ["inspection", "quality_control"]
        assert knowledge.expertise_level == "intermediate"
        assert knowledge.confidence_score == 0.8
        assert knowledge.sources == ["training_data", "user_feedback"]
        assert isinstance(knowledge.patterns, dict)


class TestWorldState:
    """Test WorldState functionality."""

    def test_world_state_creation(self):
        """Test creating a WorldState instance."""
        now = datetime.now()
        time_context = TimeContext(current_time=now, timezone="UTC")
        location_context = LocationContext()
        system_context = SystemContext()

        world_state = WorldState(timestamp=now, time_context=time_context, location_context=location_context, system_context=system_context)

        assert world_state.timestamp == now
        assert world_state.time_context == time_context
        assert world_state.location_context == location_context
        assert world_state.system_context == system_context
        assert isinstance(world_state.domain_knowledge, dict)
        assert isinstance(world_state.shared_patterns, dict)
        assert isinstance(world_state.global_events, list)
        assert isinstance(world_state.system_alerts, list)


class TestWorldModel:
    """Test WorldModel functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_home = Path.home()

        # Mock home directory
        self.mock_home = Path(self.temp_dir)
        # This is a simplified test - in a real scenario you'd use proper mocking

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_world_model_creation(self):
        """Test creating a WorldModel instance."""
        world_model = WorldModel()

        assert world_model.world_dir is not None
        assert world_model.current_state is None
        assert world_model.last_update is None
        assert len(world_model.state_providers) == 5  # time, location, system, domain, patterns
        assert "time" in world_model.state_providers
        assert "location" in world_model.state_providers
        assert "system" in world_model.state_providers
        assert "domain" in world_model.state_providers
        assert "patterns" in world_model.state_providers

    def test_time_provider(self):
        """Test TimeProvider functionality."""
        provider = TimeProvider()
        time_context = provider.get_current_state()

        assert isinstance(time_context, TimeContext)
        assert isinstance(time_context.current_time, datetime)
        assert isinstance(time_context.timezone, str)
        assert isinstance(time_context.is_business_hours, bool)
        assert isinstance(time_context.is_holiday, bool)
        assert isinstance(time_context.season, str)
        assert isinstance(time_context.time_period, str)

    def test_location_provider(self):
        """Test LocationProvider functionality."""
        provider = LocationProvider()
        location_context = provider.get_current_state()

        assert isinstance(location_context, LocationContext)
        assert isinstance(location_context.timezone, str)
        assert isinstance(location_context.country, str)
        assert isinstance(location_context.region, str)
        assert isinstance(location_context.city, str)
        assert isinstance(location_context.environment, str)
        assert isinstance(location_context.network, str)

    def test_system_provider(self):
        """Test SystemProvider functionality."""
        provider = SystemProvider()
        system_context = provider.get_current_state()

        assert isinstance(system_context, SystemContext)
        assert isinstance(system_context.system_load, float)
        assert isinstance(system_context.memory_usage, float)
        assert isinstance(system_context.network_status, str)
        assert isinstance(system_context.system_health, str)
        assert isinstance(system_context.maintenance_mode, bool)
        assert isinstance(system_context.last_maintenance, datetime)


if __name__ == "__main__":
    # Run basic tests
    print("Testing TimeContext...")
    test_time = TestTimeContext()
    test_time.test_time_context_creation()
    test_time.test_business_hours_detection()
    test_time.test_holiday_detection()
    test_time.test_season_detection()
    test_time.test_time_period_detection()

    print("Testing LocationContext...")
    test_location = TestLocationContext()
    test_location.test_location_context_creation()
    test_location.test_location_context_defaults()

    print("Testing SystemContext...")
    test_system = TestSystemContext()
    test_system.test_system_context_creation()
    test_system.test_system_context_defaults()

    print("Testing DomainKnowledge...")
    test_knowledge = TestDomainKnowledge()
    test_knowledge.test_domain_knowledge_creation()

    print("Testing WorldState...")
    test_world_state = TestWorldState()
    test_world_state.test_world_state_creation()

    print("Testing WorldModel...")
    test_world_model = TestWorldModel()
    test_world_model.test_world_model_creation()
    test_world_model.test_time_provider()
    test_world_model.test_location_provider()
    test_world_model.test_system_provider()

    print("All basic tests passed!")
