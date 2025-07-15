import os
import json
import time
from typing import Dict, Any, List
from pathlib import Path
from collections import defaultdict, Counter
from langchain_core.tools import tool

from utils.logging_config import get_logger
from models.api_models import StandardToolResponse, StandardMetrics, StandardError

logger = get_logger(__name__)

@tool
def explore_codebase(repository_path: str) -> StandardToolResponse:
    """
    Comprehensive codebase analysis including language detection, framework identification, architectural analysis, and structural exploration.
    
    This tool provides complete codebase intelligence in a single analysis:
    
    LANGUAGE & FRAMEWORK DETECTION:
    - Identifies all programming languages with usage statistics and confidence scoring
    - Detects frameworks and libraries with comprehensive pattern matching
    - Determines primary language and technology stack
    
    ARCHITECTURAL ANALYSIS:
    - Recognizes architectural patterns (MVC, microservices, clean architecture, etc.)
    - Identifies design patterns and structural organization
    - Analyzes component relationships and system structure
    
    STRUCTURAL EXPLORATION:
    - Complete file structure and organization analysis
    - Directory prioritization and main component identification
    - Entry point detection and configuration file analysis
    - Dependency analysis across multiple ecosystems (Python, Node.js, Go, Rust, Java, etc.)
    
    This consolidated tool replaces the need for separate detect_languages and analyze_architecture tools
    by providing integrated analysis where language detection directly informs architectural insights.
    
    Prerequisites: Repository must be cloned locally (requires repository_path)
    Provides: Complete codebase intelligence for security analysis and summary generation
    
    Args:
        repository_path: Path to the cloned repository
        
    Returns:
        StandardToolResponse containing comprehensive analysis: languages, frameworks, architecture patterns,
        file structure, main components, dependencies, and integrated summary insights
    """
    start_time = time.time()
    logger.info(f"Starting comprehensive codebase exploration at {repository_path}")
    
    try:
        results = {}
        
        # Step 1: Analyze file structure
        logger.info("Analyzing file structure and organization...")
        results['file_structure'] = _analyze_file_structure(repository_path)
        
        # Step 2: Detect languages and frameworks
        logger.info("Detecting languages and frameworks...")
        results['language_analysis'] = _detect_languages_and_frameworks(repository_path)
        
        # Step 3: Identify architectural patterns
        logger.info("Identifying architectural patterns...")
        results['architectural_patterns'] = _identify_architectural_patterns(
            repository_path, results['language_analysis']
        )
        
        # Step 4: Extract main components
        logger.info("Extracting main components and entry points...")
        results['main_components'] = _extract_main_components(
            repository_path, results['language_analysis']
        )
        
        # Step 5: Analyze dependencies
        logger.info("Analyzing project dependencies...")
        results['dependencies'] = _analyze_dependencies(repository_path)
        
        # Step 6: Generate summary insights
        results['summary'] = _generate_summary_insights(results)
        
        # Calculate execution time and metrics
        execution_time_ms = int((time.time() - start_time) * 1000)
        total_files = results['file_structure'].get('total_files', 0)
        total_lines = results['file_structure'].get('total_lines', 0)
        languages_count = len(results['language_analysis'].get('languages', {}))
        
        # Create summary message
        primary_lang = results['language_analysis'].get('primary_language', 'Unknown')
        frameworks_count = len(results['language_analysis'].get('frameworks', []))
        patterns_count = len(results['architectural_patterns'])
        
        summary = f"Analyzed {total_files} files ({total_lines:,} lines) in {primary_lang} with {languages_count} languages, {frameworks_count} frameworks, and {patterns_count} architectural patterns detected"
        
        logger.info(f"Codebase exploration complete - {total_files} files analyzed")
        
        return StandardToolResponse(
            status="success",
            tool_name="explore_codebase",
            data=results,
            summary=summary,
            metrics=StandardMetrics(
                items_processed=total_files,
                files_analyzed=total_files,
                execution_time_ms=execution_time_ms
            )
        )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to explore codebase at {repository_path}: {e}")
        
        # Create fallback data structure
        fallback_data = {
            "file_structure": {"total_files": 0, "total_lines": 0, "file_types": {}, "main_directories": []},
            "language_analysis": {"primary_language": "Unknown", "languages": {}, "frameworks": []},
            "architectural_patterns": [],
            "main_components": [],
            "dependencies": {},
            "summary": "Analysis failed due to error"
        }
        
        return StandardToolResponse(
            status="error",
            tool_name="explore_codebase",
            data=fallback_data,
            error=StandardError(
                message=f"Failed to explore codebase: {str(e)}",
                details=f"Error occurred while analyzing codebase at {repository_path}",
                error_type="codebase_exploration_error"
            ),
            summary="Codebase exploration failed",
            metrics=StandardMetrics(
                execution_time_ms=execution_time_ms
            )
        )


def _analyze_file_structure(root_path: str) -> Dict[str, Any]:
    """Analyze repository file structure with smart directory prioritization."""
    file_stats = {
        'total_files': 0,
        'total_lines': 0,
        'file_types': {},
        'directory_structure': {},
        'main_directories': [],
        'largest_files': [],
        'important_directories': []
    }
    
    # Important directories to track and prioritize
    important_dirs = {
        'src', 'lib', 'app', 'components', 'pages', 'api', 'services',
        'models', 'controllers', 'views', 'tests', 'test', '__tests__',
        'docs', 'documentation', 'config', 'scripts', 'utils', 'helpers',
        'routes', 'middleware', 'database', 'migrations', 'public', 'static'
    }
    
    # Directories to skip for analysis
    skip_dirs = {
        '.git', '__pycache__', 'node_modules', '.next', 'dist', 'build',
        '.vscode', '.idea', 'coverage', '.pytest_cache', 'venv', 'env',
        'target', 'out', '.svn', 'vendor', 'bower_components'
    }
    
    file_type_counter = Counter()
    directory_files = defaultdict(list)
    
    try:
        for root, dirs, files in os.walk(root_path):
            # Filter out directories we want to skip
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            relative_root = os.path.relpath(root, root_path)
            if relative_root == '.':
                relative_root = 'root'
            
            # Track important directories
            for dir_part in relative_root.split(os.sep):
                if dir_part.lower() in important_dirs:
                    if dir_part not in file_stats['important_directories']:
                        file_stats['important_directories'].append(dir_part)
                    if dir_part not in file_stats['main_directories']:
                        file_stats['main_directories'].append(dir_part)
            
            for file in files:
                # Skip hidden files except important ones
                if file.startswith('.') and file not in ['.env', '.env.example', '.gitignore', '.dockerignore']:
                    continue
                    
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                file_stats['total_files'] += 1
                file_type_counter[file_ext] += 1
                directory_files[relative_root].append(file)
                
                # Count lines for code files and track largest files
                code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php', '.swift', '.kt'}
                if file_ext in code_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            file_stats['total_lines'] += lines
                            
                            # Track largest files
                            relative_path = os.path.relpath(file_path, root_path)
                            file_stats['largest_files'].append({
                                'path': relative_path,
                                'lines': lines,
                                'size': os.path.getsize(file_path),
                                'extension': file_ext
                            })
                    except:
                        pass
        
        # Sort and limit largest files
        file_stats['largest_files'].sort(key=lambda x: x['lines'], reverse=True)
        file_stats['largest_files'] = file_stats['largest_files'][:10]
        
        # Convert counters to dictionaries
        file_stats['file_types'] = dict(file_type_counter.most_common())
        file_stats['directory_structure'] = dict(directory_files)
        
    except Exception as e:
        logger.error(f"Failed to analyze file structure: {e}")
    
    return file_stats


def _detect_languages_and_frameworks(root_path: str) -> Dict[str, Any]:
    """Detect programming languages and frameworks with confidence scoring."""
    language_analysis = {
        'languages': {},
        'primary_language': 'Unknown',
        'frameworks': [],
        'total_code_files': 0,
        'confidence_scores': {}
    }
    
    # Language extensions mapping
    language_extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'TypeScript React',
        '.go': 'Go',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c': 'C',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.cs': 'C#',
        '.vue': 'Vue.js',
        '.dart': 'Dart',
        '.elm': 'Elm'
    }
    
    # Framework indicators with their detection files/patterns
    framework_indicators = {
        'React': ['package.json', 'src/App.js', 'src/App.tsx', 'public/index.html', 'src/index.js'],
        'Next.js': ['next.config.js', 'pages/', 'app/', 'next.config.ts', '_app.js'],
        'Vue.js': ['vue.config.js', 'src/main.js', 'src/App.vue', 'nuxt.config.js'],
        'Angular': ['angular.json', 'src/app/', 'ng-package.json', 'angular.cli.json'],
        'Django': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py', 'asgi.py'],
        'Flask': ['app.py', 'requirements.txt', 'templates/', 'run.py'],
        'FastAPI': ['main.py', 'requirements.txt', 'app/', 'uvicorn'],
        'Spring Boot': ['pom.xml', 'application.properties', 'src/main/java/', 'application.yml'],
        'Express.js': ['package.json', 'server.js', 'app.js', 'index.js'],
        'Laravel': ['composer.json', 'artisan', 'app/Http/', 'routes/web.php'],
        'Rails': ['Gemfile', 'config/routes.rb', 'app/controllers/', 'config/application.rb'],
        'Go Gin': ['go.mod', 'main.go', 'gin'],
        'Rust Actix': ['Cargo.toml', 'src/main.rs', 'actix-web'],
        'ASP.NET Core': ['*.csproj', 'Program.cs', 'Startup.cs', 'appsettings.json'],
        'Svelte': ['svelte.config.js', 'src/App.svelte', 'package.json'],
        'Nuxt.js': ['nuxt.config.js', 'pages/', 'layouts/', 'components/']
    }
    
    language_counts = Counter()
    
    try:
        # Count files by language
        for root, dirs, files in os.walk(root_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'venv', 'env', 'dist', 'build', 'target'
            ]]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in language_extensions:
                    language = language_extensions[ext]
                    language_counts[language] += 1
                    language_analysis['total_code_files'] += 1
        
        # Convert to detailed language info
        total_files = sum(language_counts.values())
        if total_files > 0:
            for lang, count in language_counts.items():
                percentage = round((count / total_files) * 100, 1)
                language_analysis['languages'][lang] = {
                    'files': count,
                    'percentage': percentage
                }
            
            # Determine primary language
            language_analysis['primary_language'] = language_counts.most_common(1)[0][0]
        
        # Detect frameworks with confidence scoring
        detected_frameworks = []
        for framework, indicators in framework_indicators.items():
            framework_score = 0
            found_indicators = []
            
            for indicator in indicators:
                indicator_path = os.path.join(root_path, indicator)
                if os.path.exists(indicator_path):
                    framework_score += 1
                    found_indicators.append(indicator)
                elif '/' not in indicator:
                    # Check for files anywhere in the project
                    for root, dirs, files in os.walk(root_path):
                        if indicator in files:
                            framework_score += 0.5  # Lower score for files not in root
                            found_indicators.append(f"found: {indicator}")
                            break
            
            # Calculate confidence
            confidence = framework_score / len(indicators)
            
            # Include framework if confidence is above threshold
            if confidence >= 0.3:  # Lower threshold for more inclusive detection
                detected_frameworks.append({
                    'name': framework,
                    'confidence': round(confidence, 2),
                    'indicators_found': len(found_indicators),
                    'total_indicators': len(indicators),
                    'found_files': found_indicators[:5]  # Limit to first 5 for brevity
                })
        
        # Sort frameworks by confidence
        language_analysis['frameworks'] = sorted(detected_frameworks, key=lambda x: x['confidence'], reverse=True)
        
    except Exception as e:
        logger.error(f"Failed to detect languages and frameworks: {e}")
    
    return language_analysis


def _identify_architectural_patterns(root_path: str, language_info: Dict) -> List[str]:
    """Identify architectural patterns based on directory structure and files."""
    patterns = []
    
    try:
        # Collect all directory names
        dirs = set()
        files = set()
        
        for root, subdirs, file_list in os.walk(root_path):
            for subdir in subdirs:
                if not subdir.startswith('.'):
                    dirs.add(subdir.lower())
            for file in file_list:
                if not file.startswith('.'):
                    files.add(file.lower())
        
        # MVC Pattern
        mvc_indicators = ['models', 'views', 'controllers']
        if sum(1 for indicator in mvc_indicators if indicator in dirs) >= 2:
            patterns.append("MVC (Model-View-Controller)")
        
        # Microservices/Service-oriented
        if any(d in dirs for d in ['services', 'microservices']) or \
           any(f in files for f in ['docker-compose.yml', 'dockerfile']):
            patterns.append("Microservices Architecture")
        
        # Component-based (React, Vue, Angular)
        if any(d in dirs for d in ['components', 'widgets']) or \
           any(fw['name'] in ['React', 'Vue.js', 'Angular'] for fw in language_info.get('frameworks', [])):
            patterns.append("Component-Based Architecture")
        
        # Layered Architecture
        layer_indicators = ['business', 'data', 'presentation', 'domain', 'application']
        if sum(1 for indicator in layer_indicators if indicator in dirs) >= 2:
            patterns.append("Layered Architecture")
        
        # Clean Architecture
        clean_indicators = ['entities', 'usecases', 'repositories', 'adapters']
        if sum(1 for indicator in clean_indicators if indicator in dirs) >= 2:
            patterns.append("Clean Architecture")
        
        # API-first
        if any(d in dirs for d in ['api', 'endpoints', 'routes']) or \
           any(f in files for f in ['openapi.yaml', 'swagger.json', 'api.yaml']):
            patterns.append("API-First Design")
        
        # Plugin/Extension architecture
        if any(d in dirs for d in ['plugins', 'extensions', 'addons', 'modules']):
            patterns.append("Plugin Architecture")
        
        # Event-driven
        if any(d in dirs for d in ['events', 'handlers', 'listeners', 'queues']):
            patterns.append("Event-Driven Architecture")
        
        # Monorepo
        if any(f in files for f in ['lerna.json', 'nx.json', 'rush.json']) or \
           len([d for d in dirs if d in ['packages', 'apps', 'libs']]) >= 2:
            patterns.append("Monorepo Structure")
        
        # Serverless
        if any(f in files for f in ['serverless.yml', 'serverless.yaml', 'sam.yaml', 'template.yaml']):
            patterns.append("Serverless Architecture")
        
    except Exception as e:
        logger.error(f"Failed to identify architectural patterns: {e}")
    
    return patterns


def _extract_main_components(root_path: str, language_info: Dict) -> List[Dict[str, Any]]:
    """Extract main components, entry points, and important files."""
    components = []
    
    try:
        # Main application entry points
        entry_points = [
            'main.py', 'app.py', '__main__.py', 'run.py', 'wsgi.py', 'asgi.py',
            'main.go', 'main.java', 'Main.java', 'Program.cs', 'main.rs',
            'index.js', 'app.js', 'server.js', 'main.ts', 'app.ts', 'index.ts',
            'manage.py', 'artisan', 'gulpfile.js', 'webpack.config.js'
        ]
        
        for entry_file in entry_points:
            entry_path = os.path.join(root_path, entry_file)
            if os.path.exists(entry_path):
                try:
                    size = os.path.getsize(entry_path)
                    with open(entry_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                    
                    components.append({
                        'name': entry_file,
                        'type': 'Entry Point',
                        'path': entry_file,
                        'size': size,
                        'lines': lines,
                        'description': f"Main application entry point ({entry_file})"
                    })
                except:
                    pass
        
        # Important directories
        important_dirs = {
            'src': 'Source Code Directory',
            'lib': 'Library Directory',
            'app': 'Application Directory',
            'api': 'API Directory',
            'services': 'Services Directory',
            'components': 'Components Directory',
            'models': 'Data Models Directory',
            'controllers': 'Controllers Directory',
            'routes': 'Routes Directory',
            'middleware': 'Middleware Directory',
            'config': 'Configuration Directory',
            'tests': 'Tests Directory',
            'docs': 'Documentation Directory'
        }
        
        for root, dirs, files in os.walk(root_path):
            if root == root_path:  # Only check top level
                for dir_name in dirs:
                    if dir_name.lower() in important_dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            # Count files in directory
                            file_count = 0
                            for _, _, dir_files in os.walk(dir_path):
                                file_count += len(dir_files)
                            
                            components.append({
                                'name': dir_name,
                                'type': 'Directory',
                                'path': dir_name + '/',
                                'file_count': file_count,
                                'description': important_dirs[dir_name.lower()]
                            })
                        except:
                            pass
        
        # Configuration files
        config_files = {
            'package.json': 'Node.js Package Configuration',
            'requirements.txt': 'Python Dependencies',
            'go.mod': 'Go Module Configuration',
            'Cargo.toml': 'Rust Package Configuration',
            'pom.xml': 'Maven Project Configuration',
            'build.gradle': 'Gradle Build Configuration',
            'composer.json': 'PHP Composer Configuration',
            'Gemfile': 'Ruby Gems Configuration',
            'Dockerfile': 'Docker Container Configuration',
            'docker-compose.yml': 'Docker Compose Configuration',
            '.env': 'Environment Variables',
            'config.yaml': 'Application Configuration',
            'config.json': 'JSON Configuration',
            'tsconfig.json': 'TypeScript Configuration',
            'webpack.config.js': 'Webpack Build Configuration',
            'next.config.js': 'Next.js Configuration',
            'vue.config.js': 'Vue.js Configuration',
            'angular.json': 'Angular Configuration'
        }
        
        for config_file, description in config_files.items():
            config_path = os.path.join(root_path, config_file)
            if os.path.exists(config_path):
                try:
                    size = os.path.getsize(config_path)
                    components.append({
                        'name': config_file,
                        'type': 'Configuration',
                        'path': config_file,
                        'size': size,
                        'description': description
                    })
                except:
                    pass
        
        # Sort components by type and importance
        type_priority = {'Entry Point': 1, 'Directory': 2, 'Configuration': 3}
        components.sort(key=lambda x: (type_priority.get(x['type'], 4), x['name']))
        
    except Exception as e:
        logger.error(f"Failed to extract main components: {e}")
    
    return components


def _analyze_dependencies(root_path: str) -> Dict[str, Any]:
    """Analyze project dependencies across multiple ecosystems."""
    dependencies = {}
    
    try:
        # Python dependencies
        req_files = ['requirements.txt', 'requirements-dev.txt', 'Pipfile', 'pyproject.toml']
        for req_file in req_files:
            req_path = os.path.join(root_path, req_file)
            if os.path.exists(req_path):
                try:
                    with open(req_path, 'r', encoding='utf-8') as f:
                        deps = []
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and not line.startswith('-'):
                                # Extract package name
                                pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
                                deps.append(pkg.strip())
                        if deps:
                            dependencies['Python'] = {
                                'file': req_file,
                                'dependencies': deps[:20],  # Limit to first 20
                                'total_count': len(deps)
                            }
                            break
                except:
                    pass
        
        # Node.js dependencies
        package_path = os.path.join(root_path, 'package.json')
        if os.path.exists(package_path):
            try:
                with open(package_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prod_deps = list(data.get('dependencies', {}).keys())
                    dev_deps = list(data.get('devDependencies', {}).keys())
                    all_deps = prod_deps + dev_deps
                    
                    dependencies['Node.js'] = {
                        'file': 'package.json',
                        'dependencies': all_deps[:20],
                        'production_deps': len(prod_deps),
                        'dev_deps': len(dev_deps),
                        'total_count': len(all_deps)
                    }
            except:
                pass
        
        # Go dependencies
        go_mod_path = os.path.join(root_path, 'go.mod')
        if os.path.exists(go_mod_path):
            try:
                with open(go_mod_path, 'r', encoding='utf-8') as f:
                    deps = []
                    in_require_block = False
                    for line in f:
                        line = line.strip()
                        if line.startswith('require ('):
                            in_require_block = True
                            continue
                        elif line == ')' and in_require_block:
                            in_require_block = False
                            continue
                        elif in_require_block or line.startswith('require '):
                            parts = line.split()
                            if len(parts) >= 2 and not parts[0].startswith('//'):
                                module = parts[0] if in_require_block else parts[1]
                                deps.append(module)
                    
                    dependencies['Go'] = {
                        'file': 'go.mod',
                        'dependencies': deps[:20],
                        'total_count': len(deps)
                    }
            except:
                pass
        
        # Rust dependencies
        cargo_path = os.path.join(root_path, 'Cargo.toml')
        if os.path.exists(cargo_path):
            try:
                with open(cargo_path, 'r', encoding='utf-8') as f:
                    deps = []
                    in_dependencies = False
                    for line in f:
                        line = line.strip()
                        if line == '[dependencies]':
                            in_dependencies = True
                            continue
                        elif line.startswith('[') and in_dependencies:
                            in_dependencies = False
                            continue
                        elif in_dependencies and '=' in line:
                            dep_name = line.split('=')[0].strip()
                            deps.append(dep_name)
                    
                    dependencies['Rust'] = {
                        'file': 'Cargo.toml',
                        'dependencies': deps[:20],
                        'total_count': len(deps)
                    }
            except:
                pass
        
        # Java Maven dependencies
        pom_path = os.path.join(root_path, 'pom.xml')
        if os.path.exists(pom_path):
            try:
                # Simple XML parsing for Maven dependencies
                with open(pom_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract artifactId values (simplified)
                    import re
                    artifacts = re.findall(r'<artifactId>(.*?)</artifactId>', content)
                    
                    dependencies['Java Maven'] = {
                        'file': 'pom.xml',
                        'dependencies': artifacts[:20],
                        'total_count': len(artifacts)
                    }
            except:
                pass
        
    except Exception as e:
        logger.error(f"Failed to analyze dependencies: {e}")
    
    return dependencies


def _generate_summary_insights(results: Dict[str, Any]) -> str:
    """Generate summary insights from the comprehensive analysis."""
    try:
        file_structure = results.get('file_structure', {})
        language_analysis = results.get('language_analysis', {})
        patterns = results.get('architectural_patterns', [])
        components = results.get('main_components', [])
        dependencies = results.get('dependencies', {})
        
        insights = []
        
        # File structure insights
        total_files = file_structure.get('total_files', 0)
        total_lines = file_structure.get('total_lines', 0)
        insights.append(f"Repository contains {total_files} files with {total_lines:,} lines of code")
        
        # Language insights
        primary_lang = language_analysis.get('primary_language', 'Unknown')
        lang_count = len(language_analysis.get('languages', {}))
        insights.append(f"Primary language is {primary_lang} with {lang_count} languages detected")
        
        # Framework insights
        frameworks = language_analysis.get('frameworks', [])
        if frameworks:
            top_framework = frameworks[0]['name']
            confidence = frameworks[0]['confidence']
            insights.append(f"Main framework appears to be {top_framework} (confidence: {confidence})")
        
        # Architecture insights
        if patterns:
            insights.append(f"Architectural patterns: {', '.join(patterns)}")
        
        # Component insights
        entry_points = [c for c in components if c.get('type') == 'Entry Point']
        if entry_points:
            insights.append(f"Entry points found: {', '.join([c['name'] for c in entry_points])}")
        
        # Dependency insights
        if dependencies:
            ecosystems = list(dependencies.keys())
            total_deps = sum(dep.get('total_count', 0) for dep in dependencies.values())
            insights.append(f"Dependencies managed across {len(ecosystems)} ecosystems ({total_deps} total)")
        
        return " | ".join(insights)
        
    except Exception as e:
        logger.error(f"Failed to generate summary insights: {e}")
        return "Summary generation failed" 
