import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from utils.go_mod_parser import DependencyUpdate, GoModFile
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VulnerabilityInfo:
    """Information about a specific vulnerability."""
    cve_id: str
    module_path: str
    vulnerable_version: str
    fixed_version: str
    severity: str
    description: str
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


@dataclass
class VersionCompatibility:
    """Information about version compatibility and breaking changes."""
    is_major_update: bool
    is_minor_update: bool
    is_patch_update: bool
    breaking_changes: List[str] = None
    deprecations: List[str] = None
    compatibility_notes: str = ""
    
    def __post_init__(self):
        if self.breaking_changes is None:
            self.breaking_changes = []
        if self.deprecations is None:
            self.deprecations = []


class DependencyUpdater:
    """
    Service for mapping vulnerabilities to dependency fixes and managing updates.
    """
    
    def __init__(self):
        # Version patterns for different versioning schemes
        self.semver_pattern = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)(?:-([^+]+))?(?:\+(.+))?$')
        self.go_pseudo_version = re.compile(r'^v\d+\.\d+\.\d+-\d{14}-[a-f0-9]{12}$')
    
    def analyze_vulnerabilities(
        self, 
        vulnerability_results: Dict[str, Any],
        go_mod_file: GoModFile
    ) -> List[DependencyUpdate]:
        """
        Analyze vulnerability results and generate dependency updates.
        """
        updates = []
        
        logger.info(f"Analyzing vulnerabilities for go.mod with {len(go_mod_file.dependencies)} dependencies")
        
        # Parse vulnerabilities from scan results
        vulnerabilities = self._parse_vulnerability_results(vulnerability_results)
        logger.info(f"Parsed {len(vulnerabilities)} vulnerabilities from scan results")
        
        for vulnerability in vulnerabilities:
            logger.info(f"Processing vulnerability: {vulnerability.cve_id} for module {vulnerability.module_path}")
            
            # Find the dependency in go.mod
            dependency = go_mod_file.get_dependency(vulnerability.module_path)
            if not dependency:
                logger.warning(f"Vulnerability found for {vulnerability.module_path} but not in go.mod")
                continue
            
            logger.info(f"Found dependency {dependency.path} version {dependency.version}")
            
            # Check if current version is vulnerable
            if self._is_version_vulnerable(dependency.version, vulnerability.vulnerable_version):
                logger.info(f"Version {dependency.version} is vulnerable to {vulnerability.vulnerable_version}")
                update = self._create_dependency_update(vulnerability, dependency.version)
                if update:
                    logger.info(f"Created update: {update.module_path} {update.current_version} -> {update.updated_version}")
                    updates.append(update)
                else:
                    logger.warning(f"Failed to create update for {vulnerability.module_path}")
            else:
                logger.info(f"Version {dependency.version} is not vulnerable to {vulnerability.vulnerable_version}")
        
        # Sort updates by severity and impact
        updates.sort(key=lambda u: self._get_update_priority(u), reverse=True)
        
        logger.info(f"Generated {len(updates)} total dependency updates")
        return updates
    
    def _parse_vulnerability_results(self, results: Dict[str, Any]) -> List[VulnerabilityInfo]:
        """Parse vulnerability results from external scanner."""
        vulnerabilities = []
        
        logger.info(f"Parsing vulnerability results with keys: {list(results.keys())}")
        logger.info(f"Full results structure: {results}")
        
        # Handle different result formats
        if 'vulnerabilities' in results:
            vuln_list = results['vulnerabilities']
            logger.info(f"Found 'vulnerabilities' key with {len(vuln_list)} items")
        elif 'osv' in results:
            vuln_list = results['osv']
            logger.info(f"Found 'osv' key with {len(vuln_list)} items")
        else:
            # Try to extract from raw results
            vuln_list = []
            for key, value in results.items():
                if isinstance(value, list) and value:
                    logger.info(f"Found potential vulnerability list in key '{key}' with {len(value)} items")
                    vuln_list = value
                    break
            
            if not vuln_list:
                logger.warning("No vulnerability list found in results")
        
        logger.info(f"Processing {len(vuln_list)} vulnerability entries")
        
        for i, vuln_data in enumerate(vuln_list):
            try:
                logger.info(f"Processing vulnerability {i+1}: {vuln_data}")
                vulnerability = self._parse_single_vulnerability(vuln_data)
                if vulnerability:
                    logger.info(f"Successfully parsed vulnerability: {vulnerability.cve_id} for {vulnerability.module_path}")
                    vulnerabilities.append(vulnerability)
                else:
                    logger.warning(f"Failed to parse vulnerability {i+1}")
            except Exception as e:
                logger.warning(f"Failed to parse vulnerability {i+1}: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(vulnerabilities)} vulnerabilities")
        return vulnerabilities
    
    def _parse_single_vulnerability(self, vuln_data: Dict[str, Any]) -> Optional[VulnerabilityInfo]:
        """Parse a single vulnerability from scan results."""
        try:
            logger.info(f"Parsing vulnerability data: {vuln_data}")
            
            # Handle different vulnerability data formats
            cve_id = vuln_data.get('id', vuln_data.get('cve_id', 'UNKNOWN'))
            
            # Check for different module path fields
            module_path = (
                vuln_data.get('affected_module') or 
                vuln_data.get('module') or 
                vuln_data.get('package') or 
                ''
            )
            
            if not module_path:
                logger.warning("No module path found in vulnerability data")
                return None
            
            # Extract version information - handle simple format
            vulnerable_version = "<unknown"
            fixed_version = "latest"
            
            # Handle affected_versions field (list format)
            if 'affected_versions' in vuln_data:
                affected_versions = vuln_data['affected_versions']
                if isinstance(affected_versions, list) and affected_versions:
                    # Take the first affected version range
                    vulnerable_version = affected_versions[0]
                    logger.info(f"Found affected_versions: {vulnerable_version}")
            
            # Handle fixed_versions field (list format)  
            if 'fixed_versions' in vuln_data:
                fixed_versions = vuln_data['fixed_versions']
                if isinstance(fixed_versions, list) and fixed_versions:
                    # Take the first fixed version
                    fixed_version = fixed_versions[0].replace('+', '')  # Remove '+' suffix
                    logger.info(f"Found fixed_versions: {fixed_version}")
            
            # Fallback to old complex parsing logic if simple parsing didn't work
            if vulnerable_version == "<unknown" or fixed_version == "latest":
                affected = vuln_data.get('affected', [])
                if not affected and 'versions' in vuln_data:
                    affected = vuln_data['versions']
                
                for affect in affected:
                    if isinstance(affect, dict):
                        if 'ranges' in affect:
                            for range_info in affect['ranges']:
                                if range_info.get('type') == 'SEMVER':
                                    events = range_info.get('events', [])
                                    for event in events:
                                        if 'fixed' in event:
                                            fixed_version = event['fixed']
                                            break
                        
                        if 'versions' in affect:
                            # Use the first vulnerable version range
                            vulnerable_version = f"<{fixed_version}"
            
            severity = vuln_data.get('severity', vuln_data.get('database_specific', {}).get('severity', 'medium'))
            description = vuln_data.get('summary', vuln_data.get('details', 'No description available'))
            aliases = vuln_data.get('aliases', [])
            
            result = VulnerabilityInfo(
                cve_id=cve_id,
                module_path=module_path,
                vulnerable_version=vulnerable_version,
                fixed_version=fixed_version,
                severity=severity.lower(),
                description=description,
                aliases=aliases
            )
            
            logger.info(f"Successfully parsed vulnerability: {result.cve_id} for {result.module_path} ({result.vulnerable_version} -> {result.fixed_version})")
            return result
            
        except Exception as e:
            logger.warning(f"Error parsing vulnerability data: {e}")
            logger.warning(f"Vulnerability data was: {vuln_data}")
            return None
    
    def _is_version_vulnerable(self, current_version: str, vulnerable_range: str) -> bool:
        """Check if current version falls within vulnerable range."""
        try:
            logger.info(f"Checking if version {current_version} is vulnerable to {vulnerable_range}")
            
            # Handle different vulnerable range formats
            if vulnerable_range.startswith('<'):
                max_version = vulnerable_range[1:].strip()
                # For semantic versioning, we need to check if current < max
                result = self._compare_versions(current_version, max_version) < 0
                logger.info(f"Range check: {current_version} < {max_version} = {result}")
                return result
            elif vulnerable_range.startswith('<='):
                max_version = vulnerable_range[2:].strip()
                result = self._compare_versions(current_version, max_version) <= 0
                logger.info(f"Range check: {current_version} <= {max_version} = {result}")
                return result
            elif vulnerable_range.startswith('>'):
                min_version = vulnerable_range[1:].strip()
                result = self._compare_versions(current_version, min_version) > 0
                logger.info(f"Range check: {current_version} > {min_version} = {result}")
                return result
            elif vulnerable_range.startswith('>='):
                min_version = vulnerable_range[2:].strip()
                result = self._compare_versions(current_version, min_version) >= 0
                logger.info(f"Range check: {current_version} >= {min_version} = {result}")
                return result
            else:
                # Exact version match or other format - assume vulnerable for safety
                logger.info(f"Exact match or unknown format - assuming vulnerable")
                return True
                
        except Exception as e:
            logger.warning(f"Error comparing versions {current_version} vs {vulnerable_range}: {e}")
            # If we can't determine, assume vulnerable for safety
            return True
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2."""
        try:
            from packaging import version
            
            # Clean up version strings (remove 'v' prefix)
            v1_clean = version1.lstrip('v')
            v2_clean = version2.lstrip('v')
            
            logger.info(f"Comparing versions: {v1_clean} vs {v2_clean}")
            
            v1 = version.parse(v1_clean)
            v2 = version.parse(v2_clean)
            
            if v1 < v2:
                result = -1
            elif v1 > v2:
                result = 1
            else:
                result = 0
                
            logger.info(f"Version comparison result: {v1_clean} vs {v2_clean} = {result}")
            return result
            
        except Exception as e:
            logger.warning(f"Error parsing versions {version1}/{version2}: {e}")
            # Fallback to string comparison
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
    
    def _create_dependency_update(
        self, 
        vulnerability: VulnerabilityInfo, 
        current_version: str
    ) -> Optional[DependencyUpdate]:
        """Create a dependency update for a vulnerability."""
        try:
            # Generate reasoning
            reasoning = f"Fixes {vulnerability.severity} severity vulnerability {vulnerability.cve_id}"
            
            return DependencyUpdate(
                module_path=vulnerability.module_path,
                current_version=current_version,
                updated_version=vulnerability.fixed_version,
                vulnerability_ids=[vulnerability.cve_id] + vulnerability.aliases,
                severity=vulnerability.severity,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error creating dependency update: {e}")
            return None
    
    def _get_update_priority(self, update: DependencyUpdate) -> int:
        """Get priority score for update (higher = more important)."""
        priority = 0
        
        # Severity priority
        severity_scores = {
            'critical': 100,
            'high': 80,
            'medium': 60,
            'low': 40,
            'info': 20
        }
        
        priority += severity_scores.get(update.severity.lower(), 50)
        
        return priority

    def analyze_vulnerabilities_from_scan_results(
        self, 
        vulnerability_results: Dict[str, Any]
    ) -> List[DependencyUpdate]:
        """
        Analyze vulnerability results and generate dependency updates without requiring go.mod file.
        This method extracts dependency updates directly from vulnerability scan results.
        
        Args:
            vulnerability_results: Results from vulnerability scanning tool
            
        Returns:
            List of dependency updates to fix vulnerabilities
        """
        updates = []
        
        logger.info("Analyzing vulnerabilities from scan results (without go.mod)")
        
        # Parse vulnerabilities from scan results
        vulnerabilities = self._parse_vulnerability_results(vulnerability_results)
        logger.info(f"Parsed {len(vulnerabilities)} vulnerabilities from scan results")
        
        for vulnerability in vulnerabilities:
            logger.info(f"Processing vulnerability: {vulnerability.cve_id} for module {vulnerability.module_path}")
            
            # Create dependency update directly from vulnerability info
            # This assumes the vulnerability scanner already determined current version
            update = self._create_dependency_update(vulnerability, vulnerability.vulnerable_version.lstrip('<>='))
            if update:
                logger.info(f"Created update: {update.module_path} {update.current_version} -> {update.updated_version}")
                updates.append(update)
            else:
                logger.warning(f"Failed to create update for {vulnerability.module_path}")
        
        # Sort updates by severity and impact
        updates.sort(key=lambda u: self._get_update_priority(u), reverse=True)
        
        logger.info(f"Generated {len(updates)} total dependency updates from scan results")
        return updates 
