import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        panel: "#f7f4ef",
        line: "#d9d3c8",
        mint: "#1d7f70",
        berry: "#9d2f5f",
        amber: "#b76e16"
      }
    }
  },
  plugins: []
};

export default config;
