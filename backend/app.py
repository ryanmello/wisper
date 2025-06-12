"""
Main FastAPI application entry point using the factory pattern.
"""

from core.app import create_app

# Create the FastAPI application instance
app = create_app() 
