/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        main: 'var(--bg-main)',
        sidebar: 'var(--bg-sidebar)',
        surface: 'var(--bg-surface)',
        hover: 'var(--bg-hover)',
        border: 'var(--border-subtle)',
        primary: 'var(--text-primary)',
        muted: 'var(--text-muted)',
        accent: 'var(--accent-green)',
        critical: '#8E2F2B',
        high: '#C6533C',
        watch: '#D88A32',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace'],
        heading: ['Space Grotesk', 'sans-serif'],
      },
      boxShadow: {
        'emergency-glow': '0 0 35px rgba(239, 68, 68, 0.4)',
        'warning-glow': '0 0 25px rgba(245, 158, 11, 0.3)',
        'safe-glow': '0 0 20px rgba(16, 185, 129, 0.25)',
        'surface-elevated': '0 10px 30px -10px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
