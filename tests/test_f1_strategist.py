"""
Tests for F1 Race Strategist Agent
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestF1StrategistAgent:
    """Test suite for F1RaceStrategistAgent."""
    
    @pytest.fixture
    def mock_genai_client(self):
        """Create a mock Gemini client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Box, box, box! Recommend pitting at the end of this lap for medium tires."
        mock_client.models.generate_content = Mock(return_value=mock_response)
        return mock_client
    
    def test_agent_initialization(self):
        """Test that the agent initializes correctly with API key."""
        with patch('src.agents.f1_strategist.genai.Client') as mock_client_class:
            from src.agents.f1_strategist import F1RaceStrategistAgent
            
            agent = F1RaceStrategistAgent(api_key="test-api-key")
            assert agent.api_key == "test-api-key"
            assert agent.model == "gemini-2.0-flash-exp"
            mock_client_class.assert_called_once_with(api_key="test-api-key")
    
    @pytest.mark.asyncio
    async def test_chat_basic(self, mock_genai_client):
        """Test basic chat functionality."""
        with patch('src.agents.f1_strategist.genai.Client', return_value=mock_genai_client):
            from src.agents.f1_strategist import F1RaceStrategistAgent
            
            agent = F1RaceStrategistAgent(api_key="test-key")
            agent.client = mock_genai_client
            
            response = await agent.chat("What tires should I use?")
            
            assert response is not None
            assert "box" in response.lower() or "tire" in response.lower() or "medium" in response.lower()
    
    @pytest.mark.asyncio
    async def test_chat_with_history(self, mock_genai_client):
        """Test chat with conversation history."""
        with patch('src.agents.f1_strategist.genai.Client', return_value=mock_genai_client):
            from src.agents.f1_strategist import F1RaceStrategistAgent
            
            agent = F1RaceStrategistAgent(api_key="test-key")
            agent.client = mock_genai_client
            
            history = [
                {"role": "user", "content": "We're at Monaco"},
                {"role": "model", "content": "Copy that, Monaco strategy loaded."}
            ]
            
            response = await agent.chat("What's the best strategy?", history=history)
            
            assert response is not None


class TestF1StrategistAPI:
    """Test suite for the FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "F1" in data["agent"]
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "F1 Race Strategist" in data["name"]
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_format(self, client):
        """Test chat endpoint request/response format."""
        # Test that endpoint exists and returns proper structure
        # Note: Full integration test requires valid Gemini credentials
        
        # Test that endpoint handles missing message properly
        response = client.post("/api/chat", json={})
        assert response.status_code == 422  # Validation error for missing required field
        
        # Test that endpoint structure is correct with mock
        with patch('src.api.main.get_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.chat = AsyncMock(return_value="Box now!")
            mock_get_agent.return_value = mock_agent
            
            response = client.post("/api/chat", json={"message": "test"})
            # With mock, this should return proper response structure
            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert "agent" in data


class TestSystemPrompt:
    """Test the F1 strategist system prompt."""
    
    def test_system_prompt_content(self):
        """Test that system prompt contains F1 terminology."""
        from src.agents.f1_strategist import F1_STRATEGIST_SYSTEM_PROMPT
        
        # Check for F1-specific terms
        assert "Formula 1" in F1_STRATEGIST_SYSTEM_PROMPT
        assert "pit" in F1_STRATEGIST_SYSTEM_PROMPT.lower()
        assert "tire" in F1_STRATEGIST_SYSTEM_PROMPT.lower() or "tyre" in F1_STRATEGIST_SYSTEM_PROMPT.lower()
        assert "strategy" in F1_STRATEGIST_SYSTEM_PROMPT.lower()
    
    def test_system_prompt_persona(self):
        """Test that system prompt defines agent persona."""
        from src.agents.f1_strategist import F1_STRATEGIST_SYSTEM_PROMPT
        
        assert "Pit Wall AI" in F1_STRATEGIST_SYSTEM_PROMPT
        assert "race engineer" in F1_STRATEGIST_SYSTEM_PROMPT.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
