import React from "react";
import { Scale, ScrollText, BookOpen, FileText, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

const INTENT_LABELS = {
  definition:      { label: "Definition",      color: "var(--intent-definition)" },
  case_law:        { label: "Case Law",        color: "var(--intent-caselaw)" },
  statute:         { label: "Statute",          color: "var(--intent-statute)" },
  legal_reasoning: { label: "IRAC Analysis",    color: "var(--intent-irac)" },
  idar:            { label: "IDAR · Dharma",    color: "var(--intent-idar)" },
  general:         { label: "General",          color: "var(--intent-general)" },
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

  return (
    <div className={`bubble-wrapper ${isUser ? "user-wrapper" : "assistant-wrapper"}`}>
      {/* Avatar */}
      <div className={`avatar ${isUser ? "user-avatar" : "ai-avatar"}`}>
        {isUser ? <User size={18} /> : <Scale size={18} />}
      </div>

      <div className="bubble-content">
        {/* Intent badge (assistant only) */}
        {!isUser && intentMeta && (
          <span className="intent-badge" style={{ background: intentMeta.color }}>
            {intentMeta.label}
          </span>
        )}

        {/* Message bubble */}
        <div className={`bubble ${isUser ? "user-bubble" : "ai-bubble"}`}>
          {isUser ? (
            <p style={{ margin: 0 }}>{content}</p>
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}
        </div>

        {/* Sources */}
        {!isUser && sources && sources.length > 0 && (
          <div className="sources-inline">
            <span className="sources-label">Sources:</span>
            {sources.map((src, i) => (
              <span key={i} className="source-chip" title={src.citation}>
                <span style={{display: "inline-flex", alignItems: "center", marginRight: 4}}>{getSourceIcon(src.type)}</span> {src.title}
                {src.citation && <em> · {src.citation}</em>}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
