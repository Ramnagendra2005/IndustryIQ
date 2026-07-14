import React from "react";

export const TYPE_COLORS = {
  Equipment: "#f5a623",
  ProcessParameter: "#60a5fa",
  FailureMode: "#f87171",
  Person: "#c084fc",
  Regulation: "#2dd4bf",
  Procedure: "#34d399",
  Document: "#94a3b8",
  Date: "#fbbf24",
  Location: "#38bdf8",
  Part: "#fb923c",
  Unknown: "#64748b",
};

export const DOCTYPE_ICON = {
  "P&ID": "🗺️",
  WorkOrder: "🔧",
  InspectionReport: "🔍",
  OEMManual: "📘",
  IncidentReport: "🚨",
  SOP: "📋",
  RegulatoryDocument: "⚖️",
  Spreadsheet: "📊",
  Email: "✉️",
  Other: "📄",
};

/**
 * Ultra-light markdown: **bold**, bullet lines starting with •/-, and
 * [DOC:id] chips (rendered via onCite callback).
 */
export function renderRich(text, onCite) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    const trimmed = line.trim();
    const isBullet = trimmed.startsWith("•") || trimmed.startsWith("- ");
    const content = isBullet ? trimmed.replace(/^[•-]\s*/, "") : line;
    return (
      <div
        key={i}
        className={isBullet ? "flex gap-2 my-1" : trimmed === "" ? "h-2" : "my-1"}
      >
        {isBullet && <span className="text-accent mt-0.5">▸</span>}
        <span>{renderInline(content, onCite)}</span>
      </div>
    );
  });
}

function renderInline(text, onCite) {
  // split on **bold** and [DOC:id]
  const parts = [];
  const regex = /(\*\*[^*]+\*\*|\[DOC:[A-Za-z0-9\-]+\])/g;
  let last = 0;
  let m;
  let k = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(<span key={k++}>{text.slice(last, m.index)}</span>);
    const tok = m[0];
    if (tok.startsWith("**")) {
      parts.push(
        <strong key={k++} className="text-white font-semibold">
          {tok.slice(2, -2)}
        </strong>
      );
    } else {
      const id = tok.slice(5, -1);
      parts.push(
        <button
          key={k++}
          onClick={() => onCite && onCite(id)}
          className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded bg-teal/15 text-teal text-xs font-mono hover:bg-teal/30 align-baseline"
        >
          {id}
        </button>
      );
    }
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(<span key={k++}>{text.slice(last)}</span>);
  return parts;
}

export function confColor(c) {
  if (c >= 0.75) return "#34d399";
  if (c >= 0.5) return "#f5a623";
  return "#f87171";
}
