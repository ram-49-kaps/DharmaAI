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

export const sendMessage = async (message, history = [], sessionId = null, signal = null) => {
  const { data } = await API.post(
    "/chat", 
    { message, history, session_id: sessionId },
    { signal }
  );
  return data; // { intent, answer, sources, citations }
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

export default API;
