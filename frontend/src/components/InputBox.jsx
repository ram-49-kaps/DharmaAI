import React, { useState, useRef } from "react";

const QUICK_PROMPTS = [
  "What is Dharma in Indian law?",
  "Explain Kesavananda Bharati case",
  "What does Article 21 say?",
  "Apply IRAC: A minor signed a contract",
  "What is mens rea?",
];

export default function InputBox({ onSend, loading, prefillText, onPrefillUsed, messages = [], onCompactContext }) {
  const [text, setText] = useState("");
  const [showContext, setShowContext] = useState(false);
  const textareaRef = useRef(null);

  // Handle prefill from templates
  React.useEffect(() => {
    if (prefillText) {
      setText(prefillText);
      onPrefillUsed();
      textareaRef.current?.focus();
    }
  }, [prefillText, onPrefillUsed]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setText("");
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

  const inputTokens = Math.ceil(text.trim().length / 4);
  const historyString = messages.map(m => m.content).join(" ");
  const historyTokens = Math.ceil(historyString.length / 4);
  const systemTokens = 850; // Average injection prompt tokens
  const totalUsed = systemTokens + historyTokens + inputTokens;
  const totalAvailable = 8192; // Llama 3 context
  const percentUsed = Math.min(((totalUsed / totalAvailable) * 100), 100).toFixed(1);

  return (
    <div className="input-area">
      {/* Quick prompts */}
      <div className="quick-prompts">
        {QUICK_PROMPTS.map((p, i) => (
          <button key={i} className="quick-btn" onClick={() => { setText(p); textareaRef.current?.focus(); }}>
            {p}
          </button>
        ))}
      </div>

      <div className="input-row">
        <textarea
          ref={textareaRef}
          className="input-textarea"
          rows={1}
          placeholder="Ask a legal question… (Shift+Enter for new line)"
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button className="send-btn" onClick={handleSend} disabled={!text.trim() || loading}>
          {loading ? <span className="spinner" /> : "➤"}
        </button>
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
