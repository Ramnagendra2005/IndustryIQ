import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api";
import { CountUp, Reveal, RadialGauge } from "../fx";
import { DocTypeIcon } from "../icons";

const STATUS = {
  gap: { label: "GAP", color: "#f87171", bg: "bg-red-500/5", rail: "#f87171" },
  at_risk: { label: "AT RISK", color: "#f5a623", bg: "bg-accent/5", rail: "#f5a623" },
  met: { label: "MET", color: "#34d399", bg: "bg-emerald-500/5", rail: "#34d399" },
};

export default function Compliance({ onOpenDoc }) {
  const [rep, setRep] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.compliance().then((r) => { setRep(r); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-3 space-y-3">
        <div className="skeleton h-24" />
        <div className="skeleton h-28" />
        <div className="skeleton h-28" />
        <div className="skeleton h-28" />
      </div>
    );
  }
  if (!rep) return <div className="p-4 text-slate-400 text-sm">No report.</div>;

  const items = [...rep.gaps, ...rep.met];
  const nGaps = rep.gaps.filter((g) => g.status === "gap").length;
  const nRisk = rep.gaps.filter((g) => g.status === "at_risk").length;

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      <Reveal>
        <div className="glass-strong rounded-xl p-4 flex items-center gap-4">
          <RadialGauge value={rep.readiness_score} size={84} stroke={7} sublabel="ready" />
          <div className="min-w-0 flex-1">
            <div className="text-sm font-bold text-white">Audit readiness — {rep.audit_scope}</div>
            <div className="text-xs text-slate-400 mt-0.5">Factory Act · OISD-116 · ISO 10816 · auto-generated evidence pack</div>
            <div className="flex gap-2 mt-2.5 text-[11px] font-mono">
              <span className="bg-red-500/10 text-red-300 border border-red-500/30 rounded-full px-2 py-0.5">
                <CountUp value={nGaps} /> gaps
              </span>
              <span className="bg-accent/10 text-accent border border-accent/30 rounded-full px-2 py-0.5">
                <CountUp value={nRisk} /> at risk
              </span>
              <span className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 rounded-full px-2 py-0.5">
                <CountUp value={rep.met.length} /> met
              </span>
              <span className="text-slate-500 self-center ml-auto">{rep.elapsed_ms} ms</span>
            </div>
          </div>
        </div>
      </Reveal>

      {items.map((g, i) => {
        const s = STATUS[g.status] || STATUS.gap;
        return (
          <Reveal key={i} delay={0.08 + i * 0.06}>
            <div className={`relative rounded-xl glass ${s.bg} p-3.5 pl-4 overflow-hidden`}>
              {/* status rail */}
              <span className="absolute left-0 top-0 bottom-0 w-[3px]" style={{ background: s.rail, boxShadow: `0 0 8px ${s.rail}88` }} />
              <div className="flex items-center gap-2">
                <span
                  className="text-[10px] font-bold font-mono tracking-widest px-2 py-0.5 rounded-full flex items-center gap-1.5"
                  style={{ color: s.color, border: `1px solid ${s.color}55`, background: `${s.color}12` }}
                >
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.color, boxShadow: `0 0 5px ${s.color}` }} />
                  {s.label}
                </span>
                <span className="text-sm font-semibold text-white">{g.regulation}</span>
                {g.severity === "high" && (
                  <motion.span
                    animate={{ opacity: [1, 0.5, 1] }}
                    transition={{ duration: 1.6, repeat: Infinity }}
                    className="ml-auto text-[10px] font-mono text-red-300 tracking-widest"
                  >
                    HIGH SEVERITY
                  </motion.span>
                )}
              </div>
              <div className="text-xs text-slate-400 mt-2">{g.requirement}</div>
              <div className="text-sm text-slate-100 mt-1.5">{g.finding}</div>
              {g.evidence_docs?.length > 0 && (
                <div className="mt-2.5 flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] text-slate-500 font-mono tracking-wide">EVIDENCE</span>
                  {g.evidence_docs.map((d, j) => (
                    <button
                      key={j}
                      onClick={() => onOpenDoc?.(d.doc_id)}
                      className="text-[11px] font-mono bg-ink/60 border border-edge rounded-lg px-2 py-1 hover:border-teal hover:shadow-glow-teal transition-all flex items-center gap-1.5"
                    >
                      <DocTypeIcon type={d.doc_type} className="w-3.5 h-3.5 text-slate-400" />
                      {d.doc_id}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Reveal>
        );
      })}
    </div>
  );
}
