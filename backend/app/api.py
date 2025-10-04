"""
Flask API for FishNet Frontend
Provides RESTful endpoints to access illegal fishing detection data.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access


# Helper function to load JSON data
def load_json_file(filename):
    """Load JSON file if it exists."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


# API Endpoints

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get summary statistics of dark event analysis."""
    package = load_json_file('frontend_data_package.json')
    if package:
        return jsonify(package['summary'])
    return jsonify({'error': 'Data not available'}), 404


@app.route('/api/suspicious-events', methods=['GET'])
def get_suspicious_events():
    """Get list of suspicious dark events with optional filters."""
    # Query parameters
    limit = request.args.get('limit', 50, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    fishing_only = request.args.get('fishing_only', 'false').lower() == 'true'

    package = load_json_file('frontend_data_package.json')
    if not package:
        return jsonify({'error': 'Data not available'}), 404

    events = package['top_suspicious_events']

    # Apply filters
    if min_score > 0:
        events = [e for e in events if e.get('total_score', 0) >= min_score]

    if fishing_only:
        events = [e for e in events if e.get('is_fishing_vessel', False)]

    # Apply limit
    events = events[:limit]

    return jsonify({
        'count': len(events),
        'events': events
    })


@app.route('/api/hotspots', methods=['GET'])
def get_hotspots():
    """Get dark zone hotspots (hexbin aggregation)."""
    limit = request.args.get('limit', 20, type=int)

    package = load_json_file('frontend_data_package.json')
    if not package:
        return jsonify({'error': 'Data not available'}), 404

    hotspots = package['dark_zone_hotspots'][:limit]

    return jsonify({
        'count': len(hotspots),
        'hotspots': hotspots
    })


@app.route('/api/communities', methods=['GET'])
def get_communities():
    """Get suspicious vessel communities."""
    limit = request.args.get('limit', 10, type=int)

    package = load_json_file('frontend_data_package.json')
    if not package:
        return jsonify({'error': 'Data not available'}), 404

    communities = package['suspicious_communities'][:limit]

    return jsonify({
        'count': len(communities),
        'communities': communities
    })


@app.route('/api/coordinators', methods=['GET'])
def get_coordinators():
    """Get potential coordinator vessels (high betweenness centrality)."""
    limit = request.args.get('limit', 20, type=int)

    package = load_json_file('frontend_data_package.json')
    if not package:
        return jsonify({'error': 'Data not available'}), 404

    coordinators = package['potential_coordinators'][:limit]

    return jsonify({
        'count': len(coordinators),
        'coordinators': coordinators
    })


@app.route('/api/motherships', methods=['GET'])
def get_motherships():
    """Get potential mothership/transshipment vessels."""
    package = load_json_file('frontend_data_package.json')
    if not package:
        return jsonify({'error': 'Data not available'}), 404

    motherships = package['potential_motherships']

    return jsonify({
        'count': len(motherships),
        'motherships': motherships
    })


@app.route('/api/vessel/<int:mmsi>', methods=['GET'])
def get_vessel_details(mmsi):
    """Get detailed information about a specific vessel."""
    # Load scored events
    dark_events = load_json_file('scored_dark_events.json')
    if not dark_events:
        return jsonify({'error': 'Data not available'}), 404

    # Find all events for this vessel
    vessel_events = [e for e in dark_events if e['mmsi'] == mmsi]

    if not vessel_events:
        return jsonify({'error': 'Vessel not found'}), 404

    # Get vessel basic info from first event
    vessel_info = {
        'mmsi': mmsi,
        'vessel_name': vessel_events[0].get('vessel_name', 'Unknown'),
        'is_fishing_vessel': vessel_events[0].get('is_fishing_vessel', False),
        'fishing_gear_types': vessel_events[0].get('fishing_gear_types', []),
        'total_dark_events': len(vessel_events),
        'avg_suspicion_score': round(sum(e.get('total_score', 0) for e in vessel_events) / len(vessel_events), 3),
        'max_suspicion_score': max(e.get('total_score', 0) for e in vessel_events),
        'events': vessel_events
    }

    return jsonify(vessel_info)


@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """Get spatial clusters of dark events."""
    clusters = load_json_file('dark_zone_clusters.json')
    if not clusters:
        return jsonify({'error': 'Data not available'}), 404

    # Filter only hotspots
    hotspots_only = request.args.get('hotspots_only', 'false').lower() == 'true'
    if hotspots_only:
        clusters = [c for c in clusters if c.get('is_hotspot', False)]

    return jsonify({
        'count': len(clusters),
        'clusters': clusters
    })


@app.route('/api/network/stats', methods=['GET'])
def get_network_stats():
    """Get network analysis statistics."""
    centrality = load_json_file('centrality_scores.json')
    communities = load_json_file('vessel_communities.json')

    if not centrality or not communities:
        return jsonify({'error': 'Data not available'}), 404

    stats = {
        'total_vessels': len(centrality),
        'total_communities': len(communities),
        'avg_degree_centrality': round(sum(v['degree_centrality'] for v in centrality) / len(centrality), 4),
        'avg_betweenness_centrality': round(sum(v['betweenness_centrality'] for v in centrality) / len(centrality), 4),
        'suspicious_fleets': sum(1 for c in communities if c.get('is_suspicious_fleet', False))
    }

    return jsonify(stats)


@app.route('/api/search', methods=['GET'])
def search_events():
    """Search dark events by location, time, or vessel attributes."""
    # Query parameters
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius_km = request.args.get('radius_km', 50, type=float)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    dark_events = load_json_file('scored_dark_events.json')
    if not dark_events:
        return jsonify({'error': 'Data not available'}), 404

    results = dark_events

    # Filter by location if provided
    if lat is not None and lon is not None:
        from proximity_index import haversine_distance
        results = [
            e for e in results
            if haversine_distance(lat, lon, e['location'][0], e['location'][1]) <= radius_km
        ]

    # Filter by date range if provided
    if start_date:
        start = datetime.fromisoformat(start_date)
        results = [e for e in results if datetime.fromisoformat(e['start']) >= start]

    if end_date:
        end = datetime.fromisoformat(end_date)
        results = [e for e in results if datetime.fromisoformat(e['end']) <= end]

    return jsonify({
        'count': len(results),
        'events': results[:100]  # Limit to 100 results
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("\n=== FishNet API Server ===")
    print("Starting server on http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET /api/summary              - Summary statistics")
    print("  GET /api/suspicious-events    - Suspicious dark events")
    print("  GET /api/hotspots             - Dark zone hotspots")
    print("  GET /api/communities          - Suspicious vessel communities")
    print("  GET /api/coordinators         - Potential coordinator vessels")
    print("  GET /api/motherships          - Potential mothership vessels")
    print("  GET /api/vessel/<mmsi>        - Vessel details")
    print("  GET /api/clusters             - Spatial clusters")
    print("  GET /api/network/stats        - Network statistics")
    print("  GET /api/search               - Search events")
    print("  GET /api/health               - Health check")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
