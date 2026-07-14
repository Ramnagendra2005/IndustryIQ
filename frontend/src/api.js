const BASE = import.meta.env.VITE_API_BASE || "";

async function j(path, opts) {
  const r = await fetch(BASE + path, opts);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
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
