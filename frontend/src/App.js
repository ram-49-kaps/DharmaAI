import React, { useState, useEffect } from "react";
import { AlertTriangle, Menu, PanelLeft, Share2, Copy, Check, X } from "lucide-react";
import "./App.css";

import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { setAuthToken, sendMessage, shareChat } from "./services/api";
import Login from "./components/Login";
import SignUp from "./components/SignUp";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import InputBox from "./components/InputBox";
import SourcesPanel from "./components/SourcesPanel";
import TemplatesPanel from "./components/TemplatesPanel";
import PDFUploader from "./components/PDFUploader";
import Logo from "./components/Logo";
import SplashScreen from "./components/SplashScreen";
import SharedChatView from "./components/SharedChatView";
import LevelModal from "./components/LevelModal";

// ── Auth gate — goes directly to Login ────────────────────────────────────────

function AuthGate() {
  const [authView, setAuthView] = useState("login"); // login | signup

  if (authView === "login") {
    return (
      <Login
        onSwitchToSignUp={() => setAuthView("signup")}
      />
    );
  }

  return (
    <SignUp
      onSwitchToLogin={() => setAuthView("login")}
    />
  );
}

// ── Toast component ──────────────────────────────────────────────────────────

function Toast({ message, onDone }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setLeaving(true), 2200);
    const remove = setTimeout(() => onDone?.(), 2500);
    return () => { clearTimeout(timer); clearTimeout(remove); };
  }, [onDone]);

  return (
    <div className={`toast-notification ${leaving ? "toast-out" : ""}`}>
      <Check size={14} /> {message}
    </div>
  );
}

// ── Share Modal ──────────────────────────────────────────────────────────────

function ShareModal({ shareUrl, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="share-overlay" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        <h3><Share2 size={18} /> Share Chat</h3>
        <p>Anyone with this link can view this conversation.</p>
        <div className="share-link-row">
          <input
            className="share-link-input"
            value={shareUrl}
            readOnly
            onFocus={(e) => e.target.select()}
          />
          <button className="share-copy-btn" onClick={handleCopy}>
            {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy</>}
          </button>
        </div>
        <button className="share-close-btn" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

// ── Main app (authenticated) ──────────────────────────────────────────────────

function AppContent() {
  const { user, token, loading, logout } = useAuth();
  const [splashText, setSplashText] = useState("Preparing your legal workspace...");
  const [showSplash, setShowSplash] = useState(false);
  const [wasAuthGateShown, setWasAuthGateShown] = useState(false);
  const [pendingLogout, setPendingLogout] = useState(false);
  const [showLevelModal, setShowLevelModal] = useState(false);

  const prevUserRef = React.useRef(user);

  useEffect(() => {
    if (!prevUserRef.current && user) {
      if (wasAuthGateShown) {
        setSplashText("Preparing your legal workspace...");
        setShowSplash(true);
      }
    }
    prevUserRef.current = user;
  }, [user, wasAuthGateShown]);

  const handleLogout = () => {
    setSplashText("Signing out of DharmaAI...");
    setShowSplash(true);
    setPendingLogout(true);
  };

  const handleSplashComplete = () => {
    if (pendingLogout) {
      setPendingLogout(false);
      setShowSplash(false);
      logout();
    } else {
      sessionStorage.setItem('dharma-splash-seen', 'true');
      setShowSplash(false);
    }
  };

  // Sync Firebase token into axios headers
  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  const [session, setSession] = useState({
    userId: null,
    chats: [{ id: "initial", title: "New Chat", messages: [] }],
    activeChatId: "initial",
  });
  const { chats, activeChatId } = session;

  useEffect(() => {
    const currentUid = user ? user.uid : null;
    if (session.userId !== currentUid) {
      if (currentUid) {
        let savedChats = localStorage.getItem(`dharma-chats-${currentUid}`);
        let savedActiveId = localStorage.getItem(`dharma-active-chat-id-${currentUid}`);
        
        // Migrate legacy single-user chats to user-scoped keys
        if (!savedChats) {
          const legacyChats = localStorage.getItem("dharma-chats");
          const legacyActiveId = localStorage.getItem("dharma-active-chat-id");
          if (legacyChats) {
            savedChats = legacyChats;
            savedActiveId = legacyActiveId;
            localStorage.setItem(`dharma-chats-${currentUid}`, legacyChats);
            if (legacyActiveId) {
              localStorage.setItem(`dharma-active-chat-id-${currentUid}`, legacyActiveId);
            }
            localStorage.removeItem("dharma-chats");
            localStorage.removeItem("dharma-active-chat-id");
          }
        }

        setSession({
          userId: currentUid,
          chats: savedChats ? JSON.parse(savedChats) : [{ id: "initial", title: "New Chat", messages: [] }],
          activeChatId: savedActiveId || "initial",
        });
      } else {
        setSession({
          userId: null,
          chats: [{ id: "initial", title: "New Chat", messages: [] }],
          activeChatId: "initial",
        });
      }
    }
  }, [user, session.userId]);

  useEffect(() => {
    if (user && session.userId === user.uid) {
      localStorage.setItem(`dharma-chats-${user.uid}`, JSON.stringify(session.chats));
      localStorage.setItem(`dharma-active-chat-id-${user.uid}`, session.activeChatId);
    }
  }, [session, user]);

  // Check if user level profile exists, if not, show select modal
  useEffect(() => {
    if (user && !showSplash) {
      const userProfileKey = `dharma-profile-${user.uid}`;
      let profile = localStorage.getItem(userProfileKey);
      
      // Migrate legacy profile
      if (!profile) {
        const legacyProfile = localStorage.getItem("dharma-profile");
        if (legacyProfile) {
          profile = legacyProfile;
          localStorage.setItem(userProfileKey, legacyProfile);
          localStorage.removeItem("dharma-profile");
        }
      }

      if (!profile) {
        setShowLevelModal(true);
      } else {
        try {
          const parsed = JSON.parse(profile);
          if (!parsed.level) {
            setShowLevelModal(true);
          }
        } catch {
          setShowLevelModal(true);
        }
      }
    }
  }, [user, showSplash]);
  const [isLoadingReply, setIsLoadingReply] = useState(false);
  const [abortController, setAbortController] = useState(null);
  const [activePanel, setActivePanel] = useState("chat");
  const [prefillText, setPrefillText] = useState("");
  const [error, setError] = useState("");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showUploader, setShowUploader] = useState(false);
  const [toast, setToast] = useState("");
  const [shareModal, setShareModal] = useState(null); // { shareUrl }

  // Default to light mode for first-time users
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("dharma-theme");
    if (saved) return saved;
    // First time user → light mode
    return "light";
  });

  useEffect(() => {
    localStorage.setItem("dharma-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  const activeChat = chats.find((c) => c.id === activeChatId) || chats[0];
  const messages = activeChat.messages;
  const latestSources = [...messages].reverse().find((m) => m.role === "assistant")?.sources || [];

  if (loading) {
    return (
      <div className="app-skeleton-layout" data-theme={theme}>
        {/* Sidebar Skeleton */}
        <aside className="sidebar">
          <div className="skeleton-pulse" style={{ height: "36px", marginBottom: "1rem", borderRadius: "8px" }} />
          <div className="skeleton-pulse" style={{ height: "45px", marginBottom: "1.5rem", borderRadius: "12px" }} />
          <div className="skeleton-pulse" style={{ height: "36px", marginBottom: "1.5rem", borderRadius: "8px" }} />
          <div className="sidebar-section">
            <div className="skeleton-pulse" style={{ width: "60%", height: "14px", marginBottom: "1rem", borderRadius: "4px" }} />
            <div className="skeleton-pulse" style={{ height: "36px", marginBottom: "0.5rem", borderRadius: "8px" }} />
            <div className="skeleton-pulse" style={{ height: "36px", marginBottom: "0.5rem", borderRadius: "8px" }} />
            <div className="skeleton-pulse" style={{ height: "36px", marginBottom: "0.5rem", borderRadius: "8px" }} />
          </div>
          <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <div className="skeleton-pulse" style={{ height: "36px", borderRadius: "8px" }} />
            <div className="skeleton-pulse" style={{ height: "36px", borderRadius: "8px" }} />
            <div className="skeleton-pulse" style={{ height: "50px", borderRadius: "8px" }} />
          </div>
        </aside>

        {/* Main Content Area Skeleton */}
        <main className="main-area">
          <div className="mobile-header skeleton-pulse" style={{ height: "50px" }} />
          <div className="chat-window">
            <div className="skeleton-message-list">
              {[1, 2, 3, 4, 5].map((item) => (
                <div key={item} className="skeleton-message-card">
                  <div className="skeleton-avatar skeleton-pulse" />
                  <div className="skeleton-text-lines">
                    <div className="skeleton-pulse" style={{ width: "85%", height: "12px", borderRadius: "4px" }} />
                    <div className="skeleton-pulse" style={{ width: "60%", height: "12px", marginTop: "8px", borderRadius: "4px" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div style={{ padding: "1.5rem", borderTop: "1px solid var(--border)" }}>
            <div className="skeleton-pulse" style={{ height: "50px", borderRadius: "12px" }} />
          </div>
        </main>
      </div>
    );
  }

  if (!user) {
    if (!wasAuthGateShown) {
      setWasAuthGateShown(true);
    }
    return <AuthGate />;
  }

  if (showSplash) {
    return (
      <SplashScreen 
        text={splashText}
        onComplete={handleSplashComplete} 
      />
    );
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  const updateActiveChat = (newMessages, newTitle = activeChat.title) => {
    setSession((prev) => ({
      ...prev,
      chats: prev.chats.map((c) =>
        c.id === prev.activeChatId ? { ...c, messages: newMessages, title: newTitle } : c
      ),
    }));
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsLoadingReply(false);
      setError("Response cancelled by user.");
    }
  };

  const handleSend = async (text, attachments = []) => {
    if (isLoadingReply) {
      handleStop();
      return;
    }

    // Process attachments to generate persistent Base64 previews for images
    const processedAttachments = [];
    for (const att of attachments) {
      let previewData = att.preview;
      if (att.file && att.type?.startsWith("image/")) {
        try {
          previewData = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.readAsDataURL(att.file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => resolve(null);
          });
        } catch (e) {
          console.error("Base64 conversion failed", e);
        }
      }
      processedAttachments.push({
        name: att.name,
        size: att.size,
        type: att.type,
        preview: previewData || att.preview,
      });
    }

    const attachmentLabel = attachments.length
      ? `\n\nAttached: ${attachments.map((att) => att.name).join(", ")}`
      : "";
    const displayText = `${text}${attachmentLabel}`.trim() || "Attached files";
    const userMsg = { 
      role: "user", 
      content: displayText, 
      attachments: processedAttachments 
    };
    const updatedMessages = [...messages, userMsg];

    let newTitle = activeChat.title;
    if (messages.length === 0) {
      newTitle = displayText.length > 35 ? displayText.slice(0, 35) + "…" : displayText;
    }

    updateActiveChat(updatedMessages, newTitle);
    setIsLoadingReply(true);
    setError("");
    setActivePanel("chat");

    const controller = new AbortController();
    setAbortController(controller);

    const history = updatedMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      let savedProfile = {};
      try {
        const profileKey = user ? `dharma-profile-${user.uid}` : "dharma-profile";
        savedProfile = JSON.parse(localStorage.getItem(profileKey) || "{}");
      } catch {
        savedProfile = {};
      }
      const response = await sendMessage(
        text,
        history,
        activeChatId,
        controller.signal,
        attachments,
        savedProfile.level || null
      );
      updateActiveChat(
        [
          ...updatedMessages,
          {
            role: "assistant",
            content: response.answer,
            intent: response.intent,
            sources: response.sources || [],
            citations: response.citations || [],
            suggested_questions: response.suggested_questions || [],
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

  // ── Edit message (ChatGPT-style: truncate + regenerate) ────────────────────

  const handleEditMessage = async (index, newContent) => {
    // Truncate to the edited message, replace its content, then re-send
    const truncated = messages.slice(0, index);
    const originalMsg = messages[index];
    const originalAttachments = originalMsg?.attachments || [];

    const attachmentLabel = originalAttachments.length
      ? `\n\nAttached: ${originalAttachments.map((att) => att.name).join(", ")}`
      : "";
    const fullContent = `${newContent}${attachmentLabel}`.trim();

    const editedUserMsg = { 
      role: "user", 
      content: fullContent,
      attachments: originalAttachments
    };
    const updatedMessages = [...truncated, editedUserMsg];

    let newTitle = activeChat.title;
    if (index === 0) {
      newTitle = newContent.length > 35 ? newContent.slice(0, 35) + "…" : newContent;
    }

    updateActiveChat(updatedMessages, newTitle);
    setIsLoadingReply(true);
    setError("");

    const controller = new AbortController();
    setAbortController(controller);

    const history = updatedMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      let savedProfile = {};
      try {
        const profileKey = user ? `dharma-profile-${user.uid}` : "dharma-profile";
        savedProfile = JSON.parse(localStorage.getItem(profileKey) || "{}");
      } catch {
        savedProfile = {};
      }
      const response = await sendMessage(
        newContent,
        history,
        activeChatId,
        controller.signal,
        [],
        savedProfile.level || null
      );
      updateActiveChat(
        [
          ...updatedMessages,
          {
            role: "assistant",
            content: response.answer,
            intent: response.intent,
            sources: response.sources || [],
            citations: response.citations || [],
            suggested_questions: response.suggested_questions || [],
          },
        ],
        newTitle
      );
    } catch (err) {
      if (err.name === "AbortError" || err.message === "canceled") return;
      const errText = err?.response?.data?.detail || "Failed to regenerate response.";
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

  const handleRegenerate = async (index) => {
    if (index > 0 && messages[index - 1]) {
      await handleEditMessage(index - 1, messages[index - 1].content);
    }
  };

  // ── Share chat ─────────────────────────────────────────────────────────────

  const handleShareChat = async () => {
    if (messages.length === 0) return;
    try {
      const shareable = messages.map((m) => ({
        role: m.role,
        content: m.content,
        intent: m.intent || undefined,
      }));
      const result = await shareChat(activeChat.title, shareable);
      setShareModal({ shareUrl: result.share_url });
    } catch (err) {
      console.error("Share failed:", err);
      setToast("Failed to create share link");
    }
  };

  const handleNewChat = () => {
    if (messages.length > 0) {
      const newId = Date.now().toString();
      setSession((prev) => ({
        ...prev,
        chats: [{ id: newId, title: "New Chat", messages: [] }, ...prev.chats],
        activeChatId: newId,
      }));
    }
    setError("");
    setPrefillText("");
    setActivePanel("chat");
  };

  const switchChat = (id) => {
    setSession((prev) => ({ ...prev, activeChatId: id }));
    setActivePanel("chat");
    setIsMobileMenuOpen(false);
  };

  const deleteChat = (id) => {
    setSession((prev) => {
      const updated = prev.chats.filter((c) => c.id !== id);
      let newActiveId = prev.activeChatId;
      let newChats = updated;
      if (updated.length === 0) {
        const newId = Date.now().toString();
        newChats = [{ id: newId, title: "New Chat", messages: [] }];
        newActiveId = newId;
      } else if (prev.activeChatId === id) {
        newActiveId = updated[0].id;
      }
      return {
        ...prev,
        chats: newChats,
        activeChatId: newActiveId,
      };
    });
  };

  const renameChat = (id, newTitle) =>
    setSession((prev) => ({
      ...prev,
      chats: prev.chats.map((c) => (c.id === id ? { ...c, title: newTitle } : c)),
    }));

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
    <div className={`app-layout ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`} data-theme={theme}>
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
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(prev => !prev)}
        onLogout={handleLogout}
      />

      <main className="main-area">
        {/* Floating sidebar open button (visible when collapsed) */}
        {isSidebarCollapsed && (
          <div className="tooltip-wrap" style={{ position: "absolute", top: "14px", left: "14px", zIndex: 50 }}>
            <button
              className="sidebar-open-btn"
              onClick={() => setIsSidebarCollapsed(false)}
              style={{ position: "static" }}
            >
              <PanelLeft size={20} />
            </button>
            <div className="tooltip-content tooltip-bottom-left">
              Open sidebar
            </div>
          </div>
        )}

        <div className="mobile-header">
          <button className="menu-btn" onClick={() => setIsMobileMenuOpen(true)}>
            <Menu size={24} />
          </button>
          <div className="mobile-header-brand">
            <Logo size={20} />
            <strong>DharmaAI</strong>
          </div>
        </div>

        {activePanel === "chat" && (
          <>
            <ChatWindow
              messages={messages}
              loading={isLoadingReply}
              onFeatureClick={(prefix) => { setPrefillText(prefix); setActivePanel("chat"); }}
              userName={user?.displayName || user?.email?.split("@")[0] || ""}
              onEditMessage={handleEditMessage}
              onShareChat={handleShareChat}
              sessionId={activeChatId}
              onRegenerate={handleRegenerate}
              onSendSuggested={handleSend}
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

      {/* Share modal */}
      {shareModal && (
        <ShareModal
          shareUrl={shareModal.shareUrl}
          onClose={() => setShareModal(null)}
        />
      )}

      {/* Toast notification */}
      {toast && <Toast message={toast} onDone={() => setToast("")} />}

      {/* Level Selection Modal */}
      {showLevelModal && (
        <LevelModal onSave={() => setShowLevelModal(false)} />
      )}
    </div>
  );
}

// ── Root with provider ────────────────────────────────────────────────────────

export default function App() {
  // Check for shared chat URL parameter
  const params = new URLSearchParams(window.location.search);
  const shareId = params.get("share");

  if (shareId) {
    return <SharedChatView shareId={shareId} />;
  }

  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
