import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    // 本机安全策略拒绝批量删除/覆盖（≥50 文件 / 复制覆盖受限）；
    // 不复制 public/（favicon 已内联 data URI），构建覆盖写入而非清空 dist。
    emptyOutDir: false,
    publicDir: false,
  },
});
