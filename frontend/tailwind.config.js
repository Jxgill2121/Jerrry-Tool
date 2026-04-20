/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        base:     "#0d1117",
        surface:  "#161b22",
        surface2: "#21262d",
        border:   "#30363d",
        accent:   "#388bfd",
      },
    },
  },
  plugins: [],
};
