import React, { useState } from "react";
import { createUserWithEmailAndPassword, updateProfile, signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../firebase/config";
import { Scale, ScrollText, BrainCircuit, BookOpen, GraduationCap } from "lucide-react";
import Logo from "./Logo";
import AuthShowcase from "./AuthShowcase";

const LEVELS = [
  { value: "beginner", label: "Beginner Student", desc: "1st–2nd year law student" },
  { value: "advanced", label: "Advanced Student", desc: "3rd–5th year law student" },
  { value: "academician", label: "Academician", desc: "Professor or researcher" },
  { value: "practitioner", label: "Practitioner", desc: "Practicing lawyer or advocate" },
];

export default function SignUp({ onSwitchToLogin }) {
  const [step, setStep] = useState(1); // 1: account, 2: profile
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [institution, setInstitution] = useState("");
  const [level, setLevel] = useState("beginner");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    try {
      const { user } = await createUserWithEmailAndPassword(auth, email, password);
      if (name.trim()) {
        await updateProfile(user, { displayName: name.trim() });
      }
      localStorage.setItem(`dharma-profile-${user.uid}`, JSON.stringify({
        level,
        institution: institution.trim(),
        name: name.trim(),
      }));
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
      {/* ── Left: Sign Up Form ─────────────────────────────── */}
      <div className="auth-left">
        <div className="auth-left-inner">
          <div className="auth-brand-top">
            <Logo size={28} />
            <span className="auth-brand-name">DharmaAI</span>
          </div>

          <div className="auth-heading">
            <div className="auth-icon-wrap">
              <Logo size={36} />
            </div>
            <h1>Create Your Account</h1>
            <p className="auth-heading-sub">
              Start your <span className="auth-highlight">legal research journey</span> today
            </p>
          </div>

          {error && <div className="auth-error">{error}</div>}

          {/* Step indicator */}
          <div className="auth-steps">
            <div className={`auth-step-dot ${step >= 1 ? "active" : ""}`}>1</div>
            <div className="auth-step-line" />
            <div className={`auth-step-dot ${step >= 2 ? "active" : ""}`}>2</div>
          </div>

          {step === 1 ? (
            <>
              <button className="auth-google-btn" onClick={handleGoogle} disabled={loading}>
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="" width={20} />
                Sign up with Google
              </button>

              <div className="auth-divider">
                <span className="auth-divider-line" />
                <span className="auth-divider-text">OR</span>
                <span className="auth-divider-line" />
              </div>

              <form onSubmit={(e) => { e.preventDefault(); setStep(2); }} className="auth-form">
                <div className="auth-input-group">
                  <input
                    id="signup-name"
                    type="text"
                    placeholder=" "
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="auth-input"
                  />
                  <label htmlFor="signup-name" className="auth-label">Full Name</label>
                </div>
                <div className="auth-input-group">
                  <input
                    id="signup-email"
                    type="email"
                    placeholder=" "
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="auth-input"
                  />
                  <label htmlFor="signup-email" className="auth-label">Email address</label>
                </div>
                <div className="auth-input-group">
                  <input
                    id="signup-password"
                    type="password"
                    placeholder=" "
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="auth-input"
                  />
                  <label htmlFor="signup-password" className="auth-label">Password (min 6 characters)</label>
                </div>
                <button type="submit" className="auth-submit-btn">
                  Next — Choose Your Level →
                </button>
              </form>
            </>
          ) : (
            <form onSubmit={handleSignUp} className="auth-form">
              <div className="auth-input-group">
                <input
                  id="signup-institution"
                  type="text"
                  placeholder=" "
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                  className="auth-input"
                />
                <label htmlFor="signup-institution" className="auth-label">Institution (optional)</label>
              </div>

              <p className="auth-level-label">Select your expertise level:</p>
              <div className="auth-level-grid">
                {LEVELS.map((l) => (
                  <button
                    key={l.value}
                    type="button"
                    onClick={() => setLevel(l.value)}
                    className={`auth-level-card ${level === l.value ? "active" : ""}`}
                  >
                    <span className="auth-level-name">{l.label}</span>
                    <span className="auth-level-desc">{l.desc}</span>
                  </button>
                ))}
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? "Creating account…" : "Create Account"}
              </button>
              <button type="button" className="auth-back-btn" onClick={() => setStep(1)}>
                ← Back
              </button>
            </form>
          )}

          <p className="auth-switch">
            Already have an account?{" "}
            <button className="auth-switch-link" onClick={onSwitchToLogin}>Sign In</button>
          </p>

          <p className="auth-terms">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>

          <p style={{
            fontSize: "0.72rem",
            color: "var(--text-muted, #6b7280)",
            textAlign: "center",
            marginTop: "1.5rem",
            opacity: 0.85
          }}>
            Developed by <strong>Ram Kapadia</strong> & <strong>Arnav Narula</strong>
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
    "auth/email-already-in-use": "An account with this email already exists.",
    "auth/invalid-email": "Invalid email address.",
    "auth/weak-password": "Password is too weak.",
    "auth/popup-closed-by-user": "Sign-up popup was closed.",
    "auth/network-request-failed": "Network error. Check your connection.",
  };
  return map[code] || "Sign-up failed. Please try again.";
}
