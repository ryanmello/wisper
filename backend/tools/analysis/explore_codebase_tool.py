"""
Explore Codebase Tool - Analyze repository structure, file types, and organization
"""

import os
from typing import Dict, Any
from pathlib import Path
from collections import defaultdict, Counter
from langchain_core.tools import tool

from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def explore_codebase(repository_path: str) -> Dict[str, Any]:
    """Analyze repository structure, file types, and directory organization to understand codebase composition.
    
    This tool provides a comprehensive overview of the repository by analyzing file types, directory structure, 
    code metrics, and overall organization. It's useful for getting a high-level understanding of the codebase 
    size, complexity, and structure before diving into more specific analysis.
    
    Prerequisites: Repository must be cloned locally (requires repository_path)
    Provides: Structural overview that complements other analysis tools
    
    Args:
        repository_path: Path to the cloned repository
        
    Returns:
        Dictionary containing file structure analysis, statistics, and organization
    """
    logger.info(f"Exploring codebase structure at {repository_path}")
    
    try:
        file_types = Counter()
        directory_analysis = defaultdict(list)
        
        skip_dirs = {
            '.git', '__pycache__', 'node_modules', '.next', 'dist', 'build',
            '.vscode', '.idea', 'coverage', '.pytest_cache', 'venv', 'env'
        }
        
        total_files = 0
        total_lines = 0
        
        for root, dirs, files in os.walk(repository_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            rel_path = os.path.relpath(root, repository_path)
            if rel_path == '.':
                rel_path = 'root'
            
            for file in files:
                if file.startswith('.') and file not in ['.env.example', '.gitignore', '.dockerignore']:
                    continue
                    
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                file_types[file_ext] += 1
                directory_analysis[rel_path].append(file)
                total_files += 1
                
                # Count lines for code files
                if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.go', '.rs']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            total_lines += lines
                    except:
                        pass
        
        result = {
            "total_files": total_files,
            "total_lines": total_lines,
            "file_types": dict(file_types.most_common()),
            "directory_structure": dict(directory_analysis),
            "main_directories": list(directory_analysis.keys())[:20],
            # Tool metadata for result compilation
            "_tool_metadata": {
                "category": "analysis",
                "result_type": "exploration",
                "output_keys": ["total_files", "total_lines", "file_types", "directory_structure"],
                "priority": 2
            }
        }
        
        logger.info(f"Codebase exploration complete - {total_files} files, {total_lines} lines of code")
        return result
        
    except Exception as e:
        logger.error(f"Failed to explore codebase at {repository_path}: {e}")
        return {
            "error": str(e),
            "total_files": 0,
            "total_lines": 0,
            "file_types": {},
            "directory_structure": {},
            "main_directories": [],
            "_tool_metadata": {
                "category": "analysis",
                "result_type": "exploration",
                "output_keys": [],
                "priority": 2
            }
        } 