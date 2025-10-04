import React, { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  CircleMarker,
  Circle,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Custom marker icons for different event types
const createCustomIcon = (color, icon) => {
  return L.divIcon({
    className: "custom-marker",
    html: `
      <div style="
        background: ${color};
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        font-size: 16px;
      ">
        ${icon}
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
};

const getEventIcon = (event) => {
  const score = event.total_score || 0;

  // Mothership or high-connection vessels
  if (event.nearby_vessels_at_start > 10) {
    return createCustomIcon("#ff3838", "🚢");
  }

  // Fishing vessels
  if (event.is_fishing_vessel) {
    if (score >= 0.7) {
      return createCustomIcon("#ff3838", "🎣");
    } else if (score >= 0.5) {
      return createCustomIcon("#ffa500", "🎣");
    } else {
      return createCustomIcon("#4ecdc4", "🎣");
    }
  }

  // Other vessels by suspicion level
  if (score >= 0.7) {
    return createCustomIcon("#ff3838", "⚠️");
  } else if (score >= 0.5) {
    return createCustomIcon("#ffa500", "⚠️");
  } else {
    return createCustomIcon("#4ecdc4", "⚠️");
  }
};

export const EventMap = ({ events, hotspots, onEventClick }) => {
  const [mapCenter] = useState([20, -30]); // Atlantic Ocean center
  const [mapZoom] = useState(3);
  const [showHotspots, setShowHotspots] = useState(true);
  const [showEvents, setShowEvents] = useState(true);
  const [filterLevel, setFilterLevel] = useState("all"); // all, high, medium, low

  const filteredEvents = events.filter((event) => {
    const score = event.total_score || 0;
    if (filterLevel === "high") return score >= 0.7;
    if (filterLevel === "medium") return score >= 0.4 && score < 0.7;
    if (filterLevel === "low") return score < 0.4;
    return true;
  });

  const getHotspotColor = (score) => {
    if (score >= 0.7) return "#ff3838";
    if (score >= 0.5) return "#ffa500";
    return "#4ecdc4";
  };

  return (
    <div style={{ position: "relative" }}>
      {/* Map Controls */}
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
        }}
      >
        <div
          style={{ marginBottom: "10px", color: "#00d4ff", fontWeight: "bold" }}
        >
          Map Controls
        </div>

        <div style={{ marginBottom: "10px" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer",
              color: "#fff",
            }}
          >
            <input
              type="checkbox"
              checked={showEvents}
              onChange={(e) => setShowEvents(e.target.checked)}
              style={{ cursor: "pointer" }}
            />
            Show Events
          </label>
        </div>

        <div style={{ marginBottom: "10px" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer",
              color: "#fff",
            }}
          >
            <input
              type="checkbox"
              checked={showHotspots}
              onChange={(e) => setShowHotspots(e.target.checked)}
              style={{ cursor: "pointer" }}
            />
            Show Hotspots
          </label>
        </div>

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
            }}
          >
            <option value="all">All Events</option>
            <option value="high">High Risk (≥0.7)</option>
            <option value="medium">Medium Risk (0.4-0.7)</option>
            <option value="low">Low Risk (&lt;0.4)</option>
          </select>
        </div>

        {/* Legend */}
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
            Legend
          </div>
          <div style={{ fontSize: "0.8em", color: "#ccc" }}>
            <div style={{ marginBottom: "5px" }}>🎣 Fishing Vessel</div>
            <div style={{ marginBottom: "5px" }}>🚢 High Connections</div>
            <div style={{ marginBottom: "5px" }}>⚠️ Other Vessel</div>
            <div
              style={{
                marginTop: "10px",
                paddingTop: "10px",
                borderTop: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "5px",
                }}
              >
                <div
                  style={{
                    width: "12px",
                    height: "12px",
                    background: "#ff3838",
                    borderRadius: "50%",
                  }}
                ></div>
                High Risk
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "5px",
                }}
              >
                <div
                  style={{
                    width: "12px",
                    height: "12px",
                    background: "#ffa500",
                    borderRadius: "50%",
                  }}
                ></div>
                Medium Risk
              </div>
              <div
                style={{ display: "flex", alignItems: "center", gap: "8px" }}
              >
                <div
                  style={{
                    width: "12px",
                    height: "12px",
                    background: "#4ecdc4",
                    borderRadius: "50%",
                  }}
                ></div>
                Low Risk
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: "10px", fontSize: "0.75em", color: "#666" }}>
          Showing {filteredEvents.length} of {events.length} events
        </div>
      </div>

      {/* Map */}
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: "600px", width: "100%", borderRadius: "10px" }}
        scrollWheelZoom={true}
      >
        {/* Base Map Tile Layer - Dark Theme */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Hotspots - Show as circles */}
        {showHotspots &&
          hotspots?.map((hotspot, idx) => (
            <Circle
              key={`hotspot-${idx}`}
              center={[hotspot.center[0], hotspot.center[1]]}
              radius={50000} // 50km radius
              pathOptions={{
                color: getHotspotColor(hotspot.avg_suspicion_score),
                fillColor: getHotspotColor(hotspot.avg_suspicion_score),
                fillOpacity: 0.2,
                weight: 2,
              }}
            >
              <Popup>
                <div style={{ color: "#000" }}>
                  <strong>Dark Zone Hotspot</strong>
                  <br />
                  Grid: {hotspot.grid_id}
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

        {/* Events - Show as markers */}
        {showEvents &&
          filteredEvents?.map((event, idx) => {
            if (!event.location || event.location.length !== 2) return null;

            return (
              <Marker
                key={`event-${idx}`}
                position={[event.location[0], event.location[1]]}
                icon={getEventIcon(event)}
                eventHandlers={{
                  click: () => onEventClick && onEventClick(event),
                }}
              >
                <Popup>
                  <div style={{ color: "#000", minWidth: "200px" }}>
                    <strong style={{ fontSize: "1.1em", color: "#00d4ff" }}>
                      MMSI: {event.mmsi}
                    </strong>
                    <br />
                    <br />

                    <div style={{ marginBottom: "8px" }}>
                      <strong>Suspicion Score:</strong>{" "}
                      {event.total_score?.toFixed(3)}
                      <br />
                      <strong>Confidence:</strong>{" "}
                      {event.confidence_score?.toFixed(3)}
                    </div>

                    <div style={{ marginBottom: "8px" }}>
                      <strong>Type:</strong>{" "}
                      {event.is_fishing_vessel ? "🎣 Fishing" : "🚢 Other"}
                      <br />
                      {event.fishing_gear_types?.length > 0 && (
                        <>
                          <strong>Gear:</strong>{" "}
                          {event.fishing_gear_types.join(", ")}
                          <br />
                        </>
                      )}
                    </div>

                    <div style={{ marginBottom: "8px" }}>
                      <strong>Duration:</strong>{" "}
                      {event.duration_hours?.toFixed(1)} hours
                      <br />
                      <strong>Region:</strong> {event.region || "Unknown"}
                    </div>

                    {event.nearby_vessels_at_start > 0 && (
                      <div
                        style={{
                          background: "#fff3cd",
                          padding: "5px",
                          borderRadius: "3px",
                          marginTop: "8px",
                        }}
                      >
                        ⚠️ {event.nearby_vessels_at_start} nearby vessels
                        <br />({event.unique_nearby_vessels} unique)
                      </div>
                    )}

                    <div
                      style={{
                        marginTop: "10px",
                        fontSize: "0.85em",
                        color: "#666",
                        borderTop: "1px solid #ddd",
                        paddingTop: "8px",
                      }}
                    >
                      {new Date(event.start).toLocaleString()}
                      <br />→ {new Date(event.end).toLocaleString()}
                    </div>

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
