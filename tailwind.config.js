/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./estuairefleet/templates/**/*.html",
    "./estuairefleet/static/js/**/*.js",
    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        insam: {
          50: "#fff1f3",
          100: "#ffe0e5",
          200: "#ffc1cb",
          300: "#ff92a3",
          400: "#fb5870",
          500: "#e42949",
          600: "#c8102e",
          700: "#a90f29",
          800: "#8d1128",
          900: "#781328",
        },
        ink: "#111827",
        cloud: "#f7f8fa",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 55px rgba(15, 23, 42, .08)",
        lift: "0 22px 70px rgba(200, 16, 46, .16)",
      },
      backgroundImage: {
        "hero-grid": "linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px)",
      },
    },
  },
  plugins: [require("flowbite/plugin")],
};
