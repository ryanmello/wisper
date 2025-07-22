import os
import json
import re
import time
from langchain_core.tools import tool
from utils.logging_config import get_logger
from utils.tool_metadata_decorator import tool_category
from models.api_models import StandardToolResponse, StandardMetrics, StandardError

logger = get_logger(__name__)

@tool_category("analysis")
@tool
def analyze_dependencies(repository_path: str) -> StandardToolResponse:
    """
    Analyze project dependencies from various manifest files to understand the dependency landscape.
    
    This tool examines dependency files across multiple languages (package.json for Node.js, requirements.txt 
    for Python, go.mod for Go, pom.xml for Java, etc.) to identify external libraries, frameworks, and their 
    versions. This information is valuable for understanding project complexity, potential security risks in 
    dependencies, and technology stack composition.
    
    Prerequisites: Repository must be cloned locally (requires repository_path)
    Provides: Dependency information that security tools can analyze for vulnerabilities
    
    Args:
        repository_path: Path to the cloned repository
        
    Returns:
        StandardToolResponse with dependencies organized by language/ecosystem, versions, and analysis
    """
    start_time = time.time()
    logger.info(f"Analyzing dependencies at {repository_path}")
    
    try:
        dependencies = {}
        files_analyzed = 0
        
        # Python - requirements.txt, setup.py, pyproject.toml
        req_file = os.path.join(repository_path, 'requirements.txt')
        if os.path.exists(req_file):
            files_analyzed += 1
            try:
                with open(req_file, 'r') as f:
                    deps = []
                    for line in f.readlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Extract package name (before ==, >=, ~=, etc.)
                            dep_name = re.split(r'[=<>~!]', line)[0].strip()
                            if dep_name:
                                deps.append(dep_name)
                    dependencies['Python'] = deps[:20]  # Limit for readability
            except Exception as e:
                logger.warning(f"Failed to parse requirements.txt: {e}")
        
        # Node.js - package.json
        package_file = os.path.join(repository_path, 'package.json')
        if os.path.exists(package_file):
            files_analyzed += 1
            try:
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    deps = []
                    if 'dependencies' in package_data:
                        deps.extend(list(package_data['dependencies'].keys()))
                    if 'devDependencies' in package_data:
                        deps.extend(list(package_data['devDependencies'].keys()))
                    dependencies['Node.js'] = deps[:20]
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
        
        # Go - go.mod
        go_mod = os.path.join(repository_path, 'go.mod')
        if os.path.exists(go_mod):
            files_analyzed += 1
            try:
                with open(go_mod, 'r') as f:
                    content = f.read()
                    deps = re.findall(r'require\s+([^\s]+)', content)
                    dependencies['Go'] = deps[:20]
            except Exception as e:
                logger.warning(f"Failed to parse go.mod: {e}")
        
        # Java - pom.xml
        pom_file = os.path.join(repository_path, 'pom.xml')
        if os.path.exists(pom_file):
            files_analyzed += 1
            try:
                with open(pom_file, 'r') as f:
                    content = f.read()
                    deps = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
                    dependencies['Java'] = deps[:20]
            except Exception as e:
                logger.warning(f"Failed to parse pom.xml: {e}")
        
        # Rust - Cargo.toml
        cargo_file = os.path.join(repository_path, 'Cargo.toml')
        if os.path.exists(cargo_file):
            files_analyzed += 1
            try:
                with open(cargo_file, 'r') as f:
                    content = f.read()
                    # Simple regex to find dependencies section
                    deps_match = re.search(r'\[dependencies\](.*?)(?:\[|$)', content, re.DOTALL)
                    if deps_match:
                        deps_section = deps_match.group(1)
                        deps = re.findall(r'^([a-zA-Z0-9_-]+)\s*=', deps_section, re.MULTILINE)
                        dependencies['Rust'] = deps[:20]
            except Exception as e:
                logger.warning(f"Failed to parse Cargo.toml: {e}")
        
        # PHP - composer.json
        composer_file = os.path.join(repository_path, 'composer.json')
        if os.path.exists(composer_file):
            files_analyzed += 1
            try:
                with open(composer_file, 'r') as f:
                    composer_data = json.load(f)
                    deps = []
                    if 'require' in composer_data:
                        deps.extend(list(composer_data['require'].keys()))
                    if 'require-dev' in composer_data:
                        deps.extend(list(composer_data['require-dev'].keys()))
                    dependencies['PHP'] = deps[:20]
            except Exception as e:
                logger.warning(f"Failed to parse composer.json: {e}")
        
        # Ruby - Gemfile
        gemfile = os.path.join(repository_path, 'Gemfile')
        if os.path.exists(gemfile):
            files_analyzed += 1
            try:
                with open(gemfile, 'r') as f:
                    content = f.read()
                    deps = re.findall(r"gem\s+['\"]([^'\"]+)['\"]", content)
                    dependencies['Ruby'] = deps[:20]
            except Exception as e:
                logger.warning(f"Failed to parse Gemfile: {e}")
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        total_dependencies = sum(len(deps) for deps in dependencies.values())
        
        # Build result data
        result_data = {
            "dependencies_by_language": dependencies,
            "total_dependencies": total_dependencies,
            "languages_with_deps": list(dependencies.keys())
        }
        
        # Create summary message
        if total_dependencies > 0:
            summary = f"Found {total_dependencies} dependencies across {len(dependencies)} ecosystems: {', '.join(dependencies.keys())}"
        else:
            summary = "No dependency files found in repository"
        
        logger.info(f"Dependency analysis complete - {total_dependencies} dependencies across {len(dependencies)} languages")
        
        return StandardToolResponse(
            status="success",
            tool_name="analyze_dependencies",
            data=result_data,
            summary=summary,
            metrics=StandardMetrics(
                items_processed=total_dependencies,
                files_analyzed=files_analyzed,
                execution_time_ms=execution_time_ms
            )
        )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to analyze dependencies at {repository_path}: {e}")
        
        return StandardToolResponse(
            status="error",
            tool_name="analyze_dependencies",
            data={
                "dependencies_by_language": {},
                "total_dependencies": 0,
                "languages_with_deps": []
            },
            error=StandardError(
                message=f"Failed to analyze dependencies: {str(e)}",
                details=f"Error occurred while analyzing dependencies at {repository_path}",
                error_type="dependency_analysis_error"
            ),
            summary="Dependency analysis failed",
            metrics=StandardMetrics(
                execution_time_ms=execution_time_ms
            )
        )
