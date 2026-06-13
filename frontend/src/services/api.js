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

export const sendMessage = async (message, history = [], sessionId = null, signal = null, attachments = [], level = null) => {
  if (attachments.length > 0) {
    const formData = new FormData();
    formData.append("message", message);
    formData.append("history", JSON.stringify(history));
    if (sessionId) formData.append("session_id", sessionId);
    if (level) formData.append("level", level);
    attachments.forEach((att) => formData.append("files", att.file || att));

    const { data } = await API.post("/chat", formData, {
      signal,
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  }

  const { data } = await API.post(
    "/chat", 
    { message, history, session_id: sessionId, level },
    { signal }
  );
  return data; // { intent, answer, sources, citations }
};

export const getThinkingSteps = async (query) => {
  const { data } = await API.post("/thinking", { query });
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
