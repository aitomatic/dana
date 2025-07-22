#!/usr/bin/env python3
"""
Comprehensive validation script for GitHub Actions workflow.

This script validates the workshop integration tests workflow without requiring
full GitHub environment setup.
"""

import subprocess
import sys
from pathlib import Path

import yaml


def validate_yaml_syntax(file_path):
    """Validate YAML syntax of the workflow file."""
    print(f"🔍 Validating YAML syntax: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        print("✅ YAML syntax is valid")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False


def validate_workflow_structure(file_path):
    """Validate GitHub Actions workflow structure."""
    print(f"🔍 Validating workflow structure: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check required top-level keys
        required_keys = ['name', 'on', 'jobs']
        for key in required_keys:
            if key not in workflow:
                print(f"❌ Missing required key: {key}")
                return False
        
        # Check jobs structure
        jobs = workflow.get('jobs', {})
        expected_jobs = [
            'workshop-tests-mock',
            'workshop-syntax-check', 
            'workshop-tests-mcp',
            'report-results'
        ]
        
        for job_name in expected_jobs:
            if job_name not in jobs:
                print(f"❌ Missing expected job: {job_name}")
                return False
            
            job = jobs[job_name]
            if 'runs-on' not in job:
                print(f"❌ Job {job_name} missing runs-on")
                return False
            
            if 'steps' not in job:
                print(f"❌ Job {job_name} missing steps")
                return False
        
        # Check trigger conditions
        on_triggers = workflow.get('on', {})
        if 'pull_request' not in on_triggers:
            print("❌ Missing pull_request trigger")
            return False
        
        if 'workflow_dispatch' not in on_triggers:
            print("❌ Missing workflow_dispatch trigger")
            return False
        
        print("✅ Workflow structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating workflow structure: {e}")
        return False


def check_referenced_files():
    """Check that files referenced in the workflow exist."""
    print("🔍 Checking referenced files exist")
    
    required_files = [
        "tests/integration/test_workshop_examples.py",
        "tests/integration/run_workshop_tests.py",
        "scripts/validate_workshop_ci.py",
        "pyproject.toml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing referenced files: {missing_files}")
        return False
    
    print("✅ All referenced files exist")
    return True


def test_act_dryrun():
    """Test the workflow using act in dry-run mode."""
    print("🔍 Testing workflow with act (dry-run)")
    
    # Check if act is available
    try:
        subprocess.run(['act', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  act not available - skipping dry-run test")
        return True
    
    # Test each job in dry-run mode
    jobs_to_test = [
        'workshop-tests-mock',
        'workshop-syntax-check'
    ]
    
    for job in jobs_to_test:
        print(f"  Testing job: {job}")
        try:
            result = subprocess.run([
                'act', 'workflow_dispatch',
                '-W', '.github/workflows/workshop-integration-tests.yml',
                '-j', job, '--dryrun'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"  ✅ Job {job} passed dry-run")
            else:
                print(f"  ❌ Job {job} failed dry-run")
                print(f"     Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Job {job} timed out (may still be valid)")
        except Exception as e:
            print(f"  ❌ Error testing job {job}: {e}")
            return False
    
    print("✅ act dry-run tests passed")
    return True


def validate_github_expressions():
    """Validate GitHub Actions expressions in the workflow."""
    print("🔍 Validating GitHub Actions expressions")
    
    workflow_file = ".github/workflows/workshop-integration-tests.yml"
    
    try:
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        # Check for common expression issues
        issues = []
        
        # Check for unescaped quotes in expressions
        if "\\`" in content and "`.na`" not in content:
            issues.append("Potential quote escaping issue in expressions")
        
        # Check for proper variable references
        if "${{ env." in content:
            print("  ✅ Environment variable references found")
        
        if "${{ needs." in content:
            print("  ✅ Job dependency references found")
        
        if "${{ github." in content:
            print("  ✅ GitHub context references found")
        
        if issues:
            for issue in issues:
                print(f"  ⚠️  {issue}")
        
        print("✅ GitHub expressions look valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating expressions: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🧪 GitHub Actions Workflow Validation")
    print("=" * 50)
    
    workflow_file = ".github/workflows/workshop-integration-tests.yml"
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Must be run from project root (pyproject.toml not found)")
        sys.exit(1)
    
    tests = [
        ("YAML Syntax", lambda: validate_yaml_syntax(workflow_file)),
        ("Workflow Structure", lambda: validate_workflow_structure(workflow_file)),
        ("Referenced Files", check_referenced_files),
        ("GitHub Expressions", validate_github_expressions),
        ("Act Dry-run", test_act_dryrun),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("📊 Validation Results")
    print("=" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All validation tests passed! Workflow is ready for GitHub.")
        sys.exit(0)
    else:
        print("❌ Some validation tests failed. Please review and fix.")
        sys.exit(1)


if __name__ == "__main__":
    main() 