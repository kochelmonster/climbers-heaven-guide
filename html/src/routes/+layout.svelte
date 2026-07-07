<script lang="coffee">
import '../app.css'
import { computePosition, autoUpdate, offset, shift, flip, arrow } from '@floating-ui/dom'
import { storePopup, initializeStores, Toast } from '@skeletonlabs/skeleton'
import { locale } from 'svelte-i18n-lingui'
import { pwaInfo } from 'virtual:pwa-info'
import { onMount } from 'svelte'


storePopup.set({ computePosition, autoUpdate, offset, shift, flip, arrow })
initializeStores()


if document?
	lang = navigator?.language.split("-")[0] || "en"
	document.documentElement.lang = lang
	import("../locales/#{lang}.ts").then ({ messages: msgs }) ->
		locale.set(lang, msgs)

service_worker = pwaInfo and import.meta.env.VITE_AS_PWA?
webManifestLink = ""


onMount () -> 
	if service_worker
		{ registerSW } = await import('virtual:pwa-register')
		registerSW
			immediate: true,
			onRegistered: (r) ->
				if r
					check = () ->
						console.log('Checking for sw update')
						r.update()

					setInterval(check, 24*3600)

				console.log("SW Registered", r)
			
			onRegisterError: (error) ->
				console.log("SW registration error", error)


`$: webManifestLink = service_worker ? pwaInfo.webManifest.linkTag : ''`
</script>

<svelte:head>
	{@html webManifestLink}
</svelte:head>

<slot></slot>
<Toast background="variant-filled-secondary" position="t"/>
