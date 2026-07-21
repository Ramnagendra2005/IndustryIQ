/**
 * Offline dossier — for poor-connectivity plant areas.
 *
 * Every answered query (and the full text of its cited source documents) is
 * cached in localStorage, keyed by the equipment the answer is about. When the
 * device goes offline, the copilot serves the best-matching cached answer with
 * an explicit OFFLINE DOSSIER badge instead of failing.
 */
const KEY = "iiq-dossier-v1";
const MAX_ANSWERS = 40;

function load() {
  try { return JSON.parse(localStorage.getItem(KEY)) || { answers: [], docs: {} }; }
  catch { return { answers: [], docs: {} }; }
}
function save(d) {
  try { localStorage.setItem(KEY, JSON.stringify(d)); }
  catch { /* storage full — dossier is best-effort */ }
}

export function rememberAnswer(question, res) {
  if (!res?.answer || !res.citations?.length) return; // don't cache refusals
  const d = load();
  d.answers = d.answers.filter((a) => a.question !== question);
  d.answers.unshift({
    question,
    answer: res.answer,
    confidence: res.confidence,
    citations: (res.citations || []).slice(0, 6),
    trust: res.trust || null,
    entities: res.focus_entities || [],
    mode: res.mode,
    at: Date.now(),
  });
  d.answers = d.answers.slice(0, MAX_ANSWERS);
  save(d);
}

export function rememberDoc(doc) {
  if (!doc?.id) return;
  const d = load();
  d.docs[doc.id] = { id: doc.id, title: doc.title, text: doc.text, doc_type: doc.doc_type, date: doc.date };
  save(d);
}

const tok = (s) => ((s || "").toLowerCase().match(/[a-z0-9\-]+/g) || []).filter((w) => w.length > 2);

/** Best cached answer for a question, or null if nothing matches well enough. */
export function offlineAnswer(question) {
  const d = load();
  const q = new Set(tok(question));
  let best = null, bestScore = 0;
  for (const a of d.answers) {
    const t = new Set(tok(a.question));
    let overlap = 0;
    for (const w of q) if (t.has(w)) overlap++;
    const score = overlap / Math.max(1, Math.min(q.size, t.size));
    if (score > bestScore) { best = a; bestScore = score; }
  }
  return bestScore >= 0.45 ? best : null;
}

export function cachedDoc(id) {
  return load().docs[id] || null;
}

export function dossierStats() {
  const d = load();
  const ents = {};
  d.answers.forEach((a) => (a.entities || []).forEach((e) => {
    if (/^[A-Z]{1,3}-\d{2,4}$/i.test(e)) ents[e] = (ents[e] || 0) + 1;
  }));
  const topEntity = Object.entries(ents).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
  return { answers: d.answers.length, docs: Object.keys(d.docs).length, topEntity };
}
