import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig(({ command }) => {
  const isProduction = command === 'build';

  return {
    plugins: [react(), tailwindcss()],
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        exclude: [
          'node_modules/**',
          'dist/**',
          'coverage/**',
          '**/*.d.ts',
          '**/*.config.*',
          '**/*.test.*',
          '**/*.spec.*',
          '**/test/**',
          '**/tests/**',
          '**/__tests__/**',
          '**/setup.ts',
          '**/vitest.config.*',
          '**/vite.config.*',
          '**/tailwind.config.*',
          '**/eslint.config.*',
          '**/prettier.config.*',
          '**/tsconfig.*',
          '**/components.json',
          '**/package.json',
          '**/package-lock.json',
          '**/index.html',
          '**/.gitignore',
          '**/.prettierrc',
          '**/README.md',
          '**/public/**',
          '**/src/test/**',
          '**/src/**/*.stories.*',
          '**/src/**/*.d.ts',
          '**/src/main.tsx',
          '**/src/types/**',
          '**/src/hooks/index.ts',
        ],
      },
    },
    build: {
      outDir: '../../api/server/static',
      emptyOutDir: true,
      assetsDir: 'static',
      rollupOptions: {
        output: {
          assetFileNames: (assetInfo) => {
            // const info = assetInfo.name?.split('.') || [];
            // const ext = info[info.length - 1];
            if (/\.(css)$/.test(assetInfo.name || '')) {
              return 'static/css/[name]-[hash][extname]';
            }
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/.test(assetInfo.name || '')) {
              return 'static/images/[name]-[hash][extname]';
            }
            if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name || '')) {
              return 'static/fonts/[name]-[hash][extname]';
            }
            return 'static/[name]-[hash][extname]';
          },
          chunkFileNames: 'static/js/[name]-[hash].js',
          entryFileNames: 'static/js/[name]-[hash].js',
        },
      },
    },
    server: {
      port: 4040,
    },
    base: isProduction ? '/static/' : '/',
    resolve: {
      alias: {
        '@': '/src',
      },
    },
  };
});
