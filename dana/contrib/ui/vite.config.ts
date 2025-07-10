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
