"""
Dark Event Hotspot Analysis
Identifies geographic hotspots of suspicious fishing activity.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class HotspotAnalyzer:
    """Analyzes geographic distribution of dark events to find hotspots."""

    def __init__(self, grid_size_degrees: float = 1.0):
        """
        Initialize hotspot analyzer.

        Args:
            grid_size_degrees: Size of grid cells in degrees (default 1.0 = ~110km)
        """
        self.grid_size = grid_size_degrees

    def find_hotspots(
        self,
        suspicious_events: pd.DataFrame,
        min_events: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find geographic hotspots of dark events using grid-based aggregation.

        Args:
            suspicious_events: DataFrame with suspicious events
            min_events: Minimum events required to be considered a hotspot

        Returns:
            List of hotspot dictionaries
        """
        logger.info(f"Finding dark event hotspots (grid size: {self.grid_size}°)...")

        # Create grid cells
        grid_data = defaultdict(lambda: {
            'events': [],
            'vessels': set(),
            'total_risk': 0,
            'locations': []
        })

        # Aggregate events into grid cells
        for _, event in suspicious_events.iterrows():
            # Calculate grid cell
            grid_lat = int(event['start_lat'] / self.grid_size) * self.grid_size
            grid_lon = int(event['start_lon'] / self.grid_size) * self.grid_size
            grid_key = (grid_lat, grid_lon)

            # Add event to grid cell
            grid_data[grid_key]['events'].append(event.to_dict())
            grid_data[grid_key]['vessels'].add(event['mmsi'])
            grid_data[grid_key]['total_risk'] += event.get('risk_score', 0)
            grid_data[grid_key]['locations'].append({
                'lat': event['start_lat'],
                'lon': event['start_lon']
            })

        # Convert to hotspot list
        hotspots = []
        for (grid_lat, grid_lon), data in grid_data.items():
            event_count = len(data['events'])

            if event_count >= min_events:  # Only include significant hotspots
                # Calculate center point
                center_lat = np.mean([loc['lat'] for loc in data['locations']])
                center_lon = np.mean([loc['lon'] for loc in data['locations']])

                # Calculate average risk
                avg_risk = data['total_risk'] / event_count if event_count > 0 else 0

                # Get vessel types
                vessel_types = defaultdict(int)
                for event in data['events']:
                    vessel_type = event.get('vessel_type', 'unknown')
                    vessel_types[vessel_type] += 1

                hotspots.append({
                    'grid_lat': grid_lat,
                    'grid_lon': grid_lon,
                    'center_lat': round(center_lat, 4),
                    'center_lon': round(center_lon, 4),
                    'event_count': event_count,
                    'unique_vessels': len(data['vessels']),
                    'total_risk_score': round(data['total_risk'], 3),
                    'avg_risk_score': round(avg_risk, 3),
                    'vessel_types': dict(vessel_types),
                    'intensity': self._calculate_intensity(event_count, len(data['vessels']), avg_risk),
                    'threat_level': self._classify_threat_level(event_count, len(data['vessels']), avg_risk)
                })

        # Sort by intensity
        hotspots.sort(key=lambda x: x['intensity'], reverse=True)

        logger.info(f"Found {len(hotspots)} hotspots with {min_events}+ events")

        return hotspots

    def find_temporal_hotspots(
        self,
        suspicious_events: pd.DataFrame,
        time_window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Find temporal patterns in hotspots (e.g., seasonal fishing).

        Args:
            suspicious_events: DataFrame with suspicious events
            time_window_days: Time window for aggregation

        Returns:
            List of temporal hotspot patterns
        """
        logger.info("Analyzing temporal hotspot patterns...")

        # Convert timestamps
        suspicious_events['timestamp'] = pd.to_datetime(suspicious_events['start_time'])
        suspicious_events['month'] = suspicious_events['timestamp'].dt.month
        suspicious_events['year'] = suspicious_events['timestamp'].dt.year

        # Group by time period
        temporal_patterns = []

        for (year, month), group in suspicious_events.groupby(['year', 'month']):
            if len(group) >= 2:  # At least 2 events in this period
                # Find geographic center
                center_lat = group['start_lat'].mean()
                center_lon = group['start_lon'].mean()

                temporal_patterns.append({
                    'year': int(year),
                    'month': int(month),
                    'event_count': len(group),
                    'unique_vessels': group['mmsi'].nunique(),
                    'center_lat': round(center_lat, 4),
                    'center_lon': round(center_lon, 4),
                    'avg_risk_score': round(group['risk_score'].mean(), 3),
                    'total_risk': round(group['risk_score'].sum(), 3)
                })

        # Sort by event count
        temporal_patterns.sort(key=lambda x: x['event_count'], reverse=True)

        logger.info(f"Found {len(temporal_patterns)} temporal patterns")

        return temporal_patterns

    def find_mpa_violations(
        self,
        suspicious_events: pd.DataFrame,
        mpa_data: pd.DataFrame = None
    ) -> List[Dict[str, Any]]:
        """
        Find hotspots specifically within or near Marine Protected Areas.

        Args:
            suspicious_events: DataFrame with suspicious events
            mpa_data: DataFrame with MPA boundaries

        Returns:
            List of MPA violation hotspots
        """
        if mpa_data is None or mpa_data.empty:
            logger.warning("No MPA data provided, skipping MPA violation analysis")
            return []

        logger.info("Finding MPA violation hotspots...")

        # Filter events that have MPA context
        mpa_violations = suspicious_events[
            suspicious_events.get('in_mpa', False) == True
        ].copy()

        if mpa_violations.empty:
            return []

        # Group by MPA name/ID
        mpa_hotspots = []

        for mpa_name, group in mpa_violations.groupby('mpa_name'):
            mpa_hotspots.append({
                'mpa_name': str(mpa_name),
                'event_count': len(group),
                'unique_vessels': group['mmsi'].nunique(),
                'avg_risk_score': round(group['risk_score'].mean(), 3),
                'total_risk': round(group['risk_score'].sum(), 3),
                'center_lat': round(group['start_lat'].mean(), 4),
                'center_lon': round(group['start_lon'].mean(), 4),
                'violation_severity': self._classify_mpa_severity(len(group), group['risk_score'].mean())
            })

        # Sort by total risk
        mpa_hotspots.sort(key=lambda x: x['total_risk'], reverse=True)

        logger.info(f"Found {len(mpa_hotspots)} MPA violation hotspots")

        return mpa_hotspots

    def _calculate_intensity(self, event_count: int, vessel_count: int, avg_risk: float) -> float:
        """Calculate hotspot intensity score."""
        # Weighted combination of factors
        return (event_count * 10) + (vessel_count * 5) + (avg_risk * 20)

    def _classify_threat_level(self, event_count: int, vessel_count: int, avg_risk: float) -> str:
        """Classify threat level of a hotspot."""
        intensity = self._calculate_intensity(event_count, vessel_count, avg_risk)

        if intensity > 100:
            return "CRITICAL"
        elif intensity > 50:
            return "HIGH"
        elif intensity > 20:
            return "MEDIUM"
        else:
            return "LOW"

    def _classify_mpa_severity(self, event_count: int, avg_risk: float) -> str:
        """Classify severity of MPA violations."""
        if event_count >= 10 or avg_risk > 0.7:
            return "SEVERE"
        elif event_count >= 5 or avg_risk > 0.5:
            return "SERIOUS"
        elif event_count >= 2 or avg_risk > 0.3:
            return "MODERATE"
        else:
            return "MINOR"

    def generate_heatmap_data(
        self,
        suspicious_events: pd.DataFrame,
        resolution: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Generate heatmap data for visualization.

        Args:
            suspicious_events: DataFrame with suspicious events
            resolution: Grid resolution in degrees

        Returns:
            List of grid cells with intensity values
        """
        grid_data = defaultdict(lambda: {'count': 0, 'total_risk': 0})

        for _, event in suspicious_events.iterrows():
            grid_lat = round(event['start_lat'] / resolution) * resolution
            grid_lon = round(event['start_lon'] / resolution) * resolution
            grid_key = (grid_lat, grid_lon)

            grid_data[grid_key]['count'] += 1
            grid_data[grid_key]['total_risk'] += event.get('risk_score', 0)

        # Convert to list format
        heatmap = []
        for (lat, lon), data in grid_data.items():
            heatmap.append({
                'lat': lat,
                'lon': lon,
                'count': data['count'],
                'risk_score': round(data['total_risk'] / data['count'], 3) if data['count'] > 0 else 0,
                'intensity': data['count'] * data['total_risk']
            })

        return heatmap
