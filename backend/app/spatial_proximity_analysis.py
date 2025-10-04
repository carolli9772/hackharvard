"""
Spatial Proximity Analysis Script
Identifies vessels in proximity to dark events for pattern detection.
"""

import pandas as pd
from scipy.spatial import cKDTree
from data_preprocessing import load_ais_data, preprocess_ais_data
from dark_event_detection import detect_dark_events


def find_nearby_vessels(df, dark_events, spatial_threshold_km=5, temporal_window_minutes=10):
    """
    Find vessels within spatial and temporal proximity of dark events.

    Args:
        df (pd.DataFrame): Preprocessed AIS data
        dark_events (pd.DataFrame): Detected dark events
        spatial_threshold_km (float): Spatial proximity threshold in kilometers
        temporal_window_minutes (int): Temporal window in minutes before/after gap

    Returns:
        pd.DataFrame: Nearby vessel information for each dark event
    """
    # Convert kilometers to degrees (approximate)
    degree_per_km = 1 / 111.0
    spatial_threshold_degrees = spatial_threshold_km * degree_per_km

    # Convert temporal window to timedelta
    temporal_window_timedelta = pd.Timedelta(minutes=temporal_window_minutes)

    # Prepare spatial data
    df_spatial = df.dropna(subset=['LAT', 'LON']).copy()

    # Build spatial index
    print(f"Building spatial index with {len(df_spatial)} records...")
    spatial_index = cKDTree(df_spatial[['LAT', 'LON']])

    # Store nearby vessel information
    nearby_vessels_list = []

    print(f"\nAnalyzing {len(dark_events)} dark events...")

    # Process each dark event
    for idx, dark_event in dark_events.iterrows():
        if idx % 1000 == 0:
            print(f"  Processed {idx}/{len(dark_events)} dark events...")

        mmsi = dark_event['MMSI']
        gap_start_time = dark_event['GapStartTime']
        gap_duration = dark_event['GapDuration']
        gap_end_time = gap_start_time + gap_duration

        # Define temporal windows
        before_gap_start = gap_start_time - temporal_window_timedelta
        after_gap_end = gap_end_time + temporal_window_timedelta

        # Get last known position of the vessel before the gap
        last_pos = df_spatial[
            (df_spatial['MMSI'] == mmsi) &
            (df_spatial['BaseDateTime'] <= gap_start_time)
        ].sort_values(by='BaseDateTime', ascending=False).head(1)

        if last_pos.empty:
            continue

        last_lat = last_pos['LAT'].iloc[0]
        last_lon = last_pos['LON'].iloc[0]

        # Find nearby positions in spatial index
        indices_nearby = spatial_index.query_ball_point(
            [last_lat, last_lon],
            spatial_threshold_degrees
        )

        # Get nearby vessel records
        nearby_records = df_spatial.iloc[indices_nearby]

        # Filter by temporal window and exclude the vessel itself
        nearby_in_window = nearby_records[
            ((nearby_records['BaseDateTime'] >= before_gap_start) &
             (nearby_records['BaseDateTime'] < gap_start_time)) |
            ((nearby_records['BaseDateTime'] > gap_end_time) &
             (nearby_records['BaseDateTime'] <= after_gap_end))
        ]
        nearby_in_window = nearby_in_window[nearby_in_window['MMSI'] != mmsi]

        # Store information about nearby vessels
        for _, nearby_row in nearby_in_window.iterrows():
            nearby_vessels_list.append({
                'DarkEvent_MMSI': mmsi,
                'GapStartTime': gap_start_time,
                'GapDuration': gap_duration,
                'NearbyVessel_MMSI': nearby_row['MMSI'],
                'NearbyVessel_Name': nearby_row.get('VesselName', 'Unknown'),
                'NearbyVessel_Type': nearby_row.get('VesselType', 'Unknown'),
                'NearbyVessel_BaseDateTime': nearby_row['BaseDateTime'],
                'NearbyVessel_LAT': nearby_row['LAT'],
                'NearbyVessel_LON': nearby_row['LON']
            })

    # Convert to DataFrame
    df_nearby = pd.DataFrame(nearby_vessels_list)

    print(f"\nFound {len(df_nearby)} nearby vessel observations")
    print(f"  {df_nearby['DarkEvent_MMSI'].nunique()} dark events have at least one nearby vessel")

    return df_nearby


def analyze_proximity_patterns(df_nearby):
    """
    Analyze patterns in nearby vessel observations.

    Args:
        df_nearby (pd.DataFrame): Nearby vessel data

    Returns:
        dict: Analysis results
    """
    # Count nearby vessels per dark event
    nearby_counts = df_nearby.groupby('DarkEvent_MMSI')['NearbyVessel_MMSI'].nunique().reset_index()
    nearby_counts.rename(columns={'NearbyVessel_MMSI': 'UniqueNearbyVessels'}, inplace=True)

    # Count repeated observations of same vessel
    observation_counts = df_nearby.groupby(['DarkEvent_MMSI', 'NearbyVessel_MMSI']).size().reset_index(name='ObservationCount')
    repeated_observations = observation_counts[observation_counts['ObservationCount'] > 1]

    analysis = {
        'total_nearby_observations': len(df_nearby),
        'dark_events_with_nearby': df_nearby['DarkEvent_MMSI'].nunique(),
        'dark_events_multiple_nearby': len(nearby_counts[nearby_counts['UniqueNearbyVessels'] > 1]),
        'dark_events_repeated_nearby': repeated_observations['DarkEvent_MMSI'].nunique(),
        'avg_nearby_per_event': nearby_counts['UniqueNearbyVessels'].mean()
    }

    print("\nProximity Pattern Analysis:")
    print(f"  Total nearby vessel observations: {analysis['total_nearby_observations']}")
    print(f"  Dark events with at least one nearby vessel: {analysis['dark_events_with_nearby']}")
    print(f"  Dark events with multiple nearby vessels: {analysis['dark_events_multiple_nearby']}")
    print(f"  Dark events with repeated nearby vessel observations: {analysis['dark_events_repeated_nearby']}")
    print(f"  Average nearby vessels per dark event: {analysis['avg_nearby_per_event']:.2f}")

    return analysis, nearby_counts


def main():
    """Main function to demonstrate spatial proximity analysis."""
    # Load and preprocess data
    file_path = '../../datasets/AIS_2024_01_01.csv'
    df = load_ais_data(file_path)
    df_clean = preprocess_ais_data(df)

    # Detect dark events
    dark_events = detect_dark_events(df_clean, threshold_minutes=10)

    # Find nearby vessels
    df_nearby = find_nearby_vessels(
        df_clean,
        dark_events,
        spatial_threshold_km=5,
        temporal_window_minutes=10
    )

    # Analyze patterns
    analysis, nearby_counts = analyze_proximity_patterns(df_nearby)

    # Save results
    df_nearby.to_csv('nearby_vessels.csv', index=False)
    nearby_counts.to_csv('nearby_vessel_counts.csv', index=False)
    print("\nResults saved to nearby_vessels.csv and nearby_vessel_counts.csv")

    return df_nearby, analysis


if __name__ == "__main__":
    main()
