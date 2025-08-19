#!/usr/bin/env python3
"""Script to update Pydantic v1 Config to v2 ConfigDict in schema files."""

import os
import re
from pathlib import Path

# Pattern to match old Config class
config_pattern = re.compile(
    r'(\s+)class Config:\s*\n(\s+)schema_extra\s*=\s*(\{[\s\S]*?\n\s+\})\s*\n',
    re.MULTILINE
)

def update_file(file_path):
    """Update a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if ConfigDict is already imported
    if 'ConfigDict' not in content:
        # Add ConfigDict to imports
        import_pattern = r'(from pydantic import [^;\n]*)'
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r'\1, ConfigDict',
                content
            )
    
    # Replace Config classes with model_config
    def replace_config(match):
        indent = match.group(1)
        json_schema_content = match.group(3)
        return f'{indent}model_config = ConfigDict(json_schema_extra={json_schema_content})\n'
    
    content = config_pattern.sub(replace_config, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {file_path}")

# Schema files to update
schema_dir = Path("c:/Harish/Projects/JobHunt/eagle-bank-api-python/app/schemas")
files_to_update = [
    schema_dir / "accounts.py",
    schema_dir / "transactions.py", 
    schema_dir / "errors.py"
]

for file_path in files_to_update:
    if file_path.exists():
        update_file(file_path)
    else:
        print(f"File not found: {file_path}")

print("All files updated!")
