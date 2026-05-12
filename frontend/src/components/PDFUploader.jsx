import React, { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, X, Globe, Link as LinkIcon } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const CATEGORIES = [
  { value: "iks_texts", label: "IKS Texts (Arthashastra, Manusmriti, etc.)" },
  { value: "modern_law", label: "Modern Law (Statutes, Acts)" },
  { value: "case_law", label: "Case Law (Judgments)" },
];

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function PDFUploader({ onClose }) {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState("pdf"); // pdf | link
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [category, setCategory] = useState("iks_texts");
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef(null);

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (f && f.type === "application/pdf") {
      setFile(f);
      setStatus("idle");
    } else {
      setErrorMsg("Only PDF files are accepted.");
      setStatus("error");
    }
  };

  const handleUpload = async () => {
    if (activeTab === "pdf" && !file) return;
    if (activeTab === "link" && !url) return;
    
    setStatus("uploading");
    setErrorMsg("");

    try {
      let resp;
      if (activeTab === "pdf") {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("category", category);
        resp = await fetch(`${API_URL}/api/ingest`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
      } else {
        const formData = new FormData();
        formData.append("url", url);
        formData.append("category", category);
        resp = await fetch(`${API_URL}/api/ingest-url`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
      }

      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Ingestion failed");
      setResult(data);
      setStatus("success");
    } catch (err) {
      setErrorMsg(err.message);
      setStatus("error");
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <strong>Add Knowledge (Admin)</strong>
          <button style={styles.closeBtn} onClick={onClose}><X size={18} /></button>
        </div>

        {/* Tabs */}
        <div style={styles.tabs}>
          <button 
            style={{ ...styles.tab, borderBottom: activeTab === "pdf" ? "2px solid var(--primary)" : "none", color: activeTab === "pdf" ? "var(--primary)" : "#666" }}
            onClick={() => { setActiveTab("pdf"); setStatus("idle"); }}
          >
            <FileText size={16} /> Upload PDF
          </button>
          <button 
            style={{ ...styles.tab, borderBottom: activeTab === "link" ? "2px solid var(--primary)" : "none", color: activeTab === "link" ? "var(--primary)" : "#666" }}
            onClick={() => { setActiveTab("link"); setStatus("idle"); }}
          >
            <Globe size={16} /> Add Link
          </button>
        </div>

        <div style={styles.body}>
          {status === "success" ? (
            <div style={styles.success}>
              <CheckCircle size={40} color="#10b981" />
              <p style={styles.successTitle}>Successfully Ingested</p>
              <p>{result.chunks_created} chunks added to <strong>{result.collection}</strong></p>
              <p style={styles.filename}>{result.filename}</p>
              <button style={styles.btn} onClick={() => { setFile(null); setUrl(""); setStatus("idle"); }}>
                Add More
              </button>
            </div>
          ) : (
            <>
              {activeTab === "pdf" ? (
                <div
                  style={{ ...styles.dropzone, borderColor: file ? "var(--primary)" : "#d1d5db" }}
                  onClick={() => inputRef.current?.click()}
                >
                  <input ref={inputRef} type="file" accept=".pdf" hidden onChange={handleFile} />
                  {file ? (
                    <>
                      <FileText size={32} color="var(--primary)" />
                      <p style={styles.filename}>{file.name}</p>
                      <p style={styles.filesize}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </>
                  ) : (
                    <>
                      <Upload size={32} color="#9ca3af" />
                      <p style={{ color: "#6b7280", margin: "0.5rem 0 0" }}>Click to select PDF</p>
                    </>
                  )}
                </div>
              ) : (
                <div style={styles.linkInputContainer}>
                  <LinkIcon size={20} color="#9ca3af" style={{ marginLeft: "10px" }} />
                  <input 
                    style={styles.urlInput}
                    placeholder="https://example.com/legal-document"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                </div>
              )}

              <label style={styles.label}>Collection (Where to store this?)</label>
              <select style={styles.select} value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>

              {status === "error" && (
                <div style={styles.error}>
                  <AlertCircle size={14} />
                  {errorMsg}
                </div>
              )}

              <button
                style={{ ...styles.btn, opacity: (activeTab === "pdf" && !file) || (activeTab === "link" && !url) || status === "uploading" ? 0.6 : 1 }}
                disabled={(activeTab === "pdf" && !file) || (activeTab === "link" && !url) || status === "uploading"}
                onClick={handleUpload}
              >
                {status === "uploading" ? "Processing…" : activeTab === "pdf" ? "Ingest PDF" : "Scrape Link"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
    zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem",
  },
  modal: {
    background: "#fff", borderRadius: "12px", width: "100%", maxWidth: "480px",
    boxShadow: "0 20px 60px rgba(0,0,0,0.3)", overflow: "hidden",
  },
  header: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "1rem 1.25rem", borderBottom: "1px solid #e5e7eb", fontSize: "0.95rem",
  },
  tabs: {
    display: "flex", borderBottom: "1px solid #e5e7eb",
  },
  tab: {
    flex: 1, padding: "0.75rem", background: "none", border: "none", cursor: "pointer",
    fontSize: "0.85rem", fontWeight: 600, display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem",
  },
  closeBtn: { background: "none", border: "none", cursor: "pointer", color: "#6b7280" },
  body: { padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" },
  dropzone: {
    border: "2px dashed", borderRadius: "10px", padding: "2rem",
    textAlign: "center", cursor: "pointer", transition: "border-color 0.2s",
  },
  linkInputContainer: {
    display: "flex", alignItems: "center", border: "1px solid #d1d5db", borderRadius: "8px", overflow: "hidden",
  },
  urlInput: {
    flex: 1, padding: "0.75rem", border: "none", outline: "none", fontSize: "0.875rem",
  },
  filename: { margin: "0.25rem 0 0", fontSize: "0.875rem", color: "#374151", fontWeight: 500 },
  filesize: { margin: 0, fontSize: "0.75rem", color: "#9ca3af" },
  label: { fontSize: "0.8rem", fontWeight: 600, color: "#374151" },
  select: {
    padding: "0.65rem 0.75rem", border: "1px solid #d1d5db", borderRadius: "8px",
    fontSize: "0.875rem", background: "#fff",
  },
  error: {
    display: "flex", alignItems: "center", gap: "0.5rem",
    background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626",
    borderRadius: "8px", padding: "0.65rem 0.75rem", fontSize: "0.875rem",
  },
  success: { textAlign: "center", padding: "1rem 0" },
  successTitle: { fontSize: "1.1rem", fontWeight: 700, color: "#065f46", margin: "0.75rem 0 0.25rem" },
  btn: {
    padding: "0.75rem", background: "var(--primary)", color: "#fff",
    border: "none", borderRadius: "8px", fontSize: "0.9rem", fontWeight: 600,
    cursor: "pointer",
  },
};
