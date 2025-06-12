"""
Go.mod Parser for Dependency Analysis and Updates
"""

import re
import os
import subprocess
import tempfile
from typing import Dict, List, Tuple, Optional, NamedTuple
from pathlib import Path
from dataclasses import dataclass
from utils.logging_config import get_logger

logger = get_logger(__name__)


class GoModule(NamedTuple):
    """Represents a Go module dependency."""
    path: str
    version: str
    indirect: bool = False


@dataclass
class GoModFile:
    """Represents a parsed go.mod file."""
    module_path: str
    go_version: str
    dependencies: List[GoModule]
    replace_directives: Dict[str, str]
    exclude_directives: List[str]
    raw_content: str
    
    def get_dependency(self, module_path: str) -> Optional[GoModule]:
        """Get a specific dependency by module path."""
        for dep in self.dependencies:
            if dep.path == module_path:
                return dep
        return None


@dataclass
class DependencyUpdate:
    """Represents a dependency update to fix vulnerabilities."""
    module_path: str
    current_version: str
    updated_version: str
    vulnerability_ids: List[str]
    severity: str
    reasoning: str


class GoModParser:
    """Parser and updater for Go.mod files."""
    
    def __init__(self):
        self.module_pattern = re.compile(r'^module\s+(.+)$', re.MULTILINE)
        self.go_version_pattern = re.compile(r'^go\s+(.+)$', re.MULTILINE)
        self.require_block_pattern = re.compile(r'require\s*\(\s*\n(.*?)\n\s*\)', re.DOTALL)
        self.require_line_pattern = re.compile(r'require\s+(.+)')
        self.dependency_pattern = re.compile(r'^\s*([^\s]+)\s+([^\s]+)(\s+//\s*indirect)?', re.MULTILINE)
        self.replace_pattern = re.compile(r'replace\s+([^\s]+)\s*=>\s*([^\s]+(?:\s+[^\s]+)?)')
        self.exclude_pattern = re.compile(r'exclude\s+([^\s]+)')
    
    def parse_go_mod(self, go_mod_path: str) -> GoModFile:
        """
        Parse a go.mod file and extract all information.
        
        Args:
            go_mod_path: Path to the go.mod file
            
        Returns:
            Parsed GoModFile object
            
        Raises:
            FileNotFoundError: If go.mod file doesn't exist
            ValueError: If go.mod file is malformed
        """
        if not os.path.exists(go_mod_path):
            raise FileNotFoundError(f"go.mod file not found: {go_mod_path}")
        
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read go.mod file: {e}")
        
        return self._parse_content(content)
    
    def _parse_content(self, content: str) -> GoModFile:
        """Parse go.mod file content."""
        # Extract module path
        module_match = self.module_pattern.search(content)
        if not module_match:
            raise ValueError("No module declaration found in go.mod")
        module_path = module_match.group(1).strip()
        
        # Extract Go version
        go_version_match = self.go_version_pattern.search(content)
        go_version = go_version_match.group(1).strip() if go_version_match else "1.21"
        
        # Parse dependencies
        dependencies = self._parse_dependencies(content)
        
        # Parse replace directives
        replace_directives = {}
        for match in self.replace_pattern.finditer(content):
            original = match.group(1).strip()
            replacement = match.group(2).strip()
            replace_directives[original] = replacement
        
        # Parse exclude directives
        exclude_directives = []
        for match in self.exclude_pattern.finditer(content):
            exclude_directives.append(match.group(1).strip())
        
        return GoModFile(
            module_path=module_path,
            go_version=go_version,
            dependencies=dependencies,
            replace_directives=replace_directives,
            exclude_directives=exclude_directives,
            raw_content=content
        )
    
    def _parse_dependencies(self, content: str) -> List[GoModule]:
        """Parse dependency declarations from go.mod content."""
        dependencies = []
        
        # Handle require blocks
        require_blocks = self.require_block_pattern.findall(content)
        for block in require_blocks:
            for line in block.split('\n'):
                line = line.strip()
                if line and not line.startswith('//'):
                    dep = self._parse_dependency_line(line)
                    if dep:
                        dependencies.append(dep)
        
        # Handle single require lines
        single_requires = self.require_line_pattern.findall(content)
        for require_line in single_requires:
            if '(' not in require_line:  # Skip require blocks
                dep = self._parse_dependency_line(require_line.strip())
                if dep:
                    dependencies.append(dep)
        
        return dependencies
    
    def _parse_dependency_line(self, line: str) -> Optional[GoModule]:
        """Parse a single dependency line."""
        # Remove comments
        line = line.split('//')[0].strip()
        if not line:
            return None
        
        parts = line.split()
        if len(parts) < 2:
            return None
        
        module_path = parts[0]
        version = parts[1]
        indirect = '// indirect' in line or len(parts) > 2 and 'indirect' in ' '.join(parts[2:])
        
        return GoModule(path=module_path, version=version, indirect=indirect)
    
    def update_dependencies(self, go_mod_file: GoModFile, updates: List[DependencyUpdate]) -> str:
        """
        Update dependencies in go.mod content.
        
        Args:
            go_mod_file: Parsed go.mod file
            updates: List of dependency updates to apply
            
        Returns:
            Updated go.mod content
        """
        content = go_mod_file.raw_content
        
        for update in updates:
            content = self._update_single_dependency(content, update)
        
        return content
    
    def _update_single_dependency(self, content: str, update: DependencyUpdate) -> str:
        """Update a single dependency in the content."""
        module_path = re.escape(update.module_path)
        current_version = re.escape(update.current_version)
        
        # Pattern to match the dependency line
        patterns = [
            # In require block
            f'(\\s+{module_path}\\s+){current_version}(\\s*(?://.*)?)',
            # Single require line
            f'(require\\s+{module_path}\\s+){current_version}(\\s*(?://.*)?)',
        ]
        
        for pattern in patterns:
            content = re.sub(
                pattern,
                f'\\g<1>{update.updated_version}\\g<2>',
                content,
                flags=re.MULTILINE
            )
        
        return content
    
    def validate_go_mod_syntax(self, go_mod_content: str, temp_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate go.mod syntax by attempting to parse it with Go tools.
        
        Args:
            go_mod_content: Content of go.mod file to validate
            temp_dir: Optional temporary directory to use
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
            cleanup_temp = True
        else:
            cleanup_temp = False
        
        try:
            go_mod_path = os.path.join(temp_dir, 'go.mod')
            
            # Write go.mod content
            with open(go_mod_path, 'w', encoding='utf-8') as f:
                f.write(go_mod_content)
            
            # Try to run go mod verify
            result = subprocess.run(
                ['go', 'mod', 'verify'],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr or result.stdout or "Unknown go mod error"
                
        except subprocess.TimeoutExpired:
            return False, "Go mod validation timed out"
        except FileNotFoundError:
            logger.warning("Go command not found - skipping syntax validation")
            return True, "Go command not available"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
        finally:
            if cleanup_temp:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    
    def generate_go_sum_update_command(self, repo_path: str) -> List[str]:
        return ['go', 'mod', 'tidy']
    
    def find_go_mod_files(self, repo_path: str) -> List[str]:
        go_mod_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # The vendor/ directory contains copies of external packages
            # These packages may have their own go.mod files
            # We don't want to analyze or modify these copied dependency files
            # We only care about the main project's go.mod
            if 'vendor' in dirs:
                dirs.remove('vendor')
            
            if 'go.mod' in files:
                go_mod_files.append(os.path.join(root, 'go.mod'))
        
        return go_mod_files
    
    def extract_vulnerabilities_from_results(self, vulnerability_results: Dict) -> List[DependencyUpdate]:
        """
        Extract dependency updates from vulnerability scan results.
        
        Args:
            vulnerability_results: Results from vulnerability scanning tool
            
        Returns:
            List of dependency updates to fix vulnerabilities
        """
        updates = []
        
        # This is a simplified implementation - in reality, you'd need to map
        # vulnerability data to specific version fixes
        vulnerabilities = vulnerability_results.get('vulnerabilities', [])
        
        for vuln in vulnerabilities:
            if isinstance(vuln, dict):
                module_path = vuln.get('module', '')
                current_version = vuln.get('current_version', '')
                fixed_version = vuln.get('fixed_version', '')
                vulnerability_ids = vuln.get('vulnerability_ids', [])
                severity = vuln.get('severity', 'medium')
                
                if module_path and current_version and fixed_version:
                    updates.append(DependencyUpdate(
                        module_path=module_path,
                        current_version=current_version,
                        updated_version=fixed_version,
                        vulnerability_ids=vulnerability_ids,
                        severity=severity,
                        reasoning=f"Fix for {len(vulnerability_ids)} vulnerabilities"
                    ))
        
        return updates 
