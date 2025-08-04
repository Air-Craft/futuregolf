#!/usr/bin/env python3
"""
Startup script for the FutureGolf FastAPI server
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load .env file before anything else
load_dotenv()

if __name__ == "__main__":
    # Load environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    print(f"🔧 Server running on: {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level=log_level
    )
