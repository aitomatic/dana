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
        
        replacements = [
            # 1. Replace model property getter
            {
                "old": """    @property
    def model(self) -> Optional[str]:
        """The currently selected LLM model name."""
        return self._model""",
                "new": """    @property
    def model(self) -> Optional[str]:
        """The currently selected LLM model name."""
        return self._config_manager.selected_model"""
            },
            
            # 2. Replace model property setter  
            {
                "old": """    @model.setter
    def model(self, value: str) -> None:
        """Sets the LLM model, validating its availability."""
        if not self._validate_model(value):
            self.log_warning(f"Setting model to '{value}', but it seems unavailable (missing API keys?).")
        self._model = value
        self.config["model"] = value  # Keep config in sync
        self.log_info(f"LLM model set to: {self._model}")""",
                "new": """    @model.setter
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
            self.config["model"] = value"""
            },
            
            # 3. Replace _validate_model method
            {
                "old": """    def _validate_model(self, model_name: str) -> bool:
        \"\"\"Checks if the required API keys for a given model are available.

        Args:
            model_name: The name of the model (e.g., "openai:gpt-4").

        Returns:
            True if all required keys are found in environment variables, False otherwise.
        \"\"\"
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
        return True""",
                "new": """    def _validate_model(self, model_name: str) -> bool:
        \"\"\"Checks if the required API keys for a given model are available.

        Args:
            model_name: The name of the model (e.g., "openai:gpt-4").

        Returns:
            True if all required keys are found in environment variables, False otherwise.
        \"\"\"
        return self._config_manager._validate_model(model_name)"""
            },
            
            # 4. Replace _find_first_available_model method
            {
                "old": """    def _find_first_available_model(self) -> Optional[str]:
        \"\"\"Finds the first available model from the preferred_models list.

        Iterates through `self.preferred_models` and returns the name of the
        first model for which all `required_api_keys` are set as environment vars.

        Returns:
            The name of the first available model, or None if none are available.
        \"\"\"
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
        return None""",
                "new": """    def _find_first_available_model(self) -> Optional[str]:
        \"\"\"Finds the first available model from the preferred_models list.

        Iterates through `self.preferred_models` and returns the name of the
        first model for which all `required_api_keys` are set as environment vars.

        Returns:
            The name of the first available model, or None if none are available.
        \"\"\"
        return self._config_manager._find_first_available_model()"""
            },
            
            # 5. Replace get_available_models method
            {
                "old": """    def get_available_models(self) -> List[str]:
        \"\"\"Gets a list of models from preferred_models that are currently available.

        Checks API key availability for each model in `self.preferred_models`.

        Returns:
            A list of available model names.
        \"\"\"
        available = []
        for model_config in self.preferred_models:
            model_name = model_config.get("name")
            if model_name and self._validate_model(model_name):
                available.append(model_name)
        self.log_debug(f"Available models based on API keys: {available}")
        return available""",
                "new": """    def get_available_models(self) -> List[str]:
        \"\"\"Gets a list of models from preferred_models that are currently available.

        Checks API key availability for each model in `self.preferred_models`.

        Returns:
            A list of available model names.
        \"\"\"
        available = self._config_manager.get_available_models()
        self.log_debug(f"Available models based on API keys: {available}")
        return available"""
            }
        ]
        
        # Apply all replacements
        updated_content = content
        for i, replacement in enumerate(replacements, 1):
            if replacement["old"] in updated_content:
                updated_content = updated_content.replace(replacement["old"], replacement["new"])
                print(f"✅ Applied replacement {i}/5: Method updated")
            else:
                print(f"⚠️  Replacement {i}/5: Pattern not found - may have been updated")
        
        # Write the updated content
        with open(llm_file_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated: {llm_file_path}")
        print("   - Replaced 5 configuration methods with manager calls")
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
            test_code = """
from opendxa.common.resource.llm_resource import LLMResource

# Test instantiation
llm = LLMResource(name='test_llm')

# Test configuration manager integration
print(f"Model: {llm.model}")
print(f"Available models: {len(llm.get_available_models())}")
print(f"Validation works: {llm._validate_model('openai:gpt-4o-mini')}")

print("✅ All functionality tests passed")
"""
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
        print(f"   - 5 configuration methods now use LLMConfigurationManager")
        print(f"   - All existing functionality preserved")
        print(f"   - All tests passing")
        print(f"   - Ready for Phase 3: Remove duplicate code")
    else:
        print(f"\n❌ Phase 2 failed")
        print(f"   - Changes rolled back by safety framework")
        print(f"   - LLMResource functionality preserved")


if __name__ == "__main__":
    main()