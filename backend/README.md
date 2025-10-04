# FishNet Backend - Illegal Fishing Detection System

**FishNet** detects illegal fishing via AIS silence patterns using advanced spatiotemporal analysis and network detection.

## 🎯 Overview

This backend system analyzes AIS (Automatic Identification System) data to:
- Detect "dark periods" when vessels turn off their tracking
- Correlate dark events with location, time, and nearby vessels
- Flag suspicious patterns indicative of illegal fishing
- Identify coordinated vessel networks and potential motherships

## 📊 Analysis Pipeline

### Step 1: Enhanced Dark Event Detection
**Script:** `enhanced_dark_detection.py`

Detects dark periods (AIS gaps > threshold) and enriches them with:
- Start/end timestamps and locations
- Regional classification
- Vessel information
- Fishing gear type (if applicable)

**Output:**
```json
{
  "mmsi": 231982000,
  "start": "2024-01-01T03:00:00Z",
  "end": "2024-01-01T05:30:00Z",
  "region": "Eastern Pacific",
  "location": [15.2, -88.0],
  "duration_hours": 2.5,
  "is_fishing_vessel": true
}
```

### Step 2: Vessel Proximity Index
**Script:** `proximity_index.py`

Builds a "who was near whom and when" dataset using spatial indexing (BallTree):
- Time-binned proximity detection (10-min windows)
- Distance-based vessel pairing (< 20 km)
- Haversine distance calculations

### Step 3: Dark Event Context Checking
**Script:** `dark_event_context.py`

Validates dark events by checking AIS coverage:
- Identifies vessels within 20 km during dark periods
- Calculates coverage reliability
- Assigns confidence scores based on nearby vessel transmissions

### Step 4: Multi-Factor Suspicion Scoring
**Script:** `suspicion_scoring.py`

Assigns suspicion scores (0-1) based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Dark gap length | 0.3 | Longer gaps = more suspicious |
| Coverage reliability | 0.2 | Low coverage = higher suspicion |
| Proximity to EEZ boundary | 0.2 | Near borders = higher risk |
| Proximity to fishing vessel | 0.2 | Co-occurrence with fishing fleet |
| Repeat offender | 0.1 | Frequency of dark events |

**Clustering:** Uses DBSCAN to identify dark zone hotspots and hexbin aggregation for heatmap visualization.

### Step 5: Graph-Based Network Detection
**Script:** `network_analysis.py`

Builds vessel network graph:
- **Nodes:** Vessels
- **Edges:** Co-occurrence during dark periods

**Metrics:**
- **Degree centrality:** Vessels with many connections
- **Betweenness centrality:** Potential coordinators/bridges
- **Community detection:** Identifies coordinated fleets (Louvain algorithm)
- **Transshipment detection:** Non-fishing vessels connected to multiple fishing vessels

### Step 6: Advanced Visualization
**Script:** `advanced_visualization.py`

Generates:
- Suspicion heatmaps (geographical distribution)
- Network visualizations (centrality analysis)
- Temporal pattern analysis
- Comprehensive JSON data package for frontend

### Step 7: Dataset Integration
**Script:** `dataset_analysis.py`

Cross-references dark events with:
- Fishing gear types (longlines, trawlers, purse seines, etc.)
- Marine protected areas (WDPA database)
- Fleet composition analysis

## 🚀 Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Run Analysis Pipeline

```bash
cd app

# Fast analysis (recommended for testing)
python run_pipeline.py

# Complete analysis (includes proximity index - slower)
python run_pipeline.py --full
```

### Start API Server

```bash
python api.py
```

API will be available at `http://localhost:5000`

## 🔌 API Endpoints

### Summary & Statistics
- `GET /api/summary` - Overall statistics
- `GET /api/network/stats` - Network analysis statistics

### Dark Events
- `GET /api/suspicious-events?limit=50&min_score=0.7&fishing_only=true`
- `GET /api/hotspots?limit=20` - Dark zone hotspots
- `GET /api/clusters?hotspots_only=true` - Spatial clusters

### Network Analysis
- `GET /api/communities?limit=10` - Suspicious vessel communities
- `GET /api/coordinators?limit=20` - Potential coordinator vessels
- `GET /api/motherships` - Potential mothership/transshipment vessels

### Vessel Details
- `GET /api/vessel/{mmsi}` - Detailed vessel information

### Search
- `GET /api/search?lat=15.2&lon=-88.0&radius_km=50&start_date=2024-01-01`

### Health
- `GET /api/health` - Server health check

## 📁 Output Files

### JSON Data Files
- `enhanced_dark_events.json` - Dark events with metadata
- `contextualized_dark_events.json` - Dark events with context
- `scored_dark_events.json` - Scored and clustered events
- `dark_zone_clusters.json` - Spatial clusters
- `dark_zone_hexbins.json` - Hexbin aggregation for heatmaps
- `vessel_communities.json` - Detected communities
- `centrality_scores.json` - Network centrality metrics
- `potential_motherships.json` - Transshipment vessel candidates
- `frontend_data_package.json` - Complete data package for frontend
- `dataset_analysis.json` - Fishing gear and protected area analysis

### Visualizations
- `suspicion_heatmap.png` - Geographical heatmap
- `network_viz.png` - Network analysis plots
- `temporal_analysis.png` - Temporal pattern analysis

### Network Graph
- `vessel_network.gexf` - Graph file (for Gephi/Cytoscape)

## 🛠 Individual Script Usage

### Run individual analysis steps:

```bash
# Step 1: Dark event detection
python enhanced_dark_detection.py

# Step 2: Proximity index
python proximity_index.py

# Step 3: Context checking
python dark_event_context.py

# Step 4: Scoring & clustering
python suspicion_scoring.py

# Step 5: Network analysis
python network_analysis.py

# Step 6: Visualization
python advanced_visualization.py

# Step 7: Dataset analysis
python dataset_analysis.py
```

## 📊 Data Requirements

### Required Dataset
- `AIS_2024_01_01.csv` - AIS tracking data with columns:
  - MMSI, BaseDateTime, LAT, LON, SOG, COG, Heading
  - VesselName, VesselType, Length, Width

### Optional Datasets
- Fishing gear CSVs: `drifting_longlines.csv`, `trawlers.csv`, etc.
- Protected areas: `WDPA_WDOECM_Oct2025_Public_marine_csv.csv`

## 🎨 Frontend Integration

The API provides RESTful endpoints that can be consumed by any frontend framework:

```javascript
// Example: Fetch suspicious events
fetch('http://localhost:5000/api/suspicious-events?min_score=0.7')
  .then(res => res.json())
  .then(data => {
    console.log(`Found ${data.count} suspicious events`);
    // Render on map/dashboard
  });
```

## 🔧 Configuration

Edit parameters in individual scripts:
- **Dark event threshold:** `threshold_minutes=10` (enhanced_dark_detection.py)
- **Proximity radius:** `distance_threshold_km=20` (proximity_index.py)
- **Clustering radius:** `eps_km=50` (suspicion_scoring.py)
- **Time windows:** `time_window_minutes=10` (proximity_index.py)

## 📈 Performance Notes

- **Proximity index** is the most computationally intensive step (O(n²) for large datasets)
- For datasets > 500k records, consider:
  - Using `--fast` mode (skips proximity index)
  - Sampling data for initial testing
  - Running on a server with sufficient RAM

## 🤝 Contributing

When adding new analysis modules:
1. Follow the existing pattern (load → process → save)
2. Output JSON for frontend consumption
3. Add endpoint to `api.py`
4. Update `run_pipeline.py`

## 📝 License

Part of the FishNet illegal fishing detection system - HackHarvard 2024
