# Climbers-Heaven Docutils Extensions

This guide documents the docutils extensions used by Climbers-Heaven. Each directive has its own section with a short description, a usage example with default values, and a list of the available parameters.

## geomap

Shows a map in the overview section and displays the geolocations collected from the current section and its subsections.

```docutils
.. geomap::
    :levels: 1
    :folder: None
```

levels
: Controls how deeply geolocations are collected. A value of 0 includes only the current section. A value of 1 also includes the subsections, and so on.

folder
: The name of a folder in Climbers-Heaven.kml. The geomap shows all visible objects defined in that folder.

## geolocation

Defines the geolocation of the current section. The location appears on the geomap and is marked active when the section heading is prominent.

```docutils
.. geolocation::
    :coords: None
    :marker: None
    :show-title: 0
    :direction: nw
```

coords
: A latitude and longitude pair such as 42.0931, 19.1002.

marker
: The name of a marker in Climbers-Heaven.kml. The marker must be in the folder specified by the preceding geomap directive.

show-title
: The first zoom level at which the marker title is shown on the map. Use no if the title should never be shown.

direction
: The position of the title relative to the marker. Valid values are nw (north west), n (north), ne (north east), e (east), se (south east), s (south), sw (south west), and w (west).

## routestatistics

Shows a bar chart of the grades of the routes described in the following sections.

```docutils
.. routestatistics::
    :levels: 20
    :summary: e
```

levels
: Controls how deeply routes are collected for the statistics. A value of 0 includes only the current section. A value of 1 also includes the subsections, and so on.

summary
: Controls where the total number of routes appears in the chart. e (east) places it on the right side, and w (west) places it on the left side.

## imagelist

Displays the given images. If an XMP comment is set in the image metadata, the comment is shown as the image subtitle.

```docutils
.. imagelist:: [comma separated list of path patterns]
   
```

An example path list:

```docutils
.. imagelist:: ./pics/*.jpg, ./pics/**/*.jpg
```

The first pattern adds all jpg images in the pics folder. The second pattern recursively adds all jpg images in any subfolder.

## background

Sets the background image for the current section.

```docutils
.. background:: path-to-image
```

## topo

Defines an SVG topo for the current section.

```docutils
.. topo:: path-to-svg
```

## attributes

Sets the attributes of a sector.

```docutils

.. attributes::
    :rock: limestone
    :orientation: None
    :season: None
    :sun: None
    :children: yes
    :altitude: None
    :approach: None
    :driesafterrain: None
```

rock
: Possible values: granite, limestone, sandstone, quartzite.

orientation
: Possible values: n, ne, e, se, s, sw, w, nw.

season
: The best season for climbing.

sun
: The time of day when the sector is in the sun.

children
: Indicates whether the sector is suitable for children.

altitude
: The elevation of the sector, in meters.

approach
: The approach time to the sector, in minutes.

driesafterrain
: How long the sector takes to dry after rain.

## route

Describes a route.

```docutils
.. route:: Name of the route
    :grade: None
    :length: None
    :bolts: None
    :style: None
    :steepness: None
    :other: None
    :stars: None
    :created: None
    :creator: None
    :first-ascent: None
    :topo-id: None
```

grade
: The French grade.

length
: The route length in meters.

bolts
: The number of bolts.

style
: Possible values: fingery, powerful, dyno, tufa, pockets, crack, endurance, technical, mental, crag.

steepness
: Possible values: slab, vertical, overhang, roof.

other
: Possible values: dangerous, partly bolted, runout.

stars
: The route quality from 0 to 4 stars.

created
: The year the route was created.

creator
: The creator of the route.

first-ascent
: The climber or team that made the first ascent.

topo-id
: The ID used in the topo SVG. This option is usually not needed because the route is linked to the topo by name. Use it only when the route name is not unique, such as Open Project.
