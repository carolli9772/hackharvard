from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VesselPosition(BaseModel):
    """Single AIS position record"""
    mmsi: int
    timestamp: datetime
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = None
    course: Optional[float] = None
    vessel_name: Optional[str] = None
    vessel_type: Optional[str] = None

class DarkPeriod(BaseModel):
    """Detected AIS dark period"""
    id: Optional[int] = None
    mmsi: int
    start_time: datetime
    end_time: datetime
    duration_hours: float
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    distance_km: float
    risk_score: float
    in_mpa: bool = False
    in_eez: Optional[str] = None
    is_nighttime: bool = False

class VesselRiskSummary(BaseModel):
    """Risk summary for a vessel"""
    mmsi: int
    vessel_name: Optional[str] = None
    vessel_type: Optional[str] = None
    total_dark_periods: int
    total_dark_hours: float
    avg_risk_score: float
    max_risk_score: float
    high_risk_events: int  # Events with risk > 0.7
    last_seen: datetime
    last_position: dict

class HeatmapPoint(BaseModel):
    """Point for heatmap visualization"""
    lat: float
    lon: float
    risk_score: float
    count: int

class VesselTrackPoint(BaseModel):
    """Point in vessel track for visualization"""
    timestamp: datetime
    lat: float
    lon: float
    speed: Optional[float] = None
    is_dark_period: bool = False
    risk_score: Optional[float] = None

class DetectionRequest(BaseModel):
    """Request to detect dark periods"""
    mmsi: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_risk_score: float = 0.0

class DetectionResponse(BaseModel):
    """Response from dark period detection"""
    total_vessels: int
    dark_periods_detected: int
    high_risk_events: int
    processing_time_seconds: float
    results: List[DarkPeriod]

class StatsResponse(BaseModel):
    """Overall statistics"""
    total_vessels: int
    total_ais_records: int
    total_dark_periods: int
    avg_risk_score: float
    coverage_start_date: datetime
    coverage_end_date: datetime
    high_risk_zones: List[dict]
