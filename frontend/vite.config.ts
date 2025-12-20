import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,            // важно для ngrok
    port: 5173,
    strictPort: true,
    allowedHosts: ['vanda-uncongruous-frieda.ngrok-free.dev'],

    hmr: {
      clientPort: 443,    // ngrok работает через https
    },

    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

