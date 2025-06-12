"""
Context Analyzer for understanding and parsing analysis requests.

This module analyzes context from the frontend to determine the appropriate
analysis strategy and tool selection.
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from tools.base_tool import AnalysisContext
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisAction:
    """Represents a single analysis action to be performed."""
    intent: str
    confidence: float
    priority: int  # 1 = highest priority, 2 = second highest, etc.
    reasoning: str


@dataclass
class ParsedIntent:
    """Result of intent parsing with multiple scalable actions."""
    actions: List[AnalysisAction]
    overall_confidence: float
    analysis_complexity: str  # "simple", "moderate", "complex"
    reasoning: str


@dataclass
class LanguageDetection:
    """Result of language detection."""
    detected_languages: List[str]
    confidence_scores: Dict[str, float]
    evidence: Dict[str, List[str]]


class ContextAnalyzer:
    """
    Analyzes context from frontend requests to determine analysis strategy.
    
    This class parses natural language context, detects intent, identifies
    target languages, and creates structured analysis contexts.
    """
    
    def __init__(self):
        # Language patterns for detection
        self.language_patterns = {
            "go": [r"\bgo\b", r"golang", r"\.go$", r"go\.mod", r"go\.sum"],
            "python": [r"\bpython\b", r"\.py$", r"requirements\.txt", r"setup\.py", r"pyproject\.toml"],
            "javascript": [r"\bjavascript\b", r"\bjs\b", r"\.js$", r"package\.json", r"node_modules"],
            "typescript": [r"\btypescript\b", r"\bts\b", r"\.ts$", r"tsconfig\.json"],
            "java": [r"\bjava\b", r"\.java$", r"pom\.xml", r"build\.gradle"],
            "rust": [r"\brust\b", r"\.rs$", r"cargo\.toml", r"cargo\.lock"],
            "c++": [r"\bc\+\+\b", r"\bcpp\b", r"\.cpp$", r"\.cxx$", r"\.hpp$", r"cmake"],
            "c": [r"\bc\b", r"\.c$", r"\.h$"],
            "php": [r"\bphp\b", r"\.php$", r"composer\.json"],
            "ruby": [r"\bruby\b", r"\.rb$", r"gemfile"],
            "swift": [r"\bswift\b", r"\.swift$"],
            "kotlin": [r"\bkotlin\b", r"\.kt$"],
            "dart": [r"\bdart\b", r"\.dart$"],
            "scala": [r"\bscala\b", r"\.scala$"]
        }
        
        # Initialize OpenAI client - will be set when needed
        self._llm = None
    
    def _get_llm(self):
        """Get or initialize the OpenAI LLM client."""
        if self._llm is None:
            try:
                from langchain_openai import ChatOpenAI
                import os
                
                api_key = os.getenv('OPENAI_API_KEY')

                if not api_key:
                    logger.warning("No OpenAI API key found - falling back to rule-based intent detection")
                    return None
                
                self._llm = ChatOpenAI(
                    model="gpt-4",
                    temperature=0,
                    api_key=api_key
                )
                logger.info("Initialized OpenAI client for intent classification")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e} - falling back to rule-based detection")
                return None
        
        return self._llm
    
    def analyze_context(
        self, 
        context_text: str, 
        repository_url: str, 
        additional_params: Optional[Dict] = None
    ) -> AnalysisContext:
        """
        Analyze context and create structured AnalysisContext.
        
        Args:
            context_text: Natural language context from frontend
            repository_url: URL of repository to analyze
            additional_params: Optional additional parameters
            
        Returns:
            Structured AnalysisContext object
        """
        logger.info(f"Analyzing context: {context_text[:100]}...")
        
        # Parse intent from context using AI or fallback
        parsed_intent = self._parse_intent(context_text)
        
        # Detect target languages
        language_detection = self._detect_languages(context_text, repository_url)
        
        # Determine scope and depth
        scope = self._determine_scope(context_text, parsed_intent)
        depth = self._determine_depth(context_text, parsed_intent)
        
        # Extract specific files if mentioned
        specific_files = self._extract_specific_files(context_text)
        
        return AnalysisContext(
            repository_path="",  # Will be set when repository is cloned
            repository_url=repository_url,
            intent=parsed_intent.actions[0].intent,
            target_languages=language_detection.detected_languages,
            scope=scope,
            specific_files=specific_files,
            depth=depth,
            additional_params=additional_params or {}
        )
    
    async def _parse_intent_with_ai(self, context_text: str) -> Optional[ParsedIntent]:
        """
        Use AI to parse intent from context text.
        Dynamically discovers available analysis actions from the tool registry.
        
        Args:
            context_text: Context text to analyze
            
        Returns:
            ParsedIntent object or None if AI analysis fails
        """
        llm = self._get_llm()
        if not llm:
            return None
        
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            # Dynamically get available analysis actions from tool registry
            # This makes the system scalable - no hardcoded lists to maintain
            try:
                from core.tool_registry import get_tool_registry
                registry = await get_tool_registry()
                available_tools = registry.get_all_tools()
                
                # Create dynamic action descriptions from tool metadata
                action_descriptions = []
                for tool in available_tools:
                    action_descriptions.append(f"- {tool.metadata.intent}: {tool.metadata.description}")
                
                actions_list = "\n".join(action_descriptions)
                
                # If no tools are available, fall back to basic actions
                if not action_descriptions:
                    actions_list = """- explore: General codebase exploration and architecture analysis
- find_vulnerabilities: Security vulnerability scanning and finding security issues"""
                    
            except Exception as e:
                logger.debug(f"Could not load tool registry: {e}, using basic actions")
                actions_list = """- explore: General codebase exploration and architecture analysis
- find_vulnerabilities: Security vulnerability scanning and finding security issues"""
            
            system_prompt = f"""You are an expert code analysis assistant. Analyze the user's request and identify ALL relevant analysis actions they want performed.

Available analysis actions:
{actions_list}

Analyze the user's request and return a JSON response with ALL applicable actions, ranked by priority:

{{
  "actions": [
    {{
      "intent": "most important action",
      "confidence": 0.95,
      "priority": 1,
      "reasoning": "Why this is the primary action"
    }},
    {{
      "intent": "second action",
      "confidence": 0.85,
      "priority": 2, 
      "reasoning": "Why this action is also needed"
    }},
    {{
      "intent": "third action if applicable",
      "confidence": 0.75,
      "priority": 3,
      "reasoning": "Why this additional action is relevant"
    }}
  ],
  "overall_confidence": 0.9,
  "analysis_complexity": "complex",
  "reasoning": "Overall analysis of the user's multi-faceted request"
}}

Guidelines:
- Use ONLY the intent names from the available actions list above
- Identify ALL relevant actions, not just 1-2 (can be 3-5+ for complex requests)
- Rank actions by priority (1 = highest priority)
- Each action should have high confidence (>0.7) to be included
- Set analysis_complexity: "simple" (1 action), "moderate" (2-3 actions), "complex" (4+ actions)
- Be comprehensive - users often want multiple types of analysis
- Consider implied actions and relationships between different analysis types"""

            user_message = f"User request: '{context_text}'"

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            
            # Parse JSON response
            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            result = json.loads(response_text)
            
            actions = [
                AnalysisAction(
                    intent=action["intent"],
                    confidence=action["confidence"],
                    priority=action["priority"],
                    reasoning=action["reasoning"]
                ) for action in result["actions"]
            ]
            
            return ParsedIntent(
                actions=actions,
                overall_confidence=result["overall_confidence"],
                analysis_complexity=result["analysis_complexity"],
                reasoning=result["reasoning"]
            )
            
        except Exception as e:
            logger.warning(f"AI intent parsing failed: {e}")
            return None
    
    def _parse_intent_fallback(self, context_text: str) -> ParsedIntent:
        """
        Simple fallback when AI is not available.
        Returns a basic exploration intent rather than complex keyword matching.
        
        Args:
            context_text: Context text to analyze
            
        Returns:
            ParsedIntent object with basic exploration action
        """
        logger.warning("AI intent parsing unavailable, using basic fallback")
        
        # Simple fallback: always return exploration with low confidence
        # This avoids the need to maintain keyword lists that don't scale
        action = AnalysisAction(
            intent="explore",
            confidence=0.5,
            priority=1,
            reasoning="AI unavailable - defaulting to basic exploration"
        )
        
        return ParsedIntent(
            actions=[action],
            overall_confidence=0.5,
            analysis_complexity="simple",
            reasoning="AI intent analysis unavailable, using basic exploration fallback"
        )
    
    def _parse_intent(self, context_text: str) -> ParsedIntent:
        """
        Parse the primary intent from context text using AI or fallback.
        
        Args:
            context_text: Context text to analyze
            
        Returns:
            ParsedIntent object with analysis results
        """
        # Try AI-based parsing first
        try:
            logger.debug(f"Attempting AI intent parsing for: '{context_text}'")
            import asyncio
            ai_result = asyncio.run(self._parse_intent_with_ai(context_text))
            if ai_result:
                logger.info(f"AI intent parsing successful: {ai_result.actions[0].intent} (confidence: {ai_result.overall_confidence})")
                return ai_result
            else:
                logger.debug("AI intent parsing returned None, falling back to rule-based")
        except Exception as e:
            logger.debug(f"AI intent parsing failed with exception: {e}")
            logger.debug(f"Exception type: {type(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Fall back to rule-based parsing
        logger.info("Using fallback rule-based intent parsing")
        return self._parse_intent_fallback(context_text)
    
    def _detect_languages(self, context_text: str, repository_url: str) -> LanguageDetection:
        """
        Detect target programming languages from context and repository URL.
        
        Args:
            context_text: Context text to analyze
            repository_url: Repository URL for additional clues
            
        Returns:
            LanguageDetection object with results
        """
        context_lower = context_text.lower()
        repo_url_lower = repository_url.lower()
        
        language_scores = {}
        language_evidence = {}
        
        for language, patterns in self.language_patterns.items():
            score = 0
            evidence = []
            
            for pattern in patterns:
                # Check in context text
                if re.search(pattern, context_lower):
                    score += 2
                    evidence.append(f"Found '{pattern}' in context")
                
                # Check in repository URL
                if re.search(pattern, repo_url_lower):
                    score += 1
                    evidence.append(f"Found '{pattern}' in repository URL")
            
            # Check for explicit language mentions
            if language in context_lower:
                score += 3
                evidence.append(f"Explicit mention of {language}")
            
            if score > 0:
                language_scores[language] = score
                language_evidence[language] = evidence
        
        # Convert scores to confidence percentages
        if language_scores:
            max_score = max(language_scores.values())
            confidence_scores = {
                lang: score / max_score for lang, score in language_scores.items()
            }
            # Only include languages with confidence > 0.3
            detected_languages = [
                lang for lang, conf in confidence_scores.items() if conf > 0.3
            ]
        else:
            confidence_scores = {}
            detected_languages = []
        
        return LanguageDetection(
            detected_languages=detected_languages,
            confidence_scores=confidence_scores,
            evidence=language_evidence
        )
    
    def _determine_scope(self, context_text: str, parsed_intent: ParsedIntent) -> str:
        """
        Determine analysis scope from context.
        
        Args:
            context_text: Context text
            parsed_intent: Parsed intent information
            
        Returns:
            Scope string ("full", "security_focused", "performance_focused")
        """
        context_lower = context_text.lower()
        
        # Intent-based scope determination
        if parsed_intent.actions[0].intent in ["find_vulnerabilities", "security_audit"]:
            return "security_focused"
        elif parsed_intent.actions[0].intent == "analyze_performance":
            return "performance_focused"
        
        # Keyword-based scope determination
        security_keywords = ["security", "vulnerability", "exploit", "threat"]
        performance_keywords = ["performance", "optimization", "bottleneck", "speed"]
        
        if any(keyword in context_lower for keyword in security_keywords):
            return "security_focused"
        elif any(keyword in context_lower for keyword in performance_keywords):
            return "performance_focused"
        
        return "full"
    
    def _determine_depth(self, context_text: str, parsed_intent: ParsedIntent) -> str:
        """
        Determine analysis depth from context.
        
        Args:
            context_text: Context text
            parsed_intent: Parsed intent information
            
        Returns:
            Depth string ("surface", "deep", "comprehensive")
        """
        context_lower = context_text.lower()
        
        # Depth indicators
        surface_keywords = ["quick", "brief", "overview", "summary", "fast"]
        deep_keywords = ["detailed", "thorough", "comprehensive", "in-depth", "complete"]
        
        if any(keyword in context_lower for keyword in surface_keywords):
            return "surface"
        elif any(keyword in context_lower for keyword in deep_keywords):
            return "comprehensive"
        
        # Default based on intent
        if parsed_intent.actions[0].intent in ["find_vulnerabilities", "security_audit"]:
            return "deep"
        
        return "comprehensive"
    
    def _extract_specific_files(self, context_text: str) -> List[str]:
        """
        Extract specific file mentions from context.
        
        Args:
            context_text: Context text to analyze
            
        Returns:
            List of specific files mentioned
        """
        # Common file patterns
        file_patterns = [
            r'go\.mod', r'go\.sum', r'package\.json', r'requirements\.txt',
            r'Dockerfile', r'README\.md', r'\.gitignore',
            r'\w+\.(go|py|js|ts|java|cpp|c|rs|rb|php)(?:\s|$|,|\.)',
            r'[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+\.[a-zA-Z]{1,4}'
        ]
        
        specific_files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, context_text, re.IGNORECASE)
            specific_files.extend(matches)
        
        # Clean up the matches
        cleaned_files = []
        for file_match in specific_files:
            # Remove trailing punctuation
            cleaned = re.sub(r'[,.\s]+$', '', file_match)
            if cleaned and cleaned not in cleaned_files:
                cleaned_files.append(cleaned)
        
        return cleaned_files
    
    def enhance_context_with_repository_info(
        self, 
        context: AnalysisContext, 
        repository_path: str,
        detected_languages: Optional[List[str]] = None
    ) -> AnalysisContext:
        """
        Enhance context with information gathered from the repository.
        
        Args:
            context: Existing analysis context
            repository_path: Path to cloned repository
            detected_languages: Languages detected from repository scanning
            
        Returns:
            Enhanced AnalysisContext
        """
        enhanced_context = AnalysisContext(
            repository_path=repository_path,
            repository_url=context.repository_url,
            intent=context.intent,
            target_languages=detected_languages or context.target_languages,
            scope=context.scope,
            specific_files=context.specific_files,
            depth=context.depth,
            additional_params=context.additional_params
        )
        
        return enhanced_context 