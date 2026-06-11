import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// For GitHub Pages: base path matches the repo name
// For local dev: base is '/'
const base = process.env.VITE_BASE_URL || (process.env.NODE_ENV === 'production' ? '/world_cup_scoreboard_2026/' : '/');

export default defineConfig({
  plugins: [react()],
  base,
  server: {
    proxy: {
      '/api': 'http://localhost:3001',
    },
  },
});
