import React from "react";
import { X, BookOpen, ExternalLink } from "lucide-react";

export default function SourceViewer({ source, onClose }) {
  if (!source) return null;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <div style={styles.headerLeft}>
            <BookOpen size={18} color="var(--primary)" />
            <strong style={styles.title}>{source.title}</strong>
          </div>
          <button style={styles.closeBtn} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div style={styles.meta}>
          {source.type && (
            <span style={styles.badge}>{source.type.toUpperCase()}</span>
          )}
          {source.citation && (
            <span style={styles.citation}>{source.citation}</span>
          )}
          {source.page && (
            <span style={styles.page}>p. {source.page}</span>
          )}
        </div>

        {source.excerpt ? (
          <div style={styles.content}>
            <p style={styles.excerptLabel}>Relevant excerpt:</p>
            <blockquote style={styles.excerpt}>{source.excerpt}</blockquote>
          </div>
        ) : (
          <p style={styles.noContent}>
            No preview available. Consult the original source document.
          </p>
        )}

        <div style={styles.footer}>
          <p style={styles.disclaimer}>
            Source retrieved from DharmaAI knowledge base.
            For authoritative text, consult the original publication.
          </p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
    zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center",
    padding: "1rem",
  },
  modal: {
    background: "#fff", borderRadius: "12px", width: "100%", maxWidth: "560px",
    maxHeight: "80vh", display: "flex", flexDirection: "column",
    boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
  },
  header: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "1rem 1.25rem", borderBottom: "1px solid #e5e7eb",
  },
  headerLeft: { display: "flex", alignItems: "center", gap: "0.6rem" },
  title: { fontSize: "0.95rem", color: "#111827" },
  closeBtn: { background: "none", border: "none", cursor: "pointer", color: "#6b7280", padding: "4px" },
  meta: { display: "flex", gap: "0.5rem", padding: "0.75rem 1.25rem", flexWrap: "wrap", alignItems: "center" },
  badge: {
    background: "#ede9fe", color: "#5b21b6", fontSize: "0.65rem",
    fontWeight: 700, padding: "2px 8px", borderRadius: "4px",
  },
  citation: { fontSize: "0.8rem", color: "#6b7280" },
  page: { fontSize: "0.8rem", color: "#9ca3af", marginLeft: "auto" },
  content: { padding: "0 1.25rem 1rem", overflowY: "auto", flex: 1 },
  excerptLabel: { fontSize: "0.75rem", color: "#6b7280", textTransform: "uppercase", fontWeight: 600, marginBottom: "0.5rem" },
  excerpt: {
    margin: 0, borderLeft: "3px solid var(--primary)", paddingLeft: "1rem",
    color: "#374151", fontSize: "0.9rem", lineHeight: 1.7, fontStyle: "italic",
  },
  noContent: { padding: "1rem 1.25rem", color: "#9ca3af", fontStyle: "italic", fontSize: "0.875rem" },
  footer: { padding: "0.75rem 1.25rem", borderTop: "1px solid #e5e7eb", background: "#f9fafb", borderRadius: "0 0 12px 12px" },
  disclaimer: { margin: 0, fontSize: "0.72rem", color: "#9ca3af" },
};
