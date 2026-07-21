/**
 * Voice-first field mode — Web Speech API helpers.
 *
 * Technicians wear gloves and work in 90 dB environments: hands-free voice
 * queries + spoken answers, in the technician's own language. The corpus and
 * tags stay English; only the delivery language changes (backend `lang`).
 *
 * Notes:
 *  - SpeechRecognition is Chromium/WebKit only and needs network (cloud ASR);
 *    typing always remains available as fallback.
 *  - speechSynthesis voices depend on the OS; we pick the closest match for
 *    the selected language and fall back gracefully.
 */

const SR = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

export const speechSupported = !!SR;
export const ttsSupported = typeof window !== "undefined" && "speechSynthesis" in window;

export const LANGS = [
  { code: "en", bcp: "en-IN", label: "EN", name: "English" },
  { code: "hi", bcp: "hi-IN", label: "हिं", name: "Hindi" },
  { code: "te", bcp: "te-IN", label: "తె", name: "Telugu" },
  { code: "ta", bcp: "ta-IN", label: "த", name: "Tamil" },
  { code: "kn", bcp: "kn-IN", label: "ಕ", name: "Kannada" },
  { code: "mr", bcp: "mr-IN", label: "म", name: "Marathi" },
  { code: "bn", bcp: "bn-IN", label: "বা", name: "Bengali" },
];

export function makeRecognizer(bcp, { onInterim, onFinal, onEnd, onError } = {}) {
  if (!SR) return null;
  const rec = new SR();
  rec.lang = bcp;
  rec.interimResults = true;
  rec.maxAlternatives = 1;
  rec.continuous = false;
  rec.onresult = (e) => {
    let interim = "", final = "";
    for (const res of e.results) {
      if (res.isFinal) final += res[0].transcript;
      else interim += res[0].transcript;
    }
    if (interim) onInterim?.(interim);
    if (final) onFinal?.(final.trim());
  };
  rec.onend = () => onEnd?.();
  rec.onerror = (e) => onError?.(e.error);
  return rec;
}

/** Speak an answer aloud. Citations/markdown are visual — strip before speaking. */
export function speak(text, bcp, onDone) {
  if (!ttsSupported) { onDone?.(); return; }
  window.speechSynthesis.cancel();
  const clean = (text || "")
    .replace(/\[DOC:[A-Za-z0-9\-]+\]/g, "")
    .replace(/\*\*/g, "")
    .replace(/_\([^)]*\)_/g, "")
    .replace(/[•▸→_#|]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!clean) { onDone?.(); return; }
  const u = new SpeechSynthesisUtterance(clean.slice(0, 1400)); // field briefings stay short
  u.lang = bcp;
  const voices = window.speechSynthesis.getVoices();
  const v = voices.find((x) => x.lang === bcp) ||
            voices.find((x) => x.lang?.startsWith(bcp.split("-")[0]));
  if (v) u.voice = v;
  u.rate = 1.02;
  u.onend = () => onDone?.();
  u.onerror = () => onDone?.();
  window.speechSynthesis.speak(u);
}

export function stopSpeaking() {
  if (ttsSupported) window.speechSynthesis.cancel();
}
