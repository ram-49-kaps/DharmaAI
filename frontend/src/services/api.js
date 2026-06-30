import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "";

const API = axios.create({
  baseURL: BASE_URL ? `${BASE_URL}/api` : "/api",
  timeout: 90000,
  headers: { "Content-Type": "application/json" },
});

import { auth } from "../firebase/config";

// Attach Firebase auth token to every request using an interceptor
API.interceptors.request.use(async (config) => {
  if (auth.currentUser) {
    const token = await auth.currentUser.getIdToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return config;
}, (error) => Promise.reject(error));

// Legacy helper for App.js - now handled by interceptor
export const setAuthToken = (token) => {
  // No-op
};

const parseSseFrame = (frame) => {
  let eventType = "";
  const dataLines = [];

  frame.split(/\r?\n/).forEach((line) => {
    if (!line || line.startsWith(":")) return;
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  });

  if (dataLines.length === 0) return null;

  const rawData = dataLines.join("\n");
  try {
    const parsed = JSON.parse(rawData);
    return {
      type: eventType || parsed.type || "message",
      data: Object.prototype.hasOwnProperty.call(parsed, "data") ? parsed.data : parsed,
    };
  } catch {
    return {
      type: eventType || "message",
      data: rawData,
    };
  }
};

const readSseStream = async (response, signal, onEvent) => {
  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const flushFrames = () => {
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() || "";

    frames.forEach((frame) => {
      const event = parseSseFrame(frame);
      if (event) onEvent?.(event);
    });
  };

  try {
    while (true) {
      if (signal?.aborted) {
        await reader.cancel();
        throw new DOMException("The operation was aborted.", "AbortError");
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      flushFrames();
    }

    buffer += decoder.decode();
    if (buffer.trim()) {
      const event = parseSseFrame(buffer);
      if (event) onEvent?.(event);
    }
  } finally {
    reader.releaseLock();
  }
};

export const sendMessage = async (message, history = [], sessionId = null, signal = null, attachments = [], level = null, onChunk = null, modelId = null) => {
  const headers = {};
  if (auth.currentUser) {
    const token = await auth.currentUser.getIdToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let body;
  if (attachments.length > 0) {
    const formData = new FormData();
    formData.append("message", message);
    formData.append("history", JSON.stringify(history));
    if (sessionId) formData.append("session_id", sessionId);
    if (level) formData.append("level", level);
    if (modelId) formData.append("model_id", modelId);
    attachments.forEach((att) => formData.append("files", att.file || att));
    body = formData;
  } else {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify({ message, history, session_id: sessionId, level, model_id: modelId });
  }

  const url = BASE_URL ? `${BASE_URL}/api/chat` : "/api/chat";
  const response = await fetch(url, {
    method: "POST",
    headers,
    body,
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText);
  }

  const finalResponse = { intent: "", answer: "", sources: [], citations: [], suggested_questions: [] };

  await readSseStream(response, signal, (event) => {
    if (event.type === "metadata") {
      finalResponse.intent = event.data?.intent || "";
      finalResponse.sources = event.data?.sources || [];
    } else if (event.type === "token" || event.type === "chunk") {
      finalResponse.answer += event.data || "";
    } else if (event.type === "citations") {
      finalResponse.citations = event.data || [];
    } else if (event.type === "suggestions") {
      finalResponse.suggested_questions = event.data || [];
    } else if (event.type === "error") {
      throw new Error(event.data || "Streaming request failed.");
    }

    if (onChunk) onChunk(event);
  });

  return finalResponse;
};

export const getThinkingSteps = async (query) => {
  const { data } = await API.post("/thinking", { query });
  return data;
};

export const getGreeting = async (payload) => {
  const { data } = await API.post("/greeting", payload);
  return data;
};

export const getGlossaryTerm = async (term) => {
  const { data } = await API.get(`/glossary/${encodeURIComponent(term)}`);
  return data;
};

export const listGlossary = async () => {
  const { data } = await API.get("/glossary");
  return data;
};

export const searchLegal = async (q) => {
  const { data } = await API.get("/search", { params: { q } });
  return data;
};

export const getTemplates = async () => {
  const { data } = await API.get("/templates");
  return data;
};

export const getMe = async () => {
  const { data } = await API.get("/me");
  return data;
};

export const getProfile = async () => {
  const { data } = await API.get("/profile");
  return data;
};

export const updateProfile = async (profile) => {
  const { data } = await API.put("/profile", profile);
  return data;
};

export const submitFeedback = async (feedback) => {
  const { data } = await API.post("/feedback", feedback);
  return data;
};

export const getSessions = async () => {
  const { data } = await API.get("/sessions");
  return data; // { sessions: [{session_id, title, last_active, message_count}] }
};

export const getSessionMessages = async (sessionId) => {
  const { data } = await API.get(`/sessions/${sessionId}`);
  return data; // { session_id, messages: [{role, content, created_at}] }
};

export const deleteSession = async (sessionId) => {
  const { data } = await API.delete(`/sessions/${sessionId}`);
  return data;
};

export const shareChat = async (title, messages) => {
  const { data } = await API.post("/share", { title, messages });
  return data; // { share_id, share_url }
};

export const getSharedChat = async (shareId) => {
  const { data } = await API.get(`/share/${shareId}`);
  return data; // { share_id, title, messages, created_at }
};

export default API;
