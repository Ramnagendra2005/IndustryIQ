const BASE = import.meta.env.VITE_API_BASE || "";

async function j(path, opts) {
  let r;
  try {
    r = await fetch(BASE + path, opts);
  } catch {
    throw new Error("Cannot reach the IndustryIQ server — is the backend running?");
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
  status: () => j("/api/status"),
  query: (question, mode) =>
    j("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, mode }),
    }),
  compliance: () => j("/api/compliance"),
  graph: (focus, radius = 2) =>
    j(`/api/graph${focus ? `?focus=${encodeURIComponent(focus)}&radius=${radius}` : ""}`),
  documents: () => j("/api/documents"),
  document: (id) => j(`/api/documents/${id}`),
  ingest: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return j("/api/ingest", { method: "POST", body: fd });
  },
};
