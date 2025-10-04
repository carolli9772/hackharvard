import React from "react";

export const Section = ({ title, children }) => (
  <div
    style={{
      background: "rgba(255, 255, 255, 0.05)",
      backdropFilter: "blur(10px)",
      borderRadius: "15px",
      padding: "30px",
      marginBottom: "30px",
      border: "1px solid rgba(255, 255, 255, 0.1)",
    }}
  >
    <h2 style={{ fontSize: "1.5em", marginBottom: "20px", color: "#00d4ff" }}>
      {title}
    </h2>
    {children}
  </div>
);
