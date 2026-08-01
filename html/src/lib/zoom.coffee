"""
Handles zooming of object when you double click or tap it
"""
import actual from 'actual'
import Panzoom from '@panzoom/panzoom'

getcm = actual.as("cm")

lastTap = 0
timeout = null
detectDoubleTap = (event) ->
    curTime = new Date().getTime()
    tapLen = curTime - lastTap
    if tapLen < 500 and tapLen > 0 and not event.touches.length
        touch = event.changedTouches[0]
        nevent = new Event('dblclick', bubbles: true)
        nevent.clientX = touch.clientX
        nevent.clientY = touch.clientY
        nevent.screenX = touch.screenX
        nevent.screenY = touch.screenY
        event.target.dispatchEvent(nevent)
        event.preventDefault()
        clearTimeout(timeout)
    else
        if not event.touches.length
            timeout = setTimeout((() -> clearTimeout(timeout)), 500)    
            lastTap = curTime


export class ZoomHandler
    zoomed_element: null
    panzoom: null

    constructor: (@overview) ->
        @popup = document.getElementById("marker-popup")
        document.body.addEventListener('touchend', detectDoubleTap)
        document.body.addEventListener('dblclick', @on_zoom)
        window.addEventListener('unzoom', @stop_panzoom)

    destroy: () ->
        document.body.removeEventListener('touchend', detectDoubleTap)
        document.body.removeEventListener('dblclick', @on_zoom)
        window.removeEventListener('unzoom', @stop_panzoom)

    on_zoom: (e) =>
        e.stopPropagation()
        return if getcm("height") < 15
            
        element = e.target
        while element
            if element.classList.contains 'zoom-able'
                if element.classList.contains 'zoomed'
                    @stop_panzoom()
                else
                    @start_panzoom(element)

            element = element.parentElement

    toggle_map_zoom: () =>
        if @zoomed_element?.id == "map"
            @stop_panzoom()
            return

        map = document.getElementById("map")
        @start_panzoom(map) if map

    emit_map_windowed_change: (state) ->
        window.dispatchEvent(new CustomEvent("map-windowed-change", detail: !!state))
           
    start_panzoom: (element) =>
        @stop_panzoom()

        # console.log("start zoom")
        @zoomed_element = element   
        @zoomed_element.classList.add('zoomed')
        if @zoomed_element.id == "map"
            @emit_map_windowed_change(true)
            @overview.leaflet.zoomed()
            setTimeout((() =>
                @overview.leaflet.update_size()
                @overview.leaflet.fit_bounds()), 100)
            return

        @panzoom = Panzoom element.firstElementChild,
            contain: ""
            handleStartEvent: (event) =>
                event.preventDefault()
                event.stopPropagation()
                @popup.classList.remove("show")
  
        @zoomed_element.classList.add 'zoomed'
        @zoomed_element.addEventListener('wheel', @wheel_event)
        
    stop_panzoom: () =>
        return if not @zoomed_element

        console.log("stop zoom")

        @popup.classList.remove("show")
        el = @zoomed_element
        @zoomed_element = null
        el.classList.remove('zoomed')
        if el.id == "map"
            @emit_map_windowed_change(false)
            setTimeout((() =>
                @overview.leaflet.update_size()
                @overview.leaflet.fit_bounds()
                @overview.leaflet.unzoomed()), 100)
            return

        @panzoom.destroy()
        @panzoom = null
        el.removeEventListener('wheel', @wheel_event)
        el.firstElementChild.style = ""
        el.style = ""

    wheel_event: (e) =>
        @panzoom.zoomWithWheel(e)

    check_orientation: () =>
        if @overview.getRect().top > window.innerHeight  
            # no landscape mode if overview is not at the screen
            document.documentElement.classList.remove("landscape")
            @stop_panzoom()
            return

        document.querySelector(".popup.show")?.classList.remove("show")

        is_landscape = window.innerWidth > window.innerHeight
        was_landscape = document.documentElement.classList.contains("landscape")

        if is_landscape != was_landscape and @overview.last_id           
            document.getElementById(@overview.last_id)?.scrollIntoView()

        if getcm("height") < 15 and is_landscape
            document.documentElement.classList.add("landscape")
            element = document.querySelector(".zoomed")
            return if element
            element = document.querySelector(".zoom-able.show")
            @start_panzoom(element) if element
        else
            document.documentElement.classList.remove("landscape")
            @stop_panzoom()

        

