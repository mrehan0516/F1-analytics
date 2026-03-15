"""
F1 Pit Wall AI - Test Suite
Tests for F1 data service and strategy analysis
"""
import pytest
from unittest.mock import Mock, patch
import asyncio

# Test F1 Data Service
from src.services.f1_data_service import F1DataService, f1_service


class TestF1DataService:
    """Tests for the F1 Data Service."""
    
    def test_get_current_season(self):
        """Test getting the current season year."""
        service = F1DataService()
        year = service.get_current_season()
        assert isinstance(year, int)
        assert year >= 2024
    
    def test_get_race_schedule(self):
        """Test getting race schedule."""
        service = F1DataService()
        schedule = service.get_race_schedule()
        
        assert isinstance(schedule, list)
        assert len(schedule) > 0
        
        # Check schedule structure
        race = schedule[0]
        assert "round" in race
        assert "name" in race
        assert "country" in race
        assert "circuit" in race
        assert "date" in race
    
    def test_get_mock_schedule(self):
        """Test mock schedule generation."""
        service = F1DataService()
        schedule = service._get_mock_schedule(2026)
        
        assert len(schedule) >= 6
        assert schedule[0]["name"] == "Bahrain Grand Prix"
        assert schedule[0]["round"] == 1
    
    def test_analyze_pit_strategy_stay_out(self):
        """Test strategy analysis when tyres are fresh."""
        service = F1DataService()
        
        race_data = {
            "tyre_life": 10,
            "compound": "MEDIUM",
            "weather": {"rainfall": False}
        }
        
        strategy = service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=25,
            total_laps=57
        )
        
        assert strategy["recommended_action"] == "STAY OUT"
        assert strategy["pit_window_open"] is False
        assert len(strategy["reasoning"]) > 0
    
    def test_analyze_pit_strategy_pit_soon(self):
        """Test strategy analysis when tyres are worn."""
        service = F1DataService()
        
        race_data = {
            "tyre_life": 28,  # High wear for MEDIUM
            "compound": "MEDIUM",
            "weather": {"rainfall": False}
        }
        
        strategy = service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=30,
            total_laps=57
        )
        
        assert strategy["recommended_action"] == "PIT SOON"
        assert strategy["pit_window_open"] is True
        assert strategy["next_compound"] is not None
    
    def test_analyze_pit_strategy_rain(self):
        """Test strategy analysis with rain."""
        service = F1DataService()
        
        race_data = {
            "tyre_life": 10,
            "compound": "SOFT",
            "weather": {"rainfall": True}
        }
        
        strategy = service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=20,
            total_laps=57
        )
        
        assert strategy["recommended_action"] == "PIT NOW"
        assert strategy["next_compound"] == "INTERMEDIATE"
        assert strategy["confidence"] == 0.95
    
    def test_get_mock_telemetry(self):
        """Test mock telemetry data."""
        service = F1DataService()
        telemetry = service._get_mock_telemetry("VER")
        
        assert telemetry["driver"] == "VER"
        assert "lap_time" in telemetry
        assert "speed" in telemetry
        assert "max" in telemetry["speed"]
        assert "avg" in telemetry["speed"]
        assert "min" in telemetry["speed"]
    
    def test_get_live_timing_context(self):
        """Test context generation for AI."""
        service = F1DataService()
        context = service.get_live_timing_context()
        
        assert isinstance(context, str)
        assert "F1 Season Overview" in context
        assert "Strategy Expertise" in context


class TestPitStrategyLogic:
    """Test various pit strategy scenarios."""
    
    @pytest.fixture
    def service(self):
        return F1DataService()
    
    def test_undercut_window(self, service):
        """Test undercut opportunity detection."""
        race_data = {
            "tyre_life": 18,
            "compound": "MEDIUM",
            "weather": {"rainfall": False}
        }
        
        strategy = service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=20,  # Within undercut window
            total_laps=57
        )
        
        assert strategy["pit_window_open"] is True
        assert strategy["recommended_action"] == "CONSIDER PIT"
    
    def test_soft_tyre_degradation(self, service):
        """Test soft tyre degradation threshold."""
        race_data = {
            "tyre_life": 18,  # 90% of optimal 20 laps
            "compound": "SOFT",
            "weather": {"rainfall": False}
        }
        
        strategy = service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=30,
            total_laps=57
        )
        
        assert strategy["pit_window_open"] is True
    
    def test_hard_tyre_longevity(self, service):
        """Test hard tyre can go longer."""
        race_data = {
            "tyre_life": 25,
            "compound": "HARD",
            "weather": {"rainfall": False}
        }
        
        strategy = service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=30,
            total_laps=57
        )
        
        # Hard tyres at 25 laps (62.5% of 40) should still be OK
        assert strategy["recommended_action"] in ["STAY OUT", "CONSIDER PIT"]
    
    def test_end_of_race_compound_selection(self, service):
        """Test compound selection based on remaining laps."""
        # Test with few remaining laps
        race_data = {
            "tyre_life": 35,
            "compound": "MEDIUM",
            "weather": {"rainfall": False}
        }
        
        strategy = service.analyze_pit_strategy(
            race_data=race_data,
            current_lap=45,  # Only 12 laps remaining
            total_laps=57
        )
        
        # Should recommend SOFT for short stint
        if strategy["next_compound"]:
            assert strategy["next_compound"] == "SOFT"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
