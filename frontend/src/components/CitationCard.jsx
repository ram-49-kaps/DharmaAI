import React, { useState } from "react";
import { BookOpen, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";

const TYPE_COLORS = {
  iks: { bg: "#fef3c7", border: "#f59e0b", text: "#92400e", label: "IKS" },
  case: { bg: "#ede9fe", border: "#C2410C", text: "#5b21b6", label: "Case" },
  statute: { bg: "#dbeafe", border: "#3b82f6", text: "#1e40af", label: "Statute" },
  principle: { bg: "#d1fae5", border: "#10b981", text: "#065f46", label: "Principle" },
  glossary: { bg: "#f3f4f6", border: "#6b7280", text: "#374151", label: "Glossary" },
  default: { bg: "#f3f4f6", border: "#6b7280", text: "#374151", label: "Source" },
};

export default function CitationCard({ source, onViewSource }) {
  const [expanded, setExpanded] = useState(false);

  const type = (source.type || "default").toLowerCase();
  const colors = TYPE_COLORS[type] || TYPE_COLORS.default;
  const hasExcerpt = source.excerpt && source.excerpt.length > 10;

  return (
    <div style={{ ...styles.card, borderLeft: `3px solid ${colors.border}` }}>
      <div style={styles.header}>
        <span style={{ ...styles.badge, background: colors.bg, color: colors.text }}>
          {colors.label}
        </span>
        <span style={styles.title}>{source.title}</span>
        <div style={styles.actions}>
          {hasExcerpt && (
            <button
              style={styles.iconBtn}
              onClick={() => setExpanded((v) => !v)}
              title={expanded ? "Collapse" : "Preview excerpt"}
            >
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          )}
          {onViewSource && (
            <a
              href={`https://www.google.com/search?q=${encodeURIComponent(
                source.title + (source.citation ? " " + source.citation.split(/[;,]/)[0].trim() : " Indian law")
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ ...styles.iconBtn, textDecoration: "none" }}
              title="Search on Google"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink size={14} />
            </a>
          )}
        </div>
      </div>

      {source.citation && (
        <p style={styles.citation}>
          <BookOpen size={12} style={{ marginRight: 4, flexShrink: 0 }} />
          {source.citation}
          {source.page && ` · p.${source.page}`}
        </p>
      )}

      {expanded && hasExcerpt && (
        <p style={styles.excerpt}>"{source.excerpt}…"</p>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "0.65rem 0.85rem",
    marginBottom: "0.5rem",
  },
  header: { display: "flex", alignItems: "center", gap: "0.5rem" },
  badge: {
    fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase",
    padding: "2px 6px", borderRadius: "4px", flexShrink: 0,
  },
  title: { flex: 1, fontSize: "0.82rem", fontWeight: 600, color: "#111827", lineHeight: 1.3 },
  actions: { display: "flex", gap: "0.25rem", flexShrink: 0 },
  iconBtn: {
    background: "none", border: "none", cursor: "pointer",
    color: "#6b7280", padding: "2px", display: "flex", alignItems: "center",
  },
  citation: {
    display: "flex", alignItems: "center", margin: "0.35rem 0 0",
    fontSize: "0.75rem", color: "#6b7280",
  },
  excerpt: {
    margin: "0.5rem 0 0", fontSize: "0.78rem", color: "#4b5563",
    fontStyle: "italic", lineHeight: 1.5,
    background: "#f9fafb", borderRadius: "4px", padding: "0.5rem",
  },
};
