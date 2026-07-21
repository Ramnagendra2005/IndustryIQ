import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api";
import { Reveal } from "../fx";
import { IconMap, IconAlert, IconImage } from "../icons";
import Dossier, { HEALTH } from "./Dossier";

/**
 * Interactive P&ID — "the drawing is the interface".
 *
 * Renders either an authored VECTOR diagram (crisp ISA glyphs from geometry) or
 * an uploaded IMAGE diagram (transparent clickable hotspots over the original
 * picture, with a tag-rail fallback when symbol positions weren't detected).
 * Every symbol is colour-coded by health and opens its full dossier on click.
 */
export default function PID({ onOpenDoc, onAsk, onFocusEntity }) {
  const [list, setList] = useState(null);
  const [active, setActive] = useState(null);      // doc_id
  const [diagram, setDiagram] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [selected, setSelected] = useState(null);  // clicked entity → dossier

  useEffect(() => {
    api.pids()
      .then((rows) => {
        setList(rows);
        setLoading(false);
        if (rows.length) setActive(rows[0].doc_id);
      })
      .catch((e) => { setErr(e.message); setLoading(false); });
  }, []);

  useEffect(() => {
    if (!active) return;
    setDiagram(null);
    api.pid(active).then(setDiagram).catch((e) => setErr(e.message));
  }, [active]);

  if (loading) return <div className="p-3 space-y-3"><div className="skeleton h-10" /><div className="skeleton h-72" /></div>;
  if (err && !list) return <div className="p-4 text-sm text-red-300">⚠️ {err}</div>;
  if (list && list.length === 0)
    return (
      <div className="p-6 text-center text-slate-400 text-sm">
        <IconMap className="w-10 h-10 mx-auto mb-2 text-slate-600" />
        No P&IDs yet. Upload a P&ID drawing in the <b className="text-white">Ingest</b> tab and it becomes clickable here.
      </div>
    );

  return (
    <div className="h-full flex flex-col relative">
      {/* diagram selector */}
      <div className="shrink-0 flex items-center gap-2 px-3 py-2 border-b border-edge overflow-x-auto">
        {list.map((p) => (
          <button
            key={p.doc_id}
            onClick={() => { setActive(p.doc_id); setSelected(null); }}
            className={`relative shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              active === p.doc_id ? "text-white glass border border-edge2" : "text-slate-400 hover:text-white"
            }`}
            title={p.title}
          >
            {p.kind === "image" ? <IconImage className="w-4 h-4" /> : <IconMap className="w-4 h-4" />}
            <span className="max-w-[160px] truncate">{p.title}</span>
            {p.alert_count > 0 && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-red-500/15 text-red-300 border border-red-500/30 flex items-center gap-0.5">
                <IconAlert className="w-2.5 h-2.5" /> {p.alert_count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* canvas */}
      <div className="flex-1 min-h-0 overflow-auto p-3">
        {!diagram ? (
          <div className="skeleton h-full min-h-[300px]" />
        ) : (
          <Reveal>
            <div className="mb-2 flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-white">{diagram.title}</h3>
              {diagram.unit && <span className="text-xs text-slate-400">· {diagram.unit}</span>}
              <span className="text-[10px] font-mono text-slate-500 ml-auto uppercase tracking-widest">
                {diagram.kind} · {diagram.symbols.length} symbols
              </span>
            </div>

            {diagram.kind === "vector"
              ? <VectorCanvas diagram={diagram} onPick={setSelected} />
              : <ImageCanvas diagram={diagram} onPick={setSelected} />}

            {diagram.note && (
              <div className="mt-2 text-xs text-slate-400 glass rounded-lg px-3 py-2">{diagram.note}</div>
            )}

            <Legend />
          </Reveal>
        )}
      </div>

      <Dossier
        name={selected}
        onClose={() => setSelected(null)}
        onOpenDoc={onOpenDoc}
        onAsk={onAsk}
        onFocusEntity={(tag) => setSelected(tag)}
      />
    </div>
  );
}

/* ---------------- vector renderer (ISA glyphs from geometry) ------------- */
function VectorCanvas({ diagram, onPick }) {
  const { view, symbols, connections } = diagram;
  const byTag = useMemo(() => Object.fromEntries(symbols.map((s) => [s.tag, s])), [symbols]);

  return (
    <div className="rounded-xl glass p-2 overflow-hidden">
      <svg viewBox={`0 0 ${view.w} ${view.h}`} className="w-full h-auto" style={{ maxHeight: "58vh" }}>
        <defs>
          <marker id="pid-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0 0L10 5L0 10z" fill="#3b5379" />
          </marker>
        </defs>

        {/* pipes / relations */}
        {connections.map((c, i) => {
          const a = byTag[c.source], b = byTag[c.target];
          if (!a || !b) return null;
          const flow = c.type === "CONNECTED_TO";
          const dash = c.type === "SIBLING_OF" ? "7 6" : c.type === "HAS_PART" ? "2 5" : "0";
          const col = c.type === "SIBLING_OF" ? "#5b7bb0" : c.type === "HAS_PART" ? "#c084fc" : "#3b5379";
          const mx = (a.cx + b.cx) / 2, my = (a.cy + b.cy) / 2;
          return (
            <g key={i}>
              <line
                x1={a.cx} y1={a.cy} x2={b.cx} y2={b.cy}
                stroke={col} strokeWidth={flow ? 2.4 : 1.6} strokeDasharray={dash}
                markerEnd={flow ? "url(#pid-arrow)" : undefined} opacity={0.9}
              />
              {c.label && (
                <text x={mx} y={my - 5} fill="#7f93b5" fontSize="11" textAnchor="middle" className="font-mono select-none">
                  {c.label}
                </text>
              )}
            </g>
          );
        })}

        {/* symbols */}
        {symbols.map((s, i) => (
          <SymbolGlyph key={s.tag} s={s} delay={0.03 * i} onPick={onPick} />
        ))}
      </svg>
    </div>
  );
}

/* one ISA symbol + tag, coloured by health, clickable */
function SymbolGlyph({ s, delay, onPick }) {
  const h = HEALTH[s.health] || HEALTH.ok;
  const R = 26;
  // Outer <g> holds the position (static translate). The inner <motion.g> only
  // animates opacity + scale — keeping the two transforms on separate elements
  // so Framer Motion's generated transform never clobbers the translate.
  return (
    <g transform={`translate(${s.cx} ${s.cy})`}>
      <motion.g
        initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }}
        transition={{ delay, type: "spring", stiffness: 260, damping: 20 }}
        className="cursor-pointer"
        onClick={() => onPick(s.entity || s.tag)}
        style={{ transformBox: "fill-box", transformOrigin: "center" }}
      >
        {/* health halo */}
        {s.health !== "ok" && (
          <circle r={R + 7} fill="none" stroke={h.color} strokeWidth="2" opacity="0.35">
            <animate attributeName="opacity" values="0.35;0.1;0.35" dur="2s" repeatCount="indefinite" />
          </circle>
        )}
        <g stroke={h.color} strokeWidth="2.2" fill="#0e1626" className="pid-hit">
          <Glyph kind={s.symbol} r={R} />
        </g>
        {/* tag label */}
        <text y={R + 16} textAnchor="middle" fontSize="14" fontWeight="700" fill="#e2e8f0" className="font-mono select-none pointer-events-none">
          {s.tag}
        </text>
        {s.doc_count > 0 && (
          <text y={R + 30} textAnchor="middle" fontSize="10" fill="#64748b" className="font-mono select-none pointer-events-none">
            {s.doc_count} docs
          </text>
        )}
      </motion.g>
    </g>
  );
}

/* pure geometry for each ISA glyph kind, centered at origin, radius r */
function Glyph({ kind, r }) {
  switch (kind) {
    case "pump":
      return <><circle r={r} /><path d={`M0 ${-r}L${r * 0.55} ${-r * 0.15}L0 0Z`} fill="currentColor" stroke="none" /><circle r={r * 0.16} fill="currentColor" stroke="none" /></>;
    case "valve":
      return <><path d={`M${-r} ${-r * 0.7}L0 0L${-r} ${r * 0.7}Z`} /><path d={`M${r} ${-r * 0.7}L0 0L${r} ${r * 0.7}Z`} /></>;
    case "exchanger":
      return <><circle r={r} /><path d={`M${-r} 0h${2 * r}`} /><path d={`M${-r * 0.5} ${-r * 0.5}v${r}M${r * 0.5} ${-r * 0.5}v${r}`} strokeWidth="1.4" /></>;
    case "column":
      return <rect x={-r * 0.62} y={-r * 1.5} width={r * 1.24} height={r * 3} rx={r * 0.62} />;
    case "tank":
      return <path d={`M${-r} ${-r * 0.8}a${r} ${r * 0.5} 0 0 1 ${2 * r} 0v${r * 1.6}a${r} ${r * 0.5} 0 0 1 ${-2 * r} 0Z`} />;
    case "vessel":
      return <rect x={-r * 1.3} y={-r * 0.7} width={r * 2.6} height={r * 1.4} rx={r * 0.7} />;
    case "compressor":
      return <><circle r={r} /><path d={`M${-r * 0.7} ${-r * 0.5}L${r * 0.7} ${-r * 0.8}v${r * 1.6}L${-r * 0.7} ${r * 0.5}Z`} strokeWidth="1.6" /></>;
    case "instrument":
      return <><circle r={r * 0.9} /><path d={`M${-r * 0.9} 0h${r * 1.8}`} strokeWidth="1.2" /></>;
    default:
      return <rect x={-r * 0.8} y={-r * 0.8} width={r * 1.6} height={r * 1.6} rx={4} />;
  }
}

/* ---------------- image renderer (hotspots over the picture) ------------- */
function ImageCanvas({ diagram, onPick }) {
  const hasBoxes = diagram.symbols.some((s) => s.box);

  if (!diagram.image_url || !hasBoxes) {
    // fallback: clickable equipment-tag rail (offline / no geometry)
    return (
      <div className="rounded-xl glass p-3">
        {diagram.image_url && (
          <img src={diagram.image_url} alt={diagram.title} className="w-full rounded-lg mb-3 opacity-90" />
        )}
        <div className="flex flex-wrap gap-2">
          {diagram.symbols.map((s) => <TagButton key={s.tag} s={s} onPick={onPick} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl glass p-2">
      <div className="relative inline-block w-full">
        <img src={diagram.image_url} alt={diagram.title} className="w-full rounded-lg block" />
        {diagram.symbols.map((s, i) => {
          if (!s.box) return null;
          const [x, y, w, hh] = s.box;
          const h = HEALTH[s.health] || HEALTH.ok;
          return (
            <motion.button
              key={s.tag + i}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.02 * i }}
              onClick={() => onPick(s.entity || s.tag)}
              title={`${s.tag}${s.doc_count ? ` · ${s.doc_count} docs` : ""}`}
              className="absolute group"
              style={{ left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${hh * 100}%` }}
            >
              <span
                className="absolute inset-0 rounded-md border-2 transition-all group-hover:brightness-125"
                style={{ borderColor: h.color, background: `${h.color}1f`, boxShadow: s.health !== "ok" ? `0 0 10px ${h.color}aa` : "none" }}
              />
              <span
                className="absolute -top-5 left-0 text-[10px] font-mono font-bold px-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ background: h.color, color: "#0b1120" }}
              >
                {s.tag}
              </span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

function TagButton({ s, onPick }) {
  const h = HEALTH[s.health] || HEALTH.ok;
  return (
    <button
      onClick={() => onPick(s.entity || s.tag)}
      className="flex items-center gap-1.5 text-sm font-mono glass rounded-lg px-2.5 py-1.5 hover:border-teal transition-colors"
      style={{ borderColor: s.health !== "ok" ? h.color + "88" : undefined }}
    >
      <span className="w-2 h-2 rounded-full" style={{ background: h.color }} />
      {s.tag}
      {s.doc_count > 0 && <span className="text-[10px] text-slate-500">{s.doc_count}</span>}
    </button>
  );
}

function Legend() {
  return (
    <div className="mt-3 flex items-center gap-3 text-[11px] text-slate-400 flex-wrap">
      <span className="font-mono tracking-widest text-slate-500">HEALTH</span>
      {Object.entries(HEALTH).map(([k, v]) => (
        <span key={k} className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: v.color }} />
          {v.label}
        </span>
      ))}
      <span className="ml-auto text-slate-500">Click any symbol to open its dossier →</span>
    </div>
  );
}
