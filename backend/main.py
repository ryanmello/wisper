import uvicorn
from config.settings import settings

def main():
    print(f"   Starting {settings.PROJECT_NAME}")
    print(f"   Host: {settings.HOST}")
    print(f"   Port: {settings.PORT}")
    print(f"   Reload: {settings.RELOAD}")
    print(f"   OpenAI API Key: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Missing'}")
    print(f"   Frontend URL: {settings.FRONTEND_URL}")
    print(f"   API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
        access_log=True
    )

if __name__ == "__main__":
    main()
