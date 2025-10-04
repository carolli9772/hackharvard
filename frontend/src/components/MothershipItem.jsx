import React from "react";

export const MothershipItem = ({ mothership, onClick }) => (
  <div
    style={{
      background: "rgba(255, 255, 255, 0.05)",
      borderLeft: "4px solid #ff3838",
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
    onClick={() => onClick && onClick(mothership)}
  >
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        marginBottom: "10px",
      }}
    >
      <span style={{ fontWeight: "bold", color: "#ff3838" }}>
        🚢 MOTHERSHIP CANDIDATE: {mothership.mmsi}
      </span>
      <span
        style={{
          background: "rgba(255, 59, 48, 0.3)",
          padding: "3px 10px",
          borderRadius: "12px",
          fontSize: "0.9em",
        }}
      >
        Suspicion: {mothership.total_suspicion?.toFixed(3)}
      </span>
    </div>
    <div style={{ fontSize: "0.9em", color: "#ccc", marginBottom: "8px" }}>
      🎣 Connected to {mothership.connected_fishing_vessels} fishing vessels |
      🔗 {mothership.total_connections} total connections
    </div>
    <div style={{ fontSize: "0.85em", color: "#888" }}>
      🎯 Betweenness Centrality: {mothership.betweenness_centrality?.toFixed(3)}{" "}
      |{mothership.vessel_name || "Unknown vessel"}
    </div>
  </div>
);
