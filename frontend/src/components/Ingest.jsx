import React, { useState } from "react";
import { api } from "../api";
import { TYPE_COLORS } from "../lib";

export default function Ingest({ onIngested }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [drag, setDrag] = useState(false);

  async function handle(file) {
    if (!file) return;
    setBusy(true);
    setResult(null);
    try {
      const res = await api.ingest(file);
      setResult(res);
      onIngested?.();
    } catch (e) {
      setResult({ error: e.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      <label
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); handle(e.dataTransfer.files[0]); }}
        className={`block border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
          drag ? "border-accent bg-accent/10" : "border-edge bg-panel2 hover:border-teal"
        }`}
      >
        <input type="file" className="hidden" onChange={(e) => handle(e.target.files[0])}
          accept=".pdf,.txt,.md,.eml,.csv,.xlsx,.png,.jpg,.jpeg" />
        <div className="text-3xl mb-1">📥</div>
        <div className="text-sm font-medium">{busy ? "Extracting & linking into the graph…" : "Drop a document to ingest live"}</div>
        <div className="text-xs text-slate-400 mt-1">PDF · scanned form / P&ID · spreadsheet · email · text</div>
      </label>

      {busy && (
        <div className="flex items-center gap-2 text-teal text-sm">
          <span className="w-2 h-2 rounded-full bg-teal live-dot" /> AI entity + relationship extraction running…
        </div>
      )}

      {result && !result.error && (
        <div className="bg-panel2 border border-edge rounded-xl p-3 fade-in">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-emerald-400">✓ ingested</span>
            <span className="font-medium text-white truncate">{result.document.title}</span>
            <span className="ml-auto text-[10px] font-mono text-slate-400">{result.provider}</span>
          </div>
          <div className="flex gap-2 mt-2 text-xs">
            <span className="bg-teal/10 text-teal border border-teal/30 rounded-full px-2 py-0.5">
              +{result.added_entities} entities
            </span>
            <span className="bg-accent/10 text-accent border border-accent/30 rounded-full px-2 py-0.5">
              +{result.added_relationships} relationships
            </span>
          </div>
          <div className="mt-3 grid gap-1">
            {result.extraction.entities.slice(0, 12).map((e, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="w-2 h-2 rounded-full" style={{ background: TYPE_COLORS[e.type] || "#64748b" }} />
                <span className="font-mono text-white">{e.name}</span>
                <span className="text-slate-500">{e.type}</span>
              </div>
            ))}
          </div>
          {result.extraction.relations?.length > 0 && (
            <div className="mt-2 text-xs text-slate-400">
              {result.extraction.relations.slice(0, 6).map((r, i) => (
                <div key={i} className="font-mono">
                  {r.source} <span className="text-accent">─{r.type}→</span> {r.target}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {result?.error && <div className="text-red-400 text-sm">⚠️ {result.error}</div>}
    </div>
  );
}
