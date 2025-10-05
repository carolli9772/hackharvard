import React from "react";

export const SearchBar = ({ value, onChange, placeholder = "Search..." }) => (
  <div style={{ marginBottom: "20px" }}>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: "100%",
        padding: "12px 20px",
        background: "rgba(255, 255, 255, 0.05)",
        border: "1px solid rgba(0, 212, 255, 0.3)",
        borderRadius: "8px",
        color: "#fff",
        fontSize: "1em",
        outline: "none",
      }}
      onFocus={(e) => (e.currentTarget.style.borderColor = "#00d4ff")}
      onBlur={(e) =>
        (e.currentTarget.style.borderColor = "rgba(0, 212, 255, 0.3)")
      }
    />
  </div>
);
