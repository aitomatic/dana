# OpenDXA Documentation Maintenance Prompts

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

## Essential Context for All Prompts

**Key Reference Files** (Read before executing any prompt):
- `docs/archive/original-dana/manifesto.md` - Authoritative philosophy and vision
- `docs/archive/original-dana/language.md` - Complete Dana language specification
- `docs/archive/original-dana/syntax.md` - Current Dana syntax rules
- `docs/for-engineers/reference/dana-syntax.md` - Practical Dana reference for developers
- `docs/for-researchers/manifesto/vision.md` - Updated philosophical foundations
- `docs/.ai-only/opendxa.md` - System overview and components
- `docs/.ai-only/functions.md` - Current function catalog
- `docs/.ai-only/project.md` - Directory structure guide

**Current Documentation State (Updated 2025-01-24)**:
- `docs/README.md` - Audience routing hub (keep as-is)
- `docs/for-engineers/` - Practical guides, recipes, and references for developers
- `docs/for-evaluators/` - Business ROI, competitive analysis, and proof of concepts
- `docs/for-contributors/` - Architecture, codebase navigation, and development guides
- `docs/for-researchers/` - Philosophy, theory, neurosymbolic research, and manifesto
- `docs/archive/` - Preserved original documentation (original-dana/, original-core-concepts/, original-architecture/)
- `docs/.ai-only/` - AI assistant reference materials

**Target Audience Organization**:
```
docs/
├── for-engineers/       # Task-oriented, practical guides
├── for-evaluators/     # Business ROI, competitive analysis
├── for-contributors/   # Technical architecture, development
├── for-researchers/    # Philosophy, theory, academic context
└── .ai-only/          # AI assistant structured references
```

---

## Daily Maintenance Prompts

### PROMPT 1: Function Registry Scan & Documentation Update

**Copy-Paste Ready Instructions:**

```bash
# STEP 1: Check for new/modified functions (past 24 hours)
find opendxa/dana/ opendxa/agent/capability/ opendxa/common/ -name "*.py" -newer docs/.ai-only/functions.md -exec echo "Modified: {}" \;

# STEP 2: Extract function signatures from new files
grep -n "def " [MODIFIED_FILES] | grep -v "__"
```

**For Each New Function Found:**

1. **Extract Function Details:**
   - Function signature and parameters
   - Docstring content
   - Any inline code examples
   - Identify primary use cases

2. **Update Engineer Documentation** (`docs/for-engineers/reference/functions.md`):
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

**Troubleshooting:**
- **Error**: `[common_error_message]`
- **Cause**: [Why this happens]
- **Fix**: [Specific solution]
```

3. **Update Evaluator Documentation** (`docs/for-evaluators/roi-analysis/new-capabilities.md`):
```markdown
## [FUNCTION_NAME] - Business Value Analysis

**Executive Summary:** [One sentence business value proposition]

**Quantified Benefits:**
- **Time Savings**: [X minutes/hours saved per use vs manual approach]
- **Cost Reduction**: [Estimated $ savings or efficiency gain]
- **Quality Improvement**: [Measurable accuracy/consistency improvement]

**Competitive Advantage:**
- **vs LangChain**: [How our implementation differs/excels]
- **vs AutoGen**: [Unique capabilities or ease of use]
- **vs Custom Solution**: [Development time savings, maintenance benefits]

**Implementation Investment:**
- **Development Time**: [Hours for typical integration]
- **Learning Curve**: [Low/Medium/High with explanation]
- **Integration Complexity**: [Technical difficulty assessment]

**ROI Timeline:** [When benefits outweigh implementation costs]
```

4. **Update Contributor Documentation** (`docs/for-contributors/extending/function-development.md`):
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

**Extension Points:**
```python
# How to customize this function
class CustomFunctionExtension:
    def override_behavior(self, [params]):
        # Extension pattern
        pass
```

**Testing Approach:**
- **Test File**: `[test_file_path]`
- **Key Test Cases**: [Critical scenarios tested]
- **How to Add Tests**: [Pattern to follow for new tests]

**Performance Characteristics:**
- **Time Complexity**: [Big O notation if applicable]
- **Memory Usage**: [Typical memory footprint]
- **Scalability Considerations**: [Limits or bottlenecks]
```

5. **Update Researcher Documentation** (`docs/for-researchers/research/capability-evolution.md`):
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
- **Research Applications**: [How researchers might use this capability]
- **Open Questions**: [Research directions this enables or requires]

**Neurosymbolic Integration:**
- **Symbolic Component**: [How this relates to symbolic reasoning]
- **Neural Component**: [Any AI/ML integration aspects]
- **Hybrid Benefits**: [Advantages of the combined approach]
```

6. **Update AI Assistant Reference** (`docs/.ai-only/functions.md`):
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
```

7. **Test All Examples:**
```bash
# Extract Dana code from new documentation
grep -A 10 "```dana" [modified_doc_files] > temp_examples.na
# Test each example
bin/dana temp_examples.na
# Verify outputs match documented expectations
```

**Completion Checklist:**
- [ ] Function signature and purpose documented
- [ ] Working code examples tested with `bin/dana`
- [ ] All 4 audience trees updated with appropriate content
- [ ] .ai-only reference updated for AI assistant use
- [ ] Cross-references added where relevant
- [ ] Examples verified to produce expected outputs

---

### PROMPT 2: Dana Code Example Validation & Syntax Updates

**Copy-Paste Ready Instructions:**

```bash
# STEP 1: Find all Dana code examples in documentation
find docs/ -name "*.md" -exec grep -l "```dana" {} \; > dana_example_files.txt

# STEP 2: Extract code blocks and test them
while read file; do
    echo "Processing $file"
    sed -n '/```dana/,/```/p' "$file" | sed '1d;$d' > "temp_${file##*/}.na"
    # Test if the code runs
    if bin/dana "temp_${file##*/}.na"; then
        echo "✅ $file examples work"
    else
        echo "❌ $file has broken examples"
    fi
done < dana_example_files.txt
```

**For Each Broken Example:**

1. **Identify the Issue:**
   - Compare against current syntax in `docs/dana/syntax.md`
   - Check variable scope syntax (`private:`, `public:`, `system:`, `local:`)
   - Verify function call patterns match `docs/dana/language.md`
   - Validate REPL commands against `docs/dana/repl.md`

2. **Common Syntax Fixes Needed:**

**Variable Scope Updates:**
```dana
# OLD (if found):
x = 10
# NEW:
x = 10  # Auto-scoped to local (preferred)

# OLD:
global_var = "value"
# NEW:  
public:global_var = "value"
```

**Function Call Updates:**
```dana
# Check current reason() syntax in docs/dana/language.md
# OLD (if outdated):
result = reason("prompt")
# NEW (verify current format):
result = reason("prompt", context=context)
```

**F-String Formatting:**
```dana
# Ensure current f-string syntax
# Should match patterns in docs/dana/syntax.md
log(f"Value is {private:variable_name}")
```

**REPL Command Updates:**
```dana
# Check docs/dana/repl.md for current commands
# Ensure ##nlp on/off syntax is current
# Verify multiline input patterns
```

3. **Update Examples While Preserving Purpose:**
   - Keep the same learning objective
   - Maintain pedagogical flow
   - Add expected output where missing
   - Include error examples where helpful

4. **Standard Example Format:**
```markdown
**Example: [Purpose of example]**
```dana
# [Brief comment explaining what this does]
input_data = "example_data"
result = function_name(input_data)
log(f"Result: {result}")
```
**Expected Output:**
```
Result: [specific_expected_output]
```

**Common Variations:** [If applicable, show alternative approaches]
```

5. **Validate Against Current Best Practices:**
   - Check examples in `examples/dana/na/` directory for current patterns
   - Ensure consistency with `basic_assignments.na`
   - Match reasoning patterns from `reason_demo.na`
   - Follow scope usage from `multiple_scopes.na`

6. **Test Updated Examples:**
```bash
# For each updated file
bin/dana updated_example.na
# Verify output matches documentation
# Ensure no errors or warnings
```

**Completion Checklist:**
- [ ] All Dana code blocks identified and extracted
- [ ] Broken examples fixed with current syntax
- [ ] Pedagogical purpose preserved in all updates
- [ ] Expected outputs documented where missing
- [ ] Examples tested with current `bin/dana`
- [ ] Consistency with official examples verified

---

## Weekly Analysis Prompts

### PROMPT 3: Documentation Gap Analysis & Issue Creation

**Copy-Paste Ready Instructions:**

```bash
# STEP 1: Analyze recent codebase changes
git log --since="7 days ago" --name-only --pretty=format: | grep -E '\.(py|md)$' | sort -u > recent_changes.txt

# STEP 2: Check for new modules without documentation
find opendxa/ -name "*.py" -newer docs/.ai-only/opendxa.md -exec echo "New module: {}" \;

# STEP 3: Identify new capabilities
find opendxa/agent/capability/ -name "*.py" -newer docs/.ai-only/functions.md

# STEP 4: Check for new examples
find examples/dana/na/ -name "*.na" -newer docs/.ai-only/dana.md
```

**Gap Analysis Process:**

1. **For Each New Module/Feature Found:**

**Engineer Impact Assessment:**
- **Missing**: Step-by-step implementation guides
- **Need**: Copy-paste code recipes for common use cases  
- **Missing**: Troubleshooting documentation for new error patterns
- **Need**: Integration examples with existing workflows

**Evaluator Impact Assessment:**
- **Missing**: Business value quantification and ROI analysis
- **Need**: Competitive positioning vs LangChain/AutoGen
- **Missing**: Implementation effort and resource requirements
- **Need**: Risk assessment and mitigation strategies

**Contributor Impact Assessment:**
- **Missing**: Architecture documentation for new components
- **Need**: Extension points and customization guides
- **Missing**: Testing patterns and development workflows
- **Need**: Code organization and dependency explanations

**Researcher Impact Assessment:**
- **Missing**: Theoretical foundations and design rationale
- **Need**: Academic connections and research implications
- **Missing**: Experimental results or validation studies
- **Need**: Future research directions enabled by new capabilities

2. **Gap Priority Assessment:**

**High Priority (Blocks User Success):**
```markdown
## Critical Documentation Gaps

### [Feature/Module Name]
**Impact**: Users cannot successfully implement basic use cases
**Affected Audiences**: Engineers (primary), Evaluators (secondary)
**Required Documentation**:
- `docs/for-engineers/recipes/[feature-name].md` - Step-by-step implementation
- `docs/for-engineers/troubleshooting/[feature-name].md` - Common issues
**Estimated Effort**: [X hours]
**Business Impact**: [Potential user frustration, adoption blockers]
```

**Medium Priority (Affects Adoption):**
```markdown
### [Feature/Module Name] 
**Impact**: Decision makers lack sufficient context for adoption
**Affected Audiences**: Evaluators (primary), Contributors (secondary)
**Required Documentation**:
- `docs/for-evaluators/roi-analysis/[feature-name].md` - Business value
- `docs/for-evaluators/comparison/[feature-name].md` - Competitive analysis
**Estimated Effort**: [X hours] 
**Business Impact**: [Slower adoption, unclear value proposition]
```

**Low Priority (Enhancement):**
```markdown
### [Feature/Module Name]
**Impact**: Researchers lack theoretical grounding
**Affected Audiences**: Researchers (primary)
**Required Documentation**:
- `docs/for-researchers/research/[feature-name].md` - Academic context
**Estimated Effort**: [X hours]
**Business Impact**: [Limited research collaboration, reduced academic credibility]
```

3. **Create GitHub Issues:**

**Issue Template for High Priority Gaps:**
```markdown
Title: [DOCS][HIGH] Missing engineer guide for [Feature Name]

## Gap Description
New feature [Feature Name] in `[module path]` lacks practical implementation documentation.

## User Impact
- Engineers cannot successfully implement [specific use case]
- No troubleshooting guidance for [common error scenarios] 
- Missing integration examples with existing OpenDXA workflows

## Required Documentation
- [ ] `docs/for-engineers/recipes/[feature-name].md` - Complete implementation guide
- [ ] `docs/for-engineers/reference/[feature-name].md` - Function/API reference
- [ ] `docs/for-engineers/troubleshooting/[feature-name].md` - Error resolution

## Acceptance Criteria
- [ ] Working code examples that execute with `bin/dana`
- [ ] Step-by-step tutorial from setup to working implementation
- [ ] Common error scenarios with specific solutions
- [ ] Integration patterns with existing agent capabilities

## Priority Justification
High - Blocks user success in implementing [core functionality]

## Estimated Effort
[X hours] for complete documentation across all requirements

Labels: documentation, high-priority, user-blocking
```

4. **Cross-Reference Updates Needed:**
```markdown
## Documentation Updates Required

### .ai-only Updates
- [ ] Add new capabilities to `docs/.ai-only/opendxa.md`
- [ ] Update function catalog in `docs/.ai-only/functions.md`
- [ ] Enhance quick reference in `docs/.ai-only/dana.md`

### Cross-Audience Links
- [ ] Link engineer recipes to evaluator ROI analysis
- [ ] Connect contributor architecture docs to researcher theory
- [ ] Reference new capabilities in appropriate README files

### Example Integration
- [ ] Add new patterns to `examples/dana/na/` if missing
- [ ] Reference official examples in documentation
- [ ] Ensure consistency between examples and docs
```

**Completion Checklist:**
- [ ] All recent code changes analyzed for documentation impact
- [ ] Gaps categorized by audience and priority level
- [ ] GitHub issues created for high/medium priority gaps
- [ ] Effort estimates provided for planning purposes
- [ ] Cross-reference update requirements identified

---

### PROMPT 4: Competitive Analysis Update

**Copy-Paste Ready Instructions:**

**Required Research Before Starting:**
1. Review current competitive documentation:
   - `docs/for-evaluators/comparison/vs-langchain.md`
   - `docs/for-evaluators/comparison/vs-autogen.md`  
   - `docs/for-evaluators/comparison/competitive-matrix.md`

2. Check OpenDXA's current positioning:
   - `docs/dana/manifesto.md` - Core philosophy and differentiators
   - `docs/.ai-only/opendxa.md` - Current capabilities summary

**Research Tasks:**
```bash
# STEP 1: Check for recent competitor releases
# (Manual research required)
# - Visit LangChain GitHub releases and documentation
# - Check AutoGen announcements and feature updates  
# - Search for new neurosymbolic/agent frameworks
# - Review competitor marketing claims and positioning

# STEP 2: Document findings
echo "Competitor Updates Found:" > competitive_analysis.md
echo "- LangChain: [update summary]" >> competitive_analysis.md
echo "- AutoGen: [update summary]" >> competitive_analysis.md  
echo "- New Competitors: [if any]" >> competitive_analysis.md
```

**Update Process:**

1. **Revise Feature Comparison Matrices:**

**Standard Comparison Format:**
```markdown
## OpenDXA vs [Competitor] - Updated [DATE]

### Recent Developments
**[Competitor] Updates**: [Brief summary of new features/claims]
**Impact on Positioning**: [How this affects competitive landscape]

### Updated Feature Matrix
| Capability | OpenDXA | [Competitor] | Advantage Analysis |
|------------|---------|--------------|-------------------|
| **Neurosymbolic Integration** | ✅ Native language support | ❌ External library required | Simpler, more integrated |
| **Agent Development** | ✅ Dana DSL + visual tools | ✅ Python frameworks | Domain-specific language benefits |
| **Reasoning Integration** | ✅ First-class `reason()` function | ⚠️ Plugin-based | Built-in vs bolt-on approach |
| **[New Competitor Feature]** | [Our status] | ✅ Recently added | [Honest assessment] |

### OpenDXA Sustained Advantages
**Unique Differentiators** (unchanged by competitor updates):
- **Domain-Specific Language**: Dana provides agent-native syntax
- **Neurosymbolic Design**: Built-in symbolic + neural integration
- **Cognitive Architecture**: Explicit state management and scoping
- **[Additional unique advantages]**

### Competitive Response Strategy
**Maintain Advantage Areas:**
- Emphasize Dana language benefits vs general-purpose Python
- Highlight integrated neurosymbolic approach vs plugin architectures

**Address New Competitor Strengths:**
- [If competitor added feature we lack]: Acknowledge gap, reference roadmap
- [If competitor improved existing feature]: Compare implementation approaches

### Updated Recommendations
**Choose OpenDXA When:**
- Building complex multi-agent systems requiring coordination
- Need explicit symbolic reasoning with neural components
- Want domain-specific language for agent development
- Require transparent, auditable agent decision-making

**Consider [Competitor] When:**
- [Honest assessment of when they might be better choice]
- [Specific use cases where they excel]
```

2. **Update Business Value Propositions:**

**ROI Analysis Updates:**
```markdown
## Updated ROI Analysis: OpenDXA vs Alternatives

### Development Velocity
**OpenDXA**: [X hours] average for typical agent implementation
**[Competitor]**: [Y hours] for equivalent functionality
**Advantage**: [X-Y hours] savings = [dollar value] per project

### Maintenance Overhead  
**OpenDXA**: [Maintenance characteristics with Dana language]
**[Competitor]**: [Maintenance overhead with their approach]
**Long-term Impact**: [Total cost of ownership comparison]

### New Competitive Factors
**[Recent competitor feature]**: [How this affects ROI calculus]
**Response**: [How OpenDXA's approach provides different value]
```

3. **Update Positioning Statements:**

**Across All Evaluator Documentation:**
- Scan for outdated competitive claims
- Update feature availability statements
- Revise "vs competitor" language where needed
- Ensure consistency with manifesto positioning

4. **Enhance AI Assistant Competitive Responses:**

**Update `docs/.ai-only/competitive-responses.md`:**
```markdown
## Competitive Q&A - Updated [DATE]

### Recent Competitive Developments
**[Competitor] Update**: [Summary]
**Key Impact**: [How this changes competitive conversations]

### Updated Response Patterns

**Q: "How does OpenDXA compare to [Competitor's new feature]?"**
**A**: [Factual comparison highlighting our approach benefits]
**Key Points**:
- [Point 1]: [Our architectural advantage]
- [Point 2]: [Specific benefits of our approach]
- [Point 3]: [Long-term strategic advantages]

**Q: "Why not just use [Competitor] since they added [feature]?"**
**A**: [Response emphasizing unique value proposition]
**Redirect to**: [Link to detailed comparison documentation]
```

**Completion Checklist:**
- [ ] Recent competitor developments researched and documented
- [ ] Feature comparison matrices updated with new information
- [ ] Business value propositions revised for changed landscape
- [ ] Positioning statements updated across all evaluator docs
- [ ] AI assistant responses updated for new competitive questions
- [ ] Consistency verified across all competitive documentation

---

## Event-Driven Maintenance Prompts

### PROMPT 5: New Feature Complete Documentation

**Context Setup** (Fill in when using):
```
FEATURE_NAME: [Name of new feature]
MODULE_PATH: [Implementation location]
FEATURE_TYPE: [Dana language feature / Agent capability / Core system]
```

**Pre-Documentation Research:**
```bash
# STEP 1: Understand the feature implementation
find . -name "*.py" -exec grep -l "[FEATURE_NAME]" {} \;
grep -r "[FEATURE_NAME]" opendxa/ --include="*.py" -A 5 -B 5

# STEP 2: Identify integration points
grep -r "[FEATURE_NAME]" examples/dana/na/ --include="*.na"
grep -r "[FEATURE_NAME]" docs/ --include="*.md"

# STEP 3: Test feature functionality
# [Manual testing of feature to understand behavior]
```

**Complete Documentation Creation:**

1. **Engineers Documentation** (`docs/for-engineers/recipes/[feature-name].md`):

```markdown
# [FEATURE_NAME] - Practical Implementation Guide

## What You'll Build
[One clear sentence describing the end result users will achieve]

## Prerequisites
**System Requirements:**
- OpenDXA [version] or later
- [Any additional dependencies]

**Knowledge Requirements:**
- Basic Dana language syntax ([link to docs/for-engineers/reference/dana-syntax.md])
- [Any specific background needed]

## 5-Minute Quick Start
```dana
# Minimal working example
input_data = "example_input"
result = [feature_function](input_data)
log(f"[FEATURE_NAME] result: {result}")
```
**Expected Output:**
```
[FEATURE_NAME] result: [specific_expected_output]
```

## Complete Step-by-Step Tutorial

### Step 1: Initial Setup
```dana
# Setup code with explanations
private:config = {
    "setting1": "value1",
    "setting2": "value2"
}
```
**What This Does:** [Explanation of setup purpose]
**Expected Result:** [What user should see after this step]

### Step 2: Core Implementation
```dana
# Main feature usage
private:feature_instance = create_[feature_name](private:config)
private:processed_data = private:feature_instance.process(private:input_data)
```
**What This Does:** [Explanation of core functionality]
**Expected Result:** [Observable outcomes]

### Step 3: Advanced Usage
```dana
# Advanced patterns and customization
private:advanced_config = {
    "advanced_setting": "custom_value",
    "callback": custom_handler
}
# [Complete advanced example]
```

## Real-World Use Cases

### Use Case 1: [Specific Business Scenario]
**Scenario:** [Detailed description of when/why to use this]
**Implementation:**
```dana
# Complete working code for this scenario
# Include all necessary setup and error handling
```
**Business Value:** [How this solves real problems]

### Use Case 2: [Another Practical Application]
**Scenario:** [Different use case description]
**Implementation:**
```dana
# Complete working code for second scenario
```

## Integration Patterns

### With Existing Agents
```dana
# How to add this feature to existing agent implementations
```

### With Other OpenDXA Features  
```dana
# Common combinations and integration patterns
```

## Troubleshooting Guide

### Common Issue 1
**Problem:** [Specific error message or behavior]
**Cause:** [Why this happens]
**Solution:** [Step-by-step fix]
**Prevention:** [How to avoid this issue]

### Common Issue 2
**Problem:** [Another typical problem]
**Cause:** [Root cause explanation]  
**Solution:** [Detailed resolution steps]

## Performance Considerations
- **Memory Usage:** [Typical memory requirements]
- **Processing Time:** [Expected performance characteristics]
- **Scalability:** [Limits and bottlenecks to be aware of]

## Next Steps
- [Link to related features that work well together]
- [Advanced topics or extensions to explore]
- [Community resources or examples]
```

2. **Evaluators Documentation** (`docs/for-evaluators/roi-analysis/[feature-name].md`):

```markdown
# [FEATURE_NAME] - Business Impact Analysis

## Executive Summary
[FEATURE_NAME] enables [business capability] with [quantified benefits], providing [competitive advantage] for organizations implementing [use case category].

## Business Problem & Solution

### Problem Statement
**Current Challenge:** [Specific business pain point this addresses]
**Cost of Status Quo:** [Quantified cost of not having this capability]
**Market Opportunity:** [Business opportunity enabled by this feature]

### Solution Overview
**How [FEATURE_NAME] Solves It:** [Clear explanation of solution approach]
**Key Differentiators:** [What makes our solution unique]

## Quantified Business Benefits

### Time Savings Analysis
**Before [FEATURE_NAME]:**
- [Task 1]: [X hours per occurrence]
- [Task 2]: [Y hours per occurrence]
- **Total Time per [Period]:** [Total hours]

**With [FEATURE_NAME]:**
- [Task 1]: [Reduced time] (X% reduction)
- [Task 2]: [Reduced time] (Y% reduction)  
- **Total Time per [Period]:** [New total] 
- **Net Savings:** [Hours saved] = [Dollar value at $Z/hour]

### Quality Improvements
**Accuracy Gains:** [Measurable improvement in accuracy/consistency]
**Error Reduction:** [Specific errors eliminated or reduced]
**Compliance Benefits:** [Regulatory or policy compliance advantages]

### Cost Reduction Areas
**Infrastructure Savings:** [Reduced hardware/cloud costs if applicable]
**Personnel Efficiency:** [Staff time reallocated to higher value work]
**Maintenance Reduction:** [Lower ongoing maintenance requirements]

## Competitive Analysis

### vs LangChain
| Aspect | OpenDXA [FEATURE_NAME] | LangChain Equivalent | Advantage |
|--------|------------------------|---------------------|-----------|
| Implementation | [Our approach] | [Their approach] | [Specific advantage] |
| Time to Value | [Our timeline] | [Their timeline] | [Quantified difference] |
| Maintenance | [Our requirements] | [Their requirements] | [Long-term benefit] |

### vs AutoGen  
[Similar comparison format]

### vs Custom Development
**Build vs Buy Analysis:**
- **Custom Development Cost:** [Estimated development effort and cost]
- **OpenDXA Implementation Cost:** [Our implementation effort and licensing]
- **Ongoing Maintenance:** [Comparison of long-term costs]
- **Risk Assessment:** [Technical and business risks of each approach]

## Implementation Investment

### Development Resources Required
**Initial Implementation:**
- **Senior Developer Time:** [X hours at $Y rate]
- **Testing & Validation:** [Hours for QA]
- **Integration Work:** [Hours for system integration]
- **Total Development Cost:** [Sum]

**Deployment Resources:**
- **Infrastructure Setup:** [Time and cost]
- **Training Requirements:** [Team training needs]
- **Change Management:** [Organizational change effort]

### Timeline Analysis
**Phase 1 (Weeks 1-2):** [Initial implementation milestones]
**Phase 2 (Weeks 3-4):** [Testing and refinement]
**Phase 3 (Weeks 5-6):** [Production deployment]
**Full ROI Achievement:** [Timeline to break-even]

## Risk Assessment & Mitigation

### Technical Risks
**Risk 1:** [Specific technical risk]
- **Probability:** [Low/Medium/High]
- **Impact:** [Business impact if occurs]
- **Mitigation:** [Prevention/response strategy]

### Business Risks
**Risk 1:** [Business risk such as adoption challenges]
- **Probability:** [Assessment]
- **Impact:** [Business consequences]
- **Mitigation:** [Management approach]

## Decision Framework

### Choose OpenDXA [FEATURE_NAME] When:
- [Specific organizational criteria 1]
- [Specific organizational criteria 2]
- [Use case requirements that fit perfectly]

### Consider Alternatives When:
- [Honest assessment of when other solutions might be better]
- [Specific constraints that might make alternatives preferable]

## Success Metrics & KPIs
**Immediate Metrics (Month 1):**
- [Specific measurable outcomes]

**Short-term Success (Months 2-6):**
- [Adoption and efficiency metrics]

**Long-term Value (6+ Months):**
- [Strategic business outcomes]

## Next Steps for Evaluation
1. **Technical Proof of Concept:** [Link to 30-minute demo guide]
2. **Business Case Development:** [Template for internal proposal]
3. **Pilot Program Design:** [Recommended pilot scope and metrics]
```

3. **Contributors Documentation** (`docs/for-contributors/extending/[feature-name].md`):

```markdown
# [FEATURE_NAME] - Technical Implementation & Extension Guide

## Architecture Overview

### System Integration
[FEATURE_NAME] integrates with OpenDXA through the following architectural layers:
- **Language Layer:** [How it integrates with Dana syntax]
- **Agent Runtime:** [Integration with agent execution model]
- **Core Services:** [Dependencies on OpenDXA core components]

```
┌─────────────────┐
│  Dana Language  │ ← [How feature appears in Dana code]
├─────────────────┤
│ [FEATURE_NAME]  │ ← [Feature implementation layer]
├─────────────────┤  
│  Agent Runtime  │ ← [Runtime integration points]
├─────────────────┤
│   Core System   │ ← [Core dependencies]
└─────────────────┘
```

## Code Organization

### Primary Implementation
**Main Module:** `[MODULE_PATH]/[main_file].py`
```python
# Key classes and their responsibilities
class [FeatureName]:
    """[Purpose and responsibilities]"""
    
    def __init__(self, config: [ConfigType]):
        """[Initialization details]"""
        
    def [key_method](self, input: [InputType]) -> [OutputType]:
        """[Method purpose and behavior]"""
```

**Configuration:** `[MODULE_PATH]/config.py`
- Default settings and parameter definitions
- Validation logic for configuration options
- Environment-specific overrides

**Integration Points:** `[MODULE_PATH]/integration.py`
- Dana language binding implementation
- Agent runtime registration
- Event system connections

### Dependencies
**Required OpenDXA Components:**
- `opendxa.agent.capability` - [Why needed]
- `opendxa.dana.runtime` - [Integration purpose]
- `opendxa.common.utils` - [Shared functionality used]

**External Dependencies:**
- `[external_lib]` - [Purpose and version requirements]
- `[another_lib]` - [Usage justification]

## Key Implementation Details

### Core Algorithm
```python
def [core_algorithm](input_data: InputType) -> OutputType:
    """
    [Detailed explanation of algorithm approach]
    
    Args:
        input_data: [Parameter description]
        
    Returns:
        [Return value description]
        
    Raises:
        [Exception types and conditions]
    """
    # [Step-by-step implementation with comments]
```

### State Management
- **Internal State:** [How feature manages its own state]
- **Agent Integration:** [How it integrates with agent state]
- **Persistence:** [Any persistent storage requirements]

### Error Handling Strategy
```python
# Error handling patterns used in this feature
try:
    result = [operation]
except [SpecificException] as e:
    # [How this error type is handled]
    
except [AnotherException] as e:
    # [Different handling approach]
```

## Extension Points

### Customizing Core Behavior
**Plugin Interface:**
```python
class [FeatureName]Plugin(ABC):
    """Interface for extending [FEATURE_NAME] behavior"""
    
    @abstractmethod
    def custom_processing(self, data: DataType) -> ProcessedDataType:
        """Override point for custom processing logic"""
        pass
```

**Implementation Example:**
```python
class Custom[FeatureName]Plugin([FeatureName]Plugin):
    def custom_processing(self, data: DataType) -> ProcessedDataType:
        # [Custom implementation example]
        return processed_data
        
# Registration
[feature_instance].register_plugin(Custom[FeatureName]Plugin())
```

### Configuration Extensions
```python
# How to extend configuration options
custom_config = {
    **default_config,
    "custom_option": "custom_value",
    "advanced_settings": {
        "setting1": "value1"
    }
}
```

### Dana Language Extensions
```dana
# How to extend Dana syntax for this feature (if applicable)
# [Examples of custom Dana patterns possible]
```

## Testing Framework

### Test Organization
**Unit Tests:** `tests/[feature_name]/test_[module].py`
```python
# Example test structure
class Test[FeatureName]:
    def test_[basic_functionality](self):
        """Test basic feature operation"""
        # [Test implementation]
        
    def test_[edge_case](self):
        """Test edge case handling"""
        # [Edge case test]
        
    def test_[error_conditions](self):
        """Test error handling"""
        # [Error condition tests]
```

**Integration Tests:** `tests/integration/test_[feature_name]_integration.py`
- Tests with Dana language integration
- Agent runtime integration tests  
- End-to-end workflow tests

### Running Tests
```bash
# Run feature-specific tests
pytest tests/[feature_name]/ -v

# Run integration tests
pytest tests/integration/test_[feature_name]_integration.py -v

# Run with coverage
pytest tests/[feature_name]/ --cov=[MODULE_PATH] --cov-report=html
```

### Adding New Tests
**Test Pattern to Follow:**
```python
def test_[specific_behavior]():
    """Test [specific aspect] of [FEATURE_NAME]"""
    # Arrange
    [setup_code]
    
    # Act  
    result = [feature_operation]
    
    # Assert
    assert [expected_condition]
    assert [another_expectation]
```

## Performance Characteristics

### Benchmarking
**Typical Performance:**
- **Processing Time:** [X ms/operation for typical input size]
- **Memory Usage:** [Y MB baseline + Z MB per item]
- **Throughput:** [Operations per second under normal load]

**Performance Testing:**
```python
# Benchmark test example
def benchmark_[feature_name]():
    input_data = [create_test_data]
    
    start_time = time.perf_counter()
    result = [feature_operation](input_data)
    end_time = time.perf_counter()
    
    assert end_time - start_time < [acceptable_threshold]
```

### Optimization Opportunities
- **Bottlenecks:** [Known performance bottlenecks]
- **Scaling Limits:** [Where performance degrades]
- **Optimization Strategies:** [Approaches for improvement]

## Development Workflow

### Making Changes
1. **Setup Development Environment:**
   ```bash
   # Development setup commands
   ```

2. **Code Modification Pattern:**
   ```bash
   # Edit implementation
   # Add/update tests
   # Run test suite
   pytest tests/[feature_name]/ -v
   # Update documentation
   ```

3. **Integration Testing:**
   ```bash
   # Test Dana integration
   bin/dana examples/[feature_name]_example.na
   # Test agent integration
   # Run full test suite
   ```

### Contributing Guidelines
- **Code Style:** [Specific style requirements]
- **Documentation Requirements:** [What docs need updating]
- **Review Process:** [How changes are reviewed]

## Future Enhancement Areas
- **Planned Improvements:** [Known enhancement opportunities]
- **Research Directions:** [Experimental areas for development]
- **Community Requests:** [Features requested by users]
```

4. **Researchers Documentation** (`docs/for-researchers/research/[feature-name].md`):

```markdown
# [FEATURE_NAME] - Theoretical Foundations & Research Context

## Research Domain & Academic Positioning

### Problem Domain
**Academic Field:** [Primary research domain this addresses]
**Subdisciplines:** [Specific areas within the field]
**Research Questions Addressed:**
- [Fundamental question 1]
- [Fundamental question 2]
- [Practical application question]

### Theoretical Motivation
**Core Hypothesis:** [Fundamental assumption or hypothesis being tested]
**Research Gap:** [What gap in knowledge this addresses]
**Novel Contribution:** [What new knowledge or capability this provides]

## Foundational Theories & Prior Work

### Theoretical Foundations
**Primary Theoretical Framework:** [Main academic theory this builds on]
- **Key Principles:** [Core principles from the theory]
- **Application to [FEATURE_NAME]:** [How theory applies to our implementation]
- **Extensions Made:** [How we extend or modify the theory]

**Supporting Theories:**
- **[Theory 1]:** [How it supports our approach]
- **[Theory 2]:** [Additional theoretical grounding]

### Related Academic Work
**Seminal Papers:**
1. **[Author et al. (Year)]** - "[Paper Title]"
   - **Contribution:** [What this paper established]
   - **Relevance:** [How it relates to our work]
   - **Differences:** [How our approach differs or extends]

2. **[Author et al. (Year)]** - "[Another Key Paper]"
   - **Contribution:** [Key findings or methods]
   - **Integration:** [How we build on this work]

**Recent Developments:**
- **[Recent Paper 1]:** [Current state of research]
- **[Recent Paper 2]:** [Alternative approaches being explored]

### Comparative Analysis
**Existing Approaches:**
| Approach | Theoretical Basis | Strengths | Limitations | Our Innovation |
|----------|------------------|-----------|-------------|----------------|
| [Method 1] | [Theory base] | [Advantages] | [Drawbacks] | [How we improve] |
| [Method 2] | [Theory base] | [Strengths] | [Weaknesses] | [Our advancement] |

## Design Rationale & Theoretical Justification

### Core Design Decisions
**Decision 1: [Specific Design Choice]**
- **Theoretical Justification:** [Why this choice is theoretically sound]
- **Empirical Support:** [Evidence supporting this decision]
- **Trade-offs Considered:** [Alternative approaches evaluated]
- **Expected Benefits:** [Theoretical advantages]

**Decision 2: [Another Design Choice]**
- **Academic Precedent:** [Similar choices in academic literature]
- **Novel Aspects:** [What makes our approach unique]
- **Risk Assessment:** [Theoretical risks of this choice]

### Neurosymbolic Integration Theory
**Symbolic Component Justification:**
- **Symbolic Reasoning Theory:** [How symbolic logic applies]
- **Representation Benefits:** [Advantages of symbolic representation]
- **Computational Tractability:** [Why symbolic approach is feasible]

**Neural Component Rationale:**
- **Learning Theory:** [How neural learning enhances capability]
- **Pattern Recognition:** [Benefits of neural pattern matching]
- **Adaptation Mechanisms:** [How neural components enable adaptation]

**Hybrid Architecture Benefits:**
- **Complementary Strengths:** [How symbolic + neural work together]
- **Theoretical Synergies:** [Emergent capabilities from combination]
- **Cognitive Science Support:** [How this mirrors human cognition]

## Experimental Validation & Results

### Theoretical Predictions
**Hypothesis 1:** [Specific testable prediction]
- **Test Method:** [How to validate this hypothesis]
- **Expected Outcome:** [Predicted results]
- **Significance:** [What confirmation would mean]

**Hypothesis 2:** [Another testable prediction]
- **Measurement Approach:** [How to measure this]
- **Success Criteria:** [What constitutes validation]

### Empirical Results (if available)
**Experiment 1: [Experiment Name]**
- **Methodology:** [Experimental design]
- **Results:** [Findings]
- **Theoretical Implications:** [What results mean for theory]
- **Limitations:** [Scope and constraints of findings]

### Comparative Performance
**Benchmark Studies:**
- **Comparison Method:** [How we compare to alternatives]
- **Metrics Used:** [Evaluation criteria]
- **Results Summary:** [Performance outcomes]
- **Statistical Significance:** [Confidence in results]

## Research Applications & Use Cases

### Academic Applications
**Research Use Case 1: [Specific Research Application]**
- **Research Question:** [What question this enables investigation of]
- **Methodology:** [How researchers would use this feature]
- **Expected Insights:** [Knowledge this could generate]

**Research Use Case 2: [Another Academic Application]**
- **Experimental Design:** [Research design this enables]
- **Data Collection:** [What data this can help gather]
- **Analysis Capabilities:** [Analytical possibilities]

### Cross-Disciplinary Opportunities
**Field 1: [Related Academic Field]**
- **Potential Collaboration:** [How this could be used in other fields]
- **Novel Applications:** [Unexpected use cases in other domains]

**Field 2: [Another Academic Domain]**
- **Theoretical Connections:** [Theoretical links to other fields]
- **Experimental Possibilities:** [Research this could enable]

## Open Research Questions & Future Directions

### Immediate Research Opportunities
**Question 1: [Specific Research Question]**
- **Approach:** [How this could be investigated]
- **Required Resources:** [What would be needed for this research]
- **Expected Timeline:** [How long investigation might take]
- **Potential Impact:** [Significance if answered]

**Question 2: [Another Research Direction]**
- **Theoretical Importance:** [Why this question matters]
- **Methodological Challenges:** [Difficulties in investigation]
- **Collaboration Opportunities:** [Who might partner on this]

### Long-term Research Vision
**5-Year Research Horizon:**
- [Major research directions enabled by this work]
- [Theoretical developments this could lead to]
- [Practical applications that might emerge]

**Potential Breakthroughs:**
- [Fundamental advances this might enable]
- [New research areas this could open]
- [Interdisciplinary connections possible]

## Collaboration Opportunities

### Academic Partnerships
**Research Groups:** [Specific academic groups doing related work]
**Conferences:** [Relevant academic conferences for this work]
**Journals:** [Academic journals appropriate for publication]

### Open Research Questions for Community
1. **[Question 1]:** [Specific question community could investigate]
2. **[Question 2]:** [Another question for broader research]
3. **[Question 3]:** [Community research opportunity]

### Data & Resources Available
**Research Datasets:** [Any datasets this feature generates or requires]
**Benchmarks:** [Standardized tests or comparisons available]
**Code Availability:** [Research code sharing policies]

## Citation & Attribution

### How to Cite This Work
```
[Standard academic citation format for this feature/paper]
```

### Related OpenDXA Publications
- [List of academic papers about OpenDXA that relate to this feature]
- [Conference presentations or academic talks]

### Acknowledging Contributions
[How academic users should acknowledge use of this feature in their work]
```

5. **Update Cross-References:**
```bash
# Add feature to .ai-only references
echo "## [FEATURE_NAME]" >> docs/.ai-only/opendxa.md
echo "**Purpose:** [Brief description]" >> docs/.ai-only/opendxa.md
echo "**Documentation:** [Links to all audience docs]" >> docs/.ai-only/opendxa.md

# Update audience README files
# Add feature to appropriate sections in each for-[audience]/README.md

# Create cross-links between related documentation
```

6. **Test All Examples:**
```bash
# Extract and test all Dana code from new documentation
find docs/for-engineers/recipes/[feature-name].md -exec grep -A 10 "```dana" {} \; > test_examples.na
bin/dana test_examples.na

# Verify outputs match documented expectations
```

**Completion Checklist:**
- [ ] Feature implementation thoroughly analyzed
- [ ] All 4 audience documentation trees created with appropriate depth
- [ ] Working code examples tested with `bin/dana`
- [ ] Cross-references updated across documentation
- [ ] .ai-only reference materials updated
- [ ] Examples produce documented outputs
- [ ] Integration patterns documented and tested

---

This completes the comprehensive, copy-paste ready prompt set for OpenDXA documentation maintenance. Each prompt includes all necessary context, reference materials, and step-by-step instructions for execution without additional guidance. 

```dana
result = function_name("example_input", default_param)
log(f"Result: {result}")
```

```dana
x = 10  # Auto-scoped to local (preferred)
```

```dana
global_var = "value"  # Auto-scoped to local for examples
```

```dana
result = reason("prompt", context=context)
```

```dana
input_data = "example_data"
result = function_name(input_data)
log(f"Result: {result}")
``` 