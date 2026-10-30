import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    // 개발 중에는 /api 요청을 로컬 FastAPI 서버로 넘긴다 (배포에서는 nginx가 같은 일을 한다)
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  preview: {
    // Mac에서 Cloudflare Tunnel로 공개할 때(docs/tunnel-guide.md) 들어오는 도메인을 허용한다
    allowedHosts: ['chat.sjhan.com'],
  },
})
