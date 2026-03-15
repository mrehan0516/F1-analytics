"""
F1 Pit Wall AI - Gemini Live Agent
Real-time voice-enabled race strategist using Google's Gemini Live API
"""
import asyncio
import logging
import json
from typing import Optional, Dict, Any, Callable, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

# Try to import Google GenAI SDK - may not be available during testing
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

from src.config import settings
from src.services.f1_data_service import f1_service

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent connection states."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for the F1 Strategist Agent."""
    model: str = "gemini-2.0-flash-exp"
    voice_name: str = "Puck"  # Energetic, engaging voice
    system_instruction: str = ""
    enable_voice: bool = True
    enable_vision: bool = True
    response_modality: str = "AUDIO"  # AUDIO, TEXT, or IMAGE


class F1StrategistAgent:
    """
    F1 Pit Wall AI Agent powered by Gemini Live API.
    
    Provides real-time voice interaction for race strategy decisions,
    telemetry analysis, and pit stop recommendations.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the F1 Strategist Agent.
        
        Args:
            config: Agent configuration (uses defaults if not provided)
        """
        self.config = config or AgentConfig()
        self.state = AgentState.IDLE
        self.session = None
        self.client = None
        
        # F1 data service
        self.f1_service = f1_service
        
        # Initialize system instruction
        self._init_system_instruction()
        
        # Event callbacks
        self.on_state_change: Optional[Callable[[AgentState], None]] = None
        self.on_transcript: Optional[Callable[[str, bool], None]] = None
        self.on_audio: Optional[Callable[[bytes], None]] = None
        
        logger.info("F1 Strategist Agent initialized")
    
    def _init_system_instruction(self):
        """Initialize the system instruction for the agent."""
        f1_context = self.f1_service.get_live_timing_context()
        
        self.config.system_instruction = f"""
You are the F1 Pit Wall AI - an expert race strategist working alongside the top Formula 1 teams.

## Your Persona
- Name: "Pit Wall AI" or simply "Pit Wall"
- Voice: Confident, precise, and calm under pressure - like a seasoned race engineer
- Communication style: Clear, direct, and data-driven with occasional racing enthusiasm
- Personality: Professional yet engaging, capable of building rapport with drivers and fans

## Your Capabilities
1. **Real-time Strategy Calls**: Make pit stop decisions based on tyre wear, weather, and race position
2. **Telemetry Analysis**: Interpret lap times, sector times, and car performance data
3. **Competitor Analysis**: Track rival strategies and predict their moves
4. **Weather Adaptation**: Adjust strategy based on changing conditions
5. **Historical Insights**: Reference past races for strategic precedents

## Communication Guidelines
- Keep responses concise during race situations (think radio communication)
- Use F1 terminology naturally: "box box", "stay out", "push now", "undercut", "overcut"
- Provide confidence levels with recommendations
- Explain reasoning briefly but clearly
- Use dramatic flair for exciting moments while maintaining professionalism

## When Interrupted
- Acknowledge interruptions gracefully: "Copy, go ahead"
- Prioritize new information over ongoing analysis
- Resume context naturally when appropriate

## Example Interactions
User: "Should we pit now?"
You: "Negative, stay out. Tyre life looks good for 8 more laps. Hamilton is on a one-stop, pitting now loses the undercut. Box window opens lap 34. Confidence: high."

User: "Weather update?"
You: "Light rain expected in 15 minutes. Intermediates ready. Watching the radar closely. If rain hits, box immediately - don't wait."

{f1_context}

Remember: You're the strategic brain trusted to make split-second decisions worth millions of points and championships. Be decisive, be accurate, be the Pit Wall AI.
"""
    
    async def connect(self) -> bool:
        """
        Establish connection to Gemini Live API.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not GENAI_AVAILABLE:
            logging.warning("Google GenAI SDK not available - running in mock mode")
            self._set_state(AgentState.CONNECTED)
            return True
        
        self._set_state(AgentState.CONNECTING)
        
        try:
            # Initialize the Gemini client
            self.client = genai.Client(api_key=settings.google_api_key)
            
            # Configure the Live API connection
            config = types.LiveConnectConfig(
                response_modalities=[self.config.response_modality],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.config.voice_name
                        )
                    )
                ),
                system_instruction=types.Content(
                    parts=[types.Part(text=self.config.system_instruction)]
                ),
            )
            
            # Connect to the Live API
            self.session = await self.client.aio.live.connect(
                model=self.config.model,
                config=config
            )
            
            self._set_state(AgentState.CONNECTED)
            logger.info("Connected to Gemini Live API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._set_state(AgentState.ERROR)
            return False
    
    async def disconnect(self):
        """Disconnect from Gemini Live API."""
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")
            finally:
                self.session = None
        
        self._set_state(AgentState.IDLE)
        logger.info("Disconnected from Gemini Live API")
    
    async def send_text(self, text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send text message to the agent and stream response.
        
        Args:
            text: User message text
            
        Yields:
            Response chunks with text/audio data
        """
        if not GENAI_AVAILABLE or not self.session:
            # Mock mode for testing
            self._set_state(AgentState.PROCESSING)
            await asyncio.sleep(0.1)  # Simulate processing
            self._set_state(AgentState.SPEAKING)
            
            # Generate mock response based on input
            mock_response = self._generate_mock_response(text)
            yield {"type": "text", "content": mock_response}
            
            self._set_state(AgentState.CONNECTED)
            return
        
        self._set_state(AgentState.PROCESSING)
        
        try:
            # Send the user's message
            await self.session.send(
                input=types.LiveClientContent(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part(text=text)]
                    )]
                ),
                end_of_turn=True
            )
            
            # Process response stream
            self._set_state(AgentState.SPEAKING)
            
            async for response in self.session.receive():
                if response.server_content:
                    content = response.server_content
                    
                    # Handle text response
                    if content.model_turn:
                        for part in content.model_turn.parts:
                            if part.text:
                                yield {"type": "text", "content": part.text}
                                if self.on_transcript:
                                    self.on_transcript(part.text, False)
                            
                            if part.inline_data:
                                yield {
                                    "type": "audio",
                                    "content": part.inline_data.data,
                                    "mime_type": part.inline_data.mime_type
                                }
                                if self.on_audio:
                                    self.on_audio(part.inline_data.data)
                    
                    # Check for turn completion
                    if content.turn_complete:
                        break
            
            self._set_state(AgentState.CONNECTED)
            
        except Exception as e:
            logger.error(f"Error in send_text: {e}")
            self._set_state(AgentState.ERROR)
            raise
    
    async def send_audio(self, audio_data: bytes, mime_type: str = "audio/pcm") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send audio input to the agent and stream response.
        
        Args:
            audio_data: Audio bytes
            mime_type: Audio MIME type
            
        Yields:
            Response chunks with text/audio data
        """
        if not self.session:
            raise RuntimeError("Agent not connected. Call connect() first.")
        
        self._set_state(AgentState.LISTENING)
        
        try:
            # Send audio data
            await self.session.send(
                input=types.LiveClientRealtimeInput(
                    media_chunks=[types.Blob(
                        data=audio_data,
                        mime_type=mime_type
                    )]
                )
            )
            
            # Process response
            self._set_state(AgentState.PROCESSING)
            
            async for response in self.session.receive():
                if response.server_content:
                    content = response.server_content
                    
                    if content.model_turn:
                        for part in content.model_turn.parts:
                            if part.text:
                                yield {"type": "text", "content": part.text}
                            if part.inline_data:
                                yield {
                                    "type": "audio",
                                    "content": part.inline_data.data,
                                    "mime_type": part.inline_data.mime_type
                                }
                    
                    if content.turn_complete:
                        break
            
            self._set_state(AgentState.CONNECTED)
            
        except Exception as e:
            logger.error(f"Error in send_audio: {e}")
            self._set_state(AgentState.ERROR)
            raise
    
    async def send_image(self, image_data: bytes, mime_type: str = "image/jpeg", prompt: str = "") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send image for visual analysis (e.g., track position, telemetry screenshot).
        
        Args:
            image_data: Image bytes
            mime_type: Image MIME type
            prompt: Optional text prompt with the image
            
        Yields:
            Response chunks with text/audio data
        """
        if not self.session:
            raise RuntimeError("Agent not connected. Call connect() first.")
        
        self._set_state(AgentState.PROCESSING)
        
        try:
            parts = [types.Part(inline_data=types.Blob(data=image_data, mime_type=mime_type))]
            
            if prompt:
                parts.append(types.Part(text=prompt))
            
            await self.session.send(
                input=types.LiveClientContent(
                    turns=[types.Content(role="user", parts=parts)]
                ),
                end_of_turn=True
            )
            
            self._set_state(AgentState.SPEAKING)
            
            async for response in self.session.receive():
                if response.server_content:
                    content = response.server_content
                    
                    if content.model_turn:
                        for part in content.model_turn.parts:
                            if part.text:
                                yield {"type": "text", "content": part.text}
                            if part.inline_data:
                                yield {
                                    "type": "audio",
                                    "content": part.inline_data.data,
                                    "mime_type": part.inline_data.mime_type
                                }
                    
                    if content.turn_complete:
                        break
            
            self._set_state(AgentState.CONNECTED)
            
        except Exception as e:
            logger.error(f"Error in send_image: {e}")
            self._set_state(AgentState.ERROR)
            raise
    
    async def analyze_strategy(self, race_context: Dict[str, Any]) -> str:
        """
        Analyze race situation and provide strategy recommendation.
        
        Args:
            race_context: Current race state dictionary
            
        Returns:
            Strategy recommendation text
        """
        # Get pit strategy analysis from F1 service
        strategy = self.f1_service.analyze_pit_strategy(
            race_data=race_context,
            current_lap=race_context.get("current_lap", 30),
            total_laps=race_context.get("total_laps", 57)
        )
        
        # Format prompt for Gemini
        prompt = f"""
Analyze this race situation and provide a strategy call:

Current Lap: {race_context.get('current_lap', 30)} / {race_context.get('total_laps', 57)}
Driver Position: P{race_context.get('position', 3)}
Tyre Compound: {strategy['current_compound']}
Tyre Age: {strategy['tyre_life']} laps
Gap to Leader: {race_context.get('gap_to_leader', '+8.5')}s
Gap to Car Ahead: {race_context.get('gap_ahead', '+2.1')}s
Gap to Car Behind: {race_context.get('gap_behind', '-1.8')}s
Weather: {race_context.get('weather', 'Dry, 28°C track')}

Strategy Analysis:
- Pit Window: {'Open' if strategy['pit_window_open'] else 'Closed'}
- Recommended Action: {strategy['recommended_action']}
- Next Compound: {strategy['next_compound']}
- Reasoning: {', '.join(strategy['reasoning'])}

Provide a clear, radio-style strategy call to the driver.
"""
        
        # Send to Gemini and collect response
        response_text = ""
        async for chunk in self.send_text(prompt):
            if chunk["type"] == "text":
                response_text += chunk["content"]
        
        return response_text
    
    def _set_state(self, state: AgentState):
        """Update agent state and trigger callback."""
        self.state = state
        if self.on_state_change:
            self.on_state_change(state)
        logger.debug(f"Agent state: {state.value}")
    
    def _generate_mock_response(self, text: str) -> str:
        """Generate mock response for testing when GenAI is not available."""
        text_lower = text.lower()
        
        if "pit" in text_lower:
            return "Copy that. Analyzing pit window... Based on current tyre wear, recommend staying out for 5 more laps. Confidence: high."
        elif "weather" in text_lower:
            return "Weather update: Track conditions stable, no rain expected in the next 30 minutes. Continue current strategy."
        elif "tyre" in text_lower or "tire" in text_lower:
            return "Tyre condition nominal. Mediums showing good pace with manageable degradation. Estimate 15 laps remaining life."
        elif "gap" in text_lower:
            return "Gap to leader: 8.5 seconds. Gap to car ahead: 2.1 seconds. You're in the DRS window."
        elif "strategy" in text_lower:
            return "Current strategy: One-stop. Box window opens lap 35 for fresh mediums to the end. Alternative: Two-stop aggressive if safety car."
        else:
            return "Pit Wall AI online. Standing by for race strategy queries. How can I assist?"
    
    def get_tools(self) -> list:
        """
        Get function tools for the agent (for use with function calling).
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "get_race_schedule",
                "description": "Get the F1 race schedule for the current season",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "integer",
                            "description": "Season year (optional, defaults to current)"
                        }
                    }
                }
            },
            {
                "name": "get_driver_telemetry",
                "description": "Get telemetry data for a specific driver",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "driver": {
                            "type": "string",
                            "description": "Driver code (e.g., VER, HAM, LEC)"
                        },
                        "race": {
                            "type": "string",
                            "description": "Race name or number"
                        }
                    },
                    "required": ["driver"]
                }
            },
            {
                "name": "analyze_pit_strategy",
                "description": "Analyze current race situation and recommend pit strategy",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "current_lap": {"type": "integer"},
                        "total_laps": {"type": "integer"},
                        "tyre_compound": {"type": "string"},
                        "tyre_life": {"type": "integer"}
                    },
                    "required": ["current_lap", "total_laps"]
                }
            }
        ]


# Factory function for creating agents
def create_f1_agent(voice: str = "Puck", enable_voice: bool = True) -> F1StrategistAgent:
    """
    Create and configure an F1 Strategist Agent.
    
    Args:
        voice: Voice name for audio responses
        enable_voice: Whether to enable voice output
        
    Returns:
        Configured F1StrategistAgent instance
    """
    config = AgentConfig(
        voice_name=voice,
        enable_voice=enable_voice,
        response_modality="AUDIO" if enable_voice else "TEXT"
    )
    return F1StrategistAgent(config)
