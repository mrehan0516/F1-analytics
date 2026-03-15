"""
F1 Pit Wall AI - FastAPI Backend
WebSocket-enabled API for real-time voice interaction
"""
import asyncio
import logging
import base64
import json
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import settings
from src.agents.f1_strategist import F1StrategistAgent, create_f1_agent, AgentState
from src.services.f1_data_service import f1_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Active agent sessions
agent_sessions: Dict[str, F1StrategistAgent] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("F1 Pit Wall AI starting up...")
    yield
    # Cleanup: disconnect all agent sessions
    for session_id, agent in agent_sessions.items():
        await agent.disconnect()
    logger.info("F1 Pit Wall AI shutting down...")


# Create FastAPI app
app = FastAPI(
    title="F1 Pit Wall AI",
    description="Real-time voice-enabled F1 race strategist powered by Gemini Live API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class TextMessage(BaseModel):
    """Text message request."""
    message: str
    session_id: Optional[str] = "default"


class StrategyRequest(BaseModel):
    """Race strategy analysis request."""
    current_lap: int
    total_laps: int
    position: int = 3
    tyre_compound: str = "MEDIUM"
    tyre_life: int = 20
    gap_to_leader: str = "+8.5"
    gap_ahead: str = "+2.1"
    gap_behind: str = "-1.8"
    weather: str = "Dry, 28°C track"


class SessionResponse(BaseModel):
    """Session information response."""
    session_id: str
    status: str
    state: str


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment verification."""
    return {
        "status": "healthy",
        "service": "F1 Pit Wall AI",
        "version": "1.0.0",
        "google_cloud": True
    }


# API info endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "F1 Pit Wall AI",
        "description": "Real-time voice-enabled F1 race strategist",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "schedule": "/api/schedule",
            "strategy": "/api/strategy",
            "websocket": "/ws/{session_id}",
            "docs": "/docs"
        },
        "powered_by": "Google Gemini Live API"
    }


# F1 Data endpoints
@app.get("/api/schedule")
async def get_schedule(year: Optional[int] = None):
    """Get F1 race schedule."""
    try:
        schedule = f1_service.get_race_schedule(year)
        return {"year": year or f1_service.get_current_season(), "races": schedule}
    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{year}/{race}")
async def get_session_data(year: int, race: str, session_type: str = "R"):
    """Get session data for a specific race."""
    try:
        data = f1_service.get_session_data(year, race, session_type)
        return data
    except Exception as e:
        logger.error(f"Error fetching session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/telemetry/{year}/{race}/{driver}")
async def get_telemetry(year: int, race: str, driver: str, lap: Optional[int] = None):
    """Get driver telemetry data."""
    try:
        telemetry = f1_service.get_driver_telemetry(year, race, driver, lap)
        return telemetry
    except Exception as e:
        logger.error(f"Error fetching telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Strategy endpoint
@app.post("/api/strategy")
async def analyze_strategy(request: StrategyRequest):
    """Analyze race situation and get strategy recommendation."""
    try:
        race_data = {
            "tyre_life": request.tyre_life,
            "compound": request.tyre_compound,
            "weather": {"rainfall": "rain" in request.weather.lower()},
            "position": request.position,
            "gap_to_leader": request.gap_to_leader,
            "gap_ahead": request.gap_ahead,
            "gap_behind": request.gap_behind,
        }
        
        strategy = f1_service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=request.current_lap,
            total_laps=request.total_laps
        )
        
        return {
            "analysis": strategy,
            "summary": f"Lap {request.current_lap}/{request.total_laps}: {strategy['recommended_action']}",
            "confidence": strategy["confidence"]
        }
    except Exception as e:
        logger.error(f"Error analyzing strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Text chat endpoint
@app.post("/api/chat")
async def chat(request: TextMessage):
    """Send a text message to the AI agent."""
    try:
        session_id = request.session_id
        
        # Get or create agent session
        if session_id not in agent_sessions:
            agent = create_f1_agent(enable_voice=False)
            if await agent.connect():
                agent_sessions[session_id] = agent
            else:
                raise HTTPException(status_code=500, detail="Failed to connect to AI")
        
        agent = agent_sessions[session_id]
        
        # Collect response
        response_text = ""
        async for chunk in agent.send_text(request.message):
            if chunk["type"] == "text":
                response_text += chunk["content"]
        
        return {
            "session_id": session_id,
            "response": response_text,
            "state": agent.state.value
        }
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time voice interaction
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice interaction.
    
    Protocol:
    - Client sends: {"type": "text|audio|image", "data": "...", "mime_type": "..."}
    - Server sends: {"type": "text|audio|state", "data": "...", "mime_type": "..."}
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")
    
    # Create agent for this session
    agent = create_f1_agent(enable_voice=True)
    
    # Set up callbacks
    async def on_state_change(state: AgentState):
        try:
            await websocket.send_json({"type": "state", "data": state.value})
        except Exception:
            pass
    
    agent.on_state_change = lambda s: asyncio.create_task(on_state_change(s))
    
    try:
        # Connect to Gemini
        if not await agent.connect():
            await websocket.send_json({"type": "error", "data": "Failed to connect to AI"})
            await websocket.close()
            return
        
        agent_sessions[session_id] = agent
        await websocket.send_json({"type": "state", "data": "connected"})
        
        # Send welcome message
        welcome = "Pit Wall AI online. Ready to assist with race strategy. How can I help?"
        async for chunk in agent.send_text(welcome):
            if chunk["type"] == "text":
                await websocket.send_json({"type": "text", "data": chunk["content"]})
            elif chunk["type"] == "audio":
                await websocket.send_json({
                    "type": "audio",
                    "data": base64.b64encode(chunk["content"]).decode(),
                    "mime_type": chunk["mime_type"]
                })
        
        # Main message loop
        while True:
            try:
                message = await websocket.receive_json()
                msg_type = message.get("type", "text")
                data = message.get("data", "")
                mime_type = message.get("mime_type", "")
                
                if msg_type == "text":
                    # Text message
                    async for chunk in agent.send_text(data):
                        if chunk["type"] == "text":
                            await websocket.send_json({"type": "text", "data": chunk["content"]})
                        elif chunk["type"] == "audio":
                            await websocket.send_json({
                                "type": "audio",
                                "data": base64.b64encode(chunk["content"]).decode(),
                                "mime_type": chunk["mime_type"]
                            })
                
                elif msg_type == "audio":
                    # Audio input
                    audio_bytes = base64.b64decode(data)
                    async for chunk in agent.send_audio(audio_bytes, mime_type):
                        if chunk["type"] == "text":
                            await websocket.send_json({"type": "text", "data": chunk["content"]})
                        elif chunk["type"] == "audio":
                            await websocket.send_json({
                                "type": "audio",
                                "data": base64.b64encode(chunk["content"]).decode(),
                                "mime_type": chunk["mime_type"]
                            })
                
                elif msg_type == "image":
                    # Image analysis
                    image_bytes = base64.b64decode(data)
                    prompt = message.get("prompt", "Analyze this F1 telemetry or track position")
                    async for chunk in agent.send_image(image_bytes, mime_type, prompt):
                        if chunk["type"] == "text":
                            await websocket.send_json({"type": "text", "data": chunk["content"]})
                        elif chunk["type"] == "audio":
                            await websocket.send_json({
                                "type": "audio",
                                "data": base64.b64encode(chunk["content"]).decode(),
                                "mime_type": chunk["mime_type"]
                            })
                
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({"type": "error", "data": str(e)})
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        if session_id in agent_sessions:
            await agent_sessions[session_id].disconnect()
            del agent_sessions[session_id]


# Session management
@app.get("/api/sessions")
async def list_sessions():
    """List active agent sessions."""
    return {
        "sessions": [
            {"session_id": sid, "state": agent.state.value}
            for sid, agent in agent_sessions.items()
        ]
    }


@app.delete("/api/sessions/{session_id}")
async def close_session(session_id: str):
    """Close an agent session."""
    if session_id in agent_sessions:
        await agent_sessions[session_id].disconnect()
        del agent_sessions[session_id]
        return {"status": "closed", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


# Serve demo page
@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Serve the demo HTML page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1 Pit Wall AI - Demo</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', system-ui, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #e10600;
            margin-bottom: 30px;
        }
        h1 { 
            font-size: 2.5rem; 
            color: #e10600;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .subtitle { color: #aaa; margin-top: 10px; }
        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            background: #333;
            margin: 15px 0;
        }
        .status.connected { background: #0a5; }
        .status.error { background: #e10600; }
        .chat-container {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            min-height: 400px;
            max-height: 500px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        .message {
            padding: 12px 18px;
            margin: 10px 0;
            border-radius: 15px;
            max-width: 80%;
        }
        .message.user {
            background: #e10600;
            margin-left: auto;
            text-align: right;
        }
        .message.ai {
            background: rgba(255,255,255,0.1);
            border: 1px solid #e10600;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e10600;
            border-radius: 30px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1rem;
        }
        input[type="text"]:focus { 
            outline: none;
            background: rgba(255,255,255,0.15);
        }
        button {
            padding: 15px 30px;
            background: #e10600;
            border: none;
            border-radius: 30px;
            color: #fff;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover { background: #ff1a1a; transform: scale(1.05); }
        button:disabled { background: #666; cursor: not-allowed; }
        .mic-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .mic-btn.recording { background: #0a5; animation: pulse 1s infinite; }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(10,170,85,0.7); }
            70% { box-shadow: 0 0 0 20px rgba(10,170,85,0); }
            100% { box-shadow: 0 0 0 0 rgba(10,170,85,0); }
        }
        .quick-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }
        .quick-btn {
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border: 1px solid #e10600;
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏎️ F1 Pit Wall AI</h1>
            <p class="subtitle">Real-time Race Strategy Assistant</p>
            <div id="status" class="status">Connecting...</div>
        </header>
        
        <div id="chat" class="chat-container">
            <div class="message ai">Welcome to Pit Wall AI. Ready to assist with race strategy!</div>
        </div>
        
        <div class="input-area">
            <input type="text" id="message" placeholder="Ask about race strategy..." />
            <button id="send">Send</button>
            <button id="mic" class="mic-btn">🎤</button>
        </div>
        
        <div class="quick-actions">
            <button class="quick-btn" onclick="quickSend('Should we pit now?')">Pit Now?</button>
            <button class="quick-btn" onclick="quickSend('What\\'s the weather forecast?')">Weather</button>
            <button class="quick-btn" onclick="quickSend('Analyze our tyre strategy')">Tyres</button>
            <button class="quick-btn" onclick="quickSend('Who is the fastest right now?')">Fastest</button>
            <button class="quick-btn" onclick="quickSend('Gap to the leader?')">Gap</button>
        </div>
        
        <footer>
            Powered by Google Gemini Live API | Built for Gemini Live Agent Challenge
        </footer>
    </div>
    
    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('message');
        const sendBtn = document.getElementById('send');
        const micBtn = document.getElementById('mic');
        const status = document.getElementById('status');
        
        let ws;
        let isRecording = false;
        let mediaRecorder;
        
        function connect() {
            const sessionId = 'demo-' + Math.random().toString(36).substr(2, 9);
            ws = new WebSocket(`ws://${location.host}/ws/${sessionId}`);
            
            ws.onopen = () => {
                status.textContent = 'Connected';
                status.className = 'status connected';
            };
            
            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'text') {
                    addMessage(msg.data, 'ai');
                } else if (msg.type === 'audio') {
                    playAudio(msg.data, msg.mime_type);
                } else if (msg.type === 'state') {
                    status.textContent = msg.data;
                }
            };
            
            ws.onclose = () => {
                status.textContent = 'Disconnected';
                status.className = 'status';
                setTimeout(connect, 3000);
            };
            
            ws.onerror = () => {
                status.textContent = 'Error';
                status.className = 'status error';
            };
        }
        
        function addMessage(text, type) {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.textContent = text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function send() {
            const text = input.value.trim();
            if (text && ws.readyState === WebSocket.OPEN) {
                addMessage(text, 'user');
                ws.send(JSON.stringify({type: 'text', data: text}));
                input.value = '';
            }
        }
        
        function quickSend(text) {
            input.value = text;
            send();
        }
        
        function playAudio(base64Data, mimeType) {
            const audio = new Audio(`data:${mimeType};base64,${base64Data}`);
            audio.play();
        }
        
        sendBtn.onclick = send;
        input.onkeypress = (e) => { if (e.key === 'Enter') send(); };
        
        micBtn.onclick = async () => {
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
                    mediaRecorder = new MediaRecorder(stream);
                    const chunks = [];
                    
                    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
                    mediaRecorder.onstop = async () => {
                        const blob = new Blob(chunks, {type: 'audio/webm'});
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64 = reader.result.split(',')[1];
                            ws.send(JSON.stringify({
                                type: 'audio',
                                data: base64,
                                mime_type: 'audio/webm'
                            }));
                        };
                        reader.readAsDataURL(blob);
                        stream.getTracks().forEach(t => t.stop());
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    micBtn.classList.add('recording');
                    micBtn.textContent = '⏹️';
                } catch (err) {
                    alert('Microphone access denied');
                }
            } else {
                mediaRecorder.stop();
                isRecording = false;
                micBtn.classList.remove('recording');
                micBtn.textContent = '🎤';
            }
        };
        
        connect();
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
