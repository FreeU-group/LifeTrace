import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
  base: './',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
  },
  server: {
    port: 8844,
    host: true,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8840',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://localhost:8840',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
