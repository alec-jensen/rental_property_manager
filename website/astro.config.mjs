import { defineConfig } from 'astro/config';

import sitemap from '@astrojs/sitemap';
import tailwind from '@astrojs/tailwind';
import AstroPWA from '@vite-pwa/astro'

const DEV_PORT = 2121;

// https://astro.build/config
export default defineConfig({
	site: process.env.CI
		? 'https://themesberg.github.io'
		: `http://localhost:${DEV_PORT}`,
	base: process.env.CI ? '/flowbite-astro-admin-dashboard' : undefined,

	// output: 'server',

	/* Like Vercel, Netlify,… Mimicking for dev. server */
	// trailingSlash: 'always',

	server: {
		/* Dev. server only */
		port: DEV_PORT,
	},

	vite: {
    logLevel: 'info',
    server: {
      fs: {
        // Allow serving files from hoisted root node_modules
        allow: ['../..']
      }
    },
  },

	integrations: [
		//
		sitemap(),
		tailwind(),
		AstroPWA({
      mode: 'development',
      base: '/',
      scope: '/',
      includeAssets: ['favicon.svg'],
      registerType: 'autoUpdate',
      manifest: {
        name: 'TDM Properties',
        short_name: 'TDM Properties',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'favicon-192px.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'favicon-512px.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: 'favicon-512px.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable any',
          },
        ],
      },
      workbox: {
        navigateFallback: '/',
        globPatterns: ['**/*.{css,js,html,svg,png,ico,txt}'],
      },
      devOptions: {
        enabled: true,
        navigateFallbackAllowlist: [/^\//],
      },
      experimental: {
        directoryAndTrailingSlashHandler: true,
      }
    }),
	],
});
