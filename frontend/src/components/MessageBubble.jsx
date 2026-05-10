import React, { useState } from "react";
import { Scale, ScrollText, BookOpen, FileText, User, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import Logo from "./Logo";
import CitationCard from "./CitationCard";
import SourceViewer from "./SourceViewer";

const INTENT_LABELS = {
  definition:     { label: "Definition",     color: "var(--intent-definition)" },
  case_lookup:    { label: "Case Law",       color: "var(--intent-caselaw)" },
  statute_lookup: { label: "Statute",        color: "var(--intent-statute)" },
  irac_analysis:  { label: "IRAC Analysis",  color: "var(--intent-irac)" },
  idar_analysis:  { label: "IDAR · Dharma",  color: "var(--intent-idar)" },
  comparative:    { label: "Comparative",    color: "var(--intent-general)" },
  follow_up:      { label: "Follow-up",      color: "var(--intent-general)" },
  general_qa:     { label: "General",        color: "var(--intent-general)" },
  // legacy labels
  case_law:       { label: "Case Law",       color: "var(--intent-caselaw)" },
  statute:        { label: "Statute",        color: "var(--intent-statute)" },
  legal_reasoning:{ label: "IRAC Analysis",  color: "var(--intent-irac)" },
  idar:           { label: "IDAR · Dharma",  color: "var(--intent-idar)" },
  general:        { label: "General",        color: "var(--intent-general)" },
};

const getSourceIcon = (type) => {
  if (type === "case") return <Scale size={14} />;
  if (type === "statute") return <ScrollText size={14} />;
  if (type === "glossary") return <BookOpen size={14} />;
  return <FileText size={14} />;
};

export default function MessageBubble({ message }) {
  const { role, content, intent, sources } = message;
  const isUser = role === "user";
  const intentMeta = INTENT_LABELS[intent] || null;
  const [viewSource, setViewSource] = useState(null);
  const [showAllSources, setShowAllSources] = useState(false);

  const visibleSources = showAllSources ? sources : (sources || []).slice(0, 3);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`bubble-wrapper ${isUser ? "user-wrapper" : "assistant-wrapper"}`}>
      <div className={`avatar ${isUser ? "user-avatar" : "ai-avatar"}`}>
        {isUser ? <User size={18} /> : <Logo size={18} color="white" />}
      </div>

      <div className="bubble-content">
        {!isUser && intentMeta && (
          <span className="intent-badge" style={{ background: intentMeta.color }}>
            {intentMeta.label}
          </span>
        )}

        <div className={`bubble ${isUser ? "user-bubble" : "ai-bubble"}`}>
          {isUser ? (
            <p style={{ margin: 0 }}>{content}</p>
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}
        </div>

        {/* Citation pills */}
        {!isUser && sources && sources.length > 0 && (
          <div style={{ marginTop: "0.5rem" }}>
            <p style={styles.sourcesLabel}>
              Sources ({sources.length})
            </p>
            {visibleSources.map((src, i) => (
              <CitationCard
                key={i}
                source={src}
                onViewSource={() => setViewSource(src)}
              />
            ))}
            {sources.length > 3 && (
              <button
                style={styles.showMoreBtn}
                onClick={() => setShowAllSources((v) => !v)}
              >
                {showAllSources ? "Show fewer" : `+${sources.length - 3} more sources`}
              </button>
            )}
          </div>
        )}
        {/* Copy Button */}
        {!isUser && (
          <button 
            onClick={handleCopy}
            style={styles.copyBtn}
            title="Copy response"
          >
            {copied ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
            <span style={{ marginLeft: "4px" }}>{copied ? "Copied" : "Copy"}</span>
          </button>
        )}
      </div>

      {viewSource && (
        <SourceViewer source={viewSource} onClose={() => setViewSource(null)} />
      )}
    </div>
  );
}

const styles = {
  sourcesLabel: {
    margin: "0 0 0.35rem",
    fontSize: "0.72rem",
    color: "#9ca3af",
    textTransform: "uppercase",
    fontWeight: 600,
    letterSpacing: "0.05em",
  },
  showMoreBtn: {
    background: "none",
    border: "none",
    color: "var(--primary)",
    cursor: "pointer",
    fontSize: "0.78rem",
    padding: "0.25rem 0",
    fontWeight: 500,
  },
  copyBtn: {
    display: "flex",
    alignItems: "center",
    background: "none",
    border: "none",
    color: "var(--text-muted)",
    cursor: "pointer",
    fontSize: "0.75rem",
    padding: "0.25rem 0",
    marginTop: "0.25rem",
    transition: "color 0.2s",
  }
};
