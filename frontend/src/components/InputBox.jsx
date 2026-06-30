import React, { useState, useRef, useEffect } from "react";
import { Square, Paperclip, X, FileText, Image, Send, ChevronDown, Check, Mic } from "lucide-react";

const QUICK_PROMPTS = [
  "What is Dharma in Indian law?",
  "Explain Kesavananda Bharati case",
  "What does Article 21 say?",
];

const MODELS = [
  { id: "llama-3.3-70b-versatile", name: "Llama 3.3 70B", desc: "Deep reasoning" },
  { id: "llama-3.1-8b-instant", name: "Llama 3.1 8B", desc: "Fastest answers" },
  { id: "gemma2-9b-it", name: "Gemma 2 9B", desc: "Alternative fallback" },
];

export default function InputBox({ onSend, loading, prefillText, onPrefillUsed, messages = [], onCompactContext, selectedModel, onModelChange }) {
  const [text, setText] = useState("");
  const [showContext, setShowContext] = useState(false);
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const modelMenuRef = useRef(null);
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const recognitionRef = useRef(null);

  // Setup Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      
      recognitionRef.current.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }
        
        setInterimText(interimTranscript);
        
        if (finalTranscript) {
          setText(prev => {
            const newText = prev + (prev.endsWith(' ') || prev.length === 0 ? '' : ' ') + finalTranscript;
            return newText;
          });
        }
        
        // Auto resize textarea
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto";
          textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
        setInterimText("");
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        setInterimText("");
      };
    }
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      setInterimText("");
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (e) {
        console.error(e);
      }
    }
  };

  // Close model menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (modelMenuRef.current && !modelMenuRef.current.contains(event.target)) {
        setShowModelMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
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
          placeholder="Ask anything Prakarna AI..."
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
        />

        {isListening && (
          <div className="listening-pill" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--surface-2)',
            borderRadius: '24px',
            padding: '8px 16px',
            margin: '8px 0',
            border: '1px solid var(--border)',
            gap: '12px',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: 'var(--primary)',
              color: 'white',
              flexShrink: 0
            }}>
              <Mic size={14} />
            </div>

            <div style={{ flex: 1, minHeight: '30px', minWidth: 0, display: 'flex', alignItems: 'center' }}>
              <span style={{ 
                opacity: interimText ? 0.9 : 0.5, 
                fontStyle: interimText ? 'normal' : 'italic', 
                color: 'var(--text)', 
                fontSize: '0.95rem',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {interimText || "Listening..."}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
              <button 
                onClick={toggleListening}
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  border: 'none',
                  background: 'var(--surface-3)',
                  color: 'var(--text)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
              >
                <X size={14} />
              </button>
              <button 
                onClick={() => {
                  toggleListening();
                  // Optionally Auto-send when clicking check
                  // handleSend(); 
                }}
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  border: 'none',
                  background: 'var(--primary)',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
              >
                <Check size={14} />
              </button>
            </div>
          </div>
        )}
        
        <div className="input-actions-row">
          <button className="input-action-btn" onClick={() => fileInputRef.current?.click()}>
            <Paperclip size={14} /> <span className="action-btn-text">Attach</span>
          </button>
          <button className="input-action-btn" onClick={() => fileInputRef.current?.click()}>
            <Image size={14} /> <span className="action-btn-text">Upload Media</span>
          </button>
          
          <span className="upload-limits-tip" style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginLeft: "8px", alignSelf: "center" }}>
            Max 10 files (up to 20MB/file)
          </span>

          <div className="model-selector-wrapper" style={{ marginLeft: "auto", position: "relative" }} ref={modelMenuRef}>
            <button 
              className="model-selector-btn" 
              onClick={() => setShowModelMenu(!showModelMenu)}
              title="Select AI Model"
            >
              <span>{MODELS.find(m => m.id === selectedModel)?.name || "Model"}</span>
              <ChevronDown size={14} style={{ marginLeft: 4, opacity: 0.7 }} />
            </button>
            
            {showModelMenu && (
              <div className="model-selector-menu">
                {MODELS.map((m) => (
                  <button 
                    key={m.id} 
                    className={`model-option-btn ${selectedModel === m.id ? "active" : ""}`}
                    onClick={() => {
                      onModelChange(m.id);
                      setShowModelMenu(false);
                    }}
                  >
                    <div className="model-option-text">
                      <span className="model-option-name">{m.name}</span>
                      <span className="model-option-desc">{m.desc}</span>
                    </div>
                    {selectedModel === m.id && <Check size={14} className="model-check-icon" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button 
            onClick={toggleListening}
            className={`mic-btn ${isListening ? "active" : ""}`}
            style={{ 
              marginLeft: "8px", 
              width: "36px", 
              height: "36px", 
              borderRadius: "50%", 
              background: isListening ? "var(--danger)" : "var(--surface-2)", 
              border: "1px solid var(--border)",
              color: isListening ? "#fff" : "var(--text)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              transition: "all 0.2s ease",
              flexShrink: 0
            }}
            title="Speech to text"
          >
            <Mic size={16} />
          </button>

          <button 
            className={`send-btn ${loading ? "stop-mode" : ""}`} 
            onClick={handleSend} 
            disabled={!text.trim() && !loading && attachments.length === 0}
            style={{ marginLeft: "8px" }}
          >
            {loading ? <Square size={14} fill="currentColor" /> : <Send size={16} />}
          </button>
        </div>
      </div>

      <div
        className="context-wrapper"
        onMouseEnter={() => setShowContext(true)}
        onMouseLeave={() => setShowContext(false)}
      >
        <div
          className="context-badge"
          onClick={() => setShowContext(prev => !prev)}
          title="View Token Memory Usage"
        >
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
