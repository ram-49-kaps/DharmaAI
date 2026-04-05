import React, { useState } from "react";
import { AlertTriangle, Menu, Scale } from "lucide-react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import InputBox from "./components/InputBox";
import SourcesPanel from "./components/SourcesPanel";
import TemplatesPanel from "./components/TemplatesPanel";
import { sendMessage } from "./services/api";
import Logo from "./components/Logo";

export default function App() {
  const [chats, setChats] = useState([
    { id: "initial", title: "New Consultation", messages: [] }
  ]);
  const [activeChatId, setActiveChatId] = useState("initial");

  const [loading, setLoading] = useState(false);
  const [activePanel, setActivePanel] = useState("chat");
  const [prefillText, setPrefillText] = useState("");
  const [error, setError] = useState("");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];
  const messages = activeChat.messages;

  const latestSources = [...messages].reverse().find((m) => m.role === "assistant")?.sources || [];

  const updateActiveChat = (newMessages, newTitle = activeChat.title) => {
    setChats(prev => prev.map(c =>
      c.id === activeChatId
        ? { ...c, messages: newMessages, title: newTitle }
        : c
    ));
  };

  const handleSend = async (text) => {
    const userMsg = { role: "user", content: text };
    const updatedMessages = [...messages, userMsg];

    // Auto-generate title on the very first message sent
    let newTitle = activeChat.title;
    if (messages.length === 0) {
      newTitle = text.length > 25 ? text.slice(0, 25) + "..." : text;
    }

    updateActiveChat(updatedMessages, newTitle);
    setLoading(true);
    setError("");
    setActivePanel("chat");

    const history = updatedMessages.slice(-12).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const response = await sendMessage(text, history);
      updateActiveChat([
        ...updatedMessages,
        {
          role: "assistant",
          content: response.answer,
          intent: response.intent,
          sources: response.sources,
        },
      ], newTitle);
    } catch (err) {
      const errText = err?.response?.data?.detail || "Backend error. Is your FastAPI server running on port 8000?";
      setError(errText);
      updateActiveChat([
        ...updatedMessages,
        { role: "assistant", content: errText, intent: "general", sources: [] },
      ], newTitle);
    } finally {
      setLoading(false);
    }
  };

  const handleUseTemplate = (prefix) => {
    setPrefillText(prefix);
    setActivePanel("chat");
  };

  const handleNewChat = () => {
    if (messages.length > 0) {
      const newId = Date.now().toString();
      setChats(prev => [{ id: newId, title: "New Consultation", messages: [] }, ...prev]);
      setActiveChatId(newId);
    }
    setError("");
    setPrefillText("");
    setActivePanel("chat");
  };

  const switchChat = (id) => {
    setActiveChatId(id);
    setActivePanel("chat");
    setIsMobileMenuOpen(false);
  };

  const deleteChat = (id) => {
    const updatedChats = chats.filter(c => c.id !== id);
    if (updatedChats.length === 0) {
      const newId = Date.now().toString();
      setChats([{ id: newId, title: "New Consultation", messages: [] }]);
      setActiveChatId(newId);
    } else {
      setChats(updatedChats);
      if (activeChatId === id) {
        setActiveChatId(updatedChats[0].id);
      }
    }
  };

  const renameChat = (id, newTitle) => {
    setChats(prev => prev.map(c => c.id === id ? { ...c, title: newTitle } : c));
  };

  const handleExport = () => {
    const lines = messages.map((m) => {
      const role = m.role === "user" ? "YOU" : "DHARMAAI";
      const badge = m.intent ? ` [${m.intent.toUpperCase()}]` : "";
      return `${role}${badge}:\n${m.content}\n`;
    });
    const blob = new Blob([lines.join("\n---\n\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dharmaai-chat-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app-layout">
      {/* Mobile Backdrop */}
      {isMobileMenuOpen && (
        <div className="mobile-backdrop" onClick={() => setIsMobileMenuOpen(false)} />
      )}

      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={() => { handleNewChat(); setIsMobileMenuOpen(false); }}
        onSwitchChat={switchChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
        onExport={handleExport}
        activePanel={activePanel}
        setActivePanel={(panel) => { setActivePanel(panel); setIsMobileMenuOpen(false); }}
        isExportDisabled={messages.length === 0}
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      <main className="main-area">
        {/* Mobile Header (Hidden on Desktop) */}
        <div className="mobile-header">
          <button className="menu-btn" onClick={() => setIsMobileMenuOpen(true)}>
            <Menu size={24} />
          </button>
          <div className="mobile-header-brand">
            <Logo size={20} color="var(--primary)" />
            <strong>DharmaAI</strong>
          </div>
        </div>
        {activePanel === "chat" && (
          <>
            <ChatWindow messages={messages} loading={loading} onFeatureClick={handleUseTemplate} />
            {error && <div className="error-banner"><AlertTriangle size={16} style={{ marginRight: 6 }} /> {error}</div>}
            <InputBox
              onSend={handleSend}
              loading={loading}
              prefillText={prefillText}
              onPrefillUsed={() => setPrefillText("")}
              messages={messages}
              onCompactContext={handleNewChat}
            />
          </>
        )}

        {activePanel === "sources" && (
          <div className="panel-page">
            <SourcesPanel
              sources={latestSources}
              onDocumentClick={(title) => {
                setPrefillText(`Tell me more about ${title}: `);
                setActivePanel("chat");
              }}
            />
          </div>
        )}

        {activePanel === "templates" && (
          <div className="panel-page">
            <TemplatesPanel onUseTemplate={handleUseTemplate} />
          </div>
        )}
      </main>
    </div>
  );
}
