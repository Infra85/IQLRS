import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        quantum: {
          50: "#eefaff",
          100: "#d8f2ff",
          200: "#b8e9ff",
          300: "#8ed7ff",
          400: "#67c1ff",
          500: "#4da8ff",
          600: "#3288d4",
          700: "#276aa5",
          800: "#214e74",
          900: "#17354d",
          950: "#0a1c29",
        },
        ink: {
          950: "#030405",
          900: "#07090c",
          800: "#11151a",
          700: "#1b2229",
        },
        surface: {
          DEFAULT: "#11151a",
          raised: "#151a20",
          muted: "#1b2229",
        },
        signal: {
          cyan: "#30C9D7",
          mint: "#4DD6A7",
          amber: "#F7B955",
          rose: "#F57A93",
        },
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
