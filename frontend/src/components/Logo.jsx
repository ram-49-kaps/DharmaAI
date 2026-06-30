import React from "react";

export default function Logo({ size = 24, className = "", variant }) {
  // If this is the new logo with built-in padding, we use a scale transform to make it legible
  return (
    <img 
      src={process.env.PUBLIC_URL + '/logo.png'} 
      alt="Prakarna AI Logo" 
      width={size} 
      height={size} 
      className={`logo-img ${className}`} 
      style={{ objectFit: "contain", transform: "scale(3.2) translateY(6%)" }}
    />
  );
}
