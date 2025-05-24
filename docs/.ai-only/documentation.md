<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

# OpenDXA Documentation Maintenance Prompts

## Background Context for All Prompts

**Current Documentation Structure (Updated 2025-01-24)**:
- `docs/README.md` - Audience routing hub with clear paths for each user type
- `docs/for-engineers/` - Practical guides, recipes, and references for developers
- `docs/for-evaluators/` - Business ROI, competitive analysis, and proof of concepts
- `docs/for-contributors/` - Architecture, codebase navigation, and development guides
- `docs/for-researchers/` - Philosophy, theory, neurosymbolic research, and manifesto
- `docs/archive/` - Preserved original documentation (dana/, core-concepts/, architecture/)
- `docs/.ai-only/` - AI assistant reference materials (this directory)

**Key Reference Files**:
- `docs/archive/original-dana/language.md` - Complete Dana language specification (authoritative)
- `docs/archive/original-dana/manifesto.md` - Authoritative philosophy and vision
- `docs/for-engineers/reference/dana-syntax.md` - Current practical Dana reference
- `docs/for-researchers/manifesto/vision.md` - Updated philosophical foundations
- `docs/.ai-only/opendxa.md` - System overview and components
- `docs/.ai-only/functions.md` - Current function catalog
- `docs/.ai-only/project.md` - Directory structure guide

**Audience-Specific Update Targets**:
- **Engineers**: Focus on practical how-to guides, working code examples, troubleshooting
- **Evaluators**: Emphasize business value, ROI calculations, competitive advantages
- **Contributors**: Provide technical depth, architecture details, development workflows
- **Researchers**: Include theoretical foundations, research opportunities, academic context

## Daily Maintenance Prompts

### Prompt 1: Function Registry Scan
```
**Task**: Scan for new or modified Dana functions and update documentation

**Required Reading**:
1. Review `docs/.ai-only/functions.md` for current function catalog format
2. Check `docs/.ai-only/project.md` for module organization
3. Reference `docs/dana/language.md` for Dana syntax patterns

**Instructions**:
1. Search these directories for new .py files or modified function signatures since yesterday:
   - `opendxa/dana/`
   - `opendxa/agent/capability/`
   - `opendxa/common/`

2. For each new/modified function found:
   - Extract function signature, docstring, and any inline examples
   - Identify the function's purpose and primary use cases
   
3. Update documentation in ALL audience trees:

   **Engineers** (`docs/for-engineers/reference/functions.md`):
   ```markdown
   ## [Function Name]
   **Signature**: `function_name(param1, param2)`
   **Purpose**: [One sentence practical description]
   
   **Example**:
   ```dana
   [Working code example with expected output]
   ```
   
   **Common Use Cases**:
   - [Specific practical scenario]
   - [Another concrete use case]
   
   **Troubleshooting**:
   - If you see [error], try [solution]
   ```

   **Evaluators** (`docs/for-evaluators/roi-analysis/new-capabilities.md`):
   ```markdown
   ## [Function Name] - Business Value
   **Value Proposition**: [How this saves time/money]
   **Time Savings**: [Quantified estimate vs manual approach]
   **Competitive Advantage**: [What competitors can't do]
   **Implementation Effort**: [Low/Medium/High with timeframe]
   ```

   **Contributors** (`docs/for-contributors/extending/function-development.md`):
   ```markdown
   ## [Function Name] Implementation
   **Location**: `[file path and line number]`
   **Dependencies**: [Required imports/modules]
   **Extension Points**: [How to customize/extend]
   **Testing**: [How to test this function]
   ```

   **Researchers** (`docs/for-researchers/research/capability-evolution.md`):
   ```markdown
   ## [Function Name] - Theoretical Context
   **Design Rationale**: [Why this function exists]
   **Theoretical Foundations**: [Academic/research basis]
   **Related Work**: [Academic papers or research connections]
   ```

4. Update `.ai-only/functions.md` with structured reference:
   ```markdown
   ### [Function Name]
   **Module**: `[module.path]`
   **Signature**: `[full signature]`
   **Purpose**: [Concise description]
   **Audience Usage**:
   - Engineers: [Link to practical guide]
   - Evaluators: [Link to business analysis]
   - Contributors: [Link to implementation details]
   - Researchers: [Link to theoretical context]
   ```

5. Test all code examples by running them with `bin/dana`

**Output**: List of files modified and summary of documentation added
```

### Prompt 2: Example Validation & Syntax Updates
```
**Task**: Validate all Dana code examples work with current syntax

**Required Reading**:
1. Review `docs/dana/syntax.md` for current Dana syntax rules
2. Check `docs/dana/repl.md` for REPL usage patterns
3. Reference recent changes in `examples/dana/na/` for syntax evolution

**Instructions**:
1. Extract all Dana code blocks from these documentation locations:
   ```bash
   # Search for Dana code blocks (```dana or ```)
   grep -r "```dana" docs/for-engineers/
   grep -r "```dana" docs/for-evaluators/
   grep -r "```dana" docs/for-contributors/
   grep -r "```dana" docs/for-researchers/
   grep -r "```dana" docs/.ai-only/
   ```

2. For each code example found:
   - Save to temporary .na file
   - Execute with current `bin/dana` command
   - Compare output with any documented expected results
   
3. Fix broken examples while preserving pedagogical purpose:
   - Update to current Dana syntax (reference `docs/dana/syntax.md`)
   - Maintain the same learning objective
   - Add expected output where missing
   - Test fixed examples again

4. Update syntax patterns to match current best practices:
   - Variable scope syntax (`private:`, `public:`, etc.)
   - Function calls and parameters
   - F-string formatting
   - REPL command usage

5. Check examples against recent patterns in `examples/dana/na/`:
   - `basic_assignments.na` - Variable assignment patterns
   - `reason_demo.na` - AI reasoning integration
   - `multiple_scopes.na` - Scope usage patterns

**Common Syntax Updates Needed**:
- Old: `reason("prompt")` → New: Check current reason() syntax in `docs/dana/language.md`
- Old: Variable syntax → New: Current scope syntax from `docs/dana/syntax.md`
- Old: REPL commands → New: Current commands from `docs/dana/repl.md`

**Output**: List of examples fixed with details of syntax updates made
```

## Weekly Analysis Prompts

### Prompt 3: Content Gap Analysis
```
**Task**: Identify missing documentation for recent OpenDXA features

**Required Reading**:
1. Review `docs/.ai-only/project.md` for current project structure
2. Check `docs/.ai-only/opendxa.md` for system component overview
3. Scan recent commits in project history for new features

**Instructions**:
1. Analyze recent codebase changes (past 7 days):
   ```bash
   # Check for new modules/capabilities
   git log --since="7 days ago" --name-only --pretty=format: | grep -E '\.(py|md)$' | sort -u
   ```

2. Compare against existing documentation coverage:
   - New modules in `opendxa/` - do they have corresponding docs?
   - New capabilities in `opendxa/agent/capability/` - are they explained?
   - New examples in `examples/dana/na/` - are they documented?

3. For each gap, assess impact on ALL audiences:

   **Engineers Gap Assessment**:
   - Missing: Practical how-to guides for new features
   - Need: Step-by-step recipes for common use cases
   - Missing: Troubleshooting for new error patterns

   **Evaluators Gap Assessment**:
   - Missing: Business value analysis of new capabilities
   - Need: ROI calculations for new features
   - Missing: Competitive positioning updates

   **Contributors Gap Assessment**:
   - Missing: Architecture documentation for new modules
   - Need: Extension points and customization guides
   - Missing: Development workflow updates

   **Researchers Gap Assessment**:
   - Missing: Theoretical context for new capabilities
   - Need: Design rationale documentation
   - Missing: Academic connections and research implications

4. Create prioritized task list:
   ```markdown
   ## High Priority Gaps (Affects user success)
   1. [Feature Name] - Missing engineer recipes
      - Impact: Users can't implement basic use cases
      - Files needed: `for-engineers/recipes/[feature].md`
   
   ## Medium Priority Gaps (Affects adoption)
   2. [Feature Name] - Missing evaluator analysis
      - Impact: Decision makers lack business justification
      - Files needed: `for-evaluators/roi-analysis/[feature].md`
   
   ## Low Priority Gaps (Nice to have)
   3. [Feature Name] - Missing theoretical context
      - Impact: Researchers lack academic grounding
      - Files needed: `for-researchers/research/[feature].md`
   ```

5. Create GitHub issues for significant gaps using this template:
   ```markdown
   Title: [DOCS] Missing documentation for [Feature Name]
   
   **Gap Description**: [What's missing]
   **Affected Audiences**: [Engineers/Evaluators/Contributors/Researchers]
   **User Impact**: [How this affects user success]
   **Priority**: [High/Medium/Low based on user impact]
   **Files to Create**: [Specific file paths needed]
   ```

**Output**: Prioritized list of documentation gaps with impact assessment and GitHub issues created
```

### Prompt 4: Competitive Positioning Update
```
**Task**: Update competitive analysis documentation for accuracy

**Required Reading**:
1. Review current comparisons in `docs/for-evaluators/comparison/`
2. Check `docs/dana/manifesto.md` for OpenDXA positioning principles
3. Reference `docs/.ai-only/opendxa.md` for current capabilities summary

**Instructions**:
1. Review existing competitive documentation:
   - `docs/for-evaluators/comparison/vs-langchain.md`
   - `docs/for-evaluators/comparison/vs-autogen.md`
   - `docs/for-evaluators/comparison/competitive-matrix.md`

2. Research recent competitor developments:
   - LangChain: Check latest releases and new capabilities
   - AutoGen: Review recent feature announcements
   - New competitors: Search for emerging neurosymbolic/agent frameworks

3. Update comparison matrices using this format:
   ```markdown
   ## Feature Comparison: OpenDXA vs [Competitor]
   
   | Capability | OpenDXA | [Competitor] | Advantage |
   |------------|---------|--------------|-----------|
   | [Feature 1] | ✅ Native support | ❌ Requires plugins | Simpler setup |
   | [Feature 2] | ✅ Built-in | ✅ Available | Comparable |
   | [Feature 3] | ❌ Planned | ✅ Available | Competitor advantage |
   
   **OpenDXA Unique Value**:
   - [Specific advantage not available elsewhere]
   - [Another differentiator]
   
   **When to Choose OpenDXA**:
   - [Specific use case scenario]
   - [Another decision criteria]
   
   **When [Competitor] Might Be Better**:
   - [Honest assessment of competitor strengths]
   ```

4. Update business value propositions:
   - Quantify advantages where possible ("50% faster setup")
   - Include real customer/user feedback if available
   - Reference specific Dana language benefits
   - Highlight neurosymbolic approach advantages

5. Ensure consistency across all evaluator documentation:
   - Same competitive claims in all comparison files
   - Updated feature lists reflect current OpenDXA capabilities
   - Business value statements align with `docs/dana/manifesto.md`

**Output**: List of comparison updates made with specific changes and rationale
```

## Event-Driven Maintenance Prompts

### Prompt 5: New Feature Documentation
```
**Task**: Create comprehensive documentation for a new OpenDXA feature

**Context Variables** (Fill these in when using prompt):
- `FEATURE_NAME`: [Name of the new feature]
- `MODULE_PATH`: [Where feature is implemented]
- `FEATURE_TYPE`: [Agent capability/Dana language feature/Core system/etc.]

**Required Reading Before Starting**:
1. Analyze the feature implementation in `[MODULE_PATH]`
2. Review `docs/.ai-only/opendxa.md` to understand how feature fits in system
3. Check `docs/dana/language.md` if it's a Dana language feature
4. Reference similar features in existing documentation for formatting patterns

**Instructions**:
1. Feature Analysis Phase:
   ```bash
   # Understand the feature implementation
   grep -r "[FEATURE_NAME]" opendxa/
   find . -name "*.py" -exec grep -l "[FEATURE_NAME]" {} \;
   ```
   - What problem does this feature solve?
   - How does it integrate with existing system?
   - What are the key use cases?
   - What configuration options exist?
   - Are there dependencies or prerequisites?

2. Create audience-specific documentation:

   **Engineers Documentation** (`docs/for-engineers/recipes/[feature-name].md`):
   ```markdown
   # [Feature Name] - Practical Guide
   
   ## What You'll Build
   [One sentence describing the end result]
   
   ## Prerequisites
   - [Required setup/knowledge]
   - [Dependencies to install]
   
   ## Quick Start (5 minutes)
   ```dana
   [Minimal working example with expected output]
   ```
   
   ## Step-by-Step Tutorial
   ### Step 1: [Action]
   ```dana
   [Code]
   ```
   **Expected Output**: [What user should see]
   
   ### Step 2: [Next Action]
   [Continue with complete working example]
   
   ## Common Use Cases
   ### Use Case 1: [Scenario]
   [Complete working code for this scenario]
   
   ### Use Case 2: [Another Scenario]
   [Complete working code]
   
   ## Troubleshooting
   **Problem**: [Common error/issue]
   **Solution**: [How to fix it]
   **Why This Happens**: [Brief explanation]
   
   ## Integration with Existing Code
   [How to add this feature to existing projects]
   ```

   **Evaluators Documentation** (`docs/for-evaluators/roi-analysis/[feature-name].md`):
   ```markdown
   # [Feature Name] - Business Analysis
   
   ## Executive Summary
   [Feature Name] enables [business capability] with [quantified benefit].
   
   ## Business Value Proposition
   **Problem Solved**: [What business pain this addresses]
   **Solution Provided**: [How this feature solves it]
   **Quantified Benefits**:
   - Time Savings: [X hours/week saved vs manual approach]
   - Cost Reduction: [$ amount or percentage]
   - Quality Improvement: [Measurable improvement]
   
   ## Competitive Analysis
   | Capability | OpenDXA | LangChain | AutoGen | Advantage |
   |------------|---------|-----------|---------|-----------|
   | [Feature capability] | ✅ Native | ❌ Plugin required | ❌ Not available | First-class support |
   
   ## Implementation Effort
   **Development Time**: [Estimated hours for typical implementation]
   **Skill Requirements**: [What expertise needed]
   **Integration Complexity**: [Low/Medium/High with explanation]
   
   ## ROI Analysis
   **Investment**: [Time/resources to implement]
   **Returns**: [Benefits achieved]
   **Payback Period**: [Time to break even]
   
   ## Risk Assessment
   **Technical Risks**: [What could go wrong technically]
   **Business Risks**: [Business impact of issues]
   **Mitigation Strategies**: [How to reduce risks]
   ```

   **Contributors Documentation** (`docs/for-contributors/extending/[feature-name].md`):
   ```markdown
   # [Feature Name] - Implementation Guide
   
   ## Architecture Overview
   [High-level design with diagrams if needed]
   
   ## Code Organization
   **Main Implementation**: `[file path and key classes/functions]`
   **Dependencies**: [Required modules and why]
   **Configuration**: [How feature is configured]
   
   ## Key Components
   ### [Component 1]
   **Purpose**: [What this component does]
   **Location**: `[file path:line numbers]`
   **Key Methods**: [Important methods and their purposes]
   
   ## Extension Points
   ### Customizing [Aspect]
   [How developers can customize this feature]
   ```python
   # Example extension code
   ```
   
   ### Adding [Capability]
   [How to extend the feature's capabilities]
   
   ## Testing
   **Test Location**: `[test file paths]`
   **How to Run Tests**: [Commands to execute]
   **Adding New Tests**: [Patterns to follow]
   
   ## Integration Patterns
   [How this feature integrates with other system components]
   
   ## Performance Considerations
   [Memory usage, speed, scalability concerns]
   ```

   **Researchers Documentation** (`docs/for-researchers/research/[feature-name].md`):
   ```markdown
   # [Feature Name] - Theoretical Foundations
   
   ## Research Context
   **Problem Domain**: [Academic field this addresses]
   **Theoretical Basis**: [Academic theories this builds on]
   **Novel Contributions**: [What's new/different about our approach]
   
   ## Design Rationale
   **Why This Approach**: [Theoretical justification for design choices]
   **Alternative Approaches Considered**: [What else was considered and why rejected]
   **Trade-offs Made**: [What was sacrificed for what benefits]
   
   ## Academic Connections
   **Related Papers**: [Academic work that influences this]
   **Research Applications**: [How researchers might use this]
   **Future Research Directions**: [What research questions this opens]
   
   ## Theoretical Implications
   [How this contributes to neurosymbolic AI research]
   ```

3. Update cross-references and indexes:
   - Add feature to `.ai-only/functions.md` or `.ai-only/opendxa.md`
   - Update README files in each audience tree
   - Add cross-links from related existing documentation

4. Create working examples and test all code:
   ```bash
   # Test all Dana code examples
   bin/dana [example-file.na]
   ```

**Output**: Complete feature documentation across all audience trees with tested examples
```

### Prompt 6: Breaking Change Migration Documentation
```
**Task**: Create migration guides for breaking changes

**Context Variables** (Fill these in when using prompt):
- `CHANGE_DESCRIPTION`: [What changed]
- `AFFECTED_COMPONENTS`: [What parts of system are affected]
- `OLD_PATTERN`: [How things worked before]
- `NEW_PATTERN`: [How things work now]
- `TIMELINE`: [When change takes effect]

**Required Reading Before Starting**:
1. Understand the change by reviewing relevant code diffs
2. Check `docs/dana/` for any syntax/language changes
3. Review existing examples in `examples/dana/na/` to see what breaks
4. Reference `docs/.ai-only/project.md` to understand affected areas

**Instructions**:
1. Impact Analysis Phase:
   ```bash
   # Find all documentation that references old patterns
   grep -r "[OLD_PATTERN]" docs/
   grep -r "[OLD_PATTERN]" examples/
   ```
   - List all affected documentation files
   - Identify broken examples
   - Assess scope of user impact

2. Create migration guides for each audience:

   **Engineers Migration Guide** (`docs/for-engineers/migration/[change-name].md`):
   ```markdown
   # [Change Name] Migration Guide
   
   ## ⚠️ Breaking Change Alert
   **What Changed**: [CHANGE_DESCRIPTION]
   **Timeline**: [When this takes effect]
   **Urgency**: [High/Medium/Low - how quickly users must act]
   
   ## Before & After Examples
   ### Old Way (No Longer Works)
   ```dana
   [OLD_PATTERN example]
   ```
   **Error You'll See**: [Specific error message]
   
   ### New Way (Current Syntax)
   ```dana
   [NEW_PATTERN example]
   ```
   **Expected Output**: [What should happen]
   
   ## Step-by-Step Migration
   ### Step 1: Identify Affected Code
   [How to find code that needs updating]
   ```bash
   # Search command to find affected files
   ```
   
   ### Step 2: Update Syntax
   [Specific transformation rules]
   
   ### Step 3: Test Changes
   [How to verify migration worked]
   
   ## Common Migration Issues
   **Issue**: [Common problem users encounter]
   **Cause**: [Why this happens]
   **Solution**: [How to fix it]
   
   ## Migration Checklist
   - [ ] [Task 1]
   - [ ] [Task 2]
   - [ ] [Test everything works]
   
   ## Getting Help
   [Where to get help if stuck]
   ```

   **Evaluators Migration Guide** (`docs/for-evaluators/migration/[change-name].md`):
   ```markdown
   # [Change Name] - Business Impact Assessment
   
   ## Executive Summary
   [CHANGE_DESCRIPTION] requires [migration effort] with [business impact].
   
   ## Business Impact
   **Development Time Impact**: [Hours/days of developer time needed]
   **System Downtime**: [Any service interruption required]
   **Risk Level**: [High/Medium/Low with explanation]
   
   ## Migration Timeline
   **Preparation Phase**: [What to do before change]
   **Migration Window**: [When to perform migration]
   **Validation Phase**: [How to verify success]
   
   ## Resource Requirements
   **Developer Time**: [Estimated hours by skill level]
   **Testing Time**: [Time needed for validation]
   **Support Time**: [Potential support overhead]
   
   ## Communication Templates
   ### For Development Team
   [Email template explaining technical changes]
   
   ### For Stakeholders
   [Executive summary of business impact]
   
   ## Risk Mitigation
   **Backup Strategy**: [How to preserve rollback capability]
   **Testing Strategy**: [How to minimize migration risk]
   **Monitoring**: [What to watch for during migration]
   ```

   **Contributors Migration Guide** (`docs/for-contributors/migration/[change-name].md`):
   ```markdown
   # [Change Name] - Technical Migration Details
   
   ## Technical Overview
   **Root Cause**: [Why this change was necessary]
   **System Impact**: [What system components are affected]
   **Backward Compatibility**: [What breaks and what remains compatible]
   
   ## Code Changes Required
   ### Core System Changes
   [Changes needed in core OpenDXA components]
   
   ### Extension/Plugin Changes
   [How custom extensions need to be updated]
   
   ### Testing Updates
   [How to update tests for new patterns]
   
   ## Implementation Details
   **File Locations**: [Specific files that changed]
   **API Changes**: [Function signatures that changed]
   **Configuration Changes**: [Config format updates]
   
   ## Extension Migration
   ### Custom Capabilities
   [How to update custom agent capabilities]
   
   ### Custom Functions
   [How to update custom Dana functions]
   
   ## Testing Migration Success
   ```bash
   # Commands to verify migration worked
   ```
   
   ## Development Workflow Updates
   [Changes to development process]
   ```

3. Update affected documentation:
   - Add deprecation warnings to old documentation
   - Update all code examples to new patterns
   - Create redirects from old content to migration guides

4. Enhance AI assistant guidance:
   ```markdown
   # Update docs/.ai-only/[relevant-file].md
   
   ## Breaking Change Alert: [Change Name]
   **Status**: Active as of [date]
   **Impact**: [What users will experience]
   **Migration**: See [link to migration guides]
   **AI Assistant Guidance**: When users mention [old pattern], direct them to migration guide
   ```

**Output**: Complete migration documentation with audience-specific guides and updated references
```

### Prompt 7: One-Time Documentation Structure Migration
```
**Task**: Execute the migration from current docs structure to audience-optimized structure

**WARNING**: This is a major restructuring. Create backup before executing.

**Required Reading Before Starting**:
1. Complete review of current `docs/` structure
2. Full understanding of target audience-specific organization
3. Review of all existing content quality and value

**Pre-Migration Backup**:
```bash
# Create complete backup
cp -r docs/ docs-backup-$(date +%Y%m%d)
git add . && git commit -m "Backup before documentation restructure"
```

**Migration Instructions**:

### Phase 1: Create Target Directory Structure
```bash
# Create new audience-specific directories
mkdir -p docs/for-engineers/{setup,recipes,reference,troubleshooting}
mkdir -p docs/for-evaluators/{comparison,roi-analysis,proof-of-concept,adoption-guide}
mkdir -p docs/for-contributors/{codebase,architecture,extending,development}
mkdir -p docs/for-researchers/{manifesto,neurosymbolic,research,future-work}
mkdir -p docs/internal/{requirements,product-specs,planning}
mkdir -p docs/archive/{original-dana,original-core-concepts,original-architecture}
```

### Phase 2: Content Analysis and Redistribution

**Analyze `docs/dana/` (16 files) - Excellent source material**:
```bash
# List all dana files to process
ls -la docs/dana/

# For each file, extract audience-specific content:
# language.md → Multiple audiences (philosophy, syntax, examples)
# syntax.md → Engineers (practical reference)
# repl.md → Engineers (tool usage)
# manifesto.md → Researchers (philosophy)
# [Continue for all 16 files]
```

**Content Mapping Strategy**:
```markdown
## Dana Directory Content Redistribution

### docs/dana/language.md → Multiple Targets:
- Philosophical sections → for-researchers/manifesto/vision.md
- Syntax sections → for-engineers/reference/dana-syntax.md
- Examples → for-engineers/recipes/basic-patterns.md
- Design rationale → for-contributors/architecture/language-design.md

### docs/dana/syntax.md → Engineers Focus:
- Complete file → for-engineers/reference/dana-syntax.md
- Quick reference → .ai-only/cheat-sheet.md

### docs/dana/repl.md → Engineers + Contributors:
- User guide → for-engineers/setup/repl-guide.md
- Implementation details → for-contributors/development/repl-internals.md

### docs/dana/manifesto.md → Researchers:
- Complete file → for-researchers/manifesto/vision.md
- Executive summary → for-evaluators/comparison/philosophy-overview.md
```

**Redistribute `docs/core-concepts/`**:
```bash
# Move architecture content based on audience needs
cp docs/core-concepts/architecture.md docs/for-contributors/architecture/system-design.md
# Extract high-level overview for evaluators
# Create practical guide for engineers
```

**Handle Internal/Archive Content**:
```bash
# Move internal planning docs
mv docs/requirements/ docs/internal/requirements/
mv docs/key-differentiators/ docs/internal/marketing/

# Archive original structure for reference
mv docs/dana/ docs/archive/original-dana/
mv docs/core-concepts/ docs/archive/original-core-concepts/
mv docs/architecture/ docs/archive/original-architecture/
```

### Phase 3: Create Audience Entry Points

**Engineers Entry Point** (`docs/for-engineers/README.md`):
```markdown
# OpenDXA for Engineers

## 🚀 Quick Start
Get from zero to working agent in 15 minutes.

- [5-Minute Setup](setup/installation.md) - Install and verify OpenDXA
- [Build Your First Agent](recipes/first-agent.md) - Working code in 10 minutes
- [Dana Language Basics](reference/dana-syntax.md) - Essential syntax reference

## 📋 Common Tasks
Jump directly to solutions for typical engineering problems.

- 🤖 [Build a Chatbot](recipes/chatbot/) - Customer service, FAQ, conversational AI
- 📄 [Process Documents](recipes/document-processor/) - Extract, analyze, transform content
- 🔄 [Create Workflows](recipes/workflow-agent/) - Multi-step automated processes
- 🔗 [Integrate APIs](recipes/api-integration/) - Connect external services
- 🐛 [Debug Issues](troubleshooting/) - Common problems and solutions

## 📚 Reference
Quick lookup for syntax, functions, and commands.

- [Dana Language Reference](reference/dana-syntax.md) - Complete syntax guide
- [Function Catalog](reference/functions.md) - All available functions with examples
- [REPL Commands](reference/repl-guide.md) - Interactive development environment
- [Error Messages](troubleshooting/error-reference.md) - Error codes and fixes

## 🎯 By Experience Level
- **New to OpenDXA**: Start with [Quick Start](#-quick-start)
- **Experienced Developer**: Jump to [Common Tasks](#-common-tasks)
- **Debugging Issue**: Check [Troubleshooting](troubleshooting/)
```

[Create similar detailed entry points for other audiences following same pattern]

### Phase 4: Content Adaptation
For each major concept, create audience-optimized versions:

**Example: Agent Architecture Concept**
```bash
# Create 4 different versions of agent architecture explanation:

# Engineers: Practical implementation guide
cat > docs/for-engineers/recipes/agent-architecture.md << 'EOF'
# Building Agent Architecture - Practical Guide

## What You'll Build
A structured agent with capabilities, resources, and clear data flow.

## Basic Agent Structure
```dana
private:agent_name = "DocumentProcessor"
private:capabilities = ["read_files", "extract_text", "summarize"]
# [Complete working example]
```
[Continue with practical examples...]
EOF

# [Create similar files for other audiences with appropriate focus]
```

### Phase 5: Update Cross-References
```bash
# Update main README to route users
cat > docs/README.md << 'EOF'
# OpenDXA Documentation

## Choose Your Path

### 🛠️ I want to build with OpenDXA
→ **[For Engineers](for-engineers/)** - Practical guides, recipes, and references
*Perfect for developers who want to get working quickly*

### 🔍 I'm evaluating OpenDXA for my team
→ **[For Evaluators](for-evaluators/)** - Comparisons, ROI analysis, and proof of concepts
*Perfect for technical leads and decision makers*

### 🏗️ I want to contribute or extend OpenDXA
→ **[For Contributors](for-contributors/)** - Architecture, codebase, and development guides
*Perfect for developers who want to modify or extend the system*

### 🧠 I want to understand the philosophy and theory
→ **[For Researchers](for-researchers/)** - Manifesto, theory, and academic context
*Perfect for researchers and those interested in the theoretical foundations*

[Continue with visual presentation and examples from current excellent README]
EOF
```

### Phase 6: Validation and Testing
```bash
# Validate migration completeness
echo "Checking that no critical content was lost..."

# Test that each audience tree is self-sufficient
echo "Testing engineer journey: Setup → First Agent → Complex Use Case"
# [Validation commands]

# Test all code examples work
echo "Testing all Dana code examples..."
find docs/ -name "*.md" -exec grep -l "```dana" {} \; | while read file; do
    echo "Testing examples in $file"
    # Extract and test Dana code blocks
done

# Verify cross-references work
echo "Checking internal links..."
# Link validation commands

# Confirm .ai-only is updated for new structure
echo "Validating AI assistant references..."
```

**Post-Migration Checklist**:
- [ ] All original content preserved (check docs/archive/)
- [ ] Each audience tree is self-sufficient for primary goals
- [ ] Cross-references between trees work correctly
- [ ] All Dana code examples execute successfully
- [ ] .ai-only updated for new structure
- [ ] Main README provides clear audience routing
- [ ] No broken internal links

**Output**: Complete migration with preserved content, improved organization, and validated functionality
```

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 
