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


# Calculate summary statistics from scored_dark_events
def calculate_summary_stats(events):
    """Calculate summary statistics from dark events."""
    if not events:
        return {}

    fishing_events = [e for e in events if e.get('is_fishing_vessel', False)]
    high_suspicion = [e for e in events if e.get('total_score', 0) >= 0.7]

    # Calculate average duration
    durations = [e.get('duration_hours', 0) for e in events if e.get('duration_hours')]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Count unique vessels
    unique_vessels = len(set(e.get('mmsi') for e in events if e.get('mmsi')))

    # Count hotspots (events in same grid cells)
    grid_cells = set()
    for event in events:
        if event.get('location'):
            lat, lon = event['location']
            # Round to 1 degree grid
            grid_id = f"{int(lat)},{int(lon)}"
            grid_cells.add(grid_id)

    return {
        'total_dark_events': len(events),
        'high_suspicion_events': len(high_suspicion),
        'fishing_vessel_events': len(fishing_events),
        'avg_duration_hours': round(avg_duration, 2),
        'total_vessels_involved': unique_vessels,
        'total_hotspots': len(grid_cells)
    }


# API Endpoints

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get summary statistics of dark event analysis."""
    events = load_json_file('scored_dark_events.json')
    if events:
        summary = calculate_summary_stats(events)
        return jsonify(summary)
    return jsonify({'error': 'Data not available'}), 404


@app.route('/api/suspicious-events', methods=['GET'])
def get_suspicious_events():
    """Get list of suspicious dark events with optional filters."""
    # Query parameters
    limit = request.args.get('limit', 50, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    fishing_only = request.args.get('fishing_only', 'false').lower() == 'true'

    events = load_json_file('scored_dark_events.json')
    if not events:
        return jsonify({'error': 'Data not available'}), 404

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

@app.route('/api/suspicious-events/top', methods=['GET'])
def get_top_suspicious_events():
    """Get top suspicious events sorted by score for map display."""
    limit = request.args.get('limit', 5000, type=int)

    events = load_json_file('scored_dark_events.json')
    if not events:
        return jsonify({'error': 'Data not available'}), 404

    # Sort by suspicion score (highest first)
    events.sort(key=lambda x: x.get('total_score', 0), reverse=True)

    # Apply limit
    events = events[:limit]

    return jsonify({
        'count': len(events),
        'events': events
    })

@app.route('/api/hotspots', methods=['GET'])
def get_hotspots():
    """Get dark zone hotspots (aggregated by grid cell)."""
    limit = request.args.get('limit', 20, type=int)

    events = load_json_file('scored_dark_events.json')
    if not events:
        return jsonify({'error': 'Data not available'}), 404

    # Aggregate events by 1-degree grid cells
    grid_map = {}
    for event in events:
        if not event.get('location'):
            continue

        lat, lon = event['location']
        grid_lat = round(lat)
        grid_lon = round(lon)
        grid_id = f"{grid_lat},{grid_lon}"

        if grid_id not in grid_map:
            grid_map[grid_id] = {
                'grid_id': grid_id,
                'center': [grid_lat, grid_lon],
                'event_count': 0,
                'total_score': 0,
                'vessels': set()
            }

        grid_map[grid_id]['event_count'] += 1
        grid_map[grid_id]['total_score'] += event.get('total_score', 0)
        if event.get('mmsi'):
            grid_map[grid_id]['vessels'].add(event['mmsi'])

    # Convert to list and calculate averages
    hotspots = []
    for grid_id, data in grid_map.items():
        hotspots.append({
            'grid_id': grid_id,
            'center': data['center'],
            'event_count': data['event_count'],
            'avg_suspicion_score': round(data['total_score'] / data['event_count'], 3),
            'unique_vessels': len(data['vessels'])
        })

    # Sort by event count
    hotspots.sort(key=lambda x: x['event_count'], reverse=True)

    return jsonify({
        'count': len(hotspots[:limit]),
        'hotspots': hotspots[:limit]
    })


@app.route('/api/vessel/<int:mmsi>', methods=['GET'])
def get_vessel_details(mmsi):
    """Get detailed information about a specific vessel."""
    events = load_json_file('scored_dark_events.json')
    if not events:
        return jsonify({'error': 'Data not available'}), 404

    # Find all events for this vessel
    vessel_events = [e for e in events if e.get('mmsi') == mmsi]

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


@app.route('/api/search', methods=['GET'])
def search_events():
    """Search dark events by location, time, or vessel attributes."""
    # Query parameters
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius_km = request.args.get('radius_km', 50, type=float)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    events = load_json_file('scored_dark_events.json')
    if not events:
        return jsonify({'error': 'Data not available'}), 404

    results = events

    # Filter by location if provided
    if lat is not None and lon is not None:
        def haversine_distance(lat1, lon1, lat2, lon2):
            from math import radians, sin, cos, sqrt, atan2
            R = 6371  # Earth radius in km

            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))

            return R * c

        results = [
            e for e in results
            if e.get('location') and haversine_distance(lat, lon, e['location'][0], e['location'][1]) <= radius_km
        ]

    # Filter by date range if provided
    if start_date:
        start = datetime.fromisoformat(start_date)
        results = [e for e in results if e.get('start') and datetime.fromisoformat(e['start']) >= start]

    if end_date:
        end = datetime.fromisoformat(end_date)
        results = [e for e in results if e.get('end') and datetime.fromisoformat(e['end']) <= end]

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
    print("Starting server on http://localhost:5001")
    print("\nAvailable endpoints:")
    print("  GET /api/summary              - Summary statistics")
    print("  GET /api/suspicious-events    - Suspicious dark events")
    print("  GET /api/hotspots             - Dark zone hotspots")
    print("  GET /api/vessel/<mmsi>        - Vessel details")
    print("  GET /api/search               - Search events")
    print("  GET /api/health               - Health check")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
