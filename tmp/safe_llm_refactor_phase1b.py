#!/usr/bin/env python3
"""
Safe LLMResource Phase 1B: Minimal Configuration Manager Integration

This script carefully integrates the LLMConfigurationManager into LLMResource
without removing existing code. This allows us to test the integration first.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from pathlib import Path
from refactoring_safety_framework import SafetyFramework, RefactoringContext

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def safe_integrate_configuration_manager():
    """Phase 1B: Minimal integration of LLMConfigurationManager."""
    framework = SafetyFramework()
    
    context = RefactoringContext(
        name="llm_resource_phase1b_integration",
        description="Integrate LLMConfigurationManager alongside existing code",
        target_files=[
            "opendxa/common/resource/llm_resource.py"
        ],
        test_modules=[
            "tests/common/resource/",
        ]
    )
    
    # Load baseline
    baseline = framework.load_baseline()
    if baseline is None:
        print("❌ No baseline found. Run safety framework first.")
        return False
    
    print(f"📊 Baseline: {baseline.passed}/{baseline.total} tests passing ({baseline.success_rate:.1f}%)")
    
    # Create backup
    backup_name = framework.create_backup(context)
    
    try:
        print(f"\n🔧 Phase 1B: {context.description}")
        print("⚠️  MINIMAL CHANGE: Adding configuration manager alongside existing code")
        
        # Read the current LLMResource file
        llm_file_path = project_root / "opendxa/common/resource/llm_resource.py"
        with open(llm_file_path, 'r') as f:
            content = f.read()
        
        # Add import for configuration manager
        import_line = "from opendxa.common.resource.llm_configuration_manager import LLMConfigurationManager"
        
        # Find the imports section and add our import
        lines = content.split('\n')
        import_insertion_point = -1
        for i, line in enumerate(lines):
            if line.startswith('from opendxa.common.utils.token_management import TokenManagement'):
                import_insertion_point = i + 1
                break
        
        if import_insertion_point > 0:
            lines.insert(import_insertion_point, import_line)
        
        # Add configuration manager initialization in __init__ method
        # Find the __init__ method and add config manager initialization
        new_lines = []
        in_init_method = False
        added_config_manager = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Look for __init__ method
            if line.strip().startswith('def __init__('):
                in_init_method = True
            
            # Add config manager after BaseResource.__init__ call
            if in_init_method and 'BaseResource.__init__' in line and not added_config_manager:
                new_lines.append('')
                new_lines.append('        # Initialize configuration manager (Phase 1B integration)')
                new_lines.append('        self._config_manager = LLMConfigurationManager(')
                new_lines.append('            explicit_model=explicit_model,')
                new_lines.append('            config=config or {}')
                new_lines.append('        )')
                added_config_manager = True
        
        # Write the updated content
        with open(llm_file_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Updated: {llm_file_path}")
        print("   - Added import for LLMConfigurationManager")
        print("   - Added config manager initialization in __init__")
        print("   - Existing code preserved unchanged")
        
        # Test that the changes work
        print("🧪 Testing integration...")
        
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/common/resource/test_llm_resource.py", "-v"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print(f"✅ Integration successful - all LLM tests still passing!")
            
            # Also test that we can import the configuration manager
            try:
                exec("from opendxa.common.resource.llm_resource import LLMResource; r = LLMResource(name='test')")
                print(f"✅ LLMResource can be instantiated with configuration manager")
                return True
            except Exception as e:
                print(f"❌ LLMResource instantiation failed: {e}")
                framework.restore_backup(backup_name)
                return False
        else:
            print(f"❌ Integration failed - tests are broken:")
            print(result.stdout)
            print(result.stderr)
            framework.restore_backup(backup_name)
            return False
            
    except Exception as e:
        print(f"💥 Integration error: {e}")
        framework.restore_backup(backup_name)
        return False


def main():
    """Main entry point for Phase 1B integration."""
    print("🔧 LLMResource Phase 1B: Minimal Configuration Manager Integration")
    print("   Strategy: Add configuration manager alongside existing code")
    print("   Risk: Very Low - no existing code removed")
    print("   Goal: Test integration before replacing existing methods")
    
    success = safe_integrate_configuration_manager()
    
    if success:
        print(f"\n✅ Phase 1B integration completed successfully!")
        print(f"   - LLMConfigurationManager is now available in LLMResource")
        print(f"   - All existing functionality preserved")
        print(f"   - Ready for Phase 2: Start using configuration manager methods")
    else:
        print(f"\n❌ Phase 1B integration failed")
        print(f"   - Changes rolled back by safety framework")
        print(f"   - LLMResource functionality preserved")


if __name__ == "__main__":
    main()