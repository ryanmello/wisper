import json
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings
from utils.logging_config import get_logger

logger = get_logger(__name__)

summarizer_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    max_tokens=100,
    api_key=settings.OPENAI_API_KEY
)

async def llm_summarize_tool_result(tool_name: str, result: Any) -> str:
    """
    Use LLM to summarize tool results while preserving critical information.
    
    Args:
        tool_name: Name of the tool that generated the result
        result: Full tool result
        
    Returns:
        XML-formatted summary: <tool_name>intelligent summary</tool_name>
    """

    try:
        if not result:
            return f"<{tool_name}>No result data available</{tool_name}>"
        
        if isinstance(result, dict) and result.get('error'):
            error_msg = str(result['error'])[:100]
            return f"<{tool_name}>Failed: {error_msg}</{tool_name}>"
        
        # Convert result to JSON for LLM processing
        result_json = json.dumps(result, default=str, indent=2)
        
        system_prompt = r"""Create concise technical summaries.

        ALWAYS include when present:
        - Package names with versions (current→target)
        - Vulnerability counts by severity (critical/high/medium)
        - File counts and primary language
        - Error messages and failure reasons
        - Success status

        CRITICAL FOR CLONE_REPOSITORY: ALWAYS preserve the clone_path (e.g., C:\Users\Ryan\AppData\Local\Temp\cipher_a4sriea9) as subsequent tools require this exact path for analysis.

        FORMAT: <tool_name>one concise sentence with key facts</tool_name>

        EXAMPLES:
        - <explore_codebase>Analyzed 1,247 Python files, MVC architecture, Django/React frameworks</explore_codebase>
        - <clone_repository>Successfully cloned to C:\Users\Ryan\AppData\Local\Temp\cipher_a4sriea9, 102 commits</clone_repository>
        """

        user_prompt = f"""Summarize this {tool_name} tool result:

        {result_json}

        Remember to preserve all critical details like package versions, error messages, counts, and status information."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await summarizer_llm.ainvoke(messages)
        summary = response.content.strip()
        
        # Validate XML format
        if not summary.startswith(f"<{tool_name}>") or not summary.endswith(f"</{tool_name}>"):
            if summary.startswith("<") and summary.endswith(">"):
                start_tag_end = summary.find(">")
                end_tag_start = summary.rfind("<")
                if start_tag_end != -1 and end_tag_start != -1:
                    content = summary[start_tag_end + 1:end_tag_start]
                    summary = f"<{tool_name}>{content}</{tool_name}>"
            else:
                summary = f"<{tool_name}>{summary}</{tool_name}>"
        
        logger.info(f"LLM summarized {tool_name}: {len(result_json)} chars → {len(summary)} chars")
        return summary
        
    except Exception as e:
        logger.warning(f"LLM summarization failed for {tool_name}: {e}")
        return f"<{tool_name}>Tool completed (LLM summarization failed)</{tool_name}>" 
