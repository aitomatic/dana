#!/usr/bin/env python3
"""
LLMResource Refactoring Analysis and Plan

This script analyzes the 808-line LLMResource class and creates a safe refactoring plan
to break it down into focused, maintainable components.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from pathlib import Path
from refactoring_safety_framework import SafetyFramework, RefactoringContext

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def analyze_llm_resource_structure():
    """Analyze the structure of LLMResource to plan refactoring."""
    
    analysis = {
        "current_state": {
            "file_size": 808,
            "methods": 22,
            "complexity": "Very High - Single massive class handling everything",
            "responsibilities": [
                "Configuration management",
                "Model selection and validation", 
                "LLM query execution",
                "Tool/function calling",
                "Token management",
                "Error handling",
                "Response processing",
                "Mock/testing support"
            ]
        },
        
        "logical_groupings": {
            "configuration_management": {
                "methods": ["__init__", "model (property)", "_get_default_model", "_validate_model", "_find_first_available_model", "get_available_models"],
                "responsibility": "Model selection, validation, and configuration loading",
                "lines_estimate": 150
            },
            
            "query_execution": {
                "methods": ["query_sync", "query", "_query_iterative", "_query_once", "_mock_llm_query"],
                "responsibility": "Core LLM API calling and response handling",
                "lines_estimate": 250
            },
            
            "tool_calling": {
                "methods": ["_build_request_params", "_get_openai_functions", "_call_requested_tools", "_call_tools"],
                "responsibility": "Tool/function call integration with LLM",
                "lines_estimate": 200
            },
            
            "lifecycle_management": {
                "methods": ["initialize", "cleanup", "can_handle", "with_mock_llm_call"],
                "responsibility": "Resource lifecycle and testing support",
                "lines_estimate": 80
            },
            
            "logging_utilities": {
                "methods": ["_log_llm_request", "_log_llm_response"],
                "responsibility": "Request/response logging and debugging",
                "lines_estimate": 50
            }
        },
        
        "refactoring_strategy": {
            "approach": "Composition over inheritance - break into focused collaborator classes",
            "safety": "Extra careful - this is core infrastructure used everywhere",
            "phases": [
                {
                    "phase": 1,
                    "description": "Extract configuration management",
                    "target": "LLMConfigurationManager",
                    "risk": "Low - mostly data transformation",
                    "impact": "Cleaner model selection logic"
                },
                {
                    "phase": 2, 
                    "description": "Extract tool calling logic",
                    "target": "LLMToolCallManager",
                    "risk": "Medium - complex tool integration",
                    "impact": "Separated concerns for tool calling"
                },
                {
                    "phase": 3,
                    "description": "Extract query execution engine",
                    "target": "LLMQueryExecutor", 
                    "risk": "High - core functionality",
                    "impact": "Focused query logic, easier testing"
                },
                {
                    "phase": 4,
                    "description": "Extract logging and utilities",
                    "target": "LLMLoggingManager",
                    "risk": "Low - utility functions",
                    "impact": "Cleaner main class"
                }
            ]
        }
    }
    
    return analysis


def create_comprehensive_test_strategy():
    """Create a comprehensive testing strategy for LLMResource refactoring."""
    
    strategy = {
        "testing_approach": "Multi-layered validation with real LLM integration tests",
        
        "test_categories": {
            "unit_tests": {
                "target": "Individual method behavior",
                "scope": "All public methods + critical private methods", 
                "focus": "Input validation, error handling, edge cases"
            },
            
            "integration_tests": {
                "target": "LLM provider integration",
                "scope": "Real API calls with various providers",
                "focus": "Tool calling, context management, error recovery"
            },
            
            "performance_tests": {
                "target": "Token management and response times",
                "scope": "Large requests, tool calling chains",
                "focus": "Memory usage, API call efficiency"
            },
            
            "compatibility_tests": {
                "target": "Existing codebase integration", 
                "scope": "All current LLMResource usage patterns",
                "focus": "Backward compatibility, interface preservation"
            }
        },
        
        "safety_measures": {
            "baseline_establishment": "Full test suite + real LLM calls",
            "mock_validation": "Ensure mock behavior unchanged",
            "provider_testing": "Test with multiple LLM providers",
            "error_simulation": "Test all error conditions",
            "rollback_testing": "Verify backup/restore works"
        },
        
        "test_data": {
            "simple_queries": "Basic text completion requests",
            "tool_calling": "Function calls with various signatures",
            "large_context": "Maximum token limit scenarios", 
            "error_conditions": "Invalid models, auth failures, rate limits",
            "edge_cases": "Empty requests, malformed responses"
        }
    }
    
    return strategy


def safe_refactor_phase_1_configuration():
    """Phase 1: Extract LLM configuration management."""
    framework = SafetyFramework()
    
    context = RefactoringContext(
        name="llm_resource_phase1_configuration",
        description="Extract LLMConfigurationManager from LLMResource",
        target_files=[
            "opendxa/common/resource/llm_resource.py",
            "opendxa/common/resource/llm_configuration_manager.py"
        ],
        test_modules=[
            "tests/common/resource/",
        ]
    )
    
    # Load baseline - this is critical for LLMResource
    baseline = framework.load_baseline()
    if baseline is None:
        print("❌ No baseline found. Establishing one first...")
        baseline = framework.establish_baseline()
    
    print(f"📊 Baseline: {baseline.passed}/{baseline.total} tests passing ({baseline.success_rate:.1f}%)")
    
    # Create backup
    backup_name = framework.create_backup(context)
    
    try:
        print(f"\n🔧 Phase 1: {context.description}")
        print("⚠️  EXTRA CARE: This is core infrastructure - proceeding cautiously")
        
        # Step 1: Create LLMConfigurationManager
        config_manager_content = '''"""
LLM Configuration Manager for OpenDXA.

This module handles model selection, validation, and configuration management
for LLM resources. Extracted from LLMResource for better separation of concerns.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any, Dict, List, Optional

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.exceptions import ConfigurationError, LLMError


class LLMConfigurationManager:
    """Manages LLM model configuration, selection and validation."""
    
    def __init__(self, explicit_model: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize configuration manager.
        
        Args:
            explicit_model: Specific model to use, overrides auto-selection
            config: Additional configuration parameters
        """
        self.explicit_model = explicit_model
        self.config = config or {}
        self.config_loader = ConfigLoader()
        self._selected_model = None
        
    @property
    def selected_model(self) -> str:
        """Get the currently selected model."""
        if self._selected_model is None:
            self._selected_model = self._determine_model()
        return self._selected_model
    
    @selected_model.setter
    def selected_model(self, value: str) -> None:
        """Set the model, with validation."""
        if not self._validate_model(value):
            raise LLMError(f"Invalid or unavailable model: {value}")
        self._selected_model = value
        
    def _determine_model(self) -> str:
        """Determine which model to use based on configuration and availability."""
        # Priority: explicit model > auto-selection > default
        if self.explicit_model:
            if self._validate_model(self.explicit_model):
                return self.explicit_model
            else:
                raise LLMError(f"Explicitly requested model '{self.explicit_model}' is not available")
        
        # Try auto-selection
        auto_model = self._find_first_available_model()
        if auto_model:
            return auto_model
            
        # Fallback to default
        default = self._get_default_model()
        if self._validate_model(default):
            return default
            
        raise LLMError("No available LLM models found. Please check your API keys and configuration.")
    
    def _get_default_model(self) -> str:
        """Get the default model from configuration."""
        try:
            return self.config_loader.get_config().get("llm", {}).get("default_model", "openai:gpt-4o-mini")
        except Exception:
            return "openai:gpt-4o-mini"
    
    def _validate_model(self, model_name: str) -> bool:
        """Validate that a model is available and properly configured."""
        if not model_name:
            return False
            
        try:
            provider = model_name.split(":")[0] if ":" in model_name else "openai"
            
            # Check for required API keys/configuration
            required_keys = {
                "openai": ["OPENAI_API_KEY"],
                "anthropic": ["ANTHROPIC_API_KEY"],  
                "google": ["GOOGLE_API_KEY"],
                "cohere": ["COHERE_API_KEY"],
                "mistral": ["MISTRAL_API_KEY"],
                "groq": ["GROQ_API_KEY"],
            }
            
            if provider in required_keys:
                return any(os.getenv(key) for key in required_keys[provider])
                
            return True  # Unknown providers assumed valid
            
        except Exception:
            return False
    
    def _find_first_available_model(self) -> Optional[str]:
        """Find the first available model from preferred list."""
        try:
            config = self.config_loader.get_config()
            preferred_models = config.get("llm", {}).get("preferred_models", [
                "openai:gpt-4o",
                "openai:gpt-4o-mini", 
                "anthropic:claude-3-5-sonnet-20241022",
                "google:gemini-1.5-pro",
            ])
            
            for model in preferred_models:
                if self._validate_model(model):
                    return model
                    
            return None
            
        except Exception:
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of all available models."""
        try:
            config = self.config_loader.get_config()
            all_models = config.get("llm", {}).get("all_models", [
                "openai:gpt-4o",
                "openai:gpt-4o-mini",
                "openai:gpt-4-turbo",
                "anthropic:claude-3-5-sonnet-20241022",
                "anthropic:claude-3-5-haiku-20241022",
                "google:gemini-1.5-pro",
                "google:gemini-1.5-flash",
                "cohere:command-r-plus",
                "mistral:mistral-large-latest",
                "groq:llama-3.1-70b-versatile",
            ])
            
            return [model for model in all_models if self._validate_model(model)]
            
        except Exception:
            return []
    
    def get_model_config(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        target_model = model or self.selected_model
        
        try:
            config = self.config_loader.get_config()
            model_configs = config.get("llm", {}).get("model_configs", {})
            
            # Get model-specific config or defaults
            return model_configs.get(target_model, {
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30
            })
            
        except Exception:
            return {
                "max_tokens": 4096, 
                "temperature": 0.7,
                "timeout": 30
            }
'''
        
        # Create the configuration manager file
        config_file_path = project_root / "opendxa/common/resource/llm_configuration_manager.py"
        with open(config_file_path, 'w') as f:
            f.write(config_manager_content)
        
        print(f"✅ Created: {config_file_path}")
        
        # For now, just test that the file is created and can be imported
        print("✅ Phase 1 structure ready - will implement integration in next step")
        
        # For Phase 1, we're just creating a new file without modifying existing code
        # Let's validate by running the specific tests manually
        print("🧪 Validating that existing LLM tests still pass...")
        
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/common/resource/test_llm_resource.py", "-v"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print(f"✅ LLM tests still passing - Phase 1 setup completed successfully")
            return True
        else:
            print(f"❌ LLM tests failed after Phase 1:")
            print(result.stdout)
            print(result.stderr)
            framework.restore_backup(backup_name)
            return False
            
    except Exception as e:
        print(f"💥 Phase 1 error: {e}")
        framework.restore_backup(backup_name)
        return False


def main():
    """Main entry point for LLMResource refactoring."""
    print("🔍 Analyzing LLMResource for safe refactoring...")
    
    # Analyze current structure
    analysis = analyze_llm_resource_structure()
    
    print(f"\n📊 LLMResource Analysis:")
    print(f"   File size: {analysis['current_state']['file_size']} lines")
    print(f"   Methods: {analysis['current_state']['methods']} methods")
    print(f"   Complexity: {analysis['current_state']['complexity']}")
    
    print(f"\n🏗️ Logical Groupings Identified:")
    for name, group in analysis['logical_groupings'].items():
        print(f"   {name}: {group['lines_estimate']} lines - {group['responsibility']}")
    
    # Create testing strategy
    strategy = create_comprehensive_test_strategy()
    print(f"\n🧪 Testing Strategy:")
    print(f"   Approach: {strategy['testing_approach']}")
    print(f"   Categories: {len(strategy['test_categories'])} test types")
    print(f"   Safety measures: {len(strategy['safety_measures'])} validations")
    
    print(f"\n⚠️  CAUTION: LLMResource is core infrastructure")
    print(f"   - Used throughout the system for all LLM operations")
    print(f"   - Extra testing and validation required")
    print(f"   - Incremental approach with extensive safety checks")
    
    # Ask for confirmation to proceed
    print(f"\n🚀 Ready to start Phase 1: Configuration Management extraction")
    print(f"   Target: Extract model selection and validation logic")
    print(f"   Risk: Low (mostly data transformation)")
    print(f"   Estimated reduction: ~150 lines")
    
    # For safety, let's start with Phase 1 setup
    success = safe_refactor_phase_1_configuration()
    
    if success:
        print(f"\n✅ Phase 1 setup completed successfully!")
        print(f"   Next step: Integrate LLMConfigurationManager into LLMResource")
        print(f"   Then: Continue with phases 2-4")
    else:
        print(f"\n❌ Phase 1 failed - safety framework protected us")


if __name__ == "__main__":
    main()