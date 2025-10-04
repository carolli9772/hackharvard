import React from "react";

export const CoordinatorItem = ({ coordinator, onClick }) => (
  <div
    style={{
      background: "rgba(255, 255, 255, 0.05)",
      borderLeft: "4px solid #ffa500",
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
    onClick={() => onClick && onClick(coordinator)}
  >
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        marginBottom: "10px",
      }}
    >
      <span style={{ fontWeight: "bold", color: "#ffa500" }}>
        🎯 MMSI: {coordinator.mmsi}
        {coordinator.is_fishing && " 🎣"}
      </span>
      <span
        style={{
          background: "rgba(255, 165, 0, 0.3)",
          padding: "3px 10px",
          borderRadius: "12px",
          fontSize: "0.9em",
        }}
      >
        Suspicion: {coordinator.total_suspicion?.toFixed(3)}
      </span>
    </div>
    <div style={{ fontSize: "0.9em", color: "#ccc", marginBottom: "8px" }}>
      🔗 Betweenness: {coordinator.betweenness_centrality?.toFixed(3)} | Degree:{" "}
      {coordinator.degree_centrality?.toFixed(3)} | Closeness:{" "}
      {coordinator.closeness_centrality?.toFixed(3)}
    </div>
    <div style={{ fontSize: "0.85em", color: "#888" }}>
      🌑 {coordinator.dark_event_count} dark events |{" "}
      {coordinator.vessel_name || "Unknown vessel"}
    </div>
  </div>
);
