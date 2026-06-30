with open("src/App.js", "r") as f:
    lines = f.readlines()

new_handle_send = """  const handleSend = async (text, attachments = []) => {
    if (isLoadingReply) {
      handleStop();
      return;
    }

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
      ? `\\n\\nAttached: ${attachments.map((att) => att.name).join(", ")}`
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

    // Initialize assistant message
    updateActiveChat(
      [
        ...updatedMessages,
        {
          role: "assistant",
          content: "",
          intent: "",
          sources: [],
          citations: [],
          suggested_questions: [],
        },
      ],
      newTitle
    );

    setIsLoadingReply(true);
    setThinkingSteps(DEFAULT_THINKING_STEPS);
    getThinkingSteps(text || "Analyzing attached files")
      .then((steps) => {
        if (Array.isArray(steps) && steps.length > 0) {
          setThinkingSteps(steps);
        }
      })
      .catch((err) => console.error("Thinking steps fetch failed:", err));
    setError("");
    setActivePanel("chat");

    const controller = new AbortController();
    setAbortController(controller);

    const history = updatedMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const onChunk = (parsed) => {
      setSession((prev) => {
        const currentChats = prev.chats;
        const activeChatIndex = currentChats.findIndex(c => c.id === prev.activeChatId);
        if (activeChatIndex === -1) return prev;
        
        const chat = currentChats[activeChatIndex];
        const msgs = [...chat.messages];
        const lastMsg = { ...msgs[msgs.length - 1] };
        
        if (parsed.type === "metadata") {
          lastMsg.intent = parsed.data.intent;
          lastMsg.sources = parsed.data.sources;
          lastMsg.citations = parsed.data.citations;
          lastMsg.response_id = parsed.data.response_id;
          lastMsg.timestamp = parsed.data.timestamp;
        } else if (parsed.type === "chunk") {
          lastMsg.content += parsed.data;
        } else if (parsed.type === "suggestions") {
          lastMsg.suggested_questions = parsed.data;
        }
        
        msgs[msgs.length - 1] = lastMsg;
        
        const newChats = [...currentChats];
        newChats[activeChatIndex] = { ...chat, messages: msgs };
        
        return { ...prev, chats: newChats };
      });
    };

    try {
      let savedProfile = {};
      try {
        const profileKey = user ? `dharma-profile-${user.uid}` : "dharma-profile";
        savedProfile = JSON.parse(localStorage.getItem(profileKey) || "{}");
      } catch {
        savedProfile = {};
      }
      
      await sendMessage(
        text,
        history,
        activeChatId,
        controller.signal,
        attachments,
        savedProfile.level || null,
        onChunk
      );
      
    } catch (err) {
      if (err.name === "AbortError" || err.message === "canceled") {
        console.log("Request aborted");
        return;
      }
      const errText = err.message || "Backend error. Is your FastAPI server running on port 8000?";
      setError(errText);
      
      setSession((prev) => {
        const currentChats = prev.chats;
        const activeChatIndex = currentChats.findIndex(c => c.id === prev.activeChatId);
        if (activeChatIndex === -1) return prev;
        const chat = currentChats[activeChatIndex];
        const msgs = [...chat.messages];
        const lastMsg = { ...msgs[msgs.length - 1] };
        lastMsg.content = (lastMsg.content ? lastMsg.content + "\\n\\n" : "") + `**Error:** ${errText}`;
        msgs[msgs.length - 1] = lastMsg;
        const newChats = [...currentChats];
        newChats[activeChatIndex] = { ...chat, messages: msgs };
        return { ...prev, chats: newChats };
      });
    } finally {
      setIsLoadingReply(false);
      setAbortController(null);
    }
  };\n"""

new_handle_edit = """  const handleEditMessage = async (index, newContent) => {
    const truncated = messages.slice(0, index);
    const originalMsg = messages[index];
    const originalAttachments = originalMsg?.attachments || [];

    const attachmentLabel = originalAttachments.length
      ? `\\n\\nAttached: ${originalAttachments.map((att) => att.name).join(", ")}`
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

    // Initialize assistant message
    updateActiveChat(
      [
        ...updatedMessages,
        {
          role: "assistant",
          content: "",
          intent: "",
          sources: [],
          citations: [],
          suggested_questions: [],
        },
      ],
      newTitle
    );

    setIsLoadingReply(true);
    setThinkingSteps(DEFAULT_THINKING_STEPS);
    getThinkingSteps(newContent || "Regenerating response")
      .then((steps) => {
        if (Array.isArray(steps) && steps.length > 0) {
          setThinkingSteps(steps);
        }
      })
      .catch((err) => console.error("Thinking steps fetch failed:", err));
    setError("");
    setActivePanel("chat");

    const controller = new AbortController();
    setAbortController(controller);

    const history = updatedMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const onChunk = (parsed) => {
      setSession((prev) => {
        const currentChats = prev.chats;
        const activeChatIndex = currentChats.findIndex(c => c.id === prev.activeChatId);
        if (activeChatIndex === -1) return prev;
        
        const chat = currentChats[activeChatIndex];
        const msgs = [...chat.messages];
        const lastMsg = { ...msgs[msgs.length - 1] };
        
        if (parsed.type === "metadata") {
          lastMsg.intent = parsed.data.intent;
          lastMsg.sources = parsed.data.sources;
          lastMsg.citations = parsed.data.citations;
          lastMsg.response_id = parsed.data.response_id;
          lastMsg.timestamp = parsed.data.timestamp;
        } else if (parsed.type === "chunk") {
          lastMsg.content += parsed.data;
        } else if (parsed.type === "suggestions") {
          lastMsg.suggested_questions = parsed.data;
        }
        
        msgs[msgs.length - 1] = lastMsg;
        
        const newChats = [...currentChats];
        newChats[activeChatIndex] = { ...chat, messages: msgs };
        
        return { ...prev, chats: newChats };
      });
    };

    try {
      let savedProfile = {};
      try {
        const profileKey = user ? `dharma-profile-${user.uid}` : "dharma-profile";
        savedProfile = JSON.parse(localStorage.getItem(profileKey) || "{}");
      } catch {
        savedProfile = {};
      }
      
      await sendMessage(
        newContent,
        history,
        activeChatId,
        controller.signal,
        originalAttachments,
        savedProfile.level || null,
        onChunk
      );
    } catch (err) {
      if (err.name === "AbortError" || err.message === "canceled") {
        console.log("Request aborted");
        return;
      }
      const errText = err.message || "Backend error. Is your FastAPI server running on port 8000?";
      setError(errText);
      
      setSession((prev) => {
        const currentChats = prev.chats;
        const activeChatIndex = currentChats.findIndex(c => c.id === prev.activeChatId);
        if (activeChatIndex === -1) return prev;
        const chat = currentChats[activeChatIndex];
        const msgs = [...chat.messages];
        const lastMsg = { ...msgs[msgs.length - 1] };
        lastMsg.content = (lastMsg.content ? lastMsg.content + "\\n\\n" : "") + `**Error:** ${errText}`;
        msgs[msgs.length - 1] = lastMsg;
        const newChats = [...currentChats];
        newChats[activeChatIndex] = { ...chat, messages: msgs };
        return { ...prev, chats: newChats };
      });
    } finally {
      setIsLoadingReply(false);
      setAbortController(null);
    }
  };\n"""

def find_line_index(lines, search_str):
    for i, line in enumerate(lines):
        if search_str in line:
            return i
    return -1

send_start = find_line_index(lines, "const handleSend =")
send_end = find_line_index(lines, "// ── Edit message")
edit_start = find_line_index(lines, "const handleEditMessage =")
edit_end = find_line_index(lines, "const handleShare =")
if edit_end == -1:
    edit_end = find_line_index(lines, "// ── Share")

if -1 not in (send_start, send_end, edit_start, edit_end):
    # Slice the list
    new_lines = lines[:send_start] + [new_handle_send, "\n", "  // ── Edit message (ChatGPT-style: truncate + regenerate) ────────────────────\n\n"] + [new_handle_edit, "\n"] + lines[edit_end:]
    with open("src/App.js", "w") as f:
        f.writelines(new_lines)
    print("Successfully replaced functions.")
else:
    print(f"Failed finding indexes: send_start={send_start}, send_end={send_end}, edit_start={edit_start}, edit_end={edit_end}")

