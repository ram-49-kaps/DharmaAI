import React, { useState, useRef, useEffect } from "react";
import { Scale, ScrollText, BookOpen, FileText, User, Copy, Check, ThumbsUp, ThumbsDown, Share2, Pencil, RefreshCw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import Logo from "./Logo";
import CitationCard from "./CitationCard";
import SourceViewer from "./SourceViewer";
import { submitFeedback } from "../services/api";

const INTENT_LABELS = {
  definition:     { label: "Definition",     color: "var(--intent-definition)" },
  case_lookup:    { label: "Case Law",       color: "var(--intent-caselaw)" },
  statute_lookup: { label: "Statute",        color: "var(--intent-statute)" },
  irac_analysis:  { label: "IRAC Analysis",  color: "var(--intent-irac)" },
  filac_analysis: { label: "FILAC Analysis", color: "var(--intent-irac)" },
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

const stripMarkdown = (md) => {
  if (!md) return "";
  return md
    .replace(/^#+\s+/gm, "")               // Headers
    .replace(/(\*\*|__)(.*?)\1/g, "$2")    // Bold
    .replace(/(\*|_)(.*?)\1/g, "$2")       // Italic
    .replace(/^\>\s+/gm, "")               // Blockquotes
    .replace(/`(.*?)`/g, "$1")             // Inline code
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")// Links
    .replace(/^[\*\-\+]\s+/gm, "")         // Unordered lists
    .replace(/^\d+\.\s+/gm, "")            // Ordered lists
    .replace(/^(---|\*\*\*|___)\s*$/gm, "")// Horizontal rules
    .replace(/(\n\s*){3,}/g, "\n\n")       // Remove excessive newlines
    .trim();
};

const cleanUserContent = (text) => {
  if (!text) return "";
  return text.split(/\n\nAttached:/)[0].trim();
};

export default function MessageBubble({ message, messageIndex, onEditMessage, onShareChat, sessionId, onRegenerate, onSendSuggested }) {
  const { role, content, intent, sources } = message;
  const isUser = role === "user";
  const intentMeta = INTENT_LABELS[intent] || null;
  const [viewSource, setViewSource] = useState(null);
  const [showAllSources, setShowAllSources] = useState(false);
  const visibleSources = showAllSources ? sources : (sources || []).slice(0, 3);

  // Copy state
  const [copied, setCopied] = useState(false);

  // Feedback state
  const [feedback, setFeedback] = useState(null); // null | 'up' | 'down'

  // Edit state (user messages only)
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(isUser ? cleanUserContent(content) : content);
  const editRef = useRef(null);

  useEffect(() => {
    setEditText(isUser ? cleanUserContent(content) : content);
  }, [content, isUser]);

  useEffect(() => {
    if (isEditing && editRef.current) {
      editRef.current.focus();
      editRef.current.style.height = "auto";
      editRef.current.style.height = editRef.current.scrollHeight + "px";
    }
  }, [isEditing]);

  const handleCopy = () => {
    const plainText = stripMarkdown(content);
    navigator.clipboard.writeText(plainText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };


  const handleFeedback = async (type) => {
    const newFeedback = feedback === type ? null : type;
    setFeedback(newFeedback);
    if (newFeedback) {
      try {
        await submitFeedback({
          session_id: sessionId || null,
          feedback_type: type === "up" ? "thumbs_up" : "thumbs_down",
          query: "",
          response: content,
        });
      } catch (err) {
        console.error("Feedback failed:", err);
      }
    }
  };

  const handleEditSave = () => {
    const trimmed = editText.trim();
    if (trimmed && trimmed !== content && onEditMessage) {
      onEditMessage(messageIndex, trimmed);
    }
    setIsEditing(false);
  };

  const handleEditCancel = () => {
    setEditText(content);
    setIsEditing(false);
  };

  const handleEditKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleEditSave();
    }
    if (e.key === "Escape") handleEditCancel();
  };

  return (
    <div className={`bubble-wrapper ${isUser ? "user-wrapper" : "assistant-wrapper"}`}>
      <div className={`avatar ${isUser ? "user-avatar" : "ai-avatar"}`}>
        {isUser ? <User size={18} color="var(--primary)" /> : <Logo size={18} />}
      </div>

      <div className="bubble-content">
        {!isUser && intentMeta && (
          <span className="intent-badge" style={{ background: intentMeta.color }}>
            {intentMeta.label}
          </span>
        )}

        <div className={`bubble ${isUser ? "user-bubble" : "ai-bubble"}`} style={{ position: "relative" }}>
          {isUser ? (
            isEditing ? (
              <div className="user-edit-area">
                <textarea
                  ref={editRef}
                  className="user-edit-textarea"
                  value={editText}
                  onChange={(e) => {
                     setEditText(e.target.value);
                     e.target.style.height = "auto";
                     e.target.style.height = e.target.scrollHeight + "px";
                  }}
                  onKeyDown={handleEditKeyDown}
                />
                <div className="user-edit-actions">
                  <button className="edit-cancel-btn" onClick={handleEditCancel}>Cancel</button>
                  <button className="edit-save-btn" onClick={handleEditSave}>Save & Send</button>
                </div>
              </div>
            ) : (
              <>
                <p style={{ margin: 0 }}>{cleanUserContent(content)}</p>
                {message.attachments && message.attachments.length > 0 && (
                  <div className="bubble-attachments">
                    {message.attachments.map((att, idx) => {
                      const isImage = att.type?.startsWith("image/") || att.preview?.startsWith("data:image/") || att.preview?.startsWith("blob:");
                      if (isImage) {
                        return (
                          <div key={idx} className="bubble-attachment-preview-wrap">
                            <img 
                              src={att.preview} 
                              alt={att.name} 
                              className="bubble-attachment-img" 
                              onClick={() => window.open(att.preview, "_blank")}
                            />
                            <span className="bubble-attachment-name" title={att.name}>{att.name}</span>
                          </div>
                        );
                      } else {
                        return (
                          <div key={idx} className="bubble-attachment-file" title={att.name}>
                            <FileText size={14} style={{ marginRight: "4px" }} />
                            <span className="bubble-attachment-name" style={{ margin: 0 }}>{att.name}</span>
                          </div>
                        );
                      }
                    })}
                  </div>
                )}
              </>
            )
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}

          {/* Edit button for user messages */}
          {isUser && !isEditing && onEditMessage && (
            <div className="tooltip-wrap user-msg-edit-tooltip">
              <button
                className="user-msg-edit-btn"
                onClick={() => setIsEditing(true)}
              >
                <Pencil size={12} />
              </button>
              <div className="tooltip-content">Edit message</div>
            </div>
          )}
        </div>

        {/* Citation pills */}
        {!isUser && sources && sources.length > 0 && (
          <div style={{ marginTop: "0.35rem" }}>
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

        {/* Suggested Questions */}
        {!isUser && message.suggested_questions && message.suggested_questions.length > 0 && (
          <div className="suggested-questions-container">
            <p style={styles.sourcesLabel}>Suggested Follow-ups</p>
            <div className="suggested-questions-chips">
              {message.suggested_questions.map((q, i) => (
                <button
                  key={i}
                  className="suggested-q-chip"
                  onClick={() => onSendSuggested?.(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons — AI messages only, appear on hover */}
        {!isUser && (
          <div className="message-actions">
            <div className="tooltip-wrap">
              <button
                onClick={handleCopy}
                className="msg-action-btn"
              >
                {copied ? <Check size={14} color="var(--success, #22c55e)" /> : <Copy size={14} />}
              </button>
              <div className="tooltip-content">
                {copied ? "Copied!" : "Copy response"}
              </div>
            </div>

            <div className="tooltip-wrap">
              <button
                className={`msg-action-btn ${feedback === 'up' ? 'feedback-active' : ''}`}
                onClick={() => handleFeedback('up')}
              >
                <ThumbsUp size={14} />
              </button>
              <div className="tooltip-content">Helpful</div>
            </div>

            <div className="tooltip-wrap">
              <button
                className={`msg-action-btn ${feedback === 'down' ? 'feedback-active-neg' : ''}`}
                onClick={() => handleFeedback('down')}
              >
                <ThumbsDown size={14} />
              </button>
              <div className="tooltip-content">Not helpful</div>
            </div>

            {onShareChat && (
              <div className="tooltip-wrap">
                <button
                  className="msg-action-btn"
                  onClick={() => onShareChat?.()}
                >
                  <Share2 size={14} />
                </button>
                <div className="tooltip-content">Share chat</div>
              </div>
            )}

            {onRegenerate && (
              <div className="tooltip-wrap">
                <button
                  className="msg-action-btn"
                  onClick={() => onRegenerate(messageIndex)}
                >
                  <RefreshCw size={14} />
                </button>
                <div className="tooltip-content">Regenerate response</div>
              </div>
            )}
          </div>
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
    margin: "0 0 0.3rem",
    fontSize: "0.68rem",
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
    fontSize: "0.75rem",
    padding: "0.2rem 0",
    fontWeight: 500,
  },
};
