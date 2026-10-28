import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  // Allow VITE_API_URL to be injected at build time by Vercel
  // Set VITE_API_URL=https://your-render-app.onrender.com/api in Vercel env vars
})
