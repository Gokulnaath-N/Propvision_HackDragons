/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0B0F19",
        primary: "#5B8CFF",
        accent: "#9FE870",
        textPrimary: "#E6EDF3",
        textSecondary: "#9BA3AF",
        panel: "rgba(255, 255, 255, 0.05)",
        panelHover: "rgba(255, 255, 255, 0.1)",
        border: "rgba(255, 255, 255, 0.1)",
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-blob': 'radial-gradient(circle at center, rgba(91, 140, 255, 0.15) 0%, rgba(11, 15, 25) 70%)',
      }
    },
  },
  plugins: [],
}
