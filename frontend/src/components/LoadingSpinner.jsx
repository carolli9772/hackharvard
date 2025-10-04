import React from "react";

export const LoadingSpinner = ({ message = "Loading..." }) => (
  <div
    style={{
      textAlign: "center",
      padding: "40px",
      color: "#aaa",
      fontSize: "1.2em",
    }}
  >
    <div
      style={{
        width: "40px",
        height: "40px",
        border: "4px solid rgba(0, 212, 255, 0.3)",
        borderTop: "4px solid #00d4ff",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
        margin: "0 auto 20px",
      }}
    />
    {message}
  </div>
);
