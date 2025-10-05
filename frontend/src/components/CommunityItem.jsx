import React from "react";

export const CommunityItem = ({ community, onClick }) => (
  <div
    style={{
      background: "rgba(255, 255, 255, 0.05)",
      borderLeft: community.is_suspicious_fleet
        ? "4px solid #ff3838"
        : "4px solid #00d4ff",
      padding: "15px",
      marginBottom: "10px",
      borderRadius: "5px",
      //   cursor: "pointer",
      transition: "all 0.2s",
    }}
    // onMouseEnter={(e) =>
    //   (e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)")
    // }
    // onMouseLeave={(e) =>
    //   (e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)")
    // }
    onClick={() => onClick && onClick(community)}
  >
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        marginBottom: "10px",
      }}
    >
      <span style={{ fontWeight: "bold", color: "#00d4ff" }}>
        🌐 Community {community.community_id}
        {community.is_suspicious_fleet && (
          <span style={{ color: "#ff3838", marginLeft: "10px" }}>
            ⚠️ SUSPICIOUS FLEET
          </span>
        )}
      </span>
      <span
        style={{
          background: "rgba(255, 59, 48, 0.3)",
          padding: "3px 10px",
          borderRadius: "12px",
          fontSize: "0.9em",
        }}
      >
        Avg Score: {community.avg_suspicion_score?.toFixed(3)}
      </span>
    </div>
    <div style={{ fontSize: "0.9em", color: "#ccc", marginBottom: "8px" }}>
      👥 {community.vessel_count} vessels | 🎣 {community.fishing_vessel_count}{" "}
      fishing vessels | 🔗 {community.internal_connections} connections
    </div>
    <div style={{ fontSize: "0.85em", color: "#888" }}>
      Key Vessels: {community.vessel_mmsis?.slice(0, 5).join(", ")}
      {community.vessel_mmsis?.length > 5 && "..."}
    </div>
  </div>
);
