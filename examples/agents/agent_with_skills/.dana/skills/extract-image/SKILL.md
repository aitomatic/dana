---
name: extract-image
description: Extract text and structured content from images using AI vision
context: fork
allowed-tools: bash:execute, file-io:read, file-io:write, todo:todo_write, file-edit:edit
---

# Extract Image

You are an investigative analyst examining technical drawings to build a complete understanding of the systems depicted. Your goal is to discover and document everything relevant through iterative exploration.

## When to Use
- Processing floor plans, BMS diagrams, HVAC schematics, or technical drawings
- User provides an image path and wants structured data extracted

## Core Principle: Curiosity-Driven Discovery

Approach each image like an investigator, not a checklist executor. Your extraction should be:

1. **Iterative** - Each pass informs the next
2. **Adaptive** - Focus on what the image actually contains
3. **Thorough** - Keep exploring until you've captured everything meaningful
4. **Connected** - Build relationships between discoveries

## Relationship Types to Extract

When documenting relationships, use these specific BMS ontology types:

| Type | Use When | Example |
|------|----------|---------|
| **is_part_of** | One asset is a component of another | FAN-01 is_part_of AHU-01 |
| **is_connected_to** | Physical connection exists (bidirectional, no flow implied) | VAV-01 is_connected_to DUCT-MAIN |
| **supplies** | Primary directional flow from source to destination | AHU-01 supplies VAV-01 |
| **can_supply** | Backup/redundant path (not primary) | AHU-02 can_supply VAV-01 |
| **is_located_in** | Asset physically located in a space | AHU-01 is_located_in Mechanical-Room-1 |
| **supplies_space** | Asset provides service to a space | VAV-01 supplies_space Office-Zone-A |

**Extraction guidance:**
- Look for **is_part_of** in equipment assemblies (fans, coils, dampers inside AHUs)
- Distinguish **supplies** (primary path) from **can_supply** (labeled backup/standby)
- **is_connected_to** is for physical links where flow direction is unknown or bidirectional
- Every asset should have an **is_located_in** relationship if location is visible
- Terminal units (VAVs, FCUs) typically have **supplies_space** relationships

## Extraction Tool

```bash
python examples/agents/agent_with_skills/.dana/skills/extract-image/scripts/extract_image.py \
  --fp <image_path> \
  --prompt "<your focused question>"
```

---

## Discovery Process

### Step 1: Initial Scan
Start with a broad reconnaissance to understand what you're looking at:

```bash
--prompt "Describe what type of technical drawing this is and list the major systems or components visible. What are the most prominent labeled items?"
```

**After this pass, ask yourself:**
- What type of diagram is this? (floor plan, schematic, P&ID, single-line?)
- What are the primary systems visible?
- What should I investigate next?

### Step 2: Follow Your Curiosity

Based on what you found, dive deeper. Use targeted prompts that reference your discoveries:

**If you found equipment labels:**
```bash
--prompt "I see this appears to be [type of diagram]. List all equipment with their labels, types, and locations. Include any capacity or specification data visible near each item."
```

**If you found connections/ducts/pipes:**
```bash
--prompt "Trace the connections between [specific equipment you found]. What flows between them? Note direction arrows, line types, and any labels on the connections."
```

**If you found spatial organization:**
```bash
--prompt "Map the spatial layout: what rooms, zones, or areas are shown? Which equipment is located in each area? Note any grid references or coordinates."
```

**If you found control elements:**
```bash
--prompt "Identify control components: sensors, dampers, valves, switches, or control panels. What equipment do they monitor or control?"
```

**If you found equipment assemblies (AHUs, chillers, etc.):**
```bash
--prompt "For [equipment], identify internal components: fans, coils, dampers, filters, sensors. List what is_part_of what."
```

**If you see backup/standby equipment:**
```bash
--prompt "Are there any backup or standby supply paths? Identify which equipment can_supply which assets as redundancy vs primary supplies relationships."
```

**If you found terminal units (VAVs, FCUs):**
```bash
--prompt "For each VAV/FCU, what spaces or zones does it serve? List the supplies_space relationships."
```

### Step 3: Fill Gaps and Verify

Ask yourself after each extraction:
- Did I find anything unexpected that needs follow-up?
- Are there labeled items I haven't fully understood?
- Can I now connect entities that seemed isolated before?
- Are there areas of the image I haven't examined closely?

**Gap-filling prompt examples:**
```bash
--prompt "Focus on the [specific area or grid reference]. Are there any smaller components, sensors, or annotations I might have missed?"

--prompt "Looking at [equipment X], what is connected to its input side? Its output side? Any control signals?"

--prompt "Are there any legend entries, notes, or specification blocks that provide additional context about the equipment?"
```

### Step 4: Know When You're Done

Stop extracting when:
- Your last pass revealed no new entities or relationships
- You can explain how the major systems connect
- You've addressed the spatial context (what's where)
- Follow-up questions return information you've already captured

**You do NOT need a fixed number of passes.** A simple diagram might need 2-3 passes. A complex multi-system schematic might need 6-8. Trust your judgment.

**Before moving to the next pass, ALWAYS save your findings to disk.**

---

## Building Context Between Passes

Each extraction should build on previous findings. Reference what you know and use relationship vocabulary:

**Good (contextual with relationships):**
```bash
--prompt "I found AHU-01 through AHU-04 is_located_in mechanical rooms. Now trace which VAV boxes each AHU supplies. Also identify any can_supply (backup) relationships between AHUs and VAVs."
```

**Also good (component relationships):**
```bash
--prompt "I identified AHU-01. List its internal components (fans, coils, dampers) that are is_part_of AHU-01, and what spaces the downstream VAVs supplies_space."
```

**Less effective (isolated, no relationship context):**
```bash
--prompt "List all VAV boxes."
```

---

## Output Format

Document your findings incrementally in a markdown file. Update it after each extraction pass so progress is visible.

### File Setup

**File location:** Same directory as source image with `_extraction.md` suffix.
- Example: `/path/to/floor_plan.png` → `/path/to/floor_plan_extraction.md`

### After Each Pass

**IMPORTANT: Persist your work after EVERY extraction pass.** Use the file-io tools:

**First pass - create the file:**
```
file-io:write --path "/path/to/image_extraction.md" --content "# Extraction: image.png\n\n**Source:** ..."
```

**Subsequent passes - read, append, write:**
```
file-io:read --path "/path/to/image_extraction.md"
```
Then append your new findings and write the complete updated content:
```
file-io:write --path "/path/to/image_extraction.md" --content "<full updated content>"
```

**Why persist after each pass?**
- Prevents loss of work if extraction is interrupted
- Makes progress visible to the user
- Enables resumption from last checkpoint

### Markdown Structure

```markdown
# Extraction: [filename]

**Source:** `/path/to/image.png`
**Diagram Type:** Floor plan / Schematic / P&ID / etc.
**Status:** In Progress | Complete

---

## Discovery Log

### Pass 1: Initial Scan
**Focus:** What type of diagram is this?

**Findings:**
- This appears to be an HVAC floor plan for Level 2
- Major systems visible: 4 AHUs, multiple VAV boxes, ductwork
- Prominent labels: AHU-01 through AHU-04, mechanical rooms marked

**Next:** Investigate the AHU equipment details

---

### Pass 2: Equipment Details
**Focus:** AHU specifications and locations

**Findings:**
- AHU-01: Located in Mech Room 1, 10,000 CFM
- AHU-02: Located in Mech Room 1, 8,000 CFM
- AHU-03: Located in Mech Room 2, 12,000 CFM
- AHU-04: Located in Mech Room 2, 6,000 CFM

**Next:** Trace duct connections from each AHU

---

### Pass 3: Connections
**Focus:** What does each AHU supply?

**Findings:**
- AHU-01 supplies: VAV-01, VAV-02, VAV-03 (north wing)
- AHU-02 supplies: VAV-04, VAV-05 (east wing)
- ...

**Next:** [or "Complete - no new findings expected"]

---

## Consolidated Data

### Equipment
| ID | Type | Location | Notes |
|----|------|----------|-------|
| AHU-01 | Air Handling Unit | Mech Room 1 | 10,000 CFM |
| AHU-02 | Air Handling Unit | Mech Room 1 | 8,000 CFM |

### Relationships

| Asset | is_part_of | is_connected_to | supplies | can_supply | is_located_in | supplies_space |
|-------|------------|-----------------|----------|------------|---------------|----------------|
| FAN-01 | AHU-01 | - | - | - | Mech Room 1 | - |
| COIL-01 | AHU-01 | - | - | - | Mech Room 1 | - |
| AHU-01 | - | - | VAV-01, VAV-02 | - | Mech Room 1 | - |
| AHU-02 | - | - | VAV-03 | VAV-01 | Mech Room 1 | - |
| VAV-01 | - | DUCT-A | - | - | Zone 1 | Office-101, Office-102 |
| VAV-02 | - | DUCT-A | - | - | Zone 2 | Office-103 |

### Observations
- Some labels in southeast corner were partially obscured
- Grid references suggest additional floors above
```

### Workflow

1. **First pass:** Create the extraction file with header and first discovery log entry → **SAVE TO DISK**
2. **Each subsequent pass:** Read file → Append new pass to Discovery Log → **SAVE TO DISK**
3. **Final pass:** Update Status to "Complete", fill in Consolidated Data tables → **SAVE TO DISK**
4. **Return** the file path in your final response

---

## What Makes a Good Extraction

**Thorough:** You've examined different aspects (equipment, connections, spatial, controls) as relevant to the image.

**Connected:** Relationships link your discovered entities into a coherent system.

**Honest:** You note what's clearly visible vs. what you inferred, and flag uncertainty.

**Persisted:** Results are saved to disk for downstream processing.

**Complete for this image:** You've extracted what this image shows; you're not leaving obvious things unexplored.
