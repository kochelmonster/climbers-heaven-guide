<script lang="coffee">
import Layout from '$lib/Layout.svelte'
import { onMount, onDestroy, tick } from 'svelte'
import { pushState } from "$app/navigation"
import { get, writable } from 'svelte/store'
import { getToastStore } from '@skeletonlabs/skeleton'
import { t } from 'svelte-i18n-lingui'
import FaCopy from 'svelte-icons/fa/FaCopy.svelte'
import FaUndoAlt from 'svelte-icons/fa/FaUndoAlt.svelte'
import {
    DEFAULT_MAP_PROVIDER_URL,
    GOOGLE_MAP_PROVIDER_URL,
    mapProviderUrl,
    resetMapProviderUrl,
    setMapProviderUrl,
    useGoogleMapProviderUrl
} from '$lib/map-provider.js'
import debounce from 'lodash/debounce'

version = __APP_VERSION__

title = "Climbing in Montenegro"
intersector = overview = zoom_handler = content = null
active_id = writable(null)
top_id = first_hash = ""
rating_help = null
map_provider_dialog = false
map_provider_input = DEFAULT_MAP_PROVIDER_URL


toastStore = getToastStore()

ask_for_gps = () ->
    toastStore.trigger
        title: "GPS"
        message: "Please allow the browser to track your location"
        type: "info"
        duration: 5000


update_anchors = () ->
    for anchor in content.querySelectorAll("a.reference.external")
        anchor.setAttribute("target", "_blank")
    return


load = () ->
    return if typeof window == 'undefined'

    [html, gjson, { Overview }, { Intersector }, { ZoomHandler }] = await Promise.all([
        fetch("data/guide.txt"), fetch("data/guide.json"),
        import("$lib/overview.coffee"), import("$lib/intersector.coffee"), 
        import("$lib/zoom.coffee")])
    txt = await html.text()
    content.innerHTML = txt
    update_anchors()
    top_id = document.getElementsByClassName("section")[0].id
    tick()

    gjson = await gjson.json()
    overview = new Overview(gjson)
    intersector = new Intersector(overview, active_id, gjson)
    zoom_handler = new ZoomHandler(overview)
    window.overview = overview

    check_resize()

    # console.log("first hash", first_hash)
    document.getElementById(first_hash.slice(1))?.scrollIntoView()
    first_hash = ""
    
    window.addEventListener("request-gps", ask_for_gps)
    
    splash = document.getElementById("splash")
    splash.classList.add("hidden")
    setTimeout((()->splash.remove()), 300)


close = () ->
    @classList.remove("show")


open_map_provider_dialog = () ->
    map_provider_input = $mapProviderUrl
    map_provider_dialog = true


close_map_provider_dialog = () ->
    map_provider_dialog = false


toggle_map_window = () ->
    zoom_handler?.toggle_map_zoom()


notify_map_provider_change = () ->
    return if typeof window == 'undefined'
    window.dispatchEvent(new CustomEvent("map-provider-changed", detail: $mapProviderUrl))


apply_map_provider = (value) ->
    setMapProviderUrl(value)
    map_provider_input = $mapProviderUrl
    notify_map_provider_change()


update_map_provider_input = (event) ->
    apply_map_provider(event.currentTarget.value)


reset_map_provider = () ->
    resetMapProviderUrl()
    map_provider_input = $mapProviderUrl
    notify_map_provider_change()


copy_google_map_provider = () ->
    useGoogleMapProviderUrl()
    map_provider_input = $mapProviderUrl
    notify_map_provider_change()


check_resize = () ->
    id = get(active_id)

    overview?.update_scroll_margin()
    zoom_handler?.check_orientation()

    intersector?.update_observers()


debounced_check_resize = debounce(check_resize, 50)

on_resize = () -> 
    intersector?.stop_observers()
    debounced_check_resize()



onMount () ->
    first_hash = location.hash
    window.route_rating = route_rating
    load()
    window.addEventListener("request-map-provider-dialog", open_map_provider_dialog)
    window.addEventListener("request-map-window-toggle", toggle_map_window)
    window.addEventListener("resize", on_resize)
    console.log("on load", document.referrer)
    ###
    if document.referrer != "https://www.climbers-heaven.me/"
        toastStore.trigger
            message: "<a href=\"https://www.climbers-heaven.me/\" target=\"_blank\">Book your climbing vacation at Climbers Heaven</a>"
            type: "info"
            duration: 25000
            autohide: true
    ###
    

onDestroy () ->
    overview?.destroy()
    intersector?.destroy()
    zoom_handler?.destroy()
    window?.removeEventListener("request-gps", ask_for_gps)
    window?.removeEventListener("request-map-provider-dialog", open_map_provider_dialog)
    window?.removeEventListener("request-map-window-toggle", toggle_map_window)
    window?.removeEventListener("resize", on_resize)



#console.log("guide_json", guide_json)

route_rating = () ->
    rating_help.classList.add("show")


`$: {`
if overview and $active_id
    title = overview.update($active_id or top_id)
    title = "Climbing in Montenegro" if not title
    new_hash = "#" + $active_id
    pushState(new_hash) if location.hash != new_hash
`}`


</script>

<svelte:head>
    <title>{title}</title> 
</svelte:head>

<div id="marker-popup" class="card shadow-xl p-2" data-popup="markerPopup"></div>

<div id="route_rating" class="popup fixed w-full h-full z-40" on:click={close} bind:this={rating_help}>
    <div class="bottom-0 absolute w-full">
        <div>{$t`Čevapi Rating`}</div>
        <div class="flex flex-row gap-3 shadow-xl p-2">
            <div><img src="cevapi-1.svg" alt={$t`Good`}> {$t`Good`}</div>
            <div><img src="cevapi-2.svg" alt={$t`Very good`}> {$t`Very good`}</div>
            <div><img src="cevapi-3.svg" alt={$t`Superb`}>{$t`Superb`}</div>
        </div>
    </div>
</div>

<div id="map-provider-dialog" class:show={map_provider_dialog} class="fixed inset-0 z-40 p-4">
    <div class="card shadow-xl p-4 map-provider-panel">
        <div class="map-provider-panel-header">
            <button
                type="button"
                class="btn-icon btn-icon-sm variant-filled"
                on:click={close_map_provider_dialog}
                aria-label={$t`Close`}
                title={$t`Close`}
            >
                ✕
            </button>
        </div>
        <p>{$t`Because of license issues we cannot provide a satellite view.`}</p>
        <label class="map-provider-label" for="map-provider-input">{$t`This is the current map provider:`}</label>
        <div class="map-provider-row">
            <input
                id="map-provider-input"
                class="input map-provider-input"
                type="text"
                bind:value={map_provider_input}
                on:input={update_map_provider_input}
                spellcheck="false"
            >
            <button
                type="button"
                class="btn-icon btn-icon-sm variant-filled map-provider-action-button"
                on:click={reset_map_provider}
                aria-label={$t`Reset`}
                title={$t`Reset`}
            >
                <span class="map-provider-icon map-provider-reset-icon"><FaUndoAlt/></span>
            </button>
        </div>
        <p>{$t`For a satellite view you have to enter`}</p>
        <div class="map-provider-row map-provider-helper-row">
            <div class="map-provider-helper">{GOOGLE_MAP_PROVIDER_URL}</div>
            <button
                type="button"
                class="btn-icon btn-icon-sm variant-filled map-provider-action-button"
                on:click={copy_google_map_provider}
                aria-label={$t`Copy`}
                title={$t`Copy`}
            >
                <span class="map-provider-icon map-provider-copy-icon"><FaCopy/></span>
            </button>
        </div>
    </div>
</div>

<Layout>
    <div slot="main" class="main">
        <div class="contents" bind:this={content}></div>
        <div id="padding">Version {version}</div>
    </div>
</Layout>

<style>
#padding {
    height: 65vh;
    padding: 4pt;
    font-size: small;
}

.main {
    min-height: 100%;
}

:global(.leaflet-control-zoom) {
    display: none;
}

:global(.zoomed .leaflet-control-zoom) {
    display: unset;
}
</style>
    