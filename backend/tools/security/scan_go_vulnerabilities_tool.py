"""
Scan Go Vulnerabilities Tool - Scan Go projects for security vulnerabilities using govulncheck
"""

import subprocess
from typing import Dict, Any, Optional
from langchain_core.tools import tool

from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def scan_go_vulnerabilities(repository_path: str) -> Dict[str, Any]:
    """Scan Go repository for security vulnerabilities using govulncheck.
    
    This tool specifically scans Go projects for known security vulnerabilities using the official govulncheck 
    tool from the Go team. It should be used when the repository contains Go code (you can determine this by 
    running detect_languages first). The tool analyzes Go modules and dependencies for known CVEs and security issues.
    
    Prerequisites: Repository must contain Go code (check with detect_languages); Go and govulncheck must be installed
    Best used: After confirming the repository uses Go language
    
    Args:
        repository_path: Path to the cloned repository containing Go code
        
    Returns:
        Dictionary with vulnerability findings, affected modules, and security recommendations
    """
    logger.info(f"Scanning Go vulnerabilities at {repository_path}")
    
    try:
        # Check if govulncheck is available
        result = subprocess.run(
            ["govulncheck", "-version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.returncode != 0:
            logger.warning("govulncheck not available")
            return {
                "status": "skipped",
                "reason": "govulncheck not available",
                "vulnerabilities_found": 0,
                "raw_output": ""
            }
        
        # Run govulncheck scan
        logger.info("Running govulncheck scan...")
        scan_result = subprocess.run(
            ["govulncheck", "./..."],
            cwd=repository_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120  # 2 minute timeout for scan
        )
        
        raw_output = scan_result.stdout
        
        # Analyze results
        if scan_result.returncode == 0:
            # No vulnerabilities found
            logger.info("govulncheck completed - no vulnerabilities found")
            return {
                "status": "completed",
                "vulnerabilities_found": 0,
                "raw_output": raw_output,
                "clean": True,
                "summary": "No vulnerabilities found in Go dependencies"
            }
        else:
            # Vulnerabilities found or scan had issues
            if raw_output and ("vulnerabilities" in raw_output.lower() or "affected" in raw_output.lower()):
                # Parse vulnerability count
                vuln_count = _extract_vulnerability_count(raw_output)
                
                logger.warning(f"govulncheck found {vuln_count} vulnerabilities")
                return {
                    "status": "completed",
                    "vulnerabilities_found": vuln_count,
                    "raw_output": raw_output,
                    "clean": False,
                    "summary": f"Found {vuln_count} security vulnerabilities",
                    "affected_files": _extract_affected_files(raw_output)
                }
            else:
                # Scan failed for other reasons
                logger.error(f"govulncheck scan failed: {scan_result.stderr}")
                return {
                    "status": "error",
                    "reason": "Scan failed",
                    "error": scan_result.stderr,
                    "vulnerabilities_found": 0,
                    "raw_output": raw_output
                }
                
    except subprocess.TimeoutExpired:
        logger.warning("govulncheck scan timed out")
        return {
            "status": "error",
            "reason": "Scan timed out",
            "vulnerabilities_found": 0,
            "raw_output": ""
        }
    except FileNotFoundError:
        logger.info("govulncheck not installed")
        return {
            "status": "skipped",
            "reason": "govulncheck not installed",
            "vulnerabilities_found": 0,
            "raw_output": ""
        }
    except Exception as e:
        logger.error(f"Failed to scan Go vulnerabilities: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "vulnerabilities_found": 0,
            "raw_output": ""
        }

def _extract_vulnerability_count(output: str) -> int:
    """Extract number of vulnerabilities from govulncheck output."""
    import re
    
    # Look for patterns like "Your code is affected by X vulnerabilities"
    patterns = [
        r"affected by (\d+) vulnerabilities",
        r"found (\d+) vulnerabilities",
        r"(\d+) vulnerabilities found"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    # If no explicit count found, count unique vulnerability IDs
    vuln_ids = re.findall(r"(GO-\d{4}-\d{4})", output)
    return len(set(vuln_ids))

def _extract_affected_files(output: str) -> list:
    """Extract list of affected files from govulncheck output."""
    import re
    
    # Look for file paths in the output
    file_patterns = [
        r"([a-zA-Z0-9_./\\-]+\.go)",
        r"^\s*([a-zA-Z0-9_./\\-]+\.go):",
    ]
    
    affected_files = set()
    for pattern in file_patterns:
        matches = re.findall(pattern, output, re.MULTILINE)
        for match in matches:
            if match and not match.startswith('go'):  # Exclude go command outputs
                affected_files.add(match)
    
    return list(affected_files)[:10]  # Limit to first 10 files 