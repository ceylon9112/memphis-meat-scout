/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        charcoal: '#1C1C1C',
        'burnt-orange': '#C8471A',
        cream: '#F5F0E8',
        gold: '#E8C547',
        'smoke': '#2E2E2E',
        'ash': '#4A4A4A',
      },
      fontFamily: {
        display: ['Oswald', 'Impact', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
