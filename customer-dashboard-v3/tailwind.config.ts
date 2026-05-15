import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg:      "#F7F7F5",
        surface: "#F0F0ED",
        card:    "#FFFFFF",
        sidebar: "#EFEFEC",
        border:  "#E4E4DC",
        border2: "#D4D4CC",
        mint:    "#00A991",
        amber:   "#D97706",
        danger:  "#DC2626",
        success: "#059669",
        ink:     "#171717",
        muted:   "#737373",
        muted2:  "#A3A3A3",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "SF Mono", "Cascadia Code", "monospace"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)",
        md:   "0 4px 12px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.04)",
      },
    },
  },
  plugins: [],
};

export default config;
