"""
Security Audit Tool - Perform general security audit based on repository language and patterns
"""

import os
import re
from typing import Dict, Any, List
from langchain_core.tools import tool

from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def security_audit(repository_path: str, language_info: Dict[str, Any]) -> Dict[str, Any]:
    """Perform general security audit based on repository language and common vulnerability patterns.
    
    This tool conducts a comprehensive security analysis by examining code patterns, configuration files, 
    dependencies, and potential security vulnerabilities across multiple languages. It provides language-specific 
    security checks when language_info is provided from the detect_languages tool, enabling more targeted 
    vulnerability detection.
    
    Prerequisites: Repository must be cloned locally; enhanced by language_info from detect_languages
    Use for: General security analysis across multiple programming languages
    
    Args:
        repository_path: Path to the cloned repository
        language_info: Language detection results for targeted security analysis
        
    Returns:
        Dictionary with security findings, risk assessment, and remediation recommendations
    """
    logger.info(f"Performing security audit for {language_info['primary_language']} project at {repository_path}")
    
    try:
        security_issues = []
        recommendations = []
        
        # Language-specific security checks
        if language_info['primary_language'].lower() == "python":
            security_issues.extend(_check_python_security(repository_path))
        elif language_info['primary_language'].lower() == "javascript" or language_info['primary_language'].lower() == "typescript":
            security_issues.extend(_check_javascript_security(repository_path))
        elif language_info['primary_language'].lower() == "java":
            security_issues.extend(_check_java_security(repository_path))
        elif language_info['primary_language'].lower() == "go":
            security_issues.extend(_check_go_security(repository_path))
        
        # General security checks (all languages)
        security_issues.extend(_check_general_security(repository_path))
        
        # Generate recommendations based on issues found
        recommendations = _generate_security_recommendations(security_issues, language_info['primary_language'])
        
        # Calculate risk level
        risk_level = _calculate_risk_level(security_issues)
        
        result = {
            "primary_language": language_info['primary_language'],
            "security_issues": security_issues,
            "total_issues": len(security_issues),
            "risk_level": risk_level,
            "recommendations": recommendations,
            "audit_summary": f"Found {len(security_issues)} potential security issues"
        }
        
        logger.info(f"Security audit complete - {len(security_issues)} issues found, risk level: {risk_level}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to perform security audit: {e}")
        return {
            "error": str(e),
            "primary_language": language_info['primary_language'],
            "security_issues": [],
            "total_issues": 0,
            "risk_level": "unknown",
            "recommendations": [],
            "audit_summary": "Security audit failed"
        }

def _check_python_security(repo_path: str) -> List[Dict[str, Any]]:
    """Check for Python-specific security issues."""
    issues = []
    
    # Check for hardcoded secrets in Python files
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for hardcoded passwords/keys
                        patterns = [
                            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
                            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded API key"),
                            (r'secret\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded secret"),
                        ]
                        
                        for pattern, description in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append({
                                    "type": "hardcoded_secret",
                                    "severity": "high",
                                    "file": os.path.relpath(file_path, repo_path),
                                    "description": description,
                                    "language": "Python"
                                })
                except:
                    pass
    
    # Check for unsafe dependencies
    req_file = os.path.join(repo_path, 'requirements.txt')
    if os.path.exists(req_file):
        try:
            with open(req_file, 'r') as f:
                content = f.read()
                # Check for known problematic packages
                problematic = ['pickle', 'marshal', 'shelve']
                for pkg in problematic:
                    if pkg in content:
                        issues.append({
                            "type": "unsafe_dependency",
                            "severity": "medium",
                            "file": "requirements.txt",
                            "description": f"Potentially unsafe package: {pkg}",
                            "language": "Python"
                        })
        except:
            pass
    
    return issues

def _check_javascript_security(repo_path: str) -> List[Dict[str, Any]]:
    """Check for JavaScript/TypeScript-specific security issues."""
    issues = []
    
    # Check package.json for known vulnerable packages
    package_file = os.path.join(repo_path, 'package.json')
    if os.path.exists(package_file):
        try:
            import json
            with open(package_file, 'r') as f:
                package_data = json.load(f)
                
                # Check for eval usage (dangerous)
                dependencies = package_data.get('dependencies', {})
                if 'eval' in str(dependencies):
                    issues.append({
                        "type": "dangerous_function",
                        "severity": "high",
                        "file": "package.json",
                        "description": "Usage of eval() function detected",
                        "language": "JavaScript"
                    })
        except:
            pass
    
    # Check for hardcoded secrets in JS/TS files
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for console.log with sensitive data
                        if re.search(r'console\.log.*(?:password|secret|key|token)', content, re.IGNORECASE):
                            issues.append({
                                "type": "information_disclosure",
                                "severity": "medium",
                                "file": os.path.relpath(file_path, repo_path),
                                "description": "Potential sensitive data in console.log",
                                "language": "JavaScript"
                            })
                except:
                    pass
    
    return issues

def _check_java_security(repo_path: str) -> List[Dict[str, Any]]:
    """Check for Java-specific security issues."""
    issues = []
    
    # Check for hardcoded secrets in Java files
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for SQL injection patterns
                        if re.search(r'Statement.*executeQuery.*\+', content):
                            issues.append({
                                "type": "sql_injection",
                                "severity": "high",
                                "file": os.path.relpath(file_path, repo_path),
                                "description": "Potential SQL injection vulnerability",
                                "language": "Java"
                            })
                except:
                    pass
    
    return issues

def _check_go_security(repo_path: str) -> List[Dict[str, Any]]:
    """Check for Go-specific security issues."""
    issues = []
    
    # Note: This is a basic check - the scan_go_vulnerabilities tool provides more comprehensive Go security scanning
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.go'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for unsafe package usage
                        if 'import "unsafe"' in content:
                            issues.append({
                                "type": "unsafe_package",
                                "severity": "medium",
                                "file": os.path.relpath(file_path, repo_path),
                                "description": "Usage of unsafe package",
                                "language": "Go"
                            })
                except:
                    pass
    
    return issues

def _check_general_security(repo_path: str) -> List[Dict[str, Any]]:
    """Check for general security issues across all languages."""
    issues = []
    
    # Check for exposed environment files
    dangerous_files = ['.env', '.env.local', '.env.production', 'config.ini', 'secrets.txt']
    for file in dangerous_files:
        file_path = os.path.join(repo_path, file)
        if os.path.exists(file_path):
            issues.append({
                "type": "exposed_config",
                "severity": "high",
                "file": file,
                "description": f"Sensitive configuration file may be exposed: {file}",
                "language": "General"
            })
    
    # Check for large binary files (potential embedded secrets)
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
                    if file.endswith(('.exe', '.bin', '.so', '.dll')):
                        issues.append({
                            "type": "large_binary",
                            "severity": "low",
                            "file": os.path.relpath(file_path, repo_path),
                            "description": "Large binary file detected - review for embedded secrets",
                            "language": "General"
                        })
            except:
                pass
    
    return issues

def _generate_security_recommendations(issues: List[Dict[str, Any]], language: str) -> List[str]:
    """Generate security recommendations based on found issues."""
    recommendations = []
    
    issue_types = [issue["type"] for issue in issues]
    
    if "hardcoded_secret" in issue_types:
        recommendations.append("Move hardcoded secrets to environment variables or secure configuration")
    
    if "sql_injection" in issue_types:
        recommendations.append("Use parameterized queries to prevent SQL injection")
    
    if "exposed_config" in issue_types:
        recommendations.append("Add sensitive configuration files to .gitignore")
    
    if "unsafe_dependency" in issue_types:
        recommendations.append("Review and update potentially unsafe dependencies")
    
    # Language-specific recommendations
    if language.lower() == "go":
        recommendations.append("Consider using govulncheck for comprehensive Go vulnerability scanning")
    elif language.lower() == "javascript":
        recommendations.append("Consider using npm audit for dependency vulnerability scanning")
    elif language.lower() == "python":
        recommendations.append("Consider using safety or bandit for Python security scanning")
    
    if not recommendations:
        recommendations.append("No major security issues detected in basic audit")
    
    return recommendations

def _calculate_risk_level(issues: List[Dict[str, Any]]) -> str:
    """Calculate overall risk level based on security issues."""
    if not issues:
        return "low"
    
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for issue in issues:
        severity = issue.get("severity", "low")
        severity_counts[severity] += 1
    
    if severity_counts["high"] > 0:
        return "high"
    elif severity_counts["medium"] > 2:
        return "medium-high"
    elif severity_counts["medium"] > 0:
        return "medium"
    else:
        return "low" 