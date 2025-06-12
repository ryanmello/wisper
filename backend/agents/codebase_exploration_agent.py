import os
import json
import logging
from typing import Dict, List, Any, TypedDict
from pathlib import Path
from collections import defaultdict, Counter
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

class CodebaseAnalysisState(TypedDict):
    repository_url: str
    clone_path: str
    file_structure: Dict[str, Any]
    language_analysis: Dict[str, Any]
    architecture_patterns: List[str]
    main_components: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    code_statistics: Dict[str, Any]
    framework_analysis: Dict[str, Any]
    architectural_insights: str
    progress: float
    current_step: str
    errors: List[str]

class CodebaseExplorationAgent:    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0,
            api_key=openai_api_key
        )
        
        self.openai_api_key = openai_api_key
        self.temp_dir = None
        self.current_state = None
        
        self.config_files = {
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 
            'pom.xml', 'build.gradle', 'composer.json', 'Gemfile'
        }
        
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

    def analyze_file_structure(self, root_path: str) -> Dict[str, Any]:
        file_types = Counter()
        directory_analysis = defaultdict(list)
        
        skip_dirs = {
            '.git', '__pycache__', 'node_modules', '.next', 'dist', 'build',
            '.vscode', '.idea', 'coverage', '.pytest_cache', 'venv', 'env'
        }
        
        total_files = 0
        total_lines = 0
        
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            rel_path = os.path.relpath(root, root_path)
            if rel_path == '.':
                rel_path = 'root'
            
            for file in files:
                if file.startswith('.') and file not in ['.env.example', '.gitignore', '.dockerignore']:
                    continue
                    
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                file_types[file_ext] += 1
                directory_analysis[rel_path].append(file)
                total_files += 1
                
                if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.go', '.rs']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            total_lines += lines
                    except:
                        pass
        
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "file_types": dict(file_types.most_common()),
            "directory_structure": dict(directory_analysis),
            "main_directories": list(directory_analysis.keys())[:20]
        }

    def detect_languages_and_frameworks(self, root_path: str) -> Dict[str, Any]:
        """Detect programming languages and frameworks used."""
        languages = Counter()
        frameworks = []
        
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.jsx': 'React JSX', '.tsx': 'TypeScript React',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C',
            '.go': 'Go', '.rs': 'Rust', '.php': 'PHP',
            '.rb': 'Ruby', '.swift': 'Swift', '.kt': 'Kotlin',
            '.cs': 'C#', '.scala': 'Scala', '.clj': 'Clojure'
        }
        
        for root, dirs, files in os.walk(root_path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in language_map:
                    languages[language_map[ext]] += 1
        
        for framework, indicators in self.framework_indicators.items():
            score = 0
            for indicator in indicators:
                indicator_path = os.path.join(root_path, indicator)
                if os.path.exists(indicator_path):
                    score += 1
            
            if score >= len(indicators) * 0.5:
                frameworks.append({
                    "name": framework,
                    "confidence": score / len(indicators),
                    "indicators_found": score
                })
        
        return {
            "languages": dict(languages.most_common()),
            "primary_language": languages.most_common(1)[0][0] if languages else "Unknown",
            "frameworks": sorted(frameworks, key=lambda x: x['confidence'], reverse=True),
            "total_code_files": sum(languages.values())
        }

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
        go_mod = os.path.join(root_path, 'go.mod')
        if os.path.exists(go_mod):
            try:
                with open(go_mod, 'r') as f:
                    content = f.read()
                    import re
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
                    import re
                    deps = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
                    dependencies['Java'] = deps[:20]
            except:
                pass
        
        return dependencies

    def identify_architectural_patterns(self, root_path: str, language_info: Dict) -> List[str]:
        """Identify architectural patterns and design approaches."""
        patterns = []
        
        dirs = [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))]
        files = [f for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path, f))]
        
        if any(d in ['models', 'views', 'controllers'] for d in dirs) or \
           any(d in ['app/models', 'app/views', 'app/controllers'] for d in dirs):
            patterns.append("MVC (Model-View-Controller)")
        
        if 'docker-compose.yml' in files or 'kubernetes' in dirs or 'k8s' in dirs:
            patterns.append("Microservices Architecture")
        
        if any(d in ['domain', 'infrastructure', 'application', 'interfaces'] for d in dirs):
            patterns.append("Clean Architecture")
        
        if 'components' in dirs or 'src/components' in [os.path.join(r, d) for r, dirs, f in os.walk(root_path) for d in dirs]:
            patterns.append("Component-Based Architecture")
        
        if any(d in ['services', 'repositories', 'entities', 'dto'] for d in dirs):
            patterns.append("Layered Architecture")
        
        if any(keyword in str(dirs + files).lower() for keyword in ['event', 'queue', 'pub', 'sub', 'kafka', 'rabbitmq']):
            patterns.append("Event-Driven Architecture")
        
        if any(f in ['openapi.yml', 'swagger.yml', 'api.yml'] for f in files) or 'api' in dirs:
            patterns.append("API-First Design")
        
        return patterns

    def extract_main_components(self, root_path: str, language_info: Dict) -> List[Dict[str, Any]]:
        components = []
        main_files = []
        main_patterns = [ 'main.py', 'app.py', 'server.py', 'index.js', 'app.js', 'server.js',
                          'main.go', 'main.java', 'Program.cs', 'main.cpp', 'main.rs']
        
        for pattern in main_patterns:
            file_path = os.path.join(root_path, pattern)
            if os.path.exists(file_path):
                main_files.append({
                    "name": pattern,
                    "type": "Entry Point",
                    "path": pattern,
                    "size": os.path.getsize(file_path)
                })
        
        config_files = []
        for config_file in self.config_files:
            file_path = os.path.join(root_path, config_file)
            if os.path.exists(file_path):
                config_files.append({
                    "name": config_file,
                    "type": "Configuration",
                    "path": config_file,
                    "size": os.path.getsize(file_path)
                })
        
        important_dirs = []
        dir_types = {
            'src': 'Source Code',
            'lib': 'Library',
            'components': 'UI Components',
            'services': 'Business Logic',
            'models': 'Data Models',
            'controllers': 'Controllers',
            'views': 'View Layer',
            'utils': 'Utilities',
            'api': 'API Layer',
            'tests': 'Test Suite',
            'docs': 'Documentation'
        }
        
        for dir_name, dir_type in dir_types.items():
            dir_path = os.path.join(root_path, dir_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                important_dirs.append({
                    "name": dir_name,
                    "type": dir_type,
                    "path": dir_name,
                    "file_count": file_count
                })
        
        components.extend(main_files)
        components.extend(config_files)
        components.extend(important_dirs)
        
        return components

    async def analyze_code_with_llm(self, analysis_data: Dict) -> str:
        """Use LLM to provide architectural insights."""
        
        prompt = f"""
        As a senior software architect, analyze this codebase structure and provide comprehensive insights:

        Repository Analysis:
        - Primary Language: {analysis_data['language_analysis']['primary_language']}
        - Languages Used: {', '.join(analysis_data['language_analysis']['languages'].keys())}
        - Frameworks: {', '.join([f['name'] for f in analysis_data['language_analysis']['frameworks']])}
        - Total Files: {analysis_data['file_structure']['total_files']}
        - Total Lines of Code: {analysis_data['file_structure']['total_lines']}

        Directory Structure:
        {json.dumps(analysis_data['file_structure']['main_directories'], indent=2)}

        Main Components:
        {json.dumps([c['name'] + ' (' + c['type'] + ')' for c in analysis_data['main_components']], indent=2)}

        Architectural Patterns Detected:
        {', '.join(analysis_data['architecture_patterns']) if analysis_data['architecture_patterns'] else 'None clearly identified'}

        Dependencies:
        {json.dumps(analysis_data['dependencies'], indent=2)}

        Please provide:
        1. **Architecture Overview**: High-level description of the system architecture
        2. **Technology Stack Assessment**: Analysis of technology choices and their suitability
        3. **Code Organization**: How well the code is structured and organized
        4. **Scalability Considerations**: Potential scalability strengths and challenges
        5. **Maintainability**: Code maintainability and technical debt indicators
        6. **Recommendations**: Specific suggestions for improvement

        Format your response as clear, actionable insights that would be valuable for developers and stakeholders.
        """

        messages = [
            SystemMessage(content="You are a senior software architect providing detailed codebase analysis."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content

    async def clone_and_setup(self, state: CodebaseAnalysisState) -> CodebaseAnalysisState:
        """Step 1: Clone repository and basic setup."""
        state["current_step"] = "Initializing repository clone..."
        state["progress"] = 5.0
        
        state["current_step"] = "Cloning repository..."
        state["progress"] = 10.0
        
        from services.repository_service import repository_service
        clone_result = repository_service.clone_repository(state["repository_url"])
        
        if clone_result["status"] == "error":
            state["errors"].append(f"Failed to clone repository: {clone_result['error']}")
            return state

        state["clone_path"] = clone_result["clone_path"]
        
        if clone_result["status"] == "success":
            self.temp_dir = clone_result["clone_path"]
            
        state["current_step"] = "Repository cloned successfully"
        state["progress"] = 15.0
        
        return state

    async def analyze_structure(self, state: CodebaseAnalysisState) -> CodebaseAnalysisState:
        """Step 2: Analyze file structure."""
        state["current_step"] = "Starting file structure analysis..."
        state["progress"] = 20.0
        
        if not state["clone_path"]:
            state["errors"].append("No clone path available")
            return state
        
        try:
            state["current_step"] = "Analyzing file structure..."
            state["progress"] = 30.0
            
            file_structure = self.analyze_file_structure(state["clone_path"])
            state["file_structure"] = file_structure
            
            state["current_step"] = "File structure analysis complete"
            state["progress"] = 40.0
        except Exception as e:
            state["errors"].append(f"File structure analysis failed: {str(e)}")
        
        return state

    async def analyze_languages(self, state: CodebaseAnalysisState) -> CodebaseAnalysisState:
        """Step 3: Analyze languages and frameworks."""
        state["current_step"] = "Starting language detection..."
        state["progress"] = 45.0
        
        try:
            state["current_step"] = "Detecting languages and frameworks..."
            state["progress"] = 55.0
            
            language_analysis = self.detect_languages_and_frameworks(state["clone_path"])
            state["language_analysis"] = language_analysis
            
            dependencies = self.analyze_dependencies(state["clone_path"])
            state["dependencies"] = dependencies
            
            state["current_step"] = "Language analysis complete"
            state["progress"] = 65.0
        except Exception as e:
            state["errors"].append(f"Language analysis failed: {str(e)}")
        
        return state

    async def identify_architecture(self, state: CodebaseAnalysisState) -> CodebaseAnalysisState:
        """Step 4: Identify architectural patterns and components."""
        state["current_step"] = "Starting architecture analysis..."
        state["progress"] = 70.0
        
        try:
            state["current_step"] = "Identifying architecture patterns..."
            state["progress"] = 80.0
            
            patterns = self.identify_architectural_patterns(state["clone_path"], state["language_analysis"])
            state["architecture_patterns"] = patterns
            
            components = self.extract_main_components(state["clone_path"], state["language_analysis"])
            state["main_components"] = components
            
            state["current_step"] = "Architecture analysis complete"
            state["progress"] = 85.0
        except Exception as e:
            state["errors"].append(f"Architecture analysis failed: {str(e)}")
        
        return state

    async def generate_insights(self, state: CodebaseAnalysisState) -> CodebaseAnalysisState:
        """Step 5: Generate AI-powered insights."""
        state["current_step"] = "Preparing AI analysis..."
        state["progress"] = 88.0
        
        try:
            state["current_step"] = "Generating architectural insights..."
            state["progress"] = 92.0
            
            insights = await self.analyze_code_with_llm({
                "language_analysis": state["language_analysis"],
                "file_structure": state["file_structure"],
                "main_components": state["main_components"],
                "architecture_patterns": state["architecture_patterns"],
                "dependencies": state["dependencies"]
            })
            
            state["architectural_insights"] = insights
            state["current_step"] = "Analysis complete!"
            state["progress"] = 100.0
        except Exception as e:
            state["errors"].append(f"Insight generation failed: {str(e)}")
            state["current_step"] = "Analysis complete with errors"
            state["progress"] = 100.0
        
        return state

    def create_workflow(self):
        workflow = StateGraph(CodebaseAnalysisState)
        
        workflow.add_node("clone", self.clone_and_setup)
        workflow.add_node("structure", self.analyze_structure)
        workflow.add_node("languages", self.analyze_languages)
        workflow.add_node("architecture", self.identify_architecture)
        workflow.add_node("insights", self.generate_insights)
        
        workflow.set_entry_point("clone")
        workflow.add_edge("clone", "structure")
        workflow.add_edge("structure", "languages")
        workflow.add_edge("languages", "architecture")
        workflow.add_edge("architecture", "insights")
        workflow.add_edge("insights", END)
        
        return workflow.compile()

    async def analyze_repository(self, repository_url: str):
        """Main method to analyze a repository with comprehensive codebase exploration."""
        
        initial_state = CodebaseAnalysisState(
            repository_url=repository_url,
            clone_path="",
            file_structure={},
            language_analysis={},
            architecture_patterns=[],
            main_components=[],
            dependencies={},
            code_statistics={},
            framework_analysis={},
            architectural_insights="",
            progress=0.0,
            current_step="Starting analysis...",
            errors=[]
        )
        
        self.current_state = initial_state
        
        workflow = self.create_workflow()
        
        final_state = None
        async for step_output in workflow.astream(initial_state):
            for node_name, state in step_output.items():
                final_state = state
                self.current_state = state

                yield {
                    "type": "progress",
                    "current_step": state["current_step"],
                    "progress": state["progress"],
                    "partial_results": {
                        "file_structure": state.get("file_structure", {}),
                        "language_analysis": state.get("language_analysis", {}),
                        "architecture_patterns": state.get("architecture_patterns", []),
                        "main_components": state.get("main_components", [])
                    }
                }
        
        if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
            from services.repository_service import repository_service
            cleanup_success = repository_service.cleanup_directory(self.temp_dir)
            if not cleanup_success:
                repository_service.schedule_delayed_cleanup(self.temp_dir)
            self.temp_dir = None
        
        yield {
            "type": "completed",
            "results": {
                "repository_url": final_state["repository_url"],
                "file_structure": final_state["file_structure"],
                "language_analysis": final_state["language_analysis"],
                "architecture_patterns": final_state["architecture_patterns"],
                "main_components": final_state["main_components"],
                "dependencies": final_state["dependencies"],
                "architectural_insights": final_state["architectural_insights"],
                "errors": final_state["errors"]
            }
        } 
