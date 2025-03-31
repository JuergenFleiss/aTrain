/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./aTrain/templates/*.html", "./aTrain/templates/*/*.html", "./aTrain/templates/*/*/*.html", "./aTrain/static/JS/*.js"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
}

