import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0a0a0f",
        panel: "#0e0e14",
        accent: {
          DEFAULT: "#2dd4bf",
          dim: "rgba(45, 212, 191, 0.35)",
        },
        maya: "#f59e0b",
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 12px rgba(45, 212, 191, 0.25)",
        "glow-lg": "0 0 24px rgba(45, 212, 191, 0.35)",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.25" },
        },
      },
      animation: {
        "pulse-dot": "pulseDot 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
