/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#070b14",
        panel: "#0c1322",
        panel2: "#111b2f",
        edge: "#1d2b47",
        edge2: "#2b3f66",
        accent: "#f5a623",
        teal: "#2dd4bf",
        glow: "#38bdf8",
        amber: "#fbbf24",
        danger: "#f87171",
        ok: "#34d399",
      },
      fontFamily: {
        sans: ["Space Grotesk", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        "glow-accent": "0 0 18px -2px rgba(245, 166, 35, 0.35)",
        "glow-teal": "0 0 18px -2px rgba(45, 212, 191, 0.35)",
        "glow-danger": "0 0 18px -2px rgba(248, 113, 113, 0.4)",
        "glow-blue": "0 0 18px -2px rgba(56, 189, 248, 0.35)",
        lift: "0 8px 24px -8px rgba(0, 0, 0, 0.6)",
      },
      animation: {
        float: "float 5s ease-in-out infinite",
        shimmer: "shimmer 1.6s linear infinite",
        marchDash: "marchDash 24s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-4px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        marchDash: {
          to: { strokeDashoffset: "-1000" },
        },
      },
    },
  },
  plugins: [],
};
