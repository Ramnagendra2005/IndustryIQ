const BASE = import.meta.env.VITE_API_BASE || "";
const TOKEN_KEY = "iq-token";

// --- session token (persisted so a refresh keeps you signed in) ------------
let _token = localStorage.getItem(TOKEN_KEY) || "";
const _authListeners = new Set();

export const auth = {
  get token() { return _token; },
  set(token) {
    _token = token || "";
    if (_token) localStorage.setItem(TOKEN_KEY, _token);
    else localStorage.removeItem(TOKEN_KEY);
    _authListeners.forEach((fn) => fn(_token));
  },
  clear() { auth.set(""); },
  onChange(fn) { _authListeners.add(fn); return () => _authListeners.delete(fn); },
};

async function j(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (_token) headers.Authorization = `Bearer ${_token}`;
  let r;
  try {
    r = await fetch(BASE + path, { ...opts, headers });
  } catch {
    throw new Error("Cannot reach the IndustryIQ server — is the backend running?");
  }
  if (r.status === 401 && _token) {
    auth.clear();  // stale/invalid token — bounce back to login
  }
  if (!r.ok) {
    let msg = `Request failed (HTTP ${r.status})`;
    try {
      const d = await r.json();
      msg = d.detail || d.error || msg;
    } catch { /* non-JSON error body */ }
    throw new Error(msg);
  }
  return r.json();
}

export const api = {
  // --- auth ---------------------------------------------------------------
  login: async (email, password) => {
    const d = await j("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    auth.set(d.token);
    return d.user;
  },
  register: async (payload) => {
    const d = await j("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    auth.set(d.token);
    return d.user;
  },
  me: () => j("/api/auth/me"),
  logout: () => auth.clear(),

  status: () => j("/api/status"),
  query: (question, mode, lang = "en") =>
    j("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, mode, lang }),
    }),
  compliance: () => j("/api/compliance"),
  trust: () => j("/api/trust"),
  graph: (focus, radius = 2) =>
    j(`/api/graph${focus ? `?focus=${encodeURIComponent(focus)}&radius=${radius}` : ""}`),
  documents: () => j("/api/documents"),
  document: (id) => j(`/api/documents/${id}`),
  pids: () => j("/api/pids"),
  pid: (id) => j(`/api/pid/${encodeURIComponent(id)}`),
  // token in the query string: <img> can't send an Authorization header
  pidImageUrl: (id) =>
    `${BASE}/api/pid/${encodeURIComponent(id)}/image${_token ? `?token=${encodeURIComponent(_token)}` : ""}`,
  entity: (name) => j(`/api/entity/${encodeURIComponent(name)}`),
  ingest: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return j("/api/ingest", { method: "POST", body: fd });
  },
};
