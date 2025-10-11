**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 1.0.0  
**Status:** Design

# World Model Specification

## Overview

The World Model provides agents with fundamental awareness of the world around them, including temporal, spatial, and contextual information. This enables agents to make more informed decisions based on current world state and to maintain shared knowledge across the system.

## Core Concepts

### 1. **World State Awareness**
Agents need to understand:
- **When** they are operating (time, date, timezone)
- **Where** they are operating (location, environment)
- **What** is happening (current events, system state)
- **Who** they are interacting with (user context, permissions)

### 2. **Shared Knowledge**
The world model provides:
- **Domain Knowledge**: Expertise shared across problem domains
- **System Intelligence**: Aggregated learning from all agents
- **Cross-User Patterns**: Successful strategies used by similar users
- **Environmental Context**: Current world conditions and constraints

## Architecture

### **Storage Structure**
```
~/.models/
├── users/           # User profiles (existing)
├── strategies/      # Strategy patterns (existing)
├── contexts/        # Context patterns (existing)
└── world/          # World model and shared knowledge
    ├── time.json           # Current time and timezone info
    ├── location.json       # Location and environment data
    ├── system.json         # System state and health
    ├── domain_knowledge/   # Domain-specific expertise
    │   ├── general.json    # General knowledge
    │   ├── technical.json  # Technical expertise
    │   └── business.json   # Business domain knowledge
    ├── shared_patterns.json # Cross-user successful patterns
    └── world_state.json    # Current world state snapshot
```

### **Component Architecture**
```
Agent → AgentMind → WorldModel → World State Providers
  ↑         ↑          ↑              ↑
Request  Mind Manager World State   Time, Location,
                                    System, Domain
                                    Knowledge
```

## World Model Components

### 1. **Temporal Awareness**
```python
@dataclass
class TimeContext:
    """Current time and temporal context."""
    current_time: datetime
    timezone: str
    day_of_week: str
    is_business_hours: bool
    is_holiday: bool
    season: str
    time_period: str  # "morning", "afternoon", "evening", "night"
    
    def __post_init__(self):
        self.day_of_week = self.current_time.strftime("%A")
        self.is_business_hours = self._check_business_hours()
        self.is_holiday = self._check_holiday()
        self.season = self._determine_season()
        self.time_period = self._determine_time_period()
```

### 2. **Spatial Awareness**
```python
@dataclass
class LocationContext:
    """Location and environmental context."""
    coordinates: tuple[float, float] | None  # lat, lon
    timezone: str
    country: str
    region: str
    city: str
    environment: str  # "office", "home", "mobile", "cloud"
    network: str      # "local", "vpn", "public", "corporate"
    
    def __post_init__(self):
        if self.coordinates:
            self.timezone = self._get_timezone_from_coordinates()
```

### 3. **System State**
```python
@dataclass
class SystemContext:
    """Current system state and health."""
    system_load: float
    memory_usage: float
    network_status: str
    available_resources: dict[str, Any]
    system_health: str  # "healthy", "degraded", "critical"
    maintenance_mode: bool
    last_maintenance: datetime
```

### 4. **Domain Knowledge**
```python
@dataclass
class DomainKnowledge:
    """Domain-specific expertise and knowledge."""
    domain: str
    topics: list[str]
    expertise_level: str  # "beginner", "intermediate", "advanced", "expert"
    last_updated: datetime
    confidence_score: float
    sources: list[str]
    patterns: dict[str, Any]
```

### 5. **World State**
```python
@dataclass
class WorldState:
    """Current snapshot of world state."""
    timestamp: datetime
    time_context: TimeContext
    location_context: LocationContext
    system_context: SystemContext
    domain_knowledge: dict[str, DomainKnowledge]
    shared_patterns: dict[str, Any]
    global_events: list[str]
    system_alerts: list[str]
    
    def __post_init__(self):
        self.timestamp = datetime.now()
```

## World Model Implementation

### **Core WorldModel Class**
```python
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
            "patterns": SharedPatternsProvider()
        }
    
    def get_current_state(self) -> WorldState:
        """Get current world state, updating if necessary."""
        if (self.current_state is None or 
            self.last_update is None or
            datetime.now() - self.last_update > self.update_interval):
            self._update_world_state()
        
        return self.current_state
    
    def _update_world_state(self):
        """Update world state from all providers."""
        state_data = {}
        
        for provider_name, provider in self.state_providers.items():
            try:
                state_data[provider_name] = provider.get_current_state()
            except Exception as e:
                # Log error and use cached/default state
                state_data[provider_name] = provider.get_cached_state()
        
        self.current_state = WorldState(**state_data)
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
    
    def get_shared_patterns(self, pattern_type: str = None) -> dict[str, Any]:
        """Get shared patterns, optionally filtered by type."""
        patterns = self.get_current_state().shared_patterns
        if pattern_type:
            return patterns.get(pattern_type, {})
        return patterns
    
    def add_shared_pattern(self, pattern_type: str, pattern_id: str, pattern_data: dict):
        """Add a new shared pattern."""
        if self.current_state:
            if pattern_type not in self.current_state.shared_patterns:
                self.current_state.shared_patterns[pattern_type] = {}
            self.current_state.shared_patterns[pattern_type][pattern_id] = pattern_data
            self._persist_shared_patterns()
```

## State Providers

### **Time Provider**
```python
class TimeProvider:
    """Provides current time and temporal context."""
    
    def get_current_state(self) -> TimeContext:
        """Get current temporal context."""
        now = datetime.now()
        return TimeContext(
            current_time=now,
            timezone=self._get_system_timezone(),
            day_of_week=now.strftime("%A"),
            is_business_hours=self._check_business_hours(now),
            is_holiday=self._check_holiday(now),
            season=self._determine_season(now),
            time_period=self._determine_time_period(now)
        )
    
    def _get_system_timezone(self) -> str:
        """Get system timezone."""
        try:
            import time
            return time.tzname[time.daylight]
        except:
            return "UTC"
    
    def _check_business_hours(self, dt: datetime) -> bool:
        """Check if current time is during business hours."""
        hour = dt.hour
        return 9 <= hour <= 17 and dt.weekday() < 5
    
    def _check_holiday(self, dt: datetime) -> bool:
        """Check if current date is a holiday."""
        # Basic holiday checking - could be enhanced with holiday API
        holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (12, 25), # Christmas
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
```

### **Location Provider**
```python
class LocationProvider:
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
            network=self._determine_network()
        )
    
    def _get_coordinates(self) -> tuple[float, float] | None:
        """Get current coordinates from available sources."""
        # Try IP geolocation first
        try:
            import requests
            response = requests.get("https://ipapi.co/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return (data.get("latitude"), data.get("longitude"))
        except:
            pass
        
        # Fallback to system timezone
        return None
    
    def _get_timezone_from_coordinates(self, coords: tuple[float, float] | None) -> str:
        """Get timezone from coordinates."""
        if coords:
            try:
                import requests
                lat, lon = coords
                response = requests.get(f"https://timezone-api.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("timezone", "UTC")
            except:
                pass
        
        # Fallback to system timezone
        try:
            import time
            return time.tzname[time.daylight]
        except:
            return "UTC"
    
    def _get_country(self, coords: tuple[float, float] | None) -> str:
        """Get country from coordinates."""
        if coords:
            try:
                import requests
                lat, lon = coords
                response = requests.get(f"https://reverse-geocode.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("country", "Unknown")
            except:
                pass
        
        return "Unknown"
    
    def _get_region(self, coords: tuple[float, float] | None) -> str:
        """Get region from coordinates."""
        if coords:
            try:
                import requests
                lat, lon = coords
                response = requests.get(f"https://reverse-geocode.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("region", "Unknown")
            except:
                pass
        
        return "Unknown"
    
    def _get_city(self, coords: tuple[float, float] | None) -> str:
        """Get city from coordinates."""
        if coords:
            try:
                import requests
                lat, lon = coords
                response = requests.get(f"https://reverse-geocode.example.com/{lat}/{lon}", timeout=5)
                if response.status_code == 200:
                    return response.json().get("city", "Unknown")
            except:
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
```

### **System Provider**
```python
class SystemProvider:
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
            last_maintenance=self._get_last_maintenance()
        )
    
    def _get_system_load(self) -> float:
        """Get current system load."""
        try:
            import psutil
            return psutil.getloadavg()[0]  # 1-minute load average
        except:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent
        except:
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
        except:
            return "unknown"
    
    def _get_available_resources(self) -> dict[str, Any]:
        """Get available system resources."""
        resources = {}
        
        try:
            import psutil
            
            # CPU info
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            resources["cpu"] = {
                "count": cpu_count,
                "usage_percent": cpu_percent,
                "available": cpu_count * (100 - cpu_percent) / 100
            }
            
            # Memory info
            memory = psutil.virtual_memory()
            resources["memory"] = {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "usage_percent": memory.percent
            }
            
            # Disk info
            disk = psutil.disk_usage('/')
            resources["disk"] = {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "usage_percent": (disk.used / disk.total) * 100
            }
            
        except:
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
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            if disk_usage > 95:
                return "critical"
            elif disk_usage > 90:
                return "degraded"
            
            return "healthy"
            
        except:
            return "unknown"
    
    def _check_maintenance_mode(self) -> bool:
        """Check if system is in maintenance mode."""
        # Could check for maintenance flag file or database setting
        return False
    
    def _get_last_maintenance(self) -> datetime:
        """Get timestamp of last maintenance."""
        # Could read from maintenance log or database
        return datetime.now() - timedelta(days=7)  # Default: 1 week ago
```

## Integration with AgentMind

### **Enhanced AgentMind Class**
```python
class AgentMind:
    """AgentMind mixin with world model integration."""
    
    def __init__(self):
        # Existing attributes
        self.user_profile: UserProfile | None = None
        self.strategy_patterns: dict[str, StrategyPattern] = {}
        self.context_patterns: dict[str, ContextPattern] = {}
        
        # World model integration
        self.world_model = WorldModel()
        
        # Storage paths
        self.models_dir = Path("~/.models").expanduser()
        self.users_dir = self.models_dir / "users"
        self.strategies_dir = self.models_dir / "strategies"
        self.contexts_dir = self.models_dir / "contexts"
        self.world_dir = self.models_dir / "world"
    
    def initialize_mind(self, user_id: str = "default"):
        """Initialize the agent mind with world model."""
        # Load user profile and patterns
        self.user_profile = self._load_user_profile(user_id)
        self.strategy_patterns = self._load_strategy_patterns(user_id)
        self.context_patterns = self._load_context_patterns(user_id)
        
        # Initialize world model
        self.world_model.initialize()
        
        # Ensure storage directories exist
        self._ensure_storage_directories()
    
    def get_world_context(self) -> WorldState:
        """Get current world context."""
        return self.world_model.get_current_state()
    
    def get_temporal_context(self) -> TimeContext:
        """Get current temporal context."""
        return self.world_model.get_temporal_context()
    
    def get_location_context(self) -> LocationContext:
        """Get current location context."""
        return self.world_model.get_location_context()
    
    def get_system_context(self) -> SystemContext:
        """Get current system context."""
        return self.world_model.get_system_context()
    
    def get_domain_knowledge(self, domain: str) -> DomainKnowledge | None:
        """Get knowledge for a specific domain."""
        return self.world_model.get_domain_knowledge(domain)
    
    def update_domain_knowledge(self, domain: str, knowledge: DomainKnowledge):
        """Update domain knowledge."""
        self.world_model.update_domain_knowledge(domain, knowledge)
    
    def get_shared_patterns(self, pattern_type: str = None) -> dict[str, Any]:
        """Get shared patterns from world model."""
        return self.world_model.get_shared_patterns(pattern_type)
    
    def add_shared_pattern(self, pattern_type: str, pattern_id: str, pattern_data: dict):
        """Add a new shared pattern to world model."""
        self.world_model.add_shared_pattern(pattern_type, pattern_id, pattern_data)
```

## Usage Examples

### **Basic World Model Usage**
```python
# Initialize agent with world model
agent = MyAgent()
agent.initialize_mind("user123")

# Get current world context
world_state = agent.get_world_context()
print(f"Current time: {world_state.time_context.current_time}")
print(f"Location: {world_state.location_context.city}, {world_state.location_context.country}")
print(f"System health: {world_state.system_context.system_health}")

# Use temporal context for decision making
if world_state.time_context.is_business_hours:
    strategy = "business_hours_strategy"
else:
    strategy = "after_hours_strategy"

# Use location context for localization
if world_state.location_context.country == "US":
    date_format = "MM/DD/YYYY"
else:
    date_format = "DD/MM/YYYY"

# Use system context for resource management
if world_state.system_context.system_health == "critical":
    # Use lightweight processing strategies
    max_concurrent_tasks = 1
else:
    max_concurrent_tasks = 5
```

### **Domain Knowledge Usage**
```python
# Get domain knowledge
tech_knowledge = agent.get_domain_knowledge("technical")
if tech_knowledge and tech_knowledge.expertise_level == "expert":
    # Use advanced technical strategies
    strategy = "expert_technical_strategy"
else:
    # Use basic technical strategies
    strategy = "basic_technical_strategy"

# Update domain knowledge
new_knowledge = DomainKnowledge(
    domain="semiconductor",
    topics=["inspection", "quality_control"],
    expertise_level="intermediate",
    last_updated=datetime.now(),
    confidence_score=0.8,
    sources=["training_data", "user_feedback"],
    patterns={}
)
agent.update_domain_knowledge("semiconductor", new_knowledge)
```

### **Shared Patterns Usage**
```python
# Get shared patterns for a specific type
successful_strategies = agent.get_shared_patterns("strategy")
if "semiconductor_inspection" in successful_strategies:
    strategy = successful_strategies["semiconductor_inspection"]
    # Use proven strategy

# Add new successful pattern
new_pattern = {
    "problem_type": "quality_anomaly_detection",
    "strategy": "multi_layer_analysis",
    "success_rate": 0.95,
    "execution_time": 2.3,
    "user_satisfaction": 0.9
}
agent.add_shared_pattern("strategy", "quality_anomaly_detection", new_pattern)
```

## Configuration

### **World Model Configuration**
```python
class WorldModelConfig:
    """Configuration for world model behavior."""
    
    # Update intervals
    state_update_interval: timedelta = timedelta(minutes=5)
    pattern_update_interval: timedelta = timedelta(hours=1)
    knowledge_update_interval: timedelta = timedelta(hours=6)
    
    # Provider settings
    enable_time_provider: bool = True
    enable_location_provider: bool = True
    enable_system_provider: bool = True
    enable_domain_provider: bool = True
    enable_patterns_provider: bool = True
    
    # Privacy settings
    enable_location_tracking: bool = False
    enable_system_monitoring: bool = True
    enable_cross_user_learning: bool = False
    
    # Storage settings
    max_pattern_file_size: int = 1024 * 1024  # 1MB
    pattern_retention_days: int = 90
    knowledge_retention_days: int = 365
```

## Performance Characteristics

### **Performance Targets**
- **World state updates**: < 100ms for full state refresh
- **Temporal context access**: < 1ms for time-based queries
- **Location context access**: < 50ms for location queries
- **System context access**: < 10ms for system state queries
- **Domain knowledge access**: < 20ms for knowledge queries
- **Pattern retrieval**: < 30ms for pattern lookups

### **Scalability Considerations**
- **State caching**: In-memory caching with configurable TTL
- **Lazy loading**: Load world state only when requested
- **Background updates**: Update world state in background threads
- **Resource monitoring**: Efficient system resource monitoring
- **Pattern storage**: Compressed JSON storage with size limits

## Security and Privacy

### **Data Protection**
- **Location privacy**: Optional location tracking with user consent
- **System isolation**: System monitoring limited to necessary metrics
- **Pattern anonymization**: Shared patterns contain no user-identifiable data
- **Access control**: World model access controlled by agent permissions

### **Privacy Controls**
- **Location opt-out**: Users can disable location tracking
- **System monitoring opt-out**: Users can disable system monitoring
- **Pattern sharing opt-out**: Users can opt out of pattern sharing
- **Data retention**: Configurable data retention policies

## Future Enhancements

### **Advanced World Model Features**
- **Real-time event streaming**: Subscribe to world state changes
- **Predictive modeling**: Predict future world states
- **Multi-agent coordination**: Coordinate world model across agent networks
- **External integrations**: Weather, news, market data APIs
- **Machine learning**: Learn from world state patterns

### **Enterprise Features**
- **Compliance monitoring**: Ensure world model meets compliance requirements
- **Audit trails**: Track world model access and modifications
- **Role-based access**: Different world model access levels
- **Data governance**: Structured data governance policies
- **Integration APIs**: REST APIs for external system integration

## Conclusion

The World Model provides agents with fundamental awareness of their operating environment, enabling more intelligent and context-aware decision making. By integrating temporal, spatial, and system awareness with shared knowledge and patterns, agents can operate more effectively in dynamic environments.

This specification provides the foundation for a robust world model that scales from basic awareness to sophisticated multi-agent coordination, while maintaining privacy and security controls appropriate for enterprise environments.
