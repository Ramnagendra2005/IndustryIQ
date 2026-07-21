# Design — IndustryIQ

A locked design system for this app. Every screen redesign reads this file
before emitting code. Do not regenerate per screen — extend or amend this file
when the system needs to grow.

**Register:** a refinery control room after dark. Bloomberg-terminal density,
mission-control calm. Instrument panels, not SaaS cards. The UI must read as
"the plant's collective memory — it sees what you can't."

## Genre
atmospheric (dark technical canvas), disciplined by the industrial brief:
no glassmorphism, density over whitespace, flat high-contrast fills.

## Macrostructure family
Single-shell application (control-room workbench). All screens are app pages —
panels inside the shell, no marketing pages, no hero enrichment anywhere.

- App shell:  header toolbar + split chat/panels + tab rail
- Panels:     dense instrument layouts; every card shows 3–4 data points
              without a click; compact vertical rhythm

## Theme (custom · "refinery control room after dark")
Raw OKLCH channels live in `frontend/src/tokens.css`; Tailwind maps semantic
class names onto them. Never inline a colour value in a component.

- `--iq-paper`    oklch(15% 0.018 255) — page ground
- `--iq-paper-2`  oklch(18% 0.02 255)  — panel plate
- `--iq-paper-3`  oklch(22% 0.024 255) — raised plate (elevation = lighter)
- `--iq-rule`     oklch(32% 0.028 255) — hairline
- `--iq-ink`      oklch(93% 0.008 250) — primary text
- `--iq-accent`   oklch(78% 0.14 75)   — amber. THE action/brand hue.
- `--iq-data`     oklch(78% 0.115 180) — teal. Telemetry & data ONLY.
- `--iq-alarm`    oklch(68% 0.19 25)   — red. Danger states only, never décor.
- `--iq-ok`       oklch(76% 0.15 160)  — green. Confirmed-good only.

Colour discipline: amber ≤ ~5% of any viewport. Neutrals are navy-tinted
(hue 250–255), never flat grey. No gradients on interactive elements.
No gradient text. No pure #000/#fff.

## Typography
- Display: Space Grotesk, 600/700, roman only (italic headers banned)
- Body:    Space Grotesk 400
- Mono:    JetBrains Mono — EVERY data value, ID, timestamp, reading,
           and stenciled panel label (`.stencil`: 10px, +0.14em, uppercase)
- Engineers read mono: if it's a number or a tag, it's mono.

## Spacing
4-pt scale, dense. Panel padding 12–16px, card gaps 8–12px. Information
density over whitespace — closer to a terminal than a landing page.

## Corners
Mixed on purpose: data surfaces near-sharp (2–8px via remapped Tailwind
radii), pills/lamps fully round. Nothing bubbly.

## Motion
Mechanical, never springy. Easings `--ease-out / --ease-in / --ease-in-out`
(tokens.css). Durations 120/220/420ms. Entering elements: fade + ≤8px rise.
Evidence trail animates as a signal trace (sequential stagger). No idle
bobbing, no decorative infinite loops — only functional indicators may loop
(status lamps, skeletons, needle jitter, stream caret). Full
`prefers-reduced-motion` support.

## Microinteractions stance
- Silent success (no celebratory toasts)
- Status is shown by panel lamps (`.live-dot`, `.danger-dot`), not chips
- Focus ring: 2px amber, instant, never animated
- Hover: hairline ring + 1px lift (`shadow-glow-*` = re-disciplined rings)

## Component voice
- Panels: `.glass` / `.glass-strong` = flat opaque plates, hairline rule,
  inset top light. NOT frosted glass.
- Stencil labels head every panel section (`ANALYSIS`, `EVIDENCE TRAIL`,
  `CONFLICTING SOURCES`) — stacked above content, never left-of-heading.
- Severity rails: 3–4px solid left edge in the semantic hue.
- TRUST CHECK: `.hazard` placard — yellow/black striped leading edge.
- Proactive alert: `.border-flow` annunciator tile — steady alarm frame +
  inset alarm rail; only the lamp blinks.
- Citations: filing-tab cards — doc-type coloured tab on the left edge.
- Gauges/readouts: RadialGauge + mono CountUp readouts; instrument, not chart.

## CTA voice
- Primary: amber fill, `--radius-control` (6px), ink-on-amber text
- Secondary: plate fill + hairline, text brightens on hover
- Never gradient fills; never two primary CTAs in one view

## Per-page allowances
- App screens MUST NOT use enrichment — function carries the page.
- Boot splash is the one theatrical moment: POST self-test sequence
  (mono boot lines, [ ]→[✓] checks, drawn logo edges, CRT scanline).

## What screens MUST share
- The wordmark, the amber accent + its discipline, both fonts,
  panel/lamp/stencil/rail vocabulary, CTA voice, tokens.css.

## What screens MAY differ on
- Instrument choice per domain: dial gauge (Trust), checklist matrix
  (Compliance), file registry (Documents), conveyor pipeline (Ingest),
  force graph (Explore), briefing (Chat).
