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
          primary: { DEFAULT: "#0ea5e9" },   // sky-500
          success: { DEFAULT: "#16a34a" },   // green-600
          warning: { DEFAULT: "#f59e0b" },   // amber-500
          danger:  { DEFAULT: "#ef4444" }    // red-500
        },
        layout: {
          radius: { small: "0.375rem", medium: "0.75rem", large: "1rem" }
        }
      },
      dark: {
        colors: {
          primary: { DEFAULT: "#0ea5e9" },
          success: { DEFAULT: "#22c55e" },
          warning: { DEFAULT: "#fbbf24" },
          danger:  { DEFAULT: "#f87171" }
        }
      }
    }
  })],
};

export default config;

