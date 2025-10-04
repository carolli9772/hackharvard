import React from "react";

export const FilterButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    style={{
      background: active ? "#00d4ff" : "rgba(0, 212, 255, 0.2)",
      border: "1px solid #00d4ff",
      color: active ? "#0f2027" : "#00d4ff",
      padding: "10px 20px",
      borderRadius: "25px",
      cursor: "pointer",
      transition: "all 0.3s",
      fontSize: "1em",
      fontWeight: active ? "bold" : "normal",
    }}
    onMouseEnter={(e) => {
      if (!active) {
        e.currentTarget.style.background = "rgba(0, 212, 255, 0.3)";
      }
    }}
    onMouseLeave={(e) => {
      if (!active) {
        e.currentTarget.style.background = "rgba(0, 212, 255, 0.2)";
      }
    }}
  >
    {children}
  </button>
);
