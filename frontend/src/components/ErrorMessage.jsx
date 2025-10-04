import React from "react";

export const ErrorMessage = ({ message }) => (
  <div
    style={{
      background: "rgba(255, 59, 48, 0.2)",
      border: "1px solid #ff3b30",
      borderRadius: "10px",
      padding: "20px",
      margin: "20px 0",
      color: "#ff6b6b",
    }}
  >
    ⚠️ {message}
  </div>
);
