import React from "react";

export default function Logo({ size = 24, color = "currentColor", className = "" }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer abstract tech ring (AI edge computing constraint) */}
      <circle cx="50" cy="50" r="42" stroke={color} strokeWidth="6" strokeDasharray="16 12" />
      
      {/* Inner solid ring establishing core bounds */}
      <circle cx="50" cy="50" r="30" stroke={color} strokeWidth="5" />
      
      {/* 8-spoke Dharma Chakra (Ashoka Chakra analogue) intersecting the center node */}
      <path 
        d="M50 16 L50 84 M16 50 L84 50 M26 26 L74 74 M26 74 L74 26" 
        stroke={color} 
        strokeWidth="6" 
        strokeLinecap="round"
      />
      
      {/* Center glowing intelligence core */}
      <circle cx="50" cy="50" r="12" fill={color} />
    </svg>
  );
}
