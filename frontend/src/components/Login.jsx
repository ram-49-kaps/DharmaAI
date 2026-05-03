import React, { useState } from "react";
import { signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../firebase/config";
import Logo from "./Logo";

export default function Login({ onSwitchToSignUp }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.brand}>
          <Logo size={40} color="var(--primary)" />
          <h1 style={styles.title}>DharmaAI</h1>
          <p style={styles.subtitle}>Indian Legal Intelligence Platform</p>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <button style={styles.googleBtn} onClick={handleGoogle} disabled={loading}>
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="" width={18} />
          Continue with Google
        </button>

        <div style={styles.divider}><span>or</span></div>

        <form onSubmit={handleEmail} style={styles.form}>
          <input
            style={styles.input}
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button style={styles.submitBtn} type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p style={styles.switchText}>
          Don't have an account?{" "}
          <button style={styles.link} onClick={onSwitchToSignUp}>Sign Up</button>
        </p>

        <p style={styles.disclaimer}>
          Educational use only · Not legal advice
        </p>
      </div>
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
  };
  return map[code] || "Sign-in failed. Please try again.";
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%)",
    padding: "1rem",
  },
  card: {
    background: "#fff",
    borderRadius: "16px",
    padding: "2.5rem",
    width: "100%",
    maxWidth: "420px",
    boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
  },
  brand: { textAlign: "center", marginBottom: "2rem" },
  title: { margin: "0.5rem 0 0.25rem", color: "var(--primary)", fontSize: "1.8rem", fontWeight: 800 },
  subtitle: { margin: 0, color: "#666", fontSize: "0.9rem" },
  error: {
    background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626",
    borderRadius: "8px", padding: "0.75rem 1rem", marginBottom: "1rem", fontSize: "0.875rem",
  },
  googleBtn: {
    width: "100%", display: "flex", alignItems: "center", justifyContent: "center",
    gap: "0.75rem", padding: "0.75rem", border: "1px solid #d1d5db", borderRadius: "8px",
    background: "#fff", cursor: "pointer", fontSize: "0.95rem", fontWeight: 500,
    transition: "background 0.15s",
  },
  divider: {
    display: "flex", alignItems: "center", gap: "0.75rem", margin: "1.25rem 0",
    color: "#9ca3af", fontSize: "0.85rem",
    "::before": { content: '""', flex: 1, height: "1px", background: "#e5e7eb" },
    "::after": { content: '""', flex: 1, height: "1px", background: "#e5e7eb" },
  },
  form: { display: "flex", flexDirection: "column", gap: "0.75rem" },
  input: {
    padding: "0.75rem 1rem", border: "1px solid #d1d5db", borderRadius: "8px",
    fontSize: "0.95rem", outline: "none",
  },
  submitBtn: {
    padding: "0.75rem", background: "var(--primary)", color: "#fff",
    border: "none", borderRadius: "8px", fontSize: "0.95rem", fontWeight: 600,
    cursor: "pointer",
  },
  switchText: { textAlign: "center", marginTop: "1.25rem", fontSize: "0.875rem", color: "#6b7280" },
  link: { background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontWeight: 600 },
  disclaimer: { textAlign: "center", marginTop: "1rem", fontSize: "0.75rem", color: "#9ca3af" },
};
