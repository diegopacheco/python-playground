import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const taped = ['/books', '/calc', '/images', '/notes', '/game', '/blog', '/tapes']

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      taped.map((prefix) => [prefix, { target: 'http://127.0.0.1:7500', changeOrigin: false }])
    ),
  },
})
