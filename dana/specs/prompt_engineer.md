# PromptEngineer Framework Specification

## Overview

The PromptEngineer is a framework for iterative prompt optimization that learns from LLM responses and user feedback to continuously improve prompt templates and generation strategies.

## Core Philosophy

- **KISS Principle**: Minimal API with maximum functionality
- **Self-Learning**: Automatically evaluates and improves prompts
- **UUID Tracking**: Full lineage and versioning of prompts and templates
- **Flexible Input**: Supports both raw queries and templated prompts
- **Progressive Enhancement**: Works with minimal input, improves with more data

## API Interface

### PromptEngineer Class

```python
class PromptEngineer:
    def generate(self, query=None, template=None, prompt_id=None, prompt_data=None):
        """
        Generate a prompt from query or template with optional data substitution.

        Args:
            query (str, optional): Raw query string for prompt generation
            template (str, optional): Template string with optional UUID metadata
            prompt_id (str, optional): Explicit UUID for tracking
            prompt_data (dict, optional): Data to substitute into template

        Returns:
            Prompt: Object with .id and .text attributes

        Behavior:
            - If template contains <prompt_id>UUID</prompt_id>, extracts and uses that UUID
            - If prompt_id parameter provided, uses that UUID
            - Otherwise generates new UUID
            - Strips UUID metadata from template content
            - Substitutes prompt_data into template using string formatting
        """

    def update(self, response, prompt_id, feedback=None, ask_for_feedback=False):
        """
        Update prompt based on LLM response and optional feedback.

        Args:
            response (str): LLM response to learn from
            prompt_id (str): UUID of the prompt that generated this response
            feedback (str, optional): User-provided feedback string
            ask_for_feedback (bool, optional): Whether to request user feedback

        Behavior:
            - Uses provided feedback if available
            - Asks user for feedback if ask_for_feedback=True
            - Self-evaluates response if no feedback provided
            - Updates internal prompt/template based on evaluation
            - Maintains history of all interactions
        """
```

### Prompt Class

```python
class Prompt:
    def __init__(self, id, text):
        self.id = id      # UUID string for tracking
        self.text = text  # Final prompt text to send to LLM
```

## Data Structures

### Persistence Layer

Template versions and feedback history are stored in the local filesystem:

```
~/.dana/prteng/<prompt_id>/
├── template.json          # Current template content and metadata
├── versions/              # Template version history
│   ├── v1.json
│   ├── v2.json
│   └── ...
├── interactions/          # Response and feedback history
│   ├── 2024-01-15_10-30-45.json
│   ├── 2024-01-15_11-15-22.json
│   └── ...
└── metadata.json         # Prompt metadata and learning state
```

### Internal State

```python
class PromptEngineerState:
    # Runtime cache (loaded from ~/.dana/prteng/)
    prompts: Dict[str, Prompt]           # prompt_id -> Prompt
    templates: Dict[str, str]            # template_id -> template_content
    prompt_to_template: Dict[str, str]   # prompt_id -> template_id

    # Learning History (persisted to filesystem)
    interactions: List[Interaction]      # All prompt-response-feedback cycles
    evaluations: Dict[str, Evaluation]   # prompt_id -> evaluation results

    # Learning State (persisted to metadata.json)
    learned_patterns: Dict[str, Any]     # Extracted patterns and improvements
    success_metrics: Dict[str, float]    # Performance metrics per template
```

### Interaction Record

```python
@dataclass
class Interaction:
    prompt_id: str
    response: str
    feedback: Optional[str]
    evaluation: Optional[Evaluation]
    timestamp: datetime
    success_score: float
```

### Evaluation Result

```python
@dataclass
class Evaluation:
    prompt_id: str
    response: str
    criteria_scores: Dict[str, float]  # clarity, completeness, style, etc.
    overall_score: float
    improvement_suggestions: List[str]
    confidence: float
```

## Template Processing

### UUID Extraction

```python
def parse_template(template: str) -> Tuple[str, Optional[str]]:
    """
    Extract UUID from template metadata and return clean template.

    Format: <prompt_id>UUID</prompt_id> at start of template
    Returns: (clean_template, extracted_uuid)
    """
    uuid_pattern = r'<prompt_id>([a-f0-9-]{36})</prompt_id>'
    match = re.search(uuid_pattern, template, re.IGNORECASE)

    if match:
        uuid = match.group(1)
        clean_template = re.sub(r'<prompt_id>[^<]+</prompt_id>\s*', '', template)
        return clean_template.strip(), uuid

    return template, None
```

### Data Substitution

```python
def substitute_data(template: str, prompt_data: Dict[str, Any]) -> str:
    """
    Substitute prompt_data into template using Python string formatting.

    Supports: {key}, {key:format}, {key!conversion}
    """
    try:
        return template.format(**prompt_data)
    except KeyError as e:
        raise ValueError(f"Missing required template variable: {e}")
    except ValueError as e:
        raise ValueError(f"Template formatting error: {e}")
```

## Learning Mechanisms

### Self-Evaluation Criteria

```python
EVALUATION_CRITERIA = {
    "clarity": "Is the response clear and understandable?",
    "completeness": "Does the response fully address the prompt?",
    "accuracy": "Is the response factually correct?",
    "style": "Does the response match the desired style/tone?",
    "length": "Is the response an appropriate length?",
    "structure": "Is the response well-structured and organized?"
}
```

### Learning Strategies

1. **Pattern Recognition**: Identify successful prompt patterns
2. **Template Evolution**: Modify templates based on feedback
3. **Parameter Optimization**: Adjust template parameters for better results
4. **Context Learning**: Learn from similar prompts and responses
5. **User Preference Modeling**: Adapt to individual user preferences

### Update Algorithm

```python
def update_prompt(self, response: str, prompt_id: str, feedback: str = None):
    """
    Core learning algorithm:
    1. Evaluate response (self or user feedback)
    2. Identify improvement opportunities
    3. Update template/parameters
    4. Record interaction for future learning
    """
    # Get current prompt and template
    prompt = self.prompts[prompt_id]
    template_id = self.prompt_to_template[prompt_id]

    # Evaluate response
    if feedback:
        evaluation = self.parse_user_feedback(feedback)
    else:
        evaluation = self.self_evaluate(response, prompt)

    # Identify improvements
    improvements = self.identify_improvements(prompt, response, evaluation)

    # Update template
    if improvements:
        self.evolve_template(template_id, improvements)

    # Record interaction
    self.record_interaction(prompt_id, response, feedback, evaluation)
```

## Usage Examples

### Basic Usage

```python
engineer = PromptEngineer()

# Generate from query
prompt = engineer.generate("Write a Python function")
response = llm.generate(prompt.text)
engineer.update(response, prompt.id)

# Generate from template
system_template = "You are a helpful assistant that writes {style} explanations of {topic} for {audience}."
template_data = {"style": "simple", "topic": "AI", "audience": "beginners"}
prompt = engineer.generate("Write a Python function", system_template=system_template, template_data=template_data)
response = llm.generate(prompt.text)
engineer.update(response, prompt.id, feedback="Too technical")
```

### Template with UUID

```python
system_template = """
<prompt_id>550e8400-e29b-41d4-a716-446655440000</prompt_id>
You are a helpful assistant that creates {format} about {subject} with {tone} tone.
"""
template_data = {"format": "summary", "subject": "AI ethics", "tone": "professional"}
prompt = engineer.generate("Create a summary about AI ethics", system_template=system_template, template_data=template_data)
# Uses embedded UUID, strips metadata from template content
```

### Iterative Improvement

```python
engineer = PromptEngineer()
system_template = "You are a helpful assistant that writes {style} explanations of {topic}."

for iteration in range(5):
    prompt = engineer.generate("Explain machine learning", system_template=system_template, template_data={"style": "simple", "topic": "ML"})
    response = llm.generate(prompt.text)

    if iteration % 2 == 0:
        # Ask for user feedback occasionally
        engineer.update(response, prompt.id, ask_for_feedback=True)
    else:
        # Self-evaluate most of the time
        engineer.update(response, prompt.id)
```

## Implementation Notes

### Persistence Management

```python
class PromptEngineerPersistence:
    def __init__(self, base_dir="~/.dana/prteng"):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_prompt_dir(self, prompt_id: str) -> Path:
        """Get directory for specific prompt_id"""
        return self.base_dir / prompt_id

    def save_template_version(self, prompt_id: str, template: str, version: int):
        """Save template version to versions/v{version}.json"""
        prompt_dir = self.get_prompt_dir(prompt_id)
        versions_dir = prompt_dir / "versions"
        versions_dir.mkdir(exist_ok=True)

        version_file = versions_dir / f"v{version}.json"
        with open(version_file, 'w') as f:
            json.dump({
                "template": template,
                "version": version,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

    def save_interaction(self, prompt_id: str, interaction: Interaction):
        """Save interaction to interactions/ directory"""
        prompt_dir = self.get_prompt_dir(prompt_id)
        interactions_dir = prompt_dir / "interactions"
        interactions_dir.mkdir(exist_ok=True)

        timestamp = interaction.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        interaction_file = interactions_dir / f"{timestamp}.json"
        with open(interaction_file, 'w') as f:
            json.dump(asdict(interaction), f, indent=2, default=str)

    def load_prompt_history(self, prompt_id: str) -> List[Interaction]:
        """Load all interactions for a prompt_id"""
        prompt_dir = self.get_prompt_dir(prompt_id)
        interactions_dir = prompt_dir / "interactions"

        if not interactions_dir.exists():
            return []

        interactions = []
        for file_path in sorted(interactions_dir.glob("*.json")):
            with open(file_path, 'r') as f:
                data = json.load(f)
                interactions.append(Interaction(**data))

        return interactions
```

### UUID Generation
- Use standard UUID4 format
- Ensure uniqueness across all prompts and templates
- Maintain backward compatibility with existing UUIDs

### Error Handling
- Graceful handling of malformed templates
- Validation of UUID formats
- Fallback to auto-generation for invalid UUIDs
- Safe filesystem operations with proper error handling

### Performance Considerations
- Efficient template parsing and caching
- Lazy loading of interaction history
- Fast lookup for prompt/template relationships
- Minimal memory footprint with filesystem persistence

### Extensibility
- Plugin architecture for custom evaluation criteria
- Configurable learning algorithms
- Support for different LLM providers
- Pluggable persistence backends (filesystem, database, etc.)

## Future Enhancements

1. **Multi-Modal Support**: Images, audio, structured data
2. **Collaborative Learning**: Shared prompt libraries
3. **A/B Testing**: Compare prompt variations
4. **Analytics Dashboard**: Visualize learning progress
5. **Export/Import**: Share learned prompts across systems
