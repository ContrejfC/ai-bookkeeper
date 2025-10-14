import type { Config } from "tailwindcss";
import { nextui } from "@nextui-org/react";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./pages/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}"
  ],
  darkMode: "class",
  theme: {
    extend: {
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem"
      }
    }
  },
  plugins: [nextui({
    // Map Tailwind tokens to NextUI semantic tokens
    themes: {
      light: {
        colors: {
          primary: { DEFAULT: "#10b981" },   // emerald-500
          success: { DEFAULT: "#059669" },   // emerald-600
          warning: { DEFAULT: "#f59e0b" },   // amber-500
          danger:  { DEFAULT: "#ef4444" }    // red-500
        },
        layout: {
          radius: { small: "0.375rem", medium: "0.75rem", large: "1rem" }
        }
      },
      dark: {
        colors: {
          primary: { DEFAULT: "#10b981" },   // emerald-500
          success: { DEFAULT: "#059669" },   // emerald-600
          warning: { DEFAULT: "#fbbf24" },   // amber-400
          danger:  { DEFAULT: "#f87171" }    // red-400
        },
        layout: {
          radius: { small: "0.375rem", medium: "0.75rem", large: "1rem" }
        }
      }
    }
  })],
};

export default config;

