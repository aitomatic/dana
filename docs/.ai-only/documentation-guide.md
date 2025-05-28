# OpenDXA Documentation Guide

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

## Documentation Strategy & Vision

### Current Documentation Structure (Updated 2025-01-24)

**Target Audience Organization:**
```
docs/
├── README.md                    # Audience routing hub
├── for-engineers/               # Practical guides, recipes, and references
├── for-evaluators/             # Business ROI, competitive analysis, proof of concepts
├── for-contributors/           # Architecture, codebase navigation, development guides
├── for-researchers/            # Philosophy, theory, neurosymbolic research, manifesto
├── designs/                    # Authoritative design specifications and language documentation
└── .ai-only/                   # AI assistant reference materials
```

**Key Reference Files:**
- `docs/designs/dana/manifesto.md` - Authoritative philosophy and vision
- `docs/designs/dana/language.md` - Complete Dana language specification
- `docs/designs/dana/syntax.md` - Current Dana syntax rules
- `docs/for-engineers/reference/dana-syntax.md` - Practical Dana reference for developers
- `docs/for-researchers/manifesto/vision.md` - Updated philosophical foundations
- `docs/.ai-only/opendxa.md` - System overview and components
- `docs/.ai-only/functions.md` - Current function catalog
- `docs/.ai-only/project.md` - Directory structure guide

### Audience Definitions

#### Engineers
**Primary Goals:** Build working solutions quickly, troubleshoot issues, integrate with existing systems
**Content Focus:** Step-by-step recipes, working code examples, troubleshooting guides, API references
**Success Metrics:** Time to first working implementation, problem resolution speed

#### Evaluators  
**Primary Goals:** Assess business value, compare alternatives, justify adoption decisions
**Content Focus:** ROI analysis, competitive comparisons, proof of concepts, implementation effort estimates
**Success Metrics:** Decision confidence, business case strength, risk assessment clarity

#### Contributors
**Primary Goals:** Understand architecture, extend functionality, contribute improvements
**Content Focus:** System design, extension points, development workflows, testing patterns
**Success Metrics:** Contribution quality, development velocity, architectural understanding

#### Researchers
**Primary Goals:** Understand theoretical foundations, explore research applications, advance the field
**Content Focus:** Design rationale, academic connections, theoretical implications, future research directions
**Success Metrics:** Research insights, academic contributions, theoretical advancement

### Documentation Principles

1. **Audience-First Organization**: Each audience tree is self-sufficient for primary goals
2. **Separation of Concerns**: Implementation details vs architectural concepts vs business value
3. **Cross-Reference System**: Clear navigation between audience-specific content
4. **Single Source of Truth**: Avoid duplication while maintaining audience-appropriate presentation
5. **Validation-Driven**: All code examples must be tested and working

## Daily Maintenance Procedures

### Function Registry Scan & Documentation Update

**Frequency:** Daily
**Purpose:** Ensure new/modified functions are documented across all audience trees

**Step 1: Identify Changes**
```bash
# Check for new/modified functions (past 24 hours)
find opendxa/dana/ opendxa/agent/capability/ opendxa/common/ -name "*.py" -newer docs/.ai-only/functions.md -exec echo "Modified: {}" \;

# Extract function signatures from new files
grep -n "def " [MODIFIED_FILES] | grep -v "__"
```

**Step 2: Update Documentation**
For each new function, update all audience trees using the templates in `templates/function-docs.md`.

**Step 3: Validation**
```bash
# Test all Dana code examples
find docs/ -name "*.md" -exec grep -l "```dana" {} \; | while read file; do
    sed -n '/```dana/,/```/p' "$file" | sed '1d;$d' > "temp_${file##*/}.na"
    bin/dana "temp_${file##*/}.na" || echo "❌ $file has broken examples"
done
```

### Dana Code Example Validation

**Frequency:** Daily
**Purpose:** Ensure all Dana code examples work with current syntax

**Step 1: Find Examples**
```bash
find docs/ -name "*.md" -exec grep -l "```dana" {} \; > dana_example_files.txt
```

**Step 2: Validate Syntax**
- Check variable scope syntax (`private:`, `public:`, `system:`, `local:`)
- Verify function call patterns match current specification
- Validate REPL commands against current implementation
- Ensure f-string formatting follows current standards

**Step 3: Fix and Test**
- Update syntax while preserving pedagogical purpose
- Add expected outputs where missing
- Test with `bin/dana` to verify functionality

## Weekly Analysis Procedures

### Documentation Gap Analysis

**Frequency:** Weekly
**Purpose:** Identify missing documentation for recent features and create prioritized task list

**Step 1: Analyze Recent Changes**
```bash
git log --since="7 days ago" --name-only --pretty=format: | grep -E '\.(py|md)$' | sort -u > recent_changes.txt
find opendxa/ -name "*.py" -newer docs/.ai-only/opendxa.md
find opendxa/agent/capability/ -name "*.py" -newer docs/.ai-only/functions.md
find examples/dana/na/ -name "*.na" -newer docs/.ai-only/dana.md
```

**Step 2: Gap Assessment**
For each new module/feature, assess impact on all audiences:
- **Engineers**: Missing practical guides, troubleshooting docs
- **Evaluators**: Missing business value analysis, competitive positioning
- **Contributors**: Missing architecture docs, extension guides
- **Researchers**: Missing theoretical context, design rationale

**Step 3: Prioritization**
- **High Priority**: Blocks user success (missing engineer recipes)
- **Medium Priority**: Affects adoption (missing evaluator analysis)
- **Low Priority**: Nice to have (missing theoretical context)

**Step 4: Issue Creation**
Create GitHub issues for significant gaps using the template in `templates/gap-analysis.md`.

### Competitive Positioning Update

**Frequency:** Weekly
**Purpose:** Keep competitive analysis current and accurate

**Step 1: Review Current Comparisons**
- Check `docs/for-evaluators/comparison/` for accuracy
- Research recent competitor developments
- Identify new competitors or capabilities

**Step 2: Update Comparisons**
- Use comparison matrix template from `templates/competitive-analysis.md`
- Quantify advantages where possible
- Include honest assessment of competitor strengths
- Ensure consistency across all evaluator documentation

## Event-Driven Procedures

### New Feature Documentation

**Trigger:** New feature implementation
**Purpose:** Create comprehensive documentation across all audience trees

**Required Context Variables:**
- `FEATURE_NAME`: Name of the new feature
- `MODULE_PATH`: Implementation location
- `FEATURE_TYPE`: Agent capability/Dana language feature/Core system

**Process:**
1. **Feature Analysis**: Understand implementation, integration, use cases, dependencies
2. **Audience-Specific Documentation**: Create content using templates in `templates/feature-docs.md`
3. **Cross-Reference Updates**: Add to indexes and navigation
4. **Validation**: Test all code examples and verify links

### Breaking Change Migration

**Trigger:** Breaking changes to API or syntax
**Purpose:** Help users migrate smoothly with minimal disruption

**Required Context Variables:**
- `CHANGE_DESCRIPTION`: What changed
- `AFFECTED_COMPONENTS`: System parts affected
- `OLD_PATTERN`: Previous behavior
- `NEW_PATTERN`: New behavior
- `TIMELINE`: When change takes effect

**Process:**
1. **Impact Analysis**: Find affected documentation and examples
2. **Migration Guides**: Create audience-specific migration documentation using templates in `templates/migration.md`
3. **Content Updates**: Fix all affected examples and add deprecation warnings
4. **Validation**: Test migration completeness and functionality

## Quality Standards

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

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 