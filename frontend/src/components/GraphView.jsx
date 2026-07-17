import React, { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { api } from "../api";
import { TYPE_COLORS } from "../lib";

export default function GraphView({ focus, trail = [], onFocusEntity }) {
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

  // Evidence trail from the last answer: hops are (label, relation, label);
  // resolve to node ids so trail edges/nodes can be styled distinctly.
  const { trailEdges, trailNodes } = useMemo(() => {
    const byLabel = new Map(data.nodes.map((n) => [n.label, n.id]));
    const edges = new Set();
    const nodes = new Set();
    for (const h of trail) {
      const s = byLabel.get(h.source);
      const t = byLabel.get(h.target);
      if (!s || !t) continue;
      edges.add(`${s}|${t}`);
      edges.add(`${t}|${s}`); // graph is drawn undirected enough to match both ways
      nodes.add(s);
      nodes.add(t);
    }
    return { trailEdges: edges, trailNodes: nodes };
  }, [data, trail]);

  const linkId = (e) => (typeof e === "object" ? e.id : e);
  const onTrailLink = (l) => trailEdges.has(`${linkId(l.source)}|${linkId(l.target)}`);

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
        {trailNodes.size > 0 && (
          <span className="flex items-center gap-1.5 bg-amber-400/10 border border-amber-400/40 text-amber-300 rounded-full px-2 py-0.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 live-dot" />
            evidence trail from last answer
          </span>
        )}
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
          linkColor={(l) => (onTrailLink(l) ? "#fbbf24" : "#2a3a5c")}
          linkWidth={(l) => (onTrailLink(l) ? 3 : l.type === "SIBLING_OF" || l.type === "CONNECTED_TO" ? 2 : 1)}
          linkDirectionalParticles={(l) => (onTrailLink(l) ? 3 : 0)}
          linkDirectionalParticleWidth={3}
          linkDirectionalParticleColor={() => "#fbbf24"}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          onNodeClick={(n) => onFocusEntity?.(n.label)}
          nodeCanvasObject={(node, ctx, scale) => {
            const color = TYPE_COLORS[node.type] || "#64748b";
            const onTrail = trailNodes.has(node.id);
            const r = (node.highlight || onTrail ? 7 : 4 + Math.min(node.mentions || 1, 4)) / 1;
            if (onTrail) {
              // amber halo so the whole evidence path pops
              ctx.beginPath();
              ctx.arc(node.x, node.y, r + 3.5, 0, 2 * Math.PI);
              ctx.fillStyle = "rgba(251, 191, 36, 0.25)";
              ctx.fill();
            }
            ctx.beginPath();
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            if (node.highlight || onTrail) {
              ctx.lineWidth = 2;
              ctx.strokeStyle = onTrail ? "#fbbf24" : "#ffffff";
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
