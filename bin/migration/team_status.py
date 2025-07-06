#!/usr/bin/env python3
"""
Team Migration Status - Generate summary for team communication
"""

import subprocess
from datetime import datetime


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_recent_branches() -> list[tuple[str, str, str]]:
    """Get list of recent branches with dates and authors."""
    code, stdout, stderr = run_command([
        "git", "for-each-ref", "--format=%(refname:short) %(committerdate:short) %(authorname)",
        "refs/remotes/origin/feat/", "refs/remotes/origin/demo/", "refs/remotes/origin/chore/"
    ])
    
    if code != 0:
        return []
    
    branches = []
    for line in stdout.strip().split('\n'):
        if line.strip():
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                branch, date, author = parts[0], parts[1], parts[2]
                branches.append((branch, date, author))
    
    # Sort by date (most recent first)
    branches.sort(key=lambda x: x[1], reverse=True)
    return branches[:15]  # Top 15 most recent


def get_migration_status() -> str:
    """Get current migration status."""
    try:
        with open("DANA_MIGRATION.md") as f:
            content = f.read()
            
        # Count completed phases
        completed = content.count("✅")
        total = content.count("Phase")
        
        return f"{completed}/{total} phases complete ({completed/total*100:.0f}%)"
    except:
        return "Status unknown"


def generate_team_summary():
    """Generate team communication summary."""
    
    print("=" * 70)
    print("📢 DANA MIGRATION - TEAM UPDATE")
    print("=" * 70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🚀 Status: {get_migration_status()}")
    print()
    
    print("📋 WHAT'S HAPPENING:")
    print("• Repository is being migrated from 'opendxa' to 'dana' structure")
    print("• All existing code continues to work (compatibility layer active)")
    print("• New code should use 'dana.*' imports")
    print("• Migration tools are available to help with branch updates")
    print()
    
    print("🔄 RECENT ACTIVE BRANCHES:")
    branches = get_recent_branches()
    if branches:
        for branch, date, author in branches[:10]:
            # Clean up branch name
            branch_name = branch.replace("origin/", "")
            print(f"  📋 {branch_name:<30} {date} ({author})")
    else:
        print("  No recent branches found")
    print()
    
    print("✅ WHAT WORKS NOW:")
    print("• All your existing imports (opendxa.*) work unchanged")
    print("• All existing tests should pass")
    print("• All existing functionality is preserved")
    print("• You can continue development normally")
    print()
    
    print("🔧 MIGRATION TOOLS AVAILABLE:")
    print("• scripts/migration/migrate_branch.py - Migrate your branch imports")
    print("• scripts/migration/validate_branch.py - Validate branch after migration")
    print("• TEAM_MIGRATION_STRATEGY.md - Detailed migration guide")
    print()
    
    print("📝 ACTION ITEMS FOR TEAM MEMBERS:")
    print("1. 📚 Read TEAM_MIGRATION_STRATEGY.md")
    print("2. 🔄 Test compatibility with your current branch:")
    print("   python scripts/migration/validate_branch.py")
    print("3. 🌟 For new work: Use 'dana.*' imports")
    print("4. 🔧 Migrate existing branches when ready:")
    print("   python scripts/migration/migrate_branch.py --dry-run")
    print("5. 💬 Report any issues or questions immediately")
    print()
    
    print("🆘 SUPPORT:")
    print("• Migration documentation: TEAM_MIGRATION_STRATEGY.md")
    print("• Technical details: DANA_MIGRATION.md")
    print("• Questions: Ask in team chat or create GitHub issue")
    print()
    
    print("🎯 TIMELINE:")
    print("• Week 1: Core migration complete (current)")
    print("• Week 1-2: Team member branch migrations")
    print("• Week 2: Final cutover and cleanup")
    print()
    
    print("💡 REMEMBER:")
    print("• Your existing code continues to work")
    print("• Migration is about adopting new structure, not fixing broken code")
    print("• Compatibility layer ensures smooth transition")
    print("• Tools are available to help with migration")
    print()
    
    print("=" * 70)
    print("Questions? Check TEAM_MIGRATION_STRATEGY.md or ask the team!")
    print("=" * 70)


if __name__ == "__main__":
    generate_team_summary()