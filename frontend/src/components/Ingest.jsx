import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../api";
import { TYPE_COLORS } from "../lib";
import { CountUp } from "../fx";
import { IconUpload, IconCheck } from "../icons";

const STAGES = ["Parse", "Extract", "Link"];

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
      <motion.label
        animate={{ scale: drag ? 1.02 : 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 28 }}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); handle(e.dataTransfer.files[0]); }}
        className={`relative block rounded-2xl p-8 text-center cursor-pointer transition-shadow glass ${
          drag ? "shadow-glow-accent" : "hover:shadow-glow-teal"
        }`}
      >
        {/* marching dashed border */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" aria-hidden="true">
          <rect
            x="1.5" y="1.5"
            rx="15" fill="none"
            stroke={drag ? "#f5a623" : "#2b3f66"}
            strokeWidth="1.5"
            strokeDasharray="8 6"
            style={{ width: "calc(100% - 3px)", height: "calc(100% - 3px)", animation: "marchDash 24s linear infinite" }}
          />
        </svg>
        <input type="file" className="hidden" onChange={(e) => handle(e.target.files[0])}
          accept=".pdf,.txt,.md,.eml,.csv,.xlsx,.png,.jpg,.jpeg" />
        <IconUpload className={`w-9 h-9 mx-auto animate-float ${drag ? "text-accent" : "text-teal"}`} />
        <div className="text-sm font-semibold mt-2.5 text-white">
          {busy ? "Extracting & linking into the graph…" : "Drop a document to ingest live"}
        </div>
        <div className="text-xs text-slate-400 mt-1 font-mono">PDF · scanned form / P&ID · spreadsheet · email · text</div>
      </motion.label>

      <AnimatePresence>
        {busy && <PipelineIndicator key="pipe" />}
      </AnimatePresence>

      {result && !result.error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-strong rounded-xl p-3.5"
        >
          <div className="flex items-center gap-2 text-sm">
            <span className="w-5 h-5 rounded-full bg-emerald-500/15 text-emerald-400 grid place-items-center">
              <IconCheck className="w-3 h-3" />
            </span>
            <span className="text-emerald-400 font-medium">ingested</span>
            <span className="font-medium text-white truncate">{result.document.title}</span>
            <span className="ml-auto text-[10px] font-mono text-slate-400">{result.provider}</span>
          </div>
          <div className="flex gap-2 mt-2.5 text-xs font-mono">
            <span className="bg-teal/10 text-teal border border-teal/30 rounded-full px-2.5 py-0.5">
              +<CountUp value={result.added_entities} duration={700} /> entities
            </span>
            <span className="bg-accent/10 text-accent border border-accent/30 rounded-full px-2.5 py-0.5">
              +<CountUp value={result.added_relationships} duration={700} /> relationships
            </span>
          </div>
          <div className="mt-3 grid gap-1">
            {result.extraction.entities.slice(0, 12).map((e, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + i * 0.06, type: "spring", stiffness: 300, damping: 24 }}
                className="flex items-center gap-2 text-xs"
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ background: TYPE_COLORS[e.type] || "#64748b", boxShadow: `0 0 6px ${TYPE_COLORS[e.type] || "#64748b"}aa` }}
                />
                <span className="font-mono text-white">{e.name}</span>
                <span className="text-slate-500">{e.type}</span>
              </motion.div>
            ))}
          </div>
          {result.extraction.relations?.length > 0 && (
            <div className="mt-2.5 text-xs text-slate-400 space-y-0.5">
              {result.extraction.relations.slice(0, 6).map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 + i * 0.08 }}
                  className="font-mono"
                >
                  {r.source} <span className="text-accent">─{r.type}<span className="arrow-pulse">→</span></span> {r.target}
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      )}
      {result?.error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-400 text-sm">
          ⚠️ {result.error}
        </motion.div>
      )}
    </div>
  );
}

/* Parse → Extract → Link stage chips lighting up in sequence */
function PipelineIndicator() {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setStage((s) => (s + 1) % (STAGES.length + 1)), 900);
    return () => clearInterval(id);
  }, []);
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="glass rounded-xl px-4 py-3 flex items-center gap-2"
    >
      {STAGES.map((s, i) => (
        <React.Fragment key={s}>
          {i > 0 && (
            <div className="flex-1 h-px relative overflow-hidden bg-edge">
              {stage >= i && (
                <motion.div
                  className="absolute inset-y-0 w-8 bg-gradient-to-r from-transparent via-teal to-transparent"
                  animate={{ x: ["-100%", "400%"] }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                />
              )}
            </div>
          )}
          <span
            className={`text-xs font-mono px-2.5 py-1 rounded-full border transition-all ${
              stage >= i
                ? "border-teal/50 text-teal bg-teal/10 shadow-glow-teal"
                : "border-edge text-slate-500"
            }`}
          >
            {s}
          </span>
        </React.Fragment>
      ))}
      <span className="ml-2 text-[11px] text-slate-400 font-mono hidden sm:inline">AI entity + relationship extraction…</span>
    </motion.div>
  );
}
