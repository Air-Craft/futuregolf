#!/usr/bin/env python3
"""Test the correct generate_content API."""
import asyncio
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

async def test_generate():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Check the generate_content method signature
    print("Generate content method signature:")
    import inspect
    sig = inspect.signature(client.aio.models.generate_content)
    print(f"Parameters: {sig}")
    
    print("\nMethod docstring:")
    print(client.aio.models.generate_content.__doc__)

if __name__ == "__main__":
    asyncio.run(test_generate())