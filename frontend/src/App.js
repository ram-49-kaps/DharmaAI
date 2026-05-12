import React, { useState, useEffect } from "react";
import { AlertTriangle, Menu } from "lucide-react";
import "./App.css";

import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { setAuthToken, sendMessage } from "./services/api";
import Login from "./components/Login";
import SignUp from "./components/SignUp";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import InputBox from "./components/InputBox";
import SourcesPanel from "./components/SourcesPanel";
import TemplatesPanel from "./components/TemplatesPanel";
import PDFUploader from "./components/PDFUploader";
import Logo from "./components/Logo";

// ── Auth gate ─────────────────────────────────────────────────────────────────

function AuthGate() {
  const [authView, setAuthView] = useState("login");
  if (authView === "login") return <Login onSwitchToSignUp={() => setAuthView("signup")} />;
  return <SignUp onSwitchToLogin={() => setAuthView("login")} />;
}

// ── Main app (authenticated) ──────────────────────────────────────────────────

function AppContent() {
  const { user, token, loading } = useAuth();

  // Sync Firebase token into axios headers
  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  const [chats, setChats] = useState([
    { id: "initial", title: "New Consultation", messages: [] }
  ]);
  const [activeChatId, setActiveChatId] = useState("initial");
  const [isLoadingReply, setIsLoadingReply] = useState(false);
  const [abortController, setAbortController] = useState(null);
  const [activePanel, setActivePanel] = useState("chat");
  const [prefillText, setPrefillText] = useState("");
  const [error, setError] = useState("");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showUploader, setShowUploader] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem("dharma-theme") || "light");

  useEffect(() => {
    localStorage.setItem("dharma-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  const activeChat = chats.find((c) => c.id === activeChatId) || chats[0];
  const messages = activeChat.messages;
  const latestSources = [...messages].reverse().find((m) => m.role === "assistant")?.sources || [];

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <Logo size={32} color="var(--primary)" />
      </div>
    );
  }

  if (!user) return <AuthGate />;

  // ── Helpers ────────────────────────────────────────────────────────────────

  const updateActiveChat = (newMessages, newTitle = activeChat.title) => {
    setChats((prev) =>
      prev.map((c) =>
        c.id === activeChatId ? { ...c, messages: newMessages, title: newTitle } : c
      )
    );
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsLoadingReply(false);
      setError("Response cancelled by user.");
    }
  };

  const handleSend = async (text) => {
    if (isLoadingReply) {
      handleStop();
      return;
    }

    const userMsg = { role: "user", content: text };
    const updatedMessages = [...messages, userMsg];

    let newTitle = activeChat.title;
    if (messages.length === 0) {
      newTitle = text.length > 35 ? text.slice(0, 35) + "…" : text;
    }

    updateActiveChat(updatedMessages, newTitle);
    setIsLoadingReply(true);
    setError("");
    setActivePanel("chat");

    const controller = new AbortController();
    setAbortController(controller);

    const history = updatedMessages.slice(-12).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const response = await sendMessage(text, history, activeChatId, controller.signal);
      updateActiveChat(
        [
          ...updatedMessages,
          {
            role: "assistant",
            content: response.answer,
            intent: response.intent,
            sources: response.sources || [],
            citations: response.citations || [],
          },
        ],
        newTitle
      );
    } catch (err) {
      if (err.name === "AbortError" || err.message === "canceled") {
        console.log("Request aborted");
        return;
      }
      const errText =
        err?.response?.data?.detail ||
        "Backend error. Is your FastAPI server running on port 8000?";
      setError(errText);
      updateActiveChat(
        [...updatedMessages, { role: "assistant", content: errText, intent: "general_qa", sources: [] }],
        newTitle
      );
    } finally {
      setIsLoadingReply(false);
      setAbortController(null);
    }
  };

  const handleNewChat = () => {
    if (messages.length > 0) {
      const newId = Date.now().toString();
      setChats((prev) => [{ id: newId, title: "New Consultation", messages: [] }, ...prev]);
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
    const updated = chats.filter((c) => c.id !== id);
    if (updated.length === 0) {
      const newId = Date.now().toString();
      setChats([{ id: newId, title: "New Consultation", messages: [] }]);
      setActiveChatId(newId);
    } else {
      setChats(updated);
      if (activeChatId === id) setActiveChatId(updated[0].id);
    }
  };

  const renameChat = (id, newTitle) =>
    setChats((prev) => prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c)));

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
    a.download = `dharmaai-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="app-layout" data-theme={theme}>
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
        onOpenUploader={() => setShowUploader(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main className="main-area">
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
            <ChatWindow
              messages={messages}
              loading={isLoadingReply}
              onFeatureClick={(prefix) => { setPrefillText(prefix); setActivePanel("chat"); }}
            />
            {error && (
              <div className="error-banner">
                <AlertTriangle size={16} style={{ marginRight: 6 }} /> {error}
              </div>
            )}
            <InputBox
              onSend={handleSend}
              loading={isLoadingReply}
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
            <TemplatesPanel
              onUseTemplate={(prefix) => { setPrefillText(prefix); setActivePanel("chat"); }}
            />
          </div>
        )}
      </main>

      {showUploader && <PDFUploader onClose={() => setShowUploader(false)} />}
    </div>
  );
}

// ── Root with provider ────────────────────────────────────────────────────────

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
