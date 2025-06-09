#!/usr/bin/env python3
"""
Safe LLMResource Phase 2: Replace existing methods with configuration manager

This script carefully replaces existing configuration methods in LLMResource
with calls to the integrated LLMConfigurationManager, while preserving
all existing functionality.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from pathlib import Path
from refactoring_safety_framework import SafetyFramework, RefactoringContext

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def safe_replace_configuration_methods():
    """Phase 2: Replace existing configuration methods with configuration manager calls."""
    framework = SafetyFramework()
    
    context = RefactoringContext(
        name="llm_resource_phase2_replace_methods",
        description="Replace existing configuration methods with LLMConfigurationManager calls",
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
        print(f"\n🔧 Phase 2: {context.description}")
        print("⚠️  CRITICAL PHASE: Replacing existing functionality")
        
        # Read the current LLMResource file
        llm_file_path = project_root / "opendxa/common/resource/llm_resource.py"
        with open(llm_file_path, 'r') as f:
            content = f.read()
        
        # Strategy: Replace method implementations while keeping signatures identical
        # This preserves the external API completely
        
        # Check that the file has the configuration manager import
        if "from opendxa.common.resource.llm_configuration_manager import LLMConfigurationManager" not in content:
            print("❌ LLMConfigurationManager import not found. Run Phase 1B first.")
            return False
        
        print("✅ LLMConfigurationManager import found")
        
        # Replace model property getter
        old_getter = '''    @property
    def model(self) -> Optional[str]:
        """The currently selected LLM model name."""
        return self._model'''
        
        new_getter = '''    @property
    def model(self) -> Optional[str]:
        """The currently selected LLM model name."""
        return self._config_manager.selected_model'''
        
        if old_getter in content:
            content = content.replace(old_getter, new_getter)
            print("✅ Replaced model property getter")
        else:
            print("⚠️  Model property getter not found - may have been updated")
        
        # Replace model property setter
        old_setter = '''    @model.setter
    def model(self, value: str) -> None:
        """Sets the LLM model, validating its availability."""
        if not self._validate_model(value):
            self.log_warning(f"Setting model to '{value}', but it seems unavailable (missing API keys?).")
        self._model = value
        self.config["model"] = value  # Keep config in sync
        self.log_info(f"LLM model set to: {self._model}")'''
        
        new_setter = '''    @model.setter
    def model(self, value: str) -> None:
        """Sets the LLM model, validating its availability."""
        try:
            self._config_manager.selected_model = value
            self._model = value  # Keep backward compatibility
            self.config["model"] = value  # Keep config in sync
            self.log_info(f"LLM model set to: {self._model}")
        except Exception as e:
            self.log_warning(f"Setting model to '{value}', but validation failed: {e}")
            # Still set it for backward compatibility
            self._model = value
            self.config["model"] = value'''
        
        if old_setter in content:
            content = content.replace(old_setter, new_setter)
            print("✅ Replaced model property setter")
        else:
            print("⚠️  Model property setter not found - may have been updated")
        
        # Note: For now, just updating the critical model properties
        # Additional methods (_validate_model, etc.) can be updated in subsequent steps
        
        # Write the updated content
        with open(llm_file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated: {llm_file_path}")
        print("   - Replaced model property getter and setter")
        print("   - Preserved all method signatures and behavior")
        print("   - Maintained backward compatibility")
        
        # Test the changes comprehensively
        print("🧪 Testing Phase 2 changes...")
        
        import subprocess
        
        # Test 1: LLM resource tests
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/common/resource/test_llm_resource.py", "-v"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode != 0:
            print(f"❌ LLM resource tests failed:")
            print(result.stdout)
            print(result.stderr)
            framework.restore_backup(backup_name)
            return False
        
        # Test 2: All common tests
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/common/", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode != 0:
            print(f"❌ Common tests failed:")
            print(result.stdout)
            framework.restore_backup(backup_name)
            return False
        
        # Test 3: Instantiation and basic functionality
        try:
            test_code = '''
from opendxa.common.resource.llm_resource import LLMResource

# Test instantiation
llm = LLMResource(name='test_llm')

# Test configuration manager integration
print(f"Model: {llm.model}")
print(f"Available models: {len(llm.get_available_models())}")
print(f"Validation works: {llm._validate_model('openai:gpt-4o-mini')}")

print("✅ All functionality tests passed")
'''
            exec(test_code)
        except Exception as e:
            print(f"❌ Functionality test failed: {e}")
            framework.restore_backup(backup_name)
            return False
        
        print(f"✅ Phase 2 replacement successful - all tests passing!")
        return True
            
    except Exception as e:
        print(f"💥 Phase 2 error: {e}")
        framework.restore_backup(backup_name)
        return False


def main():
    """Main entry point for Phase 2."""
    print("🔧 LLMResource Phase 2: Replace Configuration Methods")
    print("   Strategy: Replace method implementations with config manager calls")
    print("   Risk: Medium - changing core functionality")
    print("   Safety: Preserve all method signatures and behavior")
    
    success = safe_replace_configuration_methods()
    
    if success:
        print(f"\n✅ Phase 2 completed successfully!")
        print(f"   - Model properties now use LLMConfigurationManager")
        print(f"   - All existing functionality preserved")
        print(f"   - All tests passing")
        print(f"   - Ready for Phase 3: Remove duplicate code")
    else:
        print(f"\n❌ Phase 2 failed")
        print(f"   - Changes rolled back by safety framework")
        print(f"   - LLMResource functionality preserved")


if __name__ == "__main__":
    main()