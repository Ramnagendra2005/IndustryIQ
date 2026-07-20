import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "./api";
import Chat from "./components/Chat";
import GraphView from "./components/GraphView";
import Documents from "./components/Documents";
import Compliance from "./components/Compliance";
import Trust from "./components/Trust";
import Ingest from "./components/Ingest";
import { CountUp } from "./fx";
import { IconGraph, IconDocs, IconShield, IconUpload, IconChat, IconDesktop, IconField, IconConflict } from "./icons";

const TABS = [
  { id: "graph", label: "Knowledge Graph", Icon: IconGraph },
  { id: "docs", label: "Documents", Icon: IconDocs },
  { id: "compliance", label: "Compliance", Icon: IconShield },
  { id: "trust", label: "Trust", Icon: IconConflict },
  { id: "ingest", label: "Ingest", Icon: IconUpload },
];

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const [status, setStatus] = useState(null);
  const [tab, setTab] = useState(params.get("tab") || "graph");
  const [focus, setFocus] = useState(params.get("focus") || "P-101");
  const [trail, setTrail] = useState([]); // evidence-trail hops from the last answer
  const [openDoc, setOpenDoc] = useState(null);
  const [field, setField] = useState(params.get("field") === "1");
  const [reloadKey, setReloadKey] = useState(0);
  const [mobilePanel, setMobilePanel] = useState(params.has("tab")); // mobile: show panels vs chat
  const [booted, setBooted] = useState(() => sessionStorage.getItem("iq-booted") === "1");

  useEffect(() => { api.status().then(setStatus).catch(() => {}); }, [reloadKey]);

  function openDocument(id) {
    setOpenDoc(id);
    setTab("docs");
    setMobilePanel(true);
  }
  function focusEntity(e) {
    setFocus(e);
    setTab("graph");
  }
  function finishBoot() {
    sessionStorage.setItem("iq-booted", "1");
    setBooted(true);
  }

  const graph = status?.graph;

  if (!booted) return <BootSplash status={status} onDone={finishBoot} />;

  return (
    <div className="h-full flex flex-col">
      <div className="scanline" />
      {/* header */}
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="shrink-0 border-b border-edge glass-strong px-4 py-2.5 flex items-center gap-3 relative z-10"
      >
        <div className="flex items-center gap-2.5">
          <LogoMark />
          <div className="leading-tight">
            <div className="font-bold text-white tracking-tight">
              Industry<span className="text-gradient">IQ</span>
            </div>
            <div className="text-[10px] text-slate-400 -mt-0.5 tracking-wide">UNIFIED ASSET &amp; OPERATIONS BRAIN</div>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-2 ml-4 text-xs">
          {graph && (
            <>
              <Stat label="entities" value={graph.entities} />
              <Stat label="links" value={graph.relationships} />
              <Stat label="docs" value={graph.documents} />
            </>
          )}
        </div>

        <div className="ml-auto flex items-center gap-2">
          {status && (
            <span className="flex items-center gap-1.5 text-[11px] glass rounded-full px-2.5 py-1 font-mono tracking-wide">
              <span className={`w-2 h-2 rounded-full ${status.llm_mode === "live" ? "bg-emerald-400 shadow-glow-teal" : "bg-teal live-dot"}`} />
              <span className="text-slate-300">{status.llm_mode === "live" ? "LIVE — GEMINI" : "SEED — DETERMINISTIC"}</span>
            </span>
          )}
          <div className="flex rounded-full glass p-0.5 text-xs relative">
            {[{ v: false, label: "Engineer", Icon: IconDesktop }, { v: true, label: "Field", Icon: IconField }].map(({ v, label, Icon }) => (
              <button
                key={label}
                onClick={() => setField(v)}
                className={`relative px-2.5 py-1 rounded-full flex items-center gap-1.5 transition-colors ${field === v ? "text-ink font-semibold" : "text-slate-300 hover:text-white"}`}
              >
                {field === v && (
                  <motion.span
                    layoutId="modePill"
                    className="absolute inset-0 rounded-full bg-accent shadow-glow-accent"
                    transition={{ type: "spring", stiffness: 500, damping: 35 }}
                  />
                )}
                <Icon className="w-3.5 h-3.5 relative z-10" />
                <span className="relative z-10 hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </div>
      </motion.header>

      {/* body */}
      <div className={`flex-1 min-h-0 ${field ? "max-w-md mx-auto w-full" : ""}`}>
        {/* desktop: split; mobile: toggle */}
        <div className="h-full flex flex-col md:flex-row">
          {/* chat */}
          <motion.section
            initial={{ opacity: 0, x: -16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.45, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
            className={`md:w-[46%] md:max-w-[560px] border-r border-edge min-h-0 flex-1 md:flex-none ${mobilePanel ? "hidden md:flex md:flex-col" : "flex flex-col"}`}
          >
            <Chat onFocusEntity={focusEntity} onOpenDoc={openDocument} onTrail={setTrail} field={field} />
          </motion.section>

          {/* panels */}
          {!field && (
            <motion.section
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.45, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
              className={`flex-1 min-h-0 flex flex-col ${mobilePanel ? "flex" : "hidden md:flex"}`}
            >
              <nav className="shrink-0 flex items-center gap-1 px-2 py-1.5 border-b border-edge overflow-x-auto">
                <button className="md:hidden text-slate-400 px-2" onClick={() => setMobilePanel(false)}>← chat</button>
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    className={`relative px-3 py-1.5 rounded-lg text-sm whitespace-nowrap flex items-center gap-1.5 transition-colors ${tab === t.id ? "text-white" : "text-slate-400 hover:text-white"}`}
                  >
                    {tab === t.id && (
                      <motion.span
                        layoutId="tabPill"
                        className="absolute inset-0 rounded-lg glass border border-edge2"
                        transition={{ type: "spring", stiffness: 450, damping: 34 }}
                      />
                    )}
                    <t.Icon className={`w-4 h-4 relative z-10 ${tab === t.id ? "text-accent" : ""}`} />
                    <span className="relative z-10">{t.label}</span>
                  </button>
                ))}
              </nav>
              <div className="flex-1 min-h-0 relative">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={tab + reloadKey}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                    className="absolute inset-0"
                  >
                    {tab === "graph" && <GraphView focus={focus} trail={trail} onFocusEntity={focusEntity} key={"g" + reloadKey} />}
                    {tab === "docs" && <Documents openId={openDoc} onClose={() => setOpenDoc(null)} key={"d" + reloadKey} />}
                    {tab === "compliance" && <Compliance onOpenDoc={openDocument} />}
                    {tab === "trust" && <Trust onOpenDoc={openDocument} key={"t" + reloadKey} />}
                    {tab === "ingest" && <Ingest onIngested={() => setReloadKey((k) => k + 1)} />}
                  </motion.div>
                </AnimatePresence>
              </div>
            </motion.section>
          )}
        </div>
      </div>

      {/* mobile bottom nav */}
      {!field && (
        <nav className="md:hidden shrink-0 border-t border-edge glass-strong flex relative z-10">
          <button onClick={() => setMobilePanel(false)} className={`flex-1 py-2 text-xs flex items-center justify-center gap-1.5 ${!mobilePanel ? "text-accent" : "text-slate-400"}`}>
            <IconChat className="w-4 h-4" /> Copilot
          </button>
          <button onClick={() => { setMobilePanel(true); setTab("graph"); }} className={`flex-1 py-2 text-xs flex items-center justify-center gap-1.5 ${mobilePanel ? "text-accent" : "text-slate-400"}`}>
            <IconGraph className="w-4 h-4" /> Explore
          </button>
        </nav>
      )}
    </div>
  );
}

/* Animated logo mark — three glowing nodes, connected, idle float */
function LogoMark() {
  return (
    <div className="w-9 h-9 rounded-xl glass grid place-items-center animate-float shadow-glow-blue">
      <svg viewBox="0 0 32 32" className="w-6 h-6">
        <path d="M10 11L22 9M10 11l6 11M22 9l-6 13" stroke="#3b5379" strokeWidth="1.4" />
        <circle cx="10" cy="11" r="3.2" fill="#38bdf8">
          <animate attributeName="opacity" values="1;0.6;1" dur="3s" repeatCount="indefinite" />
        </circle>
        <circle cx="22" cy="9" r="2.6" fill="#2dd4bf">
          <animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite" />
        </circle>
        <circle cx="16" cy="22" r="3.8" fill="#fbbf24">
          <animate attributeName="opacity" values="1;0.7;1" dur="2.4s" repeatCount="indefinite" />
        </circle>
      </svg>
    </div>
  );
}

/* Boot splash — plays once per session, skippable on click */
function BootSplash({ status, onDone }) {
  const [lines, setLines] = useState(0);
  const graph = status?.graph;
  const bootLines = [
    `▸ knowledge graph … ${graph ? `${graph.entities} entities · ${graph.relationships} links` : "loading"}`,
    `▸ hybrid index … BM25 + semantic ready`,
    `▸ agents … copilot · rca · compliance · trust online`,
  ];

  useEffect(() => {
    if (lines < bootLines.length) {
      const id = setTimeout(() => setLines((l) => l + 1), 380);
      return () => clearTimeout(id);
    }
    const id = setTimeout(onDone, 650);
    return () => clearTimeout(id);
  }, [lines]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <motion.div
      className="h-full grid place-items-center cursor-pointer select-none"
      onClick={onDone}
      exit={{ opacity: 0, scale: 1.04 }}
    >
      <div className="text-center">
        <svg viewBox="0 0 64 64" className="w-24 h-24 mx-auto">
          <path className="draw-stroke" d="M20 22L44 18M20 22l12 22M44 18l-12 26" stroke="#3b5379" strokeWidth="2" fill="none" />
          <circle cx="20" cy="22" r="6" fill="#38bdf8" opacity="0.9" />
          <circle cx="44" cy="18" r="5" fill="#2dd4bf" opacity="0.9" />
          <circle cx="32" cy="44" r="7" fill="#fbbf24" opacity="0.9" />
        </svg>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-4 text-3xl font-bold tracking-tight text-white"
        >
          Industry<span className="text-gradient">IQ</span>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-xs text-slate-400 tracking-[0.25em] mt-1"
        >
          UNIFIED ASSET &amp; OPERATIONS BRAIN
        </motion.div>
        <div className="mt-6 font-mono text-xs text-left space-y-1.5 min-h-[60px] w-72 mx-auto">
          {bootLines.slice(0, lines).map((l, i) => (
            <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} className="text-teal/90">
              {l}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

function Stat({ label, value }) {
  return (
    <span className="glass rounded-lg px-2 py-1">
      <CountUp value={value} className="font-mono text-white" /> <span className="text-slate-400">{label}</span>
    </span>
  );
}
