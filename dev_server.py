"""Local development server for Eagle Bank API with debugging."""
import uvicorn
import os

# Set environment variables for local development
os.environ.update({
    "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5433/eagle_bank",
    "REDIS_URL": "redis://localhost:6380",
    "JWT_SECRET_KEY": "your-local-secret-key-for-development",
    "KEYCLOAK_SERVER_URL": "http://localhost:8080",
    "KEYCLOAK_REALM": "eagle-bank",
    "KEYCLOAK_CLIENT_ID": "eagle-bank-api",
    "KEYCLOAK_CLIENT_SECRET": "your-client-secret",
    "LOG_LEVEL": "DEBUG",
    "DEBUG": "true",
    "ENVIRONMENT": "development"
})

if __name__ == "__main__":
    # Import after setting environment variables
    from app.main import app
    
    print("🚀 Starting Eagle Bank API in DEBUG mode...")
    print("📍 Set breakpoints in VS Code and press F5 to debug!")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="debug"
    )
