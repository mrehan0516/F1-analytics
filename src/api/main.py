"""
F1 Race Strategist Live Agent - FastAPI Application
Provides REST API and WebSocket endpoints for the F1 strategist agent.
"""

import asyncio
import base64
import json
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config.settings import settings
from src.agents.f1_strategist import F1RaceStrategistAgent, LiveSession

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🏎️ F1 Race Strategist Live Agent starting up...")
    logger.info(f"Environment: {settings.app_env}")
    yield
    logger.info("🏁 F1 Race Strategist Live Agent shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="F1 Race Strategist Live Agent",
    description="Real-time multimodal AI agent for Formula 1 race strategy analysis powered by Google Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - configurable for security
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat message request."""
    message: str
    history: Optional[list] = None


class ChatResponse(BaseModel):
    """Chat message response."""
    response: str
    agent: str = "Pit Wall AI"


class AnalysisResponse(BaseModel):
    """Image analysis response."""
    analysis: str
    agent: str = "Pit Wall AI"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent: str
    version: str
    environment: str


# Global agent instance
agent = None


def get_agent() -> F1RaceStrategistAgent:
    """Get or create agent instance."""
    global agent
    if agent is None:
        agent = F1RaceStrategistAgent()
    return agent


# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Google Cloud deployment verification."""
    return HealthResponse(
        status="healthy",
        agent="F1 Race Strategist - Pit Wall AI",
        version="1.0.0",
        environment=settings.app_env
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "F1 Race Strategist Live Agent",
        "description": "Real-time multimodal AI agent for Formula 1 race strategy analysis",
        "powered_by": "Google Gemini Live API",
        "endpoints": {
            "chat": "POST /api/chat - Send a text message",
            "analyze": "POST /api/analyze - Analyze an F1 race image",
            "live": "WS /api/live - Real-time audio/video session",
            "health": "GET /health - Health check"
        }
    }


# Chat Endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message to the F1 strategist.
    
    Example queries:
    - "What tire strategy would you recommend for a 50-lap race at Silverstone?"
    - "Should we undercut or overcut the car ahead?"
    - "What's the typical pit window for medium tires?"
    """
    try:
        strategist = get_agent()
        response = await strategist.chat(request.message, request.history)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Image Analysis Endpoint
@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = "Analyze this F1 race image and provide strategic insights."
):
    """
    Analyze an F1 race image (timing screen, telemetry, race footage).
    
    Upload an image of:
    - Timing screens (gaps, sector times)
    - Telemetry data (speed traces, tire temps)
    - Race footage (track position, weather)
    - Tire condition close-ups
    """
    try:
        # Read image data
        image_data = await file.read()
        
        strategist = get_agent()
        analysis = await strategist.analyze_image(image_data, prompt)
        
        return AnalysisResponse(analysis=analysis)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for Live Session
@app.websocket("/api/live")
async def live_session(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio/video interaction.
    
    Protocol:
    1. Connect to websocket
    2. Send JSON messages with type: 'text', 'audio', or 'image'
    3. Receive JSON responses with type: 'text' or 'audio'
    4. Close connection when done
    """
    await websocket.accept()
    logger.info("Live session connected")
    
    strategist = get_agent()
    session = None
    
    try:
        # Create live session
        session = await strategist.create_live_session()
        
        # Start receiving task
        async def receive_and_send():
            async for response in session.receive():
                if response["type"] == "text":
                    await websocket.send_json({
                        "type": "text",
                        "data": response["data"]
                    })
                elif response["type"] == "audio":
                    await websocket.send_json({
                        "type": "audio",
                        "data": base64.b64encode(response["data"]).decode()
                    })
        
        receive_task = asyncio.create_task(receive_and_send())
        
        # Handle incoming messages
        while True:
            try:
                message = await websocket.receive_json()
                msg_type = message.get("type", "text")
                data = message.get("data", "")
                
                if msg_type == "text":
                    await session.send_text(data)
                elif msg_type == "audio":
                    audio_data = base64.b64decode(data)
                    await session.send_audio(audio_data)
                elif msg_type == "image":
                    image_data = base64.b64decode(data)
                    await session.send_image(image_data)
                    
            except WebSocketDisconnect:
                break
                
        receive_task.cancel()
        
    except Exception as e:
        logger.error(f"Live session error: {e}")
        await websocket.send_json({"type": "error", "data": str(e)})
    finally:
        if session:
            await session.close()
        logger.info("Live session closed")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
