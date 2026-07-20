import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

/* ------------------------------------------------------------------ */
/* CountUp — springy animated number                                    */
/* ------------------------------------------------------------------ */
export function CountUp({ value = 0, duration = 900, className = "" }) {
  const [display, setDisplay] = useState(0);
  const fromRef = useRef(0);

  useEffect(() => {
    const from = fromRef.current;
    const to = Number(value) || 0;
    if (from === to) { setDisplay(to); return; }
    const t0 = performance.now();
    let raf;
    const tick = (t) => {
      const p = Math.min((t - t0) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
      setDisplay(Math.round(from + (to - from) * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = to;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);

  return <span className={className}>{display}</span>;
}

/* ------------------------------------------------------------------ */
/* Reveal — staggered fade+rise entrance wrapper                        */
/* ------------------------------------------------------------------ */
export function Reveal({ children, delay = 0, y = 10, className = "" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/* StreamText — types content in word-by-word with a caret.             */
/* render(visibleText) lets the caller keep rich rendering (DOC chips). */
/* Click to skip. Calls onDone when finished.                           */
/* ------------------------------------------------------------------ */
export function StreamText({ text = "", speed = 18, render, onDone, className = "" }) {
  const words = useRef(text.split(/(\s+)/)); // keep whitespace tokens
  const [count, setCount] = useState(0);
  const doneRef = useRef(false);
  const total = words.current.length;
  const done = count >= total;

  useEffect(() => {
    if (done) {
      if (!doneRef.current) { doneRef.current = true; onDone?.(); }
      return;
    }
    const id = setTimeout(() => setCount((c) => c + 2), speed);
    return () => clearTimeout(id);
  }, [count, done, speed, onDone]);

  const visible = done ? text : words.current.slice(0, count).join("");

  return (
    <div
      className={`${className} ${done ? "" : "stream-caret cursor-pointer"}`}
      onClick={() => !done && setCount(total)}
      title={done ? undefined : "Click to skip"}
    >
      {render ? render(visible) : visible}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* GlowBar — progress bar that fills with a moving sheen                */
/* ------------------------------------------------------------------ */
export function GlowBar({ value = 0, color = "#2dd4bf", height = 6, className = "" }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className={`rounded-full bg-edge overflow-hidden ${className}`} style={{ height }}>
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        className="h-full rounded-full relative overflow-hidden"
        style={{ background: color, boxShadow: `0 0 10px ${color}66` }}
      >
        <div
          className="absolute inset-0"
          style={{
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent)",
            backgroundSize: "200% 100%",
            animation: "shimmer 2s linear infinite",
          }}
        />
      </motion.div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* RadialGauge — SVG circular gauge with animated arc + glow            */
/* ------------------------------------------------------------------ */
export function RadialGauge({ value = 0, size = 64, stroke = 6, color, label, sublabel }) {
  const pct = Math.max(0, Math.min(1, value));
  const c = color || (pct >= 0.75 ? "#34d399" : pct >= 0.5 ? "#f5a623" : "#f87171");
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const [shown, setShown] = useState(0);

  useEffect(() => {
    const t0 = performance.now();
    let raf;
    const tick = (t) => {
      const p = Math.min((t - t0) / 1000, 1);
      setShown(pct * (1 - Math.pow(1 - p, 3)));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [pct]);

  return (
    <div className="relative inline-grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1d2b47" strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={c} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - shown)}
          style={{ filter: `drop-shadow(0 0 4px ${c}88)` }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center leading-none">
        <div>
          <div className="font-mono font-bold" style={{ color: c, fontSize: size * 0.24 }}>
            {label ?? `${Math.round(shown * 100)}%`}
          </div>
          {sublabel && <div className="text-slate-500" style={{ fontSize: size * 0.11 }}>{sublabel}</div>}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* ThinkingIndicator — cycles retrieval phases with traveling pulse     */
/* ------------------------------------------------------------------ */
const PHASES = ["Traversing knowledge graph", "Ranking evidence", "Composing answer"];
export function ThinkingIndicator() {
  const [phase, setPhase] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setPhase((p) => (p + 1) % PHASES.length), 1100);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="flex items-center gap-2.5 text-slate-400 text-sm fade-in">
      <span className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-teal"
            animate={{ opacity: [0.25, 1, 0.25], scale: [0.85, 1.15, 0.85] }}
            transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.22 }}
          />
        ))}
      </span>
      <motion.span
        key={phase}
        initial={{ opacity: 0, y: 3 }}
        animate={{ opacity: 1, y: 0 }}
        className="font-mono text-xs tracking-wide"
      >
        {PHASES[phase]}…
      </motion.span>
    </div>
  );
}
