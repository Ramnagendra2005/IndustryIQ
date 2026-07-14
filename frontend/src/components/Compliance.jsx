import React, { useEffect, useState } from "react";
import { api } from "../api";
import { DOCTYPE_ICON } from "../lib";

const STATUS = {
  gap: { label: "GAP", color: "#f87171", bg: "bg-red-500/10", border: "border-red-500/40" },
  at_risk: { label: "AT RISK", color: "#f5a623", bg: "bg-accent/10", border: "border-accent/40" },
  met: { label: "MET", color: "#34d399", bg: "bg-emerald-500/10", border: "border-emerald-500/40" },
};

export default function Compliance({ onOpenDoc }) {
  const [rep, setRep] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.compliance().then((r) => { setRep(r); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4 text-slate-400 text-sm">Assessing compliance…</div>;
  if (!rep) return <div className="p-4 text-slate-400 text-sm">No report.</div>;

  const items = [...rep.gaps, ...rep.met];
  const pct = Math.round(rep.readiness_score * 100);

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      <div className="bg-panel2 border border-edge rounded-xl p-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-white">Audit readiness — {rep.audit_scope}</div>
            <div className="text-xs text-slate-400">Factory Act · OISD-116 · ISO 10816 · auto-generated evidence pack</div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold" style={{ color: pct >= 75 ? "#34d399" : pct >= 50 ? "#f5a623" : "#f87171" }}>{pct}%</div>
            <div className="text-[10px] text-slate-500">ready · {rep.elapsed_ms} ms</div>
          </div>
        </div>
        <div className="mt-2 h-2 rounded-full bg-edge overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: pct >= 75 ? "#34d399" : pct >= 50 ? "#f5a623" : "#f87171" }} />
        </div>
      </div>

      {items.map((g, i) => {
        const s = STATUS[g.status] || STATUS.gap;
        return (
          <div key={i} className={`rounded-xl border ${s.border} ${s.bg} p-3`}>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ color: s.color, border: `1px solid ${s.color}55` }}>
                {s.label}
              </span>
              <span className="text-sm font-semibold text-white">{g.regulation}</span>
              {g.severity === "high" && <span className="ml-auto text-[10px] text-red-300">HIGH SEVERITY</span>}
            </div>
            <div className="text-xs text-slate-300 mt-1.5">{g.requirement}</div>
            <div className="text-sm text-slate-100 mt-2">{g.finding}</div>
            {g.evidence_docs?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                <span className="text-[10px] text-slate-400 self-center">evidence:</span>
                {g.evidence_docs.map((d, j) => (
                  <button key={j} onClick={() => onOpenDoc?.(d.doc_id)}
                    className="text-[11px] font-mono bg-ink/60 border border-edge rounded px-1.5 py-0.5 hover:border-teal">
                    {DOCTYPE_ICON[d.doc_type]} {d.doc_id}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
