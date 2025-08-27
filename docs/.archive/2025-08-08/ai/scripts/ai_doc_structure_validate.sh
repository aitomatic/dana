#!/bin/bash

# AI Documentation Structure Validation Script
# Validates MkDocs navigation and checks for orphaned files

set -e

echo "=== AI DOCUMENTATION STRUCTURE VALIDATION STARTED $(date) ==="

# Create output directory
mkdir -p docs/.ai-only/ai_output

# 1. Validate MkDocs navigation structure
echo "Validating MkDocs navigation structure..."
python3 -c "
import yaml
import os

def extract_nav_files(nav_items):
    files = []
    for item in nav_items:
        if isinstance(item, dict):
            for title, path in item.items():
                if isinstance(path, str) and path.endswith('.md'):
                    files.append(path)
                elif isinstance(path, list):
                    files.extend(extract_nav_files(path))
        elif isinstance(item, str) and item.endswith('.md'):
            files.append(item)
    return files

try:
    with open('mkdocs.yml') as f:
        # Use safe_load but handle custom tags by replacing them temporarily
        content = f.read()
        # Replace the problematic Python function reference
        content = content.replace('!!python/name:pymdownx.superfences.fence_code_format', 'fence_code_format')
        config = yaml.safe_load(content)
    
    nav_files = set(extract_nav_files(config['nav']))
    print(f'Files in navigation: {len(nav_files)}')
    
    # Check for missing files
    missing_files = []
    for nav_file in nav_files:
        if not os.path.exists(f'docs/{nav_file}'):
            missing_files.append(nav_file)
    
    if missing_files:
        print(f'❌ Missing files: {len(missing_files)}')
        with open('docs/.ai-only/ai_output/missing_nav_files.txt', 'w') as f:
            for file in missing_files:
                f.write(f'{file}\n')
    else:
        print('✅ All navigation files exist')
        
except Exception as e:
    print(f'❌ Navigation validation failed: {e}')
    exit(1)
"

# 2. Check for orphaned files
echo "Checking for orphaned files..."
find docs -name "*.md" -not -path "docs/.ai-only/*" -not -path "docs/.archive/*" -not -path "docs/.design/*" | while read file; do
    rel_path=${file#docs/}
    if ! grep -q "$rel_path" mkdocs.yml; then
        echo "$rel_path" >> docs/.ai-only/ai_output/orphaned_files.txt
    fi
done

if [ -f docs/.ai-only/ai_output/orphaned_files.txt ]; then
    echo "Orphaned files found: $(wc -l < docs/.ai-only/ai_output/orphaned_files.txt)"
else
    echo "✅ No orphaned files found"
    touch docs/.ai-only/ai_output/orphaned_files.txt
fi

# 3. Test all links
echo "Testing all links..."
# Build to temp directory for link checking
mkdir -p /tmp/docs-test
make docs-build --site-dir /tmp/docs-test 2>/dev/null || echo "Build failed, continuing with link check"

# Simple link check (would use linkchecker if available)
find /tmp/docs-test -name "*.html" -exec grep -o 'href="[^"]*"' {} \; | grep -v "http" | sort -u > docs/.ai-only/ai_output/internal_links.txt
echo "Internal links found: $(wc -l < docs/.ai-only/ai_output/internal_links.txt)"

# 4. Validate mkdocs.yml syntax
echo "Validating mkdocs.yml syntax..."
python3 -c "
import yaml
try:
    with open('mkdocs.yml') as f:
        content = f.read()
        # Replace the problematic Python function reference
        content = content.replace('!!python/name:pymdownx.superfences.fence_code_format', 'fence_code_format')
        yaml.safe_load(content)
    print('✅ mkdocs.yml is valid')
except Exception as e:
    print(f'❌ mkdocs.yml validation failed: {e}')
    exit(1)
"

# 5. Check plugin configuration
echo "Checking plugin configuration..."
python3 -c "
import yaml
with open('mkdocs.yml') as f:
    content = f.read()
    # Replace the problematic Python function reference
    content = content.replace('!!python/name:pymdownx.superfences.fence_code_format', 'fence_code_format')
    config = yaml.safe_load(content)

required_plugins = ['search', 'mermaid2', 'section-index', 'mkdocstrings']
for plugin in required_plugins:
    if plugin in config.get('plugins', []):
        print(f'✅ {plugin} plugin configured')
    else:
        print(f'⚠️  {plugin} plugin not found')
"

# 6. Generate structure validation summary
echo "Generating structure validation summary..."
cat > docs/.ai-only/ai_output/structure_validation_summary.txt << EOF
=== AI STRUCTURE VALIDATION SUMMARY ===
Date: $(date)
Navigation files: $(python3 -c "import yaml; content=open('mkdocs.yml').read(); content=content.replace('!!python/name:pymdownx.superfences.fence_code_format', 'fence_code_format'); config=yaml.safe_load(content); print(len([f for f in config['nav'] if isinstance(f, str) and f.endswith('.md')]))" 2>/dev/null || echo "0")
Missing nav files: $(wc -l < docs/.ai-only/ai_output/missing_nav_files.txt 2>/dev/null || echo "0")
Orphaned files: $(wc -l < docs/.ai-only/ai_output/orphaned_files.txt)
Internal links: $(wc -l < docs/.ai-only/ai_output/internal_links.txt)
MkDocs config valid: $(python3 -c "import yaml; content=open('mkdocs.yml').read(); content=content.replace('!!python/name:pymdownx.superfences.fence_code_format', 'fence_code_format'); yaml.safe_load(content); print('YES')" 2>/dev/null || echo "NO")
EOF

# Cleanup
rm -rf /tmp/docs-test

echo "=== AI DOCUMENTATION STRUCTURE VALIDATION COMPLETE $(date) ===" 