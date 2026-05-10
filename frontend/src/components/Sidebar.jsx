import React from "react";
import { Plus, MessageSquare, Library, BrainCircuit, Pencil, Trash2, Download, X, Check, X as XIcon, Upload, LogOut, User, Sun, Moon } from "lucide-react";
import Logo from "./Logo";
import { useAuth } from "../contexts/AuthContext";

export default function Sidebar({
  chats,
  activeChatId,
  onNewChat,
  onSwitchChat,
  onDeleteChat,
  onRenameChat,
  onExport,
  activePanel,
  setActivePanel,
  isExportDisabled,
  isOpen,
  onClose,
  onOpenUploader,
  theme,
  onToggleTheme,
}) {
  const { user, logout } = useAuth();
  const [editingChatId, setEditingChatId] = React.useState(null);
  const [editTitle, setEditTitle] = React.useState("");
  const [deleteConfirmId, setDeleteConfirmId] = React.useState(null);

  const startRename = (e, chat) => {
    e.stopPropagation();
    setEditingChatId(chat.id);
    setEditTitle(chat.title);
    setDeleteConfirmId(null);
  };

  const submitRename = () => {
    if (editTitle.trim()) onRenameChat(editingChatId, editTitle.trim());
    setEditingChatId(null);
  };

  const handleEditKeyDown = (e) => {
    if (e.key === "Enter") submitRename();
    if (e.key === "Escape") setEditingChatId(null);
  };

  const confirmDelete = (e, chatId) => {
    e.stopPropagation();
    onDeleteChat(chatId);
    setDeleteConfirmId(null);
  };

  // Admin check — simple heuristic; real check is on backend
  const isAdmin = user && process.env.REACT_APP_ADMIN_EMAILS?.split(",").includes(user.email);

  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon"><Logo size={28} color="white" /></div>
        <div className="logo-text">
          <div className="logo-title">DharmaAI</div>
          <div className="logo-sub">Indian Legal Assistant</div>
        </div>
        <button className="mobile-close-btn" onClick={onClose}><X size={20} /></button>
      </div>

      {/* New Chat */}
      <button className="new-chat-btn" onClick={onNewChat}>
        <span><Plus size={18} /></span> New Consultation
      </button>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {[
          { id: "chat",      icon: <MessageSquare size={18} />, label: "Chat" },
          { id: "sources",   icon: <Library size={18} />,       label: "Library & Sources" },
          { id: "templates", icon: <BrainCircuit size={18} />,  label: "Brainstorming Templates" },
        ].map((item) => (
          <button
            key={item.id}
            className={`nav-btn ${activePanel === item.id ? "nav-btn-active" : ""}`}
            onClick={() => setActivePanel(item.id)}
          >
            <span className="nav-icon">{item.icon}</span> {item.label}
          </button>
        ))}
      </nav>

      {/* Chat history */}
      <div className="sidebar-section">
        <p className="sidebar-section-title">Recent Chats</p>
        {chats.length === 0 && <p className="sidebar-empty">No queries yet</p>}
        {chats.map((chat) => {
          const isEditing  = editingChatId === chat.id;
          const isDeleting = deleteConfirmId === chat.id;
          return (
            <div
              key={chat.id}
              className="history-item"
              style={activeChatId === chat.id ? { background: "rgba(26,35,126,0.08)", color: "var(--primary)", fontWeight: 600 } : {}}
              onClick={() => { if (!isEditing) onSwitchChat(chat.id); }}
            >
              {isEditing ? (
                <input
                  type="text" autoFocus className="sidebar-edit-input"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={submitRename} onKeyDown={handleEditKeyDown}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="history-title">{chat.title}</span>
              )}
              <div className="chat-actions">
                {isDeleting ? (
                  <>
                    <button className="chat-action-btn confirm-del" onClick={(e) => confirmDelete(e, chat.id)}><Check size={14} color="var(--danger)" /></button>
                    <button className="chat-action-btn" onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(null); }}><XIcon size={14} /></button>
                  </>
                ) : (
                  <>
                    <button className="chat-action-btn" title="Rename" onClick={(e) => startRename(e, chat)}><Pencil size={14} /></button>
                    <button className="chat-action-btn" title="Delete" onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(chat.id); setEditingChatId(null); }}><Trash2 size={14} /></button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <button className="export-btn" onClick={onExport} disabled={isExportDisabled}>
          <Download size={16} /> Export Session
        </button>

        <button className="export-btn" onClick={onToggleTheme}>
          {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
          {theme === "light" ? "Dark Mode" : "Light Mode"}
        </button>

        {/* Admin PDF upload */}
        {isAdmin && onOpenUploader && (
          <button className="export-btn" style={{ marginTop: "0.4rem" }} onClick={onOpenUploader}>
            <Upload size={16} /> Upload PDF (Admin)
          </button>
        )}

        {/* User profile */}
        {user && (
          <div style={styles.profileCard}>
            {user.photoURL ? (
              <img src={user.photoURL} alt="" style={styles.avatar} referrerPolicy="no-referrer" />
            ) : (
              <div style={styles.avatarFallback}>
                <User size={14} color="#fff" />
              </div>
            )}
            <div style={styles.profileInfo}>
              <span style={styles.profileName}>{user.displayName || user.email?.split("@")[0] || "User"}</span>
              <span style={styles.profileEmail}>{user.email}</span>
            </div>
            <button style={styles.logoutBtn} onClick={logout} title="Sign out">
              <LogOut size={14} />
            </button>
          </div>
        )}

        <p className="disclaimer" style={{ marginTop: "0.25rem" }}>
          Educational use only · Not legal advice<br />
          Powered by IKS & Modern Jurisprudence
        </p>
      </div>
    </aside>
  );
}

const styles = {
  profileCard: {
    marginTop: "0.5rem",
    padding: "0.6rem 0.75rem",
    background: "var(--surface)",
    borderRadius: "var(--radius-sm)",
    border: "1px solid var(--border)",
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
  },
  avatar: { width: 28, height: 28, borderRadius: "50%", objectFit: "cover", flexShrink: 0 },
  avatarFallback: {
    width: 28, height: 28, borderRadius: "50%", background: "var(--primary)",
    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  profileInfo: { flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" },
  profileName: { fontSize: "0.82rem", fontWeight: 700, color: "var(--primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  profileEmail: { fontSize: "0.68rem", color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  logoutBtn: { background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "2px", flexShrink: 0 },
};
