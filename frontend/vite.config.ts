import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    port: 5173,
    strictPort: false,
    open: true,
    host: true,
    https: {}, // Force HTTPS to be recognized (basicSsl fills the certs)
    proxy: {
      '/chat': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/chat_stream': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/stats': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/avatar-check': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/process_audio': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/cameras': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/stream': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/execute': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/devices': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/speak': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/tts': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/phygital': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/settings': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
      '/kb': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false },
    }
  }
})
