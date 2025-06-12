"""
Dependency Audit Agent - Security scanning, vulnerability detection, and automated fixing
"""

import os
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List

logger = logging.getLogger(__name__)

class DependencyAuditAgent:
    """Agent specialized in dependency auditing, security scanning, and vulnerability fixes."""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.temp_dir = None
    
    async def _scan_vulnerabilities(self, clone_path: str, repository_url: str = "") -> Optional[Dict[str, Any]]:
        """Scan for security vulnerabilities in the repository."""
        logger.info(f"Starting vulnerability scan for path: {clone_path}")
        
        try:
            from tools.security.go_vulnerability_tool import GoVulnerabilityTool
            from tools.base_tool import AnalysisContext
        except ImportError as e:
            logger.warning(f"Vulnerability scanning not available: {e}")
            return None
        
        # Check if this is a Go project
        go_mod_path = os.path.join(clone_path, "go.mod")
        logger.info(f"Checking for go.mod at: {go_mod_path}")
        
        if not os.path.exists(go_mod_path):
            logger.info("No go.mod found, skipping vulnerability scan")
            return None
        
        logger.info("go.mod found, proceeding with vulnerability scan")
        
        try:
            # Create analysis context for vulnerability scanning
            context = AnalysisContext(
                repository_path=clone_path,
                repository_url=repository_url,
                target_languages=["go"],
                intent="security_audit",
                additional_params={}
            )
            
            # Initialize and run vulnerability tool
            vuln_tool = GoVulnerabilityTool()
            logger.info("Initialized GoVulnerabilityTool")
            
            # Validate context
            is_valid, errors = vuln_tool.validate_context(context)
            if not is_valid:
                logger.warning(f"Context validation failed: {errors}")
                return None
            
            logger.info("Context validation passed, running vulnerability scan")
            
            # Run vulnerability scan
            result = await vuln_tool.execute(context)
            
            if result.success:
                logger.info(f"Vulnerability scan successful: {result.results.get('scan_summary', {})}")
                return result.results
            else:
                logger.warning(f"Vulnerability scan failed: {result.errors}")
                return None
                
        except Exception as e:
            logger.error(f"Vulnerability scanning failed: {e}")
            return None

    def analyze_dependencies(self, root_path: str) -> Dict[str, List[str]]:
        """Analyze project dependencies from various manifest files."""
        dependencies = {}
        
        # Python - requirements.txt, setup.py, pyproject.toml
        req_file = os.path.join(root_path, 'requirements.txt')
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r') as f:
                    deps = [line.strip().split('==')[0].split('>=')[0].split('~=')[0] 
                           for line in f.readlines() 
                           if line.strip() and not line.startswith('#')]
                    dependencies['Python'] = deps[:20]  # Limit for readability
            except:
                pass
        
        # Node.js - package.json
        import json
        package_file = os.path.join(root_path, 'package.json')
        if os.path.exists(package_file):
            try:
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    deps = []
                    if 'dependencies' in package_data:
                        deps.extend(list(package_data['dependencies'].keys()))
                    if 'devDependencies' in package_data:
                        deps.extend(list(package_data['devDependencies'].keys()))
                    dependencies['Node.js'] = deps[:20]
            except:
                pass
        
        # Go - go.mod
        import re
        go_mod = os.path.join(root_path, 'go.mod')
        if os.path.exists(go_mod):
            try:
                with open(go_mod, 'r') as f:
                    content = f.read()
                    deps = re.findall(r'require\s+([^\s]+)', content)
                    dependencies['Go'] = deps[:20]
            except:
                pass
        
        # Java - pom.xml
        pom_file = os.path.join(root_path, 'pom.xml')
        if os.path.exists(pom_file):
            try:
                with open(pom_file, 'r') as f:
                    content = f.read()
                    deps = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
                    dependencies['Java'] = deps[:20]
            except:
                pass
        
        return dependencies

    async def analyze_repository(self, repository_url: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Specialized dependency audit workflow that scans for vulnerabilities and creates PRs.
        
        Args:
            repository_url: GitHub repository URL
            
        Yields:
            Progress updates and results including PR information
        """
        logger.info(f"Starting dependency audit for repository: {repository_url}")
        
        # Clone repository
        yield {
            "type": "progress",
            "current_step": "Cloning repository for dependency audit...",
            "progress": 10.0
        }
        
        from services.repository_service import repository_service
        clone_result = repository_service.clone_repository(repository_url)
        if clone_result["status"] != "success":
            yield {
                "type": "error", 
                "error": f"Failed to clone repository: {clone_result.get('error', 'Unknown error')}"
            }
            return

        clone_path = clone_result["clone_path"]
        logger.info(f"Successfully cloned repository to: {clone_path}")
        
        # Debug: Check what files exist in the cloned repository
        if os.path.exists(clone_path):
            try:
                files = os.listdir(clone_path)
                logger.info(f"Repository contains {len(files)} items: {files[:10]}...")  # Show first 10 items
                go_mod_exists = os.path.exists(os.path.join(clone_path, "go.mod"))
                logger.info(f"go.mod exists: {go_mod_exists}")
            except Exception as e:
                logger.warning(f"Could not list repository contents: {e}")
        else:
            logger.error(f"Clone path does not exist: {clone_path}")
        
        try:
            # Basic repository analysis
            yield {
                "type": "progress",
                "current_step": "Analyzing repository structure...",
                "progress": 20.0
            }
            
            dependencies = self.analyze_dependencies(clone_path)
            primary_language = repository_service.detect_primary_language(clone_path)
            
            # Vulnerability scanning
            yield {
                "type": "progress",
                "current_step": "Scanning for security vulnerabilities...",
                "progress": 50.0
            }
            
            vulnerability_results = await self._scan_vulnerabilities(clone_path, repository_url)
            
            if not vulnerability_results:
                yield {
                    "type": "completed",
                    "results": {
                        "repository_url": repository_url,
                        "primary_language": primary_language,
                        "dependencies": dependencies,
                        "vulnerability_scan": {
                            "status": "skipped",
                            "reason": "No Go project detected or scanner unavailable"
                        },
                        "summary": "Dependency audit completed - no vulnerabilities to scan"
                    }
                }
                return
            
            vulnerabilities_found = vulnerability_results.get("scan_summary", {}).get("vulnerabilities_found", 0)
            
            if vulnerabilities_found == 0:
                yield {
                    "type": "completed",
                    "results": {
                        "repository_url": repository_url,
                        "primary_language": primary_language,
                        "dependencies": dependencies,
                        "vulnerability_scan": vulnerability_results,
                        "github_pr": {
                            "success": True,
                            "action": "none_needed",
                            "message": "No vulnerabilities found - no PR needed",
                            "vulnerabilities_fixed": 0
                        },
                        "summary": "Dependency audit completed - no vulnerabilities found"
                    }
                }
                return
            
            # Vulnerabilities found - create PR automatically
            yield {
                "type": "progress",
                "current_step": f"Found {vulnerabilities_found} vulnerabilities - creating fix PR...",
                "progress": 80.0
            }
            
            try:
                from services.github_service import github_service
                pr_result = github_service.create_security_pr(
                    repository_url, 
                    vulnerability_results
                )
                
                # Convert PRCreationResult to dictionary format
                pr_dict = {
                    "success": pr_result.success,
                    "pr_url": pr_result.pr_url,
                    "pr_number": pr_result.pr_number,
                    "branch_name": pr_result.branch_name,
                    "files_changed": pr_result.files_changed,
                    "vulnerabilities_fixed": pr_result.vulnerabilities_fixed,
                    "error": pr_result.error_message
                }
                
                yield {
                    "type": "completed",
                    "results": {
                        "repository_url": repository_url,
                        "primary_language": primary_language,
                        "dependencies": dependencies,
                        "vulnerability_scan": vulnerability_results,
                        "github_pr": pr_dict,
                        "summary": f"Dependency audit completed - {vulnerabilities_found} vulnerabilities found and PR created"
                    }
                }
                
            except Exception as e:
                yield {
                    "type": "error",
                    "error": f"Failed to create security PR: {str(e)}",
                    "results": {
                        "repository_url": repository_url,
                        "primary_language": primary_language,
                        "dependencies": dependencies,
                        "vulnerability_scan": vulnerability_results,
                        "summary": f"Dependency audit completed - {vulnerabilities_found} vulnerabilities found but PR creation failed"
                    }
                }
                
        except Exception as e:
            logger.error(f"Dependency audit failed: {e}")
            yield {
                "type": "error",
                "error": f"Dependency audit failed: {str(e)}"
            }
        finally:
            # Cleanup
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                cleanup_success = repository_service.cleanup_directory(self.temp_dir)
                if not cleanup_success:
                    repository_service.schedule_delayed_cleanup(self.temp_dir)
                self.temp_dir = None 
