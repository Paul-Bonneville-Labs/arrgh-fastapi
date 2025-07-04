#!/usr/bin/env python3
"""
LangChain 0.2 → 0.3 Migration Compatibility Check
This script identifies potential breaking changes in our LangChain usage.
"""

import os
import ast
import sys
from pathlib import Path

def find_langchain_imports(file_path):
    """Find all LangChain-related imports in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        langchain_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if 'langchain' in alias.name or 'langgraph' in alias.name:
                        langchain_imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and ('langchain' in node.module or 'langgraph' in node.module):
                    names = [alias.name for alias in node.names]
                    langchain_imports.append(f"from {node.module} import {', '.join(names)}")
        
        return langchain_imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def check_breaking_changes(import_line):
    """Check for known breaking changes in LangChain 0.3."""
    issues = []
    
    # Known breaking changes from LangChain 0.2 to 0.3
    breaking_changes = {
        'langchain.llms': 'Moved to langchain_community.llms or deprecated',
        'langchain.chat_models': 'Moved to provider-specific packages (langchain_openai, etc.)',
        'langchain.embeddings': 'Moved to provider-specific packages',
        'langchain.vectorstores': 'Moved to langchain_community.vectorstores',
        'langchain.document_loaders': 'Moved to langchain_community.document_loaders',
        'langchain.schema': 'Reorganized into langchain_core.messages, langchain_core.documents',
        'langgraph.prebuilt': 'Some classes may have been removed or renamed',
    }
    
    for old_import, message in breaking_changes.items():
        if old_import in import_line:
            issues.append(f"  ⚠️  {old_import}: {message}")
    
    # Check for specific classes that might have changed
    if 'ToolExecutor' in import_line and 'langgraph.prebuilt' in import_line:
        issues.append("  ⚠️  ToolExecutor from langgraph.prebuilt may have been removed/renamed")
    
    return issues

def main():
    print("🔍 LangChain 0.2 → 0.3 Migration Check")
    print("=" * 50)
    
    # Find all Python files in src/
    src_dir = Path('src')
    if not src_dir.exists():
        print("❌ src/ directory not found")
        return
    
    python_files = list(src_dir.rglob('*.py'))
    notebook_files = list(Path('notebooks').rglob('*.py')) if Path('notebooks').exists() else []
    
    all_files = python_files + notebook_files
    
    total_issues = 0
    files_with_langchain = 0
    
    for file_path in all_files:
        imports = find_langchain_imports(file_path)
        if imports:
            files_with_langchain += 1
            print(f"\n📄 {file_path}")
            print("-" * len(str(file_path)))
            
            file_issues = 0
            for import_line in imports:
                print(f"  📦 {import_line}")
                issues = check_breaking_changes(import_line)
                if issues:
                    file_issues += len(issues)
                    for issue in issues:
                        print(issue)
                else:
                    print("    ✅ Likely compatible")
            
            if file_issues == 0:
                print("  ✅ No known breaking changes detected")
            else:
                print(f"  ⚠️  {file_issues} potential issues found")
            
            total_issues += file_issues
    
    # Check notebooks manually for LangChain usage
    notebook_file = Path('notebooks/newsletter_processing.ipynb')
    if notebook_file.exists():
        print(f"\n📄 {notebook_file} (manual check needed)")
        print("-" * len(str(notebook_file)))
        print("  ℹ️  Jupyter notebook - manual review required for LangChain usage")
        print("  ℹ️  Check for: imports, LLM initialization, schema usage")
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"  Files with LangChain: {files_with_langchain}")
    print(f"  Potential issues: {total_issues}")
    
    if total_issues == 0:
        print("  ✅ No obvious breaking changes detected")
        print("  ℹ️  Still test thoroughly as some changes might not be detectable")
    else:
        print("  ⚠️  Breaking changes likely - review and update code")
    
    print("\n📚 NEXT STEPS:")
    print("  1. Review LangChain 0.3 migration guide")
    print("  2. Update import statements as needed")
    print("  3. Test entity extraction pipeline thoroughly")
    print("  4. Update any deprecated API usage")

if __name__ == "__main__":
    main()