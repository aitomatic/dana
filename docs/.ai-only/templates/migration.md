# Breaking Change Migration Templates

Use these templates when documenting breaking changes and creating migration guides across all audience trees.

## Context Variables Template

Before using any template, define these context variables:
- `CHANGE_DESCRIPTION`: What changed
- `AFFECTED_COMPONENTS`: System parts affected  
- `OLD_PATTERN`: Previous behavior/syntax
- `NEW_PATTERN`: New behavior/syntax
- `TIMELINE`: When change takes effect
- `URGENCY`: How quickly users must act (High/Medium/Low)

## Engineers Migration Template (`docs/for-engineers/migration/[change-name].md`)

```markdown
# [CHANGE_NAME] Migration Guide

## ⚠️ Breaking Change Alert
**What Changed:** [CHANGE_DESCRIPTION]
**Timeline:** [When this takes effect]
**Urgency:** [High/Medium/Low - how quickly users must act]
**Impact Level:** [How many users/projects this affects]

## Before & After Examples

### Old Way (No Longer Works)
```dana
# Previous syntax/approach
[OLD_PATTERN_example]
```
**Error You'll See:** 
```
[Specific error message users will encounter]
```

### New Way (Current Syntax)
```dana
# Updated syntax/approach
[NEW_PATTERN_example]
```
**Expected Output:** 
```
[What should happen with new approach]
```

## Quick Migration Checklist
- [ ] [Task 1 - most critical]
- [ ] [Task 2 - important]
- [ ] [Task 3 - validation]
- [ ] Test everything works with new syntax

## Step-by-Step Migration

### Step 1: Identify Affected Code
**What to Look For:** [Specific patterns that need updating]

**Search Commands:**
```bash
# Find files that need updating
grep -r "[OLD_PATTERN_search_term]" your_project/
find . -name "*.na" -exec grep -l "[old_syntax]" {} \;
```

**Files to Check:**
- [File type 1]: [What to look for]
- [File type 2]: [Specific patterns]

### Step 2: Update Syntax
**Transformation Rules:**
1. Replace `[old_syntax_1]` with `[new_syntax_1]`
2. Change `[old_pattern_2]` to `[new_pattern_2]`
3. Update `[old_approach_3]` to use `[new_approach_3]`

**Automated Migration (if available):**
```bash
# Migration script or commands
sed -i 's/[old_pattern]/[new_pattern]/g' *.na
# [Additional automation commands]
```

**Manual Updates Required:**
- [Change 1]: [Why manual update needed]
- [Change 2]: [Specific manual steps]

### Step 3: Test Changes
**Validation Steps:**
```bash
# How to verify migration worked
bin/dana your_migrated_file.na
# [Additional test commands]
```

**What to Verify:**
- [Verification point 1]
- [Verification point 2]
- [Performance check if applicable]

### Step 4: Update Dependencies
**If Using External Libraries:**
- [Library 1]: Update to version [X.Y.Z] or later
- [Library 2]: [Specific update instructions]

**Configuration Changes:**
```dana
# Updated configuration syntax
[new_config_example]
```

## Common Migration Issues

### Issue 1: [Common Problem]
**Symptoms:** [How users recognize this problem]
**Cause:** [Why this happens during migration]
**Solution:** 
```dana
# Fix for this specific issue
[solution_code]
```
**Prevention:** [How to avoid this in future]

### Issue 2: [Another Common Problem]
**Symptoms:** [Recognition signs]
**Cause:** [Root cause]
**Solution:** [Step-by-step fix]

### Issue 3: [Performance/Compatibility Issue]
**Symptoms:** [How this manifests]
**Workaround:** [Temporary solution if needed]
**Permanent Fix:** [Long-term resolution]

## Advanced Migration Scenarios

### Large Codebases
**Batch Processing:**
```bash
# Scripts for processing multiple files
for file in *.na; do
    # Migration commands
done
```

**Incremental Migration:**
1. [Phase 1]: [What to migrate first]
2. [Phase 2]: [Next priority items]
3. [Phase 3]: [Final migration steps]

### Custom Extensions
**If You've Extended OpenDXA:**
- [Extension type 1]: [How to update]
- [Extension type 2]: [Migration approach]

## Rollback Plan
**If Migration Fails:**
1. [Rollback step 1]
2. [Rollback step 2]
3. [How to restore previous state]

**Backup Strategy:**
```bash
# Create backup before migration
cp -r your_project/ your_project_backup_$(date +%Y%m%d)
```

## Getting Help
**If You're Stuck:**
- [Support channel 1]: [When to use]
- [Support channel 2]: [What information to provide]
- [Documentation links]: [Additional resources]

**Common Questions:**
- **Q:** [Frequent question 1]
- **A:** [Answer with example]

- **Q:** [Frequent question 2]  
- **A:** [Answer with solution]

## Timeline and Support
**Migration Deadline:** [When old syntax stops working]
**Support Period:** [How long old syntax will be supported]
**Deprecation Warnings:** [When warnings start appearing]
```

## Evaluators Migration Template (`docs/for-evaluators/migration/[change-name].md`)

```markdown
# [CHANGE_NAME] - Business Impact Assessment

## Executive Summary
[CHANGE_DESCRIPTION] requires [migration_effort] with [business_impact]. Organizations should plan for [timeline] to complete migration with [resource_requirements].

## Business Impact Analysis

### Immediate Impact
**Development Team Impact:**
- **Time Required:** [Hours/days of developer time needed]
- **Team Size:** [Number of developers needed]
- **Skill Level:** [Required expertise for migration]

**System Impact:**
- **Downtime Required:** [Any service interruption needed]
- **Performance Impact:** [Temporary or permanent performance changes]
- **Feature Availability:** [Any features temporarily unavailable]

### Risk Assessment
**Migration Risks:**
- **Technical Risk:** [Probability and impact of technical issues]
- **Timeline Risk:** [Risk of delays]
- **Resource Risk:** [Risk of insufficient resources]

**Business Continuity:**
- **Service Disruption:** [Potential for service interruption]
- **Customer Impact:** [Effect on end users]
- **Revenue Impact:** [Potential business impact]

## Resource Requirements

### Development Resources
**Team Composition:**
- Senior Developer: [X hours] - [Specific responsibilities]
- Mid-level Developer: [Y hours] - [Tasks assigned]
- QA Engineer: [Z hours] - [Testing requirements]

**Skill Requirements:**
- [Skill 1]: [Why needed, proficiency level]
- [Skill 2]: [Application to migration]
- [Training Needs]: [If team needs upskilling]

### Infrastructure Resources
**Development Environment:**
- [Resource 1]: [What's needed]
- [Resource 2]: [Requirements]

**Testing Environment:**
- [Testing requirement 1]
- [Testing requirement 2]

### Timeline and Costs
**Migration Phases:**
- **Preparation:** [Duration] - [Activities and costs]
- **Execution:** [Duration] - [Migration activities and costs]
- **Validation:** [Duration] - [Testing and verification costs]

**Total Investment:**
- **Development Time:** [Total hours × hourly rate]
- **Infrastructure:** [Any additional infrastructure costs]
- **Training:** [If team training is needed]
- **Contingency:** [Buffer for unexpected issues]

## Communication Strategy

### Stakeholder Communication
**Executive Summary for Leadership:**
[Brief summary suitable for executives, focusing on business impact and timeline]

**Technical Team Briefing:**
[Summary for technical teams, focusing on implementation details]

**Customer Communication (if applicable):**
[How to communicate any customer-facing changes]

### Timeline Communication
**Milestone 1:** [Date] - [What stakeholders should expect]
**Milestone 2:** [Date] - [Next checkpoint]
**Completion:** [Date] - [Final deliverable]

## Risk Mitigation

### Technical Risk Mitigation
**Backup Strategy:**
- [How to preserve rollback capability]
- [Data backup requirements]
- [Configuration backup needs]

**Testing Strategy:**
- [How to minimize migration risk through testing]
- [Staging environment requirements]
- [Validation procedures]

**Monitoring Strategy:**
- [What to monitor during migration]
- [Key performance indicators to watch]
- [Alert thresholds]

### Business Risk Mitigation
**Contingency Planning:**
- [Plan A]: [Primary migration approach]
- [Plan B]: [Alternative if issues arise]
- [Rollback Plan]: [How to revert if necessary]

**Communication Plan:**
- [How to keep stakeholders informed]
- [Escalation procedures if issues arise]
- [Status reporting schedule]

## Success Metrics

### Technical Success Criteria
- [Metric 1]: [How to measure technical success]
- [Metric 2]: [Another technical indicator]
- [Performance Baseline]: [Expected performance after migration]

### Business Success Criteria
- [Business metric 1]: [How to measure business success]
- [User satisfaction]: [How to measure user impact]
- [Operational efficiency]: [Efficiency improvements expected]

## Post-Migration Benefits

### Immediate Benefits
- [Benefit 1]: [What improves immediately]
- [Benefit 2]: [Another immediate advantage]

### Long-term Benefits
- [Long-term benefit 1]: [Future advantages]
- [Long-term benefit 2]: [Strategic improvements]
- [Competitive advantage]: [How this improves market position]

## Decision Framework

### Proceed with Migration When:
- [Condition 1]: [Business justification]
- [Condition 2]: [Technical readiness]
- [Condition 3]: [Resource availability]

### Delay Migration When:
- [Condition 1]: [When to postpone]
- [Condition 2]: [Risk factors that suggest delay]

### Seek Alternative When:
- [Condition 1]: [When to consider other options]
- [Alternative approaches]: [If migration isn't suitable]
```

## Contributors Migration Template (`docs/for-contributors/migration/[change-name].md`)

```markdown
# [CHANGE_NAME] - Technical Migration Details

## Technical Overview

### Root Cause Analysis
**Why This Change Was Necessary:**
[Technical justification for the breaking change]

**System Architecture Impact:**
[How this affects overall system design]

**Backward Compatibility Analysis:**
- **What Breaks:** [Specific incompatibilities]
- **What Remains Compatible:** [What continues to work]
- **Deprecation Timeline:** [How long old features are supported]

## Code Changes Required

### Core System Changes
**Modified Components:**
- `[component1]`: [What changed and why]
- `[component2]`: [Modifications made]

**New Dependencies:**
- `[dependency1]`: [Why added, version requirements]
- `[dependency2]`: [Purpose and integration]

**Removed Dependencies:**
- `[old_dependency1]`: [Why removed, replacement]
- `[old_dependency2]`: [Migration path]

### API Changes
**Function Signature Changes:**
```python
# Old signature
def old_function(param1, param2):
    pass

# New signature  
def new_function(param1, param2, new_param=default):
    pass
```

**Class Interface Changes:**
```python
# Old interface
class OldClass:
    def old_method(self):
        pass

# New interface
class NewClass:
    def new_method(self, additional_param):
        pass
```

**Configuration Changes:**
```python
# Old configuration format
OLD_CONFIG = {
    'setting1': 'value1',
    'setting2': 'value2'
}

# New configuration format
NEW_CONFIG = {
    'settings': {
        'setting1': 'value1',
        'setting2': 'value2',
        'new_setting': 'default_value'
    }
}
```

## Extension Migration

### Custom Capabilities
**If You've Built Custom Agent Capabilities:**
```python
# Old capability pattern
class OldCustomCapability:
    def execute(self, input_data):
        # Old implementation
        pass

# New capability pattern
class NewCustomCapability:
    def execute(self, input_data, context=None):
        # Updated implementation with context
        pass
```

### Custom Functions
**Dana Function Updates:**
```python
# Old function registration
@dana_function
def custom_function(param1):
    return result

# New function registration
@dana_function(version="2.0")
def custom_function(param1, context=None):
    return result
```

### Plugin Architecture Changes
**Plugin Interface Updates:**
```python
# Old plugin interface
class OldPlugin:
    def initialize(self):
        pass

# New plugin interface
class NewPlugin:
    def initialize(self, config, context):
        pass
```

## Testing Migration

### Test Updates Required
**Unit Test Changes:**
```python
# Old test pattern
def test_old_functionality():
    result = old_function(param1, param2)
    assert result == expected

# New test pattern
def test_new_functionality():
    result = new_function(param1, param2, new_param)
    assert result == expected
```

**Integration Test Updates:**
```python
# Updated integration test patterns
def test_integration_with_new_api():
    # Test new integration patterns
    pass
```

**Mock Updates:**
```python
# Old mocking approach
@patch('module.old_function')
def test_with_old_mock(mock_func):
    pass

# New mocking approach
@patch('module.new_function')
def test_with_new_mock(mock_func):
    pass
```

## Development Workflow Updates

### Build Process Changes
```bash
# Updated build commands
python setup.py build --new-flag
# [Additional build steps]
```

### Development Environment Setup
```bash
# New development setup requirements
pip install -r requirements-dev.txt
# [Additional setup steps]
```

### Code Style Updates
**New Linting Rules:**
- [Rule 1]: [What changed in code style]
- [Rule 2]: [New requirements]

**Updated Pre-commit Hooks:**
```yaml
# Updated .pre-commit-config.yaml
repos:
  - repo: [new_repo_url]
    rev: [version]
    hooks:
      - id: [new_hook]
```

## Debugging Migration Issues

### Common Development Issues
**Issue 1: [Specific Development Problem]**
**Symptoms:** [How developers recognize this]
**Debug Steps:**
```bash
# Debugging commands
python -m pdb your_script.py
# [Additional debug steps]
```
**Solution:** [How to fix]

**Issue 2: [Another Development Issue]**
**Symptoms:** [Recognition signs]
**Investigation:** [How to investigate]
**Resolution:** [Fix approach]

### Logging Changes
**Updated Logging Configuration:**
```python
# New logging setup
import logging
logger = logging.getLogger('opendxa.new_module')
logger.setLevel(logging.DEBUG)
```

**New Log Formats:**
```python
# Updated log message patterns
logger.info(f"[NewModule] Processing {data} with context {context}")
```

## Performance Impact

### Performance Changes
**Expected Performance Impact:**
- [Operation 1]: [Performance change]
- [Operation 2]: [Speed/memory impact]

**Benchmarking:**
```bash
# How to benchmark before/after migration
python benchmark_script.py --before
# [Migration steps]
python benchmark_script.py --after
```

### Optimization Opportunities
**New Optimization Possibilities:**
- [Optimization 1]: [How to take advantage]
- [Optimization 2]: [Implementation approach]

## Documentation Updates

### Code Documentation
**Docstring Updates:**
```python
def updated_function(param1, param2, new_param=None):
    """
    Updated docstring reflecting new parameters and behavior.
    
    Args:
        param1: [Description]
        param2: [Description]  
        new_param: [New parameter description]
    
    Returns:
        [Updated return description]
    """
```

**README Updates:**
- [Section 1]: [What needs updating]
- [Section 2]: [New information to add]

### API Documentation
**Updated API References:**
- [API endpoint 1]: [Changes needed]
- [API endpoint 2]: [Documentation updates]

## Future Considerations

### Upcoming Changes
**Related Changes in Pipeline:**
- [Future change 1]: [How it relates to current migration]
- [Future change 2]: [Preparation needed]

### Extension Opportunities
**New Extension Points:**
- [Extension point 1]: [How developers can extend]
- [Extension point 2]: [New customization options]

### Research Directions
**Technical Research Enabled:**
- [Research direction 1]: [What this migration enables]
- [Research direction 2]: [New possibilities]
```

## Usage Instructions

1. **Pre-Migration Analysis**: Thoroughly understand the scope and impact of the breaking change before creating documentation

2. **Template Customization**: Replace all bracketed placeholders with change-specific content

3. **Audience Adaptation**: Ensure each template addresses the specific concerns and needs of its target audience

4. **Testing**: Validate all migration steps and code examples work as documented

5. **Cross-References**: Link between audience-specific migration guides where appropriate

6. **Timeline Coordination**: Ensure all audience documentation reflects consistent timelines and milestones 