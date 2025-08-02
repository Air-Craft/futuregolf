"""
AI Swing Detection WebSocket API - Using LangChain with DI
Based on AI_SWING_DETECTION.md specification
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

from core.container import container, configure_container
from core.interfaces import VisionModel, PromptLoader, ConfigProvider
import config.swing_detection as swing_config
from config.api import API_VERSION_PREFIX

router = APIRouter(prefix=f"{API_VERSION_PREFIX}/ws", tags=["swing_detection"])

# Configure logging
logger = logging.getLogger(__name__)


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
        self.is_analyzing: bool = False
        self.analysis_start_time: Optional[float] = None
        self.analysis_task: Optional[asyncio.Task] = None
        self.analysis_result: Optional[Dict[str, Any]] = None
        
        # Get dependencies from container
        self.vision_model = container.get(VisionModel)
        self.prompt_loader = container.get(PromptLoader)
        self.config = container.get(ConfigProvider)
        
        # Load swing detection prompt
        self.swing_prompt = self.prompt_loader.load_prompt("swing_detection")
    
    def add_image(self, timestamp: float, image_base64: str):
        """Add image to buffer and maintain sort order"""
        self.image_buffer.append({
            "timestamp": timestamp,
            "image": image_base64
        })
        # logger.debug(f"🖼️ Image timestamp: {timestamp}")

        # Sort by timestamp
        self.image_buffer.sort(key=lambda x: x["timestamp"])
        
        # NO TRIMMING - we keep all frames until swing is detected
        # Buffer only clears after successful swing detection
        
        # Update timestamps
        if self.image_buffer:
            self.first_timestamp = self.image_buffer[0]["timestamp"]
            self.last_timestamp = self.image_buffer[-1]["timestamp"]
    
        # logger.debug(f"🖼️ Image added:: first: {self.first_timestamp}, last: {self.last_timestamp}")

    def apply_rolling_window(self, current_timestamp: float):
        """DEPRECATED - We no longer use rolling windows
        Buffer is kept intact until swing detection, then cleared completely
        """
        pass  # Method kept for backwards compatibility but does nothing
    
    def should_submit_to_llm(self) -> bool:
        """Check if we should submit to LLM based on time threshold"""
        if not self.last_timestamp:
            # This is normal when buffer is empty or has single frame
            return False
        
        time_span = self.last_timestamp - self.first_timestamp
        threshold = self.config.get("LLM_SUBMISSION_THRESHOLD", 1.0)
        
        # Only log when we're close to threshold to reduce noise
        if time_span >= threshold * 0.8:
            logger.debug(f"⏳ Time span: {time_span:.2f}s (threshold: {threshold:.2f}s)")
        
        return time_span >= threshold
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get current context window and size information"""
        context_window = 0.0
        if self.last_timestamp:
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
        """Analyze image sequence for golf swing using vision model"""
        
        # Take a snapshot of current buffer for analysis
        # This allows us to continue collecting frames while analyzing
        snapshot_buffer = self.image_buffer.copy()
        
        if not snapshot_buffer:
            return {
                "swing_detected": False,
                "reason": "No images in buffer"
            }
        
        try:
            # Prepare PIL images from snapshot
            pil_images = []
            
            for img_data in snapshot_buffer:
                # Images are already resized and compressed by client
                # Just decode for analysis
                image_bytes = base64.b64decode(img_data["image"])
                image = Image.open(BytesIO(image_bytes))
                pil_images.append(image)
            
            # Time the LLM call
            start_time = datetime.now()
            
            # Use vision model to analyze
            result = await self.vision_model.analyze_images(pil_images, self.swing_prompt)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"🗣️ LLM Reponse {result} in time {response_time:.2f}s")
            
            # Store confidence for later use
            self.last_confidence = result.get("confidence", 0.0)
            
            logger.info(f"Swing analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing swing: {e}")
            return {
                "swing_detected": False,
                "confidence": 0.0,
                "error": str(e)
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


# Image processing now done by client - keeping for reference
# def resize_and_compress_image(image_base64: str, config: ConfigProvider) -> str:
#     """Resize and compress image for faster processing using box fit"""
#     try:
#         # Decode base64 image
#         image_bytes = base64.b64decode(image_base64)
#         image = Image.open(BytesIO(image_bytes))
#         
#         # Convert to grayscale if configured
#         if config.get("IMAGE_CONVERT_BW", True):
#             image = image.convert('L')
#         elif image.mode != 'RGB':
#             image = image.convert('RGB')
#         
#         # Get target box size
#         max_size = (
#             config.get("IMAGE_MAX_SIZE", (128, 128))[0],
#             config.get("IMAGE_MAX_SIZE", (128, 128))[1]
#         )
#         
#         # Calculate new size maintaining aspect ratio (box fit)
#         original_width, original_height = image.size
#         box_width, box_height = max_size
#         
#         # Calculate scale factor to fit within box
#         scale = min(box_width / original_width, box_height / original_height)
#         
#         # Only resize if the image is larger than the box
#         if scale < 1:
#             new_width = int(original_width * scale)
#             new_height = int(original_height * scale)
#             image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
#         
#         # Compress and encode to WebP
#         buffer = BytesIO()
#         quality = config.get("IMAGE_WEBP_QUALITY", 40)
#         image.save(buffer, format='WEBP', quality=quality, method=6)
#         compressed_bytes = buffer.getvalue()
#         compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
#         
#         return compressed_b64
#         
#     except Exception as e:
#         logger.error(f"Error compressing image: {e}")
#         return image_base64  # Return original if compression fails


@router.websocket("/detect-golf-swing")
async def detect_golf_swing_websocket(websocket: WebSocket):
    # logger.setLevel(logging.DEBUG)
    """
    WebSocket endpoint for golf swing detection
    Accepts stream of images with timestamps and detects complete swings
    """
    logger.debug(f"🪢 websocket::Detect Golf Swing")
    
    # Configure container on first use (lazy initialization)
    if not container.has(ConfigProvider):
        configure_container(swing_config)
    
    # Accept connection and create session
    await websocket.accept()
    session_id = await session_manager.create_session(websocket)
    session = session_manager.get_session(session_id)
    
    # Get config for logging
    config = container.get(ConfigProvider)
    submission_threshold = config.get("LLM_SUBMISSION_THRESHOLD", 2.0)
    cooldown = config.get("POST_DETECTION_COOLDOWN", 2.0)
    confidence_threshold = config.get("CONFIDENCE_THRESHOLD", 0.7)
    
    logger.info(f"🚀 New swing detection session started: {session_id}")
    logger.info(f"⚙️ Settings: threshold={submission_threshold}s, cooldown={cooldown}s, confidence>={confidence_threshold}")
    logger.info(f"🤖 Using model: {session.vision_model.get_model_info()}")
    
    try:
        while True:
        
            # Receive message from client
            data = await websocket.receive_json()

            # Extract timestamp and image
            timestamp = data.get("timestamp")
            image_base64 = data.get("image_base64")

            if timestamp is None or not image_base64:
                logger.debug(f"Missing timestamp or image_base64: {data}")
                await websocket.send_json({
                    "error": "Missing timestamp or image_base64"
                })
                continue
            
            # Image processing now done by client
            # compressed_image = resize_and_compress_image(image_base64, config)
            
            # Add image to buffer (using client-processed image)
            session.add_image(float(timestamp), image_base64)
            logger.debug(f"Added frame at {timestamp}s, buffer size: {len(session.image_buffer)}, first: {session.first_timestamp}, last: {session.last_timestamp}")
            
            # Check if we're in cooldown period
            current_time = float(timestamp)
            if session.cooldown_until and current_time < session.cooldown_until:
                # Still in cooldown, send waiting response
                cooldown_remaining = session.cooldown_until - current_time
                logger.debug(f"❄️ Frame at {current_time:.2f}s ignored - in cooldown for {cooldown_remaining:.1f}s more")
                response = {
                    "status": "cooldown",
                    "cooldown_remaining": cooldown_remaining,
                    "total_swings": session.swings_detected
                }
                await websocket.send_json(response)
                continue
            
            # Don't apply rolling window - user specified we should only clear on swing detection
            # This prevents losing frames during analysis
            # session.apply_rolling_window(current_time)
            
            # Get context info
            context_info = session.get_context_info()
            
            # Check if currently analyzing
            if session.is_analyzing:
                # logger.debug("🤔 Currently analyzing")
                # Send analyzing status while LLM is processing
                elapsed = datetime.now().timestamp() - session.analysis_start_time if session.analysis_start_time else 0
                logger.debug(f"⏳ Currently analyzing, elapsed: {elapsed:.2f}s")
                response = {
                    "status": "analyzing",
                    "message": "Processing swing detection...",
                    "elapsed_time": elapsed,
                    "context_window": context_info["context_window"],
                    "buffer_size": len(session.image_buffer)
                }
                await websocket.send_json(response)
                continue
            
            # Check if there's a completed analysis to process
            if session.analysis_task and session.analysis_task.done():
                logger.debug("✅ analysis done")
                # Get the result
                result = session.analysis_result
                session.analysis_task = None
                session.analysis_result = None
                
                confidence = result.get("confidence", 0.0)
                swing_detected = result.get("swing_detected", False)
                
                # Check if confidence meets threshold
                if swing_detected:
                    session.swings_detected += 1
                    # Use the timestamp from when analysis was triggered
                    detection_timestamp = session.last_timestamp if session.last_timestamp else timestamp
                    logger.info(f"🏌️ SWING {session.swings_detected} DETECTED at {detection_timestamp:.2f}s (confidence: {confidence:.2f})")
                    
                    # Send detection response
                    response = {
                        "status": "evaluated",
                        "swing_detected": True,
                        "confidence": confidence,
                        "timestamp": detection_timestamp,
                        "context_window": context_info["context_window"],
                        "context_size": context_info["context_size"],
                        "total_swings": session.swings_detected
                    }
                    await websocket.send_json(response)
                    
                    # Clear context for next swing
                    session.clear_context()
                    session.cooldown_until = detection_timestamp + cooldown
                    session.is_analyzing = False
                    session.analysis_start_time = None
                
            
            # Check if we should submit to LLM (and not already analyzing)
            elif session.should_submit_to_llm() and not session.is_analyzing:
                logger.info(f"🔍 Submitting to LLM - context window: {context_info['context_window']:.2f}s, buffer size: {len(session.image_buffer)} frames")
                
                # Mark as analyzing BEFORE creating the task
                session.is_analyzing = True
                session.analysis_start_time = datetime.now().timestamp()
                
                # Create background task for analysis
                async def analyze_and_store():
                    result = await session.analyze_for_swing()
                    # print("💎 HEY IM done")
                    session.analysis_result = result
                    session.is_analyzing = False 
                
                # Start analysis in background
                logger.debug("🧌 Starting analysis in background...")
                session.analysis_task = asyncio.create_task(analyze_and_store())
                
                # Check if we're analyzing
                # Send analyzing status
                response = {
                    "status": "analyzing",
                    "message": "Processing swing detection...",
                    "elapsed_time": 0,
                    "context_window": context_info["context_window"],
                    "buffer_size": len(session.image_buffer)
                }
                await websocket.send_json(response)
            else:

                logger.debug("should_submit_to_llm said no")
                # Not enough data yet or still analyzing
                if session.is_analyzing:
                    # Still analyzing, send status
                    elapsed = datetime.now().timestamp() - session.analysis_start_time if session.analysis_start_time else 0
                    response = {
                        "status": "analyzing", 
                        "message": "Processing swing detection...",
                        "elapsed_time": elapsed,
                        "context_window": context_info["context_window"],
                        "buffer_size": len(session.image_buffer)
                    }
                else:
                    # Not enough data yet
                    time_needed = submission_threshold - context_info["context_window"]
                    if len(session.image_buffer) % 5 == 1:  # Log every 5th frame to reduce noise
                        logger.debug(f"⏳ Need {time_needed:.2f}s more data before analysis (current window: {context_info['context_window']:.2f}s)")
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