#!/usr/bin/env python3
import asyncio
import websockets
import json
import base64
from datetime import datetime

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/detect-golf-swing"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send a test frame
            test_data = {
                "timestamp": datetime.now().timestamp(),
                "image_base64": base64.b64encode(b"dummy_image_data").decode()
            }
            
            await websocket.send(json.dumps(test_data))
            print("📤 Sent test frame")
            
            # Receive response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            # Parse and display
            data = json.loads(response)
            print(f"📊 Status: {data.get('status')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())