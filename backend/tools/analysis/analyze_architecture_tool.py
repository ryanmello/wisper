"""
Analyze Architecture Tool - Identify architectural patterns and main components
"""

import os
from typing import Dict, List, Any
from pathlib import Path
from langchain_core.tools import tool

from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def analyze_architecture(repository_path: str, language_info: Dict[str, Any]) -> Dict[str, Any]:
    """Identify architectural patterns and main components in the repository based on language and structure.
    
    This tool performs deep architectural analysis by examining directory structure, file organization, and 
    applying language-specific architectural pattern recognition. It works best when provided with language_info 
    from the detect_languages tool, as this enables framework-specific pattern detection (e.g., React component 
    architecture, Django MVT, Spring Framework patterns).
    
    Prerequisites: Repository must be cloned locally; strongly recommended to run detect_languages first
    Enhanced by: language_info from detect_languages tool for framework-specific pattern recognition
    
    Args:
        repository_path: Path to the cloned repository
        language_info: Language detection results from detect_languages tool (for enhanced analysis)
        
    Returns:
        Dictionary with architectural patterns and main components
    """
    logger.info(f"Analyzing architecture patterns at {repository_path}")
    
    try:
        primary_language = language_info.get("primary_language", "Unknown")
        frameworks = language_info.get("frameworks", [])
        
        # Identify architectural patterns
        patterns = []
        
        # Check for common patterns based on directory structure
        dirs = [d for d in os.listdir(repository_path) if os.path.isdir(os.path.join(repository_path, d))]
        files = [f for f in os.listdir(repository_path) if os.path.isfile(os.path.join(repository_path, f))]
        
        # MVC Pattern Detection
        if any(d in ['models', 'views', 'controllers'] for d in dirs):
            patterns.append("MVC (Model-View-Controller)")
        
        # Microservices Pattern
        if any(d in ['services', 'microservices'] for d in dirs) or len([d for d in dirs if 'service' in d.lower()]) > 1:
            patterns.append("Microservices Architecture")
        
        # Domain-Driven Design
        if any(d in ['domain', 'domains', 'entities', 'aggregates'] for d in dirs):
            patterns.append("Domain-Driven Design")
        
        # Clean Architecture / Hexagonal Architecture
        if any(d in ['core', 'infrastructure', 'application', 'adapters'] for d in dirs):
            patterns.append("Clean/Hexagonal Architecture")
        
        # Repository Pattern
        if any('repository' in d.lower() or 'repo' in d.lower() for d in dirs):
            patterns.append("Repository Pattern")
        
        # Plugin Architecture
        if any(d in ['plugins', 'extensions', 'addons'] for d in dirs):
            patterns.append("Plugin Architecture")
        
        # Event-Driven Architecture
        if any(d in ['events', 'handlers', 'listeners'] for d in dirs):
            patterns.append("Event-Driven Architecture")
        
        # API-First Architecture
        if any(d in ['api', 'apis', 'endpoints'] for d in dirs) or any(f in ['openapi.yaml', 'swagger.yaml', 'api.yaml'] for f in files):
            patterns.append("API-First Architecture")
        
        # Extract main components
        components = []
        
        # Analyze directory structure for main components
        for dir_name in dirs:
            if dir_name.startswith('.'):
                continue
                
            dir_path = os.path.join(repository_path, dir_name)
            file_count = sum(len(files) for _, _, files in os.walk(dir_path))
            dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, _, filenames in os.walk(dir_path)
                          for filename in filenames)
            
            # Determine component type based on name and content
            component_type = "module"
            if dir_name.lower() in ['src', 'source', 'lib', 'library']:
                component_type = "source"
            elif dir_name.lower() in ['test', 'tests', 'testing', '__tests__']:
                component_type = "test"
            elif dir_name.lower() in ['docs', 'documentation', 'doc']:
                component_type = "documentation"
            elif dir_name.lower() in ['config', 'configuration', 'settings']:
                component_type = "configuration"
            elif dir_name.lower() in ['api', 'apis', 'routes', 'endpoints']:
                component_type = "api"
            elif dir_name.lower() in ['ui', 'frontend', 'client', 'web']:
                component_type = "frontend"
            elif dir_name.lower() in ['backend', 'server', 'core']:
                component_type = "backend"
            elif dir_name.lower() in ['database', 'db', 'data', 'models']:
                component_type = "data"
            elif dir_name.lower() in ['utils', 'utilities', 'helpers', 'common']:
                component_type = "utility"
            
            components.append({
                "name": dir_name,
                "type": component_type,
                "path": dir_name,
                "file_count": file_count,
                "size_bytes": dir_size
            })
        
        # Sort components by size/importance
        components.sort(key=lambda x: x["file_count"], reverse=True)
        components = components[:10]  # Limit to top 10 components
        
        # Framework-specific patterns
        framework_names = [f["name"] for f in frameworks]
        if "React" in framework_names or "Next.js" in framework_names:
            patterns.append("Component-Based Architecture")
        if "Django" in framework_names:
            patterns.append("Django MVT (Model-View-Template)")
        if "Spring Boot" in framework_names:
            patterns.append("Spring Framework Architecture")
        
        result = {
            "architectural_patterns": patterns,
            "main_components": components,
            "primary_language": primary_language,
            "detected_frameworks": framework_names,
            "total_components": len(components)
        }
        
        logger.info(f"Architecture analysis complete - {len(patterns)} patterns, {len(components)} components")
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze architecture at {repository_path}: {e}")
        return {
            "error": str(e),
            "architectural_patterns": [],
            "main_components": [],
            "primary_language": "Unknown",
            "detected_frameworks": [],
            "total_components": 0
        } 