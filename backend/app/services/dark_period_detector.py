import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from geopy.distance import geodesic
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

class DarkPeriodDetector:
    """Detects AIS dark periods and calculates risk scores"""

    def __init__(self):
        self.threshold_hours = settings.DARK_PERIOD_THRESHOLD_HOURS
        self.w_gap = settings.RISK_WEIGHT_GAP_DURATION
        self.w_dist = settings.RISK_WEIGHT_DISTANCE
        self.w_mpa = settings.RISK_WEIGHT_MPA
        self.w_night = settings.RISK_WEIGHT_NIGHTTIME

    def detect_dark_periods(self, ais_df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect dark periods in AIS data

        Args:
            ais_df: DataFrame with columns [mmsi, timestamp, lat, lon, speed, course]

        Returns:
            DataFrame of detected dark periods
        """
        dark_periods = []

        # Sort by vessel and time
        ais_df = ais_df.sort_values(['mmsi', 'timestamp'])

        # Group by vessel
        for mmsi, vessel_data in ais_df.groupby('mmsi'):
            vessel_data = vessel_data.sort_values('timestamp').reset_index(drop=True)

            if len(vessel_data) < 2:
                continue

            # Calculate time gaps
            vessel_data['time_diff'] = vessel_data['timestamp'].diff()

            # Find gaps exceeding threshold
            for idx in range(1, len(vessel_data)):
                time_gap = vessel_data.iloc[idx]['time_diff']

                if pd.isna(time_gap):
                    continue

                gap_hours = time_gap.total_seconds() / 3600

                if gap_hours >= self.threshold_hours:
                    start_row = vessel_data.iloc[idx - 1]
                    end_row = vessel_data.iloc[idx]

                    # Calculate distance traveled
                    start_pos = (start_row['lat'], start_row['lon'])
                    end_pos = (end_row['lat'], end_row['lon'])
                    distance_km = geodesic(start_pos, end_pos).kilometers

                    # Check if nighttime (simplified: between 6 PM and 6 AM UTC)
                    start_hour = start_row['timestamp'].hour
                    is_nighttime = start_hour >= 18 or start_hour <= 6

                    # Calculate risk score (will be enhanced with MPA data later)
                    risk_score = self._calculate_risk_score(
                        gap_hours=gap_hours,
                        distance_km=distance_km,
                        in_mpa=False,  # To be filled by spatial join
                        is_nighttime=is_nighttime
                    )

                    dark_period = {
                        'mmsi': mmsi,
                        'start_time': start_row['timestamp'],
                        'end_time': end_row['timestamp'],
                        'duration_hours': gap_hours,
                        'start_lat': start_row['lat'],
                        'start_lon': start_row['lon'],
                        'end_lat': end_row['lat'],
                        'end_lon': end_row['lon'],
                        'distance_km': distance_km,
                        'risk_score': risk_score,
                        'in_mpa': False,
                        'is_nighttime': is_nighttime
                    }

                    dark_periods.append(dark_period)

        return pd.DataFrame(dark_periods)

    def _calculate_risk_score(
        self,
        gap_hours: float,
        distance_km: float,
        in_mpa: bool,
        is_nighttime: bool
    ) -> float:
        """
        Calculate risk score for a dark period

        Risk factors:
        1. Gap duration (normalized by max expected gap)
        2. Distance traveled during gap / time (speed indicator)
        3. Occurred in Marine Protected Area
        4. Occurred at nighttime
        """
        # Normalize gap duration (0-1, cap at 24 hours)
        gap_score = min(gap_hours / 24.0, 1.0)

        # Normalize distance (suspicious if moving fast during silence)
        # Expected: <100km for 3-24 hour gap
        avg_speed_kmh = distance_km / gap_hours if gap_hours > 0 else 0
        # Suspicious if speed > 20 km/h (~10 knots) during silence
        distance_score = min(avg_speed_kmh / 20.0, 1.0)

        # MPA score (binary)
        mpa_score = 1.0 if in_mpa else 0.0

        # Nighttime score (binary)
        night_score = 1.0 if is_nighttime else 0.0

        # Weighted combination
        risk = (
            self.w_gap * gap_score +
            self.w_dist * distance_score +
            self.w_mpa * mpa_score +
            self.w_night * night_score
        )

        return round(risk, 3)

    def calculate_vessel_statistics(self, dark_periods_df: pd.DataFrame) -> Dict:
        """Calculate summary statistics per vessel"""
        if dark_periods_df.empty:
            return {}

        vessel_stats = []

        for mmsi, vessel_periods in dark_periods_df.groupby('mmsi'):
            stats = {
                'mmsi': mmsi,
                'total_dark_periods': len(vessel_periods),
                'total_dark_hours': vessel_periods['duration_hours'].sum(),
                'avg_risk_score': vessel_periods['risk_score'].mean(),
                'max_risk_score': vessel_periods['risk_score'].max(),
                'high_risk_events': len(vessel_periods[vessel_periods['risk_score'] > 0.7]),
                'last_seen': vessel_periods['end_time'].max()
            }
            vessel_stats.append(stats)

        return pd.DataFrame(vessel_stats).to_dict('records')

    def generate_heatmap_data(
        self,
        dark_periods_df: pd.DataFrame,
        grid_size: float = 0.5
    ) -> List[Dict]:
        """
        Generate heatmap grid data from dark periods

        Args:
            dark_periods_df: DataFrame of dark periods
            grid_size: Grid cell size in degrees (default 0.5°)

        Returns:
            List of heatmap points with aggregated risk
        """
        if dark_periods_df.empty:
            return []

        # Use end positions (where vessel reappeared)
        dark_periods_df['lat_grid'] = (dark_periods_df['end_lat'] / grid_size).round() * grid_size
        dark_periods_df['lon_grid'] = (dark_periods_df['end_lon'] / grid_size).round() * grid_size

        # Aggregate by grid cell
        heatmap = dark_periods_df.groupby(['lat_grid', 'lon_grid']).agg({
            'risk_score': 'mean',
            'mmsi': 'count'
        }).reset_index()

        heatmap.columns = ['lat', 'lon', 'risk_score', 'count']

        return heatmap.to_dict('records')
