import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/health': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/auth': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/incidents': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/status': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/risk': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/intelligence': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/volunteers': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/assignments': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/sensors': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/notifications': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})