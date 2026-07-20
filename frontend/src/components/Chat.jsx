import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { api } from "../api";
import { renderRich } from "../lib";
import { CountUp, Reveal, StreamText, RadialGauge, ThinkingIndicator } from "../fx";
import { IconChat, IconMicroscope, IconSend, IconBrain, IconConflict, DocTypeIcon, DOCTYPE_TINT } from "../icons";

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
            className={`relative px-3.5 py-1 rounded-full text-sm font-medium transition-colors ${
              mode === mm.id ? "text-ink" : "text-slate-300 hover:text-white"
            }`}
          >
            {mode === mm.id && (
              <motion.span
                layoutId="chatModePill"
                className="absolute inset-0 rounded-full bg-accent shadow-glow-accent"
                transition={{ type: "spring", stiffness: 500, damping: 35 }}
              />
            )}
            <span className="relative z-10">{mm.label}</span>
          </button>
        ))}
        <span className="text-xs text-slate-500 ml-1 hidden sm:inline">
          {MODES.find((x) => x.id === mode)?.hint}
        </span>
      </div>

      {/* messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-4">
            <Reveal>
              <HeroMark />
              <h2 className="text-xl font-bold text-white mt-3 tracking-tight">
                Ask the plant's <span className="text-gradient">collective memory</span>
              </h2>
              <p className="text-sm max-w-sm mx-auto mt-1.5 text-slate-400">
                The copilot fuses P&IDs, work orders, inspections, OEM manuals and
                incident history into one answer — with sources.
              </p>
            </Reveal>

            {/* proactive alert — surfaces the cross-doc risk before anyone asks */}
            <Reveal delay={0.15}>
              <button
                onClick={() => send("Why is pump P-101 vibrating and tripping?", "rca")}
                className="mt-5 block w-full max-w-md mx-auto text-left rounded-xl border-flow px-3.5 py-3 hover:shadow-glow-danger transition-shadow group"
              >
                <div className="flex items-center gap-2 text-[11px] font-bold text-red-300 tracking-widest font-mono">
                  <span className="w-2 h-2 rounded-full bg-red-400 danger-dot" /> PROACTIVE ALERT — LIVE
                </div>
                <div className="text-sm text-slate-100 mt-1.5">
                  P-101 vibration trending toward the OEM trip limit — sister pump <b>P-102</b> failed
                  catastrophically under this same signature in 2023.
                </div>
                <VibrationMeter value={5.8} alarm={4.5} trip={7.1} />
                <div className="text-xs text-red-300/90 mt-2 flex items-center gap-1">
                  Run root-cause analysis
                  <span className="transition-transform group-hover:translate-x-1">→</span>
                </div>
              </button>
            </Reveal>

            <div className="mt-4 grid gap-2 max-w-md mx-auto">
              {SUGGESTIONS.map((s, i) => (
                <Reveal key={i} delay={0.25 + i * 0.07}>
                  <button
                    onClick={() => send(s.q, s.mode)}
                    className="w-full text-left text-sm px-3.5 py-2.5 rounded-xl glass hover:border-edge2 hover:shadow-glow-teal transition-all flex items-center gap-2.5 group"
                  >
                    {s.mode === "rca"
                      ? <IconMicroscope className="w-4 h-4 text-accent shrink-0" />
                      : <IconChat className="w-4 h-4 text-teal shrink-0" />}
                    <span className="text-slate-200 group-hover:text-white transition-colors">{s.q}</span>
                  </button>
                </Reveal>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className="flex justify-end"
            >
              <div className="bg-gradient-to-br from-accent to-[#e8920c] text-ink px-3.5 py-2 rounded-2xl rounded-br-sm max-w-[85%] text-sm font-medium shadow-glow-accent">
                {m.text}
              </div>
            </motion.div>
          ) : (
            <Answer key={i} m={m} onFocusEntity={onFocusEntity} onOpenDoc={onOpenDoc} stream={i === messages.length - 1} />
          )
        )}

        {busy && <ThinkingIndicator />}
      </div>

      {/* input */}
      <div className="p-3 border-t border-edge shrink-0">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder={field ? "Ask from the field…" : "Ask about any asset, failure, or regulation…"}
            className="flex-1 glass rounded-xl px-3.5 py-2.5 text-sm outline-none focus:border-accent focus:shadow-glow-accent transition-shadow bg-transparent"
          />
          <motion.button
            whileTap={{ scale: 0.88 }}
            onClick={() => send()}
            disabled={busy}
            className="w-11 h-11 rounded-xl bg-accent text-ink grid place-items-center disabled:opacity-50 shadow-glow-accent"
          >
            <IconSend className="w-5 h-5" />
          </motion.button>
        </div>
      </div>
    </div>
  );
}

/* Animated hero mark — orbiting graph nodes */
function HeroMark() {
  return (
    <div className="relative w-16 h-16 mx-auto">
      <motion.div
        className="absolute inset-0"
        animate={{ rotate: 360 }}
        transition={{ duration: 24, repeat: Infinity, ease: "linear" }}
      >
        <span className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-teal shadow-glow-teal" />
        <span className="absolute bottom-1 left-1 w-1.5 h-1.5 rounded-full bg-glow shadow-glow-blue" />
        <span className="absolute bottom-2 right-0 w-2 h-2 rounded-full bg-accent shadow-glow-accent" />
      </motion.div>
      <div className="absolute inset-0 grid place-items-center">
        <IconBrain className="w-9 h-9 text-slate-300 animate-float" />
      </div>
    </div>
  );
}

/* Live-feeling vibration meter: needle jitters in the amber zone */
function VibrationMeter({ value, alarm, trip }) {
  const max = trip * 1.15;
  const pct = (v) => (v / max) * 100;
  return (
    <div className="mt-2.5">
      <div className="flex justify-between text-[10px] font-mono text-slate-400 mb-1">
        <span>VIBRATION — P-101 DE BEARING</span>
        <span className="text-amber">{value} mm/s</span>
      </div>
      <div className="relative h-2.5 rounded-full overflow-hidden bg-ink/80 border border-edge">
        {/* zones */}
        <div className="absolute inset-y-0 left-0 bg-emerald-500/25" style={{ width: `${pct(alarm)}%` }} />
        <div className="absolute inset-y-0 bg-amber/25" style={{ left: `${pct(alarm)}%`, width: `${pct(trip) - pct(alarm)}%` }} />
        <div className="absolute inset-y-0 bg-red-500/30" style={{ left: `${pct(trip)}%`, right: 0 }} />
        {/* trip threshold */}
        <div className="absolute inset-y-0 w-px bg-red-400" style={{ left: `${pct(trip)}%` }} />
        {/* needle */}
        <div className="absolute inset-y-0 needle-jitter" style={{ left: `${pct(value)}%` }}>
          <div className="w-0.5 h-full bg-white shadow-[0_0_6px_rgba(255,255,255,0.9)]" />
        </div>
      </div>
      <div className="flex justify-between text-[9px] font-mono text-slate-500 mt-0.5">
        <span>0</span>
        <span className="text-amber">alarm {alarm}</span>
        <span className="text-red-400">trip {trip}</span>
      </div>
    </div>
  );
}

function Answer({ m, onFocusEntity, onOpenDoc, stream }) {
  const baselineMin = 20; // McKinsey: ~35% of day searching; a manual cross-doc dig ≈ 20 min
  const [streamed, setStreamed] = useState(!stream);
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
      <div className="glass rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed">
        {stream && !streamed ? (
          <StreamText
            text={m.answer || ""}
            speed={16}
            render={(t) => renderRich(t, onOpenDoc)}
            onDone={() => setStreamed(true)}
          />
        ) : (
          renderRich(m.answer || "", onOpenDoc)
        )}
      </div>

      {streamed && (
        <>
          {/* metrics row */}
          <Reveal className="flex flex-wrap items-center gap-2 text-xs">
            <div className="flex items-center gap-2 glass rounded-full pl-1 pr-3 py-1">
              <RadialGauge value={m.confidence || 0} size={30} stroke={3.5} />
              <span className="text-slate-400">confidence</span>
            </div>
            <div className="bg-teal/10 text-teal border border-teal/30 rounded-full px-2.5 py-1 font-mono flex items-center gap-1">
              ⚡ <CountUp value={m._wall ?? m.elapsed_ms} duration={600} /> ms
              <span className="text-slate-500">vs</span>
              <span className="line-through decoration-red-400/70 text-slate-400">~{baselineMin} min</span>
              <span className="text-slate-500">manual</span>
            </div>
            {m.mode === "rca" && (
              <div className="bg-accent/10 text-accent border border-accent/30 rounded-full px-2.5 py-1 flex items-center gap-1.5">
                <IconMicroscope className="w-3.5 h-3.5" /> Root-Cause Analysis
              </div>
            )}
            {m.trust && (
              <div
                className="rounded-full px-2.5 py-1 font-mono flex items-center gap-1.5 border"
                style={{
                  color: m.trust.freshness >= 0.6 ? "#34d399" : m.trust.freshness >= 0.3 ? "#f5a623" : "#f87171",
                  borderColor: (m.trust.freshness >= 0.6 ? "#34d399" : m.trust.freshness >= 0.3 ? "#f5a623" : "#f87171") + "4d",
                  background: (m.trust.freshness >= 0.6 ? "#34d399" : m.trust.freshness >= 0.3 ? "#f5a623" : "#f87171") + "14",
                }}
                title="Freshness of the weakest cited source"
              >
                ● sources {Math.round(m.trust.freshness * 100)}% fresh
              </div>
            )}
          </Reveal>

          {/* trust layer — conflict & staleness warnings on the cited sources */}
          {m.trust?.warnings?.length > 0 && (
            <Reveal delay={0.08} className="rounded-xl border border-amber/40 bg-amber/5 px-3 py-2.5">
              <div className="text-[11px] text-amber mb-1.5 flex items-center gap-1.5 font-mono tracking-widest font-bold">
                <IconConflict className="w-3.5 h-3.5" />
                TRUST CHECK — {m.trust.warnings.length} CAUTION{m.trust.warnings.length > 1 ? "S" : ""} ON THESE SOURCES
              </div>
              <ul className="space-y-1">
                {m.trust.warnings.map((w, i) => (
                  <li key={i} className="text-xs text-slate-200 flex gap-1.5">
                    <span className="text-amber shrink-0">⚠</span> {w}
                  </li>
                ))}
              </ul>
            </Reveal>
          )}

          {/* graph paths — the connected-dots evidence trail */}
          {m.graph_paths?.length > 0 && (
            <Reveal delay={0.1} className="glass rounded-xl px-3 py-2.5">
              <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-1.5 font-mono tracking-wide">
                <span className="w-1.5 h-1.5 rounded-full bg-amber live-dot" />
                EVIDENCE TRAIL — KNOWLEDGE-GRAPH LINKS
              </div>
              <div className="flex flex-wrap gap-1.5">
                {m.graph_paths.slice(0, 10).map((h, i) => (
                  <motion.span
                    key={i}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.12 + i * 0.06 }}
                    className="text-xs font-mono bg-ink/60 border border-edge rounded-lg px-2 py-1"
                  >
                    <button className="text-accent hover:underline" onClick={() => onFocusEntity?.(h.source)}>{h.source}</button>
                    <span className="text-slate-500 mx-1">─{h.relation}<span className="arrow-pulse text-amber">→</span></span>
                    <button className="text-teal hover:underline" onClick={() => onFocusEntity?.(h.target)}>{h.target}</button>
                  </motion.span>
                ))}
              </div>
            </Reveal>
          )}

          {/* citations */}
          {m.citations?.length > 0 && (
            <div>
              <Reveal delay={0.15} className="text-[11px] text-slate-400 mb-1.5 font-mono tracking-wide">
                {m.citations.length} SOURCES · {new Set(m.citations.map((c) => c.doc_type)).size} DOCUMENT TYPES
              </Reveal>
              <div className="grid gap-1.5">
                {m.citations.slice(0, 6).map((c, i) => (
                  <motion.button
                    key={i}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.18 + i * 0.06 }}
                    whileHover={{ y: -2 }}
                    onClick={() => onOpenDoc?.(c.doc_id)}
                    className="text-left glass rounded-xl px-3 py-2 hover:border-teal hover:shadow-glow-teal transition-all"
                  >
                    <div className="flex items-center gap-2.5 text-sm">
                      <span
                        className="w-7 h-7 rounded-lg grid place-items-center shrink-0"
                        style={{ background: `${DOCTYPE_TINT[c.doc_type] || "#94a3b8"}1a`, color: DOCTYPE_TINT[c.doc_type] || "#94a3b8" }}
                      >
                        <DocTypeIcon type={c.doc_type} className="w-4 h-4" />
                      </span>
                      <span className="font-medium text-white truncate">{c.title}</span>
                      <span className="text-xs font-mono text-teal ml-auto shrink-0">{c.doc_id}</span>
                    </div>
                    <div className="text-xs text-slate-400 mt-1 line-clamp-2 pl-9">{c.snippet}</div>
                  </motion.button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
