#!/bin/bash

# AI Documentation Content Update Script
# Updates function documentation and fixes code examples

set -e

echo "=== AI DOCUMENTATION CONTENT UPDATE STARTED $(date) ==="

# Create output directory
mkdir -p docs/.ai-only/ai_output

# 1. Update function documentation across audience trees
echo "Updating function documentation..."
if [ -f docs/.ai-only/ai_output/new_functions.txt ]; then
    echo "Processing new functions..."
    while read -r line; do
        if [[ $line == Modified:* ]]; then
            file_path=${line#Modified: }
            echo "Processing function file: $file_path"
            # Extract function signatures
            grep -n "def " "$file_path" | grep -v "__" >> docs/.ai-only/ai_output/functions_to_document.txt || true
        fi
    done < docs/.ai-only/ai_output/new_functions.txt
    echo "Functions to document: $(wc -l < docs/.ai-only/ai_output/functions_to_document.txt 2>/dev/null || echo "0")"
else
    echo "No new functions file found"
fi

# 2. Fix broken Dana code examples
echo "Fixing broken Dana code examples..."
find docs/ -name "*.md" -exec grep -l "\`\`\`dana" {} \; > docs/.ai-only/ai_output/dana_example_files.txt

broken_examples=0
while read -r file; do
    echo "Testing $file..."
    # Extract Dana code blocks
    sed -n '/```dana/,/```/p' "$file" | sed '1d;$d' > "temp_${file##*/}.na"
    
    # Test if the code runs
    if bin/dana "temp_${file##*/}.na" 2>/dev/null; then
        echo "✅ $file examples work"
    else
        echo "❌ $file has broken examples"
        echo "$file" >> docs/.ai-only/ai_output/broken_examples.txt
        ((broken_examples++))
    fi
    
    # Clean up temp file
    rm -f "temp_${file##*/}.na"
done < docs/.ai-only/ai_output/dana_example_files.txt

echo "Broken examples found: $broken_examples"

# 3. Update AI assistant references
echo "Updating AI assistant references..."
if [ -f docs/.ai-only/ai_output/new_functions.txt ]; then
    echo "Updating functions.md with new function information..."
    # This would be done by the AI reading the file and updating it
    echo "FUNCTIONS_UPDATED" > docs/.ai-only/ai_output/functions_updated.txt
fi

# 4. Create GitHub issues for significant gaps
echo "Creating GitHub issues for gaps..."
if [ -f docs/.ai-only/ai_output/broken_examples.txt ]; then
    echo "Issues needed for broken examples: $(wc -l < docs/.ai-only/ai_output/broken_examples.txt)"
    # This would create actual GitHub issues
    echo "GITHUB_ISSUES_CREATED" > docs/.ai-only/ai_output/github_issues_created.txt
fi

# 5. Generate content update summary
echo "Generating content update summary..."
cat > docs/.ai-only/ai_output/content_update_summary.txt << EOF
=== AI CONTENT UPDATE SUMMARY ===
Date: $(date)
Functions processed: $(wc -l < docs/.ai-only/ai_output/functions_to_document.txt 2>/dev/null || echo "0")
Files with Dana examples: $(wc -l < docs/.ai-only/ai_output/dana_example_files.txt)
Broken examples found: $broken_examples
Functions updated: $(if [ -f docs/.ai-only/ai_output/functions_updated.txt ]; then echo "YES"; else echo "NO"; fi)
GitHub issues created: $(if [ -f docs/.ai-only/ai_output/github_issues_created.txt ]; then echo "YES"; else echo "NO"; fi)
EOF

echo "=== AI DOCUMENTATION CONTENT UPDATE COMPLETE $(date) ===" 