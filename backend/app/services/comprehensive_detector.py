"""
Comprehensive illegal fishing detection using multiple data sources
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict
from geopy.distance import geodesic
from shapely.geometry import Point
import logging

logger = logging.getLogger(__name__)

class ComprehensiveIllegalFishingDetector:
    """
    Advanced detector that combines multiple signals:
    1. AIS dark periods (going silent)
    2. Marine Protected Area violations
    3. Speed anomalies
    4. Fishing activity patterns
    5. Time-between-signals analysis
    """

    def __init__(self, mpa_data: pd.DataFrame = None):
        self.mpa_data = mpa_data
        self.dark_period_threshold_hours = 3.0
        self.min_suspicious_speed = 2.0  # knots - suspiciously slow (possible fishing)
        self.max_suspicious_speed = 15.0  # knots - suspiciously fast (fleeing)

    def detect_illegal_activity(self, fishing_data: pd.DataFrame) -> pd.DataFrame:
        """
        Main detection pipeline - analyzes all risk factors

        Returns DataFrame with suspicious events and comprehensive risk scores
        """
        logger.info(f"Running comprehensive illegal fishing detection on {len(fishing_data)} records")

        suspicious_events = []

        # Sort by vessel and time
        fishing_data = fishing_data.sort_values(['mmsi', 'timestamp'])

        # Analyze each vessel
        for mmsi, vessel_data in fishing_data.groupby('mmsi'):
            vessel_data = vessel_data.sort_values('timestamp').reset_index(drop=True)

            if len(vessel_data) < 2:
                continue

            # Calculate time differences
            vessel_data['time_diff_hours'] = vessel_data['timestamp'].diff().dt.total_seconds() / 3600

            # Analyze each trajectory segment
            for idx in range(1, len(vessel_data)):
                prev_row = vessel_data.iloc[idx - 1]
                curr_row = vessel_data.iloc[idx]

                time_gap_hours = curr_row['time_diff_hours']

                if pd.isna(time_gap_hours):
                    continue

                # Calculate risk factors
                risk_factors = self._calculate_comprehensive_risk(
                    prev_row=prev_row,
                    curr_row=curr_row,
                    time_gap_hours=time_gap_hours,
                    vessel_type=vessel_data.iloc[0].get('vessel_type', 'unknown')
                )

                # Only flag if overall risk is significant
                if risk_factors['total_risk_score'] >= 0.3:
                    event = {
                        'mmsi': mmsi,
                        'start_time': prev_row['timestamp'],
                        'end_time': curr_row['timestamp'],
                        'start_lat': prev_row['lat'],
                        'start_lon': prev_row['lon'],
                        'end_lat': curr_row['lat'],
                        'end_lon': curr_row['lon'],
                        'vessel_type': vessel_data.iloc[0].get('vessel_type', 'unknown'),
                        **risk_factors
                    }
                    suspicious_events.append(event)

        if not suspicious_events:
            logger.warning("No suspicious events detected")
            return pd.DataFrame()

        result_df = pd.DataFrame(suspicious_events)
        logger.info(f"✓ Detected {len(result_df)} suspicious events")
        logger.info(f"  - High risk (>0.7): {len(result_df[result_df['total_risk_score'] > 0.7])}")
        logger.info(f"  - Medium risk (0.5-0.7): {len(result_df[result_df['total_risk_score'].between(0.5, 0.7)])}")
        logger.info(f"  - Low risk (0.3-0.5): {len(result_df[result_df['total_risk_score'].between(0.3, 0.5)])}")

        return result_df

    def _calculate_comprehensive_risk(
        self,
        prev_row: pd.Series,
        curr_row: pd.Series,
        time_gap_hours: float,
        vessel_type: str
    ) -> Dict:
        """Calculate risk score using ALL available signals"""

        # 1. DARK PERIOD RISK (AIS silence)
        dark_period_risk = 0.0
        if time_gap_hours >= self.dark_period_threshold_hours:
            # Normalize: 3-24 hours gap
            dark_period_risk = min(time_gap_hours / 24.0, 1.0)

        # 2. SPEED ANOMALY RISK
        speed_risk = 0.0
        curr_speed = curr_row.get('speed', 0)
        prev_speed = prev_row.get('speed', 0)

        # Suspiciously slow (possible illegal fishing)
        if curr_speed < self.min_suspicious_speed and curr_speed > 0:
            speed_risk = 0.6
        # Suspiciously fast (possible fleeing)
        elif curr_speed > self.max_suspicious_speed:
            speed_risk = 0.4
        # Sudden speed changes
        if abs(curr_speed - prev_speed) > 10:
            speed_risk = max(speed_risk, 0.5)

        # 3. MARINE PROTECTED AREA VIOLATION
        mpa_risk = 0.0
        in_mpa = False
        if self.mpa_data is not None and not self.mpa_data.empty:
            # Check if vessel is in MPA (simplified - would use actual geometry)
            in_mpa = self._check_mpa_violation(curr_row['lat'], curr_row['lon'])
            if in_mpa:
                mpa_risk = 0.8  # High risk if in protected area

        # 4. FISHING ACTIVITY INDICATOR
        fishing_risk = 0.0
        is_fishing = curr_row.get('is_fishing', -1)
        if is_fishing == 1:  # Actively fishing
            fishing_risk = 0.3  # Baseline for fishing
            if in_mpa:
                fishing_risk = 1.0  # Max risk: fishing in MPA!

        # 5. DISTANCE TRAVELED DURING GAP
        distance_risk = 0.0
        if time_gap_hours > 0:
            start_pos = (prev_row['lat'], prev_row['lon'])
            end_pos = (curr_row['lat'], curr_row['lon'])
            distance_km = geodesic(start_pos, end_pos).kilometers

            # Suspicious if moving fast during AIS silence
            avg_speed_kmh = distance_km / time_gap_hours
            if avg_speed_kmh > 20:  # ~10 knots while silent
                distance_risk = min(avg_speed_kmh / 40.0, 1.0)

        # 6. NIGHTTIME OPERATION
        nighttime_risk = 0.0
        curr_hour = curr_row['timestamp'].hour
        is_nighttime = curr_hour >= 20 or curr_hour <= 5
        if is_nighttime:
            nighttime_risk = 0.2
            if is_fishing == 1:
                nighttime_risk = 0.5  # More suspicious if fishing at night

        # 7. DISTANCE FROM SHORE
        shore_risk = 0.0
        distance_from_shore = curr_row.get('distance_from_shore', 0)
        if distance_from_shore > 100000:  # >100km from shore
            shore_risk = 0.3  # Suspicious if very far from shore

        # WEIGHTED COMBINATION
        weights = {
            'dark_period': 0.25,
            'mpa_violation': 0.30,  # Highest weight
            'fishing_activity': 0.20,
            'speed_anomaly': 0.10,
            'distance_traveled': 0.08,
            'nighttime': 0.04,
            'shore_distance': 0.03
        }

        total_risk = (
            weights['dark_period'] * dark_period_risk +
            weights['mpa_violation'] * mpa_risk +
            weights['fishing_activity'] * fishing_risk +
            weights['speed_anomaly'] * speed_risk +
            weights['distance_traveled'] * distance_risk +
            weights['nighttime'] * nighttime_risk +
            weights['shore_distance'] * shore_risk
        )

        return {
            'total_risk_score': round(total_risk, 3),
            'dark_period_hours': time_gap_hours if time_gap_hours >= self.dark_period_threshold_hours else 0,
            'dark_period_risk': round(dark_period_risk, 3),
            'mpa_violation': in_mpa,
            'mpa_risk': round(mpa_risk, 3),
            'fishing_detected': bool(is_fishing == 1),
            'fishing_risk': round(fishing_risk, 3),
            'speed_anomaly_risk': round(speed_risk, 3),
            'distance_risk': round(distance_risk, 3),
            'nighttime_operation': is_nighttime,
            'nighttime_risk': round(nighttime_risk, 3),
            'distance_from_shore_km': distance_from_shore / 1000 if distance_from_shore else 0,
            'shore_distance_risk': round(shore_risk, 3),
            'current_speed_knots': curr_speed,
            'violation_type': self._classify_violation(
                in_mpa, is_fishing, dark_period_risk > 0, speed_risk > 0
            )
        }

    def _check_mpa_violation(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within a Marine Protected Area"""
        # Simplified check - in production would use actual geometry
        # For now, we'll flag if MPA data exists and coordinates are valid
        if self.mpa_data is None or self.mpa_data.empty:
            return False

        # TODO: Implement actual spatial join with MPA polygons
        # For demo, we'll do a simple proximity check to known MPA locations
        return False  # Placeholder

    def _classify_violation(
        self,
        in_mpa: bool,
        is_fishing: bool,
        has_dark_period: bool,
        has_speed_anomaly: bool
    ) -> str:
        """Classify the type of violation"""
        if in_mpa and is_fishing:
            return "ILLEGAL_FISHING_IN_MPA"
        elif in_mpa:
            return "MPA_INTRUSION"
        elif has_dark_period and is_fishing:
            return "FISHING_WITH_AIS_OFF"
        elif has_dark_period:
            return "SUSPICIOUS_AIS_SILENCE"
        elif has_speed_anomaly and is_fishing:
            return "SUSPICIOUS_FISHING_BEHAVIOR"
        else:
            return "GENERAL_SUSPICIOUS_ACTIVITY"

    def calculate_vessel_risk_profile(self, suspicious_events: pd.DataFrame) -> pd.DataFrame:
        """Calculate overall risk profile per vessel"""
        if suspicious_events.empty:
            return pd.DataFrame()

        vessel_profiles = []

        for mmsi, events in suspicious_events.groupby('mmsi'):
            profile = {
                'mmsi': mmsi,
                'vessel_type': events.iloc[0]['vessel_type'],
                'total_suspicious_events': len(events),
                'avg_risk_score': events['total_risk_score'].mean(),
                'max_risk_score': events['total_risk_score'].max(),
                'high_risk_events': len(events[events['total_risk_score'] > 0.7]),
                'mpa_violations': events['mpa_violation'].sum(),
                'fishing_while_dark': len(events[(events['dark_period_hours'] > 0) & events['fishing_detected']]),
                'total_dark_hours': events['dark_period_hours'].sum(),
                'nighttime_operations': events['nighttime_operation'].sum(),
                'last_violation_time': events['end_time'].max(),
                'last_lat': events.iloc[-1]['end_lat'],
                'last_lon': events.iloc[-1]['end_lon'],
                'primary_violation_type': events['violation_type'].mode()[0] if len(events) > 0 else 'UNKNOWN'
            }
            vessel_profiles.append(profile)

        return pd.DataFrame(vessel_profiles).sort_values('avg_risk_score', ascending=False)
