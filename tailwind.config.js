/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./frontend/src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        muted: "#697386",
        panel: "#ffffff",
        line: "#d9dee7",
        brand: "#145c72",
        action: "#287c76",
        caution: "#a15c16",
        danger: "#b42318"
      }
    }
  },
  plugins: []
};
