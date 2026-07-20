import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api";
import { Reveal } from "../fx";
import { DocTypeIcon, DOCTYPE_TINT, IconArrowLeft, IconCalendar, IconFactory, IconImage } from "../icons";

export default function Documents({ openId, onClose }) {
  const [docs, setDocs] = useState([]);
  const [active, setActive] = useState(null);

  useEffect(() => {
    api.documents().then(setDocs).catch(() => {});
  }, []);

  useEffect(() => {
    if (openId) api.document(openId).then(setActive).catch(() => {});
  }, [openId]);

  if (active) {
    const tint = DOCTYPE_TINT[active.doc_type] || "#94a3b8";
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center gap-2.5 px-3 py-2 border-b border-edge shrink-0">
          <button
            onClick={() => { setActive(null); onClose?.(); }}
            className="text-slate-400 hover:text-white flex items-center gap-1 group"
          >
            <IconArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" />
            back
          </button>
          <span
            className="w-6 h-6 rounded-md grid place-items-center shrink-0"
            style={{ background: `${tint}1a`, color: tint }}
          >
            <DocTypeIcon type={active.doc_type} className="w-3.5 h-3.5" />
          </span>
          <span className="text-sm font-medium truncate">{active.title}</span>
          <span className="ml-auto text-xs font-mono text-teal shrink-0">{active.id}</span>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <Reveal>
            <div className="flex flex-wrap gap-2 mb-3 text-xs">
              <Chip><DocTypeIcon type={active.doc_type} className="w-3.5 h-3.5" /> {active.doc_type}</Chip>
              {active.date && <Chip><IconCalendar className="w-3.5 h-3.5" /> {active.date}</Chip>}
              {active.unit && <Chip><IconFactory className="w-3.5 h-3.5" /> {active.unit}</Chip>}
              {active.is_image && <Chip><IconImage className="w-3.5 h-3.5" /> vision-parsed</Chip>}
            </div>
            <div className="glass rounded-xl overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2 border-b border-edge bg-ink/40 text-[11px] font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-teal live-dot" />
                <span className="text-slate-400">SOURCE DOCUMENT</span>
                <span className="ml-auto text-teal">{active.id}</span>
              </div>
              <pre className="whitespace-pre-wrap text-sm text-slate-200 font-mono leading-relaxed p-4">
                {active.text}
              </pre>
            </div>
          </Reveal>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-3 space-y-2">
      <div className="text-[11px] text-slate-400 mb-1 font-mono tracking-wide">
        {docs.length} DOCUMENTS · {new Set(docs.map((d) => d.doc_type)).size} FORMATS — ONE UNIFIED BRAIN
      </div>
      {docs.map((d, i) => {
        const tint = DOCTYPE_TINT[d.doc_type] || "#94a3b8";
        return (
          <motion.button
            key={d.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.04, 0.4) }}
            whileHover={{ y: -2 }}
            onClick={() => api.document(d.id).then(setActive)}
            className="w-full text-left glass rounded-xl px-3 py-2.5 hover:border-teal hover:shadow-glow-teal transition-all"
          >
            <div className="flex items-center gap-2.5">
              <span
                className="w-9 h-9 rounded-lg grid place-items-center shrink-0"
                style={{ background: `${tint}1a`, color: tint }}
              >
                <DocTypeIcon type={d.doc_type} className="w-[18px] h-[18px]" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-white truncate">{d.title}</div>
                <div className="text-xs text-slate-400 truncate">{d.preview}</div>
              </div>
              <div className="text-right shrink-0">
                <div className="text-xs font-mono text-teal">{d.id}</div>
                <div className="text-[10px] font-mono text-slate-500">{d.date}</div>
              </div>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

function Chip({ children }) {
  return <span className="glass rounded-full px-2.5 py-1 flex items-center gap-1.5 text-slate-300">{children}</span>;
}
