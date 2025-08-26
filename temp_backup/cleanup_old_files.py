#!/usr/bin/env python3
"""
Cleanup script to remove old duplicate files after refactoring.
"""

import os
from pathlib import Path

def main():
    """Remove old duplicate files."""
    
    # Files to remove (old versions that have been moved)
    files_to_remove = [
        "shared/llm.py",           # Now in shared/llm/client.py
        "shared/adapters.py",      # Now in shared/llm/adapters.py
        "shared/init.py",          # Empty file, not needed
    ]
    
    removed_count = 0
    
    for file_path in files_to_remove:
        full_path = Path(file_path)
        if full_path.exists():
            try:
                full_path.unlink()  # Remove the file
                print(f"✓ Removed {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"✗ Failed to remove {file_path}: {e}")
        else:
            print(f"- File not found: {file_path}")
    
    print(f"\n🧹 Cleanup complete! Removed {removed_count} files.")
    
    # Show final directory structure
    print("\n📁 Final shared/ directory structure:")
    shared_dir = Path("shared")
    for item in sorted(shared_dir.rglob("*")):
        if item.is_file() and not item.name.startswith(".") and "__pycache__" not in str(item):
            indent = "  " * (len(item.parts) - 1)
            print(f"{indent}{item.name}")

if __name__ == "__main__":
    main()
