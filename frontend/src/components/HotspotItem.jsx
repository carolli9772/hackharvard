import React from "react";

export const HotspotItem = ({ hotspot, onClick }) => {
  const severity =
    hotspot.avg_suspicion_score >= 0.7
      ? "#ff3838"
      : hotspot.avg_suspicion_score >= 0.5
      ? "#ffa500"
      : "#4ecdc4";

  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.05)",
        borderLeft: `4px solid ${severity}`,
        padding: "15px",
        marginBottom: "10px",
        borderRadius: "5px",
        // cursor: "pointer",
        transition: "all 0.2s",
      }}
      //   onMouseEnter={(e) =>
      //     (e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)")
      //   }
      //   onMouseLeave={(e) =>
      //     (e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)")
      //   }
      onClick={() => onClick && onClick(hotspot)}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "10px",
        }}
      >
        <span style={{ fontWeight: "bold", color: "#00d4ff" }}>
          📍 Grid: {hotspot.grid_id}
        </span>
        <span
          style={{
            background: `${severity}33`,
            padding: "3px 10px",
            borderRadius: "12px",
            fontSize: "0.9em",
            color: severity,
          }}
        >
          Score: {hotspot.avg_suspicion_score?.toFixed(3)}
        </span>
      </div>
      <div style={{ fontSize: "0.9em", color: "#ccc", marginBottom: "8px" }}>
        🗺️ Center: [{hotspot.center[0].toFixed(2)},{" "}
        {hotspot.center[1].toFixed(2)}]
      </div>
      <div style={{ fontSize: "0.9em", color: "#ccc" }}>
        📊 {hotspot.event_count} dark events | 🚢 {hotspot.unique_vessels}{" "}
        unique vessels
      </div>
    </div>
  );
};
