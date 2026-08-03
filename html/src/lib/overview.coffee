###
Handles the overview window
###
import 'leaflet/dist/leaflet.css'
import marker from "$lib/svg/marker.svg?raw"
import cliff from "$lib/svg/mountain.svg?raw"
import L from 'leaflet'
import logo from "$lib/svg/logo.svg?raw"
import MapTools from './MapTools.svelte'


marker_type =
    cliff: cliff
    parking: marker


class Leaflet
    leaflet: null
    contrast_threshold: 145
    contrast_sample_size: 3
    #tile_url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    #tile_url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    
    default_tile_provider_url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    google_tile_provider_url: "https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    map_provider_storage_key: "map-provider-url"
    tile_provider_url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    map_tile_options:
        minZoom: 0
        maxZoom: 20
        maxNativeZoom: 19
        attribution: false
        crossOrigin: true
    
    satellite_tile_url: "http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    satellite_tile_options:
        subdomains:['mt0','mt1','mt2','mt3']
        minZoom: 0
        maxZoom: 20
        maxNativeZoom: 19
        attribution: false
        crossOrigin: true

    map_options:
        center: [42.858534, 19.102059]
        zoom: 8
        zoomControl: false
        attributionControl: false
        doubleClickZoom: false
        minZoom: 7
        maxBounds: L.latLngBounds([41.8091845, 18.4434835], [43.5834689, 20.4155324])
    current_bounds: null

    constructor: () ->
        map_container = document.getElementById("map")
        @marker_box = {}
        @contrast_canvas = document.createElement("canvas")
        @contrast_canvas.width = @contrast_canvas.height = @contrast_sample_size
        @contrast_context = @contrast_canvas.getContext("2d", willReadFrequently: true)
        @contrast_sampling_enabled = !!@contrast_context

        # hack:
        # leaflet zoom control will call focus which will scroll the page
        # avoid that scrolling
        map_container.focus = () ->

        @measure_marker_box(map_container)

        @leaflet = L.map(map_container, @map_options)
        @leaflet.setMaxBounds(@map_options.maxBounds)
        @leaflet.on("zoomend", @on_zoom)
        @leaflet.on("moveend", @schedule_marker_contrast_update)
        window.leaflet = @leaflet

        @add_tools()

        @tile_provider_url = @load_tile_provider_url()
        @replace_tile_layer()
        window.addEventListener("map-provider-changed", @on_map_provider_changed)
        window.addEventListener("map-windowed-change", @on_map_windowed_change)

        @markers = L.layerGroup().addTo(@leaflet)
        @unzoomed()

    destroy: () ->
        window.removeEventListener("map-provider-changed", @on_map_provider_changed)
        window.removeEventListener("map-windowed-change", @on_map_windowed_change)
        @tile_layer?.off("load", @schedule_marker_contrast_update)
        @leaflet.remove()

    add_tools: () ->
        toolbar = L.control({ position: 'bottomright' })
        toolbar.onAdd = () =>
            div = L.DomUtil.create('div', 'leaflet-control leaflet-control-custom flex flex-col ')
            @toolbar = new MapTools target: div
            return div
        toolbar.addTo(@leaflet)

        zoom = L.control.zoom position: 'bottomright'
        zoom.addTo(@leaflet)

        @toolbar.$on("click-gps", @on_gps)
        @toolbar.$on("click-bounds", @on_bounds)
        @toolbar.$on("click-fullscreen", @on_fullscreen)
        @toolbar.$on("click-configure", @on_configure)

    on_configure: () =>
        window.dispatchEvent(new CustomEvent("request-map-provider-dialog"))

    on_map_provider_changed: ({ detail }) =>
        @set_tile_provider_url(detail)

    on_map_windowed_change: ({ detail }) =>
        @toolbar?.$set(fullscreen: !!detail)

    on_fullscreen: () =>
        window.dispatchEvent(new CustomEvent("request-map-window-toggle"))

    normalize_tile_provider_url: (tile_url) ->
        tile_url = (tile_url ? "").trim()
        return @default_tile_provider_url if not tile_url.length

        google_tile_pattern = /^https?:\/\/\{s\}\.google\.com\/vt\/lyrs=s&x=\{x\}&y=\{y\}&z=\{z\}$/
        return @google_tile_provider_url if google_tile_pattern.test(tile_url)

        return tile_url

    load_tile_provider_url: () ->
        stored_tile_provider_url = window.localStorage.getItem(@map_provider_storage_key)
        return @normalize_tile_provider_url(stored_tile_provider_url)

    is_satellite_tile_provider_url: (tile_url) ->
        normalized_tile_provider_url = @normalize_tile_provider_url(tile_url)
        return normalized_tile_provider_url == @google_tile_provider_url

    get_tile_options: (tile_url) ->
        if @is_satellite_tile_provider_url(tile_url)
            return @satellite_tile_options
        return @map_tile_options

    replace_tile_layer: () ->
        @tile_layer?.off("load", @schedule_marker_contrast_update)
        @tile_layer?.remove()
        @tile_layer = L.tileLayer(@tile_provider_url, @get_tile_options(@tile_provider_url))
        @tile_layer.on("load", @schedule_marker_contrast_update)
        @tile_layer.addTo(@leaflet)

    set_tile_provider_url: (tile_url) =>
        tile_url = @normalize_tile_provider_url(tile_url)
        return if tile_url == @tile_provider_url and @tile_layer?

        @tile_provider_url = tile_url
        @replace_tile_layer()

    on_gps: ({ detail }) =>
        if detail
            error = (err) => 
                console.warn("No position found", err)
                switch error.code
                    when error.PERMISSION_DENIED
                        @toolbar.$set({ gps: false })
                        window.dispatchEvent(new CustomEvent("request-gps"))
                        console.warn("No permission to track gps")
                    when error.POSITION_UNAVAILABLE
                        @toolbar.$set({ gps: false })
                        console.warn("No position available")
                    when error.TIMEOUT
                        @toolbar.$set({ gps: false })
                        console.warn("Timeout")
                    when error.UNKNOWN_ERROR
                        console.warn("Unknown error")

                @toolbar.$set({ gps: false })
                console.warn("No permission to track gps", result)

            @watch_id = navigator.geolocation.watchPosition(@gps_changed, error, enableHighAccuracy: true)
        else
            navigator.geolocation.clearWatch(@watch_id)
            if @bullseye
                @leaflet.removeLayer(@bullseye)
                delete @bullseye

    gps_changed: (pos) =>
        console.log("gps", pos.coords)
        @move_gps_marker(pos.coords)

    on_bounds: () =>
        @fit_bounds()

    show: () ->
        @leaflet.getContainer().classList.add("show")

    zoomed: () ->
        map = @leaflet
        map.dragging.enable()
        map.touchZoom.enable()
        map.scrollWheelZoom.enable()
        map.boxZoom.enable()
        map.keyboard.enable()
        map.tap.enable() if (map.tap) 
        document.getElementById('map').style.cursor = 'grab'

    unzoomed: () ->
        map = @leaflet
        map.dragging.disable()
        map.touchZoom.disable()
        map.scrollWheelZoom.disable()
        map.boxZoom.disable()
        map.keyboard.disable()
        map.tap.disable() if (map.tap) 
        document.getElementById('map').style.cursor = 'default'

    update_size: () =>
        try
            @leaflet.invalidateSize(true)
        catch e
            console.warn("error update_size", e)

    measure_marker_box: (map_container) ->
        for k, v of marker_type
            map_container.innerHTML += """
                                       <div id='tmp' class='leaflet-container leaflet-marker-icon' 
                                           style='visibility:hidden; position:absolute'>
                                           <div class="marker-container">
                                               <div class="icon">#{v}</div>
                                           </div>
                                       </div>"""
            tmp = document.getElementById("tmp")
            r = tmp.getBoundingClientRect()
            @marker_box[k] = [r.width, r.height]
            tmp.remove()

    move_gps_marker: (coords) ->
        coords = [coords.latitude, coords.longitude]
        console.log("move coord", coords)

        if @bullseye
            @bullseye.setLatLng(coords)
            return

        bullseye = document.getElementById("button-gps").innerHTML
        html = """<div class="marker-container"><div class="icon">#{bullseye}</div></div>"""
        icon = L.divIcon
            html: html
            className: "bullseye"
            iconSize: [20, 20]
            iconAnchor: [10, 10]
        @bullseye = L.marker(coords, icon: icon)
        @bullseye.addTo(@leaflet)

    create_marker: (obj, type) ->
        title = @get_title(obj.href) ? ""
        klass_name = "marker-" + obj.type

        styles = ""
        switch obj.title_pos
            when "N" then styles = ""

        direction = obj.direction ? ""

        zoom = 0
        if obj.show_title == "no"
            direction = "hidden"
        else
            if parseInt(obj.show_title) > 0
                direction += " zoom-" + obj.show_title

        container_style = ""
        if obj.color
            container_style += """ style="--marker-custom-color:#{obj.color}" """

        
        a_attribute = if obj.href 
            """ id="marker-#{obj.href}" href="##{obj.href}" """
        else 
            ""

         html = """<a class="marker-container"#{a_attribute}#{container_style}>
             <div class="marker-title #{direction}">#{title}</div>
               <div class="icon">#{marker_type[type]}</div></a>"""

        box = anchor = @marker_box[type]
        switch type
            when "parking"
                anchor = [box[0]/2, box[1]]
            when "cliff"
                anchor = [box[0], box[1]]

        icon = L.divIcon
            html: html
            className: klass_name
            iconSize: @marker_box[type]
            iconAnchor: anchor

        return L.marker obj.coords,
            icon: icon
            title: title

    on_zoom: () =>
        c = @leaflet.getContainer()
        c.querySelectorAll(".zhide").forEach (e) -> e.classList.remove("zhide")
        for i in [0...@leaflet.getZoom()]
            c.querySelectorAll(".zoom-"+i).forEach (e) -> e.classList.add("zhide")
        @schedule_marker_contrast_update()

    schedule_marker_contrast_update: () =>
        return if @contrast_update_scheduled

        @contrast_update_scheduled = true
        requestAnimationFrame(() =>
            @contrast_update_scheduled = false
            @refresh_marker_contrast()
        )

    refresh_marker_contrast: () =>
        container = @leaflet?.getContainer()
        return if not container

        for marker_element in container.querySelectorAll(".leaflet-marker-icon .marker-container")
            marker_element.classList.remove("contrast-dark-bg", "contrast-light-bg")
            marker_element.classList.add(@marker_contrast_mode(marker_element))

    marker_contrast_mode: (marker) ->
        return @fallback_marker_contrast_mode() if not @contrast_sampling_enabled

        luminances = []
        for point in @marker_sample_points(marker)
            luminance = @sample_background_luminance(point.x, point.y)
            luminances.push(luminance) if luminance?

        return @fallback_marker_contrast_mode() if not luminances.length

        average = luminances.reduce(((sum, value) -> sum + value), 0) / luminances.length
        if average < @contrast_threshold then "contrast-dark-bg" else "contrast-light-bg"

    fallback_marker_contrast_mode: () ->
        if @is_satellite_tile_provider_url(@tile_provider_url)
            return "contrast-dark-bg"
        return "contrast-light-bg"

    marker_sample_points: (marker) ->
        samples = []

        for element in [marker.querySelector(".icon"), marker.querySelector(".marker-title:not(.zhide)")]
            continue if not element

            rect = element.getBoundingClientRect()
            continue if rect.width == 0 or rect.height == 0

            samples.push
                x: rect.left + rect.width / 2
                y: rect.top + rect.height / 2

        return samples

    sample_background_luminance: (x, y) ->
        tile = @find_loaded_tile_at_point(x, y)
        return null if not tile

        rect = tile.getBoundingClientRect()
        return null if not rect.width or not rect.height or not tile.naturalWidth or not tile.naturalHeight

        sample_size = @contrast_sample_size
        sx = Math.round((x - rect.left) / rect.width * tile.naturalWidth - sample_size / 2)
        sy = Math.round((y - rect.top) / rect.height * tile.naturalHeight - sample_size / 2)
        sx = Math.max(0, Math.min(tile.naturalWidth - sample_size, sx))
        sy = Math.max(0, Math.min(tile.naturalHeight - sample_size, sy))

        try
            @contrast_context.clearRect(0, 0, sample_size, sample_size)
            @contrast_context.drawImage(tile, sx, sy, sample_size, sample_size, 0, 0, sample_size, sample_size)
            pixels = @contrast_context.getImageData(0, 0, sample_size, sample_size).data
        catch error
            console.warn("Marker contrast sampling disabled", error)
            @contrast_sampling_enabled = false
            return null

        luminance = 0
        for index in [0...pixels.length] by 4
            luminance += 0.2126 * pixels[index] + 0.7152 * pixels[index + 1] + 0.0722 * pixels[index + 2]

        return luminance / (pixels.length / 4)

    find_loaded_tile_at_point: (x, y) ->
        for tile in @leaflet.getContainer().querySelectorAll(".leaflet-tile-loaded")
            rect = tile.getBoundingClientRect()
            if rect.left <= x <= rect.right and rect.top <= y <= rect.bottom
                return tile

        return null

    fit_bounds: () ->
        return if not @current_bounds
        @leaflet.fitBounds @current_bounds,
            paddingTopLeft: [10, @marker_box["cliff"][1]+10]
            paddingBottomRight: [10, 10]
        @on_zoom()

    get_title: (id) ->
        return document.getElementById(id)?.querySelector("h1,h2,h3,h4")?.innerText

    update: (data) ->
        @markers.clearLayers()
        @current_bounds = L.latLngBounds()
        for obj in data.objects
            switch obj.type
                when "area", "sector"
                    @markers.addLayer(@create_marker(obj, "cliff"))
                    @current_bounds.extend(obj.coords)

                when "parking"
                    @markers.addLayer(@create_marker(obj, "parking"))
                    @current_bounds.extend(obj.coords)

                when "access"
                    @markers.addLayer(L.polyline(obj.coords))
                    for c in obj.coords
                        @current_bounds.extend(c)

        @fit_bounds()
        @schedule_marker_contrast_update()

        check_fit_bounds = () =>
            # a hack of a leaflet bug?
            # console.log("check_fit_bounds", @current_bounds, @leaflet.getBounds())
            @fit_bounds()
            @schedule_marker_contrast_update()

        setTimeout(check_fit_bounds, 500)

    show_location: (id) ->
        @leaflet.getContainer().querySelectorAll(".active").forEach (e) -> e.classList.remove("active")
        m = document.getElementById("marker-"+id)
        m?.classList.add("active")


# load all tiles needed for the standard maps
class PreloadLeaflet
    leaflet: null
    tile_url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    tile_options:
        minZoom: 0
        maxZoom: 20
        maxNativeZoom: 19
        attribution: false
    map_options:
        center: [42.858534, 19.102059]
        zoom: 8
        zoomControl: false
        attributionControl: false
        doubleClickZoom: false
        boxZoom: false
        dragging: false
        trackResize: false
        keyboard: false
        scrollWheelZoom: false
        tapHold: false
        zoomAnimation: false
        fadeAnimation: false
        minZoom: 7
        maxBounds: L.latLngBounds([41.8091845, 18.4434835], [43.5834689, 20.4155324])

    constructor: (data) ->
        @geo_data = (v.geomap for _, v of data when v.geomap)

        @container = document.createElement("div")
        @container.style.visibility = "hidden"
        @container.style.position = "absolute"
        @container.style.zIndex = -1
        @container.style.width = "100vw"
        @container.style.height = "100vh"
        document.body.appendChild(@container)

        @leaflet = L.map(@container, @map_options)
        @leaflet.setMaxBounds(@map_options.maxBounds)

        @last_bounds = @map_options.maxBounds

        @tiles = L.tileLayer(@tile_url, @tile_options).addTo(@leaflet)
        @tiles.on("load", @update)

        @update()

    update: () =>
        clearTimeout(@timeout) if @timeout?
        while @geo_data.length
            data = @geo_data.shift()
            current_bounds = L.latLngBounds()

            for obj in data.objects
                if obj.type in ["area", "sector", "parking"]
                    current_bounds.extend(obj.coords)

                else if obj.type == "access"
                    for c in obj.coords
                        current_bounds.extend(c)

            if current_bounds
                continue if @last_bounds.equals(current_bounds)
                @last_bounds = current_bounds
                @timeout = setTimeout(@update, 1000)
                @leaflet.fitBounds current_bounds,
                    paddingTopLeft: [10, 60]
                    paddingBottomRight: [10, 10]
                break

        if not @geo_data.length 
            # done loaded all tiles
            requestAnimationFrame () =>
                console.log("!remove preloader")
                @leaflet.remove()
                @container.remove()
                @leaflet = @container = null
            return


export class Overview
    leaflet: null
    container: null
    active_element:
        type: null
        id: null
        element: null

    constructor: (@guide_json) ->
        @container = document.getElementById("overview-container")
        @popup = document.getElementById("marker-popup")
        @leaflet = new Leaflet()
        @container.addEventListener("click", @on_click)
        @update_size()
        @find_topo_aspect()
        new PreloadLeaflet(@guide_json) if import.meta.env.VITE_AS_PWA?

    find_nearest_sector: () ->
        found_pos = (pos) =>
            nearest_id = null
            nearest_dist = 100000000000
            crd = pos.coords

            for k, v of @guide_json
                if v.coords?
                    dist = Math.abs(v.coords[0] - crd.latitude) + Math.abs(v.coords[1] - crd.longitude)
                    console.log("check", k, v.coords, crd, dist)
                    if dist < nearest_dist
                        nearest_id = k
                        nearest_dist = dist
                        console.log("!nearest id", k)
            
            location.hash = "#"+nearest_id if nearest_id 

        navigator.geolocation.getCurrentPosition(found_pos, ()->, {enableHighAccuracy: true})
        
    destroy: () ->
        @container.removeEventListener("click", @on_click)
        @leaflet.destroy()

    find_topo_aspect: () ->
        # find the aspect ratio of the widest topo
        @smallest_ratio = 5000
        for topo in @container.getElementsByClassName("topo")
            width = topo.firstElementChild.width.baseVal.value
            height = topo.firstElementChild.height.baseVal.value
            ratio = height / width
            @smallest_ratio = ratio if ratio < @smallest_ratio
        return

    getRect: () ->
        return @container.getBoundingClientRect()

    update_scroll_margin: () =>
        br = document.getElementById("breadcrump")
        br_height = br.getBoundingClientRect().height
        br_width = br.getBoundingClientRect().width
        if not br_height
            br.innerHTML = "HH"
            br_height = br.getBoundingClientRect().height
            br_width = br.getBoundingClientRect().width
            br.innerHTML = ""

        height = Math.min(br_width * @smallest_ratio, window.innerHeight * 0.45)
        @container.style.height = (height+br_height)+"px"
        rect = @container.getBoundingClientRect()
        
        for e in document.getElementsByClassName("after-overview-container")
            e.style.scrollMarginTop = rect.height + "px"
        return

    update_size: () =>
        @leaflet.update_size()

    last_id: null

    update: (id) ->
        return if id == @last_id
        @last_id = id

        document.querySelectorAll(".active-route").forEach (element) ->
            element.classList.remove "active-route" 

        title = @show_breadcrumbs(id)
        @update_size()

        data = @guide_json[id] ? {}
        # console.log("update_overview", id, data, @active_element) 

        @show_map(data["geomap"])
        @show_topo(data["topo"])

        if (route = data["route"])
            @clear_active_topo()
            document.getElementById(id).classList.add "active-route"
            document.getElementById(route["id"])?.classList.add("active-topo")
            use_ = @active_element.element.querySelector("use")
            use_.setAttribute("xlink:href", "#"+route["id"])
            title = route["name"] + " " + route["grade"]+"/"+title

        if (location = data["geolocation"])
            @leaflet.show_location(location)

        return title

    show_topo: (topo) ->
        return if not topo
        return if @active_element.type == "topo" and @active_element.id == topo

        @clear_active()
        @clear_active_topo()

        @active_element.type = "topo"
        @active_element.id = topo
        @active_element.element = te = document.getElementById(topo)
        te.classList.add("show")

    on_click: (e) =>
        @popup.classList.remove("show")
        return if @active_element.type != "topo"

        # show a popup

        ancestor = e.target.closest("[href]")
        return if not ancestor

        is_zoomed = ancestor.closest(".zoom-able.zoomed")
        return if not is_zoomed

        id = ancestor?.getAttribute("href")?.slice(1)
        data = @guide_json[id] ? {}

        popup = document.getElementById("marker-popup")
        popup.innerHTML = data?.route?.name + " " + data?.route?.grade

        @popup.style.left = e.clientX + "px"
        @popup.style.top = e.clientY + "px"
        @popup.classList.add("show")

    clear_active_topo: () ->
        @container.querySelectorAll(".active-topo").forEach (e) -> e.classList.remove("active-topo")

    show_map: (geomap) ->
        return if not geomap
        return if @active_element.type == "geomap" and @active_element.id == geomap.id

        @clear_active() if @active_element.type != "geomap"

        @active_element.type = "geomap"
        @active_element.id = geomap.id
        @active_element.element = @leaflet

        @leaflet.update(geomap)
        @leaflet.show()

    show_breadcrumbs: (id) ->
        br = document.getElementById("breadcrump")

        start = document.getElementById(id)
        if not start
            br.innerHTML = ""
            return
        
        sections = []
        parent = start.parentElement
        while parent
            if parent.classList.contains("section")
                sections.push(parent)

            parent = parent.parentElement

        sections.pop() # the climbing areas
        sections.reverse()

        title = []
        if sections.length > 0
            breadcrumbs = ["""<li class="crump"><a href="#the-climbing-areas" class="anchor icon">#{logo}</a></li>"""]
            for s in sections
                header = s.querySelector("h1, h2, h3, h4")
                if header
                    breadcrumbs.push("""<li class="crump"><a href="##{s.id}" class="anchor">#{header.textContent}</a></li>""")
                    title.push(header.textContent)

            br.innerHTML = breadcrumbs.join("""<li class="crump-separator">></li>""")
        else
            br.innerHTML = ""

        title.reverse()
        return title.join("/")

    clear_active: () ->
        @container.querySelectorAll(".show").forEach (e) -> e.classList.remove("show", "zoomed")
        window.dispatchEvent(new Event('unzoom'))


