import json
import time
from typing import Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logging_config import get_logger
from utils.tool_metadata_decorator import tool_category
from config.settings import settings
from models.api_models import StandardToolResponse, StandardMetrics, StandardError

logger = get_logger(__name__)

@tool_category("reporting")
@tool
def generate_summary(tool_results: Any) -> StandardToolResponse:
    """Generate summary of all previous tool calls.
    
    Args:
        tool_results: Results from previously executed tools.
        
    Returns:
        StandardToolResponse with summary
    """
    start_time = time.time()
    logger.info("Generating summary from context window")
    
    try:
        if not settings.OPENAI_API_KEY:
            return StandardToolResponse(
                status="error",
                tool_name="generate_summary",
                data={"summary": "No OpenAI API key available"},
                summary="Summary generation failed - no API key",
                error=StandardError(
                    message="OpenAI API key not configured",
                    error_type="configuration_error"
                )
            )
        
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )
        
        system_prompt = SystemMessage(content="""
        You are an expert code analysis assistant. Analyze the repository analysis results provided and create a clear, comprehensive summary.
        
        Focus on:
        - Key findings and insights
        - Security issues if any
        - Code quality observations
        - Actionable recommendations
        
        Provide a clear, readable summary that would be useful for developers and stakeholders.
        """)
        
        human_prompt = HumanMessage(content=f"""
        Please analyze and summarize the following repository analysis results:

        {json.dumps(tool_results, indent=2, default=str)}
        """)
                
        logger.info("Sending summary request to AI")
        response = llm.invoke([system_prompt, human_prompt])
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        result = StandardToolResponse(
            status="success",
            tool_name="generate_summary",
            data={"summary": response.content},
            summary=response.content[:200] + "..." if len(response.content) > 200 else response.content,
            metrics=StandardMetrics(
                items_processed=len(tool_results) if isinstance(tool_results, dict) else 1,
                execution_time_ms=execution_time_ms
            )
        )
        
        logger.info("AI-powered summary generated successfully")
        return result
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to generate AI summary: {e}")
        
        return StandardToolResponse(
            status="error",
            tool_name="generate_summary",
            data={"summary": f"Summary generation failed: {str(e)}"},
            summary="Summary generation failed",
            metrics=StandardMetrics(
                items_processed=0,
                execution_time_ms=execution_time_ms
            ),
            error=StandardError(
                message=f"Failed to generate summary: {str(e)}",
                error_type="generation_error"
            )
        ) 
