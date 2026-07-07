# climbers-heaven docutils extentions

the paper describes the docutuls extentions for climbers-heaven. Each directive is described in a separate section. First there is a general description of the directive, then you see the call with its default values following by a description of the parameters.

# geomap

Shows a map in the overview section of the document. And display geolocatons of the following sections.

```docutils
.. geomap::
    :levels: 1
    :folder: None
```

levels
: How deep the geolocations are collected. A value of 0 means only locations in the current section are considered. A value of 1 means also locations in the subsections are considered. And so on.

folder
: a folder name in Climbers-Heaven.kml. The geomap will show all visible
objects defined in the folder on the map.

## geolocation

Defines a geolocation of the current section. The geolocation is shown on the geomap. And marked aktive if the section header is prominent.

```docutils
.. geolocation::
    :coords: None
    :marker: None
    :show-title: 0
    :direction: nw
```
coords
: a latitude, longitude pair like 42.0931, 19.1002

marker
: the name of a marker in Climbers-Heaven.kml. The marker has to be in the folder specified in the previous geomap directive.

show-title
: the first zoom level, when the title oft the marker is shown in the map. no means the title will never be shown.

direction
: the position where the title relativle to the marker is shown. nw (north west), n (north), ne (north east), e (east), se (south east),
s (south), sw (south west), w (west).


## routestatistics

Shows a bar chart of the grades of the routes that are described in the following sections.

```docutils
.. routestatistics::
    :levels: 20
    :summary: e
```

levels
: How deep the routes for the statics are collected. A value of 0 means only routes in the current section are considered. A value of 1 means also routes in the subsections are considered. And so on.

summary
: Where to place the number of routes in the chart. e (east) means on the right side of the chart. w (west) means on the left side of the chart.

## imagelist

Displays th given images. If the xmp comment is set in the metadata of the image, the comment is shown as subtitle of the image.

```docutils
.. imagelist:: [comma separated list of path patterns]
   
```

An example for a path list:

```docutils
.. imagelist:: ./pics/*.jpg, ./pics/**/*.jpg
```

The first pattern adds all jpg images in the pics folder the second recusrsively adds all jpgs of any subfolders.

## background

Sets the background image of the current section.

```docutils
.. background:: path-to-image
```

## topo

Defines a topo svg for the current section.

```docutils
.. topo:: path-to-svg
```

## attributes

Set the attributes of a sector.

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
: posible values: granite, limestone, sandstone, quartzite

orientation
: a choice of these values: n, ne, e, se, s, sw, w, nw

season
: best season to climb

sun
: time of the day the sector is in the sun

children
: suitable for children

altitude
: elevation of the sector in meter

approach
: time to approach the sector in minutes

driesafterrain
: how long it takes until the sector is dry after rain

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
: French grade

length
: Length of the route in meters

bolts
: Count of bolts

style
: A choice of these values: fingery, powerful, dyno, tufa, pockets, crack, endurance, technical, mental, tufa, crag

steepness
: A choice of these values: slab, vertical, overhang, roof

other
: A choice of these values dangerous, partly bolted, runout

stars
: Beauty of the route 0-4

created
: Year of creation

creator
: Creator of the route

first-ascent
: first ascent

topo-id
: id in the topo svg. This option is usually not needed because, the
route will be linked to the topo by the name. But if the name is not unique like "Open Project" you can use the topo-id.
