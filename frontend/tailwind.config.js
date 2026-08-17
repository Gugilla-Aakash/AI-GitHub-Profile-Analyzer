/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class", // Enables switching between light and dark mode
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./providers/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        neo: {
          // Exact colors matched from your reference images
          light: "#f0f2f5",
          dark: "#1a1b23",
        },
      },
      boxShadow: {
        // Light mode 3D shadows
        "neo-outset": "8px 8px 16px #d1d5db, -8px -8px 16px #ffffff",
        "neo-inset": "inset 8px 8px 16px #d1d5db, inset -8px -8px 16px #ffffff",
        // Dark mode 3D shadows
        "neo-outset-dark": "8px 8px 16px #121319, -8px -8px 16px #22232d",
        "neo-inset-dark":
          "inset 8px 8px 16px #121319, inset -8px -8px 16px #22232d",
      },
    },
  },
  plugins: [],
};
