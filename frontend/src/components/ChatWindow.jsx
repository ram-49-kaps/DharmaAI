import React, { useEffect, useRef, useState } from "react";
import { Scale, ScrollText, Landmark, BookOpen, BrainCircuit, Flower2, Loader2, ArrowRight } from "lucide-react";
import MessageBubble from "./MessageBubble";
import Logo from "./Logo";

const THINKING_STEPS = [
  "Analyzing your query...",
  "Searching knowledge base...",
  "Retrieving relevant case law...",
  "Cross-referencing statutes...",
  "Preparing comprehensive response...",
];

function ThinkingAnimation() {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % THINKING_STEPS.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="thinking-animation">
      <div className="thinking-icon">
        <Logo size={22} />
      </div>
      <div className="thinking-content">
        <div className="thinking-header">
          <span className="thinking-pulse-dot" />
          <span className="thinking-text">{THINKING_STEPS[stepIndex]}</span>
        </div>
        <div className="thinking-visual">
          <div className="thinking-line" />
          <div className="thinking-glow-wave" />
        </div>
      </div>
    </div>
  );
}

export default function ChatWindow({ messages, loading, onFeatureClick, userName, onEditMessage, onShareChat, sessionId, onRegenerate }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (messages.length > 0 || loading) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const greeting = userName ? `Welcome, ${userName}` : "Welcome to DharmaAI";

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="welcome">
          <div className="welcome-brand"><Logo size={48} /></div>
          <h2>{greeting}</h2>
          <p>
            Your AI-powered legal research companion — bridging the Indian Knowledge
            System with modern jurisprudence. Ask about case law, statutes,
            legal definitions, or apply structured reasoning frameworks like
            IRAC, FILAC, and IDAR to any legal scenario.
          </p>
          <div className="welcome-features">
            <div className="feature-card" onClick={() => onFeatureClick?.("Explain the case law for: ")} style={{cursor: "pointer"}}>
              <span className="feature-label">Explain the case law for a specific scenario</span>
              <span className="feature-icon"><ScrollText size={20} /></span>
              <span className="feature-arrow"><ArrowRight size={18} /></span>
            </div>
            <div className="feature-card" onClick={() => onFeatureClick?.("Look up the statute: ")} style={{cursor: "pointer"}}>
              <span className="feature-label">Look up the statute for a specific act</span>
              <span className="feature-icon"><Landmark size={20} /></span>
              <span className="feature-arrow"><ArrowRight size={18} /></span>
            </div>
            <div className="feature-card" onClick={() => onFeatureClick?.("Apply the IRAC reasoning method to this scenario: ")} style={{cursor: "pointer"}}>
              <span className="feature-label">Apply the IRAC reasoning method</span>
              <span className="feature-icon"><BrainCircuit size={20} /></span>
              <span className="feature-arrow"><ArrowRight size={18} /></span>
            </div>
            <div className="feature-card" onClick={() => onFeatureClick?.("What is the Dharma and IKS perspective on: ")} style={{cursor: "pointer"}}>
              <span className="feature-label">Explore the Dharma and IKS perspective</span>
              <span className="feature-icon"><Flower2 size={20} /></span>
              <span className="feature-arrow"><ArrowRight size={18} /></span>
            </div>
          </div>
        </div>
      ) : (
        messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            messageIndex={i}
            onEditMessage={onEditMessage}
            onShareChat={onShareChat}
            sessionId={sessionId}
            onRegenerate={onRegenerate}
          />
        ))
      )}

      {loading && <ThinkingAnimation />}


      <div ref={bottomRef} />
    </div>
  );
}

