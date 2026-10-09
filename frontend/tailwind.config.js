/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#0b0f19',
          surface: '#0f172a',
          panel: '#111827',
          border: '#1e2c40',
          cyan: '#00e5ff',
          green: '#10b981',
          red: '#f43f5e',
          amber: '#f59e0b',
          purple: '#a855f7',
          slate: '#334155',
          text: '#f8fafc',
          muted: '#94a3b8',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { textShadow: '0 0 4px #00e5ff' },
          '100%': { textShadow: '0 0 16px #00e5ff, 0 0 32px #00e5ff' },
        },
      },
    },
  },
  plugins: [],
};
