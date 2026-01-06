/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Templates Django globaux
    './templates/**/*.html',
    // Templates de toutes les apps Django
    './accounts/templates/**/*.html',
    './dashboard/templates/**/*.html',
    './events/templates/**/*.html',
    './fractionnement/templates/**/*.html',
    './home/templates/**/*.html',
    './role/templates/**/*.html',
    './secteurs/templates/**/*.html',
    // Fichiers Python (pour les classes dynamiques)
    './**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        'custom-blue': {
          DEFAULT: '#1f4d9b',
          hover: '#1a3f82',
        },
      },
    },
  },
  plugins: [],
}

