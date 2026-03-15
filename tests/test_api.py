"""
F1 Pit Wall AI - API Tests
Tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "F1 Pit Wall AI"
        assert data["google_cloud"] is True


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_api_info(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "F1 Pit Wall AI"
        assert "endpoints" in data
        assert "powered_by" in data


class TestScheduleEndpoint:
    """Tests for schedule endpoint."""
    
    def test_get_schedule(self, client):
        """Test getting race schedule."""
        response = client.get("/api/schedule")
        
        assert response.status_code == 200
        data = response.json()
        assert "year" in data
        assert "races" in data
        assert len(data["races"]) > 0
    
    def test_get_schedule_with_year(self, client):
        """Test getting schedule for specific year."""
        response = client.get("/api/schedule?year=2025")
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2025


class TestStrategyEndpoint:
    """Tests for strategy analysis endpoint."""
    
    def test_analyze_strategy(self, client):
        """Test strategy analysis."""
        request_data = {
            "current_lap": 25,
            "total_laps": 57,
            "position": 3,
            "tyre_compound": "MEDIUM",
            "tyre_life": 20
        }
        
        response = client.post("/api/strategy", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "summary" in data
        assert "confidence" in data
    
    def test_analyze_strategy_rain(self, client):
        """Test strategy with rain condition."""
        request_data = {
            "current_lap": 30,
            "total_laps": 57,
            "position": 5,
            "tyre_compound": "SOFT",
            "tyre_life": 15,
            "weather": "Rain starting"
        }
        
        response = client.post("/api/strategy", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        # Should detect rain and recommend pitting
        assert "PIT" in data["analysis"]["recommended_action"]


class TestDemoPage:
    """Tests for demo page."""
    
    def test_demo_page_loads(self, client):
        """Test demo page returns HTML."""
        response = client.get("/demo")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "F1 Pit Wall AI" in response.text


class TestSessionManagement:
    """Tests for session management."""
    
    def test_list_sessions(self, client):
        """Test listing sessions."""
        response = client.get("/api/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_close_nonexistent_session(self, client):
        """Test closing a session that doesn't exist."""
        response = client.delete("/api/sessions/nonexistent")
        
        assert response.status_code == 404


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
