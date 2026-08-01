<script lang="coffee">
import Layout from '$lib/Layout.svelte'
import { onMount, onDestroy, tick } from 'svelte'
import { pushState } from "$app/navigation"
import { get, writable } from 'svelte/store'
import { getToastStore } from '@skeletonlabs/skeleton'
import { t } from 'svelte-i18n-lingui'
import debounce from 'lodash/debounce'

version = __APP_VERSION__

title = "Climbing in Montenegro"
intersector = overview = zoom_handler = content = null
active_id = writable(null)
top_id = first_hash = ""
rating_help = null


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
    window.addEventListener("resize", on_resize)
    console.log("on load", document.referrer)
    if document.referrer != "https://www.climbers-heaven.me/"
        toastStore.trigger
            message: "<a href=\"https://www.climbers-heaven.me/\" target=\"_blank\">Book your climbing vacation at Climbers Heaven</a>"
            type: "info"
            duration: 25000
            autohide: true
    

onDestroy () ->
    overview?.destroy()
    intersector?.destroy()
    zoom_handler?.destroy()
    window?.removeEventListener("request-gps", ask_for_gps)
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
    