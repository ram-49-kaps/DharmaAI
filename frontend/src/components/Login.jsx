import React, { useState } from "react";
import { signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../firebase/config";
import { Scale, ScrollText, BrainCircuit, BookOpen, GraduationCap, Mail } from "lucide-react";
import Logo from "./Logo";
import AuthShowcase from "./AuthShowcase";

export default function Login({ onSwitchToSignUp }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);

  const handleEmail = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setError(friendlyError(err.code));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError("");
    setLoading(true);
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      setError(friendlyError(err.code));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-split-page">
      {/* ── Left: Login Form ──────────────────────────────── */}
      <div className="auth-left">
        <div className="auth-left-inner">
          {/* Brand */}
          <div className="auth-brand-top">
            <Logo size={28} />
            <span className="auth-brand-name">DharmaAI</span>
          </div>

          {/* Heading */}
          <div className="auth-heading">
            <div className="auth-icon-wrap">
              <Logo size={36} />
            </div>
            <h1>AI-Powered Legal Research</h1>
            <p className="auth-heading-sub">
              <span className="auth-highlight">Grounded in Indian Jurisprudence</span>
              {" "}& the Indian Knowledge System
            </p>
          </div>

          {error && <div className="auth-error">{error}</div>}

          {/* Google button */}
          <button className="auth-google-btn" onClick={handleGoogle} disabled={loading}>
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="" width={20} />
            Continue with Google
          </button>

          {/* Divider */}
          <div className="auth-divider">
            <span className="auth-divider-line" />
            <span className="auth-divider-text">OR</span>
            <span className="auth-divider-line" />
          </div>

          {/* Email toggle / form */}
          {!showEmailForm ? (
            <button className="auth-email-btn" onClick={() => setShowEmailForm(true)}>
              <Mail size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} /> Continue with Email
            </button>
          ) : (
            <form onSubmit={handleEmail} className="auth-form">
              <div className="auth-input-group">
                <input
                  id="login-email"
                  type="email"
                  placeholder=" "
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="auth-input"
                />
                <label htmlFor="login-email" className="auth-label">Email address</label>
              </div>
              <div className="auth-input-group">
                <input
                  id="login-password"
                  type="password"
                  placeholder=" "
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="auth-input"
                />
                <label htmlFor="login-password" className="auth-label">Password</label>
              </div>
              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? "Signing in…" : "Sign In"}
              </button>
            </form>
          )}

          <p className="auth-switch">
            Don't have an account?{" "}
            <button className="auth-switch-link" onClick={onSwitchToSignUp}>Create Account</button>
          </p>

          <p className="auth-terms">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>

      {/* ── Right: Showcase ───────────────────────────────── */}
      <AuthShowcase />
    </div>
  );
}

function friendlyError(code) {
  const map = {
    "auth/invalid-email": "Invalid email address.",
    "auth/user-not-found": "No account found with this email.",
    "auth/wrong-password": "Incorrect password.",
    "auth/too-many-requests": "Too many attempts. Please try again later.",
    "auth/popup-closed-by-user": "Sign-in popup was closed.",
    "auth/network-request-failed": "Network error. Check your connection.",
    "auth/invalid-credential": "Invalid credentials. Please check your email and password.",
  };
  return map[code] || "Sign-in failed. Please try again.";
}
