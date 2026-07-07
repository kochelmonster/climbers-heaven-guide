import adapter from '@sveltejs/adapter-static';
import blocklayout from "blocklayout/svelte";
//import { sveltePreprocess, coffeescript } from "svelte-preprocess";
import sveltePreprocess from "svelte-preprocess";

let production = process.env["NODE_ENV"] == 'production';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter({
      // fallback: 'index.html'
    }),
    prerender: {
      handleMissingId: "ignore",
    }
  },
  preprocess: [
    sveltePreprocess({
      sourceMap: !production,
    }),
    blocklayout()
  ]
};

export default config;

