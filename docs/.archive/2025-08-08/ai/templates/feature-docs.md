# New Feature Documentation Templates

Use these templates when documenting new OpenDXA features across all audience trees.

## Context Variables Template

Before using any template, define these context variables:
- `FEATURE_NAME`: Name of the new feature
- `MODULE_PATH`: Where feature is implemented  
- `FEATURE_TYPE`: Agent capability/Dana language feature/Core system/etc.
- `PRIMARY_USE_CASES`: Main scenarios where this feature is used
- `DEPENDENCIES`: Required components or prerequisites

## Engineers Template (`docs/for-engineers/recipes/[feature-name].md`)

```markdown
# [FEATURE_NAME] - Practical Guide

## What You'll Build
[One sentence describing the end result users will achieve]

## Prerequisites
- [Required setup/knowledge]
- [Dependencies to install]
- [System requirements]

## Quick Start (5 minutes)
```dana
# Minimal working example that demonstrates core functionality
[basic_example_code]
```
**Expected Output:**
```
[exact_output_user_should_see]
```

## Step-by-Step Tutorial

### Step 1: [Initial Setup Action]
```dana
# [Comment explaining what this step accomplishes]
[code_for_step_1]
```
**What This Does:** [Explanation of step purpose]
**Expected Result:** [What user should observe]

### Step 2: [Next Action]
```dana
# [Comment for step 2]
[code_for_step_2]
```
**What This Does:** [Explanation]
**Expected Result:** [Observable outcome]

### Step 3: [Final Action]
```dana
# [Comment for final step]
[code_for_step_3]
```
**Final Result:** [Complete working implementation]

## Common Use Cases

### Use Case 1: [Specific Scenario]
**When to Use:** [Situation description]
**Implementation:**
```dana
# Complete working code for this scenario
[scenario_1_code]
```
**Expected Outcome:** [What this achieves]

### Use Case 2: [Another Scenario]
**When to Use:** [Different situation]
**Implementation:**
```dana
# Complete working code for scenario 2
[scenario_2_code]
```
**Expected Outcome:** [What this achieves]

## Advanced Configuration

### Customization Options
```dana
# How to customize behavior
[customization_code]
```

### Performance Tuning
```dana
# Optimization settings
[performance_code]
```

## Troubleshooting

### Common Issues

**Problem:** [Specific error or issue users encounter]
**Symptoms:** [How users recognize this problem]
**Solution:** [Step-by-step fix]
**Why This Happens:** [Brief technical explanation]

**Problem:** [Another common issue]
**Symptoms:** [Recognition signs]
**Solution:** [How to resolve]
**Prevention:** [How to avoid in future]

### Error Reference
- `[error_message_1]`: [Cause and fix]
- `[error_message_2]`: [Cause and fix]

## Integration with Existing Code

### Adding to Existing Projects
```dana
# How to integrate this feature into existing workflows
[integration_example]
```

### Migration from Previous Approaches
```dana
# If replacing older methods, show migration path
[migration_example]
```

## Next Steps
- [Link to related recipes]
- [Link to advanced topics]
- [Link to API reference]
```

## Evaluators Template (`docs/for-evaluators/roi-analysis/[feature-name].md`)

```markdown
# [FEATURE_NAME] - Business Analysis

## Executive Summary
[FEATURE_NAME] enables [business_capability] with [quantified_benefit], providing [competitive_advantage] for organizations implementing OpenDXA.

## Business Value Proposition

### Problem Solved
**Current Pain Point:** [What business problem this addresses]
**Impact of Problem:** [Cost/time/quality issues without solution]
**Target Users:** [Who benefits from this feature]

### Solution Provided
**How [FEATURE_NAME] Solves It:** [Mechanism of solution]
**Key Capabilities:** [What this feature enables]
**Unique Approach:** [What makes this different/better]

## Quantified Benefits

### Time Savings
- **Development Time:** [Hours saved vs manual implementation]
- **Operational Time:** [Ongoing time savings per use]
- **Maintenance Time:** [Reduced maintenance overhead]

### Cost Reduction
- **Development Costs:** [$ savings vs custom development]
- **Operational Costs:** [Ongoing cost reductions]
- **Infrastructure Costs:** [Resource efficiency gains]

### Quality Improvements
- **Accuracy:** [Measurable improvement in results]
- **Consistency:** [Reduction in variability]
- **Reliability:** [Uptime/error rate improvements]

### Scalability Benefits
- **Volume Handling:** [Increased capacity]
- **Performance:** [Speed improvements]
- **Resource Efficiency:** [Better resource utilization]

## Competitive Analysis

| Capability | OpenDXA | LangChain | AutoGen | Custom Solution |
|------------|---------|-----------|---------|-----------------|
| [Key Feature 1] | ✅ Native | ❌ Plugin required | ❌ Not available | 🔧 Custom dev needed |
| [Key Feature 2] | ✅ Built-in | ✅ Available | ✅ Available | 🔧 Significant effort |
| [Key Feature 3] | ✅ Optimized | ⚠️ Basic | ❌ Missing | 🔧 Possible but complex |

**OpenDXA Advantages:**
- [Specific advantage 1 with quantification]
- [Specific advantage 2 with evidence]
- [Unique capability not available elsewhere]

## Implementation Analysis

### Development Effort
**Estimated Implementation Time:**
- Small team (2-3 developers): [X weeks]
- Medium team (4-6 developers): [X weeks]  
- Large team (7+ developers): [X weeks]

**Skill Requirements:**
- [Required expertise level]
- [Specific technical skills needed]
- [Training requirements]

### Integration Complexity
**Technical Complexity:** [Low/Medium/High]
**Integration Points:** [Number and complexity of integrations]
**Testing Requirements:** [Scope of testing needed]
**Deployment Considerations:** [Infrastructure or process changes]

## ROI Analysis

### Investment Breakdown
**Initial Costs:**
- Development time: [Hours × hourly rate]
- Training: [Time and cost]
- Infrastructure: [Any additional resources]

**Ongoing Costs:**
- Maintenance: [Hours per month]
- Support: [Support overhead]
- Updates: [Upgrade effort]

### Return Calculation
**Monthly Benefits:** [Recurring value generated]
**Annual Benefits:** [Yearly value]
**Payback Period:** [Time to break even]
**3-Year ROI:** [Total return over 3 years]

### Break-Even Analysis
**Usage Threshold:** [Minimum usage for ROI]
**Time to Value:** [When benefits start accruing]
**Risk-Adjusted ROI:** [Conservative estimate]

## Risk Assessment

### Technical Risks
- **Risk:** [Potential technical issue]
- **Probability:** [Low/Medium/High]
- **Impact:** [Effect if it occurs]
- **Mitigation:** [How to reduce risk]

### Business Risks
- **Risk:** [Business impact concern]
- **Probability:** [Likelihood]
- **Impact:** [Business effect]
- **Mitigation:** [Risk reduction strategy]

### Adoption Risks
- **Risk:** [User adoption challenge]
- **Probability:** [Likelihood]
- **Impact:** [Effect on success]
- **Mitigation:** [Adoption strategy]

## Success Metrics

### Technical Metrics
- [Performance indicator 1]
- [Performance indicator 2]
- [Quality measure]

### Business Metrics
- [Business outcome 1]
- [Business outcome 2]
- [ROI indicator]

### User Metrics
- [User satisfaction measure]
- [Adoption rate]
- [Usage frequency]

## Implementation Roadmap

### Phase 1: Proof of Concept (Week 1-2)
- [Milestone 1]
- [Milestone 2]
- **Success Criteria:** [How to measure success]

### Phase 2: Pilot Implementation (Week 3-6)
- [Milestone 3]
- [Milestone 4]
- **Success Criteria:** [Pilot success measures]

### Phase 3: Full Deployment (Week 7-12)
- [Milestone 5]
- [Milestone 6]
- **Success Criteria:** [Full deployment success]

## Decision Framework

### Choose [FEATURE_NAME] When:
- [Specific business scenario 1]
- [Specific business scenario 2]
- [Decision criteria that favor this feature]

### Consider Alternatives When:
- [Scenario where other solutions might be better]
- [Constraints that might limit effectiveness]

### Next Steps for Evaluation
1. [Specific action for decision makers]
2. [Evaluation step or pilot recommendation]
3. [Resource or information to gather]
```

## Contributors Template (`docs/for-contributors/extending/[feature-name].md`)

```markdown
# [FEATURE_NAME] - Implementation Guide

## Architecture Overview

### High-Level Design
[Diagram or description of how this feature fits into overall system]

### Component Relationships
```
[ASCII diagram or description of component interactions]
```

### Data Flow
1. [Input processing step]
2. [Core processing step]
3. [Output generation step]

## Code Organization

### Main Implementation
**Primary Module:** `[MODULE_PATH]`
**Key Classes:**
- `[ClassName1]`: [Purpose and responsibility]
- `[ClassName2]`: [Purpose and responsibility]

**Key Functions:**
- `[function_name]()`: [What it does]
- `[another_function]()`: [Purpose]

### Dependencies
**Required Modules:**
- `[module1]` - [Why needed and how used]
- `[module2]` - [Purpose and integration]

**External Dependencies:**
- `[package1]` - [Reason for dependency]
- `[package2]` - [How it's used]

### Configuration
```python
# Configuration options and their effects
FEATURE_CONFIG = {
    'setting1': 'default_value',  # [What this controls]
    'setting2': 42,               # [Purpose and valid range]
    'setting3': True              # [Boolean option explanation]
}
```

## Key Components

### [Component 1 Name]
**Purpose:** [What this component does]
**Location:** `[file_path:line_numbers]`
**Key Methods:**
```python
def method_name(self, param1, param2):
    """[Brief description of what method does]"""
    # [Implementation notes]
```

**Responsibilities:**
- [Responsibility 1]
- [Responsibility 2]

### [Component 2 Name]
**Purpose:** [Component purpose]
**Location:** `[file_path:line_numbers]`
**Integration Points:** [How it connects to other components]

## Extension Points

### Customizing [Aspect 1]
**Extension Interface:**
```python
class Custom[FeatureName]Extension:
    def customize_behavior(self, [params]):
        """Override default behavior"""
        # Custom implementation
        pass
```

**Usage Example:**
```python
# How to use the extension
custom_extension = Custom[FeatureName]Extension()
feature.register_extension(custom_extension)
```

### Adding [Capability]
**Extension Pattern:**
```python
# How to extend the feature's capabilities
class Additional[Capability]:
    def new_method(self, [params]):
        # New functionality
        pass
```

### Configuration Extensions
```python
# How to add new configuration options
def register_custom_config(config_dict):
    # Configuration extension pattern
    pass
```

## Testing

### Test Organization
**Test Files:**
- `[test_file_1]` - [What aspects are tested]
- `[test_file_2]` - [Test scope]

**Test Categories:**
- Unit tests: [What's covered]
- Integration tests: [Integration scenarios]
- End-to-end tests: [Full workflow tests]

### Running Tests
```bash
# How to run feature-specific tests
pytest tests/[feature_test_directory]/

# How to run with coverage
pytest --cov=[module_path] tests/[feature_test_directory]/
```

### Adding New Tests
**Test Pattern:**
```python
# Template for new tests
class Test[FeatureName]:
    def test_[specific_behavior](self):
        # Test setup
        # Test execution
        # Assertions
        pass
```

**Mock Requirements:**
- [External dependency 1]: [How to mock]
- [External dependency 2]: [Mock strategy]

## Integration Patterns

### Agent Integration
```python
# How this feature integrates with agents
from opendxa.agent import Agent
from opendxa.[module] import [FeatureClass]

agent = Agent()
feature = [FeatureClass](config)
agent.add_capability(feature)
```

### Dana Language Integration
```dana
# How to use from Dana language
[dana_usage_example]
```

### Resource Integration
```python
# How feature uses system resources
from opendxa.common.resource import [ResourceType]

def integrate_with_resources(resource_manager):
    # Integration pattern
    pass
```

## Performance Considerations

### Time Complexity
- [Operation 1]: O([complexity])
- [Operation 2]: O([complexity])

### Memory Usage
- **Typical Usage:** [Memory footprint]
- **Peak Usage:** [Maximum memory]
- **Memory Optimization:** [How to reduce usage]

### Scalability
**Bottlenecks:**
- [Potential bottleneck 1]
- [Potential bottleneck 2]

**Optimization Strategies:**
- [Strategy 1 for better performance]
- [Strategy 2 for scalability]

### Monitoring
```python
# How to monitor feature performance
def monitor_performance():
    # Monitoring implementation
    pass
```

## Development Workflow

### Local Development
```bash
# Setup for local development
cd opendxa/
python -m pip install -e .
# [Additional setup steps]
```

### Testing Changes
```bash
# How to test modifications
python -m pytest tests/[feature_tests]/
# [Additional validation steps]
```

### Code Style
- Follow [style guide reference]
- Use [linting tools]
- [Specific conventions for this feature]

## Debugging

### Common Issues
**Issue:** [Development problem]
**Symptoms:** [How to recognize]
**Debug Steps:** [How to investigate]
**Solution:** [How to fix]

### Debug Tools
```python
# Debugging utilities
import logging
logger = logging.getLogger('[feature_name]')

def debug_feature_state():
    # Debug helper function
    pass
```

### Logging
```python
# Logging patterns for this feature
logger.debug(f"[Feature] Processing {input_data}")
logger.info(f"[Feature] Completed with result: {result}")
logger.error(f"[Feature] Error occurred: {error}")
```

## Future Enhancements

### Planned Improvements
- [Enhancement 1]: [Description and timeline]
- [Enhancement 2]: [Description and priority]

### Extension Opportunities
- [Area for extension 1]
- [Area for extension 2]

### Research Directions
- [Research question 1]
- [Research question 2]
```

## Researchers Template (`docs/for-researchers/research/[feature-name].md`)

```markdown
# [FEATURE_NAME] - Theoretical Foundations

## Research Context

### Problem Domain
**Academic Field:** [Primary research domain this addresses]
**Subdisciplines:** [Specific areas within the field]
**Research Community:** [Relevant academic communities]

### Theoretical Basis
**Foundational Theories:**
- [Theory 1]: [How it applies to this feature]
- [Theory 2]: [Relevance and application]

**Key Principles:**
- [Principle 1]: [How it guides implementation]
- [Principle 2]: [Influence on design]

## Design Rationale

### Problem Statement
**Theoretical Problem:** [What fundamental problem this solves]
**Existing Limitations:** [What current approaches can't do]
**Research Gap:** [What was missing in the literature]

### Approach Justification
**Why This Approach:** [Theoretical justification for design choices]
**Design Philosophy:** [Underlying philosophical principles]
**Trade-off Analysis:** [What was sacrificed for what benefits]

### Alternative Approaches Considered
**Approach 1:** [Alternative method]
- **Advantages:** [Benefits of this approach]
- **Disadvantages:** [Why it wasn't chosen]
- **Research Context:** [Academic work on this approach]

**Approach 2:** [Another alternative]
- **Advantages:** [Benefits]
- **Disadvantages:** [Limitations]
- **Comparison:** [How our approach differs]

## Academic Connections

### Related Papers
**Foundational Work:**
- [Author, Year]: "[Paper Title]"
  - **Relevance:** [How it influences this feature]
  - **Key Insights:** [What we learned from it]
  - **Extensions:** [How we build upon it]

**Contemporary Research:**
- [Author, Year]: "[Paper Title]"
  - **Comparison:** [How our work relates]
  - **Differences:** [What we do differently]
  - **Complementarity:** [How works complement each other]

**Emerging Directions:**
- [Author, Year]: "[Paper Title]"
  - **Future Potential:** [How this might influence future work]
  - **Research Questions:** [Questions this raises]

### Research Applications
**Direct Applications:**
- [Research scenario 1]: [How researchers can use this]
- [Research scenario 2]: [Another application]

**Experimental Opportunities:**
- [Experiment type 1]: [What could be studied]
- [Experiment type 2]: [Research possibilities]

**Validation Studies:**
- [Study design 1]: [How to validate effectiveness]
- [Study design 2]: [Alternative validation approach]

## Neurosymbolic Integration

### Symbolic Component
**Symbolic Representation:** [How symbolic reasoning is used]
**Logic Systems:** [Formal logic or reasoning systems involved]
**Knowledge Representation:** [How knowledge is structured]

### Neural Component
**Neural Architecture:** [Any AI/ML components]
**Learning Mechanisms:** [How system learns or adapts]
**Pattern Recognition:** [Neural pattern matching aspects]

### Hybrid Benefits
**Synergistic Effects:** [How symbolic + neural > sum of parts]
**Complementary Strengths:** [How each component compensates for other's weaknesses]
**Emergent Properties:** [New capabilities that emerge from combination]

### Theoretical Implications
**For Neurosymbolic AI:** [What this means for the field]
**For Cognitive Science:** [Implications for understanding cognition]
**For AI Safety:** [Safety considerations and implications]

## Experimental Validation

### Hypotheses
**Primary Hypothesis:** [Main claim this feature tests/proves]
**Secondary Hypotheses:** [Additional claims or predictions]
**Null Hypotheses:** [What would disprove the approach]

### Metrics and Evaluation
**Quantitative Metrics:**
- [Metric 1]: [How to measure, expected values]
- [Metric 2]: [Measurement approach, benchmarks]

**Qualitative Assessments:**
- [Assessment 1]: [How to evaluate qualitatively]
- [Assessment 2]: [Qualitative criteria]

### Baseline Comparisons
**Academic Baselines:**
- [Baseline 1]: [Standard academic comparison]
- [Baseline 2]: [Another comparison point]

**Industry Baselines:**
- [Industry standard 1]: [Commercial comparison]
- [Industry standard 2]: [Another industry benchmark]

### Expected Results
**Theoretical Predictions:** [What theory predicts should happen]
**Performance Expectations:** [Expected performance characteristics]
**Boundary Conditions:** [Where approach should/shouldn't work]

## Open Research Questions

### Immediate Questions
**Question 1:** [Research question this feature enables]
- **Approach:** [How to investigate]
- **Expected Timeline:** [Research timeline]
- **Required Resources:** [What's needed for investigation]

**Question 2:** [Another research direction]
- **Methodology:** [Research approach]
- **Challenges:** [Expected difficulties]
- **Potential Impact:** [Significance if answered]

### Long-term Directions
**Theoretical Extensions:**
- [Extension 1]: [How theory could be extended]
- [Extension 2]: [Another theoretical direction]

**Practical Applications:**
- [Application 1]: [Real-world research application]
- [Application 2]: [Another practical direction]

### Interdisciplinary Connections
**Field 1:** [How this connects to other disciplines]
**Field 2:** [Another interdisciplinary connection]
**Collaboration Opportunities:** [Potential research partnerships]

## Philosophical Context

### Relation to Dana Manifesto
**Core Alignment:** [How this aligns with Dana philosophy]
**Philosophical Principles:** [Which principles this embodies]
**Vision Advancement:** [How this advances the overall vision]

### Cognitive Science Connections
**Human Cognition:** [Links to human cognitive processes]
**Cognitive Models:** [Relevant cognitive science models]
**Implications:** [What this suggests about cognition]

### AI Safety Considerations
**Safety Properties:** [How this contributes to AI safety]
**Risk Factors:** [Potential safety concerns]
**Mitigation Strategies:** [How risks are addressed]

### Ethical Implications
**Ethical Considerations:** [Ethical aspects of this capability]
**Responsible Use:** [Guidelines for responsible application]
**Societal Impact:** [Broader implications for society]

## Future Research Agenda

### Short-term (6-12 months)
- [Research goal 1]: [Specific investigation]
- [Research goal 2]: [Another near-term goal]

### Medium-term (1-3 years)
- [Research direction 1]: [Longer-term investigation]
- [Research direction 2]: [Another medium-term goal]

### Long-term (3+ years)
- [Vision 1]: [Long-term research vision]
- [Vision 2]: [Another long-term direction]

### Collaboration Opportunities
**Academic Partnerships:** [Potential academic collaborations]
**Industry Connections:** [Industry research opportunities]
**Open Source Community:** [Community research directions]
```

## Usage Instructions

1. **Feature Analysis Phase**: Before using templates, thoroughly understand the feature implementation, integration points, use cases, and dependencies

2. **Template Customization**: Replace all bracketed placeholders with feature-specific content

3. **Audience Adaptation**: Ensure each template addresses the specific needs and interests of its target audience

4. **Cross-References**: Add appropriate links between audience-specific documentation

5. **Validation**: Test all code examples and verify all claims and metrics

6. **Consistency Check**: Ensure feature descriptions align across all audience trees while maintaining appropriate focus for each audience 