"""
Advanced Visualization - Heatmap of Suspicious Zones
Creates comprehensive visualizations for FishNet frontend.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from matplotlib.patches import Rectangle
import matplotlib.colors as mcolors


def create_suspicion_heatmap(hexbin_data, output_path='suspicion_heatmap.png'):
    """
    Create a heatmap showing suspicious dark zones.

    Args:
        hexbin_data: Hexbin aggregation data from suspicion_scoring.py
        output_path: Path to save the heatmap
    """
    if not hexbin_data:
        print("No hexbin data available")
        return

    # Extract data
    lats = [h['center'][0] for h in hexbin_data]
    lons = [h['center'][1] for h in hexbin_data]
    scores = [h['avg_suspicion_score'] for h in hexbin_data]
    counts = [h['event_count'] for h in hexbin_data]

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    # Plot 1: Heatmap by suspicion score
    scatter1 = ax1.scatter(
        lons, lats,
        c=scores,
        s=[c*10 for c in counts],  # Size by event count
        cmap='YlOrRd',
        alpha=0.6,
        edgecolors='black',
        linewidth=0.5
    )
    ax1.set_title('Dark Zone Heatmap - Suspicion Score', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Longitude', fontsize=12)
    ax1.set_ylabel('Latitude', fontsize=12)
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(scatter1, ax=ax1, label='Avg Suspicion Score')

    # Plot 2: Heatmap by event count
    scatter2 = ax2.scatter(
        lons, lats,
        c=counts,
        s=[c*10 for c in counts],
        cmap='plasma',
        alpha=0.6,
        edgecolors='black',
        linewidth=0.5
    )
    ax2.set_title('Dark Zone Heatmap - Event Frequency', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Longitude', fontsize=12)
    ax2.set_ylabel('Latitude', fontsize=12)
    ax2.grid(True, alpha=0.3)
    cbar2 = plt.colorbar(scatter2, ax=ax2, label='Event Count')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved suspicion heatmap to {output_path}")


def create_network_visualization(centrality_scores, communities, output_path='network_viz.png'):
    """
    Visualize network centrality and communities.

    Args:
        centrality_scores: List of centrality scores
        communities: List of community data
        output_path: Path to save visualization
    """
    if not centrality_scores or not communities:
        print("No network data available")
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Top vessels by degree centrality
    top_degree = sorted(centrality_scores, key=lambda x: x['degree_centrality'], reverse=True)[:10]
    ax1 = axes[0, 0]
    ax1.barh(
        [f"MMSI {v['mmsi']}" for v in top_degree],
        [v['degree_centrality'] for v in top_degree],
        color='steelblue'
    )
    ax1.set_xlabel('Degree Centrality')
    ax1.set_title('Top 10 Vessels by Network Connections', fontweight='bold')
    ax1.invert_yaxis()

    # Plot 2: Top vessels by betweenness centrality (coordinators)
    top_between = sorted(centrality_scores, key=lambda x: x['betweenness_centrality'], reverse=True)[:10]
    ax2 = axes[0, 1]
    ax2.barh(
        [f"MMSI {v['mmsi']}" for v in top_between],
        [v['betweenness_centrality'] for v in top_between],
        color='coral'
    )
    ax2.set_xlabel('Betweenness Centrality')
    ax2.set_title('Top 10 Potential Coordinators', fontweight='bold')
    ax2.invert_yaxis()

    # Plot 3: Community sizes
    ax3 = axes[1, 0]
    comm_sizes = [c['vessel_count'] for c in communities]
    ax3.hist(comm_sizes, bins=20, color='mediumseagreen', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Community Size (# of vessels)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Distribution of Community Sizes', fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Community suspicion scores
    ax4 = axes[1, 1]
    comm_scores = [c['avg_suspicion_score'] for c in communities]
    ax4.hist(comm_scores, bins=20, color='crimson', alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Average Suspicion Score')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Distribution of Community Suspicion Scores', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved network visualization to {output_path}")


def create_temporal_analysis(dark_events, output_path='temporal_analysis.png'):
    """
    Analyze temporal patterns of dark events.

    Args:
        dark_events: List of dark events
        output_path: Path to save visualization
    """
    if not dark_events:
        print("No dark events available")
        return

    # Convert to DataFrame
    df = pd.DataFrame(dark_events)
    df['start'] = pd.to_datetime(df['start'])
    df['hour'] = df['start'].dt.hour

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # Plot 1: Dark events by hour of day
    ax1 = axes[0, 0]
    hour_counts = df['hour'].value_counts().sort_index()
    ax1.bar(hour_counts.index, hour_counts.values, color='navy', alpha=0.7)
    ax1.set_xlabel('Hour of Day')
    ax1.set_ylabel('Number of Dark Events')
    ax1.set_title('Dark Events by Hour of Day', fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # Plot 2: Duration distribution
    ax2 = axes[0, 1]
    durations = [e['duration_hours'] for e in dark_events]
    ax2.hist(durations, bins=30, color='darkgreen', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Duration (hours)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of Dark Period Durations', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Fishing vs Non-Fishing vessels
        # --- Plot 3: Fishing vs Non-Fishing vessels ---
    ax3 = axes[1, 0]
    fishing_counts = df['is_fishing_vessel'].value_counts(dropna=False)

    # Dynamically generate labels from data
    labels = [str(k) for k in fishing_counts.index]
    colors_pie = sns.color_palette('Set2', n_colors=len(labels))

    # If only one category, display text instead of pie
    if len(fishing_counts) > 1:
        ax3.pie(
            fishing_counts.values,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors_pie,
            startangle=90
        )
    else:
        only_label = labels[0]
        ax3.text(
            0, 0, f"Only {only_label} vessels",
            ha='center', va='center', fontsize=12, fontweight='bold'
        )
        ax3.set_aspect('equal')

    ax3.set_title('Dark Events: Fishing vs Non-Fishing Vessels', fontweight='bold')


    # Plot 4: Suspicion score distribution
    ax4 = axes[1, 1]
    scores = [e.get('total_score', 0) for e in dark_events]
    ax4.hist(scores, bins=30, color='purple', alpha=0.7, edgecolor='black')
    ax4.axvline(x=0.7, color='red', linestyle='--', linewidth=2, label='High Suspicion Threshold')
    ax4.set_xlabel('Suspicion Score')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Distribution of Suspicion Scores', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved temporal analysis to {output_path}")


def generate_frontend_data_package(dark_events, hexbin_data, clusters, communities,
                                   centrality_scores, motherships,
                                   output_path='frontend_data_package.json'):
    """
    Generate comprehensive JSON package for frontend consumption.

    Args:
        All analysis outputs
        output_path: Path to save JSON package
    """
    # Top suspicious events
    top_events = sorted(dark_events, key=lambda x: x.get('total_score', 0), reverse=True)[:50]

    # Top hotspots
    top_hotspots = sorted(hexbin_data, key=lambda x: x['event_count'], reverse=True)[:20]

    # Top suspicious communities
    top_communities = sorted(communities, key=lambda x: x['avg_suspicion_score'], reverse=True)[:10]

    # Top coordinators
    top_coordinators = sorted(centrality_scores, key=lambda x: x['betweenness_centrality'], reverse=True)[:20]

    # Summary statistics
    summary = {
        'total_dark_events': len(dark_events),
        'high_suspicion_events': sum(1 for e in dark_events if e.get('total_score', 0) >= 0.7),
        'fishing_vessel_events': sum(1 for e in dark_events if e.get('is_fishing_vessel', False)),
        'avg_duration_hours': round(np.mean([e['duration_hours'] for e in dark_events]), 2),
        'total_vessels_involved': len(set(e['mmsi'] for e in dark_events)),
        'total_communities': len(communities),
        'suspicious_communities': sum(1 for c in communities if c.get('is_suspicious_fleet', False)),
        'potential_motherships': len(motherships),
        'total_hotspots': len([h for h in hexbin_data if h['event_count'] >= 10])
    }

    # Package all data
    package = {
        'summary': summary,
        'top_suspicious_events': top_events,
        'dark_zone_hotspots': top_hotspots,
        'suspicious_communities': top_communities,
        'potential_coordinators': top_coordinators,
        'potential_motherships': motherships[:10],
        'all_clusters': clusters[:20]  # Top 20 clusters
    }

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(package, f, indent=2)

    print(f"\nFrontend Data Package Summary:")
    print(f"  Total dark events: {summary['total_dark_events']}")
    print(f"  High suspicion events: {summary['high_suspicion_events']}")
    print(f"  Suspicious communities: {summary['suspicious_communities']}")
    print(f"  Potential motherships: {summary['potential_motherships']}")
    print(f"\nSaved frontend data package to {output_path}")

    return package


def main():
    """Main function to generate all visualizations."""
    print("Generating advanced visualizations...")

    # Load all analysis outputs
    try:
        with open('scored_dark_events.json', 'r') as f:
            dark_events = json.load(f)

        with open('dark_zone_hexbins.json', 'r') as f:
            hexbin_data = json.load(f)

        with open('dark_zone_clusters.json', 'r') as f:
            clusters = json.load(f)

        with open('vessel_communities.json', 'r') as f:
            communities = json.load(f)

        with open('centrality_scores.json', 'r') as f:
            centrality_scores = json.load(f)

        with open('potential_motherships.json', 'r') as f:
            motherships = json.load(f)

    except FileNotFoundError as e:
        print(f"Error: Missing data file - {e}")
        print("Run the analysis pipeline in order:")
        print("1. enhanced_dark_detection.py")
        print("2. proximity_index.py")
        print("3. dark_event_context.py")
        print("4. suspicion_scoring.py")
        print("5. network_analysis.py")
        return

    # Create visualizations
    create_suspicion_heatmap(hexbin_data)
    create_network_visualization(centrality_scores, communities)
    create_temporal_analysis(dark_events)

    # Generate frontend data package
    package = generate_frontend_data_package(
        dark_events, hexbin_data, clusters, communities,
        centrality_scores, motherships
    )

    print("\nAll visualizations generated successfully!")

    return package


if __name__ == "__main__":
    main()
