import React, { useState, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Component to track zoom changes
function ZoomTracker({ onZoomChange }) {
  const map = useMapEvents({
    zoomend: () => {
      onZoomChange(map.getZoom());
    },
  });

  // Set initial zoom
  React.useEffect(() => {
    onZoomChange(map.getZoom());
  }, []);

  return null;
}

const createCustomIcon = (color, icon) => {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="background: ${color}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 16px;">${icon}</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
};

const createClusterIcon = (count, avgScore) => {
  const size = Math.min(60, 30 + Math.log(count) * 5);
  const color =
    avgScore >= 0.7 ? "#ff3838" : avgScore >= 0.5 ? "#ffa500" : "#4ecdc4";

  return L.divIcon({
    className: "cluster-marker",
    html: `<div style="background: ${color}; width: ${size}px; height: ${size}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 4px solid white; box-shadow: 0 3px 12px rgba(0,0,0,0.4); font-weight: bold; color: white; font-size: ${Math.min(
      18,
      12 + Math.log(count)
    )}px;">${count}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
};

const getEventIcon = (event) => {
  const score = event.total_score || 0;
  if (event.nearby_vessels_at_start > 10)
    return createCustomIcon("#ff3838", "🚢");
  if (event.is_fishing_vessel) {
    if (score >= 0.7) return createCustomIcon("#ff3838", "🎣");
    if (score >= 0.5) return createCustomIcon("#ffa500", "🎣");
    return createCustomIcon("#4ecdc4", "🎣");
  }
  if (score >= 0.7) return createCustomIcon("#ff3838", "⚠️");
  if (score >= 0.5) return createCustomIcon("#ffa500", "⚠️");
  return createCustomIcon("#4ecdc4", "⚠️");
};

export const EventMap = ({ events, hotspots, onEventClick }) => {
  const [showHotspots, setShowHotspots] = useState(true);
  const [showEvents, setShowEvents] = useState(true);
  const [filterLevel, setFilterLevel] = useState("all");
  const [currentZoom, setCurrentZoom] = useState(3);

  // Cluster events based on grid size (changes with zoom)
  const clusteredData = useMemo(() => {
    // Grid precision based on zoom level
    let precision = 0.5; // degrees
    if (currentZoom >= 6) precision = 0.2;
    if (currentZoom >= 8) precision = 0.1;
    if (currentZoom >= 10) precision = 0.05;
    if (currentZoom >= 12) precision = 0; // No clustering, show individual events

    const clusters = {};
    const filteredEvents = events.filter((event) => {
      if (!event.location) return false;
      const score = event.total_score || 0;
      if (filterLevel === "high") return score >= 0.7;
      if (filterLevel === "medium") return score >= 0.4 && score < 0.7;
      if (filterLevel === "low") return score < 0.4;
      return true;
    });

    // If zoomed in enough, return individual events
    if (precision === 0) {
      return { clusters: [], individuals: filteredEvents };
    }

    // Otherwise, cluster by grid
    filteredEvents.forEach((event) => {
      const [lat, lon] = event.location;
      const gridLat = Math.round(lat / precision) * precision;
      const gridLon = Math.round(lon / precision) * precision;
      const key = `${gridLat.toFixed(3)},${gridLon.toFixed(3)}`;

      if (!clusters[key]) {
        clusters[key] = {
          location: [gridLat, gridLon],
          events: [],
          totalScore: 0,
        };
      }

      clusters[key].events.push(event);
      clusters[key].totalScore += event.total_score || 0;
    });

    // Convert to array
    const clusterArray = Object.values(clusters).map((cluster) => ({
      location: cluster.location,
      count: cluster.events.length,
      avgScore: cluster.totalScore / cluster.events.length,
      events: cluster.events,
    }));

    return { clusters: clusterArray, individuals: [] };
  }, [events, filterLevel, currentZoom]);

  const getHotspotColor = (score) => {
    if (score >= 0.7) return "#ff3838";
    if (score >= 0.5) return "#ffa500";
    return "#4ecdc4";
  };

  return (
    <div style={{ position: "relative" }}>
      <div
        style={{
          position: "absolute",
          top: "10px",
          right: "10px",
          zIndex: 1000,
          background: "rgba(15, 32, 39, 0.95)",
          padding: "15px",
          borderRadius: "10px",
          border: "1px solid rgba(0, 212, 255, 0.3)",
          maxWidth: "220px",
        }}
      >
        <div
          style={{ marginBottom: "10px", color: "#00d4ff", fontWeight: "bold" }}
        >
          Map Controls
        </div>

        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "10px",
            cursor: "pointer",
            color: "#fff",
            fontSize: "0.9em",
          }}
        >
          <input
            type="checkbox"
            checked={showEvents}
            onChange={(e) => setShowEvents(e.target.checked)}
          />
          Show Events
        </label>

        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "10px",
            cursor: "pointer",
            color: "#fff",
            fontSize: "0.9em",
          }}
        >
          <input
            type="checkbox"
            checked={showHotspots}
            onChange={(e) => setShowHotspots(e.target.checked)}
          />
          Show Hotspots
        </label>

        <div
          style={{
            marginTop: "15px",
            paddingTop: "15px",
            borderTop: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          <div
            style={{ color: "#aaa", fontSize: "0.85em", marginBottom: "8px" }}
          >
            Filter by Risk
          </div>
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            style={{
              background: "rgba(255, 255, 255, 0.1)",
              border: "1px solid #00d4ff",
              color: "#fff",
              padding: "5px 10px",
              borderRadius: "5px",
              cursor: "pointer",
              width: "100%",
              fontSize: "0.85em",
            }}
          >
            <option value="all">All Events</option>
            <option value="high">High Risk (≥0.7)</option>
            <option value="medium">Medium (0.4-0.7)</option>
            <option value="low">Low (&lt;0.4)</option>
          </select>
        </div>

        <div
          style={{
            marginTop: "10px",
            fontSize: "0.75em",
            color: "#00d4ff",
            borderTop: "1px solid rgba(255,255,255,0.1)",
            paddingTop: "10px",
          }}
        >
          {clusteredData.individuals.length > 0
            ? `${clusteredData.individuals.length} individual events`
            : `${clusteredData.clusters.length} clusters`}
          <div style={{ color: "#666", marginTop: "3px" }}>
            Zoom {currentZoom} | Total: {events.length.toLocaleString()}
          </div>
          {currentZoom < 12 && (
            <div
              style={{ color: "#ffa500", marginTop: "5px", fontSize: "0.85em" }}
            >
              Zoom in to see individual events
            </div>
          )}
        </div>
      </div>

      <MapContainer
        center={[20, -30]}
        zoom={3}
        style={{ height: "600px", width: "100%", borderRadius: "10px" }}
        scrollWheelZoom={true}
      >
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        <ZoomTracker onZoomChange={setCurrentZoom} />

        {/* Hotspots */}
        {showHotspots &&
          hotspots?.map((hotspot, idx) => (
            <Circle
              key={`hotspot-${idx}`}
              center={[hotspot.center[0], hotspot.center[1]]}
              radius={50000}
              pathOptions={{
                color: getHotspotColor(hotspot.avg_suspicion_score),
                fillColor: getHotspotColor(hotspot.avg_suspicion_score),
                fillOpacity: 0.15,
                weight: 2,
              }}
            >
              <Popup>
                <div style={{ color: "#000" }}>
                  <strong>Hotspot {hotspot.grid_id}</strong>
                  <br />
                  Events: {hotspot.event_count}
                  <br />
                  Vessels: {hotspot.unique_vessels}
                  <br />
                  Avg Score: {hotspot.avg_suspicion_score?.toFixed(3)}
                </div>
              </Popup>
            </Circle>
          ))}

        {/* Event Clusters (when zoomed out) */}
        {showEvents &&
          clusteredData.clusters.map((cluster, idx) => (
            <Marker
              key={`cluster-${idx}`}
              position={cluster.location}
              icon={createClusterIcon(cluster.count, cluster.avgScore)}
            >
              <Popup>
                <div style={{ color: "#000", minWidth: "180px" }}>
                  <strong style={{ color: "#00d4ff" }}>
                    Cluster of {cluster.count} Events
                  </strong>
                  <br />
                  <br />
                  <strong>Avg Score:</strong> {cluster.avgScore.toFixed(3)}
                  <br />
                  <strong>Location:</strong> [{cluster.location[0].toFixed(2)},{" "}
                  {cluster.location[1].toFixed(2)}]<br />
                  <div
                    style={{
                      marginTop: "10px",
                      fontSize: "0.9em",
                      color: "#666",
                    }}
                  >
                    Zoom in to see individual events
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

        {/* Individual Events (when zoomed in) */}
        {showEvents &&
          clusteredData.individuals.map((event, idx) => {
            if (!event.location || event.location.length !== 2) return null;
            return (
              <Marker
                key={`event-${event.mmsi}-${idx}`}
                position={[event.location[0], event.location[1]]}
                icon={getEventIcon(event)}
              >
                <Popup>
                  <div style={{ color: "#000", minWidth: "200px" }}>
                    <strong style={{ color: "#00d4ff" }}>
                      MMSI: {event.mmsi}
                    </strong>
                    <br />
                    <br />
                    <strong>Score:</strong> {event.total_score?.toFixed(3)}
                    <br />
                    <strong>Confidence:</strong>{" "}
                    {event.confidence_score?.toFixed(3)}
                    <br />
                    <strong>Type:</strong>{" "}
                    {event.is_fishing_vessel ? "🎣 Fishing" : "🚢 Other"}
                    <br />
                    <strong>Duration:</strong>{" "}
                    {event.duration_hours?.toFixed(1)}h<br />
                    <strong>Region:</strong> {event.region || "Unknown"}
                    <br />
                    {event.nearby_vessels_at_start > 0 && (
                      <div
                        style={{
                          background: "#fff3cd",
                          padding: "5px",
                          borderRadius: "3px",
                          marginTop: "8px",
                          fontSize: "0.85em",
                        }}
                      >
                        ⚠️ {event.nearby_vessels_at_start} nearby vessels
                      </div>
                    )}
                    <button
                      onClick={() => onEventClick && onEventClick(event)}
                      style={{
                        marginTop: "10px",
                        background: "#00d4ff",
                        border: "none",
                        padding: "8px 15px",
                        borderRadius: "5px",
                        cursor: "pointer",
                        width: "100%",
                        fontWeight: "bold",
                        color: "#fff",
                      }}
                    >
                      View Full Details
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>
    </div>
  );
};
