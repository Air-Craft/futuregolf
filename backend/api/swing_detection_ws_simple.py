"""
AI Swing Detection WebSocket API - Simplified Version
Based on AI_SWING_DETECTION.md specification

Uses Google Gemini directly for easier testing and debugging.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any
import json
import asyncio
import logging
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config.swing_detection import (
    LLM_MODEL,
    LLM_SUBMISSION_THRESHOLD,
    CONTEXT_EXPIRY_SECONDS,
    MAX_IMAGE_BUFFER,
    IMAGE_MAX_SIZE,
    IMAGE_JPEG_QUALITY,
    CONFIDENCE_THRESHOLD,
    POST_DETECTION_COOLDOWN,
    IMAGE_CONVERT_BW
)

router = APIRouter(prefix="/ws", tags=["swing_detection"])

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class SwingDetectionSession:
    """Manages a single swing detection session"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.image_buffer: List[Dict[str, Any]] = []
        self.first_timestamp: Optional[float] = None
        self.last_timestamp: Optional[float] = None
        self.conversation_history: List[Dict[str, Any]] = []
        self.last_confidence: Optional[float] = None
        self.cooldown_until: Optional[float] = None
        self.swings_detected: int = 0
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel(
            model_name=LLM_MODEL.replace("gemini/", ""),
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=300,
            )
        )
    
    def add_image(self, timestamp: float, image_base64: str):
        """Add image to buffer and maintain sort order"""
        self.image_buffer.append({
            "timestamp": timestamp,
            "image": image_base64
        })
        
        # Sort by timestamp
        self.image_buffer.sort(key=lambda x: x["timestamp"])
        
        # Trim buffer if too large
        if len(self.image_buffer) > MAX_IMAGE_BUFFER:
            self.image_buffer = self.image_buffer[-MAX_IMAGE_BUFFER:]
        
        # Update timestamps
        if self.image_buffer:
            self.first_timestamp = self.image_buffer[0]["timestamp"]
            self.last_timestamp = self.image_buffer[-1]["timestamp"]
    
    def apply_rolling_window(self, current_timestamp: float):
        """Remove images older than CONTEXT_EXPIRY_SECONDS"""
        cutoff_time = current_timestamp - CONTEXT_EXPIRY_SECONDS
        self.image_buffer = [
            img for img in self.image_buffer 
            if img["timestamp"] > cutoff_time
        ]
        
        # Update first timestamp
        if self.image_buffer:
            self.first_timestamp = self.image_buffer[0]["timestamp"]
        else:
            self.first_timestamp = None
    
    def should_submit_to_llm(self) -> bool:
        """Check if we should submit to LLM based on time threshold"""
        if not self.first_timestamp or not self.last_timestamp:
            return False
        
        time_span = self.last_timestamp - self.first_timestamp
        return time_span >= LLM_SUBMISSION_THRESHOLD
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get current context window and size information"""
        context_window = 0.0
        if self.first_timestamp and self.last_timestamp:
            context_window = self.last_timestamp - self.first_timestamp
        
        # Estimate context size (simplified - just count images)
        context_size_kb = len(self.image_buffer) * 50  # Rough estimate
        
        return {
            "context_window": context_window,
            "context_size": context_size_kb
        }
    
    def clear_context(self):
        """Clear memory and image buffer after swing detection"""
        self.image_buffer = []
        self.first_timestamp = None
        self.last_timestamp = None
        self.conversation_history = []
    
    async def analyze_for_swing(self) -> Dict[str, Any]:
        """Analyze image sequence for golf swing using Gemini"""
        if not self.image_buffer:
            return {
                "swing_detected": False,
                "reason": "No images in buffer"
            }
        
        try:
            # Prepare images for Gemini
            parts = []
            
            # Add the prompt
            parts.append("""You are analyzing a sequence of images from a golf swing video. Determine if this shows a golf swing.

CRITERIA for detecting a golf swing:
1. Setup/Address: Player standing over ball, club at rest
2. Backswing: Club moves back and up to the top
3. Downswing: Club accelerates down toward ball
4. Impact: Club contacts ball
5. Follow-through: Club continues up after impact (SWING IS COMPLETE HERE)

IMPORTANT: 
- Detect the swing as soon as follow-through is visible. Don't wait for full finish.
- Only detect ONE swing per sequence.
- A person simply moving out of frame or adjusting position is NOT a swing.
- If the sequence shows someone mid-swing or ending a swing, that's NOT a complete swing.

Confidence scoring:
- 0.9-1.0: Clear swing with follow-through visible
- 0.8-0.9: Swing detected, minor visibility issues
- 0.7-0.8: Likely swing, some phases unclear
- 0.5-0.7: Questionable, missing key phases
- 0.0-0.5: Not a swing (partial, practice motion, or person exiting)

Be conservative - when in doubt, give lower confidence.
Respond with JSON: {"swing_detected": true/false, "confidence": 0.0-1.0}""")
            
            # Add images
            for idx, img_data in enumerate(self.image_buffer):
                # Decode and prepare image
                image_bytes = base64.b64decode(img_data["image"])
                image = Image.open(BytesIO(image_bytes))
                
                # Resize if needed
                if image.size[0] > IMAGE_MAX_SIZE[0] or image.size[1] > IMAGE_MAX_SIZE[1]:
                    image.thumbnail(IMAGE_MAX_SIZE, Image.Resampling.LANCZOS)
                
                parts.append(image)
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                parts
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            if "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                # Fallback parsing
                result = {
                    "swing_detected": False,
                    "confidence": 0.0
                }
            
            # Store confidence for later use
            self.last_confidence = result.get("confidence", 0.0)
            
            logger.info(f"Swing analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing swing: {e}")
            return {
                "swing_detected": False,
                "confidence": 0.0
            }

class SwingDetectionManager:
    """Manages all active swing detection sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, SwingDetectionSession] = {}
    
    async def create_session(self, websocket: WebSocket) -> str:
        """Create new session and return session ID"""
        session_id = f"session_{datetime.now().timestamp()}"
        self.sessions[session_id] = SwingDetectionSession(websocket)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SwingDetectionSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """Remove session on disconnect"""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Global session manager
session_manager = SwingDetectionManager()

def resize_and_compress_image(image_base64: str) -> str:
    """Resize and compress image for faster processing"""
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert to grayscale if configured
        if IMAGE_CONVERT_BW:
            image = image.convert('L')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize maintaining aspect ratio
        image.thumbnail(IMAGE_MAX_SIZE, Image.Resampling.LANCZOS)
        
        # Compress and encode back to base64
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=IMAGE_JPEG_QUALITY, optimize=True)
        compressed_bytes = buffer.getvalue()
        compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
        
        return compressed_b64
        
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        return image_base64  # Return original if compression fails

@router.websocket("/detect-golf-swing")
async def detect_golf_swing_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for golf swing detection
    Accepts stream of images with timestamps and detects complete swings
    """
    
    # Accept connection and create session
    await websocket.accept()
    session_id = await session_manager.create_session(websocket)
    session = session_manager.get_session(session_id)
    
    logger.info(f"New swing detection session started: {session_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Extract timestamp and image
            timestamp = data.get("timestamp")
            image_base64 = data.get("image_base64")
            
            if timestamp is None or not image_base64:
                await websocket.send_json({
                    "error": "Missing timestamp or image_base64"
                })
                continue
            
            # Compress image before storing
            compressed_image = resize_and_compress_image(image_base64)
            
            # Add image to buffer
            session.add_image(float(timestamp), compressed_image)
            
            # Check if we're in cooldown period
            current_time = float(timestamp)
            if session.cooldown_until and current_time < session.cooldown_until:
                # Still in cooldown, send waiting response
                response = {
                    "status": "cooldown",
                    "cooldown_remaining": session.cooldown_until - current_time,
                    "swings_detected": session.swings_detected
                }
                await websocket.send_json(response)
                continue
            
            # Apply rolling window to remove old images
            session.apply_rolling_window(current_time)
            
            # Get context info
            context_info = session.get_context_info()
            
            # Check if we should submit to LLM
            if session.should_submit_to_llm():
                # Analyze for swing
                result = await session.analyze_for_swing()
                
                confidence = result.get("confidence", 0.0)
                swing_detected = result.get("swing_detected", False)
                
                # Check if confidence meets threshold
                if swing_detected and confidence >= CONFIDENCE_THRESHOLD:
                    # Send detection response
                    response = {
                        "status": "evaluated",
                        "swing_detected": True,
                        "confidence": confidence,
                        "timestamp": timestamp,
                        "context_window": context_info["context_window"],
                        "context_size": context_info["context_size"]
                    }
                    await websocket.send_json(response)
                    
                    # Check if we've detected 3 swings (for testing)
                    if session.swings_detected >= 3:
                        await websocket.send_json({
                            "status": "test_complete",
                            "message": "3 swings detected, test complete",
                            "total_swings": session.swings_detected
                        })
                        break
                    
                    # Clear context for next swing
                    session.clear_context()
                    session.swings_detected += 1
                    session.cooldown_until = timestamp + POST_DETECTION_COOLDOWN
                    logger.info(f"Swing {session.swings_detected} detected in session {session_id} with confidence {confidence}")
                else:
                    # Continue collecting data
                    response = {
                        "status": "awaiting_more_data",
                        "swing_detected": False,
                        "confidence": confidence if swing_detected else 0.0,
                        "context_window": context_info["context_window"],
                        "context_size": context_info["context_size"]
                    }
                    await websocket.send_json(response)
                    
                    if swing_detected and confidence < CONFIDENCE_THRESHOLD:
                        logger.info(f"Low confidence swing rejected: {confidence} < {CONFIDENCE_THRESHOLD}")
            else:
                # Not enough data yet
                response = {
                    "status": "awaiting_more_data", 
                    "context_window": context_info["context_window"],
                    "context_size": context_info["context_size"]
                }
                await websocket.send_json(response)
    
    except WebSocketDisconnect:
        logger.info(f"Session {session_id} disconnected")
    except Exception as e:
        logger.error(f"Error in session {session_id}: {e}")
        try:
            await websocket.send_json({
                "error": str(e),
                "status": "error"
            })
        except:
            pass
    finally:
        # Cleanup session
        session_manager.remove_session(session_id)
        logger.info(f"Session {session_id} cleaned up")