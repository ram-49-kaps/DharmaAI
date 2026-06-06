import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import MessageBubble from "./MessageBubble";
import Logo from "./Logo";
import { getSharedChat } from "../services/api";

export default function SharedChatView({ shareId }) {
  const [chat, setChat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchChat = async () => {
      try {
        const data = await getSharedChat(shareId);
        setChat(data);
      } catch (err) {
        setError("This shared chat was not found or has been deleted.");
      } finally {
        setLoading(false);
      }
    };
    fetchChat();
  }, [shareId]);

  if (loading) {
    return (
      <div className="shared-chat-page" data-theme="light">
        <div style={{ margin: "auto", display: "flex", alignItems: "center", gap: "0.75rem", color: "var(--text-secondary)" }}>
          <Loader2 size={20} className="thinking-spin-icon" />
          Loading shared chat...
        </div>
      </div>
    );
  }

  if (error || !chat) {
    return (
      <div className="shared-chat-page" data-theme="light">
        <div className="shared-chat-header">
          <div className="shared-chat-brand">
            <Logo size={24} />
            <h2>DharmaAI</h2>
          </div>
          <a href="/" className="shared-chat-cta">Open DharmaAI</a>
        </div>
        <div style={{ margin: "auto", textAlign: "center", color: "var(--text-secondary)", padding: "2rem" }}>
          <p style={{ fontSize: "1.1rem", fontWeight: 600 }}>{error || "Chat not found"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="shared-chat-page" data-theme="light">
      <div className="shared-chat-header">
        <div className="shared-chat-brand">
          <Logo size={24} />
          <h2>DharmaAI</h2>
        </div>
        <a href="/" className="shared-chat-cta">Continue in DharmaAI</a>
      </div>

      <div className="shared-chat-body">
        {chat.messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} messageIndex={i} />
        ))}
      </div>

      <div className="shared-chat-footer">
        Shared from DharmaAI — AI-powered Indian legal research &bull; {chat.created_at ? new Date(chat.created_at).toLocaleDateString() : ""}
      </div>
    </div>
  );
}
