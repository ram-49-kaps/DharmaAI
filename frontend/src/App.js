import React, { useState, useEffect } from "react";
import { AlertTriangle, Menu, PanelLeft, Share2, Copy, Check, X } from "lucide-react";
import "./App.css";

import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { setAuthToken, sendMessage, shareChat, getThinkingSteps, getSessions, getSessionMessages, deleteSession, getProfile, updateProfile } from "./services/api";
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

const DEFAULT_THINKING_STEPS = [
  "Analyzing legal query...",
  "Searching jurisprudential records...",
  "Preparing comprehensive synthesis..."
];

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

  const [userProfile, setUserProfile] = useState(null);

  const [session, setSession] = useState({
    userId: null,
    chats: [{ id: "initial", title: "New Chat", messages: [], loaded: true }],
    activeChatId: "initial",
  });
  const { chats, activeChatId } = session;

  // Load sessions + profile from backend when user logs in
  useEffect(() => {
    const currentUid = user ? user.uid : null;
    if (session.userId !== currentUid) {
      if (currentUid) {
        // Load chat sessions from backend
        getSessions().then(({ sessions }) => {
          const backendChats = sessions.map((s) => ({
            id: s.session_id,
            title: s.title,
            messages: [],
            loaded: false,
          }));
          const chatsToSet = backendChats.length > 0
            ? backendChats
            : [{ id: "initial-" + Date.now(), title: "New Chat", messages: [], loaded: true }];
          setSession({
            userId: currentUid,
            chats: chatsToSet,
            activeChatId: chatsToSet[0].id,
          });
        }).catch(() => {
          setSession({
            userId: currentUid,
            chats: [{ id: "initial-" + Date.now(), title: "New Chat", messages: [], loaded: true }],
            activeChatId: "initial-" + Date.now(),
          });
        });

        // Load profile from backend
        getProfile().then((profile) => {
          setUserProfile(profile);
          if (!profile.level) setShowLevelModal(true);
        }).catch(() => {
          setShowLevelModal(true);
        });
      } else {
        setSession({
          userId: null,
          chats: [{ id: "initial", title: "New Chat", messages: [], loaded: true }],
          activeChatId: "initial",
        });
        setUserProfile(null);
      }
    }
  }, [user, session.userId]);
  const [isLoadingReply, setIsLoadingReply] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState(DEFAULT_THINKING_STEPS);
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

  const profileName = userProfile?.name || user?.displayName || user?.email?.split("@")[0] || "Ram";

  const [greetingText, setGreetingText] = useState("");

  useEffect(() => {
    if (!profileName) return;
    const hour = new Date().getHours();
    const greetings = [];
    if (hour >= 5 && hour < 12) {
      greetings.push(`Good morning, ${profileName}!`);
      greetings.push(`Start your morning research, ${profileName}.`);
      greetings.push(`What legal queries shall we resolve this morning, ${profileName}?`);
    } else if (hour >= 12 && hour < 17) {
      greetings.push(`Good afternoon, ${profileName}!`);
      greetings.push(`Ready for some afternoon legal research, ${profileName}?`);
      greetings.push(`How is your research shaping up this afternoon, ${profileName}?`);
    } else if (hour >= 17 && hour < 22) {
      greetings.push(`Good evening, ${profileName}!`);
      greetings.push(`Let's wrap up today's case laws, ${profileName}.`);
      greetings.push(`What constitutional laws are we checking this evening, ${profileName}?`);
    } else {
      greetings.push(`Working late, ${profileName}?`);
      greetings.push(`Hello, ${profileName}. Burning the midnight oil?`);
      greetings.push(`Need help with late-night legal analysis, ${profileName}?`);
    }
    const randomIndex = Math.floor(Math.random() * greetings.length);
    setGreetingText(greetings[randomIndex]);
  }, [profileName]);

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
    setThinkingSteps(DEFAULT_THINKING_STEPS);
    getThinkingSteps(text || "Analyzing attached files")
      .then((steps) => {
        if (Array.isArray(steps) && steps.length > 0) {
          setThinkingSteps(steps);
        }
      })
      .catch((err) => {
        console.error("Thinking steps fetch failed:", err);
      });
    setError("");
    setActivePanel("chat");

    const controller = new AbortController();
    setAbortController(controller);

    const history = updatedMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const response = await sendMessage(
        text,
        history,
        activeChatId,
        controller.signal,
        attachments,
        userProfile?.level || null
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
    setThinkingSteps(DEFAULT_THINKING_STEPS);
    getThinkingSteps(newContent || "Regenerating response")
      .then((steps) => {
        if (Array.isArray(steps) && steps.length > 0) {
          setThinkingSteps(steps);
        }
      })
      .catch((err) => {
        console.error("Thinking steps fetch failed:", err);
      });
    setError("");

    const controller = new AbortController();
    setAbortController(controller);

    const history = updatedMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const response = await sendMessage(
        newContent,
        history,
        activeChatId,
        controller.signal,
        [],
        userProfile?.level || null
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
        chats: [{ id: newId, title: "New Chat", messages: [], loaded: true }, ...prev.chats],
        activeChatId: newId,
      }));
    }
    setError("");
    setPrefillText("");
    setActivePanel("chat");
  };

  const switchChat = async (id) => {
    setSession((prev) => ({ ...prev, activeChatId: id }));
    setActivePanel("chat");
    setIsMobileMenuOpen(false);

    // Lazy-load messages from backend if not yet fetched
    const chat = session.chats.find((c) => c.id === id);
    if (chat && !chat.loaded) {
      try {
        const data = await getSessionMessages(id);
        setSession((prev) => ({
          ...prev,
          chats: prev.chats.map((c) =>
            c.id === id
              ? { ...c, messages: data.messages.map((m) => ({ role: m.role, content: m.content })), loaded: true }
              : c
          ),
        }));
      } catch {
        setSession((prev) => ({
          ...prev,
          chats: prev.chats.map((c) => (c.id === id ? { ...c, loaded: true } : c)),
        }));
      }
    }
  };

  const deleteChat = (id) => {
    deleteSession(id).catch(() => {});
    setSession((prev) => {
      const updated = prev.chats.filter((c) => c.id !== id);
      let newActiveId = prev.activeChatId;
      let newChats = updated;
      if (updated.length === 0) {
        const newId = Date.now().toString();
        newChats = [{ id: newId, title: "New Chat", messages: [], loaded: true }];
        newActiveId = newId;
      } else if (prev.activeChatId === id) {
        newActiveId = updated[0].id;
      }
      return { ...prev, chats: newChats, activeChatId: newActiveId };
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
          messages.length === 0 ? (
            <div className="centered-welcome-container">
              <div className="centered-welcome-content">
                <h1 className="centered-greeting">
                  {greetingText || `Ask away, ${profileName}!`}
                </h1>
                <InputBox
                  onSend={handleSend}
                  loading={isLoadingReply}
                  prefillText={prefillText}
                  onPrefillUsed={() => setPrefillText("")}
                  messages={messages}
                  onCompactContext={handleNewChat}
                />
              </div>
            </div>
          ) : (
            <>
              <ChatWindow
                messages={messages}
                loading={isLoadingReply}
                onFeatureClick={(prefix) => { setPrefillText(prefix); setActivePanel("chat"); }}
                userName={profileName}
                onEditMessage={handleEditMessage}
                onShareChat={handleShareChat}
                sessionId={activeChatId}
                onRegenerate={handleRegenerate}
                onSendSuggested={handleSend}
                thinkingSteps={thinkingSteps}
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
          )
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
