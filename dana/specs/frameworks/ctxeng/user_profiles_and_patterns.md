# User Profiles and Pattern Learning Specification

## Overview

This specification defines the user profile management and pattern learning system that enhances the Context Engineering Framework (CTXENG) with adaptive learning capabilities. The system enables agents to learn from repeated problem-solving experiences and provide personalized, intelligent problem-solving approaches.

## Core Concepts

### **User Profile Intelligence**
- **Persistent Storage**: User preferences and learning patterns stored under `~/.dana/users/`
- **Personalized Experience**: Tailored strategies and context based on user expertise and preferences
- **Learning Evolution**: Profiles improve over time through usage and feedback

### **Pattern Learning**
- **Strategy Patterns**: Learn which strategies work best for different problem types
- **Context Patterns**: Learn which context configurations optimize LLM performance
- **Success Metrics**: Track success rates, execution time, and user satisfaction
- **Pattern Evolution**: Remove old patterns, learn new ones, adapt to changing performance

## Architecture

### **Storage Structure**
```
~/.models/                     # All agent models and learning data
├── users/                     # User profiles and preferences
│   ├── default.json           # Default user profile
│   ├── ctn.json               # Specific user profile
│   └── shared.json            # Shared user preferences
├── strategies/                 # Strategy patterns and learning
│   ├── default.json           # Default strategy patterns
│   ├── ctn.json               # User-specific strategy patterns
│   └── global.json            # Global strategy patterns
├── contexts/                   # Context patterns and learning
│   ├── default.json           # Default context patterns
│   ├── ctn.json               # User-specific context patterns
│   └── global.json            # Global context patterns
└── world/                     # Future: World model and shared knowledge
    ├── domain_knowledge.json  # Domain-specific knowledge
    ├── shared_patterns.json   # Cross-user patterns
    └── system_intelligence.json # System-level learning
```

### **Component Architecture**
```
User Input → Agent → AgentMind → Pattern Learning Engine → Adaptive Selection Engine
     ↑           ↑       ↑              ↑                      ↑
   Problem    Strategy  Mind Manager  Pattern Storage      Pattern-Based
   Statement  Selection & Learning    & Learning          Strategy/Context
                                                          Selection
```

### **AgentMind Mixin Design**

The `AgentMind` mixin handles the complete lifecycle of user profiles, strategy patterns, and context patterns.

**Location**: `dana.core.agent.mind.AgentMind`

```python
class AgentMind:
    """Mixin for managing agent intelligence, learning, and memory."""
    
    def __init__(self):
        self.user_profile: UserProfile = None
        self.strategy_patterns: Dict[str, StrategyPattern] = {}
        self.context_patterns: Dict[str, ContextPattern] = {}
        self.world_model: WorldModel = None  # Future: shared knowledge
        
        # Storage paths
        self.models_dir = Path("~/.models").expanduser()
        self.users_dir = self.models_dir / "users"
        self.strategies_dir = self.models_dir / "strategies"
        self.contexts_dir = self.models_dir / "contexts"
        self.world_dir = self.models_dir / "world"
    
    def initialize_mind(self, user_id: str = "default"):
        """Initialize the agent's mind with user profile and patterns."""
        # Load user profile
        self.user_profile = self._load_user_profile(user_id)
        
        # Load strategy patterns
        self.strategy_patterns = self._load_strategy_patterns(user_id)
        
        # Load context patterns
        self.context_patterns = self._load_context_patterns(user_id)
        
        # Future: Load world model
        # self.world_model = self._load_world_model()
    
    def _load_user_profile(self, user_id: str) -> UserProfile:
        """Load user profile from ~/.models/users/{user_id}.json"""
        profile_file = self.users_dir / f"{user_id}.json"
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                data = json.load(f)
                return UserProfile(**data)
        else:
            return self._create_default_profile(user_id)
    
    def _load_strategy_patterns(self, user_id: str) -> Dict[str, StrategyPattern]:
        """Load strategy patterns from ~/.models/strategies/{user_id}.json"""
        patterns_file = self.strategies_dir / f"{user_id}.json"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                data = json.load(f)
                return {k: StrategyPattern(**v) for k, v in data.items()}
        else:
            return {}
    
    def _load_context_patterns(self, user_id: str) -> Dict[str, ContextPattern]:
        """Load context patterns from ~/.models/contexts/{user_id}.json"""
        patterns_file = self.contexts_dir / f"{user_id}.json"
        if profile_file.exists():
            with open(patterns_file, 'r') as f:
                data = json.load(f)
                return {k: ContextPattern(**v) for k, v in data.items()}
        else:
            return {}
    
    def update_user_preference(self, key: str, value: Any):
        """Update a user preference and persist to storage."""
        if hasattr(self.user_profile, key):
            setattr(self.user_profile, key, value)
            self._save_user_profile()
    
    def learn_from_execution(self, problem: str, strategy: Strategy, context_config: ContextConfig, result: Result):
        """Learn from execution results and update patterns."""
        problem_signature = self._create_problem_signature(problem)
        
        # Update strategy patterns
        self._update_strategy_pattern(problem_signature, strategy, result)
        
        # Update context patterns
        self._update_context_pattern(problem_signature, context_config, result)
        
        # Persist updated patterns
        self._save_patterns()
    
    def _save_user_profile(self):
        """Save user profile to ~/.models/users/{user_id}.json"""
        os.makedirs(self.users_dir, exist_ok=True)
        profile_file = self.users_dir / f"{self.user_profile.user_id}.json"
        with open(profile_file, 'w') as f:
            json.dump(self.user_profile.dict(), f, indent=2)
    
    def _save_patterns(self):
        """Save strategy and context patterns to storage under ~/.models/."""
        # Save strategy patterns
        os.makedirs(self.strategies_dir, exist_ok=True)
        strategy_file = self.strategies_dir / f"{self.user_profile.user_id}.json"
        with open(strategy_file, 'w') as f:
            json.dump(self.strategy_patterns, f, indent=2, default=str)
        
        # Save context patterns
        os.makedirs(self.contexts_dir, exist_ok=True)
        context_file = self.contexts_dir / f"{self.user_profile.user_id}.json"
        with open(context_file, 'w') as f:
            json.dump(self.context_patterns, f, indent=2, default=str)
    
    def cleanup_expired_patterns(self):
        """Remove expired patterns based on TTL and usage."""
        current_time = datetime.now()
        
        # Cleanup strategy patterns
        expired_strategies = [
            k for k, v in self.strategy_patterns.items()
            if self._is_pattern_expired(v, current_time)
        ]
        for k in expired_strategies:
            del self.strategy_patterns[k]
        
        # Cleanup context patterns
        expired_contexts = [
            k for k, v in self.context_patterns.items()
            if self._is_pattern_expired(v, current_time)
        ]
        for k in expired_contexts:
            del self.context_patterns[k]
    
    def _is_pattern_expired(self, pattern: BasePattern, current_time: datetime) -> bool:
        """Check if a pattern has expired based on TTL and usage."""
        days_since_use = (current_time - pattern.last_used).days
        return (
            pattern.usage_count < self.user_profile.learning_preferences.min_pattern_usage and
            days_since_use > self.user_profile.learning_preferences.pattern_ttl_days
        )
```

## User Profile Schema

### **Profile Structure**
```json
{
    "expertise_level": "novice" | "intermediate" | "expert" | "enterprise",
    "domain_preferences": ["general", "technical", "business", "creative", "scientific"],
    "urgency_patterns": {
        "quick": 0.6,
        "standard": 0.3,
        "thorough": 0.1
    },
    "template_preferences": {
        "problem_solving": "problem_solving",
        "conversation": "conversation",
        "analysis": "analysis"
    },
    "context_depth_preferences": {
        "general": "standard",
        "technical": "comprehensive",
        "business": "detailed",
        "creative": "standard"
    },
    "learning_preferences": {
        "pattern_learning_enabled": true,
        "cross_user_learning": false,
        "pattern_ttl_days": 30,
        "min_pattern_usage": 3
    }
}
```

### **Profile Fields**

#### **expertise_level**
- **novice**: Basic problem-solving, minimal context, simple strategies
- **intermediate**: Standard problem-solving, balanced context, common strategies
- **expert**: Advanced problem-solving, comprehensive context, sophisticated strategies
- **enterprise**: Enterprise-grade problem-solving, compliance-aware, integration-focused

#### **domain_preferences**
- **general**: Everyday problems, general-purpose strategies
- **technical**: Technical problems, specialized technical strategies
- **business**: Business problems, business-focused strategies
- **creative**: Creative problems, innovative strategies
- **scientific**: Scientific problems, research-focused strategies

#### **urgency_patterns**
- **quick**: Fast solutions, minimal context, basic strategies
- **standard**: Balanced solutions, standard context, proven strategies
- **thorough**: Comprehensive solutions, rich context, advanced strategies

## Pattern Learning Schema

### **Strategy Pattern Structure**
```json
{
    "problem_signature": "hash_of_problem_characteristics",
    "strategy_type": "RecursiveStrategy",
    "success_rate": 0.95,
    "execution_time": 0.8,
    "user_satisfaction": 0.9,
    "usage_count": 47,
    "last_used": "2024-01-15T10:30:00Z",
    "context_requirements": ["minimal", "no_history"],
    "fallback_strategies": ["DirectExecutionStrategy"],
    "domain": "technical",
    "complexity": "simple",
    "confidence": 0.92
}
```

### **Context Pattern Structure**
```json
{
    "problem_signature": "hash_of_problem_characteristics",
    "template": "problem_solving",
    "scope": "minimal",
    "priority": "relevant",
    "token_efficiency": 0.85,
    "llm_performance": 0.92,
    "usage_count": 47,
    "last_used": "2024-01-15T10:30:00Z",
    "context_keys_used": ["query", "objective"],
    "domain": "technical",
    "complexity": "simple",
    "confidence": 0.89
}
```

### **Pattern Fields**

#### **problem_signature**
- Hash of problem characteristics (type, complexity, domain, keywords)
- Used for pattern matching and retrieval
- Enables fast lookup of relevant patterns

#### **success_rate**
- Percentage of successful executions (0.0 to 1.0)
- Used to determine pattern reliability
- Patterns with low success rates are deprioritized

#### **execution_time**
- Average execution time in seconds
- Used for performance optimization
- Faster patterns are preferred when appropriate

#### **user_satisfaction**
- User feedback rating (0.0 to 1.0)
- Subjective measure of solution quality
- Balances objective metrics with user experience

#### **confidence**
- Overall confidence in the pattern (0.0 to 1.0)
- Calculated from multiple factors
- Used for pattern selection decisions

## Adaptive Selection Process

### **Strategy Selection Flow**
```python
def select_strategy(problem: str, user_profile: UserProfile) -> Strategy:
    # 1. Create problem signature
    problem_signature = create_problem_signature(problem)
    
    # 2. Look for existing patterns
    strategy_pattern = find_strategy_pattern(problem_signature)
    
    if strategy_pattern and is_pattern_reliable(strategy_pattern):
        # Use learned pattern
        strategy_type = strategy_pattern.strategy_type
        log_pattern_usage(strategy_pattern, "strategy")
        return create_strategy(strategy_type)
    else:
        # Fall back to user preferences or defaults
        return get_fallback_strategy(problem, user_profile)

def is_pattern_reliable(pattern: StrategyPattern) -> bool:
    """Determine if a pattern is reliable enough to use."""
    return (
        pattern.usage_count >= MIN_PATTERN_USAGE and
        pattern.success_rate >= SUCCESS_RATE_THRESHOLD and
        pattern.confidence >= CONFIDENCE_THRESHOLD
    )
```

### **Context Configuration Flow**
```python
def configure_context_engineering(problem: str, user_profile: UserProfile) -> ContextConfig:
    # 1. Create problem signature
    problem_signature = create_problem_signature(problem)
    
    # 2. Look for existing context patterns
    context_pattern = find_context_pattern(problem_signature)
    
    if context_pattern and is_context_pattern_reliable(context_pattern):
        # Use learned pattern
        config = ContextConfig(
            template=context_pattern.template,
            scope=context_pattern.scope,
            priority=context_pattern.priority,
            focus="quality"
        )
        log_pattern_usage(context_pattern, "context")
    else:
        # Fall back to user preferences
        config = get_fallback_context_config(problem, user_profile)
    
    return config
```

## Learning Process

### **Pattern Creation and Updates**
```python
def learn_from_execution(problem: str, strategy: Strategy, context_config: ContextConfig, result: Result):
    """Learn from execution results to improve future selections."""
    problem_signature = create_problem_signature(problem)
    
    # Update strategy pattern
    strategy_pattern = get_or_create_strategy_pattern(problem_signature)
    update_strategy_pattern(strategy_pattern, strategy, result)
    
    # Update context pattern
    context_pattern = get_or_create_context_pattern(problem_signature)
    update_context_pattern(context_pattern, context_config, result)
    
    # Save updated patterns
    save_patterns()

def update_strategy_pattern(pattern: StrategyPattern, strategy: Strategy, result: Result):
    """Update strategy pattern with execution results."""
    pattern.strategy_type = strategy.__class__.__name__
    pattern.usage_count += 1
    pattern.last_used = datetime.now()
    
    # Update success metrics
    success = assess_success(result)
    pattern.success_rate = update_success_rate(
        pattern.success_rate, 
        success, 
        pattern.usage_count
    )
    
    # Update execution time
    execution_time = measure_execution_time(result)
    pattern.execution_time = update_execution_time(
        pattern.execution_time,
        execution_time,
        pattern.usage_count
    )
    
    # Update user satisfaction
    satisfaction = assess_user_satisfaction(result)
    if satisfaction is not None:
        pattern.user_satisfaction = update_satisfaction(
            pattern.user_satisfaction,
            satisfaction,
            pattern.usage_count
        )
```

### **Pattern Evolution**
```python
def evolve_patterns():
    """Evolve patterns based on changing performance and new insights."""
    for pattern in get_all_patterns():
        # Remove old, unused patterns
        if should_remove_pattern(pattern):
            remove_pattern(pattern)
            continue
        
        # Update pattern confidence
        if pattern.usage_count >= MIN_PATTERN_USAGE:
            pattern.confidence = calculate_confidence(pattern)
        
        # Identify pattern improvements
        if pattern.success_rate < SUCCESS_RATE_THRESHOLD:
            suggest_pattern_improvements(pattern)
        
        # Update pattern metadata
        update_pattern_metadata(pattern)

def should_remove_pattern(pattern: BasePattern) -> bool:
    """Determine if a pattern should be removed."""
    return (
        pattern.usage_count < MIN_PATTERN_USAGE and
        (datetime.now() - pattern.last_used).days > PATTERN_TTL_DAYS
    )
```

## Lifecycle Management

### **Initialization Lifecycle**
1. **Agent Creation**: Load user profile and patterns from storage
2. **First Use**: Create default profiles if none exist
3. **User Switch**: Load different user profile and patterns
4. **Pattern Validation**: Verify pattern integrity and consistency

### **Runtime Lifecycle**
1. **User Preferences**: Update when user explicitly changes preferences
2. **Pattern Learning**: Update after each problem-solving execution
3. **Performance Metrics**: Track success rates, execution times, user satisfaction
4. **Pattern Evolution**: Continuously improve patterns based on performance

### **Maintenance Lifecycle**
1. **Pattern Cleanup**: Remove expired patterns based on TTL and usage
2. **Storage Optimization**: Compress old patterns, archive unused data
3. **Cross-User Learning**: Share successful patterns across similar users
4. **Data Integrity**: Validate and repair corrupted pattern data

### **Future Extensions**
1. **World Model**: Load shared knowledge and domain expertise
2. **Collaborative Learning**: Learn from team and organization patterns
3. **System Intelligence**: Aggregate learning across all agents

## Configuration and Customization

### **Learning Parameters**
```python
class LearningConfig:
    # Pattern reliability thresholds
    min_pattern_usage: int = 3          # Minimum uses before pattern is considered reliable
    success_rate_threshold: float = 0.8 # Minimum success rate for pattern usage
    confidence_threshold: float = 0.7   # Minimum confidence for pattern usage
    
    # Pattern lifecycle
    pattern_ttl_days: int = 30          # Days before unused patterns are cleaned up
    learning_rate: float = 0.1          # How quickly patterns adapt to new data
    
    # Learning behavior
    cross_user_learning: bool = False   # Whether to learn from other users' patterns
    pattern_sharing: bool = False       # Whether to share patterns across users
    feedback_learning: bool = True      # Whether to learn from user feedback
```

### **User Profile Management**
```python
class UserProfileManager:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.profile_path = f"~/.dana/users/{user_id}/"
        self.profile = self.load_profile()
    
    def load_profile(self) -> UserProfile:
        """Load user profile from storage."""
        profile_file = os.path.join(self.profile_path, "profile.json")
        if os.path.exists(profile_file):
            with open(profile_file, 'r') as f:
                data = json.load(f)
                return UserProfile(**data)
        else:
            return self.create_default_profile()
    
    def save_profile(self):
        """Save user profile to storage."""
        os.makedirs(self.profile_path, exist_ok=True)
        profile_file = os.path.join(self.profile_path, "profile.json")
        with open(profile_file, 'w') as f:
            json.dump(self.profile.dict(), f, indent=2)
    
    def update_preferences(self, **preferences):
        """Update user preferences."""
        for key, value in preferences.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        self.save_profile()
```

## Performance Characteristics

### **Performance Targets**
- **Profile loading**: < 10ms for profile and pattern access
- **Pattern matching**: < 5ms for pattern lookup and selection
- **Pattern learning**: < 50ms per execution result
- **Adaptive selection**: < 20ms for strategy and context selection
- **Pattern storage**: < 100ms for pattern persistence

### **Scalability Considerations**
- **Pattern storage**: JSON files with size limits (max 1MB per pattern file)
- **Pattern cleanup**: Automatic cleanup of old, unused patterns
- **Memory usage**: In-memory caching of frequently used patterns
- **Disk usage**: Compressed storage for large pattern collections

## Security and Privacy

### **Data Protection**
- **User isolation**: Each user's patterns are stored separately
- **Pattern anonymization**: No user-identifiable information in shared patterns
- **Access control**: User profiles are private and not shared
- **Data retention**: Automatic cleanup of old patterns

### **Privacy Controls**
- **Learning opt-out**: Users can disable pattern learning
- **Pattern deletion**: Users can delete their learning patterns
- **Cross-user isolation**: No learning from other users by default
- **Data export**: Users can export their learning data

## Integration with CTXENG

### **Enhanced Context Engine**
```python
class EnhancedContextEngine(ContextEngine):
    def __init__(self, user_id: str = "default"):
        super().__init__()
        self.user_profile_manager = UserProfileManager(user_id)
        self.pattern_learning_engine = PatternLearningEngine(user_id)
        self.adaptive_selection_engine = AdaptiveSelectionEngine(user_id)
    
    def assemble(self, query: str, context: dict = None, template: str = None, **options):
        # Use adaptive selection if no template specified
        if template is None:
            template = self.adaptive_selection_engine.select_template(query, context)
        
        # Assemble context using base functionality
        result = super().assemble(query, context, template, **options)
        
        # Learn from this interaction
        self.pattern_learning_engine.learn_from_interaction(query, context, template, result)
        
        return result
```

### **Agent Integration**
```python
class AgentInstance:
    def __init__(self, user_id: str = "default"):
        self.user_profile_manager = UserProfileManager(user_id)
        self.context_engine = EnhancedContextEngine(user_id)
    
    def solve(self, problem: str, **user_overrides):
        # Apply user overrides to profile
        profile = self.user_profile_manager.get_profile()
        profile = self.apply_overrides(profile, user_overrides)
        
        # Use adaptive selection for strategy and context
        strategy = self.adaptive_selection_engine.select_strategy(problem, profile)
        context_config = self.adaptive_selection_engine.configure_context(problem, profile)
        
        # Execute with learned optimizations
        result = strategy.execute(problem, context_config)
        
        # Learn from execution
        self.pattern_learning_engine.learn_from_execution(problem, strategy, context_config, result)
        
        return result
```

## Future Enhancements

### **Advanced Learning Features**
- **Multi-modal learning**: Learn from different types of user interactions
- **Collaborative learning**: Share patterns across similar users
- **Predictive selection**: Predict optimal strategies before execution
- **A/B testing**: Test different approaches to optimize learning

### **World Model Integration**
- **Domain Knowledge**: Shared expertise across problem domains
- **Cross-User Intelligence**: Aggregate learning from similar users
- **System-Level Patterns**: Identify global optimization opportunities
- **Knowledge Evolution**: Continuous improvement of shared knowledge

**Implementation Status**: ✅ **COMPLETED**
- Basic world model with time, location, and system awareness
- Temporal context (business hours, holidays, seasons, time periods)
- Spatial context (coordinates, timezone, country, region, city)
- System context (health, resources, network status)
- Domain knowledge and shared patterns support
- Integration with AgentMind for seamless agent awareness

### **Enterprise Features**
- **Team learning**: Learn from team problem-solving patterns
- **Compliance-aware learning**: Ensure patterns meet compliance requirements
- **Audit trails**: Track pattern usage and learning decisions
- **Performance analytics**: Detailed analysis of learning effectiveness

## Conclusion

The User Profiles and Pattern Learning system transforms CTXENG from a static configuration-driven framework to a dynamic, intelligent system that continuously improves through experience. By maintaining user preferences and learning from problem-solving patterns, the system provides personalized, efficient, and adaptive context engineering that gets smarter with every interaction.

This specification provides the foundation for creating intelligent agents that not only solve problems effectively but also learn and adapt to user needs, creating a truly personalized and continuously improving problem-solving experience.
