"""
Dark Event Detection Script
Identifies "dark periods" where vessels turn off their AIS tracking.
"""

import pandas as pd
from data_preprocessing import load_ais_data, preprocess_ais_data


def detect_dark_events(df, threshold_minutes=10):
    """
    Detect dark events (AIS silence periods) for each vessel.

    A dark event is identified when the time gap between consecutive AIS
    transmissions exceeds the specified threshold.

    Args:
        df (pd.DataFrame): Preprocessed AIS data
        threshold_minutes (int): Minimum gap duration to consider as a dark event

    Returns:
        pd.DataFrame: Dark events with MMSI, GapStartTime, and GapDuration
    """
    # Ensure data is sorted by MMSI and BaseDateTime
    df = df.sort_values(by=['MMSI', 'BaseDateTime'])

    # Calculate time difference between consecutive transmissions for each vessel
    df['TimeDifference'] = df.groupby('MMSI')['BaseDateTime'].diff()

    # Define threshold for dark events
    dark_event_threshold = pd.Timedelta(minutes=threshold_minutes)

    # Identify dark events
    dark_events = df[df['TimeDifference'] > dark_event_threshold].copy()

    # Create dark events dataframe with relevant information
    dark_events['GapDuration'] = dark_events['TimeDifference']
    dark_events_summary = dark_events[['MMSI', 'BaseDateTime', 'GapDuration']].rename(
        columns={'BaseDateTime': 'GapStartTime'}
    )

    print(f"\nDetected {len(dark_events_summary)} dark events")
    print(f"Threshold: {threshold_minutes} minutes")
    print(f"\nDark event statistics:")
    print(f"  Mean gap duration: {dark_events_summary['GapDuration'].mean()}")
    print(f"  Median gap duration: {dark_events_summary['GapDuration'].median()}")
    print(f"  Max gap duration: {dark_events_summary['GapDuration'].max()}")

    return dark_events_summary


def get_vessel_stats(df, dark_events):
    """
    Calculate statistics about vessels with dark events.

    Args:
        df (pd.DataFrame): Preprocessed AIS data
        dark_events (pd.DataFrame): Detected dark events

    Returns:
        pd.DataFrame: Statistics per vessel
    """
    # Count dark events per vessel
    dark_event_counts = dark_events.groupby('MMSI').size().reset_index(name='DarkEventCount')

    # Get vessel information from original data
    vessel_info = df.groupby('MMSI').agg({
        'VesselName': 'first',
        'VesselType': 'first',
        'Length': 'first',
        'Width': 'first',
        'BaseDateTime': 'count'  # Total number of AIS records
    }).reset_index()

    vessel_info.rename(columns={'BaseDateTime': 'TotalRecords'}, inplace=True)

    # Merge with dark event counts
    vessel_stats = vessel_info.merge(dark_event_counts, on='MMSI', how='left')
    vessel_stats['DarkEventCount'].fillna(0, inplace=True)

    # Sort by number of dark events
    vessel_stats = vessel_stats.sort_values(by='DarkEventCount', ascending=False)

    print(f"\nVessels with most dark events:")
    print(vessel_stats.head(10))

    return vessel_stats


def main():
    """Main function to demonstrate dark event detection."""
    # Load and preprocess data
    file_path = '../../datasets/AIS_2024_01_01.csv'
    df = load_ais_data(file_path)
    df_clean = preprocess_ais_data(df)

    # Detect dark events
    dark_events = detect_dark_events(df_clean, threshold_minutes=10)

    print("\nSample dark events:")
    print(dark_events.head(10))

    # Get vessel statistics
    vessel_stats = get_vessel_stats(df_clean, dark_events)

    # Save results
    dark_events.to_csv('dark_events.csv', index=False)
    vessel_stats.to_csv('vessel_dark_event_stats.csv', index=False)
    print("\nResults saved to dark_events.csv and vessel_dark_event_stats.csv")

    return dark_events, vessel_stats


if __name__ == "__main__":
    main()
