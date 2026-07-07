import { get } from 'svelte/store'

###
Findes the active topic
###

export class Intersector
    active: null
    enabled: 1
    header_height: 30

    constructor: (@overview, @active, @gjson) ->
        @intersecting_elements = {}

    destroy: () ->
        @stop_observers()

    stop_observers: () ->
        @intersection_observer1?.disconnect()
        @intersection_observer2?.disconnect()
        @intersection_observer1 = @intersection_observer2 = null

    update_observers: () ->
        @stop_observers()
        
        top = parseInt(@overview.getRect().height) - 5;
        bottom = window.innerHeight - top - @header_height
        options =
            root: null
            rootMargin: "#{-top}px 0px #{-bottom}px 0px"
            threshold: 0
        @intersection_observer1 = new IntersectionObserver(@intersect, options)
        
        bottom = window.innerHeight - @header_height
        options =
            root: null
            rootMargin: "0px 0px #{-bottom}px 0px"
            threshold: 0
        @intersection_observer2 = new IntersectionObserver(@intersect, options)
        # console.log("update observer", @intersection_observer1, @intersection_observer2)

        for e in document.getElementsByClassName("section")
            if e.classList.contains("before-overview-container")
                @intersection_observer2.observe(e)
            else
                @intersection_observer1.observe(e)

        for e in document.getElementsByClassName("route")
            @intersection_observer1.observe(e)


    calc_depth: (el) ->
        count = 0
        parent = el.parentNode
        while parent
            count++
            parent = parent.parentNode
        return count

    intersect: (changes) =>
        for c in changes
            if c.isIntersecting
                @intersecting_elements[c.target.id] = c.target
                c.target.depth = @calc_depth(c.target)
            else
                delete @intersecting_elements[c.target.id]

        depth = 0
        top = 0
        for id, c of @intersecting_elements
            if c.depth > depth or c.depth == depth and top < c.getBoundingClientRect().top
                depth = c.depth
                top = c.getBoundingClientRect().top
                te = c

        # console.log("intersect", te, @intersecting_elements)
        @active.set(te.id) if te
