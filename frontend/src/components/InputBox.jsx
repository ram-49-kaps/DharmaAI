import React, { useState, useRef } from "react";
import { Square, Paperclip, X, FileText, Image, Send } from "lucide-react";

const QUICK_PROMPTS = [
  "What is Dharma in Indian law?",
  "Explain Kesavananda Bharati case",
  "What does Article 21 say?",
];

export default function InputBox({ onSend, loading, prefillText, onPrefillUsed, messages = [], onCompactContext }) {
  const [text, setText] = useState("");
  const [showContext, setShowContext] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Handle prefill from templates
  React.useEffect(() => {
    if (prefillText) {
      setText(prefillText);
      onPrefillUsed();
      textareaRef.current?.focus();
    }
  }, [prefillText, onPrefillUsed]);

  // Window drag and drop listeners
  React.useEffect(() => {
    const handleWindowDragEnter = (e) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current++;
      if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
        setIsDragging(true);
      }
    };

    const handleWindowDragLeave = (e) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current--;
      if (dragCounter.current === 0) {
        setIsDragging(false);
      }
    };

    const handleWindowDragOver = (e) => {
      e.preventDefault();
      e.stopPropagation();
    };

    const handleWindowDrop = (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      dragCounter.current = 0;

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const files = Array.from(e.dataTransfer.files);
        const newAttachments = files.map(file => ({
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : null,
        }));
        setAttachments(prev => [...prev, ...newAttachments].slice(0, 10));
        e.dataTransfer.clearData();
      }
    };

    window.addEventListener("dragenter", handleWindowDragEnter);
    window.addEventListener("dragleave", handleWindowDragLeave);
    window.addEventListener("dragover", handleWindowDragOver);
    window.addEventListener("drop", handleWindowDrop);

    return () => {
      window.removeEventListener("dragenter", handleWindowDragEnter);
      window.removeEventListener("dragleave", handleWindowDragLeave);
      window.removeEventListener("dragover", handleWindowDragOver);
      window.removeEventListener("drop", handleWindowDrop);
    };
  }, []);

  const handleSend = () => {
    if (loading) {
      onSend(""); // Triggers handleStop in App.js because loading is true
      return;
    }
    const trimmed = text.trim();
    if (!trimmed && attachments.length === 0) return;
    onSend(trimmed, attachments);
    setText("");
    setAttachments([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e) => {
    setText(e.target.value);
    const ta = textareaRef.current;
    if (ta) { ta.style.height = "auto"; ta.style.height = ta.scrollHeight + "px"; }
  };

  // ── Attachment handling ─────────────────────────────────────────
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    const newAttachments = files.map(file => ({
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : null,
    }));
    setAttachments(prev => [...prev, ...newAttachments].slice(0, 10)); // Max 10 files
    e.target.value = ""; // Reset input
  };

  const removeAttachment = (index) => {
    setAttachments(prev => {
      const updated = [...prev];
      if (updated[index].preview) URL.revokeObjectURL(updated[index].preview);
      updated.splice(index, 1);
      return updated;
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  };

  const inputTokens = Math.ceil(text.trim().length / 4);
  const historyString = messages.map(m => m.content).join(" ");
  const historyTokens = Math.ceil(historyString.length / 4);
  const systemTokens = 850; // Average injection prompt tokens
  const totalUsed = systemTokens + historyTokens + inputTokens;
  const totalAvailable = 128000; // Groq Llama 3.3 70B context window
  const percentUsed = Math.min(((totalUsed / totalAvailable) * 100), 100).toFixed(1);

  return (
    <div className="input-area">
      {isDragging && (
        <div className="drag-drop-overlay">
          <div className="drag-drop-content">
            <div className="drag-drop-icon-wrap">
              <Paperclip size={40} className="drag-drop-icon" />
            </div>
            <h3>Drop your files here</h3>
            <p>Attach legal documents, screenshots, or images to your query (Max 10 files, up to 20MB each)</p>
          </div>
        </div>
      )}
      {/* Quick prompts */}
      {messages.length === 0 && (
        <div className="quick-prompts">
          {QUICK_PROMPTS.map((p, i) => (
            <button key={i} className="quick-btn" onClick={() => { setText(p); textareaRef.current?.focus(); }}>
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Attachment previews */}
      {attachments.length > 0 && (
        <div className="attachment-previews">
          {attachments.map((att, i) => (
            <div key={i} className="attachment-chip">
              {att.preview ? (
                <img src={att.preview} alt={att.name} className="attachment-thumb" />
              ) : (
                <FileText size={16} className="attachment-file-icon" />
              )}
              <div className="attachment-info">
                <span className="attachment-name">{att.name}</span>
                <span className="attachment-size">{formatFileSize(att.size)}</span>
              </div>
              <button className="attachment-remove" onClick={() => removeAttachment(i)}>
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="input-card">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.webp"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />
        
        <textarea
          ref={textareaRef}
          className="input-textarea"
          rows={1}
          placeholder="Ask anything DharmaAI..."
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
        />
        
        <div className="input-actions-row">
          <button className="input-action-btn" onClick={() => fileInputRef.current?.click()}>
            <Paperclip size={14} /> Attach
          </button>
          <button className="input-action-btn" onClick={() => fileInputRef.current?.click()}>
            <Image size={14} /> Upload Media
          </button>
          
          <span className="upload-limits-tip" style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginLeft: "8px", alignSelf: "center" }}>
            Max 10 files (up to 20MB/file)
          </span>

          <button 
            className={`send-btn ${loading ? "stop-mode" : ""}`} 
            onClick={handleSend} 
            disabled={!text.trim() && !loading && attachments.length === 0}
          >
            {loading ? <Square size={14} fill="currentColor" /> : <Send size={16} />}
          </button>
        </div>
      </div>

      <div className="context-wrapper">
        <div className="context-badge" onClick={() => setShowContext(!showContext)} title="View Token Memory Usage">
          <svg viewBox="0 0 36 36" className="context-donut">
            <path
              className="donut-bg"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className="donut-fill"
              strokeDasharray={`${percentUsed}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <span className="context-pct">{Math.floor(percentUsed)}%</span>
        </div>
        
        {showContext && (
          <div className="context-popup">
            <div className="context-popup-header">
              <span className="context-title">Context Window</span>
              <div className="context-stats">
                <span>{(totalUsed/1000).toFixed(1)}K / {(totalAvailable/1000).toFixed(1)}K tokens</span>
                <span>{percentUsed}%</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${percentUsed}%` }}></div>
              </div>
              <div className="reserved-note">
                <span className="reserved-dash">////</span> Reserved for response
              </div>
            </div>

            <div className="context-section">
              <strong>System</strong>
              <div className="context-row">
                <span>System Instructions</span>
                <span className="context-val">{Math.min((systemTokens/totalAvailable)*100, 100).toFixed(1)}%</span>
              </div>
            </div>

            <div className="context-section">
              <strong>User Context</strong>
              <div className="context-row">
                <span>Messages ({messages.length})</span>
                <span className="context-val">{Math.min((historyTokens/totalAvailable)*100, 100).toFixed(1)}%</span>
              </div>
              <div className="context-row">
                <span>Current Input</span>
                <span className="context-val">{Math.min((inputTokens/totalAvailable)*100, 100).toFixed(1)}%</span>
              </div>
            </div>

            <button className="compact-btn" onClick={() => { onCompactContext(); setShowContext(false); }}>
              Compact Conversation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
