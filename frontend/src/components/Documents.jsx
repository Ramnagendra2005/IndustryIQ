import React, { useEffect, useState } from "react";
import { api } from "../api";
import { DOCTYPE_ICON } from "../lib";

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
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center gap-2 px-3 py-2 border-b border-edge">
          <button onClick={() => { setActive(null); onClose?.(); }} className="text-slate-400 hover:text-white">← back</button>
          <span className="text-sm font-medium truncate">{active.title}</span>
          <span className="ml-auto text-xs font-mono text-teal">{active.id}</span>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex flex-wrap gap-2 mb-3 text-xs">
            <Chip>{DOCTYPE_ICON[active.doc_type]} {active.doc_type}</Chip>
            {active.date && <Chip>📅 {active.date}</Chip>}
            {active.unit && <Chip>🏭 {active.unit}</Chip>}
            {active.is_image && <Chip>🖼️ vision-parsed</Chip>}
          </div>
          <pre className="whitespace-pre-wrap text-sm text-slate-200 font-mono leading-relaxed bg-panel2 border border-edge rounded-xl p-4">
            {active.text}
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-3 space-y-2">
      <div className="text-xs text-slate-400 mb-1">{docs.length} documents across {new Set(docs.map((d) => d.doc_type)).size} formats — one unified brain</div>
      {docs.map((d) => (
        <button
          key={d.id}
          onClick={() => api.document(d.id).then(setActive)}
          className="w-full text-left bg-panel2 border border-edge rounded-lg px-3 py-2.5 hover:border-teal transition"
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">{DOCTYPE_ICON[d.doc_type] || "📄"}</span>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-white truncate">{d.title}</div>
              <div className="text-xs text-slate-400 truncate">{d.preview}</div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-xs font-mono text-teal">{d.id}</div>
              <div className="text-[10px] text-slate-500">{d.date}</div>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

function Chip({ children }) {
  return <span className="bg-panel2 border border-edge rounded-full px-2 py-1">{children}</span>;
}
