"""
Recording Voice API - Handles voice 'begin' signal detection for recording
Based on VIDEO_RECORDING.md spec lines 49-53
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import asyncio
import logging
from datetime import datetime
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/v1/recording", tags=["recording"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI client for LLM processing
openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class VoiceBeginRequest(BaseModel):
    """Request model for voice begin detection"""
    transcript: str
    confidence: float
    session_id: str
    timestamp: Optional[str] = None

class VoiceBeginResponse(BaseModel):
    """Response model for voice begin detection"""
    ready_to_begin: bool
    confidence: float
    reason: str
    session_id: str
    timestamp: str

class WebSocketManager:
    """Manages WebSocket connections for streaming voice processing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_contexts: Dict[str, list] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_contexts[session_id] = []
        logger.info(f"Voice session {session_id} connected")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
        logger.info(f"Voice session {session_id} disconnected")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
    
    def add_to_context(self, session_id: str, transcript: str):
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = []
        
        self.session_contexts[session_id].append({
            "transcript": transcript,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 transcripts for context
        if len(self.session_contexts[session_id]) > 10:
            self.session_contexts[session_id] = self.session_contexts[session_id][-10:]

# Global WebSocket manager
manager = WebSocketManager()

async def analyze_voice_for_begin_signal(transcript: str, context: list, confidence: float) -> tuple[bool, float, str]:
    """
    Analyze voice transcript to determine if user is ready to begin recording
    Uses LLM to determine readiness with confidence scoring
    """
    
    # Build context from previous transcripts
    context_text = ""
    if context:
        recent_context = context[-5:]  # Last 5 transcripts
        context_text = "Recent conversation context:\n"
        for item in recent_context:
            context_text += f"- {item['transcript']}\n"
        context_text += "\n"
    
    # Create prompt for LLM
    prompt = f"""You are analyzing voice input from a golf swing recording app. The user is in front of a camera ready to record their golf swings.

{context_text}Current transcript: "{transcript}"
Speech recognition confidence: {confidence}

Your task is to determine if the user has clearly indicated they are ready to begin recording their golf swing.

Look for indicators like:
- Direct statements: "begin", "start", "start recording", "I'm ready", "let's go", "record now"
- Confirmations: "yes", "okay", "sure", "let's do this", "go ahead"  
- Ready signals: "ready to begin", "ready to start", "let's begin recording"
- Action words: "record", "capture", "film", "shoot"

Consider context and natural speech patterns. Be conservative - only return true if the user has clearly indicated readiness.

Respond with a JSON object containing:
- ready_to_begin: boolean (true if clearly ready to begin recording)
- confidence: float (0.0 to 1.0, how confident you are in this assessment)
- reason: string (brief explanation of your decision)

Example responses:
{{"ready_to_begin": true, "confidence": 0.9, "reason": "User said 'I'm ready to begin recording' which is a clear indication"}}
{{"ready_to_begin": false, "confidence": 0.7, "reason": "User said 'maybe later' which indicates they are not ready now"}}
{{"ready_to_begin": false, "confidence": 0.3, "reason": "Unclear speech or unrelated conversation"}}
"""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a voice command analyzer for a golf recording app. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            result = json.loads(result_text)
            ready = result.get("ready_to_begin", False)
            llm_confidence = result.get("confidence", 0.0)
            reason = result.get("reason", "No reason provided")
            
            # Combine speech recognition confidence with LLM confidence
            # If speech recognition confidence is low, reduce overall confidence
            combined_confidence = llm_confidence * min(1.0, confidence / 0.8)
            
            logger.info(f"Voice analysis result: ready={ready}, confidence={combined_confidence}, reason={reason}")
            
            return ready, combined_confidence, reason
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {result_text}, error: {e}")
            return False, 0.0, "Failed to parse AI response"
    
    except Exception as e:
        logger.error(f"Error in voice analysis: {e}")
        return False, 0.0, f"Analysis error: {str(e)}"

@router.post("/voice/begin", response_model=VoiceBeginResponse)
async def analyze_voice_begin(request: VoiceBeginRequest):
    """
    Analyze voice input to determine if user is ready to begin recording
    REST endpoint for simple voice analysis
    """
    
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="Empty transcript provided")
    
    # Get context if session exists
    context = manager.session_contexts.get(request.session_id, [])
    
    # Add current transcript to context
    manager.add_to_context(request.session_id, request.transcript)
    
    # Analyze voice input
    ready, confidence, reason = await analyze_voice_for_begin_signal(
        request.transcript, 
        context, 
        request.confidence
    )
    
    return VoiceBeginResponse(
        ready_to_begin=ready,
        confidence=confidence,
        reason=reason,
        session_id=request.session_id,
        timestamp=datetime.now().isoformat()
    )

@router.websocket("/voice/stream/{session_id}")
async def voice_stream_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming voice processing
    Handles real-time speech-to-text and begin signal detection
    """
    
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive voice data from client
            data = await websocket.receive_json()
            
            transcript = data.get("transcript", "")
            confidence = data.get("confidence", 0.0)
            is_final = data.get("is_final", False)
            
            if not transcript.strip():
                continue
            
            # Add to context
            if is_final:
                manager.add_to_context(session_id, transcript)
            
            # Get context for analysis
            context = manager.session_contexts.get(session_id, [])
            
            # Analyze voice input
            ready, analysis_confidence, reason = await analyze_voice_for_begin_signal(
                transcript, 
                context, 
                confidence
            )
            
            # Send response back to client
            response = {
                "ready_to_begin": ready,
                "confidence": analysis_confidence,
                "reason": reason,
                "transcript": transcript,
                "is_final": is_final,
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_message(session_id, response)
            
            # If high confidence "ready" signal, log it
            if ready and analysis_confidence > 0.7:
                logger.info(f"High confidence ready signal detected for session {session_id}: {transcript}")
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)

@router.get("/voice/sessions/{session_id}/context")
async def get_session_context(session_id: str):
    """
    Get the conversation context for a voice session
    Useful for debugging and understanding session state
    """
    
    context = manager.session_contexts.get(session_id, [])
    
    return {
        "session_id": session_id,
        "context": context,
        "context_length": len(context),
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/voice/sessions/{session_id}")
async def clear_session_context(session_id: str):
    """
    Clear the conversation context for a voice session
    """
    
    if session_id in manager.session_contexts:
        del manager.session_contexts[session_id]
    
    if session_id in manager.active_connections:
        await manager.active_connections[session_id].close()
        del manager.active_connections[session_id]
    
    return {
        "message": f"Session {session_id} context cleared",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/voice/health")
async def voice_service_health():
    """
    Health check for voice processing service
    """
    
    active_sessions = len(manager.active_connections)
    total_contexts = len(manager.session_contexts)
    
    return {
        "status": "healthy",
        "service": "voice_processing",
        "active_sessions": active_sessions,
        "total_contexts": total_contexts,
        "timestamp": datetime.now().isoformat()
    }