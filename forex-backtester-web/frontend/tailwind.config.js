/** @type {import('tailwindcss').Config} */
module.exports =  {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg:      '#0A0E1A',
        surface: '#111827',
        card:    '#1A2235',
        border:  '#1E2D45',
        accent:  '#00D4AA',
        red:     '#FF4D6D',
        gold:    '#FFB347',
        muted:   '#6B7A99',
        text:    '#E2E8F0',
      },
      fontFamily: {
        display: ['"DM Mono"', 'monospace'],
        body:    ['"IBM Plex Sans"', 'sans-serif'],
      }
    }
  },
  plugins: []
}
