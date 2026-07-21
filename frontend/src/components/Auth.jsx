import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../api";
import { IconFactory, IconArrowLeft } from "../icons";

const DEMO = { email: "demo@industryiq.app", password: "demo123" };

// Login + Register for IndustryIQ. Two modes for register — "create" founds a
// new industry (with its own empty knowledge graph), "join" enters an existing
// one via its invite code. Demo credentials are shown so anyone can explore.
export default function Auth({ onAuthed }) {
  const [tab, setTab] = useState("login"); // login | register
  const [joinMode, setJoinMode] = useState("create"); // create | join
  const [form, setForm] = useState({
    email: "", name: "", password: "", industry_name: "", join_code: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [newCode, setNewCode] = useState(null); // invite code to show after "create"

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
          setNewCode(user.join_code); // show the code, then continue
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

  return (
    <div className="h-full grid place-items-center p-4 relative overflow-hidden">
      <div className="scanline" />
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md glass-strong rounded-2xl border border-edge p-7 relative z-10"
      >
        {/* brand */}
        <div className="flex items-center gap-2.5 mb-6">
          <div className="w-10 h-10 rounded-xl glass grid place-items-center shadow-glow-blue">
            <IconFactory className="w-5 h-5 text-accent" />
          </div>
          <div className="leading-tight">
            <div className="font-bold text-white text-lg tracking-tight">
              Industry<span className="text-gradient">IQ</span>
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
            className="w-full py-2.5 rounded-xl bg-accent text-ink font-semibold shadow-glow-accent hover:brightness-110 transition disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {busy ? "Working…" : tab === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        {/* demo credentials — instant access */}
        <div className="mt-5 pt-4 border-t border-edge">
          <div className="flex items-center justify-between gap-3">
            <div className="text-[11px] text-slate-400 leading-relaxed">
              <span className="text-slate-300 font-medium">Just exploring?</span> Try the demo refinery —
              <span className="font-mono text-teal"> {DEMO.email}</span> /
              <span className="font-mono text-teal"> {DEMO.password}</span>
            </div>
            <button
              onClick={useDemo} disabled={busy}
              className="shrink-0 text-xs px-3 py-1.5 rounded-lg glass border border-edge2 text-white hover:border-accent transition disabled:opacity-60"
            >
              Enter demo
            </button>
          </div>
        </div>
      </motion.div>
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
        className={`w-full glass rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 border border-edge focus:border-accent focus:outline-none transition ${mono ? "font-mono tracking-wider uppercase" : ""}`}
      />
    </label>
  );
}

// Shown once after founding a new industry: the invite code teammates use to join.
function CodeReveal({ code, name }) {
  return (
    <div className="h-full grid place-items-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }}
        className="text-center max-w-md glass-strong rounded-2xl border border-edge p-8"
      >
        <div className="w-12 h-12 rounded-xl glass grid place-items-center shadow-glow-blue mx-auto mb-4">
          <IconFactory className="w-6 h-6 text-accent" />
        </div>
        <div className="text-white font-semibold text-lg">Welcome, {name}</div>
        <p className="text-sm text-slate-400 mt-1">Your workspace is ready. Share this invite code so your team can join:</p>
        <div className="mt-4 font-mono text-2xl tracking-[0.3em] text-teal bg-teal/10 border border-teal/20 rounded-xl py-3">
          {code}
        </div>
        <p className="text-[11px] text-slate-500 mt-4">Taking you to your workspace…</p>
      </motion.div>
    </div>
  );
}
