# AI Documentation Automation Scripts

This directory contains automation scripts for AI to run complete documentation updates without human intervention.

## Scripts Overview

### `ai_doc_master.sh` - Master Automation Script
**Usage:** `bash docs/.ai-only/scripts/ai_doc_master.sh`
**Purpose:** Orchestrates the complete documentation update process
**What it does:**
- Runs all phases in sequence
- Handles error conditions
- Generates comprehensive summary
- Creates quality reports

### `ai_doc_discovery.sh` - Discovery & Analysis
**Purpose:** Identifies recent changes and documentation needs
**Outputs:**
- Recent changes analysis
- New functions detection
- Build status check
- Documentation statistics

### `ai_doc_content_update.sh` - Content Updates
**Purpose:** Updates function documentation and fixes code examples
**Outputs:**
- Functions processed
- Broken examples identified
- GitHub issues created
- Content update summary

### `ai_doc_structure_validate.sh` - Structure Validation
**Purpose:** Validates MkDocs navigation and checks for orphaned files
**Outputs:**
- Navigation validation results
- Orphaned files list
- Link checking results
- MkDocs configuration validation

### `ai_doc_qa.sh` - Quality Assurance
**Purpose:** Final validation and quality reporting
**Outputs:**
- Final Dana example tests
- Build validation
- Quality metrics
- Success criteria checklist

## Output Directory

All scripts write output to `docs/.ai-only/ai_output/`:
- `master_summary.txt` - Complete automation summary
- `quality_report.txt` - Quality assurance report
- `success_criteria.txt` - Success criteria checklist
- Various analysis files for each phase

## Success Criteria

The automation is considered successful when:
- ✅ All Dana examples execute successfully
- ✅ MkDocs builds without errors
- ✅ Navigation structure is valid
- ✅ No orphaned files
- ✅ All navigation files exist
- ✅ Content quality validated

## Usage

For complete autonomous documentation update:
```bash
bash docs/.ai-only/scripts/ai_doc_master.sh
```

For individual phases:
```bash
bash docs/.ai-only/scripts/ai_doc_discovery.sh
bash docs/.ai-only/scripts/ai_doc_content_update.sh
bash docs/.ai-only/scripts/ai_doc_structure_validate.sh
bash docs/.ai-only/scripts/ai_doc_qa.sh
```

## Requirements

- Python 3.x
- MkDocs
- Dana runtime (`bin/dana`)
- Git repository
- Make build system

## Error Handling

Scripts use `set -e` to stop on errors and provide clear error messages. Check the output files in `docs/.ai-only/ai_output/` for detailed results and any issues found. 