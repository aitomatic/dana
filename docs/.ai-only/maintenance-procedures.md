# OpenDXA Documentation Maintenance Procedures

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

## Essential Context

**Key Reference Files** (Read before executing any procedure):
- `docs/designs/dana/manifesto.md` - Authoritative philosophy and vision
- `docs/designs/dana/language.md` - Complete Dana language specification
- `docs/designs/dana/syntax.md` - Current Dana syntax rules
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
- `docs/designs/` - Authoritative design specifications and language documentation
- `docs/.ai-only/` - AI assistant reference materials

## Daily Maintenance Procedures

### PROCEDURE 1: Function Registry Scan & Documentation Update

**Frequency:** Daily
**Purpose:** Ensure new/modified functions are documented across all audience trees
**Estimated Time:** 15-30 minutes

#### Step 1: Identify Changes
```bash
# Check for new/modified functions (past 24 hours)
find opendxa/dana/ opendxa/agent/capability/ opendxa/common/ -name "*.py" -newer docs/.ai-only/functions.md -exec echo "Modified: {}" \;

# Extract function signatures from new files
grep -n "def " [MODIFIED_FILES] | grep -v "__"

# Check for new examples
find examples/dana/na/ -name "*.na" -newer docs/.ai-only/dana.md
```

#### Step 2: Extract Function Details
For each new function found:
- Function signature and parameters
- Docstring content
- Any inline code examples
- Identify primary use cases
- Note dependencies and prerequisites

#### Step 3: Update All Audience Trees
Use templates from `templates/function-docs.md` to create:

**Engineers Documentation** (`docs/for-engineers/reference/functions.md`):
- Practical usage examples
- Troubleshooting common issues
- Integration patterns

**Evaluators Documentation** (`docs/for-evaluators/roi-analysis/new-capabilities.md`):
- Business value analysis
- ROI calculations
- Competitive positioning

**Contributors Documentation** (`docs/for-contributors/extending/function-development.md`):
- Implementation details
- Extension points
- Testing approaches

**Researchers Documentation** (`docs/for-researchers/research/capability-evolution.md`):
- Theoretical foundations
- Academic connections
- Research implications

#### Step 4: Update AI Assistant Reference
Update `docs/.ai-only/functions.md` with structured reference including:
- Module path and signature
- Purpose and use cases
- Links to audience-specific documentation
- Common patterns and error handling

#### Step 5: Validation
```bash
# Test all Dana code examples
find docs/ -name "*.md" -exec grep -l "```dana" {} \; | while read file; do
    sed -n '/```dana/,/```/p' "$file" | sed '1d;$d' > "temp_${file##*/}.na"
    bin/dana "temp_${file##*/}.na" || echo "❌ $file has broken examples"
    rm -f "temp_${file##*/}.na"
done
```

#### Completion Checklist
- [ ] Function signature and purpose documented
- [ ] Working code examples tested with `bin/dana`
- [ ] All 4 audience trees updated with appropriate content
- [ ] .ai-only reference updated for AI assistant use
- [ ] Cross-references added where relevant
- [ ] Examples verified to produce expected outputs

---

### PROCEDURE 2: Dana Code Example Validation & Syntax Updates

**Frequency:** Daily
**Purpose:** Ensure all Dana code examples work with current syntax
**Estimated Time:** 20-40 minutes

#### Step 1: Find All Dana Examples
```bash
# Find all Dana code examples in documentation
find docs/ -name "*.md" -exec grep -l "```dana" {} \; > dana_example_files.txt

# Count total examples for progress tracking
grep -r "```dana" docs/ | wc -l
```

#### Step 2: Extract and Test Examples
```bash
# Process each file with Dana examples
while read file; do
    echo "Processing $file"
    # Extract Dana code blocks
    sed -n '/```dana/,/```/p' "$file" | sed '1d;$d' > "temp_${file##*/}.na"
    
    # Test if the code runs
    if bin/dana "temp_${file##*/}.na" 2>/dev/null; then
        echo "✅ $file examples work"
    else
        echo "❌ $file has broken examples - needs fixing"
        # Log the error for detailed analysis
        bin/dana "temp_${file##*/}.na" 2>&1 | head -5
    fi
    
    # Clean up temp file
    rm -f "temp_${file##*/}.na"
done < dana_example_files.txt
```

#### Step 3: Fix Broken Examples
For each broken example, validate against current syntax:

**Variable Scope Syntax:**
- Check for proper colon notation: `private:`, `public:`, `system:`, `local:`
- Ensure no dot notation: `private.x`, `public.x`
- Prefer unscoped variables (auto-scoped to local) when appropriate

**Function Call Patterns:**
- Verify against current specification in `docs/designs/dana/language.md`
- Check reason() function syntax
- Validate parameter passing patterns

**REPL Commands:**
- Ensure commands match `docs/designs/dana/repl.md`
- Verify multiline input patterns
- Check ##nlp on/off syntax

**F-String Formatting:**
- Ensure current f-string syntax
- Validate variable references in strings

#### Step 4: Update Examples While Preserving Purpose
- Keep the same learning objective
- Maintain pedagogical flow
- Add expected output where missing
- Include error examples where helpful

#### Step 5: Validate Against Best Practices
Check examples against current patterns in:
- `examples/dana/na/basic_assignments.na` - Variable assignment patterns
- `examples/dana/na/reason_demo.na` - AI reasoning integration
- `examples/dana/na/multiple_scopes.na` - Scope usage patterns

#### Completion Checklist
- [ ] All Dana code blocks identified and extracted
- [ ] Broken examples fixed with current syntax
- [ ] Pedagogical purpose preserved in all updates
- [ ] Expected outputs documented where missing
- [ ] Examples tested with current `bin/dana`
- [ ] Consistency with official examples verified

---

## Weekly Analysis Procedures

### PROCEDURE 3: Documentation Gap Analysis & Issue Creation

**Frequency:** Weekly (Monday mornings recommended)
**Purpose:** Identify missing documentation for recent features and create prioritized task list
**Estimated Time:** 45-60 minutes

#### Step 1: Analyze Recent Changes
```bash
# Analyze recent codebase changes (past 7 days)
git log --since="7 days ago" --name-only --pretty=format: | grep -E '\.(py|md)$' | sort -u > recent_changes.txt

# Check for new modules without documentation
find opendxa/ -name "*.py" -newer docs/.ai-only/opendxa.md -exec echo "New module: {}" \;

# Identify new capabilities
find opendxa/agent/capability/ -name "*.py" -newer docs/.ai-only/functions.md

# Check for new examples
find examples/dana/na/ -name "*.na" -newer docs/.ai-only/dana.md

# Look for new tests that might indicate new features
find tests/ -name "*.py" -newer docs/.ai-only/opendxa.md
```

#### Step 2: Gap Assessment by Audience
For each new module/feature found, assess impact on all audiences:

**Engineers Gap Assessment:**
- Missing: Step-by-step implementation guides
- Need: Copy-paste code recipes for common use cases
- Missing: Troubleshooting documentation for new error patterns
- Need: Integration examples with existing workflows

**Evaluators Gap Assessment:**
- Missing: Business value quantification and ROI analysis
- Need: Competitive positioning vs LangChain/AutoGen
- Missing: Implementation effort and resource requirements
- Need: Risk assessment and mitigation strategies

**Contributors Gap Assessment:**
- Missing: Architecture documentation for new components
- Need: Extension points and customization guides
- Missing: Testing patterns and development workflows
- Need: Code organization and dependency explanations

**Researchers Gap Assessment:**
- Missing: Theoretical foundations and design rationale
- Need: Academic connections and research implications
- Missing: Experimental results or validation studies
- Need: Future research directions enabled by new capabilities

#### Step 3: Prioritization Matrix
**High Priority (Blocks User Success):**
- Missing engineer recipes that prevent basic implementation
- Critical troubleshooting docs for common errors
- Essential API documentation for new features

**Medium Priority (Affects Adoption):**
- Missing evaluator analysis that blocks decision-making
- Incomplete competitive positioning
- Missing contributor guides that slow development

**Low Priority (Nice to Have):**
- Missing theoretical context for researchers
- Advanced use case documentation
- Optimization guides

#### Step 4: Create GitHub Issues
For significant gaps, create GitHub issues using this template:

```markdown
Title: [DOCS] Missing documentation for [Feature/Module Name]

**Gap Description**: [What's missing and why it's needed]
**Affected Audiences**: [Engineers/Evaluators/Contributors/Researchers]
**User Impact**: [How this affects user success - be specific]
**Priority**: [High/Medium/Low based on user impact]

**Required Documentation**:
- [ ] `docs/for-engineers/[specific-file].md` - [What content needed]
- [ ] `docs/for-evaluators/[specific-file].md` - [What content needed]
- [ ] `docs/for-contributors/[specific-file].md` - [What content needed]
- [ ] `docs/for-researchers/[specific-file].md` - [What content needed]

**Success Criteria**:
- [ ] Users can successfully implement basic use cases
- [ ] Decision makers have sufficient context for adoption
- [ ] Contributors can extend/modify the feature
- [ ] Researchers understand theoretical foundations

**Estimated Effort**: [Hours needed for complete documentation]
**Dependencies**: [Any blockers or prerequisites]
```

#### Step 5: Update Documentation Roadmap
Maintain a documentation roadmap in `docs/.ai-only/roadmap.md` with:
- Current quarter priorities
- Upcoming documentation needs
- Resource allocation
- Timeline estimates

#### Completion Checklist
- [ ] All recent changes analyzed for documentation gaps
- [ ] Gap impact assessed for all four audiences
- [ ] Priorities assigned based on user impact
- [ ] GitHub issues created for significant gaps
- [ ] Documentation roadmap updated
- [ ] Team notified of high-priority gaps

---

### PROCEDURE 4: Competitive Positioning Update

**Frequency:** Weekly (Friday afternoons recommended)
**Purpose:** Keep competitive analysis current and accurate
**Estimated Time:** 30-45 minutes

#### Step 1: Review Current Comparisons
Check existing competitive documentation for accuracy:
- `docs/for-evaluators/comparison/vs-langchain.md`
- `docs/for-evaluators/comparison/vs-autogen.md`
- `docs/for-evaluators/comparison/competitive-matrix.md`
- `docs/for-evaluators/comparison/philosophy-overview.md`

#### Step 2: Research Recent Developments
**LangChain Updates:**
- Check latest releases and new capabilities
- Review recent blog posts and announcements
- Monitor community discussions and feature requests

**AutoGen Updates:**
- Review recent feature announcements
- Check academic papers and research developments
- Monitor Microsoft research publications

**New Competitors:**
- Search for emerging neurosymbolic/agent frameworks
- Monitor academic conferences and publications
- Check startup announcements in AI agent space

**Industry Trends:**
- Review recent AI agent market analysis
- Check enterprise adoption patterns
- Monitor regulatory and compliance developments

#### Step 3: Update Comparison Matrices
Use the template from `templates/competitive-analysis.md` to update:

```markdown
## Feature Comparison: OpenDXA vs [Competitor]

| Capability | OpenDXA | [Competitor] | Advantage |
|------------|---------|--------------|-----------|
| [Feature 1] | ✅ Native support | ❌ Requires plugins | Simpler setup, better performance |
| [Feature 2] | ✅ Built-in | ✅ Available | Comparable functionality |
| [Feature 3] | ❌ Planned Q2 | ✅ Available | Competitor advantage |

**OpenDXA Unique Value:**
- [Specific advantage not available elsewhere with quantification]
- [Another differentiator with evidence]

**When to Choose OpenDXA:**
- [Specific use case scenario with business justification]
- [Another decision criteria with measurable benefits]

**When [Competitor] Might Be Better:**
- [Honest assessment of competitor strengths]
- [Specific scenarios where competitor excels]
```

#### Step 4: Update Business Value Propositions
- Quantify advantages where possible ("50% faster setup", "30% fewer lines of code")
- Include real customer/user feedback if available
- Reference specific Dana language benefits with examples
- Highlight neurosymbolic approach advantages with concrete use cases

#### Step 5: Ensure Consistency Across Documentation
- Same competitive claims in all comparison files
- Updated feature lists reflect current OpenDXA capabilities
- Business value statements align with `docs/designs/dana/manifesto.md`
- Consistent messaging across all evaluator documentation

#### Completion Checklist
- [ ] All competitor developments researched and documented
- [ ] Comparison matrices updated with current information
- [ ] Business value propositions quantified where possible
- [ ] Consistency verified across all evaluator documentation
- [ ] New competitive insights shared with product team
- [ ] Documentation reflects honest assessment of strengths/weaknesses

---

## Event-Driven Procedures

### PROCEDURE 5: New Feature Documentation

**Trigger:** New feature implementation
**Purpose:** Create comprehensive documentation across all audience trees
**Estimated Time:** 2-4 hours depending on feature complexity

#### Pre-Documentation Analysis
Before creating documentation, thoroughly analyze:

**Feature Implementation:**
```bash
# Understand the feature implementation
grep -r "[FEATURE_NAME]" opendxa/
find . -name "*.py" -exec grep -l "[FEATURE_NAME]" {} \;
```

**Integration Points:**
- How does it integrate with existing system?
- What are the key use cases?
- What configuration options exist?
- Are there dependencies or prerequisites?

**User Impact:**
- What problem does this feature solve?
- Who is the primary audience?
- What's the learning curve?
- What are potential failure modes?

#### Documentation Creation Process
Use templates from `templates/feature-docs.md` to create audience-specific documentation:

**Engineers Documentation** (`docs/for-engineers/recipes/[feature-name].md`):
- 5-minute quick start with working example
- Step-by-step tutorial with expected outputs
- Common use cases with complete code
- Troubleshooting guide with specific solutions
- Integration examples with existing workflows

**Evaluators Documentation** (`docs/for-evaluators/roi-analysis/[feature-name].md`):
- Executive summary with quantified benefits
- Business value proposition with competitive analysis
- Implementation effort and resource requirements
- ROI analysis with timeline and break-even point
- Risk assessment with mitigation strategies

**Contributors Documentation** (`docs/for-contributors/extending/[feature-name].md`):
- Architecture overview with component relationships
- Code organization and key classes/functions
- Extension points and customization options
- Testing approach and performance characteristics
- Development workflow and debugging guidance

**Researchers Documentation** (`docs/for-researchers/research/[feature-name].md`):
- Theoretical foundations and design rationale
- Academic connections and related papers
- Neurosymbolic integration and hybrid benefits
- Experimental validation and research applications
- Future research directions and collaboration opportunities

#### Cross-Reference Updates
- Add feature to `.ai-only/functions.md` or `.ai-only/opendxa.md`
- Update README files in each audience tree
- Add cross-links from related existing documentation
- Update navigation and index files

#### Validation and Testing
```bash
# Test all Dana code examples
find docs/for-engineers/recipes/[feature-name].md -exec grep -l "```dana" {} \; | while read file; do
    sed -n '/```dana/,/```/p' "$file" | sed '1d;$d' > "temp_feature_test.na"
    bin/dana "temp_feature_test.na" || echo "❌ Example in $file failed"
    rm -f "temp_feature_test.na"
done

# Verify all links work
# Check that cross-references are accurate
# Ensure consistency across audience trees
```

#### Completion Checklist
- [ ] Feature thoroughly analyzed and understood
- [ ] All four audience trees have appropriate documentation
- [ ] Code examples tested and working
- [ ] Cross-references added and verified
- [ ] Navigation updated in relevant README files
- [ ] Documentation reviewed for consistency and accuracy

---

### PROCEDURE 6: Breaking Change Migration Documentation

**Trigger:** Breaking changes to API or syntax
**Purpose:** Help users migrate smoothly with minimal disruption
**Estimated Time:** 3-6 hours depending on change scope

#### Pre-Migration Analysis
**Impact Assessment:**
```bash
# Find all documentation that references old patterns
grep -r "[OLD_PATTERN]" docs/
grep -r "[OLD_PATTERN]" examples/

# Identify affected code examples
find docs/ -name "*.md" -exec grep -l "[OLD_SYNTAX]" {} \;

# Check for affected tests
grep -r "[OLD_PATTERN]" tests/
```

**Scope Analysis:**
- List all affected documentation files
- Identify broken examples that need updating
- Assess scope of user impact (how many projects affected)
- Determine urgency level (how quickly users must migrate)

#### Migration Guide Creation
Use templates from `templates/migration.md` to create audience-specific migration guides:

**Engineers Migration Guide** (`docs/for-engineers/migration/[change-name].md`):
- Breaking change alert with timeline and urgency
- Before/after examples with specific error messages
- Step-by-step migration with search commands
- Common migration issues with solutions
- Rollback plan and getting help resources

**Evaluators Migration Guide** (`docs/for-evaluators/migration/[change-name].md`):
- Business impact assessment with resource requirements
- Timeline and cost analysis
- Risk assessment and mitigation strategies
- Communication templates for stakeholders
- Success metrics and post-migration benefits

**Contributors Migration Guide** (`docs/for-contributors/migration/[change-name].md`):
- Technical overview with root cause analysis
- Code changes required with specific examples
- Extension migration for custom capabilities
- Testing migration and development workflow updates
- Performance impact and optimization opportunities

#### Content Updates
**Fix All Affected Examples:**
- Update syntax while preserving pedagogical purpose
- Add deprecation warnings to old documentation
- Create redirects from old content to migration guides
- Test all updated examples

**Update AI Assistant Guidance:**
```markdown
# Update docs/.ai-only/[relevant-file].md

## Breaking Change Alert: [Change Name]
**Status**: Active as of [date]
**Impact**: [What users will experience]
**Migration**: See [link to migration guides]
**AI Assistant Guidance**: When users mention [old pattern], direct them to migration guide
```

#### Validation Process
```bash
# Test migration completeness
echo "Checking that no critical content was lost..."

# Validate that each audience tree addresses migration needs
echo "Testing migration paths for each audience..."

# Test all updated code examples work
echo "Testing all updated Dana code examples..."
find docs/ -name "*.md" -path "*/migration/*" -exec grep -l "```dana" {} \; | while read file; do
    echo "Testing examples in $file"
    sed -n '/```dana/,/```/p' "$file" | sed '1d;$d' > "temp_migration_test.na"
    bin/dana "temp_migration_test.na" || echo "❌ Migration example in $file failed"
    rm -f "temp_migration_test.na"
done

# Verify cross-references work
echo "Checking internal links in migration documentation..."
```

#### Communication and Rollout
**Internal Communication:**
- Notify development team of migration documentation
- Share timeline and support resources
- Coordinate with product team on user communication

**User Communication:**
- Announce breaking change with migration resources
- Provide clear timeline and support channels
- Monitor user feedback and update documentation as needed

#### Completion Checklist
- [ ] Impact analysis completed and documented
- [ ] Migration guides created for all affected audiences
- [ ] All affected examples updated and tested
- [ ] Cross-references and navigation updated
- [ ] AI assistant guidance updated for new patterns
- [ ] Communication plan executed
- [ ] User feedback monitoring established

---

## Quality Assurance Procedures

### Code Example Standards
- All Dana code must execute successfully with current `bin/dana`
- Include expected outputs for all examples
- Use current syntax (colon notation for scopes)
- Provide context comments explaining purpose
- Follow patterns from official examples in `examples/dana/na/`

### Documentation Standards
- Each audience tree must be self-sufficient for primary goals
- Cross-references should enhance, not replace, self-sufficiency
- Templates ensure consistency across similar content types
- Regular validation prevents documentation drift

### Maintenance Standards
- Daily procedures ensure rapid response to changes
- Weekly analysis prevents accumulation of gaps
- Event-driven procedures handle major changes systematically
- All procedures include validation steps

### Error Handling
- Document common errors and their solutions
- Provide clear troubleshooting steps
- Include prevention strategies where applicable
- Maintain error message reference for quick lookup

---

## Emergency Procedures

### Critical Documentation Issues
**When to Use:** Documentation errors that block user success

**Immediate Response (within 2 hours):**
1. Assess impact and affected users
2. Create temporary fix or workaround
3. Notify affected users through appropriate channels
4. Begin permanent fix development

**Permanent Fix (within 24 hours):**
1. Implement comprehensive solution
2. Test thoroughly across all affected areas
3. Update related documentation
4. Verify fix resolves original issue

### Broken Code Examples
**When to Use:** Dana code examples that don't work with current system

**Immediate Response:**
1. Identify all affected examples
2. Add warning notices to affected documentation
3. Provide working alternatives where possible
4. Log issue for systematic fix

**Systematic Fix:**
1. Update all affected examples using current syntax
2. Test each example individually
3. Verify examples work in context
4. Remove warning notices once fixed

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 