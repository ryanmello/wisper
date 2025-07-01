"""
Detect Languages Tool - Identify programming languages and frameworks used in repository
"""

import os
import json
from typing import Dict, Any
from pathlib import Path
from collections import Counter
from langchain_core.tools import tool

from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def detect_languages(repository_path: str) -> Dict[str, Any]:
    """Detect programming languages and frameworks used in the repository.
    
    This tool analyzes the repository to identify the primary programming languages, frameworks, and technologies 
    being used. The results provide valuable context for other analysis tools - for example, the analyze_architecture 
    tool uses this language information to provide language-specific architectural insights, and security tools 
    can focus on language-specific vulnerabilities.
    
    Prerequisites: Repository must be cloned locally (requires repository_path)
    Provides: language_info that other tools (especially analyze_architecture) can use for enhanced analysis
    
    Args:
        repository_path: Path to the cloned repository
        
    Returns:
        Dictionary with primary_language, frameworks, file_analysis, and language statistics
    """
    logger.info(f"Detecting languages and frameworks at {repository_path}")
    
    try:
        # Language detection by file extension
        languages = Counter()
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.jsx': 'React JSX', '.tsx': 'TypeScript React',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C',
            '.go': 'Go', '.rs': 'Rust', '.php': 'PHP',
            '.rb': 'Ruby', '.swift': 'Swift', '.kt': 'Kotlin',
            '.cs': 'C#', '.scala': 'Scala', '.clj': 'Clojure'
        }
        
        # Framework indicators
        framework_indicators = {
            'React': ['package.json', 'src/App.js', 'src/App.tsx', 'public/index.html'],
            'Next.js': ['next.config.js', 'pages/', 'app/', 'next.config.ts'],
            'Vue.js': ['vue.config.js', 'src/main.js', 'src/App.vue'],
            'Angular': ['angular.json', 'src/app/', 'ng-package.json'],
            'Django': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
            'Flask': ['app.py', 'requirements.txt', 'templates/'],
            'FastAPI': ['main.py', 'requirements.txt', 'app/'],
            'Spring Boot': ['pom.xml', 'application.properties', 'src/main/java/'],
            'Express.js': ['package.json', 'server.js', 'app.js'],
            'Laravel': ['composer.json', 'artisan', 'app/Http/'],
            'Rails': ['Gemfile', 'config/routes.rb', 'app/controllers/']
        }
        
        # Count language files
        for root, dirs, files in os.walk(repository_path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in language_map:
                    languages[language_map[ext]] += 1
        
        # Detect frameworks
        frameworks = []
        for framework, indicators in framework_indicators.items():
            score = 0
            for indicator in indicators:
                indicator_path = os.path.join(repository_path, indicator)
                if os.path.exists(indicator_path):
                    score += 1
            
            if score >= len(indicators) * 0.5:
                frameworks.append({
                    "name": framework,
                    "confidence": score / len(indicators),
                    "indicators_found": score
                })
        
        result = {
            "languages": dict(languages.most_common()),
            "primary_language": languages.most_common(1)[0][0] if languages else "Unknown",
            "frameworks": sorted(frameworks, key=lambda x: x['confidence'], reverse=True),
            "total_code_files": sum(languages.values()),
            # Tool metadata for result compilation
            "_tool_metadata": {
                "category": "analysis",
                "result_type": "language_detection",
                "output_keys": ["languages", "primary_language", "frameworks", "total_code_files"],
                "priority": 2
            }
        }
        
        logger.info(f"Language detection complete - Primary: {result['primary_language']}, {len(frameworks)} frameworks detected")
        return result
        
    except Exception as e:
        logger.error(f"Failed to detect languages at {repository_path}: {e}")
        return {
            "error": str(e),
            "languages": {},
            "primary_language": "Unknown",
            "frameworks": [],
            "total_code_files": 0,
            "_tool_metadata": {
                "category": "analysis",
                "result_type": "language_detection",
                "output_keys": [],
                "priority": 2
            }
        } 