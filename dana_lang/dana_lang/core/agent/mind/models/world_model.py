"""
World Model Implementation

Provides agents with fundamental awareness of the world around them,
including temporal, spatial, and contextual information.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class TimeContext:
    """Current time and temporal context."""

    current_time: datetime
    timezone: str
    day_of_week: str = field(init=False)
    is_business_hours: bool = field(init=False)
    is_holiday: bool = field(init=False)
    season: str = field(init=False)
    time_period: str = field(init=False)  # "morning", "afternoon", "evening", "night"

    def __post_init__(self):
        self.day_of_week = self.current_time.strftime("%A")
        self.is_business_hours = self._check_business_hours()
        self.is_holiday = self._check_holiday()
        self.season = self._determine_season()
        self.time_period = self._determine_time_period()

    def _check_business_hours(self) -> bool:
        """Check if current time is during business hours."""
        hour = self.current_time.hour
        return 9 <= hour <= 17 and self.current_time.weekday() < 5

    def _check_holiday(self) -> bool:
        """Check if current date is a holiday."""
        # Basic holiday checking - could be enhanced with holiday API
        holidays = [
            (1, 1),  # New Year's Day
            (7, 4),  # Independence Day
            (12, 25),  # Christmas
        ]
        return (self.current_time.month, self.current_time.day) in holidays

    def _determine_season(self) -> str:
        """Determine current season."""
        month = self.current_time.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"

    def _determine_time_period(self) -> str:
        """Determine time period of day."""
        hour = self.current_time.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"


@dataclass
class LocationContext:
    """Location and environmental context."""

    coordinates: tuple[float, float] | None = None  # lat, lon
    timezone: str = "UTC"
    country: str = "Unknown"
    region: str = "Unknown"
    city: str = "Unknown"
    environment: str = "office"  # "office", "home", "mobile", "cloud"
    network: str = "local"  # "local", "vpn", "public", "corporate"

    def __post_init__(self):
        if self.coordinates:
            # Try to get timezone from coordinates if not set
            if self.timezone == "UTC":
                self.timezone = self._get_timezone_from_coordinates()

    def _get_timezone_from_coordinates(self) -> str:
        """Get timezone from coordinates."""
        # This is a placeholder - in a real implementation, you'd call a timezone API
        # For now, return UTC as fallback
        return "UTC"


@dataclass
class SystemContext:
    """Current system state and health."""

    system_load: float = 0.0
    memory_usage: float = 0.0
    network_status: str = "unknown"
    available_resources: dict[str, Any] = field(default_factory=dict)
    system_health: str = "unknown"  # "healthy", "degraded", "critical"
    maintenance_mode: bool = False
    last_maintenance: datetime = field(default_factory=datetime.now)


@dataclass
class DomainKnowledge:
    """Domain-specific expertise and knowledge."""

    domain: str
    topics: list[str]
    expertise_level: str  # "beginner", "intermediate", "advanced", "expert"
    last_updated: datetime
    confidence_score: float
    sources: list[str]
    patterns: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldState:
    """Current snapshot of world state."""

    timestamp: datetime
    time_context: TimeContext
    location_context: LocationContext
    system_context: SystemContext
    domain_knowledge: dict[str, DomainKnowledge] = field(default_factory=dict)
    shared_patterns: dict[str, Any] = field(default_factory=dict)
    global_events: list[str] = field(default_factory=list)
    system_alerts: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


class StateProvider(ABC):
    """Abstract base class for state providers."""

    @abstractmethod
    def get_current_state(self) -> Any:
        """Get current state from this provider."""
        pass

    def get_cached_state(self) -> Any:
        """Get cached state from this provider."""
        # Default implementation returns None
        return None


class TimeProvider(StateProvider):
    """Provides current time and temporal context."""

    def get_current_state(self) -> TimeContext:
        """Get current temporal context."""
        now = datetime.now()
        return TimeContext(
            current_time=now,
            timezone=self._get_system_timezone(),
        )

    def _get_system_timezone(self) -> str:
        """Get system timezone."""
        try:
            import time

            return time.tzname[time.daylight]
        except Exception:
            return "UTC"

    def _check_business_hours(self, dt: datetime) -> bool:
        """Check if current time is during business hours."""
        hour = dt.hour
        return 9 <= hour <= 17 and dt.weekday() < 5

    def _check_holiday(self, dt: datetime) -> bool:
        """Check if current date is a holiday."""
        # Basic holiday checking - could be enhanced with holiday API
        holidays = [
            (1, 1),  # New Year's Day
            (7, 4),  # Independence Day
            (12, 25),  # Christmas
        ]
        return (dt.month, dt.day) in holidays

    def _determine_season(self, dt: datetime) -> str:
        """Determine current season."""
        month = dt.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"

    def _determine_time_period(self, dt: datetime) -> str:
        """Determine time period of day."""
        hour = dt.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"


class LocationProvider(StateProvider):
    """Provides location and environmental context."""

    def get_current_state(self) -> LocationContext:
        """Get current location context."""
        # Try to get location from various sources
        coordinates = self._get_coordinates()
        timezone = self._get_timezone_from_coordinates(coordinates)

        return LocationContext(
            coordinates=coordinates,
            timezone=timezone,
            country=self._get_country(coordinates),
            region=self._get_region(coordinates),
            city=self._get_city(coordinates),
            environment=self._determine_environment(),
            network=self._determine_network(),
        )

    def _get_coordinates(self) -> tuple[float, float] | None:
        """Get current coordinates from available sources."""
        # Try IP geolocation first
        try:
            import requests

            response = requests.get("https://ipapi.co/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                lat = data.get("latitude")
                lon = data.get("longitude")
                if lat is not None and lon is not None:
                    return (float(lat), float(lon))
        except Exception:
            pass

        # Fallback to system timezone
        return None

    def _get_timezone_from_coordinates(self, coords: tuple[float, float] | None) -> str:
        """Get timezone from coordinates."""
        if coords:
            try:
                import requests

                lat, lon = coords
                # This is a placeholder URL - in a real implementation, you'd use a real timezone API
                response = requests.get(f"https://timezone-api.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("timezone", "UTC")
            except Exception:
                pass

        # Fallback to system timezone
        try:
            import time

            return time.tzname[time.daylight]
        except Exception:
            return "UTC"

    def _get_country(self, coords: tuple[float, float] | None) -> str:
        """Get country from coordinates."""
        if coords:
            try:
                import requests

                lat, lon = coords
                # This is a placeholder URL - in a real implementation, you'd use a real geocoding API
                response = requests.get(f"https://reverse-geocode.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("country", "Unknown")
            except Exception:
                pass

        return "Unknown"

    def _get_region(self, coords: tuple[float, float] | None) -> str:
        """Get region from coordinates."""
        if coords:
            try:
                import requests

                lat, lon = coords
                # This is a placeholder URL - in a real implementation, you'd use a real geocoding API
                response = requests.get(f"https://reverse-geocode.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("region", "Unknown")
            except Exception:
                pass

        return "Unknown"

    def _get_city(self, coords: tuple[float, float] | None) -> str:
        """Get city from coordinates."""
        if coords:
            try:
                import requests

                lat, lon = coords
                # This is a placeholder URL - in a real implementation, you'd use a real geocoding API
                response = requests.get(f"https://reverse-geocode.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("city", "Unknown")
            except Exception:
                pass

        return "Unknown"

    def _determine_environment(self) -> str:
        """Determine current environment."""
        # Could be enhanced with environment detection
        return "office"  # Default assumption

    def _determine_network(self) -> str:
        """Determine current network type."""
        # Could be enhanced with network detection
        return "local"  # Default assumption


class SystemProvider(StateProvider):
    """Provides system state and health information."""

    def get_current_state(self) -> SystemContext:
        """Get current system context."""
        return SystemContext(
            system_load=self._get_system_load(),
            memory_usage=self._get_memory_usage(),
            network_status=self._get_network_status(),
            available_resources=self._get_available_resources(),
            system_health=self._determine_system_health(),
            maintenance_mode=self._check_maintenance_mode(),
            last_maintenance=self._get_last_maintenance(),
        )

    def _get_system_load(self) -> float:
        """Get current system load."""
        try:
            import psutil

            return psutil.getloadavg()[0]  # 1-minute load average
        except Exception:
            return 0.0

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            return memory.percent
        except Exception:
            return 0.0

    def _get_network_status(self) -> str:
        """Get current network status."""
        try:
            import psutil

            net_io = psutil.net_io_counters()
            if net_io.bytes_sent > 0 or net_io.bytes_recv > 0:
                return "connected"
            else:
                return "disconnected"
        except Exception:
            return "unknown"

    def _get_available_resources(self) -> dict[str, Any]:
        """Get available system resources."""
        resources = {}

        try:
            import psutil

            # CPU info
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            resources["cpu"] = {"count": cpu_count, "usage_percent": cpu_percent, "available": cpu_count * (100 - cpu_percent) / 100}

            # Memory info
            memory = psutil.virtual_memory()
            resources["memory"] = {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "usage_percent": memory.percent,
            }

            # Disk info
            disk = psutil.disk_usage("/")
            resources["disk"] = {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "usage_percent": (disk.used / disk.total) * 100,
            }

        except Exception:
            pass

        return resources

    def _determine_system_health(self) -> str:
        """Determine overall system health."""
        try:
            import psutil

            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return "critical"
            elif memory.percent > 80:
                return "degraded"

            # Check disk usage
            disk = psutil.disk_usage("/")
            disk_usage = (disk.used / disk.total) * 100
            if disk_usage > 95:
                return "critical"
            elif disk_usage > 90:
                return "degraded"

            return "healthy"

        except Exception:
            return "unknown"

    def _check_maintenance_mode(self) -> bool:
        """Check if system is in maintenance mode."""
        # Could check for maintenance flag file or database setting
        return False

    def _get_last_maintenance(self) -> datetime:
        """Get timestamp of last maintenance."""
        # Could read from maintenance log or database
        return datetime.now() - timedelta(days=7)  # Default: 1 week ago


class DomainKnowledgeProvider(StateProvider):
    """Provides domain knowledge information."""

    def __init__(self):
        self.world_dir = Path("~/.models/world").expanduser()
        self.domain_dir = self.world_dir / "domain_knowledge"

    def get_current_state(self) -> dict[str, DomainKnowledge]:
        """Get current domain knowledge."""
        knowledge = {}

        if self.domain_dir.exists():
            for domain_file in self.domain_dir.glob("*.json"):
                try:
                    with open(domain_file) as f:
                        data = json.load(f)
                        domain_name = domain_file.stem
                        knowledge[domain_name] = DomainKnowledge(**data)
                except Exception:
                    # Skip corrupted files
                    continue

        return knowledge


class SharedPatternsProvider(StateProvider):
    """Provides shared patterns information."""

    def __init__(self):
        self.world_dir = Path("~/.models/world").expanduser()
        self.patterns_file = self.world_dir / "shared_patterns.json"

    def get_current_state(self) -> dict[str, Any]:
        """Get current shared patterns."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}


class WorldModel:
    """Manages world state and shared knowledge."""

    def __init__(self):
        self.world_dir = Path("~/.models/world").expanduser()
        self.current_state: WorldState | None = None
        self.state_providers: dict[str, StateProvider] = {}
        self.update_interval: timedelta = timedelta(minutes=5)
        self.last_update: datetime | None = None

        # Initialize state providers
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize world state providers."""
        self.state_providers = {
            "time": TimeProvider(),
            "location": LocationProvider(),
            "system": SystemProvider(),
            "domain": DomainKnowledgeProvider(),
            "patterns": SharedPatternsProvider(),
        }

    def initialize(self):
        """Initialize the world model."""
        # Ensure world directory exists
        self.world_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.world_dir / "domain_knowledge").mkdir(exist_ok=True)

        # Load initial state
        self._update_world_state()

    def get_current_state(self) -> WorldState:
        """Get current world state, updating if necessary."""
        if self.current_state is None or self.last_update is None or datetime.now() - self.last_update > self.update_interval:
            self._update_world_state()

        return self.current_state

    def _update_world_state(self):
        """Update world state from all providers."""
        state_data = {}

        for provider_name, provider in self.state_providers.items():
            try:
                state_data[provider_name] = provider.get_current_state()
            except Exception:
                # Log error and use cached/default state
                state_data[provider_name] = provider.get_cached_state()

        # Create world state with required fields
        self.current_state = WorldState(
            timestamp=datetime.now(),
            time_context=state_data.get("time"),
            location_context=state_data.get("location"),
            system_context=state_data.get("system"),
            domain_knowledge=state_data.get("domain", {}),
            shared_patterns=state_data.get("patterns", {}),
        )

        self.last_update = datetime.now()

        # Persist current state
        self._persist_world_state()

    def get_temporal_context(self) -> TimeContext:
        """Get current temporal context."""
        return self.get_current_state().time_context

    def get_location_context(self) -> LocationContext:
        """Get current location context."""
        return self.get_current_state().location_context

    def get_system_context(self) -> SystemContext:
        """Get current system context."""
        return self.get_current_state().system_context

    def get_domain_knowledge(self, domain: str) -> DomainKnowledge | None:
        """Get knowledge for a specific domain."""
        return self.get_current_state().domain_knowledge.get(domain)

    def update_domain_knowledge(self, domain: str, knowledge: DomainKnowledge):
        """Update domain knowledge."""
        if self.current_state:
            self.current_state.domain_knowledge[domain] = knowledge
            self._persist_domain_knowledge(domain, knowledge)

    def get_shared_patterns(self, pattern_type: str | None = None) -> dict[str, Any]:
        """Get shared patterns, optionally filtered by type."""
        patterns = self.get_current_state().shared_patterns
        if pattern_type:
            return patterns.get(pattern_type, {})
        return patterns

    def add_shared_pattern(self, pattern_type: str, pattern_id: str, pattern_data: dict[str, Any]):
        """Add a new shared pattern."""
        if self.current_state:
            if pattern_type not in self.current_state.shared_patterns:
                self.current_state.shared_patterns[pattern_type] = {}
            self.current_state.shared_patterns[pattern_type][pattern_id] = pattern_data
            self._persist_shared_patterns()

    def _persist_world_state(self):
        """Persist current world state to storage."""
        try:
            state_file = self.world_dir / "world_state.json"
            with open(state_file, "w") as f:
                # Convert datetime objects to ISO format for JSON serialization
                state_dict = self._serialize_world_state()
                json.dump(state_dict, f, indent=2, default=str)
        except Exception:
            # Log error but don't fail
            pass

    def _serialize_world_state(self) -> dict[str, Any]:
        """Serialize world state for JSON storage."""
        if not self.current_state:
            return {}

        state_dict = {
            "timestamp": self.current_state.timestamp.isoformat(),
            "time_context": {
                "current_time": self.current_state.time_context.current_time.isoformat(),
                "timezone": self.current_state.time_context.timezone,
                "day_of_week": self.current_state.time_context.day_of_week,
                "is_business_hours": self.current_state.time_context.is_business_hours,
                "is_holiday": self.current_state.time_context.is_holiday,
                "season": self.current_state.time_context.season,
                "time_period": self.current_state.time_context.time_period,
            },
            "location_context": {
                "coordinates": self.current_state.location_context.coordinates,
                "timezone": self.current_state.location_context.timezone,
                "country": self.current_state.location_context.country,
                "region": self.current_state.location_context.region,
                "city": self.current_state.location_context.city,
                "environment": self.current_state.location_context.environment,
                "network": self.current_state.location_context.network,
            },
            "system_context": {
                "system_load": self.current_state.system_context.system_load,
                "memory_usage": self.current_state.system_context.memory_usage,
                "network_status": self.current_state.system_context.network_status,
                "available_resources": self.current_state.system_context.available_resources,
                "system_health": self.current_state.system_context.system_health,
                "maintenance_mode": self.current_state.system_context.maintenance_mode,
                "last_maintenance": self.current_state.system_context.last_maintenance.isoformat(),
            },
            "domain_knowledge": {},
            "shared_patterns": self.current_state.shared_patterns,
            "global_events": self.current_state.global_events,
            "system_alerts": self.current_state.system_alerts,
        }

        # Serialize domain knowledge
        for domain, knowledge in self.current_state.domain_knowledge.items():
            state_dict["domain_knowledge"][domain] = {
                "domain": knowledge.domain,
                "topics": knowledge.topics,
                "expertise_level": knowledge.expertise_level,
                "last_updated": knowledge.last_updated.isoformat(),
                "confidence_score": knowledge.confidence_score,
                "sources": knowledge.sources,
                "patterns": knowledge.patterns,
            }

        return state_dict

    def _persist_domain_knowledge(self, domain: str, knowledge: DomainKnowledge):
        """Persist domain knowledge to storage."""
        try:
            domain_file = self.world_dir / "domain_knowledge" / f"{domain}.json"
            domain_file.parent.mkdir(parents=True, exist_ok=True)

            with open(domain_file, "w") as f:
                knowledge_dict = {
                    "domain": knowledge.domain,
                    "topics": knowledge.topics,
                    "expertise_level": knowledge.expertise_level,
                    "last_updated": knowledge.last_updated.isoformat(),
                    "confidence_score": knowledge.confidence_score,
                    "sources": knowledge.sources,
                    "patterns": knowledge.patterns,
                }
                json.dump(knowledge_dict, f, indent=2)
        except Exception:
            # Log error but don't fail
            pass

    def _persist_shared_patterns(self):
        """Persist shared patterns to storage."""
        try:
            patterns_file = self.world_dir / "shared_patterns.json"
            with open(patterns_file, "w") as f:
                json.dump(self.current_state.shared_patterns, f, indent=2)
        except Exception:
            # Log error but don't fail
            pass
