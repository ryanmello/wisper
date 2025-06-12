"""
Codebase Explorer Tool - Comprehensive codebase analysis and exploration.

This tool performs deep analysis of repository structure, architecture patterns,
language detection, and component identification.
"""

import os
import time
from typing import Dict, List, Any
from pathlib import Path
from collections import defaultdict, Counter

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from tools.base_tool import BaseTool, ToolResult, ToolMetadata, ToolCapability, AnalysisContext
from utils.logging_config import get_logger

logger = get_logger(__name__)


class CodebaseExplorerTool(BaseTool):
    """
    Tool for comprehensive codebase exploration and architecture analysis.
    
    This tool analyzes repository structure, detects languages and frameworks,
    identifies architectural patterns, and extracts main components.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize OpenAI client (will be set during execution)
        self.llm = None
        
        # Configuration files for different ecosystems
        self.config_files = {
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 
            'pom.xml', 'build.gradle', 'composer.json', 'Gemfile'
        }
        
        # Framework indicators
        self.framework_indicators = {
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
    
    def _create_metadata(self) -> ToolMetadata:
        """Create metadata for the codebase explorer tool."""
        return ToolMetadata(
            name="codebase_explorer",
            description="Comprehensive codebase analysis including structure, architecture, and component identification",
            version="1.0.0",
            capabilities=[
                ToolCapability.CODEBASE_EXPLORATION,
                ToolCapability.ARCHITECTURE_REVIEW,
                ToolCapability.DEPENDENCY_ANALYSIS
            ],
            supported_languages=[
                "python", "javascript", "typescript", "go", "java", "rust", 
                "c++", "c", "php", "ruby", "swift", "kotlin"
            ],
            required_files=[],  # Can work with any repository
            optional_files=[
                "package.json", "requirements.txt", "go.mod", "Cargo.toml",
                "pom.xml", "build.gradle", "composer.json", "Gemfile"
            ],
            execution_time_estimate="1-2 minutes",
            dependencies=["langchain-openai", "GitPython"]
        )
    
    def validate_context(self, context: AnalysisContext) -> tuple[bool, List[str]]:
        """Validate that the context is suitable for codebase exploration."""
        errors = []
        
        # Check if repository path exists
        if not context.repository_path or not Path(context.repository_path).exists():
            errors.append("Repository path does not exist or is not provided")
        
        # Check if intent is compatible with codebase exploration
        compatible_intents = ["explore", "analyze", "review", "understand"]
        exploration_keywords = ["explore", "analyze", "review", "understand", "architecture", "overview", "structure"]
        
        # Check for pure security intents that should not trigger codebase exploration
        security_only_intents = ["find_vulnerabilities", "security_audit", "security"]
        security_keywords = ["vulnerability", "vulnerabilities", "security", "cve", "exploit", "attack", "threat"]
        
        # Get original context for multi-intent analysis
        original_context = context.additional_params.get('original_context', '').lower()
        
        # If this is a pure security request without exploration keywords, reject it
        if context.intent in security_only_intents:
            # Only allow if the request explicitly mentions exploration/architecture alongside security
            if not any(keyword in original_context for keyword in exploration_keywords):
                errors.append(f"Tool not suitable for pure security intent '{context.intent}' - requires exploration context")
                logger.info(f"Rejecting pure security intent '{context.intent}' for codebase explorer")
                return False, errors
            else:
                # Security intent WITH exploration keywords - allow it
                logger.info(f"Allowing security intent '{context.intent}' for codebase explorer due to exploration keywords in context")
                return len(errors) == 0, errors
        
        # If the intent contains only security keywords without exploration, reject it
        if context.intent not in compatible_intents and not any(
            intent_word in context.intent for intent_word in compatible_intents
        ):
            # Check if this is a security-only request
            if any(keyword in context.intent.lower() for keyword in security_keywords):
                if not any(keyword in original_context for keyword in exploration_keywords):
                    errors.append(f"Tool not suitable for security-focused intent '{context.intent}' without exploration context")
                    logger.info(f"Rejecting security-only request for codebase explorer: {context.intent}")
                    return False, errors
                else:
                    # Security keywords with exploration keywords - allow it
                    logger.info(f"Allowing intent '{context.intent}' for codebase explorer due to exploration keywords in context")
                    return len(errors) == 0, errors
            
            # For other non-compatible intents, just warn but allow
            logger.warning(f"Intent '{context.intent}' may not be optimal for codebase exploration")
        
        return len(errors) == 0, errors
    
    async def execute(self, context: AnalysisContext, **kwargs) -> ToolResult:
        """Execute codebase exploration analysis."""
        start_time = time.time()
        logger.info(f"Starting codebase exploration for {context.repository_url}")
        
        try:
            # Initialize LLM if not already done
            openai_api_key = kwargs.get('openai_api_key')
            if openai_api_key and not self.llm:
                self.llm = ChatOpenAI(
                    model="gpt-4",
                    temperature=0,
                    api_key=openai_api_key
                )
            
            results = {}
            
            # Step 1: Analyze file structure
            logger.info("Analyzing file structure...")
            file_structure = self._analyze_file_structure(context.repository_path)
            results['file_structure'] = file_structure
            
            # Step 2: Detect languages and frameworks
            logger.info("Detecting languages and frameworks...")
            language_analysis = self._detect_languages_and_frameworks(context.repository_path)
            results['language_analysis'] = language_analysis
            
            # Step 3: Identify architectural patterns
            logger.info("Identifying architectural patterns...")
            architecture_patterns = self._identify_architectural_patterns(
                context.repository_path, language_analysis
            )
            results['architecture_patterns'] = architecture_patterns
            
            # Step 4: Extract main components
            logger.info("Extracting main components...")
            main_components = self._extract_main_components(
                context.repository_path, language_analysis
            )
            results['main_components'] = main_components
            
            # Step 5: Analyze dependencies
            logger.info("Analyzing dependencies...")
            dependencies = self._analyze_dependencies(context.repository_path)
            results['dependencies'] = dependencies
            
            # Step 6: Generate AI insights (if LLM available)
            if self.llm:
                logger.info("Generating AI-powered architectural insights...")
                insights = await self._analyze_code_with_llm(results)
                results['architectural_insights'] = insights
            else:
                results['architectural_insights'] = "AI insights unavailable (no OpenAI API key provided)"
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                tool_name=self.metadata.name,
                success=True,
                execution_time=execution_time,
                results=results,
                metadata={
                    "total_files_analyzed": file_structure.get("total_files", 0),
                    "primary_language": language_analysis.get("primary_language", "Unknown"),
                    "frameworks_detected": len(language_analysis.get("frameworks", [])),
                    "architecture_patterns_found": len(architecture_patterns)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Codebase exploration failed: {e}")
            
            return ToolResult(
                tool_name=self.metadata.name,
                success=False,
                execution_time=execution_time,
                results={},
                errors=[str(e)]
            )
    
    def _analyze_file_structure(self, root_path: str) -> Dict[str, Any]:
        """Analyze repository file structure."""
        file_stats = {
            'total_files': 0,
            'total_lines': 0,
            'file_types': defaultdict(int),
            'directory_structure': {},
            'main_directories': [],
            'largest_files': []
        }
        
        # Common directories to track
        important_dirs = [
            'src', 'lib', 'app', 'components', 'pages', 'api', 'services',
            'models', 'controllers', 'views', 'tests', 'test', '__tests__',
            'docs', 'documentation', 'config', 'scripts', 'utils', 'helpers'
        ]
        
        try:
            for root, dirs, files in os.walk(root_path):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    'node_modules', '__pycache__', 'venv', 'env', 'dist', 'build',
                    'target', 'out', '.git', '.svn'
                ]]
                
                relative_root = os.path.relpath(root, root_path)
                if relative_root != '.':
                    # Track important directories
                    for dir_part in relative_root.split(os.sep):
                        if dir_part.lower() in important_dirs:
                            if dir_part not in file_stats['main_directories']:
                                file_stats['main_directories'].append(dir_part)
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    file_ext = Path(file).suffix.lower()
                    
                    file_stats['total_files'] += 1
                    file_stats['file_types'][file_ext] += 1
                    
                    # Count lines and track largest files
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            file_stats['total_lines'] += lines
                            
                            # Track largest files
                            relative_path = os.path.relpath(file_path, root_path)
                            file_stats['largest_files'].append({
                                'path': relative_path,
                                'lines': lines,
                                'size': os.path.getsize(file_path)
                            })
                    except:
                        pass
            
            # Sort and limit largest files
            file_stats['largest_files'].sort(key=lambda x: x['lines'], reverse=True)
            file_stats['largest_files'] = file_stats['largest_files'][:10]
            
            # Convert defaultdict to regular dict
            file_stats['file_types'] = dict(file_stats['file_types'])
            
        except Exception as e:
            logger.error(f"Failed to analyze file structure: {e}")
        
        return file_stats
    
    def _detect_languages_and_frameworks(self, root_path: str) -> Dict[str, Any]:
        """Detect programming languages and frameworks."""
        language_stats = {
            'languages': {},
            'primary_language': 'Unknown',
            'frameworks': [],
            'total_code_files': 0
        }
        
        # Language extensions mapping
        language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
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
            '.jsx': 'React'
        }
        
        language_counts = Counter()
        
        try:
            # Count files by language
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    'node_modules', '__pycache__', 'venv', 'env', 'dist', 'build'
                ]]
                
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in language_extensions:
                        language = language_extensions[ext]
                        language_counts[language] += 1
                        language_stats['total_code_files'] += 1
            
            # Convert to percentages
            total_files = sum(language_counts.values())
            if total_files > 0:
                for lang, count in language_counts.items():
                    language_stats['languages'][lang] = {
                        'files': count,
                        'percentage': round((count / total_files) * 100, 1)
                    }
                
                # Determine primary language
                language_stats['primary_language'] = language_counts.most_common(1)[0][0]
            
            # Detect frameworks
            detected_frameworks = []
            for framework, indicators in self.framework_indicators.items():
                framework_score = 0
                for indicator in indicators:
                    indicator_path = os.path.join(root_path, indicator)
                    if os.path.exists(indicator_path):
                        framework_score += 1
                
                # If more than half the indicators are present, consider framework detected
                if framework_score >= len(indicators) * 0.5:
                    detected_frameworks.append({
                        'name': framework,
                        'confidence': round(framework_score / len(indicators), 2),
                        'indicators_found': framework_score
                    })
            
            language_stats['frameworks'] = detected_frameworks
            
        except Exception as e:
            logger.error(f"Failed to detect languages and frameworks: {e}")
        
        return language_stats
    
    def _identify_architectural_patterns(self, root_path: str, language_info: Dict) -> List[str]:
        """Identify architectural patterns in the codebase."""
        patterns = []
        
        try:
            # Check directory structure for architectural patterns
            dirs = []
            for root, subdirs, files in os.walk(root_path):
                for subdir in subdirs:
                    if not subdir.startswith('.'):
                        dirs.append(subdir.lower())
            
            dir_set = set(dirs)
            
            # MVC Pattern
            if any(d in dir_set for d in ['models', 'views', 'controllers']):
                patterns.append("MVC (Model-View-Controller)")
            
            # Microservices/Service-oriented
            if any(d in dir_set for d in ['services', 'microservices']):
                patterns.append("Service-Oriented Architecture")
            
            # Component-based (React, Vue, Angular)
            if any(d in dir_set for d in ['components', 'widgets']):
                patterns.append("Component-Based Architecture")
            
            # Layered Architecture
            if any(d in dir_set for d in ['business', 'data', 'presentation', 'domain']):
                patterns.append("Layered Architecture")
            
            # Clean Architecture
            if any(d in dir_set for d in ['entities', 'usecases', 'repositories']):
                patterns.append("Clean Architecture")
            
            # API-first
            if any(d in dir_set for d in ['api', 'endpoints', 'routes']):
                patterns.append("API-First Design")
            
            # Plugin/Extension architecture
            if any(d in dir_set for d in ['plugins', 'extensions', 'addons']):
                patterns.append("Plugin Architecture")
            
            # Event-driven
            if any(d in dir_set for d in ['events', 'handlers', 'listeners']):
                patterns.append("Event-Driven Architecture")
            
        except Exception as e:
            logger.error(f"Failed to identify architectural patterns: {e}")
        
        return patterns
    
    def _extract_main_components(self, root_path: str, language_info: Dict) -> List[Dict[str, Any]]:
        """Extract main components from the codebase."""
        components = []
        
        try:
            # Look for main application files
            main_files = [
                'main.py', 'app.py', '__init__.py', 'main.go', 'main.java',
                'index.js', 'app.js', 'server.js', 'main.ts', 'app.ts'
            ]
            
            for main_file in main_files:
                main_path = os.path.join(root_path, main_file)
                if os.path.exists(main_path):
                    try:
                        size = os.path.getsize(main_path)
                        with open(main_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                        
                        components.append({
                            'name': main_file,
                            'type': 'Main Application File',
                            'path': main_file,
                            'size': size,
                            'lines': lines
                        })
                    except:
                        pass
            
            # Look for important directories
            important_dirs = ['src', 'lib', 'app', 'api', 'services', 'components']
            for root, dirs, files in os.walk(root_path):
                if root == root_path:  # Only check top level
                    for dir_name in dirs:
                        if dir_name.lower() in important_dirs:
                            dir_path = os.path.join(root, dir_name)
                            try:
                                # Count files in directory
                                file_count = sum(len(files) for _, _, files in os.walk(dir_path))
                                
                                components.append({
                                    'name': dir_name,
                                    'type': 'Main Directory',
                                    'path': dir_name + '/',
                                    'file_count': file_count
                                })
                            except:
                                pass
            
            # Look for configuration files
            config_files = [
                'package.json', 'requirements.txt', 'go.mod', 'Cargo.toml',
                'pom.xml', 'build.gradle', 'composer.json', 'Gemfile',
                'Dockerfile', '.env', 'config.yaml', 'config.json'
            ]
            
            for config_file in config_files:
                config_path = os.path.join(root_path, config_file)
                if os.path.exists(config_path):
                    try:
                        size = os.path.getsize(config_path)
                        
                        components.append({
                            'name': config_file,
                            'type': 'Configuration File',
                            'path': config_file,
                            'size': size
                        })
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Failed to extract main components: {e}")
        
        return components
    
    def _analyze_dependencies(self, root_path: str) -> Dict[str, List[str]]:
        """Analyze project dependencies."""
        dependencies = {}
        
        try:
            # Python dependencies
            req_file = os.path.join(root_path, 'requirements.txt')
            if os.path.exists(req_file):
                try:
                    with open(req_file, 'r') as f:
                        deps = []
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Extract package name (before == or >=)
                                pkg = line.split('==')[0].split('>=')[0].split('<=')[0]
                                deps.append(pkg.strip())
                        dependencies['Python'] = deps[:20]  # Limit to first 20
                except:
                    pass
            
            # Node.js dependencies
            package_file = os.path.join(root_path, 'package.json')
            if os.path.exists(package_file):
                try:
                    import json
                    with open(package_file, 'r') as f:
                        data = json.load(f)
                        deps = []
                        if 'dependencies' in data:
                            deps.extend(list(data['dependencies'].keys()))
                        if 'devDependencies' in data:
                            deps.extend(list(data['devDependencies'].keys()))
                        dependencies['Node.js'] = deps[:20]
                except:
                    pass
            
            # Go dependencies
            go_mod_file = os.path.join(root_path, 'go.mod')
            if os.path.exists(go_mod_file):
                try:
                    with open(go_mod_file, 'r') as f:
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
                                # Extract module name
                                parts = line.split()
                                if len(parts) >= 2 and not parts[0].startswith('//'):
                                    module = parts[0] if in_require_block else parts[1]
                                    deps.append(module)
                        dependencies['Go'] = deps[:20]
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Failed to analyze dependencies: {e}")
        
        return dependencies
    
    async def _analyze_code_with_llm(self, analysis_data: Dict) -> str:
        """Generate AI-powered architectural insights."""
        if not self.llm:
            return "AI analysis unavailable"
        
        try:
            # Create a summary of the analysis for the LLM
            summary = f"""
            File Structure Analysis:
            - Total files: {analysis_data['file_structure']['total_files']}
            - Total lines of code: {analysis_data['file_structure']['total_lines']}
            - Main directories: {', '.join(analysis_data['file_structure']['main_directories'])}
            
            Language Analysis:
            - Primary language: {analysis_data['language_analysis']['primary_language']}
            - Languages detected: {', '.join(analysis_data['language_analysis']['languages'].keys())}
            - Frameworks: {', '.join([f['name'] for f in analysis_data['language_analysis']['frameworks']])}
            
            Architecture Patterns: {', '.join(analysis_data['architecture_patterns'])}
            
            Main Components: {len(analysis_data['main_components'])} components identified
            
            Dependencies: {', '.join(analysis_data['dependencies'].keys())} ecosystems
            """
            
            system_prompt = """You are an expert software architect. Analyze the provided codebase analysis 
            and generate comprehensive architectural insights. Focus on:
            
            1. Overall architecture assessment
            2. Code organization and structure quality
            3. Technology stack evaluation
            4. Potential improvement areas
            5. Scalability considerations
            6. Best practices adherence
            
            Provide actionable insights in a clear, professional manner."""
            
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=summary)
            ])
            
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            return f"AI analysis failed: {str(e)}" 