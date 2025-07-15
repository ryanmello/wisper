import subprocess
from langchain_core.tools import tool
from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def scan_go_vulnerabilities(repository_path: str) -> str:
    """Scan Go repository for security vulnerabilities using govulncheck.
    
    This tool specifically scans Go projects for known security vulnerabilities using the official govulncheck 
    tool. The tool analyzes Go modules and dependencies for known CVEs and security issues.
    
    Prerequisites: Repository must contain Go code.
    Go and govulncheck must be installed.
    Best used: After confirming the repository uses Go language
    
    Args:
        repository_path: Path to the cloned repository containing Go code
        
    Returns:
        Human-readable string describing vulnerability findings and recommendations.
    """
    logger.info(f"Scanning Go vulnerabilities at {repository_path}")
    
    try:
        result = subprocess.run(
            ["govulncheck", "-version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.returncode != 0:
            logger.warning("govulncheck not available")
            return "Go vulnerability scanning skipped: govulncheck tool not available"
        
        logger.info("Running govulncheck scan...")

        scan_result = subprocess.run(
            ["govulncheck", "./..."],
            cwd=repository_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120
        )
        
        output = scan_result.stdout
        logger.info("Output: " + output)
        
        if scan_result.returncode == 0:
            logger.info("govulncheck completed - no vulnerabilities found")
            return "Go Security Scan: No vulnerabilities found in Go dependencies. The project appears secure."
        else:
            return output
                
    except subprocess.TimeoutExpired:
        logger.warning("govulncheck scan timed out")
        return "Go vulnerability scan timed out after 2 minutes"
    except FileNotFoundError:
        logger.info("govulncheck not installed")
        return "Go vulnerability scanning skipped: govulncheck not installed"
    except Exception as e:
        logger.error(f"Failed to scan Go vulnerabilities: {e}")
        return f"Go vulnerability scan failed: {str(e)}"
