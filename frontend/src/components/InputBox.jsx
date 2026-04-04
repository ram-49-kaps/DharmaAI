import React, { useState, useRef } from "react";

const QUICK_PROMPTS = [
  "What is Dharma in Indian law?",
  "Explain Kesavananda Bharati case",
  "What does Article 21 say?",
  "Apply IRAC: A minor signed a contract",
  "What is mens rea?",
];

export default function InputBox({ onSend, loading, prefillText, onPrefillUsed }) {
  const [text, setText] = useState("");
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
    </div>
  );
}
