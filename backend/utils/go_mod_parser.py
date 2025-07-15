"""
Go.mod Parser for Vulnerability Fixes
"""

import re
import os
from typing import Dict, List, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

def parse_go_mod(go_mod_path: str) -> Dict[str, str]:
    """
    Parse go.mod file and return dependencies as dict.
    
    Args:
        go_mod_path: Path to the go.mod file
        
    Returns:
        Dict mapping module path to version (e.g. {"github.com/gin-gonic/gin": "v1.7.0"})
    """
    if not os.path.exists(go_mod_path):
        raise FileNotFoundError(f"go.mod file not found: {go_mod_path}")
    
    with open(go_mod_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    dependencies = {}
    
    # Extract dependencies from require blocks
    require_block_pattern = re.compile(r'require\s*\(\s*\n(.*?)\n\s*\)', re.DOTALL)
    require_blocks = require_block_pattern.findall(content)
    
    for block in require_blocks:
        for line in block.split('\n'):
            line = line.strip()
            if line and not line.startswith('//'):
                dep = _parse_dependency_line(line)
                if dep:
                    dependencies[dep[0]] = dep[1]
    
    # Extract single require lines
    require_line_pattern = re.compile(r'require\s+([^\s]+)\s+([^\s]+)', re.MULTILINE)
    for match in require_line_pattern.finditer(content):
        module_path = match.group(1)
        version = match.group(2)
        dependencies[module_path] = version
    
    return dependencies

def _parse_dependency_line(line: str) -> Optional[tuple]:
    """Parse a single dependency line and return (module_path, version)."""
    line = line.split('//')[0].strip()  # Remove comments
    if not line:
        return None
    
    parts = line.split()
    if len(parts) < 2:
        return None
    
    return (parts[0], parts[1])

def update_go_mod_dependencies(go_mod_path: str, dependency_updates: Dict[str, str]) -> str:
    """
    Update specific dependencies in go.mod file while preserving all others.
    
    Args:
        go_mod_path: Path to the go.mod file
        dependency_updates: Dict mapping module path to new version
        
    Returns:
        Updated go.mod content
    """
    with open(go_mod_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for module_path, new_version in dependency_updates.items():
        content = _update_single_dependency(content, module_path, new_version)
    
    return content

def _update_single_dependency(content: str, module_path: str, new_version: str) -> str:
    """Update a single dependency in the go.mod content."""
    escaped_module = re.escape(module_path)
    
    # Pattern to match the dependency line and capture the version part
    patterns = [
        # In require block: "    github.com/module v1.0.0"
        f'(\\s+{escaped_module}\\s+)([^\\s]+)(\\s*(?://.*)?)',
        # Single require line: "require github.com/module v1.0.0"
        f'(require\\s+{escaped_module}\\s+)([^\\s]+)(\\s*(?://.*)?)',
    ]
    
    for pattern in patterns:
        content = re.sub(
            pattern,
            f'\\g<1>{new_version}\\g<3>',
            content,
            flags=re.MULTILINE
        )
    
    return content

def generate_dependency_updates_from_vulnerabilities(vulnerabilities: List[Dict]) -> Dict[str, str]:
    """
    Generate dependency updates from vulnerability scan results.
    
    Args:
        vulnerabilities: List of vulnerability dictionaries
        
    Returns:
        Dict mapping module path to updated version
    """
    updates = {}
    
    for vuln in vulnerabilities:
        module_path = vuln.get('package') or vuln.get('module')
        current_version = vuln.get('current_version')
        
        if module_path and current_version:
            # For now, use a simple heuristic to suggest version updates
            # In a real implementation, you'd query a vulnerability database
            suggested_version = _suggest_secure_version(module_path, current_version)
            if suggested_version:
                updates[module_path] = suggested_version
    
    return updates

def _suggest_secure_version(module_path: str, current_version: str) -> Optional[str]:
    """
    Suggest a secure version for a vulnerable module.
    This is a simplified implementation - in practice you'd use CVE databases.
    """
    # Remove 'v' prefix if present
    version = current_version.lstrip('v')
    
    try:
        # Simple heuristic: increment patch version
        parts = version.split('.')
        if len(parts) >= 3:
            patch = int(parts[2]) + 1
            suggested = f"v{parts[0]}.{parts[1]}.{patch}"
            logger.info(f"Suggesting version {suggested} for {module_path} (current: {current_version})")
            return suggested
    except (ValueError, IndexError):
        pass
    
    logger.warning(f"Could not suggest secure version for {module_path} {current_version}")
    return None 
