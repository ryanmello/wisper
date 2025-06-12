#!/usr/bin/env python3
"""
Whisper - Main FastAPI Application Entry Point
"""

import uvicorn

from config.settings import settings

def main():
    """Main entry point for the FastAPI application."""
    
    # Check for required environment variables
    if not settings.OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables")
        print("   The application will start but repository analysis will not work")
        print("   Please set OPENAI_API_KEY in your .env file")
    
    print(f"🚀 Starting Whisper API")
    print(f"   Host: {settings.HOST}")
    print(f"   Port: {settings.PORT}")
    print(f"   Reload: {settings.RELOAD}")
    print(f"   OpenAI API Key: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Missing'}")
    print(f"   Frontend URL: {settings.FRONTEND_URL}")
    print(f"   API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    
    # Start the server
    uvicorn.run(
        "app:app",  # Updated to use the new app.py file
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
        access_log=True
    )

if __name__ == "__main__":
    main() 