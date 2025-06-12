"""
Task management endpoints.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends

from models.api_models import (
    AnalysisRequest, AnalysisResponse, SmartAnalysisRequest, SmartAnalysisResponse,
    TaskStatus, ActiveConnectionsInfo, ToolRegistryInfo, IntentAnalysisRequest, AIAnalysis,
    GitHubServiceStatus
)
from core.app import get_analysis_service
from services.openai_service import OpenAIService
from config.settings import settings
from core.context_analyzer import ContextAnalyzer
from core.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/analyze-intent", response_model=AIAnalysis)
async def analyze_intent(request: IntentAnalysisRequest):
    """Analyze user intent using our advanced multi-action context analyzer."""
    
    try:
        # Use our new multi-action context analyzer with proper async handling
        analyzer = ContextAnalyzer()
        
        # First try AI parsing directly (proper async)
        ai_result = await analyzer._parse_intent_with_ai(request.context)
        
        if ai_result:
            # AI parsing successful
            parsed_intent = ai_result
        else:
            # Fall back to rule-based parsing
            parsed_intent = analyzer._parse_intent_fallback(request.context)
        
        # Convert our multi-action format to the expected AIAnalysis format
        detected_intents = []
        
        for action in parsed_intent.actions:
            # Map our analysis actions to the expected intent types
            intent_type_mapping = {
                "find_vulnerabilities": "Security Analysis",
                "security_audit": "Security Analysis", 
                "explore": "Architecture Analysis",
                "analyze_performance": "Performance Analysis",
                "code_quality": "Code Quality Analysis",
                "documentation": "Documentation Analysis",
                "dependency_analysis": "Dependency Analysis",
                "test_coverage": "Test Coverage Analysis",
                "compliance_check": "Compliance Analysis"
            }
            
            intent_type = intent_type_mapping.get(action.intent, "General Analysis")
            
            detected_intents.append({
                "type": intent_type,
                "confidence": action.confidence,
                "keywords": [],  # Keywords are handled internally by our AI system
                "suggestedScope": "security_focused" if "security" in action.intent else "full"
            })
        
        # Determine complexity and approach
        complexity_mapping = {
            "simple": "simple",
            "moderate": "moderate", 
            "complex": "comprehensive"
        }
        
        complexity = complexity_mapping.get(parsed_intent.analysis_complexity, "moderate")
        
        # Determine suggested approach based on number of actions
        if len(parsed_intent.actions) == 1:
            suggested_approach = "focused"
        elif len(parsed_intent.actions) <= 3:
            suggested_approach = "balanced"
        else:
            suggested_approach = "comprehensive"
        
        # Create AI analysis response
        analysis = AIAnalysis(
            intents=detected_intents,
            complexity=complexity,
            recommendation=f"Detected {len(parsed_intent.actions)} analysis action(s): {', '.join([a.intent.replace('_', ' ') for a in parsed_intent.actions])}. {parsed_intent.reasoning}",
            estimatedTime=f"{len(parsed_intent.actions) * 3}-{len(parsed_intent.actions) * 5} min",
            suggestedApproach=suggested_approach
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent analysis failed: {str(e)}")

@router.post("/tasks/", response_model=AnalysisResponse)
async def create_analysis_task(request: AnalysisRequest):
    """Create a new repository analysis task (legacy endpoint)."""
    analysis_service = get_analysis_service()
    if analysis_service is None:
        raise HTTPException(status_code=503, detail="Analysis service not available")
    
    task_id = await analysis_service.create_task(
        repository_url=request.repository_url,
        task_type=request.task_type
    )
    
    # Construct WebSocket URL
    websocket_url = f"ws://{settings.HOST}:{settings.PORT}/ws/tasks/{task_id}"
    
    return AnalysisResponse(
        task_id=task_id,
        status="created",
        message=f"Analysis task created for {request.repository_url}",
        websocket_url=websocket_url,
        task_type=request.task_type,
        repository_url=request.repository_url,
        github_pr_enabled=(request.task_type == "dependency-audit")
    )

@router.post("/smart-tasks/", response_model=SmartAnalysisResponse)
async def create_smart_analysis_task(request: SmartAnalysisRequest):
    """Create a new smart context-based analysis task."""
    analysis_service = get_analysis_service()
    if analysis_service is None:
        raise HTTPException(status_code=503, detail="Analysis service not available")
    
    task_id = await analysis_service.create_smart_task(
        repository_url=request.repository_url,
        context=request.context,
        intent=request.intent,
        target_languages=request.target_languages,
        scope=request.scope,
        depth=request.depth,
        additional_params=request.additional_params
    )
    
    # Construct WebSocket URL
    websocket_url = f"ws://{settings.HOST}:{settings.PORT}/ws/smart-tasks/{task_id}"
    
    return SmartAnalysisResponse(
        task_id=task_id,
        status="created",
        message=f"Smart analysis task created for {request.repository_url}",
        websocket_url=websocket_url,
        analysis_plan=None  # Will be populated during execution
    )

@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    analysis_service = get_analysis_service()
    if analysis_service is None:
        raise HTTPException(status_code=503, detail="Analysis service not available")
    
    status_info = analysis_service.get_task_status(task_id)
    return TaskStatus(**status_info)

@router.get("/active-connections", response_model=ActiveConnectionsInfo)
async def get_active_connections():
    """Get information about active WebSocket connections."""
    analysis_service = get_analysis_service()
    if analysis_service is None:
        raise HTTPException(status_code=503, detail="Analysis service not available")
    
    connections_info = analysis_service.get_active_connections_info()
    return ActiveConnectionsInfo(**connections_info)

@router.get("/tools", response_model=ToolRegistryInfo)
async def get_tool_registry_info():
    """Get information about available analysis tools."""
    analysis_service = get_analysis_service()
    if analysis_service is None:
        raise HTTPException(status_code=503, detail="Analysis service not available")
    
    try:
        registry_info = await analysis_service.get_tool_registry_info()
        return ToolRegistryInfo(**registry_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tool registry info: {str(e)}")

@router.get("/github/status", response_model=GitHubServiceStatus)
async def get_github_service_status():
    """Get GitHub service status and authentication information."""
    try:
        from services.github_service import github_service
        
        # Check if service is available and authenticated
        is_available = github_service.is_available()
        
        # Get rate limit info if authenticated
        rate_limit_remaining = None
        if is_available and github_service.github_client:
            try:
                rate_limit = github_service.github_client.get_rate_limit()
                rate_limit_remaining = rate_limit.core.remaining
            except Exception:
                pass  # Ignore rate limit errors
        
        return GitHubServiceStatus(
            available=is_available,
            authenticated=is_available,
            rate_limit_remaining=rate_limit_remaining
        )
        
    except ImportError as e:
        logger.warning(f"GitHub service not available due to import error: {e}")
        return GitHubServiceStatus(
            available=False,
            authenticated=False,
            rate_limit_remaining=None
        )
    except Exception as e:
        logger.error(f"Error checking GitHub service status: {e}")
        return GitHubServiceStatus(
            available=False,
            authenticated=False,
            rate_limit_remaining=None
        ) 