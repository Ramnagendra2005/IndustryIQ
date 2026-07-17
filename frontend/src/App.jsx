import React, { useEffect, useState } from "react";
import { api } from "./api";
import Chat from "./components/Chat";
import GraphView from "./components/GraphView";
import Documents from "./components/Documents";
import Compliance from "./components/Compliance";
import Ingest from "./components/Ingest";

const TABS = [
  { id: "graph", label: "Knowledge Graph", icon: "🕸️" },
  { id: "docs", label: "Documents", icon: "📚" },
  { id: "compliance", label: "Compliance", icon: "⚖️" },
  { id: "ingest", label: "Ingest", icon: "📥" },
];

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const [status, setStatus] = useState(null);
  const [tab, setTab] = useState(params.get("tab") || "graph");
  const [focus, setFocus] = useState(params.get("focus") || "P-101");
  const [openDoc, setOpenDoc] = useState(null);
  const [field, setField] = useState(params.get("field") === "1");
  const [reloadKey, setReloadKey] = useState(0);
  const [mobilePanel, setMobilePanel] = useState(params.has("tab")); // mobile: show panels vs chat

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

  const graph = status?.graph;

  return (
    <div className="h-full flex flex-col bg-ink">
      {/* header */}
      <header className="shrink-0 border-b border-edge bg-panel/80 backdrop-blur px-4 py-2.5 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-teal grid place-items-center text-ink font-bold">IQ</div>
          <div className="leading-tight">
            <div className="font-semibold text-white">IndustryIQ</div>
            <div className="text-[10px] text-slate-400 -mt-0.5">Unified Asset &amp; Operations Brain</div>
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
            <span className="flex items-center gap-1.5 text-xs bg-panel2 border border-edge rounded-full px-2.5 py-1">
              <span className={`w-2 h-2 rounded-full ${status.llm_mode === "live" ? "bg-emerald-400" : "bg-teal live-dot"}`} />
              <span className="text-slate-300">{status.llm_mode === "live" ? "Live Gemini" : "Offline demo"}</span>
            </span>
          )}
          <div className="flex rounded-full bg-panel2 border border-edge p-0.5 text-xs">
            <button onClick={() => setField(false)} className={`px-2.5 py-1 rounded-full ${!field ? "bg-accent text-ink font-medium" : "text-slate-300"}`}>🖥️ Engineer</button>
            <button onClick={() => setField(true)} className={`px-2.5 py-1 rounded-full ${field ? "bg-accent text-ink font-medium" : "text-slate-300"}`}>📱 Field</button>
          </div>
        </div>
      </header>

      {/* body */}
      <div className={`flex-1 min-h-0 ${field ? "max-w-md mx-auto w-full" : ""}`}>
        {/* desktop: split; mobile: toggle */}
        <div className="h-full flex flex-col md:flex-row">
          {/* chat */}
          <section className={`md:w-[46%] md:max-w-[560px] border-r border-edge min-h-0 flex-1 md:flex-none ${mobilePanel ? "hidden md:flex md:flex-col" : "flex flex-col"}`}>
            <Chat onFocusEntity={focusEntity} onOpenDoc={openDocument} field={field} />
          </section>

          {/* panels */}
          {!field && (
            <section className={`flex-1 min-h-0 flex flex-col ${mobilePanel ? "flex" : "hidden md:flex"}`}>
              <nav className="shrink-0 flex items-center gap-1 px-2 py-1.5 border-b border-edge overflow-x-auto">
                <button className="md:hidden text-slate-400 px-2" onClick={() => setMobilePanel(false)}>← chat</button>
                {TABS.map((t) => (
                  <button key={t.id} onClick={() => setTab(t.id)}
                    className={`px-3 py-1.5 rounded-lg text-sm whitespace-nowrap ${tab === t.id ? "bg-panel2 text-white border border-edge" : "text-slate-400 hover:text-white"}`}>
                    <span className="mr-1">{t.icon}</span>{t.label}
                  </button>
                ))}
              </nav>
              <div className="flex-1 min-h-0">
                {tab === "graph" && <GraphView focus={focus} onFocusEntity={focusEntity} key={"g" + reloadKey} />}
                {tab === "docs" && <Documents openId={openDoc} onClose={() => setOpenDoc(null)} key={"d" + reloadKey} />}
                {tab === "compliance" && <Compliance onOpenDoc={openDocument} />}
                {tab === "ingest" && <Ingest onIngested={() => setReloadKey((k) => k + 1)} />}
              </div>
            </section>
          )}
        </div>
      </div>

      {/* mobile bottom nav */}
      {!field && (
        <nav className="md:hidden shrink-0 border-t border-edge bg-panel flex">
          <button onClick={() => setMobilePanel(false)} className={`flex-1 py-2 text-xs ${!mobilePanel ? "text-accent" : "text-slate-400"}`}>💬 Copilot</button>
          <button onClick={() => { setMobilePanel(true); setTab("graph"); }} className={`flex-1 py-2 text-xs ${mobilePanel ? "text-accent" : "text-slate-400"}`}>🕸️ Explore</button>
        </nav>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <span className="bg-panel2 border border-edge rounded-lg px-2 py-1">
      <span className="font-mono text-white">{value}</span> <span className="text-slate-400">{label}</span>
    </span>
  );
}
