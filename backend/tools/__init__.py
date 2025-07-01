# Tools package for modular analysis tools
# This file will contain imports for all available tools

# Infrastructure tools
from .infrastructure.clone_repository_tool import clone_repository
from .infrastructure.cleanup_repository_tool import cleanup_repository

# Analysis tools  
from .analysis.explore_codebase_tool import explore_codebase
from .analysis.detect_languages_tool import detect_languages
from .analysis.analyze_dependencies_tool import analyze_dependencies
from .analysis.analyze_architecture_tool import analyze_architecture

# Security tools
from .security.scan_go_vulnerabilities_tool import scan_go_vulnerabilities
from .security.security_audit_tool import security_audit

# Git operations tools
from .git_operations.create_pull_request_tool import create_pull_request
from .git_operations.apply_fixes_tool import apply_fixes

# Reporting tools
from .reporting.generate_summary_tool import generate_summary

# Registry of all available tools
ALL_TOOLS = [
    clone_repository,
    cleanup_repository,
    explore_codebase,
    detect_languages,
    analyze_dependencies,
    analyze_architecture,
    scan_go_vulnerabilities,
    security_audit,
    create_pull_request,
    apply_fixes,
    generate_summary
] 