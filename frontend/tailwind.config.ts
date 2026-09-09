import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        quantum: {
          50: "#f0f4ff",
          100: "#dbe4ff",
          200: "#bac8ff",
          300: "#91a7ff",
          400: "#748ffc",
          500: "#5c7cfa",
          600: "#4c6ef5",
          700: "#4263eb",
          800: "#3b5bdb",
          900: "#364fc7",
        },
        ink: {
          950: "#070B18",
          900: "#0B1020",
          800: "#111A31",
          700: "#182443",
        },
        surface: {
          DEFAULT: "#10182C",
          raised: "#151F37",
          muted: "#1A2641",
        },
        signal: {
          cyan: "#30C9D7",
          mint: "#4DD6A7",
          amber: "#F7B955",
          rose: "#F57A93",
        },
      },
      boxShadow: {
        panel: "0 16px 40px rgba(0, 0, 0, 0.18)",
        "panel-hover": "0 20px 48px rgba(0, 0, 0, 0.26)",
        glow: "0 0 0 1px rgba(92, 124, 250, 0.16), 0 12px 32px rgba(76, 110, 245, 0.2)",
      },
      borderRadius: {
        "4xl": "1.75rem",
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
