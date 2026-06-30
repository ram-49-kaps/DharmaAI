import React from "react";
import { Plus, MessageSquare, Library, BrainCircuit, Pencil, Trash2, Download, X, Check, X as XIcon, Upload, LogOut, User, Sun, Moon, PanelLeftClose, Search, Sparkles } from "lucide-react";
import Logo from "./Logo";
import BrandText from "./BrandText";
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
  isCollapsed,
  onToggleCollapse,
  onLogout,
}) {
  const { user } = useAuth();
  const [editingChatId, setEditingChatId] = React.useState(null);
  const [editTitle, setEditTitle] = React.useState("");
  const [deleteConfirmId, setDeleteConfirmId] = React.useState(null);
  const deleteTarget = React.useMemo(
    () => chats.find((chat) => chat.id === deleteConfirmId),
    [chats, deleteConfirmId]
  );
  const [showLogoutConfirm, setShowLogoutConfirm] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");

  const filteredChats = chats.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
    e?.stopPropagation();
    onDeleteChat(chatId);
    setDeleteConfirmId(null);
  };

  // Admin check — simple heuristic; real check is on backend
  const isAdmin = user && process.env.REACT_APP_ADMIN_EMAILS?.split(",").includes(user.email);

  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      {/* Logo */}
      <div className="sidebar-logo" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <div className="logo-icon" style={{ display: "flex" }}><Logo size={24} variant="minimal" /></div>
        <BrandText style={{ fontSize: "1.1rem" }} />
        <div className="tooltip-wrap" style={{ marginLeft: "auto" }}>
          <button className="sidebar-collapse-btn" onClick={onToggleCollapse}>
            <PanelLeftClose size={18} />
          </button>
          <div className="tooltip-content tooltip-bottom-right">
            Close sidebar <span className="tooltip-key">⌘/</span>
          </div>
        </div>
        <button className="mobile-close-btn" onClick={onClose}><X size={20} /></button>
      </div>

      {/* New Chat */}
      <div className="sidebar-actions">
        <button className="new-chat-btn" onClick={onNewChat}>
          <span><Plus size={18} /></span> New Chat
        </button>
      </div>

      {/* Search */}
      <div className="sidebar-search">
        <Search size={14} className="sidebar-search-icon" />
        <input 
          type="text" 
          placeholder="Search..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {[
          { id: "chat",      icon: <MessageSquare size={18} />, label: "Chat" },
          { id: "sources",   icon: <Library size={18} />,       label: "Library & Resources" },
          { id: "templates", icon: <BrainCircuit size={18} />,  label: "Reasoning Templates" },
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
          <div className="sidebar-section-title">Recent Chats</div>
          {filteredChats.length === 0 ? (
            <div className="sidebar-empty">No chats found.</div>
          ) : (
            filteredChats.map((chat) => {
          const isEditing  = editingChatId === chat.id;
          const isDeleting = deleteConfirmId === chat.id;
          return (
            <div
              key={chat.id}
              className="history-item"
              style={activeChatId === chat.id ? { background: "var(--primary-surface)", color: "var(--primary)", fontWeight: 600 } : {}}
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
                <div className="tooltip-wrap">
                  <button className="chat-action-btn" onClick={(e) => startRename(e, chat)}><Pencil size={14} /></button>
                  <div className="tooltip-content" style={{ fontSize: "0.75rem", padding: "4px 8px" }}>Rename</div>
                </div>
                <div className="tooltip-wrap">
                  <button className="chat-action-btn" onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(chat.id); setEditingChatId(null); }}><Trash2 size={14} /></button>
                  <div className="tooltip-content" style={{ fontSize: "0.75rem", padding: "4px 8px" }}>Delete</div>
                </div>
              </div>
            </div>
          );
        }))}
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
          <button className="export-btn" style={{ marginTop: "0.2rem" }} onClick={onOpenUploader}>
            <Upload size={16} /> Upload PDF (Admin)
          </button>
        )}

        {/* User profile */}
        {user && (
          <div style={profileStyles.card}>
            {user.photoURL ? (
              <img src={user.photoURL} alt="" style={profileStyles.avatar} referrerPolicy="no-referrer" />
            ) : (
              <div style={profileStyles.avatarFallback}>
                <User size={14} color="#fff" />
              </div>
            )}
            <div style={profileStyles.info}>
              <span style={profileStyles.name}>{user.displayName || user.email?.split("@")[0] || "User"}</span>
              <span style={profileStyles.email}>{user.email}</span>
            </div>
            <div className="tooltip-wrap">
              <button style={profileStyles.logoutBtn} onClick={() => setShowLogoutConfirm(true)}>
                <LogOut size={14} />
              </button>
              <div className="tooltip-content tooltip-bottom-right" style={{ bottom: "auto", top: "calc(100% + 8px)", right: 0, fontSize: "0.75rem", padding: "4px 8px" }}>Sign out</div>
            </div>
          </div>
        )}



        {/* Logout confirmation modal */}
        {showLogoutConfirm && (
          <div className="logout-overlay" onClick={() => setShowLogoutConfirm(false)}>
            <div className="logout-modal" onClick={(e) => e.stopPropagation()}>
              <div className="logout-modal-icon"><LogOut size={24} color="#B45309" /></div>
              <h3 className="logout-modal-title">Sign Out</h3>
              <p className="logout-modal-text">Are you sure you want to sign out of Prakarna AI?</p>
              <div className="logout-modal-actions">
                <button className="logout-cancel-btn" onClick={() => setShowLogoutConfirm(false)}>Cancel</button>
                <button className="logout-confirm-btn" onClick={() => { setShowLogoutConfirm(false); onLogout(); }}>Sign Out</button>
              </div>
            </div>
          </div>
        )}

        {deleteTarget && (
          <div className="logout-overlay" onClick={() => setDeleteConfirmId(null)}>
            <div className="logout-modal delete-chat-modal" onClick={(e) => e.stopPropagation()}>
              <div className="logout-modal-icon delete-modal-icon"><Trash2 size={24} color="#B45309" /></div>
              <h3 className="logout-modal-title">Delete Chat?</h3>
              <p className="logout-modal-text">
                Are you sure you want to delete <strong>{deleteTarget.title}</strong>? This cannot be undone.
              </p>
              <div className="logout-modal-actions">
                <button className="logout-cancel-btn" onClick={() => setDeleteConfirmId(null)}>Cancel</button>
                <button className="logout-confirm-btn delete-confirm-btn" onClick={(e) => confirmDelete(e, deleteTarget.id)}>Delete</button>
              </div>
            </div>
          </div>
        )}

        {/* Developer Credits */}
        <div style={{
          textAlign: "center",
          fontSize: "0.75rem",
          color: "var(--text)",
          marginTop: "0.8rem",
          paddingTop: "0.8rem",
          borderTop: "1px dashed var(--border)",
          fontWeight: 500
        }}>
          Created by <span style={{ color: "var(--primary)", fontWeight: 700 }}>Ram Kapadia</span>, <span style={{ color: "var(--primary)", fontWeight: 700 }}>Arnav Narula</span> & <span style={{ color: "var(--primary)", fontWeight: 700 }}>Saanvi Aggarwal</span>
        </div>
      </div>
    </aside>
  );
}

const profileStyles = {
  card: {
    marginTop: "0.25rem",
    padding: "0.6rem 0.75rem",
    background: "var(--surface-2)",
    borderRadius: "var(--radius-sm)",
    border: "1px solid var(--border)",
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
  },
  avatar: { width: 28, height: 28, borderRadius: "50%", objectFit: "cover", flexShrink: 0 },
  avatarFallback: {
    width: 28, height: 28, borderRadius: "50%", background: "var(--gradient-primary)",
    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  info: { flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" },
  name: { fontSize: "0.82rem", fontWeight: 700, color: "var(--primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  email: { fontSize: "0.68rem", color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  logoutBtn: { background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "2px", flexShrink: 0 },
};
