from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import time
import logging
import pandas as pd

from ..models.database import get_db
from ..models.schemas import (
    DetectionRequest, DetectionResponse, DarkPeriod,
    VesselRiskSummary, HeatmapPoint, StatsResponse, VesselTrackPoint
)
from ..services.dark_period_detector import DarkPeriodDetector
from ..services.data_loader import DataLoader
from ..services.comprehensive_detector import ComprehensiveIllegalFishingDetector
from ..services.network_analyzer import VesselNetworkAnalyzer
from ..services.hotspot_analyzer import HotspotAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
detector = DarkPeriodDetector()
loader = DataLoader()
network_analyzer = VesselNetworkAnalyzer(proximity_threshold_km=50.0)
hotspot_analyzer = HotspotAnalyzer(grid_size_degrees=1.0)

# Load MPA data once at startup
logger.info("Loading Marine Protected Areas data...")
mpa_data = loader.load_mpa_data()
comprehensive_detector = ComprehensiveIllegalFishingDetector(mpa_data=mpa_data)
logger.info(f"✓ Loaded {len(mpa_data)} Marine Protected Areas")

@router.post("/detect", response_model=DetectionResponse)
async def detect_dark_periods(
    request: DetectionRequest,
    sample_size: Optional[int] = Query(10000, description="Number of records per vessel type"),
    db: Session = Depends(get_db)
):
    """
    Comprehensive illegal fishing detection using ALL data sources
    
    Analyzes: AIS dark periods, MPA violations, speed anomalies, fishing patterns
    """
    start_time = time.time()

    try:
        # Load ALL fishing vessel data from all types
        logger.info(f"Loading ALL fishing vessel types for comprehensive analysis")
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=sample_size)

        if request.mmsi:
            fishing_data = fishing_data[fishing_data['mmsi'] == request.mmsi]

        # Run COMPREHENSIVE detection
        logger.info(f"Running comprehensive detection on {fishing_data['mmsi'].nunique()} vessels")
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        # Filter by date and risk
        if not suspicious_events.empty:
            if request.start_date:
                suspicious_events = suspicious_events[suspicious_events['start_time'] >= request.start_date]
            if request.end_date:
                suspicious_events = suspicious_events[suspicious_events['end_time'] <= request.end_date]
            if 'total_risk_score' in suspicious_events.columns:
                suspicious_events = suspicious_events[suspicious_events['total_risk_score'] >= request.min_risk_score]

        results = suspicious_events.to_dict('records') if not suspicious_events.empty else []
        high_risk_count = len([r for r in results if r.get('total_risk_score', 0) > 0.7])

        processing_time = time.time() - start_time

        return DetectionResponse(
            total_vessels=fishing_data['mmsi'].nunique(),
            dark_periods_detected=len(results),
            high_risk_events=high_risk_count,
            processing_time_seconds=round(processing_time, 2),
            results=[DarkPeriod(**{
                'mmsi': r['mmsi'],
                'start_time': r['start_time'],
                'end_time': r['end_time'],
                'duration_hours': r.get('dark_period_hours', 0),
                'start_lat': r['start_lat'],
                'start_lon': r['start_lon'],
                'end_lat': r['end_lat'],
                'end_lon': r['end_lon'],
                'distance_km': 0,  # TODO: calculate
                'risk_score': r.get('total_risk_score', 0),
                'in_mpa': r.get('mpa_violation', False),
                'in_eez': None,
                'is_nighttime': r.get('nighttime_operation', False)
            }) for r in results]
        )

    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vessels", response_model=List[VesselRiskSummary])
async def get_vessel_summaries(
    min_risk_score: float = Query(0.5, description="Minimum average risk score"),
    limit: int = Query(100, description="Maximum vessels to return"),
    db: Session = Depends(get_db)
):
    """Get comprehensive risk profiles for all suspicious vessels"""
    try:
        # Load ALL fishing vessel data
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=10000)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        if suspicious_events.empty:
            return []

        # Get vessel risk profiles
        vessel_profiles = comprehensive_detector.calculate_vessel_risk_profile(suspicious_events)
        
        # Filter and limit
        vessel_profiles = vessel_profiles[vessel_profiles['avg_risk_score'] >= min_risk_score]
        vessel_profiles = vessel_profiles.head(limit)

        # Convert to response format
        results = []
        for _, profile in vessel_profiles.iterrows():
            results.append(VesselRiskSummary(
                mmsi=int(profile['mmsi']),
                vessel_name=None,
                vessel_type=profile.get('vessel_type'),
                total_dark_periods=int(profile['total_suspicious_events']),
                total_dark_hours=float(profile['total_dark_hours']),
                avg_risk_score=float(profile['avg_risk_score']),
                max_risk_score=float(profile['max_risk_score']),
                high_risk_events=int(profile['high_risk_events']),
                last_seen=profile['last_violation_time'],
                last_position={'lat': float(profile['last_lat']), 'lon': float(profile['last_lon'])}
            ))

        return results

    except Exception as e:
        logger.error(f"Failed to get vessel summaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heatmap", response_model=List[HeatmapPoint])
async def get_heatmap_data(
    grid_size: float = Query(0.5, description="Grid cell size in degrees"),
    min_risk: float = Query(0.3, description="Minimum risk score"),
    db: Session = Depends(get_db)
):
    """Get heatmap of suspicious activity hotspots"""
    try:
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=10000)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        if suspicious_events.empty:
            return []

        # Filter by risk
        if 'total_risk_score' in suspicious_events.columns:
            suspicious_events = suspicious_events[suspicious_events['total_risk_score'] >= min_risk]

        # Generate heatmap
        suspicious_events['lat_grid'] = (suspicious_events['end_lat'] / grid_size).round() * grid_size
        suspicious_events['lon_grid'] = (suspicious_events['end_lon'] / grid_size).round() * grid_size

        heatmap = suspicious_events.groupby(['lat_grid', 'lon_grid']).agg({
            'total_risk_score': 'mean',
            'mmsi': 'count'
        }).reset_index()

        return [HeatmapPoint(
            lat=row['lat_grid'],
            lon=row['lon_grid'],
            risk_score=row['total_risk_score'],
            count=row['mmsi']
        ) for _, row in heatmap.iterrows()]

    except Exception as e:
        logger.error(f"Failed to generate heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_overall_statistics(db: Session = Depends(get_db)):
    """Get comprehensive system statistics"""
    try:
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=10000)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        stats = {
            'total_vessels': int(fishing_data['mmsi'].nunique()),
            'total_ais_records': len(fishing_data),
            'total_dark_periods': len(suspicious_events),
            'avg_risk_score': float(suspicious_events['total_risk_score'].mean()) if not suspicious_events.empty else 0.0,
            'coverage_start_date': fishing_data['timestamp'].min(),
            'coverage_end_date': fishing_data['timestamp'].max(),
            'high_risk_zones': []
        }

        return StatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "FishNet Comprehensive Illegal Fishing Detection API",
        "mpa_data_loaded": len(mpa_data),
        "timestamp": datetime.utcnow()
    }


# ========== NETWORK ANALYSIS ENDPOINTS ==========

@router.get("/network/communities")
async def get_vessel_communities(
    sample_size: Optional[int] = Query(10000, description="Sample size per vessel type"),
    min_risk: float = Query(0.3, description="Minimum risk threshold")
):
    """
    Detect coordinated vessel communities using network analysis.
    Returns clusters of vessels that frequently operate together during dark periods.
    """
    try:
        # Load data and detect suspicious events
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=sample_size)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        # Filter by risk
        suspicious_events_df = pd.DataFrame(suspicious_events)
        suspicious_events_df = suspicious_events_df[suspicious_events_df['risk_score'] >= min_risk]

        # Build network and detect communities
        network_analyzer.build_network(suspicious_events_df, fishing_data)
        communities = network_analyzer.detect_communities()

        return {
            "total_communities": len(communities),
            "network_stats": network_analyzer.get_network_stats(),
            "communities": communities
        }

    except Exception as e:
        logger.error(f"Failed to detect communities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/coordinators")
async def get_coordinators(
    sample_size: Optional[int] = Query(10000, description="Sample size per vessel type"),
    min_risk: float = Query(0.3, description="Minimum risk threshold")
):
    """
    Identify potential coordinator vessels that bridge different fishing groups.
    These vessels may be organizing illegal fishing operations.
    """
    try:
        # Load data and detect suspicious events
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=sample_size)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        # Filter by risk
        suspicious_events_df = pd.DataFrame(suspicious_events)
        suspicious_events_df = suspicious_events_df[suspicious_events_df['risk_score'] >= min_risk]

        # Build network and identify coordinators
        network_analyzer.build_network(suspicious_events_df, fishing_data)
        coordinators = network_analyzer.identify_coordinators()

        return {
            "total_coordinators": len(coordinators),
            "network_stats": network_analyzer.get_network_stats(),
            "coordinators": coordinators[:20]  # Top 20
        }

    except Exception as e:
        logger.error(f"Failed to identify coordinators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/motherships")
async def get_motherships(
    sample_size: Optional[int] = Query(10000, description="Sample size per vessel type"),
    min_risk: float = Query(0.3, description="Minimum risk threshold")
):
    """
    Identify potential mothership vessels (non-fishing vessels supporting fishing operations).
    Motherships may provide fuel, supplies, or transfer catch from fishing vessels.
    """
    try:
        # Load data and detect suspicious events
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=sample_size)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        # Filter by risk
        suspicious_events_df = pd.DataFrame(suspicious_events)
        suspicious_events_df = suspicious_events_df[suspicious_events_df['risk_score'] >= min_risk]

        # Build network and identify motherships
        network_analyzer.build_network(suspicious_events_df, fishing_data)
        motherships = network_analyzer.identify_motherships()

        return {
            "total_motherships": len(motherships),
            "motherships": motherships
        }

    except Exception as e:
        logger.error(f"Failed to identify motherships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotspots")
async def get_hotspots(
    sample_size: Optional[int] = Query(10000, description="Sample size per vessel type"),
    min_risk: float = Query(0.3, description="Minimum risk threshold"),
    min_events: int = Query(3, description="Minimum events to form a hotspot"),
    grid_size: float = Query(1.0, description="Grid size in degrees")
):
    """
    Identify geographic hotspots of illegal fishing activity.
    Returns areas with concentrated suspicious events.
    """
    try:
        # Load data and detect suspicious events
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=sample_size)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        # Filter by risk
        suspicious_events_df = pd.DataFrame(suspicious_events)
        suspicious_events_df = suspicious_events_df[suspicious_events_df['risk_score'] >= min_risk]

        # Analyze hotspots
        hotspot_analyzer_temp = HotspotAnalyzer(grid_size_degrees=grid_size)
        hotspots = hotspot_analyzer_temp.find_hotspots(suspicious_events_df, min_events=min_events)

        return {
            "total_hotspots": len(hotspots),
            "grid_size_degrees": grid_size,
            "min_events": min_events,
            "hotspots": hotspots[:50]  # Top 50 hotspots
        }

    except Exception as e:
        logger.error(f"Failed to find hotspots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotspots/mpa-violations")
async def get_mpa_violation_hotspots(
    sample_size: Optional[int] = Query(10000, description="Sample size per vessel type"),
    min_risk: float = Query(0.3, description="Minimum risk threshold")
):
    """
    Identify hotspots specifically within Marine Protected Areas.
    These represent the most serious violations.
    """
    try:
        # Load data and detect suspicious events
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=sample_size)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        # Filter by risk
        suspicious_events_df = pd.DataFrame(suspicious_events)
        suspicious_events_df = suspicious_events_df[suspicious_events_df['risk_score'] >= min_risk]

        # Find MPA violation hotspots
        mpa_hotspots = hotspot_analyzer.find_mpa_violations(suspicious_events_df, mpa_data)

        return {
            "total_mpa_hotspots": len(mpa_hotspots),
            "mpa_hotspots": mpa_hotspots
        }

    except Exception as e:
        logger.error(f"Failed to find MPA violation hotspots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotspots/temporal")
async def get_temporal_patterns(
    sample_size: Optional[int] = Query(10000, description="Sample size per vessel type"),
    min_risk: float = Query(0.3, description="Minimum risk threshold")
):
    """
    Analyze temporal patterns in illegal fishing activity (e.g., seasonal trends).
    """
    try:
        # Load data and detect suspicious events
        fishing_data = loader.load_all_fishing_vessels(sample_size_per_type=sample_size)
        suspicious_events = comprehensive_detector.detect_illegal_activity(fishing_data)

        # Filter by risk
        suspicious_events_df = pd.DataFrame(suspicious_events)
        suspicious_events_df = suspicious_events_df[suspicious_events_df['risk_score'] >= min_risk]

        # Analyze temporal patterns
        temporal_patterns = hotspot_analyzer.find_temporal_hotspots(suspicious_events_df)

        return {
            "total_patterns": len(temporal_patterns),
            "temporal_patterns": temporal_patterns
        }

    except Exception as e:
        logger.error(f"Failed to analyze temporal patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))
