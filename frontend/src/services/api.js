import axios from "axios";

const API = axios.create({
  baseURL: "/api",
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

/**
 * POST /api/chat
 * @param {string} message
 * @param {Array<{role:string, content:string}>} history
 * @returns {Promise<{intent:string, answer:string, sources:Array}>}
 */
export const sendMessage = async (message, history = []) => {
  const { data } = await API.post("/chat", { message, history });
  return data; // { intent, answer, sources }
};

/**
 * GET /api/glossary/:term
 * @returns {Promise<{term, definition, example}>}
 */
export const getGlossaryTerm = async (term) => {
  const { data } = await API.get(`/glossary/${encodeURIComponent(term)}`);
  return data;
};

/**
 * GET /api/glossary
 * @returns {Promise<{terms: string[]}>}
 */
export const listGlossary = async () => {
  const { data } = await API.get("/glossary");
  return data;
};

/**
 * GET /api/search?q=
 * @returns {Promise<{results: Array<{title,snippet,type}>}>}
 */
export const searchLegal = async (q) => {
  const { data } = await API.get("/search", { params: { q } });
  return data;
};

/**
 * GET /api/templates
 * @returns {Promise<{templates: Array<{name, structure}>}>}
 */
export const getTemplates = async () => {
  const { data } = await API.get("/templates");
  return data;
};

export default API;
