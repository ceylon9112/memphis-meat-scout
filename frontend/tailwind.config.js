/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Primary BBQ accent — used strategically, not dominant
        ember:        '#C8471A',
        'ember-light':'#E8724A',

        // Outdoor lifestyle accents
        forest:       '#4A7C59',   // hunting / hiking / golf
        'forest-light':'#6BA878',
        sky:          '#5B8FA8',   // fishing / open air
        'sky-light':  '#8BB5CC',
        amber:        '#C4841A',   // beer garden / golden hour
        'amber-light':'#E0A840',

        // Text scale — warm espresso tones, never cold black
        espresso:     '#2C1F10',
        bark:         '#6B5040',
        driftwood:    '#9B8068',

        // Surfaces
        linen:        '#FAF6F0',   // page background
        parchment:    '#F3EDE3',   // subtle tint
        sage:         '#EEF4F1',   // cool accent

        // Legacy aliases kept for compatibility
        charcoal:     '#2C1F10',
        'burnt-orange':'#C8471A',
        cream:        '#FAF6F0',
        gold:         '#C4841A',
        smoke:        '#6B5040',
        ash:          '#9B8068',
      },
      fontFamily: {
        display: ['Oswald', 'Impact', 'sans-serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
