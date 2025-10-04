"""
Enhanced Dark Event Detection with Region and Location Metadata
Detects dark periods and enriches them with geographical context.
"""

import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely import wkt
import json


def load_protected_areas(file_path='../../datasets/WDPA_WDOECM_Oct2025_Public_marine_csv.csv'):
    """Load marine protected areas data."""
    try:
        # Read only necessary columns to save memory
        df = pd.read_csv(file_path, usecols=['WDPAID', 'NAME', 'DESIG_ENG', 'REP_AREA', 'GIS_AREA'])
        print(f"Loaded {len(df)} protected areas")
        return df
    except Exception as e:
        print(f"Warning: Could not load protected areas: {e}")
        return pd.DataFrame()


def load_fishing_gear_data():
    """Load all fishing gear datasets."""
    gear_types = {
        'drifting_longlines': '../../datasets/drifting_longlines.csv',
        'fixed_gear': '../../datasets/fixed_gear.csv',
        'pole_and_line': '../../datasets/pole_and_line.csv',
        'purse_seines': '../../datasets/purse_seines.csv',
        'trawlers': '../../datasets/trawlers.csv',
        'trollers': '../../datasets/trollers.csv'
    }

    fishing_data = {}
    for gear_type, path in gear_types.items():
        try:
            df = pd.read_csv(path)
            fishing_data[gear_type] = df
            print(f"Loaded {len(df)} vessels with {gear_type}")
        except Exception as e:
            print(f"Warning: Could not load {gear_type}: {e}")
            fishing_data[gear_type] = pd.DataFrame()

    return fishing_data


def classify_region(lat, lon):
    """
    Classify the region type based on coordinates.
    Simplified EEZ detection based on distance from coast.
    """
    # Simplified logic - in production, use actual EEZ boundaries
    # EEZ typically extends 200 nautical miles from coast

    # Check if near major fishing zones
    if -90 <= lat <= -30:
        return "Southern Ocean"
    elif 30 <= lat <= 70:
        return "Northern Pacific/Atlantic"
    elif -30 <= lat <= 30:
        if -180 <= lon <= -80:
            return "Eastern Pacific"
        elif -80 <= lon <= 20:
            return "Atlantic"
        elif 20 <= lon <= 180:
            return "Indo-Pacific"

    # Check proximity to EEZ edges (simplified - coastal proximity)
    # In production, use actual EEZ polygon boundaries
    if abs(lat) > 60:
        return "High Latitude Zone"

    return "Open Ocean"


def detect_enhanced_dark_events(df, threshold_minutes=10):
    """
    Detect dark events with enhanced metadata including region and location.

    Returns events in the format:
    {
        "mmsi": 231982000,
        "start": "2025-09-02T03:00Z",
        "end": "2025-09-02T05:30Z",
        "region": "EEZ edge",
        "location": [15.2, -88.0],
        "duration_hours": 2.5,
        "vessel_name": "...",
        "vessel_type": "..."
    }
    """
    # Ensure data is sorted
    df = df.sort_values(by=['MMSI', 'BaseDateTime'])

    # Calculate time gaps
    df['TimeDifference'] = df.groupby('MMSI')['BaseDateTime'].diff()

    # Filter dark events
    dark_threshold = pd.Timedelta(minutes=threshold_minutes)
    dark_events_df = df[df['TimeDifference'] > dark_threshold].copy()

    # Build enhanced event records
    enhanced_events = []

    for _, row in dark_events_df.iterrows():
        # Get previous position (start of dark period)
        prev_record = df[(df['MMSI'] == row['MMSI']) &
                         (df['BaseDateTime'] < row['BaseDateTime'])].tail(1)

        if not prev_record.empty:
            start_time = prev_record['BaseDateTime'].iloc[0]
            start_lat = prev_record['LAT'].iloc[0]
            start_lon = prev_record['LON'].iloc[0]

            end_time = row['BaseDateTime']
            end_lat = row['LAT']
            end_lon = row['LON']

            # Calculate midpoint location
            mid_lat = (start_lat + end_lat) / 2
            mid_lon = (start_lon + end_lon) / 2

            # Classify region
            region = classify_region(mid_lat, mid_lon)

            # Calculate duration
            duration_hours = (end_time - start_time).total_seconds() / 3600

            event = {
                "mmsi": int(row['MMSI']),
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "region": region,
                "location": [float(mid_lat), float(mid_lon)],
                "start_location": [float(start_lat), float(start_lon)],
                "end_location": [float(end_lat), float(end_lon)],
                "duration_hours": round(duration_hours, 2),
                "vessel_name": str(row.get('VesselName', 'Unknown')),
                "vessel_type": float(row.get('VesselType', 0)) if pd.notna(row.get('VesselType')) else None,
                "vessel_length": float(row.get('Length', 0)) if pd.notna(row.get('Length')) else None
            }

            enhanced_events.append(event)

    print(f"\nDetected {len(enhanced_events)} dark events with enhanced metadata")

    return enhanced_events


def enrich_with_fishing_gear(dark_events, fishing_data):
    """Enrich dark events with fishing gear type if vessel is in fishing fleet."""
    mmsi_to_gear = {}

    for gear_type, df in fishing_data.items():
        if not df.empty and 'mmsi' in df.columns:
            for mmsi in df['mmsi'].unique():
                if mmsi not in mmsi_to_gear:
                    mmsi_to_gear[mmsi] = []
                mmsi_to_gear[mmsi].append(gear_type)

    # Add gear type to events
    for event in dark_events:
        mmsi = event['mmsi']
        if mmsi in mmsi_to_gear:
            event['fishing_gear_types'] = mmsi_to_gear[mmsi]
            event['is_fishing_vessel'] = True
        else:
            event['fishing_gear_types'] = []
            event['is_fishing_vessel'] = False

    fishing_count = sum(1 for e in dark_events if e['is_fishing_vessel'])
    print(f"Identified {fishing_count} dark events from known fishing vessels")

    return dark_events


def save_enhanced_events(events, output_path='enhanced_dark_events.json'):
    """Save enhanced events to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} enhanced dark events to {output_path}")


def main():
    """Main function to detect and enrich dark events."""
    from data_preprocessing import load_ais_data, preprocess_ais_data

    # Load AIS data
    file_path = '../../datasets/AIS_2024_01_01.csv'
    df = load_ais_data(file_path)
    df_clean = preprocess_ais_data(df)

    # Load fishing gear data
    fishing_data = load_fishing_gear_data()

    # Detect enhanced dark events
    dark_events = detect_enhanced_dark_events(df_clean, threshold_minutes=10)

    # Enrich with fishing gear information
    dark_events = enrich_with_fishing_gear(dark_events, fishing_data)

    # Save to JSON
    save_enhanced_events(dark_events)

    # Print sample events
    print("\nSample enhanced dark events:")
    for event in dark_events[:3]:
        print(json.dumps(event, indent=2))

    return dark_events


if __name__ == "__main__":
    main()
