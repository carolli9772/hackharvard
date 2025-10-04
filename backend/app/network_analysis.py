"""
Graph-Based Network Detection for Vessel Coordination
Uses network analysis to detect coordinated illegal fishing activities.
"""

import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict
import json


def build_vessel_network(dark_events, proximity_events):
    """
    Build a graph where:
    - Nodes = vessels
    - Edges = co-occurrence during dark periods (within proximity)

    Args:
        dark_events: List of dark events with context
        proximity_events: List of proximity events

    Returns:
        NetworkX graph
    """
    G = nx.Graph()

    # Track dark period co-occurrences
    dark_cooccurrences = defaultdict(int)

    print("Building vessel network from dark events and proximity data...")

    # For each dark event, find vessels that were nearby
    for event in dark_events:
        vessel_mmsi = event['mmsi']
        nearby_vessels = event.get('nearby_vessel_details', [])

        # Add node for dark event vessel
        if not G.has_node(vessel_mmsi):
            G.add_node(
                vessel_mmsi,
                vessel_name=event.get('vessel_name', 'Unknown'),
                is_fishing=event.get('is_fishing_vessel', False),
                dark_event_count=1,
                total_suspicion=event.get('total_score', 0)
            )
        else:
            # Update counts
            G.nodes[vessel_mmsi]['dark_event_count'] += 1
            G.nodes[vessel_mmsi]['total_suspicion'] += event.get('total_score', 0)

        # Add edges for nearby vessels
        for nearby in nearby_vessels:
            nearby_mmsi = nearby['mmsi']

            # Add node if doesn't exist
            if not G.has_node(nearby_mmsi):
                G.add_node(
                    nearby_mmsi,
                    vessel_name='Unknown',
                    is_fishing=False,
                    dark_event_count=0,
                    total_suspicion=0
                )

            # Add or update edge
            if G.has_edge(vessel_mmsi, nearby_mmsi):
                G[vessel_mmsi][nearby_mmsi]['weight'] += 1
            else:
                G.add_edge(vessel_mmsi, nearby_mmsi, weight=1)

    print(f"\nNetwork Statistics:")
    print(f"  Nodes (vessels): {G.number_of_nodes()}")
    print(f"  Edges (co-occurrences): {G.number_of_edges()}")
    print(f"  Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")

    return G


def analyze_network_centrality(G):
    """
    Analyze network centrality metrics to identify key vessels.

    Metrics:
    - Degree centrality: vessels with many connections
    - Betweenness centrality: vessels that bridge groups
    - Closeness centrality: vessels central to the network
    """
    print("\nCalculating centrality metrics...")

    # Degree centrality
    degree_centrality = nx.degree_centrality(G)

    # Betweenness centrality (identifies bridges/coordinators)
    betweenness_centrality = nx.betweenness_centrality(G)

    # Closeness centrality
    if nx.is_connected(G):
        closeness_centrality = nx.closeness_centrality(G)
    else:
        # For disconnected graphs, calculate for largest component
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        closeness_centrality = nx.closeness_centrality(subgraph)

    # Combine metrics
    centrality_scores = []
    for node in G.nodes():
        centrality_scores.append({
            'mmsi': int(node),
            'vessel_name': G.nodes[node].get('vessel_name', 'Unknown'),
            'degree_centrality': round(degree_centrality.get(node, 0), 4),
            'betweenness_centrality': round(betweenness_centrality.get(node, 0), 4),
            'closeness_centrality': round(closeness_centrality.get(node, 0), 4),
            'dark_event_count': G.nodes[node].get('dark_event_count', 0),
            'total_suspicion': round(G.nodes[node].get('total_suspicion', 0), 3),
            'is_fishing': G.nodes[node].get('is_fishing', False)
        })

    # Sort by betweenness (coordinators)
    centrality_scores.sort(key=lambda x: x['betweenness_centrality'], reverse=True)

    print("\nTop 5 Potential Coordinators (by betweenness centrality):")
    for i, vessel in enumerate(centrality_scores[:5]):
        print(f"{i+1}. MMSI: {vessel['mmsi']} - Betweenness: {vessel['betweenness_centrality']}")

    return centrality_scores


def detect_communities(G):
    """
    Detect communities (clusters of coordinated vessels).

    Uses Louvain method for community detection.
    """
    print("\nDetecting vessel communities...")

    # Use Louvain community detection
    try:
        communities = nx.community.louvain_communities(G, seed=42)
    except:
        # Fallback to greedy modularity
        communities = nx.community.greedy_modularity_communities(G)

    community_data = []
    for i, community in enumerate(communities):
        vessel_list = list(community)

        # Calculate community statistics
        subgraph = G.subgraph(community)
        total_edges = subgraph.number_of_edges()

        # Get suspicion scores
        suspicion_scores = [G.nodes[v].get('total_suspicion', 0) for v in vessel_list]
        avg_suspicion = np.mean(suspicion_scores) if suspicion_scores else 0

        # Count fishing vessels
        fishing_count = sum(1 for v in vessel_list if G.nodes[v].get('is_fishing', False))

        community_data.append({
            'community_id': i,
            'vessel_count': len(vessel_list),
            'vessel_mmsis': [int(v) for v in vessel_list[:20]],  # Top 20
            'internal_connections': total_edges,
            'avg_suspicion_score': round(avg_suspicion, 3),
            'fishing_vessel_count': fishing_count,
            'is_suspicious_fleet': avg_suspicion >= 0.6 and fishing_count >= 2
        })

    # Sort by suspicion
    community_data.sort(key=lambda x: x['avg_suspicion_score'], reverse=True)

    suspicious_fleets = sum(1 for c in community_data if c['is_suspicious_fleet'])
    print(f"  Communities detected: {len(community_data)}")
    print(f"  Suspicious fleets (avg suspicion >= 0.6, 2+ fishing vessels): {suspicious_fleets}")

    return community_data


def identify_transshipment_patterns(G, centrality_scores):
    """
    Identify potential transshipment patterns.

    Transshipment indicators:
    - High betweenness centrality (vessel acts as intermediary)
    - Connected to multiple fishing vessels
    - Non-fishing vessel type
    """
    potential_motherships = []

    for score in centrality_scores:
        mmsi = score['mmsi']

        # Get neighbors
        if mmsi in G:
            neighbors = list(G.neighbors(mmsi))
            fishing_neighbors = sum(1 for n in neighbors if G.nodes[n].get('is_fishing', False))

            # Criteria for potential mothership/transshipment vessel
            if (score['betweenness_centrality'] > 0.1 and
                fishing_neighbors >= 3 and
                not score['is_fishing']):

                potential_motherships.append({
                    'mmsi': score['mmsi'],
                    'vessel_name': score['vessel_name'],
                    'betweenness_centrality': score['betweenness_centrality'],
                    'connected_fishing_vessels': fishing_neighbors,
                    'total_connections': len(neighbors),
                    'total_suspicion': score['total_suspicion']
                })

    potential_motherships.sort(key=lambda x: x['betweenness_centrality'], reverse=True)

    print(f"\nPotential Transshipment/Mothership Vessels: {len(potential_motherships)}")
    if potential_motherships:
        print("Top 3:")
        for i, vessel in enumerate(potential_motherships[:3]):
            print(f"{i+1}. MMSI: {vessel['mmsi']} - {vessel['connected_fishing_vessels']} fishing vessels connected")

    return potential_motherships


def save_network_analysis(G, centrality_scores, communities, motherships,
                          graph_path='vessel_network.gexf',
                          centrality_path='centrality_scores.json',
                          community_path='vessel_communities.json',
                          mothership_path='potential_motherships.json'):
    """Save network analysis results."""

    # Save graph in GEXF format (for visualization in Gephi, etc.)
    nx.write_gexf(G, graph_path)
    print(f"\nSaved network graph to {graph_path}")

    # Save JSON data
    with open(centrality_path, 'w') as f:
        json.dump(centrality_scores, f, indent=2)

    with open(community_path, 'w') as f:
        json.dump(communities, f, indent=2)

    with open(mothership_path, 'w') as f:
        json.dump(motherships, f, indent=2)

    print(f"Saved centrality scores to {centrality_path}")
    print(f"Saved communities to {community_path}")
    print(f"Saved potential motherships to {mothership_path}")


def main():
    """Main function for network analysis."""
    # Load contextualized dark events
    try:
        with open('contextualized_dark_events.json', 'r') as f:
            dark_events = json.load(f)
    except FileNotFoundError:
        print("Error: Run dark_event_context.py first")
        return

    # Load proximity events (if available)
    try:
        with open('proximity_index.json', 'r') as f:
            proximity_events = json.load(f)
    except FileNotFoundError:
        print("Warning: proximity_index.json not found, using dark event context only")
        proximity_events = []

    # Build network
    G = build_vessel_network(dark_events, proximity_events)

    # Analyze centrality
    centrality_scores = analyze_network_centrality(G)

    # Detect communities
    communities = detect_communities(G)

    # Identify transshipment patterns
    motherships = identify_transshipment_patterns(G, centrality_scores)

    # Save results
    save_network_analysis(G, centrality_scores, communities, motherships)

    return G, centrality_scores, communities, motherships


if __name__ == "__main__":
    main()
