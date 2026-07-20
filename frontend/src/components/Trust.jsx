import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api";
import { CountUp, Reveal, RadialGauge, GlowBar } from "../fx";
import { DocTypeIcon, IconConflict } from "../icons";

const KIND_LABEL = {
  numeric_conflict: "NUMERIC CONFLICT",
  doc_vs_reality: "DOC vs REALITY",
  stale_reference: "STALE REFERENCE",
  version_conflict: "VERSION CONFLICT",
};

const SEV = {
  high: { color: "#f87171", bg: "bg-red-500/5" },
  medium: { color: "#f5a623", bg: "bg-accent/5" },
  low: { color: "#60a5fa", bg: "bg-sky-500/5" },
};

export const FRESH_COLOR = (f) => (f >= 0.6 ? "#34d399" : f >= 0.3 ? "#f5a623" : "#f87171");

export default function Trust({ onOpenDoc }) {
  const [rep, setRep] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.trust().then((r) => { setRep(r); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-3 space-y-3">
        <div className="skeleton h-24" />
        <div className="skeleton h-28" />
        <div className="skeleton h-28" />
        <div className="skeleton h-40" />
      </div>
    );
  }
  if (!rep) return <div className="p-4 text-slate-400 text-sm">No trust report.</div>;

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      {/* header: corpus health */}
      <Reveal>
        <div className="glass-strong rounded-xl p-4 flex items-center gap-4">
          <RadialGauge value={rep.corpus_health} size={84} stroke={7} sublabel="trusted" />
          <div className="min-w-0 flex-1">
            <div className="text-sm font-bold text-white">Trust Layer — can you act on what the documents say?</div>
            <div className="text-xs text-slate-400 mt-0.5">
              Continuous scan for contradictions between documents and staleness against the corpus clock
            </div>
            <div className="flex gap-2 mt-2.5 text-[11px] font-mono">
              <span className="bg-red-500/10 text-red-300 border border-red-500/30 rounded-full px-2 py-0.5">
                <CountUp value={rep.conflicts.length} /> conflicts
              </span>
              <span className="bg-accent/10 text-accent border border-accent/30 rounded-full px-2 py-0.5">
                <CountUp value={rep.aging_count} /> aging
              </span>
              <span className="bg-red-500/10 text-red-300 border border-red-500/30 rounded-full px-2 py-0.5">
                <CountUp value={rep.stale_count} /> stale
              </span>
              <span className="text-slate-500 self-center ml-auto">{rep.elapsed_ms} ms</span>
            </div>
          </div>
        </div>
      </Reveal>

      {/* conflicts */}
      {rep.conflicts.map((c, i) => {
        const s = SEV[c.severity] || SEV.medium;
        return (
          <Reveal key={c.id} delay={0.08 + i * 0.06}>
            <div className={`relative rounded-xl glass ${s.bg} p-3.5 pl-4 overflow-hidden`}>
              <span className="absolute left-0 top-0 bottom-0 w-[3px]" style={{ background: s.color, boxShadow: `0 0 8px ${s.color}88` }} />
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className="text-[10px] font-bold font-mono tracking-widest px-2 py-0.5 rounded-full flex items-center gap-1.5"
                  style={{ color: s.color, border: `1px solid ${s.color}55`, background: `${s.color}12` }}
                >
                  <IconConflict className="w-3 h-3" />
                  {KIND_LABEL[c.kind] || c.kind}
                </span>
                <span className="text-sm font-semibold text-white">{c.title}</span>
                {c.severity === "high" && (
                  <motion.span
                    animate={{ opacity: [1, 0.5, 1] }}
                    transition={{ duration: 1.6, repeat: Infinity }}
                    className="ml-auto text-[10px] font-mono text-red-300 tracking-widest"
                  >
                    HIGH SEVERITY
                  </motion.span>
                )}
              </div>
              <div className="text-sm text-slate-100 mt-2">{c.detail}</div>
              <div className="mt-2.5 flex flex-wrap gap-1.5 items-center">
                <span className="text-[10px] text-slate-500 font-mono tracking-wide">CONFLICTING SOURCES</span>
                {c.doc_ids.map((id) => (
                  <button
                    key={id}
                    onClick={() => onOpenDoc?.(id)}
                    className="text-[11px] font-mono bg-ink/60 border border-edge rounded-lg px-2 py-1 hover:border-teal hover:shadow-glow-teal transition-all"
                  >
                    {id}
                  </button>
                ))}
              </div>
            </div>
          </Reveal>
        );
      })}

      {/* freshness table */}
      <Reveal delay={0.15}>
        <div className="glass rounded-xl p-3.5">
          <div className="text-[11px] text-slate-400 mb-2.5 font-mono tracking-wide flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-teal live-dot" />
            DOCUMENT FRESHNESS — DECAYS BY DOC-TYPE HALF-LIFE
          </div>
          <div className="space-y-2">
            {rep.freshness.map((f, i) => (
              <motion.button
                key={f.doc_id}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.05 + i * 0.03 }}
                onClick={() => onOpenDoc?.(f.doc_id)}
                className="w-full text-left flex items-center gap-2.5 group"
                title={f.note}
              >
                <DocTypeIcon type={f.doc_type} className="w-4 h-4 shrink-0" style={{ color: FRESH_COLOR(f.freshness) }} />
                <span className="text-xs font-mono text-slate-300 w-36 truncate shrink-0 group-hover:text-white transition-colors">
                  {f.doc_id}
                </span>
                <div className="flex-1 min-w-0">
                  <GlowBar value={f.freshness} color={FRESH_COLOR(f.freshness)} height={5} />
                </div>
                <span className="text-[10px] font-mono w-10 text-right shrink-0" style={{ color: FRESH_COLOR(f.freshness) }}>
                  {Math.round(f.freshness * 100)}%
                </span>
                <span className="text-[10px] font-mono text-slate-500 w-20 text-right shrink-0 hidden sm:inline">
                  {f.date || "no date"}
                </span>
              </motion.button>
            ))}
          </div>
        </div>
      </Reveal>
    </div>
  );
}
