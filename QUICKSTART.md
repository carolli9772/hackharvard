# 🚀 FishNet Quick Start Guide

Get FishNet illegal fishing detection running in **5 minutes**!

---

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

---

## Step 1: Clone & Navigate

```bash
cd /path/to/hackharvard-main
git checkout maureen-fishnet-analysis
```

---

## Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Required packages:**
- pandas, numpy
- scipy, scikit-learn
- networkx
- matplotlib, seaborn
- flask, flask-cors

---

## Step 3: Run the Analysis Pipeline

### Option A: Fast Mode (Recommended for Testing)
```bash
cd app
python run_pipeline.py
```

**Runs in ~3-5 minutes** (skips proximity index)

### Option B: Full Analysis
```bash
python run_pipeline.py --full
```

**Runs in ~10-20 minutes** (includes proximity index)

**What happens:**
1. ✅ Enhanced dark event detection
2. ✅ Vessel proximity indexing (full mode only)
3. ✅ Context validation
4. ✅ Suspicion scoring & clustering
5. ✅ Network analysis
6. ✅ Visualization generation
7. ✅ Dataset cross-referencing

---

## Step 4: Start the API Server

```bash
python api.py
```

**Server starts on:** `http://localhost:5000`

**Test it:**
```bash
curl http://localhost:5000/api/health
```

---

## Step 5: Open the Dashboard

### Option A: Direct Open
```bash
open ../frontend/example_dashboard.html
```

### Option B: Serve with Python
```bash
cd ../frontend
python -m http.server 8000
# Open http://localhost:8000/example_dashboard.html
```

---

## 🎯 What You'll See

### Dashboard Shows:
- 📊 **Summary Statistics**
  - Total dark events
  - High suspicion events
  - Fishing vessel count
  - Suspicious communities
  - Potential motherships

- ⚠️ **Top Suspicious Events**
  - Filterable by suspicion level
  - Fishing vessels only option
  - Score, location, duration

- 🌐 **Vessel Networks**
  - Detected communities
  - Network connections

---

## 📊 Using the API

### Get Summary
```bash
curl http://localhost:5000/api/summary
```

### Get Suspicious Events (High Suspicion Only)
```bash
curl "http://localhost:5000/api/suspicious-events?min_score=0.7&limit=10"
```

### Get Dark Zone Hotspots
```bash
curl "http://localhost:5000/api/hotspots?limit=20"
```

### Search Near Location
```bash
curl "http://localhost:5000/api/search?lat=15.2&lon=-88.0&radius_km=50"
```

### Get Vessel Details
```bash
curl http://localhost:5000/api/vessel/367305420
```

---

## 📁 Output Files

After running the pipeline, find these files in `/backend/app/`:

### JSON Data Files
```
enhanced_dark_events.json          # Dark events with metadata
contextualized_dark_events.json    # With coverage context
scored_dark_events.json            # Suspicion scores
dark_zone_clusters.json            # Spatial clusters
dark_zone_hexbins.json            # Heatmap data
vessel_communities.json            # Network communities
centrality_scores.json             # Centrality metrics
potential_motherships.json         # Transshipment vessels
frontend_data_package.json         # 👈 Main frontend data
dataset_analysis.json              # Gear type analysis
```

### Visualizations
```
suspicion_heatmap.png             # Geographic heatmap
network_viz.png                   # Network graphs
temporal_analysis.png             # Temporal patterns
```

### Network Graph
```
vessel_network.gexf               # For Gephi/Cytoscape
```

---

## 🔧 Customize Analysis

Edit these parameters in the scripts:

### Dark Event Threshold
**File:** `enhanced_dark_detection.py`
```python
dark_events = detect_enhanced_dark_events(df, threshold_minutes=10)
# Change to 15, 20, 30 minutes, etc.
```

### Proximity Distance
**File:** `proximity_index.py`
```python
proximity_events = build_proximity_index(
    df,
    time_window_minutes=10,      # Time window
    distance_threshold_km=20     # Distance threshold
)
```

### Clustering Radius
**File:** `suspicion_scoring.py`
```python
clustered_events, cluster_summary = cluster_dark_zones(
    scored_events,
    eps_km=50,        # Cluster radius
    min_samples=3     # Minimum points
)
```

---

## 🐛 Troubleshooting

### Error: "Module not found"
```bash
pip install -r requirements.txt
```

### Error: "File not found" during pipeline
Make sure AIS data exists:
```bash
ls ../../datasets/AIS_2024_01_01.csv
```

### API returns 404 errors
1. Check if `frontend_data_package.json` exists
2. Re-run the pipeline: `python run_pipeline.py`

### Frontend shows "CORS error"
Make sure API is running with CORS enabled (already configured in `api.py`)

### Pipeline is too slow
Use fast mode:
```bash
python run_pipeline.py  # Default is fast
```

---

## 📚 Next Steps

### 1. **Explore the API**
See all endpoints: `/backend/README.md`

### 2. **Customize Scoring**
Edit weights in `suspicion_scoring.py`:
```python
duration_score = min(event['duration_hours'] / 6.0, 1.0) * 0.3  # Change 0.3
coverage_score = (1 - event.get('coverage_reliability', 0.5)) * 0.2  # Change 0.2
# etc.
```

### 3. **Add Map Visualization**
Integrate Leaflet.js or deck.gl in `example_dashboard.html`:
```javascript
// Use hexbin_data from API to render heatmap
fetch('http://localhost:5000/api/hotspots')
  .then(res => res.json())
  .then(data => {
    // Render on map
  });
```

### 4. **Build Custom Frontend**
Use React, Vue, or your framework of choice:
```javascript
// Example with React
import { useEffect, useState } from 'react';

function Dashboard() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    fetch('http://localhost:5000/api/suspicious-events?limit=50')
      .then(res => res.json())
      .then(data => setEvents(data.events));
  }, []);

  return (
    <div>
      {events.map(event => (
        <EventCard key={event.mmsi} event={event} />
      ))}
    </div>
  );
}
```

### 5. **Deploy to Production**
```bash
# Use gunicorn for production
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

---

## 🎓 Learning Resources

1. **Full Documentation:** `/backend/README.md`
2. **System Overview:** `/FISHNET_SUMMARY.md`
3. **API Endpoints:** Check `api.py` for all routes
4. **Analysis Logic:** Each script has detailed docstrings

---

## 💡 Tips

1. **Start with fast mode** to get a feel for the system
2. **Check `frontend_data_package.json`** - it has all the key insights
3. **Use the API `/api/summary` endpoint** for quick stats
4. **Filter events** with `min_score=0.7` to see only highly suspicious ones
5. **Export network graph** (`vessel_network.gexf`) to Gephi for advanced visualization

---

## ✅ Success Checklist

- [ ] Python dependencies installed
- [ ] Pipeline runs successfully
- [ ] JSON output files generated
- [ ] API server starts on port 5000
- [ ] Dashboard loads and shows data
- [ ] API endpoints respond correctly

---

## 🆘 Need Help?

1. **Check logs:** Pipeline prints detailed progress
2. **Test API:** `curl http://localhost:5000/api/health`
3. **Verify data:** Check if AIS CSV exists
4. **Review README:** `/backend/README.md` has troubleshooting

---

## 🎉 You're Ready!

Your FishNet illegal fishing detection system is now running!

**Next:** Connect your frontend, customize visualizations, and start detecting suspicious vessel behavior.

---

**Built with ❤️ for HackHarvard 2024**
**Branch:** `maureen-fishnet-analysis`
