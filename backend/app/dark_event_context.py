"""
Dark Event Context Checker
Validates dark events by checking AIS coverage from nearby vessels.
"""

import pandas as pd
import numpy as np
import json
from proximity_index import haversine_distance, get_vessels_near_location


def check_dark_event_context(dark_events, proximity_events, df_ais,
                              radius_km=20, time_window_minutes=15):
    """
    Check context for each dark event.

    For each dark event:
    - Look up other vessels within radius and time window
    - If those vessels kept transmitting → high confidence dark event
    - Log which vessels were nearby

    Args:
        dark_events: List of enhanced dark events
        proximity_events: Proximity index from proximity_index.py
        df_ais: Original AIS DataFrame
        radius_km: Search radius in kilometers
        time_window_minutes: Time window around start/end in minutes

    Returns:
        Dark events enriched with context information
    """
    print(f"Checking context for {len(dark_events)} dark events...")

    for i, event in enumerate(dark_events):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(dark_events)} events...")

        start_time = pd.to_datetime(event['start'])
        end_time = pd.to_datetime(event['end'])
        location = event['location']

        # Find vessels near start time
        nearby_at_start = get_vessels_near_location(
            proximity_events,
            location,
            start_time,
            radius_km=radius_km,
            time_window_minutes=time_window_minutes
        )

        # Find vessels near end time
        nearby_at_end = get_vessels_near_location(
            proximity_events,
            location,
            end_time,
            radius_km=radius_km,
            time_window_minutes=time_window_minutes
        )

        # Calculate coverage reliability
        # More nearby vessels = better coverage = higher confidence
        unique_nearby_vessels = set()
        for v in nearby_at_start + nearby_at_end:
            unique_nearby_vessels.add(v['mmsi'])

        # Remove the dark event vessel itself
        unique_nearby_vessels.discard(event['mmsi'])

        # Check if nearby vessels had continuous transmission during dark period
        continuously_transmitting = []

        for nearby_mmsi in unique_nearby_vessels:
            vessel_transmissions = df_ais[
                (df_ais['MMSI'] == nearby_mmsi) &
                (df_ais['BaseDateTime'] >= start_time) &
                (df_ais['BaseDateTime'] <= end_time)
            ]

            # If vessel transmitted during dark period, it's continuously transmitting
            if len(vessel_transmissions) > 0:
                continuously_transmitting.append({
                    'mmsi': int(nearby_mmsi),
                    'transmission_count': len(vessel_transmissions)
                })

        # Calculate confidence score
        # More continuously transmitting vessels = higher confidence the dark event is real
        coverage_reliability = len(continuously_transmitting) / max(len(unique_nearby_vessels), 1)

        # Confidence calculation:
        # - High coverage reliability (many nearby vessels transmitting) = high confidence
        # - Long dark duration = higher confidence
        # - Proximity to fishing zones = higher confidence

        duration_factor = min(event['duration_hours'] / 3.0, 1.0)  # Normalize to 3 hours max
        confidence_score = (
            0.5 * coverage_reliability +
            0.3 * duration_factor +
            0.2 * (1 if event.get('is_fishing_vessel', False) else 0)
        )

        # Enrich event with context
        event['nearby_vessels_at_start'] = len(nearby_at_start)
        event['nearby_vessels_at_end'] = len(nearby_at_end)
        event['unique_nearby_vessels'] = len(unique_nearby_vessels)
        event['continuously_transmitting_nearby'] = len(continuously_transmitting)
        event['coverage_reliability'] = round(coverage_reliability, 3)
        event['confidence_score'] = round(confidence_score, 3)
        event['high_confidence'] = confidence_score >= 0.6
        event['nearby_vessel_details'] = continuously_transmitting[:5]  # Top 5 for brevity

    # Summary stats
    high_confidence_count = sum(1 for e in dark_events if e.get('high_confidence', False))
    print(f"\nContext check complete:")
    print(f"  High confidence dark events: {high_confidence_count}/{len(dark_events)}")

    return dark_events


def identify_suspicious_patterns(dark_events_with_context):
    """
    Identify suspicious patterns in dark events with context.

    Patterns to look for:
    - Repeated dark events by same vessel
    - Dark events with fishing vessels nearby
    - Dark events in high-value fishing zones
    """
    # Convert to DataFrame for analysis
    df = pd.DataFrame(dark_events_with_context)

    # Find repeat offenders
    vessel_dark_counts = df.groupby('mmsi').size().reset_index(name='dark_event_count')
    repeat_offenders = vessel_dark_counts[vessel_dark_counts['dark_event_count'] >= 3]

    print(f"\nSuspicious Pattern Analysis:")
    print(f"  Vessels with 3+ dark events: {len(repeat_offenders)}")

    # Find events with fishing vessels nearby
    fishing_nearby = df[
        df['nearby_vessel_details'].apply(lambda x: len(x) > 0)
    ]
    print(f"  Dark events with continuously transmitting nearby vessels: {len(fishing_nearby)}")

    # High confidence fishing vessel dark events
    high_conf_fishing = df[
        (df['high_confidence'] == True) &
        (df.get('is_fishing_vessel', False) == True)
    ]
    print(f"  High confidence dark events from fishing vessels: {len(high_conf_fishing)}")

    return {
        'repeat_offenders': repeat_offenders.to_dict('records'),
        'high_confidence_fishing_events': high_conf_fishing.to_dict('records')[:20]  # Top 20
    }


def save_contextualized_events(dark_events, output_path='contextualized_dark_events.json'):
    """Save contextualized dark events to JSON."""
    with open(output_path, 'w') as f:
        json.dump(dark_events, f, indent=2)
    print(f"Saved contextualized dark events to {output_path}")


def main():
    """Main function to check dark event context."""
    from data_preprocessing import load_ais_data, preprocess_ais_data
    from enhanced_dark_detection import detect_enhanced_dark_events, load_fishing_gear_data, enrich_with_fishing_gear
    from proximity_index import build_proximity_index

    # Load AIS data
    file_path = '../../datasets/AIS_2024_01_01.csv'
    df = load_ais_data(file_path)
    df_clean = preprocess_ais_data(df)

    # Detect enhanced dark events
    fishing_data = load_fishing_gear_data()
    dark_events = detect_enhanced_dark_events(df_clean, threshold_minutes=10)
    dark_events = enrich_with_fishing_gear(dark_events, fishing_data)

    # Build proximity index (this may take time for large datasets)
    print("\nBuilding proximity index (this may take a few minutes)...")
    proximity_events = build_proximity_index(
        df_clean,
        time_window_minutes=10,
        distance_threshold_km=20
    )

    # Check context for dark events
    dark_events_with_context = check_dark_event_context(
        dark_events,
        proximity_events,
        df_clean,
        radius_km=20,
        time_window_minutes=15
    )

    # Identify suspicious patterns
    patterns = identify_suspicious_patterns(dark_events_with_context)

    # Save results
    save_contextualized_events(dark_events_with_context)

    print("\nSample contextualized dark event:")
    if dark_events_with_context:
        print(json.dumps(dark_events_with_context[0], indent=2))

    return dark_events_with_context, patterns


if __name__ == "__main__":
    main()
