"""
Pattern Analysis and Suspicious Event Flagging Script
Flags dark events as suspicious based on spatiotemporal patterns.
"""

import pandas as pd
from data_preprocessing import load_ais_data, preprocess_ais_data
from dark_event_detection import detect_dark_events
from spatial_proximity_analysis import find_nearby_vessels


def flag_suspicious_events(dark_events, df_nearby, min_nearby_vessels=1, min_repeated_observations=0):
    """
    Flag dark events as suspicious based on proximity patterns.

    Args:
        dark_events (pd.DataFrame): Detected dark events
        df_nearby (pd.DataFrame): Nearby vessel observations
        min_nearby_vessels (int): Minimum nearby vessels to flag as suspicious
        min_repeated_observations (int): Minimum repeated observations threshold

    Returns:
        pd.DataFrame: Dark events with suspicious flag
    """
    # Count unique nearby vessels per dark event
    nearby_counts = df_nearby.groupby('DarkEvent_MMSI')['NearbyVessel_MMSI'].nunique().reset_index()
    nearby_counts.rename(columns={'NearbyVessel_MMSI': 'UniqueNearbyVessels'}, inplace=True)

    # Count repeated observations
    observation_counts = df_nearby.groupby(['DarkEvent_MMSI', 'NearbyVessel_MMSI']).size().reset_index(name='ObservationCount')
    repeated_obs = observation_counts[observation_counts['ObservationCount'] > min_repeated_observations]
    repeated_counts = repeated_obs.groupby('DarkEvent_MMSI').size().reset_index(name='RepeatedNearbyVessels')

    # Merge with dark events
    dark_events_flagged = dark_events.copy()

    # Add nearby vessel counts
    dark_events_flagged = dark_events_flagged.merge(
        nearby_counts, left_on='MMSI', right_on='DarkEvent_MMSI', how='left'
    )
    dark_events_flagged['UniqueNearbyVessels'].fillna(0, inplace=True)

    # Add repeated observation counts
    dark_events_flagged = dark_events_flagged.merge(
        repeated_counts, left_on='MMSI', right_on='DarkEvent_MMSI', how='left'
    )
    dark_events_flagged['RepeatedNearbyVessels'].fillna(0, inplace=True)

    # Clean up merge columns
    if 'DarkEvent_MMSI_x' in dark_events_flagged.columns:
        dark_events_flagged.drop(['DarkEvent_MMSI_x', 'DarkEvent_MMSI_y'], axis=1, inplace=True)

    # Flag as suspicious based on criteria
    dark_events_flagged['is_suspicious'] = (
        dark_events_flagged['UniqueNearbyVessels'] >= min_nearby_vessels
    )

    # Calculate suspicion score (0-100)
    dark_events_flagged['suspicion_score'] = 0

    # Score based on nearby vessels (0-40 points)
    dark_events_flagged.loc[dark_events_flagged['UniqueNearbyVessels'] > 0, 'suspicion_score'] += 20
    dark_events_flagged.loc[dark_events_flagged['UniqueNearbyVessels'] > 2, 'suspicion_score'] += 10
    dark_events_flagged.loc[dark_events_flagged['UniqueNearbyVessels'] > 5, 'suspicion_score'] += 10

    # Score based on repeated observations (0-30 points)
    dark_events_flagged.loc[dark_events_flagged['RepeatedNearbyVessels'] > 0, 'suspicion_score'] += 15
    dark_events_flagged.loc[dark_events_flagged['RepeatedNearbyVessels'] > 2, 'suspicion_score'] += 15

    # Score based on gap duration (0-30 points)
    gap_duration_hours = dark_events_flagged['GapDuration'].dt.total_seconds() / 3600
    dark_events_flagged.loc[gap_duration_hours > 0.5, 'suspicion_score'] += 10
    dark_events_flagged.loc[gap_duration_hours > 1.0, 'suspicion_score'] += 10
    dark_events_flagged.loc[gap_duration_hours > 2.0, 'suspicion_score'] += 10

    # Summary statistics
    suspicious_count = dark_events_flagged['is_suspicious'].sum()
    total_count = len(dark_events_flagged)

    print(f"\nSuspicious Event Flagging Results:")
    print(f"  Total dark events: {total_count}")
    print(f"  Flagged as suspicious: {suspicious_count} ({100*suspicious_count/total_count:.1f}%)")
    print(f"\nSuspicion score distribution:")
    print(dark_events_flagged['suspicion_score'].describe())

    return dark_events_flagged


def get_top_suspicious_events(dark_events_flagged, top_n=20):
    """
    Get the most suspicious dark events.

    Args:
        dark_events_flagged (pd.DataFrame): Dark events with suspicious flags
        top_n (int): Number of top events to return

    Returns:
        pd.DataFrame: Top suspicious events
    """
    suspicious_events = dark_events_flagged[dark_events_flagged['is_suspicious']]
    top_events = suspicious_events.nlargest(top_n, 'suspicion_score')

    print(f"\nTop {top_n} Most Suspicious Dark Events:")
    print(top_events[['MMSI', 'GapStartTime', 'GapDuration', 'UniqueNearbyVessels',
                      'RepeatedNearbyVessels', 'suspicion_score']])

    return top_events


def analyze_suspicious_vessel_types(dark_events_flagged, df, df_nearby):
    """
    Analyze vessel types involved in suspicious dark events.

    Args:
        dark_events_flagged (pd.DataFrame): Flagged dark events
        df (pd.DataFrame): Original AIS data
        df_nearby (pd.DataFrame): Nearby vessel data

    Returns:
        pd.DataFrame: Vessel type analysis
    """
    # Get vessel types for dark event vessels
    vessel_info = df.groupby('MMSI').agg({
        'VesselName': 'first',
        'VesselType': 'first',
        'Length': 'first'
    }).reset_index()

    # Merge with suspicious events
    suspicious_events = dark_events_flagged[dark_events_flagged['is_suspicious']]
    suspicious_with_info = suspicious_events.merge(vessel_info, on='MMSI', how='left')

    # Analyze by vessel type
    type_analysis = suspicious_with_info.groupby('VesselType').agg({
        'MMSI': 'count',
        'suspicion_score': 'mean'
    }).reset_index()
    type_analysis.rename(columns={'MMSI': 'SuspiciousEventCount'}, inplace=True)
    type_analysis = type_analysis.sort_values(by='SuspiciousEventCount', ascending=False)

    print("\nSuspicious Events by Vessel Type:")
    print(type_analysis.head(10))

    return type_analysis


def main():
    """Main function to demonstrate pattern analysis and flagging."""
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

    # Flag suspicious events
    dark_events_flagged = flag_suspicious_events(
        dark_events,
        df_nearby,
        min_nearby_vessels=1
    )

    # Get top suspicious events
    top_suspicious = get_top_suspicious_events(dark_events_flagged, top_n=20)

    # Analyze vessel types
    type_analysis = analyze_suspicious_vessel_types(dark_events_flagged, df_clean, df_nearby)

    # Save results
    dark_events_flagged.to_csv('flagged_dark_events.csv', index=False)
    top_suspicious.to_csv('top_suspicious_events.csv', index=False)
    type_analysis.to_csv('vessel_type_analysis.csv', index=False)
    print("\nResults saved to flagged_dark_events.csv, top_suspicious_events.csv, and vessel_type_analysis.csv")

    return dark_events_flagged, top_suspicious, type_analysis


if __name__ == "__main__":
    main()
