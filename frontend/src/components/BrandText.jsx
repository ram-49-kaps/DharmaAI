import React from "react";

export default function BrandText({ className = "", style = {}, color = "var(--text)" }) {
  return (
    <span 
      className={`brand-text ${className}`} 
      style={{
        fontFamily: "var(--font-heading)",
        fontWeight: "600",
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        ...style
      }}
    >
      <span style={{ color: color }}>Prakarna</span>
      <span style={{ color: "var(--primary)", fontWeight: "800" }}>AI</span>
    </span>
  );
}
