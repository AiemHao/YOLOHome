import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.js$/,
    exclude: [],
  },
  plugins: [
    react({
      include: /\.[jt]sx?$/,
    }),
  ],
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
});
