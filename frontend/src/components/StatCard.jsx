import React from "react";

export const StatCard = ({ label, value, unit = "", icon = "" }) => (
  <div
    style={{
      background: "rgba(255, 255, 255, 0.1)",
      backdropFilter: "blur(10px)",
      borderRadius: "15px",
      padding: "25px",
      border: "1px solid rgba(255, 255, 255, 0.2)",
      transition: "transform 0.2s",
      cursor: "default",
    }}
    onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-5px)")}
    onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}
  >
    <div
      style={{
        color: "#aaa",
        fontSize: "0.9em",
        textTransform: "uppercase",
        letterSpacing: "1px",
        marginBottom: "10px",
      }}
    >
      {icon} {label}
    </div>
    <div
      style={{
        fontSize: "2.5em",
        fontWeight: "bold",
        color: "#00ff88",
      }}
    >
      {value}
      {unit}
    </div>
  </div>
);
