"""
OpenAI Service for intent analysis and AI-powered features.
"""

import os
import json
from typing import Optional
import httpx
from models.api_models import AIAnalysis, DetectedIntent

class OpenAIService:
    """Service for handling OpenAI API calls."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        
    async def analyze_intent(self, context: str, repository: str, max_tokens: int = 200) -> AIAnalysis:
        """Analyze user intent using OpenAI API."""
        if not self.api_key:
            # Fallback to simple analysis if no OpenAI key
            return self._simple_fallback_analysis(context)
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": self._get_system_prompt()
                            },
                            {
                                "role": "user", 
                                "content": f"Repository: {repository}\n\nUser request: \"{context}\"\n\nAnalyze this request and return the JSON response."
                            }
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.3
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.status_code}")
                    
                response_data = response.json()
                ai_response = response_data["choices"][0]["message"]["content"]
                
                try:
                    # Parse the AI response as JSON
                    analysis_data = json.loads(ai_response)
                    return AIAnalysis(**analysis_data)
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Fallback if AI response is malformed
                    return self._simple_fallback_analysis(context)
                    
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
            return self._simple_fallback_analysis(context)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for intent analysis."""
        return """You are an expert code analysis assistant. Analyze the user's request to understand what types of code analysis they want. 

IMPORTANT: Look for ALL analysis types mentioned in the request, even if they use different words. Users often want multiple types of analysis in one request.

Possible analysis types:
- Security Analysis (vulnerabilities, security issues, secrets, exploits, threats)
- Performance Analysis (optimization, bottlenecks, memory issues, speed, efficiency)
- Code Quality Review (bugs, code smells, best practices, maintainability)
- Architecture Analysis (structure, patterns, dependencies, explore, overview, understand)
- Documentation Review (missing docs, code comments, documentation quality)
- Testing Analysis (test coverage, test quality, testing gaps)

Common keywords that indicate Architecture Analysis:
- "explore", "overview", "understand", "analyze structure", "codebase", "architecture", "components", "modules"

Return a JSON object with this exact structure:
{
  "intents": [
    {
      "type": "Security Analysis",
      "confidence": 0.9,
      "keywords": ["security", "vulnerability"],
      "suggestedScope": "security_focused"
    },
    {
      "type": "Architecture Analysis", 
      "confidence": 0.85,
      "keywords": ["explore", "codebase"],
      "suggestedScope": "full"
    }
  ],
  "complexity": "moderate",
  "recommendation": "Multiple analysis types detected. Recommend comprehensive analysis using security scanning tools AND architectural analysis tools to explore codebase structure and identify vulnerabilities.",
  "estimatedTime": "15-25 min",
  "suggestedApproach": "comprehensive"
}

Critical Rules:
1. DETECT ALL analysis types mentioned, don't just pick the strongest one
2. If user says "explore" + anything else, always include Architecture Analysis
3. Multiple intents should result in "comprehensive" or "multiple_focused" approach
4. Emphasize using MULTIPLE TOOLS when multiple intents are detected
5. confidence should reflect how clearly that intent is expressed (0.0-1.0)
6. suggestedScope: "security_focused", "performance_focused", or "full" 
7. complexity: "simple" (1 intent), "moderate" (2-3 intents), "complex" (4+ intents)
8. Always mention specific tools in recommendations when multiple intents detected"""

    def _simple_fallback_analysis(self, context: str) -> AIAnalysis:
        """Fallback analysis when OpenAI API is not available."""
        context_lower = context.lower()
        intents = []

        # Check for Security Analysis
        if any(keyword in context_lower for keyword in ['security', 'vulnerabilit', 'exploit', 'threat']):
            intents.append(DetectedIntent(
                type="Security Analysis",
                confidence=0.8,
                keywords=['security', 'vulnerability', 'exploit', 'threat'],
                suggestedScope='security_focused'
            ))

        # Check for Performance Analysis
        if any(keyword in context_lower for keyword in ['performance', 'optimization', 'speed', 'memory', 'bottleneck']):
            intents.append(DetectedIntent(
                type="Performance Analysis",
                confidence=0.8,
                keywords=['performance', 'optimization', 'speed', 'memory'],
                suggestedScope='performance_focused'
            ))

        # Check for Architecture/Exploration Analysis
        if any(keyword in context_lower for keyword in ['explore', 'architecture', 'codebase', 'structure', 'overview', 'understand']):
            intents.append(DetectedIntent(
                type="Architecture Analysis",
                confidence=0.8,
                keywords=['explore', 'architecture', 'codebase', 'structure'],
                suggestedScope='full'
            ))

        # Check for Code Quality Review
        if any(keyword in context_lower for keyword in ['bug', 'quality', 'best practice', 'code smell']):
            intents.append(DetectedIntent(
                type="Code Quality Review",
                confidence=0.7,
                keywords=['bug', 'quality', 'best practice'],
                suggestedScope='full'
            ))

        # Check for Documentation Review
        if any(keyword in context_lower for keyword in ['documentation', 'comment', 'doc']):
            intents.append(DetectedIntent(
                type="Documentation Review",
                confidence=0.7,
                keywords=['documentation', 'comment', 'doc'],
                suggestedScope='full'
            ))

        # Default if no specific intents detected
        if not intents:
            intents.append(DetectedIntent(
                type="General Analysis",
                confidence=0.5,
                keywords=[],
                suggestedScope='full'
            ))

        # Generate recommendation
        if len(intents) > 1:
            intent_names = ', '.join(intent.type for intent in intents)
            tool_suggestions = []
            for intent in intents:
                if intent.type == 'Security Analysis':
                    tool_suggestions.append('security scanners')
                elif intent.type == 'Performance Analysis':
                    tool_suggestions.append('performance profilers')
                elif intent.type == 'Architecture Analysis':
                    tool_suggestions.append('architectural analysis tools')
                elif intent.type == 'Code Quality Review':
                    tool_suggestions.append('code quality tools')
                elif intent.type == 'Documentation Review':
                    tool_suggestions.append('documentation analyzers')
                else:
                    tool_suggestions.append('general analysis tools')
            
            recommendation = f"Multiple analysis types detected ({intent_names}). Recommend comprehensive analysis using multiple tools: {' AND '.join(tool_suggestions)} to address all goals."
        else:
            recommendation = f"Single {intents[0].type.lower()} detected. Focused analysis recommended using specialized tools."

        return AIAnalysis(
            intents=intents,
            complexity='complex' if len(intents) > 2 else 'moderate' if len(intents) > 1 else 'simple',
            recommendation=recommendation,
            estimatedTime='20-35 min' if len(intents) > 2 else '15-25 min' if len(intents) > 1 else '10-15 min',
            suggestedApproach='comprehensive' if len(intents) > 1 else 'single_analysis'
        ) 