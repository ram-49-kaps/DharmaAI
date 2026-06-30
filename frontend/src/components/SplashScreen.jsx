import React, { useEffect } from 'react';
import Logo from './Logo';
import BrandText from './BrandText';

export default function SplashScreen({ text, onComplete }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, 2500); // 2.5 seconds splash screen
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="splash-screen">
      <div className="splash-content">
        <div className="splash-logo-wrapper" style={{ marginBottom: "20px" }}>
          <Logo size={80} variant="full" />
        </div>
        <BrandText style={{ fontSize: "1.8rem", marginBottom: "30px" }} />
        <div className="splash-loader">
          <div className="splash-loader-bar"></div>
        </div>
        <p className="splash-text">{text || "Preparing your legal workspace..."}</p>
      </div>
    </div>
  );
}
