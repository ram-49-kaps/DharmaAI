import React, { useEffect, useRef } from "react";
import { Scale, ScrollText, Landmark, BookOpen, BrainCircuit, Flower2 } from "lucide-react";
import MessageBubble from "./MessageBubble";
import Logo from "./Logo";

export default function ChatWindow({ messages, loading, onFeatureClick }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="welcome">
          <div className="welcome-brand"><Logo size={48} color="white" /></div>
          <h2>Welcome to <span>DharmaAI</span></h2>
          <p>
            Your intelligent legal research companion — grounded in the
            Indian Knowledge System (IKS) and modern Indian jurisprudence.
            Ask about case law, statutes, legal definitions, or apply
            structured reasoning frameworks.
          </p>
          <div className="welcome-features">
            <div className="feature-card" onClick={() => onFeatureClick?.("Explain the case law for: ")} style={{cursor: "pointer"}}>
              <span className="feature-icon"><ScrollText size={26} color="var(--primary)" /></span>
              <span className="feature-label">Case Law Analysis</span>
            </div>
            <div className="feature-card" onClick={() => onFeatureClick?.("Look up the statute: ")} style={{cursor: "pointer"}}>
              <span className="feature-icon"><Landmark size={26} color="var(--primary)" /></span>
              <span className="feature-label">Statute Lookup</span>
            </div>
            <div className="feature-card" onClick={() => onFeatureClick?.("Define the legal term: ")} style={{cursor: "pointer"}}>
              <span className="feature-icon"><BookOpen size={26} color="var(--primary)" /></span>
              <span className="feature-label">Legal Definitions</span>
            </div>
            <div className="feature-card" onClick={() => onFeatureClick?.("Apply the IRAC reasoning method to this scenario: ")} style={{cursor: "pointer"}}>
              <span className="feature-icon"><BrainCircuit size={26} color="var(--secondary)" /></span>
              <span className="feature-label">IRAC Reasoning</span>
            </div>
            <div className="feature-card" onClick={() => onFeatureClick?.("What is the Dharma and IKS perspective on: ")} style={{cursor: "pointer"}}>
              <span className="feature-icon"><Flower2 size={26} color="var(--intent-idar)" /></span>
              <span className="feature-label">Dharma & IKS</span>
            </div>
          </div>
        </div>
      ) : (
        messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))
      )}

      {loading && (
        <div className="message assistant">
          <div className="avatar ai-avatar"><Logo size={20} color="white" /></div>
          <div className="bubble ai-bubble typing-bubble">
            <span className="dot" /><span className="dot" /><span className="dot" />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
