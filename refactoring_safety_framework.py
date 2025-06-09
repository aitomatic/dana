#!/usr/bin/env python3
"""
OpenDXA Refactoring Safety Framework

This module provides comprehensive safety checks and validation tools for refactoring operations.
Ensures no functionality is broken during code restructuring.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class TestResults:
    """Container for test execution results."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    warnings: int = 0
    execution_time: float = 0.0
    failed_tests: List[str] = None
    
    def __post_init__(self):
        if self.failed_tests is None:
            self.failed_tests = []
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100
    
    @property
    def is_regression(self) -> bool:
        """Check if results show regression from baseline."""
        return self.failed > 0


@dataclass
class RefactoringContext:
    """Context for refactoring operation."""
    name: str
    description: str
    target_files: List[str]
    test_modules: List[str]
    backup_files: List[str] = None
    
    def __post_init__(self):
        if self.backup_files is None:
            self.backup_files = []


class SafetyFramework:
    """Main safety framework for refactoring operations."""
    
    def __init__(self, project_root: str = "/Users/ctn/src/aitomatic/opendxa"):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / ".refactoring_backups"
        self.results_dir = self.project_root / ".refactoring_results"
        self.baseline_file = self.results_dir / "baseline_results.json"
        
        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
    
    def establish_baseline(self) -> TestResults:
        """Run full test suite and establish baseline results."""
        print("🔍 Establishing baseline test results...")
        
        start_time = time.time()
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short", "-q", "--disable-warnings"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        execution_time = time.time() - start_time
        
        # Parse pytest output
        output_lines = result.stdout.split('\n')
        test_results = self._parse_pytest_output(output_lines, execution_time)
        
        # Save baseline
        with open(self.baseline_file, 'w') as f:
            json.dump(asdict(test_results), f, indent=2)
        
        print(f"✅ Baseline established: {test_results.passed}/{test_results.total} tests passing")
        print(f"   Success rate: {test_results.success_rate:.1f}%")
        print(f"   Execution time: {test_results.execution_time:.1f}s")
        
        return test_results
    
    def load_baseline(self) -> Optional[TestResults]:
        """Load previously established baseline results."""
        if not self.baseline_file.exists():
            return None
        
        with open(self.baseline_file, 'r') as f:
            data = json.load(f)
            return TestResults(**data)
    
    def create_backup(self, context: RefactoringContext) -> str:
        """Create backup of files before refactoring."""
        timestamp = int(time.time())
        backup_name = f"{context.name}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir()
        
        print(f"📦 Creating backup: {backup_name}")
        
        backed_up_files = []
        for file_path in context.target_files:
            source = self.project_root / file_path
            if source.exists():
                target = backup_path / file_path
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                import shutil
                shutil.copy2(source, target)
                backed_up_files.append(file_path)
                
                print(f"  📋 Backed up: {file_path}")
        
        # Save backup metadata
        metadata = {
            "name": backup_name,
            "context": asdict(context),
            "files": backed_up_files,
            "timestamp": timestamp
        }
        
        with open(backup_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Backup created: {len(backed_up_files)} files")
        return backup_name
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore files from backup."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_name}")
            return False
        
        metadata_file = backup_path / "metadata.json"
        if not metadata_file.exists():
            print(f"❌ Backup metadata not found: {backup_name}")
            return False
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        print(f"🔄 Restoring backup: {backup_name}")
        
        restored_count = 0
        for file_path in metadata["files"]:
            source = backup_path / file_path
            target = self.project_root / file_path
            
            if source.exists():
                import shutil
                shutil.copy2(source, target)
                restored_count += 1
                print(f"  📋 Restored: {file_path}")
        
        print(f"✅ Restored {restored_count} files")
        return True
    
    def run_targeted_tests(self, test_modules: List[str]) -> TestResults:
        """Run specific test modules."""
        if not test_modules:
            test_modules = ["tests/"]
        
        print(f"🧪 Running targeted tests: {', '.join(test_modules)}")
        
        start_time = time.time()
        cmd = ["python", "-m", "pytest"] + test_modules + ["--tb=short", "-q", "--disable-warnings"]
        
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=300
        )
        execution_time = time.time() - start_time
        
        output_lines = result.stdout.split('\n')
        test_results = self._parse_pytest_output(output_lines, execution_time)
        
        if test_results.is_regression:
            print(f"⚠️  Test failures detected: {test_results.failed} failures")
            for test in test_results.failed_tests:
                print(f"   ❌ {test}")
        else:
            print(f"✅ All tests passing: {test_results.passed}/{test_results.total}")
        
        return test_results
    
    def validate_refactoring(self, context: RefactoringContext, baseline: TestResults) -> bool:
        """Validate that refactoring hasn't broken functionality."""
        print(f"🔬 Validating refactoring: {context.name}")
        
        # Run targeted tests
        current_results = self.run_targeted_tests(context.test_modules)
        
        # Compare with baseline
        success_threshold = 99.0  # Allow 1% tolerance for flaky tests
        
        regression_detected = False
        
        # Check for new failures
        if current_results.failed > baseline.failed:
            print(f"❌ New test failures detected:")
            print(f"   Baseline: {baseline.failed} failures")
            print(f"   Current:  {current_results.failed} failures")
            regression_detected = True
        
        # Check success rate
        if current_results.success_rate < success_threshold:
            print(f"❌ Success rate below threshold:")
            print(f"   Current: {current_results.success_rate:.1f}%")
            print(f"   Required: {success_threshold}%")
            regression_detected = True
        
        # Check for significant performance regression
        if current_results.execution_time > baseline.execution_time * 1.5:
            print(f"⚠️  Performance regression detected:")
            print(f"   Baseline: {baseline.execution_time:.1f}s")
            print(f"   Current:  {current_results.execution_time:.1f}s")
            # Note: This is a warning, not a failure
        
        if regression_detected:
            print(f"❌ Validation failed for: {context.name}")
            return False
        else:
            print(f"✅ Validation passed for: {context.name}")
            return True
    
    def _parse_pytest_output(self, output_lines: List[str], execution_time: float) -> TestResults:
        """Parse pytest output to extract test results."""
        results = TestResults(execution_time=execution_time)
        
        # Look for summary line
        for line in output_lines:
            line = line.strip()
            if "failed" in line and "passed" in line:
                # Parse line like: "2 failed, 772 passed, 1 skipped, 109 deselected, 7 xfailed, 1 warning"
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    words = part.split()
                    if len(words) >= 2:
                        try:
                            number = int(words[0])
                            if 'failed' in part:
                                results.failed = number
                            elif 'passed' in part:
                                results.passed = number
                            elif 'skipped' in part:
                                results.skipped = number
                            elif 'xfailed' in part:
                                results.xfailed = number
                            elif 'warning' in part:
                                results.warnings = number
                        except (ValueError, IndexError):
                            continue
                
                results.total = results.passed + results.failed
                break
            elif "passed" in line and "failed" not in line and "=" not in line:
                # Parse line like: "772 passed in 108.14s"
                words = line.split()
                if len(words) > 0:
                    try:
                        if words[0].isdigit():
                            results.passed = int(words[0])
                            results.total = results.passed
                    except (ValueError, IndexError):
                        continue
        
        # Extract failed test names
        in_failures_section = False
        for line in output_lines:
            if "FAILURES" in line:
                in_failures_section = True
                continue
            elif in_failures_section and line.startswith("_"):
                # Extract test name from failure header
                test_name = line.split()[0].strip("_")
                if test_name and "::" in test_name:
                    results.failed_tests.append(test_name)
        
        return results


def safe_refactor_executor_architecture():
    """Example: Safely refactor the executor architecture."""
    framework = SafetyFramework()
    
    # Define refactoring context
    context = RefactoringContext(
        name="executor_architecture_refactor",
        description="Break down large executor files and extract common patterns",
        target_files=[
            "opendxa/dana/sandbox/interpreter/executor/function_executor.py",
            "opendxa/dana/ipv/executor.py",
        ],
        test_modules=[
            "tests/dana/sandbox/interpreter/",
            "tests/dana/ipv/",
        ]
    )
    
    # Establish or load baseline
    baseline = framework.load_baseline()
    if baseline is None:
        baseline = framework.establish_baseline()
    
    # Create backup
    backup_name = framework.create_backup(context)
    
    try:
        print(f"\n🔧 Starting refactoring: {context.description}")
        
        # TODO: Implement actual refactoring steps here
        # This is where the refactoring logic would go
        
        # Validate the refactoring
        if framework.validate_refactoring(context, baseline):
            print(f"✅ Refactoring completed successfully: {context.name}")
            return True
        else:
            print(f"❌ Refactoring validation failed, restoring backup...")
            framework.restore_backup(backup_name)
            return False
            
    except Exception as e:
        print(f"💥 Refactoring error: {e}")
        print(f"🔄 Restoring backup...")
        framework.restore_backup(backup_name)
        return False


if __name__ == "__main__":
    # Example usage
    framework = SafetyFramework()
    
    # Establish baseline if it doesn't exist
    baseline = framework.load_baseline()
    if baseline is None:
        print("📊 No baseline found, establishing one...")
        baseline = framework.establish_baseline()
    else:
        print(f"📊 Using existing baseline: {baseline.passed}/{baseline.total} tests passing")
    
    print("\n🛡️  Safety framework ready for refactoring operations!")
    print(f"   Baseline: {baseline.success_rate:.1f}% success rate")
    print(f"   Backup directory: {framework.backup_dir}")
    print(f"   Results directory: {framework.results_dir}")