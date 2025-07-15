import json
import time
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logging_config import get_logger
from config.settings import settings
from models.api_models import StandardToolResponse, StandardMetrics, StandardError

logger = get_logger(__name__)

@tool
def generate_summary(tool_results: Any) -> StandardToolResponse:
    """Generate AI-powered summary from analysis results to provide comprehensive insights and recommendations.
    
    This tool takes the results from multiple analysis tools and creates a cohesive, intelligent summary 
    that synthesizes findings into actionable insights.
    
    Args:
        tool_results: Results from previously executed analysis tools containing repository analysis data.
        
    Returns:
        StandardToolResponse with AI-generated summary, key insights, and recommendations
    """
    start_time = time.time()
    logger.info("Generating AI-powered summary from analysis results")
    
    try:
        if not settings.OPENAI_API_KEY:
            logger.warning("No OpenAI API key available - generating basic summary")
            return _generate_basic_fallback(tool_results, start_time)
        
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )
        
        system_prompt = SystemMessage(content=_get_system_prompt())
        
        human_prompt = HumanMessage(content=f"""
        Analyze the following repository analysis results and provide a comprehensive summary:

        {json.dumps(tool_results, indent=2, default=str)}

        Respond with a valid JSON object matching the schema provided in the system prompt.
        """)
                
        logger.info("Sending analysis request to AI")
        response = llm.invoke([system_prompt, human_prompt])
        
        summary_data = _parse_ai_response(response.content)
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        result = StandardToolResponse(
            status="success",
            tool_name="generate_summary",
            data=summary_data,
            summary=summary_data.get("executive_summary", "AI-powered analysis summary generated"),
            metrics=StandardMetrics(
                items_processed=_count_tool_results(tool_results),
                execution_time_ms=execution_time_ms
            )
        )
        
        logger.info("AI-powered summary generated successfully")
        return result
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to generate AI summary: {e}")
        logger.info("Falling back to basic summary")
        return _generate_basic_fallback(tool_results, start_time, error=str(e))

def _get_system_prompt() -> str:
    """Get the system prompt with expected response structure"""
    return """You are an expert code analysis assistant. Analyze repository analysis results and create a comprehensive, actionable summary.

    Your analysis should focus on:
    - Overall code quality and architecture
    - Security findings and risk assessment
    - Key technologies and dependencies
    - Actionable recommendations with clear priorities
    - Technical metrics and insights

    CRITICAL: You must respond with a valid JSON object that exactly matches this structure:

    {
    "executive_summary": "High-level summary for stakeholders (2-3 sentences)",
    "key_findings": ["Most important discovery 1", "Key finding 2", "..."],
    "technical_metrics": {
        "languages_count": 0,
        "total_files": 0,
        "lines_of_code": 0,
        "dependencies_count": 0,
        "architecture_patterns": ["pattern1", "pattern2"]
    },
    "security_assessment": {
        "risk_level": "low|medium|high|critical",
        "total_issues": 0,
        "vulnerabilities": 0,
        "critical_findings": ["Critical security issue 1", "..."]
    },
    "recommendations": [
        {
        "priority": "high|medium|low",
        "action": "Specific action to take",
        "rationale": "Why this matters",
        "category": "security|architecture|dependencies|maintenance"
        }
    ],
    "confidence_score": 0.9
    }

    Extract metrics from the provided data. If data is missing, use reasonable defaults (0 for counts, empty arrays for lists).
    Focus on actionable insights that would help developers, architects, and security teams.

    Respond ONLY with the JSON object - no additional text or explanation.
    """

def _parse_ai_response(response_content: str) -> Dict[str, Any]:
    """Parse LLM response and do basic validation"""
    try:
        # Parse JSON response
        response_data = json.loads(response_content)
        
        # Basic validation - ensure required fields exist with defaults
        required_structure = {
            "executive_summary": "Repository analysis completed with AI-powered insights.",
            "key_findings": [],
            "technical_metrics": {
                "languages_count": 0,
                "total_files": 0,
                "lines_of_code": 0,
                "dependencies_count": 0,
                "architecture_patterns": []
            },
            "security_assessment": {
                "risk_level": "unknown",
                "total_issues": 0,
                "vulnerabilities": 0,
                "critical_findings": []
            },
            "recommendations": [],
            "confidence_score": 0.8
        }
        
        # Merge with defaults for any missing fields
        for key, default_value in required_structure.items():
            if key not in response_data:
                response_data[key] = default_value
            elif isinstance(default_value, dict) and isinstance(response_data[key], dict):
                # Merge nested dict defaults
                for nested_key, nested_default in default_value.items():
                    if nested_key not in response_data[key]:
                        response_data[key][nested_key] = nested_default
        
        return response_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"Invalid JSON response from AI: {e}")
    
    except Exception as e:
        logger.error(f"Response validation failed: {e}")
        raise ValueError(f"Response validation error: {e}")

def _generate_basic_fallback(tool_results: Any, start_time: float, error: str = None) -> StandardToolResponse:
    """Generate basic summary when AI is not available"""
    logger.info("Generating basic fallback summary")
    
    # Extract basic metrics from tool results
    metrics = _extract_basic_metrics(tool_results)
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    summary_data = {
        "executive_summary": f"Repository analysis completed for codebase with {metrics['total_files']} files and {metrics['languages_count']} programming languages.",
        "key_findings": [
            f"Primary language: {metrics.get('primary_language', 'Unknown')}",
            f"Total dependencies: {metrics['dependencies_count']}",
            f"Security issues: {metrics['security_issues']}"
        ],
        "technical_metrics": {
            "languages_count": metrics["languages_count"],
            "total_files": metrics["total_files"],
            "lines_of_code": metrics["lines_of_code"],
            "dependencies_count": metrics["dependencies_count"],
            "architecture_patterns": metrics.get("architecture_patterns", [])
        },
        "security_assessment": {
            "risk_level": metrics.get("risk_level", "unknown"),
            "total_issues": metrics["security_issues"],
            "vulnerabilities": metrics["vulnerabilities"],
            "critical_findings": ["Analysis requires AI for detailed security assessment"]
        },
        "recommendations": [
            {
                "priority": "medium",
                "action": "Review security findings",
                "rationale": "Security issues detected that require attention",
                "category": "security"
            }
        ],
        "confidence_score": 0.5
    }
    
    # Determine status and error handling
    status = "error" if error else "partial_success"
    error_info = StandardError(
        message=f"AI summary generation failed: {error}",
        details="Fell back to basic summary generation",
        error_type="ai_generation_error"
    ) if error else None
    
    return StandardToolResponse(
        status=status,
        tool_name="generate_summary",
        data=summary_data,
        summary="Basic summary generated (AI unavailable)" if not error else "Summary generation failed - basic fallback provided",
        metrics=StandardMetrics(
            items_processed=_count_tool_results(tool_results),
            execution_time_ms=execution_time_ms
        ),
        warnings=["AI-powered analysis unavailable - basic summary provided"] if not error else None,
        error=error_info
    )

def _extract_basic_metrics(tool_results: Any) -> Dict[str, Any]:
    """Extract basic metrics from tool results for fallback"""
    metrics = {
        "languages_count": 0,
        "total_files": 0,
        "lines_of_code": 0,
        "dependencies_count": 0,
        "security_issues": 0,
        "vulnerabilities": 0
    }
    
    if not isinstance(tool_results, dict):
        return metrics
    
    # Extract from explore_codebase
    if "explore_codebase" in tool_results:
        explore_data = tool_results["explore_codebase"]
        if isinstance(explore_data, dict):
            # Language data
            lang_analysis = explore_data.get("language_analysis", {})
            if isinstance(lang_analysis, dict):
                metrics["languages_count"] = len(lang_analysis.get("languages", {}))
                metrics["primary_language"] = lang_analysis.get("primary_language", "Unknown")
            
            # File structure data
            file_structure = explore_data.get("file_structure", {})
            if isinstance(file_structure, dict):
                metrics["total_files"] = file_structure.get("total_files", 0)
                metrics["lines_of_code"] = file_structure.get("total_lines", 0)
            
            # Architecture patterns
            metrics["architecture_patterns"] = explore_data.get("architectural_patterns", [])
    
    # Extract from analyze_dependencies
    if "analyze_dependencies" in tool_results:
        dep_data = tool_results["analyze_dependencies"]
        if isinstance(dep_data, dict):
            deps_by_lang = dep_data.get("dependencies_by_language", {})
            if isinstance(deps_by_lang, dict):
                metrics["dependencies_count"] = sum(len(deps) if isinstance(deps, list) else 0 
                                                   for deps in deps_by_lang.values())
    
    # Extract from scan_go_vulnerabilities
    if "scan_go_vulnerabilities" in tool_results:
        vuln_data = tool_results["scan_go_vulnerabilities"]
        if isinstance(vuln_data, dict):
            metrics["vulnerabilities"] = vuln_data.get("vulnerabilities_found", 0)
    
    return metrics

def _count_tool_results(tool_results: Any) -> int:
    """Count number of tool results processed"""
    if isinstance(tool_results, dict):
        return len(tool_results)
    return 1 if tool_results else 0 
