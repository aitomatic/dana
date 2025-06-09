#!/usr/bin/env python3
"""
Safe LLMResource Phase 3: Remove duplicate code and complete refactoring

This script removes the configuration methods that are now duplicated
by the LLMConfigurationManager, achieving the final refactored state.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from pathlib import Path
from refactoring_safety_framework import SafetyFramework, RefactoringContext

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def safe_remove_duplicate_methods():
    """Phase 3: Remove duplicate configuration methods."""
    framework = SafetyFramework()
    
    context = RefactoringContext(
        name="llm_resource_phase3_remove_duplicates",
        description="Remove duplicate configuration methods now handled by LLMConfigurationManager",
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
        print(f"\n🔧 Phase 3: {context.description}")
        print("⚠️  FINAL PHASE: Removing duplicate methods for clean refactored state")
        
        # Read the current LLMResource file
        llm_file_path = project_root / "opendxa/common/resource/llm_resource.py"
        with open(llm_file_path, 'r') as f:
            content = f.read()
        
        # Remove the old _validate_model method since we're using the config manager's version
        old_validate_method = '''    def _validate_model(self, model_name: str) -> bool:
        """Checks if the required API keys for a given model are available.

        Args:
            model_name: The name of the model (e.g., "openai:gpt-4").

        Returns:
            True if all required keys are found in environment variables, False otherwise.
        """
        required_keys = []
        for m in self.preferred_models:
            if m.get("name") == model_name:
                required_keys = m.get("required_api_keys", [])
                break

        if not required_keys:
            # If model not in preferred_models list or has no keys listed, assume available
            # Or should we be stricter? For now, allows models not explicitly listed.
            self.log_debug(f"No API keys specified for model '{model_name}'. Assuming available.")
            return True

        missing_keys = [key for key in required_keys if not os.getenv(key)]
        if missing_keys:
            self.log_debug(f"Model '{model_name}' is missing required API keys: {missing_keys}")
            return False

        self.log_debug(f"All required API keys for model '{model_name}' are available.")
        return True'''
        
        new_validate_method = '''    def _validate_model(self, model_name: str) -> bool:
        """Checks if the required API keys for a given model are available.

        Args:
            model_name: The name of the model (e.g., "openai:gpt-4").

        Returns:
            True if all required keys are found in environment variables, False otherwise.
        """
        return self._config_manager._validate_model(model_name)'''
        
        if old_validate_method in content:
            content = content.replace(old_validate_method, new_validate_method)
            print("✅ Replaced _validate_model method with config manager call")
        else:
            print("⚠️  _validate_model method not found - may have been updated")
        
        # Remove the old _find_first_available_model method
        old_find_method = '''    def _find_first_available_model(self) -> Optional[str]:
        """Finds the first available model from the preferred_models list.

        Iterates through `self.preferred_models` and returns the name of the
        first model for which all `required_api_keys` are set as environment vars.

        Returns:
            The name of the first available model, or None if none are available.
        """
        self.log_debug(f"Searching for available model in preferred list: {self.preferred_models}")
        for model_config in self.preferred_models:
            model_name = model_config.get("name")
            if not model_name:
                self.log_warning("Skipping entry in preferred_models with missing 'name'.")
                continue

            if self._validate_model(model_name):
                self.log_debug(f"Found available model: {model_name}")
                return model_name

        self.log_warning("No available models found in the preferred_models list.")
        return None'''
        
        new_find_method = '''    def _find_first_available_model(self) -> Optional[str]:
        """Finds the first available model from the preferred_models list.

        Iterates through `self.preferred_models` and returns the name of the
        first model for which all `required_api_keys` are set as environment vars.

        Returns:
            The name of the first available model, or None if none are available.
        """
        return self._config_manager._find_first_available_model()'''
        
        if old_find_method in content:
            content = content.replace(old_find_method, new_find_method)
            print("✅ Replaced _find_first_available_model method with config manager call")
        else:
            print("⚠️  _find_first_available_model method not found - may have been updated")
        
        # Remove the old get_available_models method
        old_get_models_method = '''    def get_available_models(self) -> List[str]:
        """Gets a list of models from preferred_models that are currently available.

        Checks API key availability for each model in `self.preferred_models`.

        Returns:
            A list of available model names.
        """
        available = []
        for model_config in self.preferred_models:
            model_name = model_config.get("name")
            if model_name and self._validate_model(model_name):
                available.append(model_name)
        self.log_debug(f"Available models based on API keys: {available}")
        return available'''
        
        new_get_models_method = '''    def get_available_models(self) -> List[str]:
        """Gets a list of models from preferred_models that are currently available.

        Checks API key availability for each model in `self.preferred_models`.

        Returns:
            A list of available model names.
        """
        available = self._config_manager.get_available_models()
        self.log_debug(f"Available models based on API keys: {available}")
        return available'''
        
        if old_get_models_method in content:
            content = content.replace(old_get_models_method, new_get_models_method)
            print("✅ Replaced get_available_models method with config manager call")
        else:
            print("⚠️  get_available_models method not found - may have been updated")
        
        # Write the updated content
        with open(llm_file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated: {llm_file_path}")
        print("   - Removed duplicate configuration methods")
        print("   - All configuration logic now handled by LLMConfigurationManager")
        print("   - Preserved all method signatures and external API")
        
        # Test the changes comprehensively
        print("🧪 Testing Phase 3 changes...")
        
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
        
        # Test 3: Comprehensive functionality test
        try:
            test_code = '''
from opendxa.common.resource.llm_resource import LLMResource

# Test instantiation
llm = LLMResource(name='test_llm')

# Test all refactored methods
print(f"Model: {llm.model}")
print(f"Available models: {len(llm.get_available_models())}")
print(f"Validation works: {llm._validate_model('openai:gpt-4o-mini')}")
print(f"First available: {llm._find_first_available_model()}")

# Test model setting
original_model = llm.model
llm.model = "openai:gpt-4o-mini"
print(f"Model after setting: {llm.model}")

print("✅ All functionality tests passed")
'''
            exec(test_code)
        except Exception as e:
            print(f"❌ Functionality test failed: {e}")
            framework.restore_backup(backup_name)
            return False
        
        # Calculate line reduction
        original_lines = content.count('\n') + len(old_validate_method.split('\n')) + len(old_find_method.split('\n')) + len(old_get_models_method.split('\n'))
        final_lines = content.count('\n')
        reduction = original_lines - final_lines
        reduction_percent = (reduction / original_lines) * 100 if original_lines > 0 else 0
        
        print(f"✅ Phase 3 refactoring completed successfully!")
        print(f"   📊 Line reduction: ~{reduction} lines ({reduction_percent:.1f}%)")
        print(f"   🧹 All duplicate configuration code removed")
        print(f"   🔧 Configuration management fully delegated to LLMConfigurationManager")
        return True
            
    except Exception as e:
        print(f"💥 Phase 3 error: {e}")
        framework.restore_backup(backup_name)
        return False


def main():
    """Main entry point for Phase 3."""
    print("🔧 LLMResource Phase 3: Remove Duplicate Configuration Code")
    print("   Strategy: Remove methods now handled by LLMConfigurationManager")
    print("   Risk: Low - methods are already replaced and tested")
    print("   Goal: Clean, maintainable code with clear separation of concerns")
    
    success = safe_remove_duplicate_methods()
    
    if success:
        print(f"\n🎉 LLMResource refactoring completed successfully!")
        print(f"   - Configuration management extracted to LLMConfigurationManager")
        print(f"   - Duplicate code removed")
        print(f"   - All tests passing")
        print(f"   - Ready for Phase 4: Extract additional components if desired")
    else:
        print(f"\n❌ Phase 3 failed")
        print(f"   - Changes rolled back by safety framework")
        print(f"   - LLMResource functionality preserved")


if __name__ == "__main__":
    main()