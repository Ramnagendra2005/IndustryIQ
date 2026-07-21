import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../api";
import { Reveal } from "../fx";
import {
  DocTypeIcon, DOCTYPE_TINT, IconAlert, IconWrench, IconMicroscope, IconClock,
  IconRegulation, IconSOP, IconArrowLeft, IconConflict, IconChat, IconBolt,
} from "../icons";

/* health → color + label, shared with the P&ID symbol colouring */
export const HEALTH = {
  alert: { color: "#f87171", label: "AT RISK", ring: "shadow-glow-danger" },
  watch: { color: "#f5a623", label: "WATCH", ring: "shadow-glow-accent" },
  ok: { color: "#34d399", label: "HEALTHY", ring: "shadow-glow-teal" },
};

const FRESH_COLOR = (f) => (f >= 0.6 ? "#34d399" : f >= 0.3 ? "#f5a623" : "#f87171");

/**
 * Full entity dossier — the profile behind a clicked P&ID symbol.
 * Slides in from the right. `name` is the graph entity/tag; `onClose` dismisses;
 * `onOpenDoc` opens a source document; `onAsk` routes a question to the copilot;
 * `onFocusEntity` jumps a connected tag into a new dossier.
 */
export default function Dossier({ name, onClose, onOpenDoc, onAsk, onFocusEntity }) {
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!name) return;
    setLoading(true);
    setErr(null);
    setD(null);
    api.entity(name)
      .then((res) => { setD(res); setLoading(false); })
      .catch((e) => { setErr(e.message); setLoading(false); });
  }, [name]);

  const h = HEALTH[d?.health] || HEALTH.ok;

  return (
    <AnimatePresence>
      {name && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm z-20"
          />
          <motion.aside
            initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 380, damping: 38 }}
            className="absolute top-0 right-0 bottom-0 w-full sm:w-[440px] max-w-full glass-strong border-l border-edge z-30 flex flex-col"
          >
            {/* header */}
            <div className="shrink-0 px-4 py-3 border-b border-edge flex items-start gap-3">
              <button onClick={onClose} className="text-slate-400 hover:text-white mt-0.5 shrink-0">
                <IconArrowLeft className="w-5 h-5" />
              </button>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-lg font-bold text-white truncate">
                    {loading ? name : d?.label || name}
                  </span>
                  {d && (
                    <span
                      className="text-[10px] font-bold font-mono tracking-widest px-2 py-0.5 rounded-full flex items-center gap-1"
                      style={{ color: h.color, border: `1px solid ${h.color}55`, background: `${h.color}12` }}
                    >
                      {d.health === "alert" && <IconAlert className="w-3 h-3" />}
                      {h.label}
                    </span>
                  )}
                </div>
                {d && (
                  <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5 flex-wrap">
                    <span className="text-teal">{d.type}</span>
                    {d.unit && <><span className="text-slate-600">·</span><span>{d.unit}</span></>}
                    {d.history?.length > 0 && (
                      <><span className="text-slate-600">·</span><span>{d.history.length} records</span></>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3.5">
              {loading && (
                <div className="space-y-3">
                  <div className="skeleton h-16" /><div className="skeleton h-24" />
                  <div className="skeleton h-24" /><div className="skeleton h-32" />
                </div>
              )}
              {err && <div className="text-sm text-red-300">⚠️ {err}</div>}
              {d && !d.found && (
                <div className="text-sm text-slate-400">
                  <b className="text-white font-mono">{name}</b> isn't in the knowledge graph yet.
                </div>
              )}

              {d && d.found && (
                <>
                  {d.description && (
                    <Reveal className="text-sm text-slate-200 leading-relaxed">{d.description}</Reveal>
                  )}

                  {/* ask-the-copilot actions */}
                  <Reveal delay={0.04} className="flex gap-2">
                    <button
                      onClick={() => onAsk?.(`Why is ${d.label} at risk? What is going on with it?`, "rca")}
                      className="flex-1 flex items-center justify-center gap-1.5 text-sm px-3 py-2 rounded-xl bg-accent text-ink font-semibold shadow-glow-accent hover:brightness-110 transition"
                    >
                      <IconMicroscope className="w-4 h-4" /> Run RCA
                    </button>
                    <button
                      onClick={() => onAsk?.(`What is the maintenance history and current status of ${d.label}?`, "copilot")}
                      className="flex-1 flex items-center justify-center gap-1.5 text-sm px-3 py-2 rounded-xl glass hover:border-edge2 hover:shadow-glow-teal transition"
                    >
                      <IconChat className="w-4 h-4 text-teal" /> Ask copilot
                    </button>
                  </Reveal>

                  {/* open risks first — this is why the symbol glowed */}
                  {d.conflicts?.length > 0 && (
                    <Section title="TRUST CONFLICTS" icon={IconConflict} tint="#f87171" delay={0.06}>
                      {d.conflicts.map((c) => (
                        <div key={c.id} className="rounded-lg glass p-2.5 border-l-2" style={{ borderColor: SEV_COLOR(c.severity) }}>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-white">{c.title}</span>
                            <span className="ml-auto text-[9px] font-mono tracking-widest" style={{ color: SEV_COLOR(c.severity) }}>
                              {c.severity.toUpperCase()}
                            </span>
                          </div>
                          <div className="text-xs text-slate-300 mt-1">{c.detail}</div>
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {c.doc_ids.map((id) => <DocChip key={id} id={id} onOpenDoc={onOpenDoc} />)}
                          </div>
                        </div>
                      ))}
                    </Section>
                  )}

                  {d.compliance_gaps?.length > 0 && (
                    <Section title="COMPLIANCE GAPS" icon={IconRegulation} tint="#f5a623" delay={0.08}>
                      {d.compliance_gaps.map((g, i) => (
                        <div key={i} className="rounded-lg glass p-2.5 border-l-2" style={{ borderColor: g.status === "gap" ? "#f87171" : "#f5a623" }}>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-white">{g.regulation}</span>
                            <span className="ml-auto text-[9px] font-mono tracking-widest" style={{ color: g.status === "gap" ? "#f87171" : "#f5a623" }}>
                              {g.status.toUpperCase().replace("_", " ")}
                            </span>
                          </div>
                          <div className="text-xs text-slate-400 mt-0.5">{g.requirement}</div>
                          <div className="text-xs text-slate-200 mt-1">{g.finding}</div>
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {g.evidence_docs.map((c) => <DocChip key={c.doc_id} id={c.doc_id} onOpenDoc={onOpenDoc} />)}
                          </div>
                        </div>
                      ))}
                    </Section>
                  )}

                  {/* process connections */}
                  {(d.connections_up.length > 0 || d.connections_down.length > 0 || d.siblings.length > 0) && (
                    <Section title="PROCESS CONNECTIONS" icon={IconBolt} tint="#38bdf8" delay={0.1}>
                      <LinkFlow up={d.connections_up} down={d.connections_down} self={d.label} onFocusEntity={onFocusEntity} />
                      {d.siblings.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          <span className="text-[10px] text-slate-500 font-mono self-center">SIBLINGS</span>
                          {d.siblings.map((l) => <TagChip key={l.name} link={l} onFocusEntity={onFocusEntity} />)}
                        </div>
                      )}
                    </Section>
                  )}

                  {d.failure_modes.length > 0 && (
                    <Section title="FAILURE MODES" icon={IconAlert} tint="#f87171" delay={0.12}>
                      <div className="flex flex-wrap gap-1.5">
                        {d.failure_modes.map((l) => (
                          <span key={l.name} className="text-xs rounded-lg px-2 py-1 bg-red-500/10 text-red-200 border border-red-500/25" title={l.evidence}>
                            {l.label}
                          </span>
                        ))}
                      </div>
                    </Section>
                  )}

                  {(d.parts.length > 0 || d.parameters.length > 0) && (
                    <Section title="PARTS & PARAMETERS" icon={IconWrench} tint="#c084fc" delay={0.14}>
                      <div className="flex flex-wrap gap-1.5">
                        {d.parameters.map((l) => (
                          <span key={l.name} className="text-xs rounded-lg px-2 py-1 bg-teal/10 text-teal border border-teal/25" title={l.evidence}>
                            {l.label}
                          </span>
                        ))}
                        {d.parts.map((l) => (
                          <span key={l.name} className="text-xs rounded-lg px-2 py-1 glass" title={l.evidence}>
                            {l.label}
                          </span>
                        ))}
                      </div>
                    </Section>
                  )}

                  {/* governing procedures + regulations */}
                  {(d.procedures.length > 0 || d.regulations.length > 0) && (
                    <Section title="PROCEDURES & REGULATIONS" icon={IconSOP} tint="#34d399" delay={0.16}>
                      <div className="flex flex-wrap gap-1.5">
                        {d.procedures.map((l) => <TagChip key={l.name} link={l} onFocusEntity={onFocusEntity} />)}
                        {d.regulations.map((l) => <TagChip key={l.name} link={l} onFocusEntity={onFocusEntity} />)}
                      </div>
                    </Section>
                  )}

                  {d.people.length > 0 && (
                    <Section title="MAINTAINED BY" delay={0.18}>
                      <div className="flex flex-wrap gap-1.5">
                        {d.people.map((l) => (
                          <span key={l.name} className="text-xs rounded-lg px-2 py-1 glass">{l.label}</span>
                        ))}
                      </div>
                    </Section>
                  )}

                  {/* maintenance & document history — the timeline */}
                  {d.history.length > 0 && (
                    <Section title="MAINTENANCE & DOCUMENT HISTORY" icon={IconClock} tint="#60a5fa" delay={0.2}>
                      <div className="relative pl-4">
                        <span className="absolute left-[5px] top-1 bottom-1 w-px bg-edge" />
                        {d.history.map((doc, i) => (
                          <motion.button
                            key={doc.doc_id + i}
                            initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.02 * i }}
                            onClick={() => onOpenDoc?.(doc.doc_id)}
                            className="relative block w-full text-left pb-3 last:pb-0 group"
                          >
                            <span
                              className="absolute -left-4 top-1.5 w-2.5 h-2.5 rounded-full border-2 border-panel2"
                              style={{ background: FRESH_COLOR(doc.freshness) }}
                            />
                            <div className="flex items-center gap-2">
                              <span
                                className="w-6 h-6 rounded-md grid place-items-center shrink-0"
                                style={{ background: `${DOCTYPE_TINT[doc.doc_type] || "#94a3b8"}1a`, color: DOCTYPE_TINT[doc.doc_type] || "#94a3b8" }}
                              >
                                <DocTypeIcon type={doc.doc_type} className="w-3.5 h-3.5" />
                              </span>
                              <span className="text-sm text-white truncate group-hover:text-teal transition-colors">{doc.title}</span>
                              <span className="ml-auto text-[10px] font-mono text-slate-500 shrink-0">{doc.date || "—"}</span>
                            </div>
                            <div className="text-xs text-slate-400 mt-0.5 line-clamp-2 pl-8">{doc.snippet}</div>
                            {doc.status !== "fresh" && (
                              <span className="ml-8 text-[9px] font-mono tracking-wide" style={{ color: FRESH_COLOR(doc.freshness) }}>
                                {doc.status.toUpperCase()} · {Math.round(doc.freshness * 100)}% fresh
                              </span>
                            )}
                          </motion.button>
                        ))}
                      </div>
                    </Section>
                  )}
                </>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

const SEV_COLOR = (s) => (s === "high" ? "#f87171" : s === "medium" ? "#f5a623" : "#60a5fa");

function Section({ title, icon: Icon, tint = "#94a3b8", delay = 0, children }) {
  return (
    <Reveal delay={delay}>
      <div className="text-[10px] font-mono tracking-widest mb-1.5 flex items-center gap-1.5" style={{ color: tint }}>
        {Icon && <Icon className="w-3.5 h-3.5" />} {title}
      </div>
      <div className="space-y-1.5">{children}</div>
    </Reveal>
  );
}

function DocChip({ id, onOpenDoc }) {
  return (
    <button
      onClick={() => onOpenDoc?.(id)}
      className="text-[10px] font-mono bg-ink/60 border border-edge rounded px-1.5 py-0.5 hover:border-teal hover:text-teal transition-colors"
    >
      {id}
    </button>
  );
}

function TagChip({ link, onFocusEntity }) {
  return (
    <button
      onClick={() => onFocusEntity?.(link.name)}
      title={link.evidence}
      className="text-xs font-mono glass rounded-lg px-2 py-1 hover:border-teal hover:text-teal transition-colors"
    >
      {link.label}
    </button>
  );
}

/* upstream → this → downstream, as a compact flow */
function LinkFlow({ up, down, self, onFocusEntity }) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap text-xs">
      {up.map((l) => (
        <React.Fragment key={"u" + l.name}>
          <button onClick={() => onFocusEntity?.(l.name)} className="font-mono glass rounded-lg px-2 py-1 hover:text-teal hover:border-teal transition-colors" title={l.evidence}>
            {l.label}
          </button>
          <span className="text-teal">→</span>
        </React.Fragment>
      ))}
      <span className="font-mono font-bold text-white bg-accent/15 border border-accent/40 rounded-lg px-2 py-1">{self}</span>
      {down.map((l) => (
        <React.Fragment key={"d" + l.name}>
          <span className="text-accent">→</span>
          <button onClick={() => onFocusEntity?.(l.name)} className="font-mono glass rounded-lg px-2 py-1 hover:text-teal hover:border-teal transition-colors" title={l.evidence}>
            {l.label}
          </button>
        </React.Fragment>
      ))}
    </div>
  );
}
