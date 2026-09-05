/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#0b0c10',
        surface: {
          DEFAULT: '#14171f',
          elevated: '#1c212d',
          border: '#2e3646',
          hover: '#242a38',
        },
        emergency: {
          DEFAULT: '#dc2626',
          bright: '#ef4444',
          dark: '#991b1b',
          glow: 'rgba(239, 68, 68, 0.25)',
        },
        warning: {
          DEFAULT: '#f59e0b',
          bright: '#fbbf24',
          dark: '#b45309',
          glow: 'rgba(245, 158, 11, 0.2)',
        },
        info: {
          DEFAULT: '#3b82f6',
          bright: '#60a5fa',
        },
        safe: {
          DEFAULT: '#10b981',
          bright: '#34d399',
        },
        charcoal: {
          900: '#0b0c10',
          800: '#14171f',
          700: '#1c212d',
          600: '#2a3040',
          500: '#40495e',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace'],
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
