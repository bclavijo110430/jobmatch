// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import react from '@astrojs/react';
import icon from 'astro-icon';

// https://astro.build/config
export default defineConfig({
  integrations: [react(), icon()],
  vite: {
    plugins: [tailwindcss(), tsconfigPaths()],
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8501',
          changeOrigin: true,
          secure: false,
        },
      },
    },
  },
  output: 'static',
  build: {
    format: 'directory',
  },
  trailingSlash: 'never',
});