# PyPI Deployment Guide

Complete guide for deploying dana-agent packages to PyPI using automated CI/CD pipeline.

## 🎯 Overview

This repository includes an automated PyPI release pipeline that:
- ✅ **Tests**: Runs 1700+ tests with security scanning
- 📦 **Builds**: Creates wheel and source distributions with UI components
- 🚀 **Publishes**: Deploys to PyPI automatically
- 🏷️ **Releases**: Creates GitHub releases with artifacts

**Trigger**: Push to `release/pypi` branch

## ⚡ Quick Start

### 1. Setup PyPI Access

1. **Get PyPI API Token**
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/token/)
   - Click "Add API token" → "Entire account" scope
   - Copy token (starts with `pypi-`)

2. **Add GitHub Secret**
   - Go to Repository → **Settings** → **Secrets and Variables** → **Actions**
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token

### 2. Deploy Package

```bash
# Bump version and deploy
./bin/bump-version.py patch --commit
# Output:
# Current version: 0.25.7.19
# New version: 0.25.8.0
# ✅ Updated version to 0.25.8.0
# ✅ Committed version bump
# 🎉 Version updated to 0.25.8.0

git push origin release/pypi

# Monitor deployment
# GitHub → Actions tab → "PyPI Release"
```

## 📦 Release Types

```bash
# Build release: 0.25.7.19 → 0.25.7.20
./bin/bump-version.py build --commit

# Patch release: 0.25.7.19 → 0.25.8.0
./bin/bump-version.py patch --commit

# Minor release: 0.25.7.19 → 0.26.0.0  
./bin/bump-version.py minor --commit

# Major release: 0.25.7.19 → 1.0.0.0
./bin/bump-version.py major --commit

# Push to deploy
git push origin release/pypi
```

## 🔧 Pipeline Overview

The automated pipeline runs three parallel jobs:

### Job 1: Test & Build (Primary)
- **Node.js 23.9.0** installation for UI builds
- **1700+ tests** across Python components
- **UI build** (React + Vite) if `dana/contrib/ui` exists
- **Package build** with wheel and source distributions
- **Artifact upload** for downstream jobs

### Job 2: Security Scan (Parallel)
- **Dependency vulnerabilities** (Safety)
- **Code security issues** (Bandit) 
- **Secret detection** (basic patterns)
- **Non-blocking** - warnings only

### Job 3: PyPI Publish (Sequential)
- **Downloads** build artifacts from Job 1
- **Publishes** to PyPI using official action
- **Creates** GitHub release (commented out by default)

## 🧪 Testing Pipeline Locally

### Option 1: Test with `act` (GitHub Actions locally)

```bash
# Setup act (install if needed)
# macOS: brew install act
# Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Test security scan only
source .venv/bin/activate
act -j security-scan

# Test build process only
act -j test-and-build

# Test complete workflow (except publish)
act push -W .github/workflows/pypi-release.yml --secret-file .secrets.example
```

### Option 2: Test Individual Components

```bash
# Test package build locally
source .venv/bin/activate
uv sync --all-extras
uv add --group dev build twine

# Clean and build
rm -rf dist/ build/ *.egg-info/
python -m build
python -m twine check dist/*

# Test UI build (if exists)
if [ -d "dana/contrib/ui" ]; then
  cd dana/contrib/ui && npm i && npm run build && cd ../../..
fi
```

## 🚨 Troubleshooting

### Common Issues

**"File already exists" error**
- PyPI doesn't allow re-uploading same version
- Bump version: `./bin/bump-version.py build --commit` (quickest) or `./bin/bump-version.py patch --commit`

**Node.js version conflicts**
- Pipeline uses Node.js 23.9.0 for Vite compatibility
- Local development may use different version

**Permission errors in `act`**
- Use `catthehacker/ubuntu:runner-latest` image
- Manual uv installation avoids caching issues

**Test failures**
- All 1700+ tests must pass before deployment
- Fix failing tests before attempting release

### Debug Commands

```bash
# Check current version
grep 'version =' pyproject.toml

# Verify package contents
python -m build
tar -tzf dist/dana_agent-*.tar.gz | head -20

# Test local upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

## 📋 Required Files

The pipeline expects these files to exist:

- `pyproject.toml` - Package configuration with version
- `README.md` - Package description
- `dana/` - Main Python package
- `dana/contrib/ui/` - UI components (optional)
- `.github/workflows/pypi-release.yml` - Pipeline definition

## 🔒 Security Notes

- **API tokens** are stored as GitHub secrets
- **Attestations** are generated for package integrity
- **Security scanning** runs on every deployment
- **Trusted Publishing** recommended (see warnings in pipeline)

## 📈 Monitoring

- **GitHub Actions**: Repository → Actions tab
- **PyPI**: [dana-agent package page](https://pypi.org/project/dana-agent/)
- **Downloads**: Track usage statistics on PyPI
- **Issues**: Monitor for deployment failures via email/notifications

---

**Need Help?** Check the workflow logs in GitHub Actions for detailed error messages. 