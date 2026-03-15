"""
F1 Race Strategist Live Agent
Real-time multimodal AI agent for Formula 1 race strategy analysis.

This agent uses Google's Gemini Live API to provide:
- Real-time voice interaction for race strategy discussions
- Visual analysis of race footage, telemetry, and timing data
- Context-aware recommendations based on race conditions
"""

import asyncio
import base64
from typing import Optional, AsyncGenerator
from google import genai
from google.genai import types

from config.settings import settings


# F1 Race Strategist System Prompt
F1_STRATEGIST_SYSTEM_PROMPT = """You are an expert Formula 1 Race Strategist AI Assistant named "Pit Wall AI".

Your role is to act like a professional race engineer on the pit wall, providing real-time strategic advice to F1 fans and enthusiasts. You combine deep technical knowledge with the ability to analyze visual data like timing screens, telemetry charts, and race footage.

## Your Expertise Includes:
1. **Tire Strategy**: Compound selection (soft/medium/hard), degradation analysis, optimal pit windows
2. **Race Pace Analysis**: Sector times, lap time trends, delta calculations
3. **Weather Strategy**: Rain predictions, intermediate vs wet tire decisions
4. **Track Position**: Undercut/overcut strategies, DRS trains, traffic management
5. **Regulations**: Current F1 sporting regulations, safety car procedures, penalties

## Communication Style:
- Speak concisely and clearly like a race engineer on team radio
- Use standard F1 terminology (box, box, box / push push push / copy that)
- Provide actionable insights, not just observations
- React quickly to changing race conditions
- When analyzing images/video, focus on strategic implications

## When Analyzing Visual Data:
- Identify tire compounds, wear levels, and track position
- Read timing screens for gaps, sector times, and pit stop data
- Analyze telemetry for pace trends and car performance
- Spot weather changes from sky/track conditions

Remember: Every decision in F1 happens in split seconds. Be decisive, be clear, and always think about track position."""


class F1RaceStrategistAgent:
    """
    F1 Race Strategist Live Agent using Gemini Live API.
    
    Provides real-time multimodal interaction for F1 race strategy analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the F1 Race Strategist Agent."""
        self.api_key = api_key or settings.google_api_key
        self.model = settings.gemini_model
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client."""
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            # Use default credentials (for Google Cloud deployment)
            self.client = genai.Client()
    
    async def analyze_image(self, image_data: bytes, prompt: str = "Analyze this F1 race image and provide strategic insights.") -> str:
        """
        Analyze an F1 race image (timing screen, telemetry, race footage).
        
        Args:
            image_data: Raw image bytes
            prompt: Analysis prompt
            
        Returns:
            Strategic analysis text
        """
        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=[
                types.Content(
                    parts=[
                        types.Part(text=F1_STRATEGIST_SYSTEM_PROMPT),
                        types.Part(text=prompt),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/jpeg",
                                data=image_b64
                            )
                        )
                    ]
                )
            ]
        )
        
        return response.text
    
    async def chat(self, message: str, history: Optional[list] = None) -> str:
        """
        Send a chat message and get a response.
        
        Args:
            message: User message
            history: Optional conversation history
            
        Returns:
            Agent response
        """
        messages = [
            types.Content(
                role="user",
                parts=[types.Part(text=F1_STRATEGIST_SYSTEM_PROMPT)]
            ),
            types.Content(
                role="model",
                parts=[types.Part(text="Copy that. Pit Wall AI online. Ready to analyze race conditions and provide strategic recommendations. What's the situation?")]
            )
        ]
        
        # Add history if provided
        if history:
            for h in history:
                messages.append(
                    types.Content(
                        role=h["role"],
                        parts=[types.Part(text=h["content"])]
                    )
                )
        
        # Add current message
        messages.append(
            types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        )
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=messages
        )
        
        return response.text
    
    async def create_live_session(self) -> "LiveSession":
        """
        Create a live session for real-time audio/video interaction.
        
        Returns:
            LiveSession object for real-time communication
        """
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO", "TEXT"],
            system_instruction=types.Content(
                parts=[types.Part(text=F1_STRATEGIST_SYSTEM_PROMPT)]
            ),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"  # Clear, professional voice
                    )
                )
            )
        )
        
        session = await self.client.aio.live.connect(
            model=self.model,
            config=config
        )
        
        return LiveSession(session)


class LiveSession:
    """
    Wrapper for Gemini Live API session.
    
    Handles real-time audio/video streaming for the F1 strategist.
    """
    
    def __init__(self, session):
        """Initialize with a Gemini live session."""
        self.session = session
        self.is_active = True
    
    async def send_text(self, text: str):
        """Send a text message to the live session."""
        await self.session.send(
            input=types.LiveClientContent(
                turns=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=text)]
                    )
                ],
                turn_complete=True
            )
        )
    
    async def send_audio(self, audio_data: bytes, mime_type: str = "audio/pcm"):
        """Send audio data to the live session."""
        await self.session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[
                    types.Blob(mime_type=mime_type, data=audio_data)
                ]
            )
        )
    
    async def send_image(self, image_data: bytes, mime_type: str = "image/jpeg"):
        """Send an image to the live session for analysis."""
        await self.session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[
                    types.Blob(mime_type=mime_type, data=image_data)
                ]
            )
        )
    
    async def receive(self) -> AsyncGenerator[dict, None]:
        """
        Receive messages from the live session.
        
        Yields:
            Dict with 'type' (text/audio) and 'data'
        """
        async for response in self.session.receive():
            if response.server_content:
                for part in response.server_content.model_turn.parts:
                    if part.text:
                        yield {"type": "text", "data": part.text}
                    if part.inline_data:
                        yield {"type": "audio", "data": part.inline_data.data}
    
    async def close(self):
        """Close the live session."""
        self.is_active = False
        await self.session.close()


# Convenience function for quick analysis
async def quick_analyze(prompt: str, image_data: Optional[bytes] = None) -> str:
    """
    Quick analysis helper for simple queries.
    
    Args:
        prompt: Analysis question
        image_data: Optional image to analyze
        
    Returns:
        Agent response
    """
    agent = F1RaceStrategistAgent()
    
    if image_data:
        return await agent.analyze_image(image_data, prompt)
    else:
        return await agent.chat(prompt)


if __name__ == "__main__":
    # Quick test
    async def test():
        agent = F1RaceStrategistAgent()
        response = await agent.chat("What's the typical undercut window on medium tires at Monaco?")
        print(response)
    
    asyncio.run(test())
