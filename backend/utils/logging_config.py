import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", log_format: Optional[str] = None) -> None:
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name) 
