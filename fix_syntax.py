#!/usr/bin/env python3
"""Fix all syntax errors in schema files."""

import os
import re
from pathlib import Path

def fix_syntax_errors(file_path):
    """Fix syntax errors in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix pattern 1: {""}) -> {""}
    pattern1 = re.compile(r'(\s*"[^"]*":\s*"[^"]*"\s*)\}\)\s*\]\s*,', re.MULTILINE)
    content = pattern1.sub(r'\1}\n                ]\n                ,', content)
    
    # Fix pattern 2: }}) -> }}
    pattern2 = re.compile(r'(\s*)\}\)\s*\]\s*,\s*\n', re.MULTILINE)
    content = pattern2.sub(r'\1}\n                ],\n', content)
    
    # More targeted fixes for specific closing bracket issues
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix }) patterns inside arrays
        if line.strip().endswith('})') and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line.startswith(']'):
                line = line.replace('})', '}')
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

# Schema files to fix
schema_dir = Path("c:/Harish/Projects/JobHunt/eagle-bank-api-python/app/schemas")
files_to_fix = [
    schema_dir / "accounts.py",
    schema_dir / "transactions.py", 
    schema_dir / "errors.py"
]

for file_path in files_to_fix:
    if file_path.exists():
        fix_syntax_errors(file_path)
    else:
        print(f"File not found: {file_path}")

print("All syntax errors fixed!")
