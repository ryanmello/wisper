"""
Smart Analysis Agent - Central AI agent for intelligent tool selection and orchestration.

This agent analyzes context from the frontend and intelligently selects and coordinates
the appropriate tools to perform comprehensive repository analysis.
"""

import asyncio
import time
import tempfile
import shutil
from typing import Dict, List, Any, Optional, AsyncGenerator
from pathlib import Path
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from git import Repo

from tools.base_tool import BaseTool, ToolResult, AnalysisContext
from core.tool_registry import get_tool_registry
from core.context_analyzer import ContextAnalyzer
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SmartAnalysisAgent:
    """
    Central AI agent that intelligently selects and orchestrates analysis tools.
    
    This agent acts as the brain of the analysis system, determining which tools
    to use based on the context and coordinating their execution.
    """
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=openai_api_key
        )
        self.context_analyzer = ContextAnalyzer()
        self.temp_dir = None
        
        # Execution strategy configuration
        self.max_parallel_tools = 3
        self.tool_timeout = 300  # 5 minutes per tool
    
    async def analyze_repository(
        self, 
        repository_url: str, 
        context_text: str = "explore codebase",
        additional_params: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform intelligent repository analysis based on context.
        
        Args:
            repository_url: URL of repository to analyze
            context_text: Natural language context describing what to analyze
            additional_params: Optional additional parameters
            
        Yields:
            Progress updates and results
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze context and create analysis plan
            yield {
                "type": "progress",
                "progress": 5,
                "current_step": "Analyzing context and creating analysis plan..."
            }
            
            context = self.context_analyzer.analyze_context(
                context_text, repository_url, {
                    **(additional_params or {}),
                    'original_context': context_text  # Store original context for AI insights decision
                }
            )
            
            logger.info(f"Analyzed context - Intent: {context.intent}, Languages: {context.target_languages}")
            
            # Step 2: Clone repository
            yield {
                "type": "progress", 
                "progress": 15,
                "current_step": "Cloning repository..."
            }
            
            repo_path = await self._clone_repository(repository_url)
            context.repository_path = repo_path
            
            # Step 3: Enhance context with repository information
            yield {
                "type": "progress",
                "progress": 20,
                "current_step": "Detecting languages and enhancing context..."
            }
            
            detected_languages = self._detect_languages_from_repository(repo_path)
            if detected_languages:
                # Update context with detected languages, keeping original if no detection
                context.target_languages = detected_languages
                logger.info(f"Updated target languages from repository: {detected_languages}")

            # Step 4: Get tool registry and find suitable tools for all intents
            yield {
                "type": "progress",
                "progress": 25,
                "current_step": "Selecting appropriate analysis tools..."
            }
            
            registry = await get_tool_registry()
            
            # Parse the original intent to get secondary intents
            parsed_intent = self.context_analyzer._parse_intent(context_text)
            logger.info(f"Parsed intent - Actions: {[(a.intent, a.priority) for a in parsed_intent.actions]}")
            
            # Find tools for all identified actions
            suitable_tools = registry.find_suitable_tools(context)
            
            # Find tools for additional actions
            additional_tools = set()
            for action in parsed_intent.actions[1:]:  # Skip first action (already handled)
                # Create a temporary context with the action intent
                action_context = AnalysisContext(
                    repository_path=context.repository_path,
                    repository_url=context.repository_url,
                    intent=action.intent,
                    target_languages=context.target_languages,
                    scope=context.scope,
                    specific_files=context.specific_files,
                    depth=context.depth,
                    additional_params=context.additional_params
                )
                
                action_tools = registry.find_suitable_tools(action_context)
                for tool in action_tools:
                    if tool not in suitable_tools:
                        additional_tools.add(tool)
                        logger.info(f"Added tool '{tool.metadata.name}' for action '{action.intent}' (priority {action.priority})")
            
            # Combine all tools
            all_suitable_tools = suitable_tools + list(additional_tools)
            
            if not all_suitable_tools:
                logger.warning("No suitable tools found for context")
                all_suitable_tools = [registry.get_tool("codebase_explorer")]  # Fallback
                all_suitable_tools = [t for t in all_suitable_tools if t is not None]
            
            logger.info(f"Selected {len(all_suitable_tools)} tools: {[t.metadata.name for t in all_suitable_tools]}")
            
            # Step 5: Create execution plan
            execution_plan = await self._create_execution_plan(context, all_suitable_tools)
            
            yield {
                "type": "execution_plan",
                "progress": 30,
                "current_step": "Created execution plan",
                "execution_plan": execution_plan
            }
            
            # Step 6: Execute tools
            tool_results = {}
            total_tools = len(all_suitable_tools)
            
            # Execute tools in batches
            current_progress = 30
            progress_per_batch = 50 / len(execution_plan["batches"])
            
            for batch_index, batch in enumerate(execution_plan["batches"]):
                yield {
                    "type": "progress",
                    "progress": int(current_progress),
                    "current_step": f"Executing batch {batch_index + 1} of {len(execution_plan['batches'])}..."
                }
                
                # Execute the batch
                batch_results = await self._execute_tool_batch(
                    batch, context, 
                    int(current_progress), 
                    int(current_progress + progress_per_batch)
                )
                
                # Report individual tool completions
                for tool_name, result in batch_results.items():
                    tool_results[tool_name] = result
                    
                    yield {
                        "type": "tool_completed",
                        "tool_name": tool_name,
                        "tool_result": {
                            "success": result.success,
                            "execution_time": result.execution_time,
                            "error": result.errors[0] if result.errors else None
                        },
                        "progress": int(current_progress + (len(tool_results) / total_tools) * progress_per_batch)
                    }
                
                current_progress += progress_per_batch
                
            # Step 7: Generate AI insights if appropriate
            if self._should_generate_ai_insights(context, tool_results):
                yield {
                    "type": "progress",
                    "progress": 85,
                    "current_step": "Generating comprehensive AI insights..."
                }
                
                insights = await self._generate_comprehensive_insights(context, tool_results)
            else:
                logger.info("AI insights skipped for simple exploration request")
                insights = "Analysis complete. Results available in individual tool outputs."
            
            # Step 8: Compile final results
            yield {
                "type": "progress",
                "progress": 95,
                "current_step": "Compiling final results..."
            }
            
            final_results = await self._compile_final_results(
                context, tool_results, insights, execution_plan
            )
            
            # Step 9: Send completion
            yield {
                "type": "completed",
                "progress": 100,
                "current_step": "Analysis complete!",
                "results": final_results,
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Smart analysis failed: {e}")
            yield {
                "type": "error",
                "error": f"Analysis failed: {str(e)}"
            }
        
        finally:
            # Cleanup
            if self.temp_dir and Path(self.temp_dir).exists():
                await self._cleanup_repository(self.temp_dir)
    
    async def _clone_repository(self, repository_url: str) -> str:
        """Clone repository and return the path."""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="whisper_smart_")
            
            # Clean and validate URL
            if repository_url.startswith('https://github.com/'):
                clean_url = repository_url
            else:
                clean_url = f"https://github.com/{repository_url.replace('https://github.com/', '')}"
            
            repo = Repo.clone_from(clean_url, self.temp_dir)
            logger.info(f"Repository cloned to {self.temp_dir}")
            
            return self.temp_dir
            
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def _detect_languages_from_repository(self, repo_path: str) -> List[str]:
        """Detect programming languages from actual repository files."""
        import os
        from pathlib import Path
        
        detected_languages = []
        
        try:
            # Language indicators based on files and structure
            language_indicators = {
                "go": ["go.mod", "go.sum", "*.go"],
                "python": ["requirements.txt", "setup.py", "pyproject.toml", "*.py"],
                "javascript": ["package.json", "*.js", "*.ts"],
                "java": ["pom.xml", "build.gradle", "*.java"],
                "rust": ["Cargo.toml", "*.rs"],
                "c++": ["CMakeLists.txt", "*.cpp", "*.cxx", "*.cc", "*.hpp"],
                "c": ["*.c", "*.h"],
                "php": ["composer.json", "*.php"],
                "ruby": ["Gemfile", "*.rb"],
                "swift": ["Package.swift", "*.swift"]
            }
            
            repo_path_obj = Path(repo_path)
            
            # Check for each language
            for language, indicators in language_indicators.items():
                language_score = 0
                
                for indicator in indicators:
                    if indicator.startswith("*."):
                        # File extension check
                        extension = indicator[1:]  # Remove the *
                        found_files = list(repo_path_obj.rglob(f"*{extension}"))
                        if found_files:
                            language_score += len(found_files)  # Score based on number of files
                    else:
                        # Specific file check
                        if (repo_path_obj / indicator).exists():
                            language_score += 10  # Higher weight for specific files
                
                # Only add languages with significant evidence
                # For Go repositories, require either go.mod or multiple .go files
                if language == "go" and language_score >= 10:  # go.mod exists
                    detected_languages.append(language)
                    logger.debug(f"Detected {language} with score {language_score}")
                elif language != "go" and language_score >= 2:  # At least 2 files or 1 config file
                    detected_languages.append(language)
                    logger.debug(f"Detected {language} with score {language_score}")
            
            # Special filtering: if Go is detected with go.mod, it's likely a pure Go project
            # Remove other languages that might be false positives
            if "go" in detected_languages and (repo_path_obj / "go.mod").exists():
                # Keep Go first and only keep other languages with strong evidence
                filtered_languages = ["go"]
                for lang in detected_languages:
                    if lang != "go":
                        lang_score = 0
                        for indicator in language_indicators[lang]:
                            if indicator.startswith("*."):
                                extension = indicator[1:]
                                found_files = list(repo_path_obj.rglob(f"*{extension}"))
                                lang_score += len(found_files)
                            else:
                                if (repo_path_obj / indicator).exists():
                                    lang_score += 10
                        
                        # Only keep if there's substantial evidence (more than just 1-2 files)
                        if lang_score >= 5:
                            filtered_languages.append(lang)
                
                detected_languages = filtered_languages
            
            logger.info(f"Repository language detection: {detected_languages}")
            
        except Exception as e:
            logger.warning(f"Failed to detect languages from repository: {e}")
        
        return detected_languages
    
    def _should_generate_ai_insights(
        self, 
        context: AnalysisContext, 
        tool_results: Dict[str, ToolResult]
    ) -> bool:
        """
        Determine if AI insights should be generated based on context and results.
        
        Args:
            context: Analysis context
            tool_results: Results from executed tools
            
        Returns:
            True if AI insights should be generated
        """
        # Get the original context text
        original_context = context.additional_params.get('original_context', '').lower()
        
        # Always generate insights for security-focused analysis
        security_intents = ["security", "vulnerabilities", "audit", "find_vulnerabilities", "security_audit"]
        if context.intent in security_intents:
            return True
        
        # Always generate insights if multiple tools were executed (complex analysis)
        if len(tool_results) > 1:
            return True
        
        # Check for keywords that indicate the user wants architectural insights
        insight_keywords = [
            "architectural", "architecture", "overview", "insights", "analysis", 
            "understand", "explain", "structure", "patterns", "design",
            "how does", "what is", "summary", "report", "findings"
        ]
        
        # If the user explicitly asks for insights/architecture/overview, generate them
        if any(keyword in original_context for keyword in insight_keywords):
            logger.info(f"Generating AI insights due to request for architectural understanding")
            return True
        
        # Only skip AI insights for very basic exploration requests
        very_basic_keywords = ["just explore", "quick look", "basic scan", "simple check"]
        if any(keyword in original_context for keyword in very_basic_keywords):
            logger.info("Skipping AI insights for very basic exploration request")
            return False
        
        # Check if any tool found significant findings that warrant insights
        for tool_name, result in tool_results.items():
            if result.success and result.results:
                # Check for vulnerability findings
                if "vulnerabilities" in result.results or "security" in tool_name.lower():
                    return True
                
                # Check for complex metrics that would benefit from AI analysis
                if isinstance(result.results, dict) and len(result.results) > 5:
                    return True
        
        # Default: Generate insights for most exploration requests
        # Only very basic requests should skip insights
        logger.info("Generating AI insights for exploration request")
        return True
    
    async def _create_execution_plan(
        self, 
        context: AnalysisContext, 
        tools: List[BaseTool]
    ) -> Dict[str, Any]:
        """
        Create an intelligent execution plan for the selected tools.
        
        Args:
            context: Analysis context
            tools: List of selected tools
            
        Returns:
            Execution plan with batches and dependencies
        """
        # Categorize tools by execution characteristics
        fast_tools = []  # Tools that execute quickly (< 30 seconds)
        medium_tools = []  # Tools that take moderate time (30s - 2min)
        slow_tools = []  # Tools that take longer (> 2min)
        
        for tool in tools:
            estimate = tool.get_execution_estimate(context)
            if "second" in estimate and not "minute" in estimate:
                fast_tools.append(tool)
            elif "1-2 minute" in estimate or "30 second" in estimate:
                medium_tools.append(tool)
            else:
                slow_tools.append(tool)
        
        # Create execution batches
        batches = []
        
        # Batch 1: Fast tools (can run in parallel)
        if fast_tools:
            batches.append({
                "tools": [t.metadata.name for t in fast_tools],
                "parallel": len(fast_tools) <= self.max_parallel_tools,
                "estimated_time": "30 seconds"
            })
        
        # Batch 2: Medium tools (limited parallelism)
        if medium_tools:
            # Split into smaller batches if too many
            while medium_tools:
                batch_tools = medium_tools[:self.max_parallel_tools]
                medium_tools = medium_tools[self.max_parallel_tools:]
                
                batches.append({
                    "tools": [t.metadata.name for t in batch_tools],
                    "parallel": len(batch_tools) > 1,
                    "estimated_time": "1-2 minutes"
                })
        
        # Batch 3: Slow tools (typically sequential)
        for tool in slow_tools:
            batches.append({
                "tools": [tool.metadata.name],
                "parallel": False,
                "estimated_time": tool.get_execution_estimate(context)
            })
        
        return {
            "total_tools": len(tools),
            "estimated_total_time": self._calculate_total_estimate(batches),
            "batches": batches,
            "strategy": "intelligent_batching"
        }
    
    def _calculate_total_estimate(self, batches: List[Dict]) -> str:
        """Calculate total estimated execution time."""
        # Simple heuristic - sum sequential batches, max of parallel batches
        total_minutes = 0
        
        for batch in batches:
            if batch["parallel"]:
                # Parallel execution - use longest tool time
                total_minutes += 1  # Assume average 1 minute for parallel batch
            else:
                # Sequential execution
                if "minute" in batch["estimated_time"]:
                    # Extract minutes
                    import re
                    matches = re.findall(r'(\d+)', batch["estimated_time"])
                    if matches:
                        total_minutes += int(matches[-1])  # Take the last number
                else:
                    total_minutes += 0.5  # Assume 30 seconds
        
        if total_minutes < 1:
            return "30 seconds - 1 minute"
        elif total_minutes < 3:
            return f"{int(total_minutes)}-{int(total_minutes)+1} minutes"
        else:
            return f"{int(total_minutes)} minutes"
    
    async def _execute_tool_batch(
        self,
        batch: Dict[str, Any],
        context: AnalysisContext,
        start_progress: int,
        end_progress: int
    ) -> Dict[str, ToolResult]:
        """Execute a batch of tools."""
        registry = await get_tool_registry()
        tools_to_execute = [registry.get_tool(name) for name in batch["tools"]]
        tools_to_execute = [t for t in tools_to_execute if t is not None]
        
        results = {}
        
        if batch.get("parallel", False) and len(tools_to_execute) > 1:
            # Execute tools in parallel
            tasks = []
            for tool in tools_to_execute:
                task = asyncio.create_task(
                    self._execute_single_tool(tool, context)
                )
                tasks.append((tool.metadata.name, task))
            
            # Wait for all tasks to complete
            for tool_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=self.tool_timeout)
                    results[tool_name] = result
                except asyncio.TimeoutError:
                    logger.error(f"Tool {tool_name} timed out")
                    results[tool_name] = ToolResult(
                        tool_name=tool_name,
                        success=False,
                        execution_time=self.tool_timeout,
                        results={},
                        errors=[f"Tool execution timed out after {self.tool_timeout} seconds"]
                    )
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    results[tool_name] = ToolResult(
                        tool_name=tool_name,
                        success=False,
                        execution_time=0,
                        results={},
                        errors=[str(e)]
                    )
        else:
            # Execute tools sequentially
            for tool in tools_to_execute:
                try:
                    result = await asyncio.wait_for(
                        self._execute_single_tool(tool, context),
                        timeout=self.tool_timeout
                    )
                    results[tool.metadata.name] = result
                except Exception as e:
                    logger.error(f"Tool {tool.metadata.name} failed: {e}")
                    results[tool.metadata.name] = ToolResult(
                        tool_name=tool.metadata.name,
                        success=False,
                        execution_time=0,
                        results={},
                        errors=[str(e)]
                    )
        
        return results
    
    async def _execute_single_tool(self, tool: BaseTool, context: AnalysisContext) -> ToolResult:
        """Execute a single tool."""
        logger.info(f"Executing tool: {tool.metadata.name}")
        start_time = time.time()
        
        try:
            result = await tool.execute(context)
            execution_time = time.time() - start_time
            
            logger.info(f"Tool {tool.metadata.name} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool {tool.metadata.name} failed after {execution_time:.2f}s: {e}")
            
            return ToolResult(
                tool_name=tool.metadata.name,
                success=False,
                execution_time=execution_time,
                results={},
                errors=[str(e)]
            )
    
    async def _generate_comprehensive_insights(
        self,
        context: AnalysisContext,
        tool_results: Dict[str, ToolResult]
    ) -> str:
        """Generate AI-powered insights from all tool results."""
        
        # Combine all successful tool results
        combined_results = {}
        for tool_name, result in tool_results.items():
            if result.success:
                combined_results[tool_name] = result.results
        
        # Get the parsed intent from context analyzer
        context_analyzer = ContextAnalyzer()
        parsed_intent = context_analyzer._parse_intent(context.additional_params.get('original_context', ''))
        
        # Determine mixed intent scenario
        has_multiple_intents = len(parsed_intent.actions) > 1
        
        if has_multiple_intents:
            # Multiple intents detected - use comprehensive mixed analysis
            prompt_template = f"""
Based on the analysis results, provide comprehensive insights covering multiple aspects:

PRIMARY INTENT: {parsed_intent.actions[0].intent}
SECONDARY INTENTS: {', '.join([a.intent for a in parsed_intent.actions[1:] if a.priority > 0])}
CONFIDENCE: {parsed_intent.overall_confidence}
REASONING: {parsed_intent.reasoning}

Analysis Context: {{context}}
Tool Results: {{results}}

Please provide a comprehensive analysis that addresses all detected intents:

1. **{parsed_intent.actions[0].intent.replace('_', ' ').title()} Analysis** (Primary Focus):
   - Detailed analysis based on the primary intent
   - Key findings and insights
   - Specific recommendations

2. **{' & '.join([a.intent.replace('_', ' ').title() for a in parsed_intent.actions[1:] if a.priority > 0])} Analysis** (Secondary Focus):
   - Additional insights from secondary intents
   - Cross-cutting concerns and relationships
   - Integrated recommendations

3. **Integrated Recommendations**:
   - Combined action items addressing all aspects
   - Priority ordering of recommendations
   - Implementation considerations

Ensure the analysis is comprehensive and addresses the user's complete request while maintaining focus on the primary intent.
"""
        else:
            # Single intent - use focused analysis
            intent_prompts = {
                "explore": self._get_exploration_prompt(),
                "find_vulnerabilities": self._get_security_prompt(),
                "security_audit": self._get_security_prompt(),
                "analyze_performance": self._get_performance_prompt(),
                "code_quality": self._get_quality_prompt(),
                "documentation": self._get_documentation_prompt()
            }
            
            prompt_template = intent_prompts.get(
                parsed_intent.actions[0].intent, 
                self._get_exploration_prompt()  # Default fallback
            )
        
        # Prepare context for the AI
        analysis_summary = f"""
        Repository: {context.repository_url}
        Analysis Intent: {context.intent}
        Original Request: {context.additional_params.get('original_context', 'Not specified')}
        Target Languages: {', '.join(context.target_languages) if context.target_languages else 'Not specified'}
        Scope: {context.scope}
        
        Tool Results:
        """
        
        for tool_name, results in combined_results.items():
            analysis_summary += f"\n\n=== {tool_name.upper()} RESULTS ===\n"
            analysis_summary += str(results)[:2000]  # Limit to avoid token limits
            if len(str(results)) > 2000:
                analysis_summary += "\n... (truncated)"
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=prompt_template),
                HumanMessage(content=analysis_summary)
            ])
            
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            return "Unable to generate AI insights due to an error."
    
    async def _compile_final_results(
        self,
        context: AnalysisContext,
        tool_results: Dict[str, ToolResult],
        insights: str,
        execution_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile final analysis results."""
        
        # Calculate statistics
        successful_tools = [name for name, result in tool_results.items() if result.success]
        failed_tools = [name for name, result in tool_results.items() if not result.success]
        
        # Extract key metrics from successful tools
        metrics = {}
        vulnerability_summary = None
        
        for tool_name, result in tool_results.items():
            if result.success and result.results:
                if "vulnerability" in tool_name.lower():
                    vulnerability_summary = result.results
                
                # Extract numeric metrics
                if isinstance(result.results, dict):
                    for key, value in result.results.items():
                        if isinstance(value, (int, float)):
                            metrics[f"{tool_name}_{key}"] = value
        
        return {
            "summary": insights,
            "execution_info": {
                "tools_executed": len(tool_results),
                "successful_tools": len(successful_tools),
                "failed_tools": len(failed_tools),
                "execution_plan": execution_plan,
                "context": {
                    "intent": context.intent,
                    "languages": context.target_languages,
                    "scope": context.scope
                }
            },
            "tool_results": {
                name: result.dict() if hasattr(result, 'dict') else result
                for name, result in tool_results.items()
            },
            "vulnerability_summary": vulnerability_summary,
            "metrics": metrics,
            "recommendations": self._extract_recommendations(insights)
        }
    
    def _extract_recommendations(self, insights: str) -> List[str]:
        """Extract actionable recommendations from insights."""
        # Simple extraction based on common patterns
        recommendations = []
        
        lines = insights.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith('- ') or 
                line.startswith('* ') or 
                'recommend' in line.lower() or 
                'should' in line.lower() or
                'consider' in line.lower()):
                recommendations.append(line)
        
        return recommendations[:10]  # Limit to top 10
    
    async def _cleanup_repository(self, repo_path: str):
        """Clean up cloned repository."""
        import shutil
        import stat
        import os
        
        def handle_remove_readonly(func, path, exc):
            """Handle removal of read-only files on Windows."""
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception as e:
                logger.warning(f"Could not remove {path}: {e}")
        
        try:
            if os.path.exists(repo_path):
                # On Windows, Git creates read-only files that need special handling
                if os.name == 'nt':  # Windows
                    shutil.rmtree(repo_path, onerror=handle_remove_readonly)
                else:
                    shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository at {repo_path}")
        except PermissionError as e:
            logger.warning(f"Permission denied cleaning up repository {repo_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to cleanup repository: {e}")
    
    def _get_exploration_prompt(self) -> str:
        """Get prompt template for codebase exploration."""
        return """You are an expert software architect. 
        Analyze the provided repository analysis results and generate comprehensive architectural insights.
        
        Focus on:
        1. Overall architecture and design patterns
        2. Code organization and structure
        3. Component relationships and dependencies
        4. Design principles and architectural decisions
        5. Code quality and maintainability
        6. Key recommendations for architectural improvements
        
        Provide actionable insights that would be valuable for developers and architects.
        
        Analysis Context: {context}
        Tool Results: {results}"""
    
    def _get_security_prompt(self) -> str:
        """Get prompt template for security analysis."""
        return """You are an expert security analyst and software architect. 
        Analyze the provided repository analysis results and generate comprehensive security insights.
        
        Focus on:
        1. Security vulnerabilities and threats
        2. Security best practices compliance
        3. Risk assessment and mitigation
        4. Authentication and authorization patterns
        5. Data protection and privacy considerations
        6. Key security recommendations
        
        Provide actionable security insights that would be valuable for security teams and developers.
        
        Analysis Context: {context}
        Tool Results: {results}"""
    
    def _get_performance_prompt(self) -> str:
        """Get prompt template for performance analysis."""
        return """You are an expert performance engineer and software architect.
        Analyze the provided repository analysis results and generate performance insights.
        
        Focus on:
        1. Performance bottlenecks and optimization opportunities
        2. Resource utilization patterns
        3. Scalability considerations
        4. Algorithm efficiency and complexity analysis
        5. Memory and CPU usage patterns
        6. Key performance recommendations
        
        Provide actionable performance insights that would be valuable for optimization efforts.
        
        Analysis Context: {context}
        Tool Results: {results}"""
    
    def _get_quality_prompt(self) -> str:
        """Get prompt template for code quality analysis."""
        return """You are an expert software quality engineer and architect.
        Analyze the provided repository analysis results and generate code quality insights.
        
        Focus on:
        1. Code quality metrics and best practices compliance
        2. Technical debt identification and assessment
        3. Maintainability and readability analysis
        4. Design pattern usage and anti-patterns
        5. Testing coverage and strategy
        6. Key quality improvement recommendations
        
        Provide actionable quality insights that would be valuable for code improvement efforts.
        
        Analysis Context: {context}
        Tool Results: {results}"""
    
    def _get_documentation_prompt(self) -> str:
        """Get prompt template for documentation analysis."""
        return """You are an expert technical writer and software architect.
        Analyze the provided repository analysis results and generate documentation insights.
        
        Focus on:
        1. Documentation coverage and quality
        2. API documentation completeness
        3. Code comments and inline documentation
        4. README and getting started documentation
        5. Architecture and design documentation
        6. Key documentation improvement recommendations
        
        Provide actionable documentation insights that would improve project comprehensibility.
        
        Analysis Context: {context}
        Tool Results: {results}""" 
        