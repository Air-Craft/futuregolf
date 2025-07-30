"""  
Recording Swing Detection API - Handles swing detection from still images
Based on VIDEO_RECORDING.md spec lines 56-62
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
import logging
from datetime import datetime
import openai
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image
import tempfile

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/v1/recording", tags=["recording"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI client for LLM processing
openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SwingDetectionRequest(BaseModel):
    """Request model for swing detection"""
    session_id: str
    image_data: str  # Base64 encoded image
    sequence_number: int
    timestamp: Optional[str] = None

class SwingDetectionResponse(BaseModel):
    """Response model for swing detection"""
    swing_detected: bool
    confidence: float
    swing_phase: Optional[str] = None
    reason: str
    session_id: str
    sequence_number: int
    timestamp: str

class SwingSessionManager:
    """Manages swing analysis sessions and context"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.max_images_per_session = 50  # Keep last 50 images for context
    
    def create_session(self, session_id: str):
        """Create a new swing analysis session"""
        self.sessions[session_id] = {
            "images": [],
            "swings_detected": 0,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        logger.info(f"Created swing detection session: {session_id}")
    
    def add_image(self, session_id: str, image_data: str, sequence_number: int):
        """Add image to session context"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        session = self.sessions[session_id]
        session["images"].append({
            "sequence_number": sequence_number,
            "image_data": image_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent images to manage memory
        if len(session["images"]) > self.max_images_per_session:
            session["images"] = session["images"][-self.max_images_per_session:]
        
        session["last_activity"] = datetime.now().isoformat()
    
    def record_swing(self, session_id: str):
        """Record that a swing was detected"""
        if session_id in self.sessions:
            self.sessions[session_id]["swings_detected"] += 1
            logger.info(f"Swing #{self.sessions[session_id]['swings_detected']} detected in session {session_id}")
    
    def get_session_context(self, session_id: str) -> Dict:
        """Get session context for analysis"""
        return self.sessions.get(session_id, {})
    
    def reset_session_context(self, session_id: str):
        """Reset session context after swing detection"""
        if session_id in self.sessions:
            # Keep session metadata but clear image history for next swing
            session = self.sessions[session_id]
            session["images"] = []
            session["last_activity"] = datetime.now().isoformat()
            logger.info(f"Reset context for session {session_id}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 2):
        """Clean up old inactive sessions"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            last_activity = datetime.fromisoformat(session["last_activity"])
            age_hours = (current_time - last_activity).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")

# Global session manager
session_manager = SwingSessionManager()

def resize_and_compress_image(image_data: str, max_size: tuple = (640, 480), quality: int = 75) -> str:
    """
    Resize and compress image for faster LLM processing
    Based on spec requirement for minimum size for fastest transfer
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize maintaining aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Compress and encode back to base64
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        compressed_bytes = buffer.getvalue()
        compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
        
        original_size = len(base64.b64decode(image_data))
        compressed_size = len(compressed_bytes)
        compression_ratio = compressed_size / original_size
        
        logger.info(f"Image compressed: {original_size} -> {compressed_size} bytes ({compression_ratio:.2%})")
        
        return compressed_b64
        
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        return image_data  # Return original if compression fails

async def analyze_swing_sequence(session_id: str, current_image: str, sequence_number: int) -> tuple[bool, float, str, str]:
    """
    Analyze sequence of images to determine if a complete golf swing has occurred
    Uses vision LLM to analyze golf swing progression
    """
    
    # Get session context
    session_context = session_manager.get_session_context(session_id)
    previous_images = session_context.get("images", [])
    
    # Take last 8 images for context (about 2 seconds at 0.25s intervals)
    context_images = previous_images[-8:] if len(previous_images) > 8 else previous_images
    
    # Prepare images for analysis
    images_for_analysis = []
    
    # Add context images
    for img_data in context_images[-4:]:  # Last 4 context images
        compressed = resize_and_compress_image(img_data["image_data"])
        images_for_analysis.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{compressed}",
                "detail": "low"
            }
        })
    
    # Add current image
    compressed_current = resize_and_compress_image(current_image)
    images_for_analysis.append({
        "type": "image_url", 
        "image_url": {
            "url": f"data:image/jpeg;base64,{compressed_current}",
            "detail": "high"
        }
    })
    
    # Create prompt for swing analysis
    swing_count = session_context.get("swings_detected", 0)
    
    prompt = f"""You are analyzing a sequence of images from a golf swing recording app. The images are captured every 0.25 seconds during recording.

Current context:
- Session has detected {swing_count} complete swings so far
- This is sequence #{sequence_number} in the current session
- You are looking at the last few frames leading up to the current frame

Your task is to determine if this sequence of images shows a COMPLETE golf swing from start to finish.

A complete golf swing includes these phases in order:
1. **Setup/Address**: Player positioned behind ball, club at address
2. **Takeaway**: Initial backward movement of club
3. **Backswing**: Club moving up and back to the top
4. **Transition**: Brief pause/change of direction at top
5. **Downswing**: Club accelerating down toward ball
6. **Impact**: Club making contact with ball
7. **Follow-through**: Club continuing through and up after impact
8. **Finish**: Final position with club high and body rotated

Look for these key indicators of a COMPLETE swing:
- Clear progression through all phases
- Visible ball contact/impact moment
- Follow-through motion after impact
- Return to relatively stable finish position
- Natural golf swing rhythm and timing

Do NOT detect a swing if:
- Only partial phases are visible (like just backswing)
- Player is still in setup or practice motions
- No clear impact/ball contact occurred
- Swing appears incomplete or interrupted
- Images show non-swing movements

Be conservative - only detect complete, full swings from setup to finish.

Respond with JSON containing:
- swing_detected: boolean (true only if complete swing from start to finish)
- confidence: float (0.0 to 1.0)
- swing_phase: string (current phase if swing in progress, or "complete" if full swing detected)
- reason: string (brief explanation of decision)

Example responses:
{{"swing_detected": true, "confidence": 0.9, "swing_phase": "complete", "reason": "Complete swing sequence visible from address through impact to finish"}}
{{"swing_detected": false, "confidence": 0.7, "swing_phase": "backswing", "reason": "Player in middle of backswing, swing not yet complete"}}
{{"swing_detected": false, "confidence": 0.6, "swing_phase": "setup", "reason": "Player still in address position, no swing motion detected"}}
"""

    try:
        # Build messages with text and images
        messages = [
            {
                "role": "system", 
                "content": "You are a golf swing analysis expert. Analyze image sequences to detect complete golf swings. Respond only with valid JSON."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *images_for_analysis
                ]
            }
        ]
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",  # Using vision model
            messages=messages,
            temperature=0.1,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            result = json.loads(result_text)
            swing_detected = result.get("swing_detected", False)
            confidence = result.get("confidence", 0.0)
            swing_phase = result.get("swing_phase", "unknown")
            reason = result.get("reason", "No reason provided")
            
            logger.info(f"Swing analysis result: detected={swing_detected}, confidence={confidence}, phase={swing_phase}")
            
            return swing_detected, confidence, swing_phase, reason
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {result_text}, error: {e}")
            return False, 0.0, "unknown", "Failed to parse AI response"
    
    except Exception as e:
        logger.error(f"Error in swing analysis: {e}")
        return False, 0.0, "unknown", f"Analysis error: {str(e)}"

@router.post("/swing/detect", response_model=SwingDetectionResponse)
async def detect_swing(request: SwingDetectionRequest):
    """
    Analyze still image to detect if a complete golf swing has occurred
    Main endpoint called every 0.25 seconds during recording
    """
    
    if not request.image_data:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Add image to session context
    session_manager.add_image(
        request.session_id, 
        request.image_data, 
        request.sequence_number
    )
    
    # Analyze swing sequence
    swing_detected, confidence, swing_phase, reason = await analyze_swing_sequence(
        request.session_id,
        request.image_data,
        request.sequence_number
    )
    
    # If swing detected, record it and reset context for next swing
    if swing_detected and confidence > 0.7:  # High confidence threshold
        session_manager.record_swing(request.session_id)
        session_manager.reset_session_context(request.session_id)
    
    return SwingDetectionResponse(
        swing_detected=swing_detected,
        confidence=confidence,
        swing_phase=swing_phase,
        reason=reason,
        session_id=request.session_id,
        sequence_number=request.sequence_number,
        timestamp=datetime.now().isoformat()
    )

@router.post("/swing/detect-upload")
async def detect_swing_upload(
    session_id: str = Form(...),
    sequence_number: int = Form(...),
    image: UploadFile = File(...)
):
    """
    Alternative endpoint that accepts image file upload instead of base64
    """
    
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read and encode image
        image_bytes = await image.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create request object
        request = SwingDetectionRequest(
            session_id=session_id,
            image_data=image_b64,
            sequence_number=sequence_number,
            timestamp=datetime.now().isoformat()
        )
        
        # Process request
        return await detect_swing(request)
        
    except Exception as e:
        logger.error(f"Error processing uploaded image: {e}")
        raise HTTPException(status_code=500, detail="Failed to process image")

@router.get("/swing/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Get current status of swing detection session
    """
    
    session = session_manager.get_session_context(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "swings_detected": session.get("swings_detected", 0),
        "images_in_context": len(session.get("images", [])),
        "created_at": session.get("created_at"),
        "last_activity": session.get("last_activity"),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/swing/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """
    Reset swing detection session context
    Useful when starting a new recording or after a swing is detected
    """
    
    session_manager.reset_session_context(session_id)
    
    return {
        "message": f"Session {session_id} context reset",
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/swing/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete swing detection session completely
    """
    
    if session_id in session_manager.sessions:
        del session_manager.sessions[session_id]
        return {
            "message": f"Session {session_id} deleted",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@router.get("/swing/health")
async def swing_service_health():
    """
    Health check for swing detection service
    """
    
    total_sessions = len(session_manager.sessions)
    active_sessions = sum(1 for s in session_manager.sessions.values() 
                         if (datetime.now() - datetime.fromisoformat(s["last_activity"])).total_seconds() < 300)
    
    return {
        "status": "healthy",
        "service": "swing_detection",
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/swing/cleanup")
async def cleanup_old_sessions():
    """
    Manually trigger cleanup of old inactive sessions
    """
    
    before_count = len(session_manager.sessions)
    session_manager.cleanup_old_sessions()
    after_count = len(session_manager.sessions)
    cleaned_count = before_count - after_count
    
    return {
        "message": f"Cleaned up {cleaned_count} old sessions",
        "sessions_before": before_count,
        "sessions_after": after_count,
        "timestamp": datetime.now().isoformat()
    }