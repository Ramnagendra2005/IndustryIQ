import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../api";
import { IconFactory, IconGraph, IconBrain, IconShield, IconBolt } from "../icons";

const DEMO = { email: "demo@industryiq.app", password: "demo123" };

// Left-hero selling points. Each maps to a real capability of the app so the
// landing page tells the truth as well as looking good.
const FEATURES = [
  { icon: IconGraph, color: "#38bdf8", title: "Living knowledge graph",
    desc: "Every asset, failure and document, wired into one queryable brain." },
  { icon: IconBrain, color: "#2dd4bf", title: "Cross-document copilot",
    desc: "Connects dots across work orders, inspections & incidents no single engineer sees." },
  { icon: IconShield, color: "#f5a623", title: "Compliance & trust, built in",
    desc: "Every answer is cited, scored and traced back to the source record." },
  { icon: IconBolt, color: "#c084fc", title: "Live document ingestion",
    desc: "Drop a P&ID, spreadsheet or email — it's extracted and linked in seconds." },
];

// Rotating word in the hero subtitle for a bit of motion.
const ROTATING = ["work orders", "inspection reports", "P&IDs", "incident history", "OEM manuals"];

// ------------------------------------------------------------------ //
// Interactive knowledge-graph constellation — the hero centrepiece.
// Nodes drift and connect like the app's own graph, pulse softly, and
// gently repel from the cursor. Canvas so it stays 60fps with zero DOM.
// ------------------------------------------------------------------ //
function Constellation() {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const COLORS = ["#38bdf8", "#2dd4bf", "#f5a623", "#fbbf24", "#c084fc"];
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    let w = 0, h = 0, raf = 0, nodes = [];
    const mouse = { x: -9999, y: -9999 };

    function seed() {
      const rect = canvas.getBoundingClientRect();
      w = rect.width; h = rect.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.max(24, Math.min(70, Math.floor((w * h) / 15000)));
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.28, vy: (Math.random() - 0.5) * 0.28,
        r: 1.4 + Math.random() * 2.4,
        c: COLORS[Math.floor(Math.random() * COLORS.length)],
        ph: Math.random() * Math.PI * 2,
      }));
    }

    function draw(t) {
      ctx.clearRect(0, 0, w, h);
      const D = 132;
      for (const n of nodes) {
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;
        const dx = n.x - mouse.x, dy = n.y - mouse.y, dist = Math.hypot(dx, dy) || 1;
        if (dist < 130) { const f = ((130 - dist) / 130) * 0.9; n.x += (dx / dist) * f; n.y += (dy / dist) * f; }
      }
      // edges — brighter where nodes cluster (the "connect the dots" story)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          const dx = a.x - b.x, dy = a.y - b.y, dist = Math.hypot(dx, dy);
          if (dist < D) {
            ctx.strokeStyle = `rgba(56,189,248,${(1 - dist / D) * 0.22})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          }
        }
      }
      // nodes with a soft colour-matched glow
      for (const n of nodes) {
        const pulse = reduce ? 1 : 0.55 + 0.45 * Math.sin(t / 900 + n.ph);
        const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 6);
        g.addColorStop(0, n.c + "aa"); g.addColorStop(1, n.c + "00");
        ctx.globalAlpha = 0.5 * pulse; ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r * 6, 0, 7); ctx.fill();
        ctx.globalAlpha = pulse; ctx.fillStyle = n.c;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, 7); ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (!reduce) raf = requestAnimationFrame(draw);
    }

    seed();
    raf = requestAnimationFrame(draw);
    const ro = new ResizeObserver(() => { seed(); if (reduce) draw(0); });
    ro.observe(canvas);
    const onMove = (e) => { const r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; };
    const onLeave = () => { mouse.x = -9999; mouse.y = -9999; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseout", onLeave);
    return () => {
      cancelAnimationFrame(raf); ro.disconnect();
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseout", onLeave);
    };
  }, []);
  return <canvas ref={ref} className="absolute inset-0 w-full h-full" style={{ pointerEvents: "none" }} />;
}

// ------------------------------------------------------------------ //
// Login + Register. Two register modes — "create" founds a new industry
// (its own empty graph), "join" enters an existing one via invite code.
// ------------------------------------------------------------------ //
export default function Auth({ onAuthed }) {
  const [tab, setTab] = useState("login"); // login | register
  const [joinMode, setJoinMode] = useState("create"); // create | join
  const [form, setForm] = useState({
    email: "", name: "", password: "", industry_name: "", join_code: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [newCode, setNewCode] = useState(null);
  const [word, setWord] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setWord((w) => (w + 1) % ROTATING.length), 2200);
    return () => clearInterval(id);
  }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      if (tab === "login") {
        const user = await api.login(form.email, form.password);
        onAuthed(user);
      } else {
        const payload = {
          email: form.email, name: form.name, password: form.password,
          ...(joinMode === "create"
            ? { industry_name: form.industry_name }
            : { join_code: form.join_code }),
        };
        const user = await api.register(payload);
        if (joinMode === "create") {
          setNewCode(user.join_code);
          setTimeout(() => onAuthed(user), 2600);
        } else {
          onAuthed(user);
        }
      }
    } catch (e2) {
      setErr(e2.message || "Something went wrong.");
      setBusy(false);
    }
  }

  async function useDemo() {
    setErr("");
    setBusy(true);
    try {
      onAuthed(await api.login(DEMO.email, DEMO.password));
    } catch (e2) {
      setErr(e2.message);
      setBusy(false);
    }
  }

  if (newCode) return <CodeReveal code={newCode} name={form.industry_name} />;

  const ease = [0.22, 1, 0.36, 1];

  return (
    <div className="h-full w-full overflow-y-auto relative bg-ink">
      {/* animated backdrop */}
      <Constellation />
      <div className="scanline" />
      {/* aurora blobs — slow drifting colour washes */}
      <motion.div
        aria-hidden className="pointer-events-none absolute -top-40 -left-32 w-[42rem] h-[42rem] rounded-full blur-3xl"
        style={{ background: "radial-gradient(circle, rgba(56,189,248,0.16), transparent 60%)" }}
        animate={{ x: [0, 40, 0], y: [0, 30, 0] }} transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden className="pointer-events-none absolute top-1/3 -right-40 w-[40rem] h-[40rem] rounded-full blur-3xl"
        style={{ background: "radial-gradient(circle, rgba(245,166,35,0.13), transparent 60%)" }}
        animate={{ x: [0, -50, 0], y: [0, 40, 0] }} transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden className="pointer-events-none absolute -bottom-40 left-1/4 w-[38rem] h-[38rem] rounded-full blur-3xl"
        style={{ background: "radial-gradient(circle, rgba(45,212,191,0.12), transparent 60%)" }}
        animate={{ x: [0, 30, 0], y: [0, -30, 0] }} transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* content */}
      <div className="relative z-10 min-h-full w-full max-w-6xl mx-auto grid lg:grid-cols-2 gap-10 lg:gap-14 items-center px-6 py-10 lg:py-0">
        {/* ---------------- LEFT: hero ---------------- */}
        <motion.div
          initial="hidden" animate="show"
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } } }}
          className="order-2 lg:order-1"
        >
          {/* badge */}
          <motion.div
            variants={{ hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.5, ease }}
            className="inline-flex items-center gap-2 glass rounded-full px-3 py-1 text-[11px] font-mono tracking-widest text-slate-300 mb-6"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-teal live-dot" style={{ animationPlayState: "running" }} />
            AI-NATIVE · KNOWLEDGE GRAPH
          </motion.div>

          {/* title */}
          <motion.h1
            variants={{ hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.6, ease }}
            className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[0.95]"
          >
            Industry
            <span className="text-gradient" style={{ animationPlayState: "running" }}>IQ</span>
          </motion.h1>

          {/* rotating subtitle */}
          <motion.p
            variants={{ hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.6, ease }}
            className="mt-5 text-lg text-slate-300 max-w-md leading-relaxed"
          >
            The unified asset &amp; operations brain that connects the dots across your{" "}
            <span className="relative inline-grid align-baseline">
              <AnimatePresence mode="wait">
                <motion.span
                  key={word}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.35, ease }}
                  className="font-semibold text-accent whitespace-nowrap"
                >
                  {ROTATING[word]}
                </motion.span>
              </AnimatePresence>
            </span>
            .
          </motion.p>

          {/* feature list */}
          <div className="mt-9 space-y-2.5 max-w-md">
            {FEATURES.map((f) => (
              <motion.div
                key={f.title}
                variants={{ hidden: { opacity: 0, x: -16 }, show: { opacity: 1, x: 0 } }}
                transition={{ duration: 0.5, ease }}
                className="group flex items-start gap-3.5 rounded-xl border border-transparent p-2.5 -mx-2.5 cursor-default transition-all duration-300 hover:border-edge2 hover:bg-white/[0.03] hover:translate-x-1"
              >
                <span
                  className="relative mt-0.5 w-10 h-10 rounded-xl glass grid place-items-center shrink-0 transition-all duration-300 group-hover:scale-110"
                  style={{ color: f.color }}
                >
                  <f.icon className="w-5 h-5 transition-transform duration-300 group-hover:rotate-[-6deg]" />
                  <span
                    className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ boxShadow: `0 0 20px -2px ${f.color}` }}
                  />
                </span>
                <div>
                  <div className="text-sm font-semibold text-white group-hover:text-white">{f.title}</div>
                  <div className="text-[13px] text-slate-400 leading-snug">{f.desc}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* ---------------- RIGHT: auth card ---------------- */}
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, ease, delay: 0.15 }}
          className="order-1 lg:order-2 w-full max-w-md mx-auto lg:ml-auto"
        >
          <div className="relative">
            {/* gradient ring glow behind the card */}
            <div
              aria-hidden
              className="absolute -inset-px rounded-2xl opacity-60 blur-sm"
              style={{ background: "linear-gradient(140deg, rgba(245,166,35,0.4), rgba(56,189,248,0.25), rgba(45,212,191,0.3))" }}
            />
            <div className="relative glass-strong rounded-2xl border border-edge p-7">
              {/* brand */}
              <div className="flex items-center gap-2.5 mb-6">
                <div className="w-10 h-10 rounded-xl glass grid place-items-center shadow-glow-blue">
                  <IconFactory className="w-5 h-5 text-accent" />
                </div>
                <div className="leading-tight">
                  <div className="font-bold text-white text-lg tracking-tight">
                    Industry<span className="text-gradient" style={{ animationPlayState: "running" }}>IQ</span>
                  </div>
                  <div className="text-[10px] text-slate-400 tracking-wide">
                    UNIFIED ASSET &amp; OPERATIONS BRAIN
                  </div>
                </div>
              </div>

              {/* tabs */}
              <div className="flex rounded-xl glass p-0.5 text-sm mb-5 relative">
                {[{ id: "login", label: "Sign in" }, { id: "register", label: "Create account" }].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => { setTab(t.id); setErr(""); }}
                    className={`relative flex-1 py-2 rounded-lg transition-colors ${tab === t.id ? "text-ink font-semibold" : "text-slate-300 hover:text-white"}`}
                  >
                    {tab === t.id && (
                      <motion.span layoutId="authTab" className="absolute inset-0 rounded-lg bg-accent shadow-glow-accent"
                        transition={{ type: "spring", stiffness: 500, damping: 35 }} />
                    )}
                    <span className="relative z-10">{t.label}</span>
                  </button>
                ))}
              </div>

              <form onSubmit={submit} className="space-y-3">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={tab}
                    initial={{ opacity: 0, x: tab === "login" ? -12 : 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: tab === "login" ? 12 : -12 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-3"
                  >
                    {tab === "register" && (
                      <Field label="Your name" value={form.name} onChange={set("name")} placeholder="Alex Rivera" autoFocus />
                    )}
                    <Field label="Work email" type="email" value={form.email} onChange={set("email")} placeholder="you@company.com" autoFocus={tab === "login"} />
                    <Field label="Password" type="password" value={form.password} onChange={set("password")} placeholder="••••••••" />

                    {tab === "register" && (
                      <div className="pt-1">
                        <div className="flex rounded-lg glass p-0.5 text-xs mb-3 relative">
                          {[{ id: "create", label: "New industry" }, { id: "join", label: "Join with code" }].map((m) => (
                            <button
                              type="button" key={m.id}
                              onClick={() => setJoinMode(m.id)}
                              className={`relative flex-1 py-1.5 rounded-md transition-colors ${joinMode === m.id ? "text-ink font-semibold" : "text-slate-300 hover:text-white"}`}
                            >
                              {joinMode === m.id && (
                                <motion.span layoutId="joinMode" className="absolute inset-0 rounded-md bg-teal"
                                  transition={{ type: "spring", stiffness: 500, damping: 35 }} />
                              )}
                              <span className="relative z-10">{m.label}</span>
                            </button>
                          ))}
                        </div>
                        {joinMode === "create" ? (
                          <Field label="Industry / company name" value={form.industry_name} onChange={set("industry_name")} placeholder="Acme Chemicals" />
                        ) : (
                          <Field label="Invite code" value={form.join_code} onChange={set("join_code")} placeholder="ACME-7F3K" mono />
                        )}
                        <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                          {joinMode === "create"
                            ? "You'll get a fresh, private knowledge graph. Upload your first document to get started — we'll walk you through it."
                            : "Ask your industry admin for the invite code shown when they created the workspace."}
                        </p>
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>

                {err && (
                  <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                    className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
                    {err}
                  </motion.div>
                )}

                <button
                  type="submit" disabled={busy}
                  className="group relative w-full py-2.5 rounded-xl bg-accent text-ink font-semibold shadow-glow-accent overflow-hidden transition hover:brightness-110 hover:shadow-[0_0_28px_-2px_rgba(245,166,35,0.6)] disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {/* sheen sweep on hover */}
                  <span className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out bg-gradient-to-r from-transparent via-white/40 to-transparent" />
                  <span className="relative">{busy ? "Working…" : tab === "login" ? "Sign in" : "Create account"}</span>
                </button>
              </form>

              {/* demo — instant access */}
              <div className="mt-5 pt-4 border-t border-edge">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-[11px] text-slate-400 leading-relaxed">
                    <span className="text-slate-300 font-medium">Just exploring?</span> Try the demo refinery —
                    <span className="font-mono text-teal"> {DEMO.email}</span> /
                    <span className="font-mono text-teal"> {DEMO.password}</span>
                  </div>
                  <button
                    onClick={useDemo} disabled={busy}
                    className="shrink-0 text-xs px-3 py-1.5 rounded-lg glass border border-edge2 text-white transition hover:border-accent hover:shadow-glow-accent disabled:opacity-60"
                  >
                    Enter demo
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function Field({ label, mono, ...props }) {
  return (
    <label className="block">
      <span className="text-[11px] text-slate-400 mb-1 block">{label}</span>
      <input
        {...props}
        required
        className={`w-full glass rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 border border-edge focus:border-accent focus:outline-none focus:shadow-glow-accent transition ${mono ? "font-mono tracking-wider uppercase" : ""}`}
      />
    </label>
  );
}

// Shown once after founding a new industry: the invite code teammates use to join.
function CodeReveal({ code, name }) {
  return (
    <div className="h-full grid place-items-center p-4 relative overflow-hidden bg-ink">
      <Constellation />
      <motion.div
        initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }}
        className="relative z-10 text-center max-w-md glass-strong rounded-2xl border border-edge p-8"
      >
        <motion.div
          initial={{ rotate: -8, scale: 0.8 }} animate={{ rotate: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 18 }}
          className="w-12 h-12 rounded-xl glass grid place-items-center shadow-glow-blue mx-auto mb-4"
        >
          <IconFactory className="w-6 h-6 text-accent" />
        </motion.div>
        <div className="text-white font-semibold text-lg">Welcome, {name}</div>
        <p className="text-sm text-slate-400 mt-1">Your workspace is ready. Share this invite code so your team can join:</p>
        <motion.div
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="mt-4 font-mono text-2xl tracking-[0.3em] text-teal bg-teal/10 border border-teal/20 rounded-xl py-3"
        >
          {code}
        </motion.div>
        <p className="text-[11px] text-slate-500 mt-4">Taking you to your workspace…</p>
      </motion.div>
    </div>
  );
}
