"""
Advanced Suspicion Scoring and Clustering System
Assigns multi-factor suspicion scores and identifies dark zone hotspots.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict
import json


def calculate_eez_proximity(lat, lon):
    """
    Calculate proximity to EEZ boundary (simplified).
    In production, use actual EEZ polygon boundaries.

    Returns:
        float: Estimated distance to nearest EEZ boundary in km (0-1 normalized)
    """
    # Simplified: Assume EEZ boundaries are near coastlines
    # This is a placeholder - replace with actual EEZ boundary data

    # For now, use a simple heuristic based on latitude
    # Coastal areas are typically at certain latitudes
    coastal_zones = [
        (35, 45),   # Northern coastal zones
        (-45, -35), # Southern coastal zones
        (-10, 10)   # Equatorial coastal zones
    ]

    min_distance = 1.0
    for zone_min, zone_max in coastal_zones:
        if zone_min <= lat <= zone_max:
            min_distance = 0.1  # Close to EEZ
            break

    return min_distance


def calculate_multi_factor_score(event, repeat_offender_counts=None):
    """
    Calculate comprehensive suspicion score based on multiple factors.

    Factors:
    - Dark gap length (0.3 weight)
    - Coverage reliability (0.2 weight)
    - Proximity to EEZ boundary (0.2 weight)
    - Proximity to fishing vessel (0.2 weight)
    - Repeat offender (0.1 weight)
    """
    if repeat_offender_counts is None:
        repeat_offender_counts = {}

    # Factor 1: Dark gap length (normalized to 0-1, max at 6 hours)
    duration_score = min(event['duration_hours'] / 6.0, 1.0) * 0.3

    # Factor 2: Coverage reliability (inverse - low reliability = suspicious)
    coverage_score = (1 - event.get('coverage_reliability', 0.5)) * 0.2

    # Factor 3: Proximity to EEZ boundary
    lat, lon = event['location']
    eez_proximity = calculate_eez_proximity(lat, lon)
    eez_score = (1 - eez_proximity) * 0.2  # Closer to EEZ = higher score

    # Factor 4: Proximity to fishing vessel
    is_fishing = event.get('is_fishing_vessel', False)
    has_fishing_nearby = event.get('continuously_transmitting_nearby', 0) > 0
    fishing_score = (0.5 if is_fishing else 0) + (0.5 if has_fishing_nearby else 0)
    fishing_score *= 0.2

    # Factor 5: Repeat offender
    mmsi = event['mmsi']
    repeat_count = repeat_offender_counts.get(mmsi, 0)
    repeat_score = min(repeat_count / 10.0, 1.0) * 0.1  # Normalize to 10 events

    # Total score
    total_score = duration_score + coverage_score + eez_score + fishing_score + repeat_score

    return {
        'total_score': round(total_score, 3),
        'duration_score': round(duration_score, 3),
        'coverage_score': round(coverage_score, 3),
        'eez_score': round(eez_score, 3),
        'fishing_score': round(fishing_score, 3),
        'repeat_score': round(repeat_score, 3)
    }


def score_all_events(dark_events):
    """
    Score all dark events with multi-factor suspicion scores.
    """
    # Count repeat offenders
    repeat_counts = defaultdict(int)
    for event in dark_events:
        repeat_counts[event['mmsi']] += 1

    # Score each event
    for event in dark_events:
        scores = calculate_multi_factor_score(event, repeat_counts)
        event.update(scores)
        event['is_highly_suspicious'] = scores['total_score'] >= 0.7

    # Sort by suspicion score
    dark_events.sort(key=lambda x: x['total_score'], reverse=True)

    # Statistics
    highly_suspicious = sum(1 for e in dark_events if e['is_highly_suspicious'])
    print(f"\nSuspicion Scoring Complete:")
    print(f"  Total events: {len(dark_events)}")
    print(f"  Highly suspicious (score >= 0.7): {highly_suspicious}")
    print(f"  Average suspicion score: {np.mean([e['total_score'] for e in dark_events]):.3f}")

    return dark_events


def cluster_dark_zones(dark_events, eps_km=50, min_samples=3):
    """
    Cluster dark events spatially to identify hotspots.

    Args:
        dark_events: List of dark events with locations
        eps_km: Maximum distance between points in a cluster (km)
        min_samples: Minimum points to form a cluster

    Returns:
        Dark events with cluster labels and cluster summary
    """
    if not dark_events:
        return dark_events, []

    # Extract locations
    locations = np.array([event['location'] for event in dark_events])

    # Convert eps from km to approximate degrees
    # 1 degree ≈ 111 km
    eps_degrees = eps_km / 111.0

    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=eps_degrees, min_samples=min_samples, metric='euclidean')
    labels = clustering.fit_predict(locations)

    # Add cluster labels to events
    for i, event in enumerate(dark_events):
        event['cluster_id'] = int(labels[i])

    # Analyze clusters
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        if label != -1:  # -1 is noise
            clusters[label].append(dark_events[i])

    # Cluster summary
    cluster_summary = []
    for cluster_id, events in clusters.items():
        # Calculate cluster center
        lats = [e['location'][0] for e in events]
        lons = [e['location'][1] for e in events]
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)

        # Calculate average suspicion score
        avg_score = np.mean([e['total_score'] for e in events])

        # Identify vessels in cluster
        vessel_mmsis = list(set(e['mmsi'] for e in events))

        cluster_summary.append({
            'cluster_id': cluster_id,
            'event_count': len(events),
            'center_location': [round(center_lat, 4), round(center_lon, 4)],
            'avg_suspicion_score': round(avg_score, 3),
            'unique_vessels': len(vessel_mmsis),
            'vessel_mmsis': vessel_mmsis[:10],  # Top 10
            'is_hotspot': len(events) >= 10 and avg_score >= 0.6
        })

    # Sort by event count
    cluster_summary.sort(key=lambda x: x['event_count'], reverse=True)

    hotspot_count = sum(1 for c in cluster_summary if c['is_hotspot'])
    print(f"\nClustering Complete:")
    print(f"  Clusters identified: {len(cluster_summary)}")
    print(f"  Hotspots (10+ events, avg score >= 0.6): {hotspot_count}")
    print(f"  Noise points: {sum(1 for e in dark_events if e['cluster_id'] == -1)}")

    return dark_events, cluster_summary


def generate_hexbin_aggregation(dark_events, hex_resolution=2):
    """
    Aggregate dark events into hexagonal bins for heatmap visualization.

    Args:
        dark_events: List of dark events
        hex_resolution: H3 resolution (0-15, higher = smaller hexagons)

    Returns:
        Hexbin aggregation data
    """
    # Simple grid-based aggregation (alternative to H3)
    # Grid size based on resolution (smaller number = larger grid)
    grid_size = 10 / (hex_resolution + 1)  # degrees

    hexbins = defaultdict(lambda: {'count': 0, 'total_score': 0, 'events': []})

    for event in dark_events:
        lat, lon = event['location']

        # Create grid cell ID
        grid_lat = int(lat / grid_size) * grid_size
        grid_lon = int(lon / grid_size) * grid_size
        grid_id = f"{grid_lat:.1f},{grid_lon:.1f}"

        hexbins[grid_id]['count'] += 1
        hexbins[grid_id]['total_score'] += event['total_score']
        hexbins[grid_id]['events'].append(event['mmsi'])

    # Convert to list format
    hexbin_data = []
    for grid_id, data in hexbins.items():
        lat_str, lon_str = grid_id.split(',')
        hexbin_data.append({
            'grid_id': grid_id,
            'center': [float(lat_str), float(lon_str)],
            'event_count': data['count'],
            'avg_suspicion_score': round(data['total_score'] / data['count'], 3),
            'unique_vessels': len(set(data['events']))
        })

    # Sort by event count
    hexbin_data.sort(key=lambda x: x['event_count'], reverse=True)

    print(f"\nHexbin Aggregation Complete:")
    print(f"  Grid cells with events: {len(hexbin_data)}")
    print(f"  Hottest cell: {hexbin_data[0]['event_count']} events at {hexbin_data[0]['center']}")

    return hexbin_data


def save_scored_events(dark_events, cluster_summary, hexbin_data,
                       events_path='scored_dark_events.json',
                       clusters_path='dark_zone_clusters.json',
                       hexbin_path='dark_zone_hexbins.json'):
    """Save scored and clustered data."""
    with open(events_path, 'w') as f:
        json.dump(dark_events, f, indent=2)

    with open(clusters_path, 'w') as f:
        json.dump(cluster_summary, f, indent=2)

    with open(hexbin_path, 'w') as f:
        json.dump(hexbin_data, f, indent=2)

    print(f"\nSaved scored events to {events_path}")
    print(f"Saved cluster summary to {clusters_path}")
    print(f"Saved hexbin aggregation to {hexbin_path}")


def main():
    """Main function for suspicion scoring and clustering."""
    # Load contextualized dark events
    try:
        with open('contextualized_dark_events.json', 'r') as f:
            dark_events = json.load(f)
    except FileNotFoundError:
        print("Error: Run dark_event_context.py first to generate contextualized_dark_events.json")
        return

    # Score events
    scored_events = score_all_events(dark_events)

    # Cluster dark zones
    clustered_events, cluster_summary = cluster_dark_zones(
        scored_events,
        eps_km=50,
        min_samples=3
    )

    # Generate hexbin aggregation
    hexbin_data = generate_hexbin_aggregation(clustered_events, hex_resolution=2)

    # Save results
    save_scored_events(clustered_events, cluster_summary, hexbin_data)

    # Display top suspicious events
    print("\nTop 5 Most Suspicious Events:")
    for i, event in enumerate(clustered_events[:5]):
        print(f"\n{i+1}. MMSI: {event['mmsi']}")
        print(f"   Score: {event['total_score']}")
        print(f"   Location: {event['location']}")
        print(f"   Duration: {event['duration_hours']} hours")
        print(f"   Cluster: {event['cluster_id']}")

    return scored_events, cluster_summary, hexbin_data


if __name__ == "__main__":
    main()
