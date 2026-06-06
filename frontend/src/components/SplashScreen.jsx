import React, { useEffect } from 'react';
import Logo from './Logo';

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
        <div className="splash-logo-wrapper">
          <Logo />
        </div>
        <div className="splash-loader">
          <div className="splash-loader-bar"></div>
        </div>
        <p className="splash-text">{text || "Preparing your legal workspace..."}</p>
      </div>
    </div>
  );
}
