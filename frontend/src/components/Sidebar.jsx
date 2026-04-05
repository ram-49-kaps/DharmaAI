import React from "react";
import { Plus, MessageSquare, Library, BrainCircuit, Scale, Pencil, Trash2, Download, X, Check, X as XIcon } from "lucide-react";
import Logo from "./Logo";

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
  onClose
}) {
  
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
    if (editTitle.trim()) {
      onRenameChat(editingChatId, editTitle.trim());
    }
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

  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon"><Logo size={28} color="white" /></div>
        <div className="logo-text">
          <div className="logo-title">DharmaAI</div>
          <div className="logo-sub">Indian Legal Assistant</div>
        </div>
        <button className="mobile-close-btn" onClick={onClose}>
          <X size={20} />
        </button>
      </div>

      {/* New Chat */}
      <button className="new-chat-btn" onClick={onNewChat}>
        <span><Plus size={18} /></span> New Consultation
      </button>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {[
          { id: "chat",      icon: <MessageSquare size={18} />, label: "Chat" },
          { id: "sources",   icon: <Library size={18} />, label: "Library & Sources" },
          { id: "templates", icon: <BrainCircuit size={18} />, label: "Brainstorming Templates" },
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
          const isEditing = editingChatId === chat.id;
          const isDeleting = deleteConfirmId === chat.id;

          return (
            <div 
              key={chat.id} 
              className="history-item"
              style={activeChatId === chat.id ? { background: "rgba(26,35,126,0.08)", color: "var(--primary)", fontWeight: "600" } : {}}
              onClick={() => {
                if (!isEditing) onSwitchChat(chat.id);
              }}
            >
              {isEditing ? (
                <input
                  type="text"
                  autoFocus
                  className="sidebar-edit-input"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={submitRename}
                  onKeyDown={handleEditKeyDown}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="history-title">{chat.title}</span>
              )}

              <div className="chat-actions">
                {isDeleting ? (
                  <>
                    <button className="chat-action-btn confirm-del" title="Confirm Delete" onClick={(e) => confirmDelete(e, chat.id)}><Check size={14} color="var(--danger)" /></button>
                    <button className="chat-action-btn" title="Cancel" onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(null); }}><XIcon size={14} /></button>
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
        
        <div style={{
          marginTop: "0.5rem", 
          padding: "0.75rem", 
          background: "var(--surface)", 
          borderRadius: "var(--radius-sm)", 
          border: "1px solid var(--border)", 
          display: "flex", 
          alignItems: "center", 
          gap: "0.6rem",
          boxShadow: "var(--shadow-xs)"
        }}>
           <div style={{
             background: "var(--primary)", 
             width: "28px", 
             height: "28px", 
             borderRadius: "50%", 
             display: "flex", 
             alignItems:"center", 
             justifyContent: "center", 
             color: "white", 
             fontSize: "0.75rem", 
             fontWeight: "700"
           }}>RK</div>
           <div style={{display: "flex", flexDirection: "column"}}>
             <span style={{fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600}}>Creator</span>
             <span style={{fontSize: "0.85rem", fontWeight: "700", color: "var(--primary)"}}>Ram Kapadia</span>
           </div>
        </div>

        <p className="disclaimer" style={{marginTop: "0.25rem"}}>
          Educational use only · Not legal advice<br />
          Powered by IKS & Modern Jurisprudence
        </p>
      </div>
    </aside>
  );
}
