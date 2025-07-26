#!/usr/bin/env python3
"""Test the correct Gemini upload API."""
import asyncio
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

async def test_upload():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Try to see what methods are available
    print("Available methods on client.aio.files:")
    print(dir(client.aio.files))
    
    # Check the upload method signature
    print("\nUpload method signature:")
    print(client.aio.files.upload.__doc__)
    
    # Try different approaches
    print("\nChecking if it's positional argument...")
    import inspect
    sig = inspect.signature(client.aio.files.upload)
    print(f"Parameters: {sig}")

if __name__ == "__main__":
    asyncio.run(test_upload())