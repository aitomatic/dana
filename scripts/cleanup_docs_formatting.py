#!/usr/bin/env python3
"""
Script to clean up excessive emojis and bold formatting in documentation files.
Removes unprofessional formatting while preserving strategic symbols like ✅ and ❌.
"""

import os
import re
from pathlib import Path

# Emojis to preserve (strategic/professional)
PRESERVE_EMOJIS = {
    '✅', '❌', '✓', '✗', '⚠️', '📋', '📄'  # Checkmarks, warnings, basic document symbols
}

# Common unprofessional emojis to remove
REMOVE_EMOJIS = {
    '🚀', '🎯', '🛠️', '🔍', '🏗️', '🤖', '🔄', '🔗', '🐛', '📚', '💡', '🔧',
    '🧭', '✖️', '🧠', '📦', '🧩', '🧾', '📜', '🔑', '🎌', '🎉', '🔥', '💰'
}

def clean_file_content(content: str) -> str:
    """Clean excessive formatting from markdown content."""
    
    # Remove specific unprofessional emojis
    for emoji in REMOVE_EMOJIS:
        content = content.replace(emoji, '')
    
    # Clean up excessive bold formatting patterns
    # Pattern: **Word**: -> Word:
    content = re.sub(r'\*\*([^*]+):\*\*', r'\1:', content)
    
    # Pattern: **Word** -> Word (when not part of larger formatting)
    # Be careful not to break legitimate emphasis
    content = re.sub(r'^\s*\*\*([^*\n]+)\*\*\s*$', r'\1', content, flags=re.MULTILINE)
    
    # Pattern: * **Word** -> * Word (in bullet points)
    content = re.sub(r'(\*\s+)\*\*([^*]+)\*\*', r'\1\2', content)
    
    # Pattern: - **Word** -> - Word (in bullet points)
    content = re.sub(r'(-\s+)\*\*([^*]+)\*\*', r'\1\2', content)
    
    # Clean up multiple spaces and line breaks that might result from emoji removal
    content = re.sub(r'  +', ' ', content)  # Multiple spaces to single space
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Multiple newlines to double newline
    
    # Remove leading/trailing spaces on lines
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)
    
    return content

def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed (exclude .ai-only and .archive)."""
    path_str = str(file_path)
    
    if '.ai-only' in path_str or '.archive' in path_str:
        return False
    
    if not file_path.suffix == '.md':
        return False
        
    return True

def process_docs_directory(docs_dir: str = "docs/"):
    """Process all markdown files in the docs directory."""
    docs_path = Path(docs_dir)
    
    if not docs_path.exists():
        print(f"Documentation directory {docs_dir} not found")
        return
    
    processed_files = []
    
    # Find all markdown files
    for md_file in docs_path.rglob("*.md"):
        if not should_process_file(md_file):
            continue
            
        try:
            # Read file content
            with open(md_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Clean content
            cleaned_content = clean_file_content(original_content)
            
            # Only write if content changed
            if cleaned_content != original_content:
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                processed_files.append(str(md_file))
                print(f"Cleaned: {md_file}")
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    print(f"\nProcessed {len(processed_files)} files")
    if processed_files:
        print("Modified files:")
        for file in processed_files:
            print(f"  - {file}")

if __name__ == "__main__":
    process_docs_directory()