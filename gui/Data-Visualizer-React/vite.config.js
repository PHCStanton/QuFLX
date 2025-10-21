import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  // Remove viteSourceLocator to avoid SES lockdown interfering with 3rd-party libs like lightweight-charts
  plugins: [react()],
  publicDir: 'public',
  server: {
    host: '0.0.0.0',
    port: 5000,
    allowedHosts: true,
    fs: {
      allow: ['..']
    },
    headers: {
      'Content-Security-Policy': "script-src 'self' 'unsafe-eval' 'unsafe-inline' blob: https://unpkg.com; object-src 'none'; worker-src 'self' blob:;"
    },
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false
      },
      '/socket.io': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        ws: true
      }
    }
  },
  define: {
    __DATA_HISTORY_PATH__: JSON.stringify('/data_history')
  },
  optimizeDeps: {
    // Exclude lightweight-charts to prevent bundling issues with v5.x
    exclude: ['lightweight-charts']
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['src/tests/setupTests.js'],
    globals: true
  }
})
