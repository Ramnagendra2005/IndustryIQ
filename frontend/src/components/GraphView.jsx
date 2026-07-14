import React, { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { api } from "../api";
import { TYPE_COLORS } from "../lib";

export default function GraphView({ focus, onFocusEntity }) {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [dims, setDims] = useState({ w: 600, h: 500 });
  const wrapRef = useRef(null);
  const fgRef = useRef(null);

  useEffect(() => {
    api.graph(focus || null, 2).then(setData).catch(() => {});
  }, [focus]);

  // spread the layout out so labels are readable
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.d3Force("charge")?.strength(-220);
    fg.d3Force("link")?.distance(70);
    fg.d3ReheatSimulation?.();
  }, [data]);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setDims({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const graph = useMemo(() => {
    return {
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.links.map((l) => ({ ...l })),
    };
  }, [data]);

  const types = useMemo(() => {
    const s = {};
    data.nodes.forEach((n) => (s[n.type] = (s[n.type] || 0) + 1));
    return Object.keys(s).sort();
  }, [data]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 flex-wrap px-3 py-2 border-b border-edge text-xs">
        <span className="text-slate-400">{graph.nodes.length} entities · {graph.links.length} relationships</span>
        <span className="ml-auto flex flex-wrap gap-2">
          {types.map((t) => (
            <span key={t} className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: TYPE_COLORS[t] || "#64748b" }} />
              <span className="text-slate-300">{t}</span>
            </span>
          ))}
        </span>
      </div>
      <div ref={wrapRef} className="flex-1 relative">
        <ForceGraph2D
          ref={fgRef}
          width={dims.w}
          height={dims.h}
          graphData={graph}
          backgroundColor="#0b1220"
          warmupTicks={120}
          cooldownTicks={120}
          d3VelocityDecay={0.3}
          onEngineStop={() => fgRef.current?.zoomToFit(500, 60)}
          nodeRelSize={5}
          linkColor={() => "#2a3a5c"}
          linkWidth={(l) => (l.type === "SIBLING_OF" || l.type === "CONNECTED_TO" ? 2 : 1)}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          onNodeClick={(n) => onFocusEntity?.(n.label)}
          nodeCanvasObject={(node, ctx, scale) => {
            const color = TYPE_COLORS[node.type] || "#64748b";
            const r = (node.highlight ? 7 : 4 + Math.min(node.mentions || 1, 4)) / 1;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            if (node.highlight) {
              ctx.lineWidth = 2;
              ctx.strokeStyle = "#ffffff";
              ctx.stroke();
            }
            const label = node.label;
            const fs = Math.max(10 / scale, 3);
            ctx.font = `${node.highlight ? "bold " : ""}${fs}px ui-monospace, monospace`;
            ctx.fillStyle = node.highlight ? "#ffffff" : "#93a4c3";
            ctx.textAlign = "center";
            ctx.fillText(label, node.x, node.y + r + fs + 1);
          }}
        />
        <div className="absolute bottom-2 left-2 text-[10px] text-slate-500 bg-ink/70 rounded px-2 py-1">
          click a node to focus · drag to explore
        </div>
      </div>
    </div>
  );
}
