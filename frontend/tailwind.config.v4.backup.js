/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        por: {
          50:"#e9f9f0",100:"#c9f1dc",200:"#92e3ba",300:"#5dd798",400:"#2ecf7a",
          500:"#00a651",600:"#00904a",700:"#007a40",800:"#036336",900:"#084f2d",
        },
      },
      boxShadow: { soft: "0 1px 2px rgba(0,0,0,.12), 0 8px 24px rgba(0,0,0,.24)" },
    },
  },
  plugins: [],
};
