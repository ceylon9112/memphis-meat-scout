import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
      manifest: {
        name: 'Memphis Meat Scout',
        short_name: 'Meat Scout',
        description: 'Best verified meat deals in the Memphis area for outdoor cooks.',
        theme_color: '#C8471A',
        background_color: '#1C1C1C',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^\/api\/deals/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'deals-cache',
              expiration: { maxAgeSeconds: 7 * 24 * 60 * 60, maxEntries: 50 },
              networkTimeoutSeconds: 5,
            },
          },
          {
            urlPattern: /^\/api\/cuts/,
            handler: 'NetworkFirst',
            options: { cacheName: 'cuts-cache', expiration: { maxAgeSeconds: 24 * 60 * 60 } },
          },
          {
            urlPattern: /^\/api\/vendors/,
            handler: 'NetworkFirst',
            options: { cacheName: 'vendors-cache', expiration: { maxAgeSeconds: 24 * 60 * 60 } },
          },
          {
            urlPattern: /^\/api\/weather/,
            handler: 'NetworkFirst',
            options: { cacheName: 'weather-cache', expiration: { maxAgeSeconds: 3 * 60 * 60 } },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
