"""
Vessel Proximity Index System
Builds a "who was near whom and when" dataset using spatial indexing.
"""

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
from datetime import datetime, timedelta
import json
import pickle


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate haversine distance between two points in kilometers.
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    # Earth radius in kilometers
    r = 6371

    return c * r


def build_proximity_index(df, time_window_minutes=10, distance_threshold_km=20):
    """
    Build a vessel proximity index for all AIS points.

    Args:
        df: AIS DataFrame with MMSI, BaseDateTime, LAT, LON
        time_window_minutes: Time window for proximity detection
        distance_threshold_km: Distance threshold in kilometers

    Returns:
        List of proximity events with vessel pairs and spatiotemporal details
    """
    print(f"Building proximity index with {len(df)} AIS records...")
    print(f"Time window: {time_window_minutes} minutes, Distance threshold: {distance_threshold_km} km")

    # Sort by time
    df = df.sort_values('BaseDateTime').reset_index(drop=True)

    # Create time bins
    time_window = pd.Timedelta(minutes=time_window_minutes)
    df['TimeBin'] = df['BaseDateTime'].dt.floor(f'{time_window_minutes}min')

    proximity_events = []

    # Process each time bin
    time_bins = df['TimeBin'].unique()
    print(f"Processing {len(time_bins)} time bins...")

    for i, time_bin in enumerate(time_bins):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(time_bins)} time bins...")

        # Get all records in this time bin
        bin_data = df[df['TimeBin'] == time_bin].copy()

        if len(bin_data) < 2:
            continue

        # Convert to radians for BallTree
        coords_rad = np.radians(bin_data[['LAT', 'LON']].values)

        # Build BallTree for this time bin
        tree = BallTree(coords_rad, metric='haversine')

        # Find pairs within distance threshold
        # Convert km to radians (Earth radius = 6371 km)
        radius_rad = distance_threshold_km / 6371.0

        # Query all points
        indices_list = tree.query_radius(coords_rad, r=radius_rad)

        # Process pairs
        for idx, nearby_indices in enumerate(indices_list):
            vessel1_idx = bin_data.index[idx]
            vessel1 = bin_data.loc[vessel1_idx]

            for nearby_idx in nearby_indices:
                vessel2_idx = bin_data.index[nearby_idx]
                vessel2 = bin_data.loc[vessel2_idx]

                # Skip self-pairs and duplicate pairs
                if vessel1['MMSI'] >= vessel2['MMSI']:
                    continue

                # Calculate actual distance
                distance = haversine_distance(
                    vessel1['LAT'], vessel1['LON'],
                    vessel2['LAT'], vessel2['LON']
                )

                if distance <= distance_threshold_km:
                    proximity_events.append({
                        'time_bin': time_bin.isoformat(),
                        'vessel1_mmsi': int(vessel1['MMSI']),
                        'vessel2_mmsi': int(vessel2['MMSI']),
                        'vessel1_name': str(vessel1.get('VesselName', 'Unknown')),
                        'vessel2_name': str(vessel2.get('VesselName', 'Unknown')),
                        'vessel1_location': [float(vessel1['LAT']), float(vessel1['LON'])],
                        'vessel2_location': [float(vessel2['LAT']), float(vessel2['LON'])],
                        'distance_km': round(distance, 2),
                        'vessel1_type': float(vessel1.get('VesselType', 0)) if pd.notna(vessel1.get('VesselType')) else None,
                        'vessel2_type': float(vessel2.get('VesselType', 0)) if pd.notna(vessel2.get('VesselType')) else None
                    })

    print(f"\nFound {len(proximity_events)} proximity events")

    return proximity_events


def aggregate_proximity_stats(proximity_events):
    """
    Aggregate proximity events into statistics.

    Returns:
        DataFrame with vessel pair statistics
    """
    if not proximity_events:
        return pd.DataFrame()

    df = pd.DataFrame(proximity_events)

    # Count encounters per vessel pair
    pair_stats = df.groupby(['vessel1_mmsi', 'vessel2_mmsi']).agg({
        'time_bin': 'count',
        'distance_km': 'mean'
    }).reset_index()

    pair_stats.rename(columns={
        'time_bin': 'encounter_count',
        'distance_km': 'avg_distance_km'
    }, inplace=True)

    pair_stats = pair_stats.sort_values('encounter_count', ascending=False)

    print("\nTop vessel pairs by encounter count:")
    print(pair_stats.head(10))

    return pair_stats


def get_vessels_near_location(proximity_events, target_location, target_time,
                               radius_km=20, time_window_minutes=15):
    """
    Get all vessels near a specific location and time.

    Args:
        proximity_events: List of proximity events
        target_location: [lat, lon]
        target_time: datetime object or ISO string
        radius_km: Search radius in kilometers
        time_window_minutes: Time window in minutes

    Returns:
        List of vessels near the target
    """
    if isinstance(target_time, str):
        target_time = pd.to_datetime(target_time)

    target_lat, target_lon = target_location
    time_delta = pd.Timedelta(minutes=time_window_minutes)

    nearby_vessels = []

    for event in proximity_events:
        event_time = pd.to_datetime(event['time_bin'])

        # Check time window
        if abs(event_time - target_time) > time_delta:
            continue

        # Check vessel 1
        dist1 = haversine_distance(
            target_lat, target_lon,
            event['vessel1_location'][0], event['vessel1_location'][1]
        )
        if dist1 <= radius_km:
            nearby_vessels.append({
                'mmsi': event['vessel1_mmsi'],
                'name': event['vessel1_name'],
                'location': event['vessel1_location'],
                'distance_km': round(dist1, 2),
                'time': event['time_bin'],
                'vessel_type': event['vessel1_type']
            })

        # Check vessel 2
        dist2 = haversine_distance(
            target_lat, target_lon,
            event['vessel2_location'][0], event['vessel2_location'][1]
        )
        if dist2 <= radius_km:
            nearby_vessels.append({
                'mmsi': event['vessel2_mmsi'],
                'name': event['vessel2_name'],
                'location': event['vessel2_location'],
                'distance_km': round(dist2, 2),
                'time': event['time_bin'],
                'vessel_type': event['vessel2_type']
            })

    # Remove duplicates
    seen = set()
    unique_vessels = []
    for v in nearby_vessels:
        key = (v['mmsi'], v['time'])
        if key not in seen:
            seen.add(key)
            unique_vessels.append(v)

    return unique_vessels


def save_proximity_index(proximity_events, output_path='proximity_index.json'):
    """Save proximity index to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(proximity_events, f, indent=2)
    print(f"Saved proximity index to {output_path}")


def main():
    """Main function to build proximity index."""
    from data_preprocessing import load_ais_data, preprocess_ais_data

    # Load AIS data
    file_path = '../../datasets/AIS_2024_01_01.csv'
    df = load_ais_data(file_path)
    df_clean = preprocess_ais_data(df)

    # Build proximity index
    proximity_events = build_proximity_index(
        df_clean,
        time_window_minutes=10,
        distance_threshold_km=20
    )

    # Aggregate statistics
    pair_stats = aggregate_proximity_stats(proximity_events)

    # Save results
    save_proximity_index(proximity_events)
    pair_stats.to_csv('vessel_pair_stats.csv', index=False)
    print("Saved vessel pair statistics to vessel_pair_stats.csv")

    # Example: Find vessels near a specific location and time
    if proximity_events:
        example_event = proximity_events[0]
        nearby = get_vessels_near_location(
            proximity_events,
            example_event['vessel1_location'],
            example_event['time_bin'],
            radius_km=20,
            time_window_minutes=15
        )
        print(f"\nExample: Found {len(nearby)} vessels near location {example_event['vessel1_location']}")

    return proximity_events, pair_stats


if __name__ == "__main__":
    main()
