import React, { useState, useRef, useEffect } from "react";
import { api } from "../api";
import { renderRich, confColor, DOCTYPE_ICON } from "../lib";

const MODES = [
  { id: "copilot", label: "Ask", hint: "General operational Q&A" },
  { id: "rca", label: "RCA", hint: "Root-cause analysis — connect the dots" },
];

const SUGGESTIONS = [
  { q: "Why is pump P-101 vibrating and tripping?", mode: "rca" },
  { q: "Has this kind of failure happened on a similar pump before?", mode: "copilot" },
  { q: "What is the maintenance history of P-101?", mode: "copilot" },
  { q: "What are the OEM vibration alarm and trip limits for P-101?", mode: "copilot" },
];

export default function Chat({ onFocusEntity, onOpenDoc, onTrail, field }) {
  const [mode, setMode] = useState("rca");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 9e9, behavior: "smooth" });
  }, [messages, busy]);

  async function send(q, m) {
    const question = (q ?? input).trim();
    if (!question || busy) return;
    const useMode = m ?? mode;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setBusy(true);
    const t0 = performance.now();
    try {
      const res = await api.query(question, useMode);
      res._wall = Math.round(performance.now() - t0);
      setMessages((prev) => [...prev, { role: "assistant", ...res }]);
      onTrail?.(res.graph_paths || []);
      if (res.focus_entities?.length) onFocusEntity?.(res.focus_entities.join(","));
    } catch (e) {
      setMessages((prev) => [...prev, { role: "assistant", answer: "⚠️ " + e.message, confidence: 0, citations: [], graph_paths: [] }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* mode pills */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-edge shrink-0">
        {MODES.map((mm) => (
          <button
            key={mm.id}
            onClick={() => setMode(mm.id)}
            title={mm.hint}
            className={`px-3 py-1 rounded-full text-sm font-medium transition ${
              mode === mm.id ? "bg-accent text-ink" : "bg-panel2 text-slate-300 hover:bg-edge"
            }`}
          >
            {mm.label}
          </button>
        ))}
        <span className="text-xs text-slate-500 ml-1 hidden sm:inline">
          {MODES.find((x) => x.id === mode)?.hint}
        </span>
      </div>

      {/* messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-6">
            <div className="text-4xl mb-2">🧠</div>
            <p className="text-sm max-w-sm mx-auto">
              Ask the plant's collective memory. The copilot fuses P&IDs, work orders,
              inspections, OEM manuals and incident history into one answer — with sources.
            </p>
            <div className="mt-4 grid gap-2 max-w-md mx-auto">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => send(s.q, s.mode)}
                  className="text-left text-sm px-3 py-2 rounded-lg bg-panel2 hover:bg-edge border border-edge"
                >
                  <span className="text-accent mr-1">{s.mode === "rca" ? "🔬" : "💬"}</span>
                  {s.q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end fade-in">
              <div className="bg-accent/90 text-ink px-3 py-2 rounded-2xl rounded-br-sm max-w-[85%] text-sm font-medium">
                {m.text}
              </div>
            </div>
          ) : (
            <Answer key={i} m={m} onFocusEntity={onFocusEntity} onOpenDoc={onOpenDoc} />
          )
        )}

        {busy && (
          <div className="flex items-center gap-2 text-slate-400 text-sm fade-in">
            <span className="w-2 h-2 rounded-full bg-teal live-dot" />
            Traversing knowledge graph & retrieving sources…
          </div>
        )}
      </div>

      {/* input */}
      <div className="p-3 border-t border-edge shrink-0">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder={field ? "Ask from the field…" : "Ask about any asset, failure, or regulation…"}
            className="flex-1 bg-panel2 border border-edge rounded-xl px-3 py-2.5 text-sm outline-none focus:border-accent"
          />
          <button
            onClick={() => send()}
            disabled={busy}
            className="px-4 rounded-xl bg-accent text-ink font-semibold disabled:opacity-50"
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}

function Answer({ m, onFocusEntity, onOpenDoc }) {
  const baselineMin = 20; // McKinsey: ~35% of day searching; a manual cross-doc dig ≈ 20 min
  return (
    <div className="fade-in space-y-3">
      <div className="bg-panel2 border border-edge rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed">
        {renderRich(m.answer || "", onOpenDoc)}
      </div>

      {/* metrics row */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <div className="flex items-center gap-1.5 bg-panel2 border border-edge rounded-full px-2.5 py-1">
          <span className="text-slate-400">Confidence</span>
          <div className="w-16 h-1.5 rounded-full bg-edge overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${(m.confidence || 0) * 100}%`, background: confColor(m.confidence || 0) }} />
          </div>
          <span className="font-mono" style={{ color: confColor(m.confidence || 0) }}>
            {Math.round((m.confidence || 0) * 100)}%
          </span>
        </div>
        <div className="bg-teal/10 text-teal border border-teal/30 rounded-full px-2.5 py-1 font-mono">
          ⚡ {m._wall ?? m.elapsed_ms} ms &nbsp;vs&nbsp; ~{baselineMin} min manual
        </div>
        {m.mode === "rca" && (
          <div className="bg-accent/10 text-accent border border-accent/30 rounded-full px-2.5 py-1">
            🔬 Root-Cause Analysis
          </div>
        )}
      </div>

      {/* graph paths — the connected-dots evidence trail */}
      {m.graph_paths?.length > 0 && (
        <div className="bg-panel2/60 border border-edge rounded-xl px-3 py-2">
          <div className="text-xs text-slate-400 mb-1.5">🕸️ Evidence trail (knowledge-graph links)</div>
          <div className="flex flex-wrap gap-1.5">
            {m.graph_paths.slice(0, 10).map((h, i) => (
              <span key={i} className="text-xs font-mono bg-ink/60 border border-edge rounded px-1.5 py-0.5">
                <button className="text-accent hover:underline" onClick={() => onFocusEntity?.(h.source)}>{h.source}</button>
                <span className="text-slate-500 mx-1">─{h.relation}→</span>
                <button className="text-teal hover:underline" onClick={() => onFocusEntity?.(h.target)}>{h.target}</button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* citations */}
      {m.citations?.length > 0 && (
        <div>
          <div className="text-xs text-slate-400 mb-1.5">
            📎 {m.citations.length} sources across {new Set(m.citations.map((c) => c.doc_type)).size} document types
          </div>
          <div className="grid gap-1.5">
            {m.citations.slice(0, 6).map((c, i) => (
              <button
                key={i}
                onClick={() => onOpenDoc?.(c.doc_id)}
                className="text-left bg-panel2 border border-edge rounded-lg px-3 py-2 hover:border-teal transition"
              >
                <div className="flex items-center gap-2 text-sm">
                  <span>{DOCTYPE_ICON[c.doc_type] || "📄"}</span>
                  <span className="font-medium text-white truncate">{c.title}</span>
                  <span className="text-xs font-mono text-teal ml-auto shrink-0">{c.doc_id}</span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5 line-clamp-2">{c.snippet}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
