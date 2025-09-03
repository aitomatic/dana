# Function Documentation Templates

Use these templates when documenting new or modified functions across all audience trees.

## Engineers Template (`docs/for-engineers/reference/functions.md`)

```markdown
## [FUNCTION_NAME]
**Signature**: `function_name(param1: type, param2: type) -> return_type`
**Purpose**: [One sentence describing what this function does for practical use]

**Quick Example:**
```dana
# Minimal working example
result = function_name("example_input", default_param)
log(f"Result: {result}")
```
**Expected Output:** `Result: [expected_value]`

**Common Use Cases:**
- **[Scenario 1]**: [Specific practical application]
- **[Scenario 2]**: [Another concrete use case]

**Parameters:**
- `param1` (type): [Description of what this parameter does]
- `param2` (type, optional): [Description, include default value]

**Returns:**
- `return_type`: [Description of return value]

**Troubleshooting:**
- **Error**: `[common_error_message]`
- **Cause**: [Why this happens]
- **Fix**: [Specific solution]

**Integration Examples:**
```dana
# How to use with existing workflows
existing_data = load_data("file.txt")
processed = function_name(existing_data, custom_param)
save_result(processed, "output.txt")
```
```

## Evaluators Template (`docs/for-evaluators/roi-analysis/new-capabilities.md`)

```markdown
## [FUNCTION_NAME] - Business Value Analysis

**Executive Summary:** [One sentence business value proposition]

**Quantified Benefits:**
- **Time Savings**: [X minutes/hours saved per use vs manual approach]
- **Cost Reduction**: [Estimated $ savings or efficiency gain]
- **Quality Improvement**: [Measurable accuracy/consistency improvement]
- **Scalability**: [How this enables handling larger volumes]

**Competitive Advantage:**
- **vs LangChain**: [How our implementation differs/excels]
- **vs AutoGen**: [Unique capabilities or ease of use]
- **vs Custom Solution**: [Development time savings, maintenance benefits]

**Implementation Investment:**
- **Development Time**: [Hours for typical integration]
- **Learning Curve**: [Low/Medium/High with explanation]
- **Integration Complexity**: [Technical difficulty assessment]
- **Resource Requirements**: [Team size, skill level needed]

**ROI Analysis:**
- **Initial Investment**: [Time/cost to implement]
- **Ongoing Benefits**: [Recurring value generated]
- **Payback Period**: [When benefits outweigh implementation costs]
- **Break-even Point**: [Specific usage threshold for ROI]

**Risk Assessment:**
- **Technical Risks**: [What could go wrong technically]
- **Business Risks**: [Impact on operations if issues occur]
- **Mitigation Strategies**: [How to reduce identified risks]

**Success Metrics:**
- [Measurable outcome 1]
- [Measurable outcome 2]
- [Key performance indicator]
```

## Contributors Template (`docs/for-contributors/extending/function-development.md`)

```markdown
## [FUNCTION_NAME] Implementation Details

**Code Location:** `[file_path:line_numbers]`
**Module Dependencies:**
- `[module1]` - [why needed]
- `[module2]` - [purpose]

**Architecture Integration:**
- **Input Processing**: [How parameters are handled]
- **Core Logic**: [Main algorithm or process]
- **Output Generation**: [Return value construction]
- **Error Handling**: [Exception management approach]
- **State Management**: [How function interacts with system state]

**Key Components:**
```python
# Core implementation structure
class [ClassName]:
    def [method_name](self, [params]):
        # [Brief description of what this does]
        pass
```

**Extension Points:**
```python
# How to customize this function
class CustomFunctionExtension:
    def override_behavior(self, [params]):
        # Extension pattern
        pass

# Configuration options
FUNCTION_CONFIG = {
    'setting1': 'default_value',
    'setting2': 'another_default'
}
```

**Testing Approach:**
- **Test File**: `[test_file_path]`
- **Key Test Cases**: [Critical scenarios tested]
- **Mock Requirements**: [External dependencies that need mocking]
- **How to Add Tests**: [Pattern to follow for new tests]

**Performance Characteristics:**
- **Time Complexity**: [Big O notation if applicable]
- **Memory Usage**: [Typical memory footprint]
- **Scalability Considerations**: [Limits or bottlenecks]
- **Optimization Opportunities**: [Areas for future improvement]

**Integration Patterns:**
```python
# Common integration with other components
from opendxa.agent.capability import [CapabilityClass]

def integrate_with_agent(agent, [params]):
    # Integration example
    pass
```

**Development Notes:**
- [Important implementation decisions]
- [Known limitations or trade-offs]
- [Future enhancement possibilities]
```

## Researchers Template (`docs/for-researchers/research/capability-evolution.md`)

```markdown
## [FUNCTION_NAME] - Theoretical Foundations

**Research Domain:** [Academic field this addresses]
**Theoretical Basis:** [Academic theories or papers this builds on]

**Design Rationale:**
- **Problem Statement**: [What theoretical problem this solves]
- **Approach Justification**: [Why this specific implementation]
- **Alternative Methods Considered**: [Other approaches evaluated]
- **Trade-offs Made**: [What was sacrificed for what benefits]

**Academic Connections:**
- **Related Papers**: [Specific academic works that influence this]
  - [Author, Year]: "[Paper Title]" - [How it relates]
  - [Author, Year]: "[Paper Title]" - [Relevance to implementation]
- **Research Applications**: [How researchers might use this capability]
- **Open Questions**: [Research directions this enables or requires]

**Neurosymbolic Integration:**
- **Symbolic Component**: [How this relates to symbolic reasoning]
- **Neural Component**: [Any AI/ML integration aspects]
- **Hybrid Benefits**: [Advantages of the combined approach]
- **Theoretical Implications**: [What this means for neurosymbolic AI]

**Experimental Validation:**
- **Hypothesis**: [What this function is designed to test/prove]
- **Metrics**: [How effectiveness can be measured]
- **Baseline Comparisons**: [What to compare against]
- **Expected Results**: [Theoretical predictions]

**Future Research Directions:**
- [Research question 1 enabled by this capability]
- [Research question 2 that could extend this work]
- [Theoretical gaps that remain to be addressed]

**Philosophical Context:**
- **Relation to Dana Manifesto**: [How this aligns with core philosophy]
- **Cognitive Science Connections**: [Links to human cognition research]
- **AI Safety Considerations**: [Implications for safe AI development]
```

## AI Assistant Reference Template (`docs/.ai-only/functions.md`)

```markdown
### [FUNCTION_NAME]
**Module:** `[module.submodule]`
**Signature:** `[complete_signature_with_types]`
**Purpose:** [Concise one-line description]
**Primary Use Cases:** [Brief list]

**Quick Reference:**
```dana
# Minimal working example
result = function_name("example_input", default_param)
log(f"Result: {result}")
```

**Documentation Links:**
- Engineers: [link_to_practical_guide]
- Evaluators: [link_to_business_analysis]  
- Contributors: [link_to_implementation_details]
- Researchers: [link_to_theoretical_context]

**Common Patterns:**
- [Pattern 1]: [Brief description]
- [Pattern 2]: [Brief description]

**Error Patterns:**
- `[error_message]`: [Common cause and fix]
- `[another_error]`: [Cause and solution]

**Related Functions:**
- `[related_function_1]`: [How they work together]
- `[related_function_2]`: [Relationship]
```

## Usage Instructions

1. **For New Functions**: Use all templates to create comprehensive documentation
2. **For Modified Functions**: Update relevant sections in existing documentation
3. **Validation**: Test all Dana code examples with `bin/dana`
4. **Cross-References**: Add links between audience-specific documentation
5. **Consistency**: Ensure function descriptions align across all audiences 