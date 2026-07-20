import React, { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { api } from "../api";
import { TYPE_COLORS } from "../lib";
import { CountUp } from "../fx";

const LINK_TINT = {
  SIBLING_OF: "rgba(251, 191, 36, 0.45)",
  CONNECTED_TO: "rgba(56, 189, 248, 0.4)",
  HAS_FAILURE: "rgba(248, 113, 113, 0.35)",
  GOVERNED_BY: "rgba(45, 212, 191, 0.3)",
  DOCUMENTED_IN: "rgba(148, 163, 184, 0.22)",
};
const LINK_DEFAULT = "rgba(42, 58, 92, 0.7)";

// Tab switches unmount this component (AnimatePresence). Cache the fetched
// graph AND the simulation-positioned node objects per focus, so coming back
// paints instantly with the settled layout instead of refetch + re-warmup.
// version (= App reloadKey) invalidates the cache after an ingest.
const graphCache = new Map();
let cacheVersion = null;
function cacheFor(version) {
  if (version !== cacheVersion) {
    graphCache.clear();
    cacheVersion = version;
  }
  return graphCache;
}

export default function GraphView({ focus, trail = [], onFocusEntity, version = 0 }) {
  const cache = cacheFor(version);
  const cacheKey = focus || "__all__";
  const [data, setData] = useState(() => cache.get(cacheKey)?.data || { nodes: [], links: [] });
  const [dims, setDims] = useState({ w: 600, h: 500 });
  const [hoverType, setHoverType] = useState(null);
  const wrapRef = useRef(null);
  const fgRef = useRef(null);
  const hoverTypeRef = useRef(null);
  hoverTypeRef.current = hoverType;

  useEffect(() => {
    const hit = cache.get(cacheKey);
    if (hit) {
      setData(hit.data);
      return;
    }
    api.graph(focus || null, 2).then((d) => {
      cache.set(cacheKey, { data: d });
      setData(d);
    }).catch(() => {});
  }, [focus]); // eslint-disable-line react-hooks/exhaustive-deps

  // spread the layout out so labels are readable (skip when restoring an
  // already-settled cached layout — reheating would make it wobble)
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.d3Force("charge")?.strength(-220);
    fg.d3Force("link")?.distance(70);
    const positioned = cache.get(cacheKey)?.positioned;
    if (typeof positioned?.nodes[0]?.x !== "number") fg.d3ReheatSimulation?.();
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

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
    const hit = cache.get(cacheKey);
    if (hit?.positioned) return hit.positioned; // settled layout from a previous visit
    const g = {
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.links.map((l) => ({ ...l })),
    };
    if (hit) hit.positioned = g; // the simulation mutates x/y into these objects
    return g;
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  // cached layouts are already settled — skip warmup and finish instantly
  const settled = typeof graph.nodes[0]?.x === "number";

  const typeCounts = useMemo(() => {
    const s = {};
    data.nodes.forEach((n) => (s[n.type] = (s[n.type] || 0) + 1));
    return s;
  }, [data]);
  const types = useMemo(() => Object.keys(typeCounts).sort(), [typeCounts]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 flex-wrap px-3 py-2 border-b border-edge text-xs shrink-0">
        <span className="text-slate-400 font-mono">
          <CountUp value={graph.nodes.length} className="text-white" /> entities ·{" "}
          <CountUp value={graph.links.length} className="text-white" /> relationships
        </span>
        {trailNodes.size > 0 && (
          <span className="flex items-center gap-1.5 bg-amber/10 border border-amber/40 text-amber rounded-full px-2.5 py-0.5 font-mono text-[11px] tracking-wide">
            <span className="w-2 h-2 rounded-full bg-amber live-dot" />
            EVIDENCE TRAIL ACTIVE
          </span>
        )}
      </div>
      <div ref={wrapRef} className="flex-1 relative">
        <ForceGraph2D
          ref={fgRef}
          width={dims.w}
          height={dims.h}
          graphData={graph}
          backgroundColor="rgba(0,0,0,0)"
          warmupTicks={settled ? 0 : 120}
          cooldownTicks={settled ? 0 : 120}
          d3VelocityDecay={0.3}
          onEngineStop={() => fgRef.current?.zoomToFit(500, 60)}
          nodeRelSize={5}
          linkColor={(l) => (onTrailLink(l) ? "#fbbf24" : LINK_TINT[l.type] || LINK_DEFAULT)}
          linkWidth={(l) => (onTrailLink(l) ? 3 : l.type === "SIBLING_OF" || l.type === "CONNECTED_TO" ? 2 : 1)}
          linkDirectionalParticles={(l) => (onTrailLink(l) ? 4 : 0)}
          linkDirectionalParticleWidth={3.5}
          linkDirectionalParticleSpeed={0.012}
          linkDirectionalParticleColor={() => "#fbbf24"}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          onNodeClick={(n) => onFocusEntity?.(n.label)}
          nodeCanvasObject={(node, ctx, scale) => {
            // during a data swap the first frame can arrive before the
            // simulation has placed the node — drawing with non-finite
            // coords throws in createRadialGradient and blanks the canvas
            if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) return;
            const color = TYPE_COLORS[node.type] || "#64748b";
            const onTrail = trailNodes.has(node.id);
            const dimmed = hoverTypeRef.current && node.type !== hoverTypeRef.current && !onTrail;
            const r = (node.highlight || onTrail ? 7 : 4 + Math.min(node.mentions || 1, 4)) / 1;

            ctx.globalAlpha = dimmed ? 0.15 : 1;

            // soft color-matched glow behind every node (depth + atmosphere)
            const glowR = r * 2.6;
            const grad = ctx.createRadialGradient(node.x, node.y, r * 0.4, node.x, node.y, glowR);
            grad.addColorStop(0, color + (onTrail || node.highlight ? "55" : "2e"));
            grad.addColorStop(1, color + "00");
            ctx.beginPath();
            ctx.arc(node.x, node.y, glowR, 0, 2 * Math.PI);
            ctx.fillStyle = grad;
            ctx.fill();

            if (onTrail) {
              // pulsing amber halo so the whole evidence path breathes
              const pulse = 3 + Math.sin(performance.now() / 300) * 1.6;
              ctx.beginPath();
              ctx.arc(node.x, node.y, r + pulse, 0, 2 * Math.PI);
              ctx.fillStyle = "rgba(251, 191, 36, 0.22)";
              ctx.fill();
            }

            // node body: bright core + darker rim for depth
            ctx.beginPath();
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.beginPath();
            ctx.arc(node.x - r * 0.25, node.y - r * 0.25, r * 0.45, 0, 2 * Math.PI);
            ctx.fillStyle = "rgba(255,255,255,0.35)";
            ctx.fill();

            if (node.highlight || onTrail) {
              ctx.lineWidth = 2;
              ctx.strokeStyle = onTrail ? "#fbbf24" : "#ffffff";
              ctx.beginPath();
              ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
              ctx.stroke();
            }

            const label = node.label;
            const fs = Math.max(10 / scale, 3);
            ctx.font = `${node.highlight ? "700 " : "500 "}${fs}px "JetBrains Mono", ui-monospace, monospace`;
            // dark backing shadow so labels stay readable over the grid
            ctx.shadowColor = "rgba(7, 11, 20, 0.9)";
            ctx.shadowBlur = 4;
            ctx.fillStyle = node.highlight ? "#ffffff" : "#93a4c3";
            ctx.textAlign = "center";
            ctx.fillText(label, node.x, node.y + r + fs + 1);
            ctx.shadowBlur = 0;
            ctx.globalAlpha = 1;
          }}
        />

        {/* floating glass legend — hover a type to isolate it */}
        <div className="absolute bottom-3 right-3 glass-strong rounded-xl px-3 py-2.5 max-w-[190px]">
          <div className="text-[10px] text-slate-400 font-mono tracking-widest mb-1.5">ONTOLOGY</div>
          <div className="space-y-1">
            {types.map((t) => (
              <div
                key={t}
                onMouseEnter={() => setHoverType(t)}
                onMouseLeave={() => setHoverType(null)}
                className={`flex items-center gap-2 text-[11px] cursor-default rounded px-1 -mx-1 transition-colors ${hoverType === t ? "bg-panel2" : ""}`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ background: TYPE_COLORS[t] || "#64748b", boxShadow: `0 0 6px ${TYPE_COLORS[t] || "#64748b"}88` }}
                />
                <span className="text-slate-300 truncate">{t}</span>
                <span className="ml-auto font-mono text-slate-500">{typeCounts[t]}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="absolute bottom-3 left-3 text-[10px] text-slate-500 glass rounded-lg px-2 py-1 font-mono">
          click a node to focus · drag to explore
        </div>
      </div>
    </div>
  );
}
