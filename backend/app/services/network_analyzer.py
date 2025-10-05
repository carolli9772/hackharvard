"""
Network Analysis for Vessel Coordination Detection
Detects coordinated illegal fishing activities through network analysis.
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class VesselNetworkAnalyzer:
    """Analyzes vessel networks to detect coordination and suspicious communities."""

    def __init__(self, proximity_threshold_km: float = 50.0):
        """
        Initialize network analyzer.

        Args:
            proximity_threshold_km: Distance threshold for vessel proximity (km)
        """
        self.proximity_threshold_km = proximity_threshold_km
        self.network = None

    def build_network(self, suspicious_events: pd.DataFrame, all_ais_data: pd.DataFrame) -> nx.Graph:
        """
        Build vessel coordination network from suspicious events.

        Args:
            suspicious_events: DataFrame with suspicious dark period events
            all_ais_data: Full AIS data for proximity analysis

        Returns:
            NetworkX graph with vessels as nodes and co-occurrences as edges
        """
        G = nx.Graph()

        logger.info("Building vessel coordination network...")

        # Group by MMSI to get vessel-level data
        for mmsi, vessel_events in suspicious_events.groupby('mmsi'):
            # Add node for this vessel
            total_risk = vessel_events['risk_score'].sum()
            event_count = len(vessel_events)

            G.add_node(
                mmsi,
                mmsi=int(mmsi),
                vessel_type=vessel_events.iloc[0].get('vessel_type', 'unknown'),
                event_count=event_count,
                total_risk=float(total_risk),
                avg_risk=float(vessel_events['risk_score'].mean()),
                is_fishing=vessel_events.iloc[0].get('is_fishing', True)
            )

            # Find nearby vessels during dark periods
            for _, event in vessel_events.iterrows():
                nearby_vessels = self._find_nearby_vessels(
                    event, all_ais_data, self.proximity_threshold_km
                )

                # Create edges for co-occurrence
                for nearby_mmsi in nearby_vessels:
                    if nearby_mmsi != mmsi:
                        if G.has_edge(mmsi, nearby_mmsi):
                            G[mmsi][nearby_mmsi]['weight'] += 1
                            G[mmsi][nearby_mmsi]['encounters'].append({
                                'timestamp': event['start_time'],
                                'location': (event['start_lat'], event['start_lon'])
                            })
                        else:
                            G.add_edge(mmsi, nearby_mmsi, weight=1, encounters=[{
                                'timestamp': event['start_time'],
                                'location': (event['start_lat'], event['start_lon'])
                            }])

        self.network = G
        logger.info(f"Network built: {G.number_of_nodes()} vessels, {G.number_of_edges()} connections")

        return G

    def _find_nearby_vessels(
        self,
        event: pd.Series,
        all_ais_data: pd.DataFrame,
        threshold_km: float
    ) -> List[int]:
        """Find vessels within proximity threshold during a time period."""
        from geopy.distance import geodesic

        # Get time window
        start_time = event['start_time']
        end_time = event['end_time']

        # Filter AIS data to time window
        nearby_data = all_ais_data[
            (all_ais_data['timestamp'] >= start_time) &
            (all_ais_data['timestamp'] <= end_time)
        ]

        nearby_vessels = []
        event_location = (event['start_lat'], event['start_lon'])

        # Check distance for each vessel
        for mmsi, vessel_data in nearby_data.groupby('mmsi'):
            for _, point in vessel_data.iterrows():
                point_location = (point['lat'], point['lon'])
                distance_km = geodesic(event_location, point_location).kilometers

                if distance_km <= threshold_km:
                    nearby_vessels.append(mmsi)
                    break  # Found proximity, no need to check other points

        return nearby_vessels

    def detect_communities(self) -> List[Dict[str, Any]]:
        """
        Detect vessel communities using Louvain method.

        Returns:
            List of community dictionaries with statistics
        """
        if self.network is None:
            raise ValueError("Network not built. Call build_network() first.")

        logger.info("Detecting vessel communities...")

        # Detect communities using Louvain method
        try:
            communities = nx.community.louvain_communities(self.network, seed=42)
        except:
            # Fallback to greedy modularity
            communities = nx.community.greedy_modularity_communities(self.network)

        community_data = []

        for i, community in enumerate(communities):
            if len(community) < 2:  # Skip single-vessel communities
                continue

            vessel_list = list(community)
            subgraph = self.network.subgraph(community)

            # Calculate community metrics
            total_risk = sum(self.network.nodes[v].get('total_risk', 0) for v in vessel_list)
            total_events = sum(self.network.nodes[v].get('event_count', 0) for v in vessel_list)
            avg_risk = total_risk / len(vessel_list) if vessel_list else 0

            # Network metrics
            density = nx.density(subgraph)

            # Get vessel details
            vessels = [{
                'mmsi': int(v),
                'vessel_type': self.network.nodes[v].get('vessel_type', 'unknown'),
                'event_count': self.network.nodes[v].get('event_count', 0),
                'total_risk': round(self.network.nodes[v].get('total_risk', 0), 3),
                'avg_risk': round(self.network.nodes[v].get('avg_risk', 0), 3)
            } for v in vessel_list]

            # Sort by risk
            vessels.sort(key=lambda x: x['total_risk'], reverse=True)

            community_data.append({
                'community_id': i + 1,
                'size': len(vessel_list),
                'total_risk_score': round(total_risk, 3),
                'avg_risk_score': round(avg_risk, 3),
                'total_events': total_events,
                'density': round(density, 3),
                'vessels': vessels,
                'suspicion_level': self._classify_community_suspicion(total_risk, len(vessel_list), density)
            })

        # Sort by total risk
        community_data.sort(key=lambda x: x['total_risk_score'], reverse=True)

        logger.info(f"Detected {len(community_data)} suspicious communities")

        return community_data

    def identify_coordinators(self) -> List[Dict[str, Any]]:
        """
        Identify potential coordinator vessels using centrality metrics.

        Returns:
            List of coordinator vessels with centrality scores
        """
        if self.network is None:
            raise ValueError("Network not built. Call build_network() first.")

        logger.info("Identifying coordinator vessels...")

        # Calculate centrality metrics
        degree_centrality = nx.degree_centrality(self.network)
        betweenness_centrality = nx.betweenness_centrality(self.network)

        # Combine metrics
        coordinators = []
        for node in self.network.nodes():
            # High betweenness = vessel bridges different groups (coordinator role)
            betweenness = betweenness_centrality.get(node, 0)
            degree = degree_centrality.get(node, 0)

            # Only include vessels with significant coordination role
            if betweenness > 0.01 or degree > 0.1:
                coordinators.append({
                    'mmsi': int(node),
                    'vessel_type': self.network.nodes[node].get('vessel_type', 'unknown'),
                    'betweenness_centrality': round(betweenness, 4),
                    'degree_centrality': round(degree, 4),
                    'connections': self.network.degree(node),
                    'event_count': self.network.nodes[node].get('event_count', 0),
                    'total_risk': round(self.network.nodes[node].get('total_risk', 0), 3),
                    'coordinator_score': round(betweenness * 100 + degree * 50, 2),
                    'role': self._classify_coordinator_role(betweenness, degree)
                })

        # Sort by coordinator score
        coordinators.sort(key=lambda x: x['coordinator_score'], reverse=True)

        logger.info(f"Identified {len(coordinators)} potential coordinators")

        return coordinators

    def identify_motherships(self) -> List[Dict[str, Any]]:
        """
        Identify potential mothership vessels.
        Motherships are non-fishing vessels with many connections to fishing vessels.

        Returns:
            List of potential mothership vessels
        """
        if self.network is None:
            raise ValueError("Network not built. Call build_network() first.")

        logger.info("Identifying potential mothership vessels...")

        motherships = []

        for node in self.network.nodes():
            is_fishing = self.network.nodes[node].get('is_fishing', True)

            # Look for non-fishing vessels with many fishing vessel connections
            if not is_fishing:
                neighbors = list(self.network.neighbors(node))

                if len(neighbors) >= 2:  # Connected to at least 2 other vessels
                    # Count fishing vessel connections
                    fishing_connections = sum(
                        1 for n in neighbors
                        if self.network.nodes[n].get('is_fishing', False)
                    )

                    if fishing_connections >= 2:  # Connected to at least 2 fishing vessels
                        # Calculate total encounters
                        total_encounters = sum(
                            self.network[node][n]['weight']
                            for n in neighbors
                        )

                        motherships.append({
                            'mmsi': int(node),
                            'vessel_type': self.network.nodes[node].get('vessel_type', 'unknown'),
                            'total_connections': len(neighbors),
                            'fishing_connections': fishing_connections,
                            'total_encounters': total_encounters,
                            'event_count': self.network.nodes[node].get('event_count', 0),
                            'total_risk': round(self.network.nodes[node].get('total_risk', 0), 3),
                            'mothership_score': round(fishing_connections * 10 + total_encounters * 5, 2)
                        })

        # Sort by mothership score
        motherships.sort(key=lambda x: x['mothership_score'], reverse=True)

        logger.info(f"Identified {len(motherships)} potential motherships")

        return motherships

    def _classify_community_suspicion(self, total_risk: float, size: int, density: float) -> str:
        """Classify community suspicion level."""
        avg_risk_per_vessel = total_risk / size if size > 0 else 0

        if avg_risk_per_vessel > 5 and density > 0.5:
            return "VERY_HIGH"
        elif avg_risk_per_vessel > 3 or density > 0.4:
            return "HIGH"
        elif avg_risk_per_vessel > 1.5 or density > 0.25:
            return "MEDIUM"
        else:
            return "LOW"

    def _classify_coordinator_role(self, betweenness: float, degree: float) -> str:
        """Classify the role of a coordinator vessel."""
        if betweenness > 0.1 and degree > 0.2:
            return "CENTRAL_COORDINATOR"
        elif betweenness > 0.05:
            return "BRIDGE_COORDINATOR"
        elif degree > 0.15:
            return "HUB_COORDINATOR"
        else:
            return "MINOR_COORDINATOR"

    def get_network_stats(self) -> Dict[str, Any]:
        """Get overall network statistics."""
        if self.network is None:
            raise ValueError("Network not built. Call build_network() first.")

        # Get connected components
        components = list(nx.connected_components(self.network))
        largest_component_size = max(len(c) for c in components) if components else 0

        return {
            'total_vessels': self.network.number_of_nodes(),
            'total_connections': self.network.number_of_edges(),
            'connected_components': len(components),
            'largest_component_size': largest_component_size,
            'average_degree': round(sum(dict(self.network.degree()).values()) / self.network.number_of_nodes(), 2) if self.network.number_of_nodes() > 0 else 0,
            'density': round(nx.density(self.network), 4)
        }
