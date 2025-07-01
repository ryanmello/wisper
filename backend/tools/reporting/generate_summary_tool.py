"""
Generate Summary Tool - Create AI-powered comprehensive summaries from analysis results
"""

import json
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from utils.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

@tool
def generate_summary(analysis_results: Dict[str, Any], user_context: str) -> Dict[str, Any]:
    """Generate AI-powered summary from analysis results to provide comprehensive insights and recommendations.
    
    This tool takes the results from multiple analysis tools and creates a cohesive, intelligent summary 
    that synthesizes findings into actionable insights. It's particularly useful for complex analyses where 
    multiple tools have been used, as it can identify patterns and connections across different analysis results.
    
    Prerequisites: One or more analysis tools should have been run to provide analysis_results
    Best used: As a final step to synthesize and summarize findings from multiple analysis tools
    
    Args:
        analysis_results: Dictionary containing results from previously executed analysis tools
        user_context: Original user request context for tailored summary generation
        
    Returns:
        Dictionary with AI-generated summary, key insights, and recommendations
    """
    logger.info("Generating AI-powered summary from analysis results")
    
    try:
        # Initialize LLM if OpenAI API key is available
        if not settings.OPENAI_API_KEY:
            logger.warning("No OpenAI API key available - generating basic summary")
            return _generate_basic_summary(analysis_results)
        
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Prepare analysis data for AI
        prepared_data = _prepare_analysis_data(analysis_results)
        
        # Create AI prompt
        system_prompt = SystemMessage(content="""
You are an expert code analysis assistant. Analyze the provided repository analysis results and create a comprehensive, actionable summary.

Focus on:
1. Overall architecture and code quality
2. Security findings and recommendations  
3. Key technologies and dependencies
4. Main strengths and areas for improvement
5. Actionable next steps

Provide insights that would be valuable to developers, architects, and security teams.
Structure your response as a professional analysis report.
""")
        
        human_prompt = HumanMessage(content=f"""
Please analyze these repository analysis results and provide a comprehensive summary:

{json.dumps(prepared_data, indent=2)}

Provide a structured analysis with clear insights and recommendations.
""")
        
        # Generate AI summary
        response = llm.invoke([system_prompt, human_prompt])
        ai_summary = response.content
        
        # Extract key metrics
        metrics = _extract_key_metrics(analysis_results)
        
        # Generate actionable recommendations
        recommendations = _generate_recommendations(analysis_results)
        
        result = {
            "ai_summary": ai_summary,
            "key_metrics": metrics,
            "recommendations": recommendations,
            "analysis_timestamp": _get_timestamp(),
            "summary_type": "ai_powered"
        }
        
        logger.info("AI-powered summary generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate AI summary: {e}")
        logger.info("Falling back to basic summary")
        return _generate_basic_summary(analysis_results)

def _prepare_analysis_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare analysis data for AI consumption, filtering out noise."""
    prepared = {}
    
    # File structure summary
    if "file_structure" in results:
        fs = results["file_structure"]
        prepared["file_structure"] = {
            "total_files": fs.get("total_files", 0),
            "total_lines": fs.get("total_lines", 0),
            "main_file_types": dict(list(fs.get("file_types", {}).items())[:10]),
            "main_directories": fs.get("main_directories", [])[:10]
        }
    
    # Language analysis
    if "language_analysis" in results:
        lang = results["language_analysis"]
        prepared["languages"] = {
            "primary": lang.get("primary_language", "Unknown"),
            "all_languages": lang.get("languages", {}),
            "frameworks": lang.get("frameworks", [])
        }
    
    # Architecture patterns
    if "architectural_patterns" in results:
        prepared["architecture"] = {
            "patterns": results["architectural_patterns"],
            "components": results.get("main_components", [])[:5]  # Top 5 components
        }
    
    # Dependencies
    if "dependencies_by_language" in results:
        prepared["dependencies"] = results["dependencies_by_language"]
    
    # Security findings
    if "security_issues" in results:
        prepared["security"] = {
            "total_issues": len(results["security_issues"]),
            "risk_level": results.get("risk_level", "unknown"),
            "issue_summary": _summarize_security_issues(results["security_issues"])
        }
    
    # Vulnerability scan results
    if "vulnerabilities_found" in results:
        prepared["vulnerabilities"] = {
            "count": results["vulnerabilities_found"],
            "status": results.get("status", "unknown")
        }
    
    return prepared

def _summarize_security_issues(issues: list) -> Dict[str, int]:
    """Summarize security issues by type and severity."""
    summary = {"by_severity": {"high": 0, "medium": 0, "low": 0}, "by_type": {}}
    
    for issue in issues:
        severity = issue.get("severity", "low")
        issue_type = issue.get("type", "unknown")
        
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        summary["by_type"][issue_type] = summary["by_type"].get(issue_type, 0) + 1
    
    return summary

def _extract_key_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key quantitative metrics from analysis results."""
    metrics = {}
    
    # Code metrics
    if "file_structure" in results:
        fs = results["file_structure"]
        metrics["code_files"] = fs.get("total_files", 0)
        metrics["lines_of_code"] = fs.get("total_lines", 0)
    
    # Language diversity
    if "language_analysis" in results:
        lang = results["language_analysis"]
        metrics["languages_count"] = len(lang.get("languages", {}))
        metrics["frameworks_count"] = len(lang.get("frameworks", []))
    
    # Dependency metrics
    if "dependencies_by_language" in results:
        deps = results["dependencies_by_language"]
        metrics["total_dependencies"] = sum(len(d) for d in deps.values())
        metrics["dependency_ecosystems"] = len(deps)
    
    # Security metrics
    if "security_issues" in results:
        metrics["security_issues"] = len(results["security_issues"])
        metrics["risk_level"] = results.get("risk_level", "unknown")
    
    if "vulnerabilities_found" in results:
        metrics["vulnerabilities"] = results["vulnerabilities_found"]
    
    # Architecture complexity
    if "architectural_patterns" in results:
        metrics["architecture_patterns"] = len(results["architectural_patterns"])
    
    if "main_components" in results:
        metrics["main_components"] = len(results["main_components"])
    
    return metrics

def _generate_recommendations(results: Dict[str, Any]) -> list:
    """Generate actionable recommendations based on analysis results."""
    recommendations = []
    
    # Security recommendations
    if "security_issues" in results and results["security_issues"]:
        recommendations.append("Address identified security issues to improve code safety")
    
    if "vulnerabilities_found" in results and results["vulnerabilities_found"] > 0:
        recommendations.append("Update dependencies to fix security vulnerabilities")
    
    # Architecture recommendations
    if "architectural_patterns" in results:
        patterns = results["architectural_patterns"]
        if not patterns:
            recommendations.append("Consider implementing clear architectural patterns for better maintainability")
        elif len(patterns) > 5:
            recommendations.append("Review architectural complexity - multiple patterns detected")
    
    # Dependency recommendations
    if "dependencies_by_language" in results:
        deps = results["dependencies_by_language"]
        total_deps = sum(len(d) for d in deps.values())
        if total_deps > 50:
            recommendations.append("Consider dependency audit - high number of dependencies detected")
    
    # Code organization recommendations
    if "file_structure" in results:
        fs = results["file_structure"]
        if fs.get("total_files", 0) > 1000:
            recommendations.append("Consider modularization strategies for large codebase")
    
    # Default recommendations
    if not recommendations:
        recommendations.append("Codebase appears well-structured - continue following best practices")
    
    return recommendations

def _generate_basic_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate basic summary without AI when OpenAI is not available."""
    summary_parts = []
    
    # File structure summary
    if "file_structure" in results:
        fs = results["file_structure"]
        summary_parts.append(f"Repository contains {fs.get('total_files', 0)} files with {fs.get('total_lines', 0)} lines of code.")
    
    # Language summary
    if "language_analysis" in results:
        lang = results["language_analysis"]
        primary = lang.get("primary_language", "Unknown")
        frameworks = lang.get("frameworks", [])
        summary_parts.append(f"Primary language: {primary}.")
        if frameworks:
            framework_names = [f["name"] for f in frameworks]
            summary_parts.append(f"Detected frameworks: {', '.join(framework_names)}.")
    
    # Security summary
    if "security_issues" in results:
        issues = results["security_issues"]
        if issues:
            summary_parts.append(f"Found {len(issues)} security issues requiring attention.")
        else:
            summary_parts.append("No major security issues detected.")
    
    # Vulnerability summary
    if "vulnerabilities_found" in results:
        vulns = results["vulnerabilities_found"]
        if vulns > 0:
            summary_parts.append(f"Found {vulns} security vulnerabilities in dependencies.")
        else:
            summary_parts.append("No vulnerabilities found in dependencies.")
    
    basic_summary = " ".join(summary_parts)
    
    return {
        "ai_summary": basic_summary,
        "key_metrics": _extract_key_metrics(results),
        "recommendations": _generate_recommendations(results),
        "analysis_timestamp": _get_timestamp(),
        "summary_type": "basic"
    }

def _get_timestamp() -> str:
    """Get current timestamp for the summary."""
    from datetime import datetime
    return datetime.now().isoformat() 