"""
Visualization and Reporting Script
Creates plots and visualizations for AIS dark event analysis.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from data_preprocessing import load_ais_data, preprocess_ais_data
from dark_event_detection import detect_dark_events
from spatial_proximity_analysis import find_nearby_vessels
from pattern_analysis import flag_suspicious_events


def plot_suspicious_event_locations(dark_events_flagged, df, output_path='suspicious_locations.png'):
    """
    Plot geographical distribution of suspicious dark events.

    Args:
        dark_events_flagged (pd.DataFrame): Flagged dark events
        df (pd.DataFrame): Original AIS data
        output_path (str): Path to save the plot
    """
    # Get last known positions for suspicious events
    suspicious_events = dark_events_flagged[dark_events_flagged['is_suspicious']].copy()

    last_positions = []
    for _, row in suspicious_events.iterrows():
        mmsi = row['MMSI']
        gap_start_time = row['GapStartTime']

        last_pos = df[(df['MMSI'] == mmsi) & (df['BaseDateTime'] <= gap_start_time)].sort_values(
            by='BaseDateTime', ascending=False
        ).head(1)

        if not last_pos.empty:
            pos_data = last_pos.iloc[0].to_dict()
            pos_data['suspicion_score'] = row['suspicion_score']
            last_positions.append(pos_data)

    if not last_positions:
        print("No position data available for suspicious events")
        return

    df_positions = pd.DataFrame(last_positions)

    # Create plot
    plt.figure(figsize=(14, 10))
    scatter = plt.scatter(
        df_positions['LON'],
        df_positions['LAT'],
        c=df_positions['suspicion_score'],
        cmap='YlOrRd',
        alpha=0.6,
        s=50,
        edgecolors='black',
        linewidth=0.5
    )
    plt.colorbar(scatter, label='Suspicion Score')
    plt.title('Geographical Distribution of Suspicious Dark Events', fontsize=16, fontweight='bold')
    plt.xlabel('Longitude', fontsize=12)
    plt.ylabel('Latitude', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved suspicious event locations plot to {output_path}")


def plot_gap_duration_distribution(dark_events_flagged, output_path='gap_duration_distribution.png'):
    """
    Plot distribution of gap durations for suspicious vs non-suspicious events.

    Args:
        dark_events_flagged (pd.DataFrame): Flagged dark events
        output_path (str): Path to save the plot
    """
    # Convert gap duration to hours
    dark_events_flagged = dark_events_flagged.copy()
    dark_events_flagged['GapDuration_hours'] = dark_events_flagged['GapDuration'].dt.total_seconds() / 3600

    # Create plot
    plt.figure(figsize=(12, 6))
    sns.histplot(
        data=dark_events_flagged,
        x='GapDuration_hours',
        hue='is_suspicious',
        bins=50,
        kde=True,
        alpha=0.6
    )
    plt.title('Distribution of Dark Event Gap Durations', fontsize=16, fontweight='bold')
    plt.xlabel('Gap Duration (Hours)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.legend(title='Is Suspicious', labels=['Non-Suspicious', 'Suspicious'])
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved gap duration distribution plot to {output_path}")


def plot_suspicion_score_distribution(dark_events_flagged, output_path='suspicion_scores.png'):
    """
    Plot distribution of suspicion scores.

    Args:
        dark_events_flagged (pd.DataFrame): Flagged dark events
        output_path (str): Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(
        data=dark_events_flagged,
        x='suspicion_score',
        bins=20,
        kde=True,
        color='crimson',
        alpha=0.7
    )
    plt.title('Distribution of Suspicion Scores', fontsize=16, fontweight='bold')
    plt.xlabel('Suspicion Score', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved suspicion score distribution plot to {output_path}")


def plot_nearby_vessel_analysis(dark_events_flagged, output_path='nearby_vessel_counts.png'):
    """
    Plot analysis of nearby vessel counts.

    Args:
        dark_events_flagged (pd.DataFrame): Flagged dark events
        output_path (str): Path to save the plot
    """
    # Filter suspicious events
    suspicious = dark_events_flagged[dark_events_flagged['is_suspicious']].copy()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Distribution of unique nearby vessels
    axes[0].hist(suspicious['UniqueNearbyVessels'], bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    axes[0].set_title('Unique Nearby Vessels per Suspicious Event', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Number of Unique Nearby Vessels', fontsize=10)
    axes[0].set_ylabel('Frequency', fontsize=10)
    axes[0].grid(True, alpha=0.3, axis='y')

    # Plot 2: Distribution of repeated nearby vessels
    axes[1].hist(suspicious['RepeatedNearbyVessels'], bins=20, color='coral', alpha=0.7, edgecolor='black')
    axes[1].set_title('Repeated Nearby Vessels per Suspicious Event', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Number of Repeated Nearby Vessels', fontsize=10)
    axes[1].set_ylabel('Frequency', fontsize=10)
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved nearby vessel analysis plot to {output_path}")


def generate_summary_report(dark_events_flagged, df_nearby, output_path='summary_report.json'):
    """
    Generate JSON summary report for frontend consumption.

    Args:
        dark_events_flagged (pd.DataFrame): Flagged dark events
        df_nearby (pd.DataFrame): Nearby vessel data
        output_path (str): Path to save JSON report
    """
    suspicious_events = dark_events_flagged[dark_events_flagged['is_suspicious']]

    summary = {
        'total_dark_events': len(dark_events_flagged),
        'suspicious_events': len(suspicious_events),
        'suspicious_percentage': round(100 * len(suspicious_events) / len(dark_events_flagged), 2),
        'avg_suspicion_score': round(suspicious_events['suspicion_score'].mean(), 2),
        'max_suspicion_score': int(suspicious_events['suspicion_score'].max()),
        'avg_gap_duration_hours': round(suspicious_events['GapDuration'].dt.total_seconds().mean() / 3600, 2),
        'avg_nearby_vessels': round(suspicious_events['UniqueNearbyVessels'].mean(), 2),
        'total_nearby_observations': len(df_nearby),
        'unique_vessels_with_dark_events': dark_events_flagged['MMSI'].nunique(),
        'unique_vessels_suspicious': suspicious_events['MMSI'].nunique()
    }

    # Top suspicious events for frontend
    top_suspicious = suspicious_events.nlargest(10, 'suspicion_score')
    summary['top_suspicious_events'] = []

    for _, event in top_suspicious.iterrows():
        summary['top_suspicious_events'].append({
            'mmsi': int(event['MMSI']),
            'gap_start_time': event['GapStartTime'].isoformat(),
            'gap_duration_hours': round(event['GapDuration'].total_seconds() / 3600, 2),
            'suspicion_score': int(event['suspicion_score']),
            'unique_nearby_vessels': int(event['UniqueNearbyVessels']),
            'repeated_nearby_vessels': int(event['RepeatedNearbyVessels'])
        })

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary Report:")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved summary report to {output_path}")

    return summary


def main():
    """Main function to generate all visualizations and reports."""
    print("Starting visualization and reporting process...")

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
    dark_events_flagged = flag_suspicious_events(dark_events, df_nearby)

    # Generate visualizations
    print("\nGenerating visualizations...")
    plot_suspicious_event_locations(dark_events_flagged, df_clean)
    plot_gap_duration_distribution(dark_events_flagged)
    plot_suspicion_score_distribution(dark_events_flagged)
    plot_nearby_vessel_analysis(dark_events_flagged)

    # Generate summary report
    summary = generate_summary_report(dark_events_flagged, df_nearby)

    print("\nAll visualizations and reports generated successfully!")

    return summary


if __name__ == "__main__":
    main()
