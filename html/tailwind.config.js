// @ts-check
import { join } from 'path';
import { climbersHeavenTheme } from './climbers-heaven-theme';

// 1. Import the Skeleton plugin
import { skeleton } from '@skeletonlabs/tw-plugin';

/** @type {import('tailwindcss').Config} */
export default {
	// 2. Opt for dark mode to be handled via the class method
	darkMode: 'class',
	content: [
		'./src/**/*.{html,js,svelte,ts,coffee}',
		'./static/**/*.txt',
		// 3. Append the path to the Skeleton package
		join(require.resolve(
			'@skeletonlabs/skeleton'),
			'../**/*.{html,js,svelte,ts}'
		)
	],
	theme: {
		fontFamily: {
			sans: ["Verdana", "Geneva", "Tahoma", "sans-serif"]
		},
		extend: {
			"maxWidth": {
				"maximal": "1024px"
			}
		},
	},
	plugins: [
		// 4. Append the Skeleton plugin (after other plugins)
		skeleton({
			themes: {
				custom: [
					climbersHeavenTheme
				]
			}
		})
	]
}
