import { coffee } from "vite-plugin-coffee3";
import { sveltekit } from '@sveltejs/kit/vite';
//import { enhancedImages } from '@sveltejs/enhanced-img';
import { defineConfig } from 'vite';
import mkcert from 'vite-plugin-mkcert';
import { SvelteKitPWA } from '@vite-pwa/sveltekit'


let production = process.env["NODE_ENV"] == 'production';

let config = {
  optimizeDeps: {
    noDiscovery: true,
    include: [
      'actual',
      '@lingui/core',
      '@lingui/message-utils/compileMessage',
      '@messageformat/parser',
      'leaflet',
      'lodash/debounce',
      'unraw'
    ],
  },
  plugins: [
    //enhancedImages(),
    sveltekit(),
    coffee({
      sourceMap: !production,
    }),
    mkcert(),
    SvelteKitPWA({
      registerType: 'autoUpdate',
      trailingSlash: 'always',

      manifest: {
        name: 'Climbing in Montenegro',
        short_name: 'Montenegro Climbing Guide',
        description: 'The interactive climbing guide to Montenegro',
        display: "minimal-ui",
        theme_color: '#e4e6ee',
        "icons": [
          {
            "src": "pwa-64x64.png",
            "sizes": "64x64",
            "type": "image/png"
          },
          {
            "src": "pwa-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
          },
          {
            "src": "pwa-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
          },
          {
            "src": "maskable-icon-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable"
          }
        ],
        "screenshots": [
          {
            "src": "desktop.png",
            "sizes": "1280x720",
            "type": "image/png",
            "form_factor": "wide",
            "purpose": "any"
          },
          {
            "src": "mobile.png",
            "sizes": "360x640",
            "type": "image/png",
            "form_factor": "narrow",
            "purpose": "any"
          }
        ]
      },
      workbox: {
        globPatterns: ['client/**/*.{js,css,html,txt,json,jpg,png,svg,ico}'],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/.\.tile\.openstreetmap\.org\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              expiration: {
                maxEntries: 1000,
                maxAgeSeconds: 60 * 60 * 24 * 365 // <== 365 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      },
      devOptions: {
        enabled: true
        /* other options */
      }
    })
  ],
  define: {
    '__APP_VERSION__': JSON.stringify(process.env.npm_package_version),
  },
  build: {
    sourcemap: false,
    minify: true,
    cssMinify: true,
  },
  server: {
    https: true,
    sourcemap: "inline",
    proxy: {}
  }
};

/*
Does not work because of sveltekit :-(
if (! process.env["VITE_AS_PWA"]) {
  config.build.rollupOptions = {
    output: {
      entryFileNames: '[name].js',
      assetFileNames: '[name].[ext]',
      chunkFileNames: '[name].js',
    }
  };
}

console.log("with pwa?", process.env["VITE_AS_PWA"])
*/

export default defineConfig(config);
