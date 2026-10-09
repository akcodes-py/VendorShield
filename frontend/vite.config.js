import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// WHY: proxy /api to FastAPI avoids CORS in dev (strict CORS still on backend).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000', '/health': 'http://localhost:8000' } },
})
