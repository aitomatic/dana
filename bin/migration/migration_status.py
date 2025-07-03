#!/usr/bin/env python3
"""Track and display migration progress."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Migration phases and their tasks
PHASES = {
    0: {
        "name": "Pre-Migration Setup",
        "tasks": [
            "Create full backup of repository",
            "Tag current version as pre-migration-v1.0", 
            "Create dana/ directory structure",
            "Set up dual-import compatibility layer",
            "Create migration helper scripts",
            "Verify existing tests pass"
        ]
    },
    1: {
        "name": "Core Dana Language",
        "tasks": [
            "Copy Dana parser to dana/core/lang/parser/",
            "Copy interpreter to dana/core/lang/interpreter/",
            "Copy AST to dana/core/lang/ast/",
            "Create compatibility imports",
            "Add new import paths to sys.path"
        ]
    },
    2: {
        "name": "Runtime and Module System",
        "tasks": [
            "Migrate module system to dana/core/runtime/modules/",
            "Update module search paths",
            "Migrate REPL to dana/core/repl/",
            "Create forwarding imports"
        ]
    },
    3: {
        "name": "Standard Library Functions",
        "tasks": [
            "Copy function implementations to dana/core/stdlib/",
            "Update function registry",
            "Test core functions",
            "Test math functions",
            "Test string functions"
        ]
    }
}

STATUS_FILE = Path("scripts/migration/status.json")


def load_status() -> Dict:
    """Load migration status from file."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)
    return {"phases": {}, "started": datetime.now().isoformat()}


def save_status(status: Dict) -> None:
    """Save migration status to file."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def get_phase_status(status: Dict, phase: int) -> Tuple[int, int]:
    """Get completed and total tasks for a phase."""
    phase_data = status.get("phases", {}).get(str(phase), {})
    completed = len([t for t in phase_data.get("tasks", {}).values() if t.get("completed")])
    total = len(PHASES.get(phase, {}).get("tasks", []))
    return completed, total


def update_task_status(phase: int, task_index: int, completed: bool = True) -> None:
    """Update the status of a specific task."""
    status = load_status()
    phase_str = str(phase)
    
    if phase_str not in status["phases"]:
        status["phases"][phase_str] = {"tasks": {}}
    
    task_key = str(task_index)
    if task_key not in status["phases"][phase_str]["tasks"]:
        status["phases"][phase_str]["tasks"][task_key] = {}
    
    status["phases"][phase_str]["tasks"][task_key]["completed"] = completed
    status["phases"][phase_str]["tasks"][task_key]["timestamp"] = datetime.now().isoformat()
    
    save_status(status)


def display_status() -> None:
    """Display current migration status."""
    status = load_status()
    
    print("\n" + "="*60)
    print("DANA MIGRATION STATUS")
    print("="*60)
    print(f"Started: {status.get('started', 'Unknown')}")
    print()
    
    total_tasks = 0
    completed_tasks = 0
    
    for phase_num, phase_info in PHASES.items():
        completed, total = get_phase_status(status, phase_num)
        total_tasks += total
        completed_tasks += completed
        
        # Determine phase status
        if completed == 0:
            status_icon = "⏳"
            status_text = "Pending"
        elif completed < total:
            status_icon = "🔄"
            status_text = f"In Progress ({completed}/{total})"
        else:
            status_icon = "✅"
            status_text = "Complete"
        
        print(f"Phase {phase_num}: {phase_info['name']} {status_icon} {status_text}")
        
        # Show task details if phase is in progress
        if 0 < completed < total:
            phase_data = status.get("phases", {}).get(str(phase_num), {})
            for i, task in enumerate(phase_info["tasks"]):
                task_completed = phase_data.get("tasks", {}).get(str(i), {}).get("completed", False)
                icon = "✓" if task_completed else "○"
                print(f"  {icon} {task}")
    
    # Overall progress
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    print()
    print(f"Overall Progress: {completed_tasks}/{total_tasks} tasks ({progress:.1f}% Complete)")
    print("="*60)


def mark_phase_complete(phase: int) -> None:
    """Mark all tasks in a phase as complete."""
    for i in range(len(PHASES[phase]["tasks"])):
        update_task_status(phase, i, True)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "complete":
            if len(sys.argv) > 2:
                phase = int(sys.argv[2])
                mark_phase_complete(phase)
                print(f"Marked phase {phase} as complete")
        elif sys.argv[1] == "task":
            if len(sys.argv) > 3:
                phase = int(sys.argv[2])
                task = int(sys.argv[3])
                update_task_status(phase, task)
                print(f"Marked phase {phase} task {task} as complete")
    
    display_status()