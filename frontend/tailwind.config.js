/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0f172a",
        cardBg: "#1e293b",
        applyGreen: "#22c55e",
        stretchYellow: "#eab308",
        skipRed: "#ef4444",
      }
    },
  },
  plugins: [],
}
