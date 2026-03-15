"""
F1 Data Service - Real-time race data and telemetry processing
"""
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class F1DataService:
    """
    Service for fetching and processing F1 race data using FastF1.
    Provides real-time insights for race strategy decisions.
    """
    
    def __init__(self, cache_dir: str = "./f1_cache"):
        """Initialize F1 Data Service with cache directory."""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Enable FastF1 cache
        try:
            import fastf1
            fastf1.Cache.enable_cache(cache_dir)
            self.fastf1 = fastf1
            logger.info(f"FastF1 cache enabled at {cache_dir}")
        except ImportError:
            logger.warning("FastF1 not installed. Using mock data.")
            self.fastf1 = None
    
    def get_current_season(self) -> int:
        """Get current F1 season year."""
        return datetime.now().year
    
    def get_race_schedule(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get F1 race schedule for a given year.
        
        Args:
            year: Season year (defaults to current year)
            
        Returns:
            List of race information dictionaries
        """
        year = year or self.get_current_season()
        
        if self.fastf1:
            try:
                schedule = self.fastf1.get_event_schedule(year)
                races = []
                for _, event in schedule.iterrows():
                    races.append({
                        "round": int(event.get("RoundNumber", 0)),
                        "name": event.get("EventName", "Unknown"),
                        "country": event.get("Country", "Unknown"),
                        "circuit": event.get("Location", "Unknown"),
                        "date": str(event.get("EventDate", "")),
                    })
                return races
            except Exception as e:
                logger.error(f"Error fetching schedule: {e}")
        
        # Mock data for demonstration
        return self._get_mock_schedule(year)
    
    def _get_mock_schedule(self, year: int) -> List[Dict[str, Any]]:
        """Return mock F1 schedule for demonstration."""
        return [
            {"round": 1, "name": "Bahrain Grand Prix", "country": "Bahrain", "circuit": "Sakhir", "date": f"{year}-03-02"},
            {"round": 2, "name": "Saudi Arabian Grand Prix", "country": "Saudi Arabia", "circuit": "Jeddah", "date": f"{year}-03-09"},
            {"round": 3, "name": "Australian Grand Prix", "country": "Australia", "circuit": "Melbourne", "date": f"{year}-03-24"},
            {"round": 4, "name": "Japanese Grand Prix", "country": "Japan", "circuit": "Suzuka", "date": f"{year}-04-07"},
            {"round": 5, "name": "Chinese Grand Prix", "country": "China", "circuit": "Shanghai", "date": f"{year}-04-21"},
            {"round": 6, "name": "Miami Grand Prix", "country": "USA", "circuit": "Miami", "date": f"{year}-05-04"},
        ]
    
    def get_session_data(self, year: int, race: str, session: str = "R") -> Optional[Dict[str, Any]]:
        """
        Get session data for a specific race.
        
        Args:
            year: Season year
            race: Race name or round number
            session: Session type (R=Race, Q=Qualifying, FP1/FP2/FP3=Practice)
            
        Returns:
            Session data dictionary
        """
        if self.fastf1:
            try:
                sess = self.fastf1.get_session(year, race, session)
                sess.load()
                
                return {
                    "event_name": sess.event.EventName,
                    "session_name": sess.name,
                    "date": str(sess.date),
                    "weather": self._extract_weather(sess),
                    "results": self._extract_results(sess),
                    "fastest_lap": self._extract_fastest_lap(sess),
                }
            except Exception as e:
                logger.error(f"Error loading session: {e}")
        
        return self._get_mock_session_data(year, race, session)
    
    def _extract_weather(self, session) -> Dict[str, Any]:
        """Extract weather data from session."""
        try:
            weather = session.weather_data
            if weather is not None and len(weather) > 0:
                latest = weather.iloc[-1]
                return {
                    "air_temp": float(latest.get("AirTemp", 25)),
                    "track_temp": float(latest.get("TrackTemp", 35)),
                    "humidity": float(latest.get("Humidity", 50)),
                    "rainfall": bool(latest.get("Rainfall", False)),
                }
        except Exception:
            pass
        return {"air_temp": 25, "track_temp": 35, "humidity": 50, "rainfall": False}
    
    def _extract_results(self, session) -> List[Dict[str, Any]]:
        """Extract race results from session."""
        try:
            results = session.results
            if results is not None:
                return [
                    {
                        "position": int(row.get("Position", 0)),
                        "driver": row.get("Abbreviation", ""),
                        "team": row.get("TeamName", ""),
                        "time": str(row.get("Time", "")),
                        "points": float(row.get("Points", 0)),
                    }
                    for _, row in results.head(10).iterrows()
                ]
        except Exception:
            pass
        return []
    
    def _extract_fastest_lap(self, session) -> Dict[str, Any]:
        """Extract fastest lap information."""
        try:
            laps = session.laps
            if laps is not None and len(laps) > 0:
                fastest = laps.pick_fastest()
                return {
                    "driver": fastest.get("Driver", ""),
                    "time": str(fastest.get("LapTime", "")),
                    "lap_number": int(fastest.get("LapNumber", 0)),
                }
        except Exception:
            pass
        return {"driver": "VER", "time": "1:30.000", "lap_number": 45}
    
    def _get_mock_session_data(self, year: int, race: str, session: str) -> Dict[str, Any]:
        """Return mock session data for demonstration."""
        return {
            "event_name": race if isinstance(race, str) else f"Round {race}",
            "session_name": session,
            "date": f"{year}-03-15",
            "weather": {"air_temp": 28, "track_temp": 42, "humidity": 45, "rainfall": False},
            "results": [
                {"position": 1, "driver": "VER", "team": "Red Bull Racing", "time": "1:32:45.678", "points": 25},
                {"position": 2, "driver": "NOR", "team": "McLaren", "time": "+5.234", "points": 18},
                {"position": 3, "driver": "LEC", "team": "Ferrari", "time": "+12.567", "points": 15},
                {"position": 4, "driver": "PIA", "team": "McLaren", "time": "+18.901", "points": 12},
                {"position": 5, "driver": "SAI", "team": "Ferrari", "time": "+22.345", "points": 10},
            ],
            "fastest_lap": {"driver": "VER", "time": "1:31.234", "lap_number": 42},
        }
    
    def get_driver_telemetry(self, year: int, race: str, driver: str, lap: Optional[int] = None) -> Dict[str, Any]:
        """
        Get driver telemetry data for analysis.
        
        Args:
            year: Season year
            race: Race name or round
            driver: Driver abbreviation (e.g., "VER", "HAM")
            lap: Specific lap number (None for fastest lap)
            
        Returns:
            Telemetry data dictionary
        """
        if self.fastf1:
            try:
                session = self.fastf1.get_session(year, race, "R")
                session.load()
                
                driver_laps = session.laps.pick_driver(driver)
                
                if lap:
                    target_lap = driver_laps[driver_laps["LapNumber"] == lap].iloc[0]
                else:
                    target_lap = driver_laps.pick_fastest()
                
                telemetry = target_lap.get_telemetry()
                
                return {
                    "driver": driver,
                    "lap_number": int(target_lap.get("LapNumber", 0)),
                    "lap_time": str(target_lap.get("LapTime", "")),
                    "compound": target_lap.get("Compound", "MEDIUM"),
                    "tyre_life": int(target_lap.get("TyreLife", 0)),
                    "speed": {
                        "max": float(telemetry["Speed"].max()),
                        "avg": float(telemetry["Speed"].mean()),
                        "min": float(telemetry["Speed"].min()),
                    },
                    "throttle_avg": float(telemetry["Throttle"].mean()),
                    "brake_avg": float(telemetry["Brake"].mean()),
                }
            except Exception as e:
                logger.error(f"Error fetching telemetry: {e}")
        
        return self._get_mock_telemetry(driver)
    
    def _get_mock_telemetry(self, driver: str) -> Dict[str, Any]:
        """Return mock telemetry data for demonstration."""
        return {
            "driver": driver,
            "lap_number": 42,
            "lap_time": "1:31.456",
            "compound": "MEDIUM",
            "tyre_life": 18,
            "speed": {"max": 342.5, "avg": 218.3, "min": 68.2},
            "throttle_avg": 72.5,
            "brake_avg": 15.3,
        }
    
    def analyze_pit_strategy(self, race_data: Dict[str, Any], current_lap: int, total_laps: int) -> Dict[str, Any]:
        """
        Analyze and recommend pit stop strategy.
        
        Args:
            race_data: Current race state data
            current_lap: Current lap number
            total_laps: Total race laps
            
        Returns:
            Strategy recommendation dictionary
        """
        remaining_laps = total_laps - current_lap
        tyre_life = race_data.get("tyre_life", 20)
        compound = race_data.get("compound", "MEDIUM")
        weather = race_data.get("weather", {})
        
        # Strategy logic
        recommendation = {
            "current_compound": compound,
            "tyre_life": tyre_life,
            "remaining_laps": remaining_laps,
            "pit_window_open": False,
            "recommended_action": "STAY OUT",
            "next_compound": None,
            "confidence": 0.75,
            "reasoning": [],
        }
        
        # Tyre degradation analysis
        if compound == "SOFT":
            optimal_life = 20
        elif compound == "MEDIUM":
            optimal_life = 30
        else:  # HARD
            optimal_life = 40
        
        degradation_factor = tyre_life / optimal_life
        
        # Weather check
        if weather.get("rainfall", False):
            recommendation["pit_window_open"] = True
            recommendation["recommended_action"] = "PIT NOW"
            recommendation["next_compound"] = "INTERMEDIATE"
            recommendation["confidence"] = 0.95
            recommendation["reasoning"].append("Rain detected - switch to intermediates")
        
        # Tyre life check
        elif degradation_factor > 0.8:
            recommendation["pit_window_open"] = True
            recommendation["recommended_action"] = "PIT SOON"
            
            if remaining_laps <= 25:
                recommendation["next_compound"] = "SOFT"
            elif remaining_laps <= 35:
                recommendation["next_compound"] = "MEDIUM"
            else:
                recommendation["next_compound"] = "HARD"
            
            recommendation["confidence"] = 0.85
            recommendation["reasoning"].append(f"Tyre degradation at {degradation_factor*100:.0f}%")
            recommendation["reasoning"].append(f"Recommend {recommendation['next_compound']} for remaining {remaining_laps} laps")
        
        # Undercut/Overcut opportunity
        elif 15 <= current_lap <= 25 and tyre_life >= 15:
            recommendation["pit_window_open"] = True
            recommendation["recommended_action"] = "CONSIDER PIT"
            recommendation["next_compound"] = "HARD"
            recommendation["confidence"] = 0.65
            recommendation["reasoning"].append("Strategic window for undercut opportunity")
        
        else:
            recommendation["reasoning"].append(f"Tyres in good condition ({tyre_life} laps)")
            recommendation["reasoning"].append("Continue current stint")
        
        return recommendation
    
    def get_live_timing_context(self) -> str:
        """
        Generate a context summary for the AI agent about current F1 state.
        
        Returns:
            Formatted context string for Gemini
        """
        schedule = self.get_race_schedule()
        
        context = """
## F1 Season Overview
You have access to comprehensive F1 data including:
- Race schedules and circuit information
- Historical race results and standings
- Lap times and telemetry analysis
- Tyre compound strategies and pit stop timing
- Weather conditions and their impact on strategy

## Current Season Races
"""
        for race in schedule[:5]:
            context += f"- Round {race['round']}: {race['name']} ({race['circuit']}, {race['country']})\n"
        
        context += """
## Strategy Expertise
As a Pit Wall AI, you excel at:
1. Real-time race strategy decisions
2. Pit stop timing optimization
3. Tyre compound selection
4. Weather-based adaptations
5. Competitor analysis and positioning
6. Undercut/overcut strategy calls

Always provide clear, confident recommendations with reasoning.
"""
        return context


# Export service instance
f1_service = F1DataService()
