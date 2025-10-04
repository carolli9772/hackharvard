import React from "react";

export const EventItem = ({ event, onClick }) => {
  const score = event.total_score || 0;
  const confidence = event.confidence_score || 0;
  const suspicionClass =
    score >= 0.7 ? "#ff3838" : score >= 0.4 ? "#ffa500" : "#4ecdc4";
  const location = event.location
    ? `[${event.location[0].toFixed(2)}, ${event.location[1].toFixed(2)}]`
    : "Unknown";

  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.05)",
        borderLeft: `4px solid ${suspicionClass}`,
        padding: "15px",
        marginBottom: "10px",
        borderRadius: "5px",
        cursor: "pointer",
        transition: "all 0.2s",
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)")
      }
      onClick={() => onClick && onClick(event)}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "10px",
        }}
      >
        <span style={{ fontWeight: "bold", color: "#00d4ff" }}>
          MMSI: {event.mmsi}
        </span>
        <div style={{ display: "flex", gap: "10px" }}>
          <span
            style={{
              background: "rgba(255, 59, 48, 0.3)",
              padding: "3px 10px",
              borderRadius: "12px",
              fontSize: "0.85em",
            }}
          >
            Suspicion: {score.toFixed(3)}
          </span>
          <span
            style={{
              background: "rgba(0, 212, 255, 0.3)",
              padding: "3px 10px",
              borderRadius: "12px",
              fontSize: "0.85em",
            }}
          >
            Confidence: {confidence.toFixed(3)}
          </span>
        </div>
      </div>

      <div style={{ fontSize: "0.9em", color: "#ccc", marginBottom: "8px" }}>
        📍 {location} | 🌍 {event.region || "Unknown Region"}
      </div>

      <div style={{ fontSize: "0.9em", color: "#ccc", marginBottom: "8px" }}>
        ⏱️ {event.duration_hours?.toFixed(1)}h |
        {event.is_fishing_vessel ? " 🎣 Fishing Vessel" : " 🚢 Other Vessel"}
        {event.fishing_gear_types &&
          event.fishing_gear_types.length > 0 &&
          ` (${event.fishing_gear_types.join(", ")})`}
      </div>

      <div style={{ fontSize: "0.85em", color: "#888" }}>
        📅 {new Date(event.start).toLocaleString()} →{" "}
        {new Date(event.end).toLocaleString()}
      </div>

      {event.nearby_vessels_at_start > 0 && (
        <div
          style={{
            fontSize: "0.85em",
            color: "#ffa500",
            marginTop: "8px",
            padding: "5px 10px",
            background: "rgba(255, 165, 0, 0.1)",
            borderRadius: "5px",
          }}
        >
          ⚠️ {event.nearby_vessels_at_start} nearby vessels at start (
          {event.unique_nearby_vessels} unique)
        </div>
      )}
    </div>
  );
};
