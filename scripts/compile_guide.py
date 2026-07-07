"""
To run this script, you need to install the following packages:

- conda install docutils
- const install Pillow
- conda install svgelements
- pip install fastkml
- pip install levenshtein
- pip install htmlmin
"""
import logging
import warnings
import sys
import pathlib
import json
import svgelements
import drawsvg as draw
import unicodedata
import glob
import io
import tempfile
import mimetypes
import base64
import htmlmin
from PIL import Image
from collections import defaultdict
from docutils import nodes
from docutils.transforms import Transform
from docutils.parsers.rst import Directive, directives
from docutils.core import publish_parts
from docutils.writers.html4css1 import HTMLTranslator, Writer
with warnings.catch_warnings(action="ignore"):
    from fastkml import kml
from Levenshtein import distance
from eightanu_scraper import find_route_url

__DIR__ = pathlib.Path(__file__).parent
from images import MImageCollector, MImageHTMLTranslator, write_images

TOPO_ASPECT_RATIO = 0.56  # h / w
ASPECT_MARGIN = 25


tempdir = None

with open(__DIR__ / "kompass.svg", "r") as file:
    KOMPASS = file.read()
    KOMPASS = KOMPASS.replace(
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>', ""
    )


with open(__DIR__ / "season.svg", "r") as file:
    SEASON = file.read()
    SEASON = SEASON.replace(
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>', ""
    )

CEVAPI_RATING = {"1": "Good", "2": "Very good", "3": "Superb"}


LINK = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512" class="svelte-c8tyih"><path d="M576 24v127.984c0 21.461-25.96 31.98-40.971 16.971l-35.707-35.709-243.523 243.523c-9.373 9.373-24.568 9.373-33.941 0l-22.627-22.627c-9.373-9.373-9.373-24.569 0-33.941L442.756 76.676l-35.703-35.705C391.982 25.9 402.656 0 424.024 0H552c13.255 0 24 10.745 24 24zM407.029 270.794l-16 16A23.999 23.999 0 0 0 384 303.765V448H64V128h264a24.003 24.003 0 0 0 16.97-7.029l16-16C376.089 89.851 365.381 64 344 64H48C21.49 64 0 85.49 0 112v352c0 26.51 21.49 48 48 48h352c26.51 0 48-21.49 48-48V287.764c0-21.382-25.852-32.09-40.971-16.97z"></path></svg>
""".strip()

font_size = "1.1rem"
big_font_size = "1.5rem"


def name_to_id(name):
    return (
        unicodedata.normalize("NFKD", name)
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
        .replace(" ", "-")
        .replace(":", "-")
        .replace("’", "-")
    )


def save_image_url_to_file(image_url, file_path, rcrop, embedded=False):
    if not image_url.startswith("data:image"):
        raise ValueError("Only data URLs are supported.")

    mimetype = image_url.split(";")[0].split(":")[1]
    suffix = mimetypes.guess_extension(mimetype)
    file_path = file_path.with_suffix(".avif")

    data = image_url.split(",")[1]
    data = base64.b64decode(data)
    bytes_io = io.BytesIO(data)
    image = Image.open(bytes_io)
    # print("topo image",  image.size)

    image = image.crop(rcrop)
    image = image.convert('RGB')

    if embedded:
        buffered = io.BytesIO()
        image.save(buffered, format="png")
        img_str = base64.b64encode(buffered.getvalue())
        return "data:image/png;base64," + img_str.decode("utf-8")

    image.save(file_path, optimize=True, quality=90)

    # with open(file_path, "wb") as file:
    #    file.write(base64.b64decode(data))

    return file_path


class Collector:
    def __init__(self, start_level, end_level):
        self.start_level = start_level
        self.end_level = end_level


class RouteStatisticsNode(nodes.Element):
    pass


class RouteStatistics(Directive):
    required_arguments = 0
    optional_arguments = 0
    has_content = False
    option_spec = {
        "levels": directives.nonnegative_int,
        "summary": directives.value_or(("w", "e", "n"), lambda x: "e"),
    }
    levels = 1

    def run(self):
        self.options.setdefault("levels", 20)
        return [RouteStatisticsNode(self.block_text, **self.options)]


directives.register_directive("routestatistics", RouteStatistics)


class RouteStatisticsCollector(Collector):
    def __init__(self, start_level, end_level, summary):
        super().__init__(start_level, end_level)
        self.summary = summary
        self.routes = []

    def to_json(self):
        result = defaultdict(int)
        for route in self.routes:
            result[route["grade"]] += 1

        return {
            "type": "routestatistics",
            "routes": dict(result),
        }

    def draw(self):
        # Collect route grades and their counts
        route_grades = defaultdict(int)
        for route in self.routes:
            route_grades[route["grade"].split("/")[-1].strip()] += 1

        # Sort the grades in ascending order
        sorted_grades = sorted(route_grades.items(), key=lambda x: x[0])

        # Calculate the maximum count for scaling the bar heights
        max_count = max(route_grades.values())

        # Set the dimensions and spacing for the bar chart
        bar_width = 30
        bar_spacing = 10
        chart_height = 200
        chart_width = (bar_width + bar_spacing) * len(sorted_grades)

        offset = 22

        # Create a new drawing for the bar chart
        chart = draw.Drawing(chart_width, chart_height + offset + 20)
        chart.view_box = f"0 0 {chart_width} {chart_height+40}".split(" ")

        # Draw each bar in the chart

        # Calculate the sum of all routes
        total_routes = sum(route_grades.values())

        if self.summary == "w":
            x = 10
            text_anchor = "start"
        else:
            x = chart_width - 10
            text_anchor = "end"

        if self.summary != "n":
            # Draw the sum of all routes in the upper right corner
            chart.append(
                draw.Text(
                    "\u03A3 = " + str(total_routes),
                    big_font_size,
                    x=x,
                    y=offset - 2,
                    text_anchor=text_anchor,
                )
            )

        x = 0
        for grade, count in sorted_grades:
            # Calculate the height of the bar based on the count
            bar_height = (count / max_count) * chart_height

            # Draw the bar
            chart.append(
                draw.Rectangle(
                    x,
                    offset + chart_height - bar_height,
                    bar_width,
                    bar_height,
                    fill="blue",
                    **{"class": "grade-" + grade.replace("+", "p")},
                )
            )

            # Draw the grade label below the bar
            chart.append(
                draw.Text(
                    str(count),
                    font_size,
                    x=x + bar_width / 2,
                    y=offset - 2 + chart_height - bar_height,
                    text_anchor="middle",
                )
            )

            # Draw the grade label below the bar
            chart.append(
                draw.Text(
                    grade,
                    font_size,
                    x=x + bar_width / 2,
                    y=chart_height + offset + 15,
                    text_anchor="middle",
                )
            )

            # Move to the next position for the next bar
            x += bar_width + bar_spacing

        # Return the bar chart as SVG
        return chart.as_svg(header="")


class GeoLocationNode(nodes.Element):
    pass


def coords(argument):
    return [float(a) for a in argument.split(",")]


def yesno(argument):
    return directives.choice(argument, ("yes", "no"))


class GeoLocation(Directive):
    required_arguments = 0
    optional_arguments = 0
    has_content = True
    option_spec = {
        "coords": coords,
        "marker": directives.unchanged,
        "show-title": directives.value_or(("yes", "no"), directives.nonnegative_int),
        "color": directives.unchanged,
        "direction": directives.value_or(
            ("n", "ne", "e", "se", "s", "sw", "w", "nw"), "nw"
        ),
    }

    def run(self):
        return [GeoLocationNode(self.block_text, **self.options)]


directives.register_directive("geolocation", GeoLocation)


class GeoMapNode(nodes.Element):
    pass


class GeoMap(Directive):
    required_arguments = 0
    optional_arguments = 0
    has_content = False
    option_spec = {
        "levels": directives.nonnegative_int,
        "folder": directives.unchanged,
        "style": directives.value_or(("map", "satellite"), "map")
    }
    levels = 1

    def run(self):
        objs = []
        folder = ""
        if "folder" in self.options:
            folder = self.options["folder"]
            try:
                objs = geo_data[folder]
            except KeyError:
                raise self.error(f"Folder '{folder}' not found.")

        return [GeoMapNode(self.block_text, objs=objs, folder=folder,
                           style=self.options.get("style", "map"))]


directives.register_directive("geomap", GeoMap)


class GeoMapCollector(Collector):
    folder = ""
    style = "map"

    def __init__(self, id_, start_level, end_level, objects):
        super().__init__(start_level, end_level)
        self.id = id_
        self.objects = objects

    def to_json(self):
        return {
            "type": "geomap",
            "id": self.id,
            "style": self.style,
            "objects": self.objects
        }

    def __repr__(self):
        return f"GeoMap({self.folder})"


class TopoNode(nodes.Element):
    pass


class Topo(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False

    def run(self):
        source_path = pathlib.Path(self.state_machine.input_lines.source(0))
        path = source_path.parent / directives.path(self.arguments[0])
        return [TopoNode(self.block_text, path=path, routes=[])]


directives.register_directive("topo", Topo)


class AttributesNode(nodes.Element):
    pass


def rock(argument):
    return directives.choice(
        argument, ("granite", "limestone", "sandstone", "quartzite")
    )


def multiple_choice(argument, choices):
    if not argument:
        return []
    return [
        directives.choice(a.strip(), choices) for a in argument.split(",") if a.strip()
    ]


def orientation(argument):
    return multiple_choice(argument, ("n", "ne", "e", "se", "s", "sw", "w", "nw"))


def season(argument):
    items = [item.strip()
             for item in argument.lower().replace(";", ",").split(",")]
    months = []
    for item in items:
        month_mapping = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        if "-" in item:
            start_month, end_month = item.split("-")
            start_month = month_mapping[start_month.strip()]
            end_month = month_mapping[end_month.strip()]
            if start_month and end_month:
                if start_month > end_month:
                    end_month += 12
                months.extend(
                    ((m - 1) % 12) + 1 for m in range(start_month, end_month + 1)
                )
        else:
            month = month_mapping.get(item.lower())
            if month:
                months.append(month)

    return months


class Attributes(Directive):
    required_arguments = 0
    optional_arguments = 0
    has_content = False
    option_spec = {
        "rock": rock,
        "orientation": orientation,
        "season": season,  # season,
        "sun": directives.unchanged,
        "children": yesno,
        "altitude": directives.nonnegative_int,
        "approach": directives.nonnegative_int,
        "driesafterrain": directives.nonnegative_int,
        "8anu": directives.unchanged,
    }

    def run(self):
        return [AttributesNode(self.block_text, **self.options)]


directives.register_directive("attributes", Attributes)


def grade(argument):
    return argument


def climbing_style(argument):
    return multiple_choice(
        argument,
        (
            "fingery",
            "powerful",
            "dyno",
            "tufa",
            "pockets",
            "crack",
            "endurance",
            "technical",
            "mental",
            "tufa",
            "crag",
        ),
    )


def steepness(argument):
    return multiple_choice(argument, ("slab", "vertical", "overhang", "roof"))


def route_other(argument):
    return multiple_choice(argument, ("dangerous", "partly bolted", "runout"))


class RouteNode(nodes.Element):
    pass


class Route(Directive):
    required_arguments = 1
    optional_arguments = 20
    has_content = True
    option_spec = {
        "grade": grade,
        "length": directives.unchanged,
        "bolts": directives.unchanged,
        "style": climbing_style,
        "steepness": steepness,
        "other": route_other,
        "stars": directives.unchanged,
        "created": directives.unchanged,
        "creator": directives.unchanged,
        "first-ascent": directives.unchanged,
        "topo-id": directives.unchanged,
        "8anu": directives.unchanged,
    }

    def run(self):
        name = " ".join(self.arguments)
        text = "\n".join(self.content)
        node = RouteNode(text, name=name, **self.options)
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


directives.register_directive("route", Route)


def my_html_parts(
    input_string, source_path=None, destination_path=None, fast=False, **kwargs
):
    overrides = {
        "input_encoding": "utf-8",
        "output_encoding": "utf-8",
        "stylesheet": None,
        "stylesheet_path": None,
        "embed_stylesheet": False,
        "link_stylesheet": True,
        "syntax_highlight": "none",
        "math_output": "mathjax",
        "math_output_options": {},
    }
    overrides.update(kwargs)
    writer = MyHTMLWriter(destination_path=destination_path, fast=fast)
    return publish_parts(
        source=input_string,
        source_path=source_path,
        destination_path=destination_path,
        writer=writer,
        settings_overrides=overrides,
    )


class SimpleImage(draw.DrawingBasicElement):
    """A linked or embedded image."""

    TAG_NAME = "image"

    def __init__(self, x, y, width, height, uri):
        super().__init__(x=x, y=y, width=width, height=height, xlink__href=uri)


class SimpleUse(draw.DrawingBasicElement):
    """A copy of another element, drawn at a given position

    The referenced element becomes an SVG def shared between all Use elements
    that reference it.  Useful for drawings with many copies of similar shapes.
    Additional arguments like `fill='red'` will be used as the default for this
    copy of the shapes.
    """

    TAG_NAME = "use"

    def __init__(self, **kwargs):
        super().__init__(xlink__href="")


class SvgA(draw.DrawingParentElement):
    TAG_NAME = "a"

    def __init__(self, href):
        super().__init__(href=href)


class CollectorTransform(Transform):
    default_priority = 1000

    @classmethod
    def factory(cls, destination_path, fast):
        def create(*args, **kwargs):
            kwargs["destination"] = destination_path.parent
            kwargs["fast"] = fast
            return cls(*args, **kwargs)

        create.default_priority = cls.default_priority
        return create

    def __init__(self, document, startnode, destination, fast=False):
        super().__init__(document, startnode)
        self.destination = destination
        self.fast = fast

    def apply(self):
        visitor = CollectorVisitor(self.document, self.fast)
        self.document.walkabout(visitor)
        self.document.json_output = visitor.json_output
        self.document.first_section = visitor.first_section
        self.document.images = visitor.images
        self.document.image_titles = visitor.image_titles
        self.document.topos = {}
        self.document.background_images = visitor.background_images
        self.document.transform_messages[:] = []
       
        crop_rects = [self.get_crop_rect(node) for node in visitor.topos]
        aspect = TOPO_ASPECT_RATIO
        min_aspect = 0
        max_aspect = 100
        for r in crop_rects:
            if r:
                xmin, ymin, xmax, ymax, width, height = r
                w = xmax - xmin
                h = ymax - ymin
                max_aspect = min(max_aspect, height / w)
                min_aspect = max(min_aspect, h / width)
                # print("aspect", (max_aspect, height / w), (min_aspect,  h / width))

        aspect = (max_aspect + min_aspect) / 2
        aspect = min(max(aspect, min_aspect), max_aspect)

        for i, (node, cr) in enumerate(zip(visitor.topos, crop_rects)):
            self.modify_svg(node, visitor, i, aspect, cr[:4])

    def get_crop_rect(self, node):
        path = node.get("path")

        try:
            with open(path, "r") as file:
                svg = svgelements.SVG.parse(file, reify=False)
        except FileNotFoundError:
            self.document.reporter.error(
                f"File '{path}' not found.", base_node=node)
            return

        min_x = svg.width
        min_y = svg.height
        max_x = 0
        max_y = 0

        for element in svg.elements():
            if isinstance(element, svgelements.Path):
                xmin, ymin, xmax, ymax = element.bbox(transformed=False)
                min_x = min(min_x, xmin, xmax)
                min_y = min(min_y, ymin, ymax)
                max_x = max(max_x, xmin, xmax)
                max_y = max(max_y, ymin, ymax)

            elif isinstance(element, svgelements.Line):
                min_x = min(element.start.x, min_x)
                min_y = min(element.start.y, min_y)
                max_x = max(element.end.x, max_x)
                max_y = max(element.end.y, max_y)

            elif isinstance(element, svgelements.Polyline) or isinstance(
                element, svgelements.Polygon
            ):
                for point in element.points:
                    min_x = min(point.x, min_x)
                    min_y = min(point.y, min_y)
                    max_x = max(point.x, max_x)
                    max_y = max(point.y, max_y)

        return [
            max(min_x - ASPECT_MARGIN, 0),
            max(min_y - ASPECT_MARGIN, 0),
            min(max_x + ASPECT_MARGIN, svg.width),
            min(max_y + ASPECT_MARGIN, svg.height),
            svg.width,
            svg.height,
        ]

    def modify_svg(self, node, visitor, index, aspect, crop_rect):
        topo_id = "topo-" + node["section"]
        path = node.get("path")

        try:
            with open(path, "r") as file:
                svg = svgelements.SVG.parse(file, reify=False)
        except FileNotFoundError:
            self.document.reporter.error(
                f"File '{path}' not found.", base_node=node)
            return

        # bring the topos all to the same aspect ratio to fit nicely in the site
        xmin, ymin, xmax, ymax = crop_rect
        w = xmax - xmin
        h = ymax - ymin
        hc = svg.width * aspect
        wc = svg.height / aspect
        if h <= hc <= svg.height:
            dh = (hc - h) / 2
            y0 = max(ymin - dh, 0)
            y1 = min(y0 + hc, svg.height)
            y0 = max(y1 - hc, 0)
            y0 = min(y0, ymin)
            y1 = max(y1, ymax)
            rcrop = [0, y0, svg.width, y1]
        else:
            dw = (wc - w) / 2
            x0 = max(xmin - dw, 0)
            x1 = min(x0 + wc, svg.width)
            x0 = max(x1 - wc, 0)
            x0 = min(x0, xmin)
            x1 = max(x1, xmax)
            rcrop = [x0, 0, x1, svg.height]

        cwidth = rcrop[2] - rcrop[0]
        cheight = rcrop[3] - rcrop[1]

        d = draw.Drawing(int(cwidth), int(cheight))
        d.view_box = str(svg.viewbox).split(" ")
        d.view_box[2] = str(int(cwidth))
        d.view_box[3] = str(int(cheight))
        transform = f"translate({-rcrop[0]}, {-rcrop[1]})"
        """
        print(
            "view box",
            topo_id,
            aspect,
            cheight / cwidth,
            d.view_box,
            rcrop,
            crop_rect,
            svg.viewbox,
            transform,
        )
        """

        for element in svg.elements():
            if isinstance(element, svgelements.Path):
                draw_element = draw.Path(
                    d=element.d(transformed=False),
                    **{"vector-effect": "non-scaling-stroke"},
                )

            elif isinstance(element, svgelements.Line):
                draw_element = draw.Line(
                    element.start.x, element.start.y, element.end.x, element.end.y
                )
            elif isinstance(element, svgelements.Polyline):
                draw_element = draw.Polyline(element.points)

            elif isinstance(element, svgelements.Polygon):
                draw_element = draw.Polygon(element.points)

            elif isinstance(element, svgelements.Text):
                draw_element = draw.Text(
                    element.text, font_size, x=element.x, y=element.y
                )

            elif isinstance(element, svgelements.Image):
                path = pathlib.Path(tempdir.name) / f"topo-{index}"
                path = save_image_url_to_file(element.url, path, rcrop)
                url = visitor.add_image(path)
                # url = save_image_url_to_file(element.url, path, rcrop, True)
                draw_element = SimpleImage(
                    x=0,
                    y=0,
                    width=cwidth,
                    height=cheight,
                    uri=url,
                )
            else:
                continue

            if element.id and not isinstance(element, svgelements.Image):
                id_ = element.id
                best_dist = 1000
                number = 0
                routes = node.get("routes")
                for i, route in enumerate(routes):
                    dist = distance(name_to_id(route["name"]), id_)
                    if id_ == route.get("topo-id"):
                        dist = 0

                    if dist < best_dist:
                        best_dist = dist
                        number = i
                        if dist == 0:
                            break

                if best_dist != 1000:
                    id_ = (
                        node["section"]
                        + "-"
                        + route.get("topo-id",
                                    name_to_id(routes[number]["name"]))
                    )

                g = draw.Group(id=id_, transform=transform,
                               **{"class": "topo-route"})
                g.append(draw_element)

                draw_element = g

                if best_dist != 1000:
                    route = routes[number]
                    route["html_id"] = hid = "route-" + id_
                    self.document.json_output[hid]["topo"] = topo_id
                    self.document.json_output[hid]["route"] = {
                        "name": route["name"],
                        "grade": route["grade"],
                        "id": id_,
                        "topo": topo_id,
                    }

                    lowest = (0, 0)
                    for p in element.as_points():
                        if p.y > lowest[1]:
                            lowest = (p.x, p.y)
                    # print("points", lowest, number, element.id)

                    x = lowest[0] - 15
                    y = lowest[1]
                    w = h = 30
                    g.append(draw.Rectangle(x, y, w, h, rx="10", ry="10"))
                    g.append(
                        draw.Text(
                            str(number + 1),
                            font_size,
                            x + h / 2,
                            y + h / 2,
                            text_anchor="middle",
                            dominant_baseline="middle",
                        )
                    )

                    anchor = SvgA("#" + hid)
                    anchor.append(g)
                    draw_element = anchor

            d.append(draw_element)

        d.append(SimpleUse())
        # d.save_svg(str(self.destination / (node["section"]+"-topo.svg")))
        # print("save", str(self.destination / (node["section"]+"-topo.svg")))
        self.document.topos[topo_id] = d.as_svg(header="")


class CollectorVisitor(MImageCollector, nodes.SparseNodeVisitor):
    def __init__(self, document, fast):
        super().__init__(document)
        self.fast = fast
        self.section_level = 0
        self.active_topo = None
        self.active_statistics = []
        self.active_geomaps = []
        self.section_ids = []
        self.last_section_id = ""
        self.json_output = defaultdict(dict)
        self.topos = []
        self.url_8anu = None
        self.route_number = 0
        self.first_section = ""

    def unknown_visit(self, node):
        pass

    def unknown_departure(self, node):
        pass

    def visit_RouteStatisticsNode(self, node):
        collector = RouteStatisticsCollector(
            self.section_level,
            self.section_level + node.attributes.get("levels", 1),
            node.attributes.get("summary", "e"),
        )
        self.active_statistics.append(collector)
        node.attributes["collector"] = collector

    def depart_RouteStatisticsNode(self, node):
        pass

    def visit_GeoLocationNode(self, node):
        id_ = self.last_section_id
        if "coords" in node.attributes:
            obj = {
                "type": "area",
                "path": "area/" + id_,
                "name": id_,
                "coords": node.attributes["coords"],
                "href": id_,
                "show_title": node.attributes.get("show-title"),
                "direction": node.attributes.get("direction", "nw"),
            }
            for collector in self.active_geomaps:
                if collector.end_level >= self.section_level:
                    collector.objects.append(obj)

            self.json_output[id_]["geolocation"] = id_
            self.json_output[id_]["geomap"] = self.active_geomaps[-1]
            self.json_output[id_]["coords"] = node.attributes["coords"]
            return

        if "marker" in node.attributes:
            for collector in self.active_geomaps:
                if collector.end_level >= self.section_level:
                    for obj in collector.objects:
                        if obj["path"] == node.attributes["marker"]:
                            obj["href"] = self.json_output[id_]["geolocation"] = id_
                            obj["show_title"] = node.attributes.get(
                                "show-title")
                            obj["direction"] = node.attributes.get(
                                "direction", "nw")
                            obj["color"] = node.attributes.get("color")
                            self.json_output[id_]["geomap"] = self.active_geomaps[-1]
                            self.json_output[id_]["coords"] = obj.get("coords")
                            break

    def visit_AttributesNode(self, node):
        try:
            node.attributes["coords"] = self.json_output[self.last_section_id]["coords"]
        except KeyError:
            pass

        if "8anu" in node.attributes:
            self.url_8anu = node.attributes["8anu"]

    def depart_AttributesNode(self, node):
        pass

    def depart_GeoLocationNode(self, node):
        pass

    def visit_GeoMapNode(self, node):
        collector = GeoMapCollector(
            self.last_section_id,
            self.section_level,
            self.section_level + node.attributes.get("levels", 1),
            node.attributes.get("objs", []),
        )
        collector.folder = node.attributes.get("folder", "")
        collector.style = node.attributes.get("style", "map")
        self.active_geomaps.append(collector)
        self.json_output[self.last_section_id]["geomap"] = collector

    def depart_GeoMapNode(self, node):
        pass

    def visit_TopoNode(self, node):
        self.active_topo = node
        node["section"] = self.last_section_id
        self.topos.append(node)

    def depart_TopoNode(self, node):
        pass

    def visit_RouteNode(self, node):
        self.route_number += 1

        for collector in self.active_statistics:
            if collector.end_level >= self.section_level:
                collector.routes.append(node.attributes)

        node.attributes["section"] = self.last_section_id

        if self.active_topo is None:
            self.document.reporter.warning(
                f'Route "{node.attributes["name"]}" without topo.')
            node.attributes["number"] = self.route_number
        else:
            routes = self.active_topo.get("routes")
            routes.append(node.attributes)
            node.attributes["number"] = len(routes)

        if self.url_8anu and "8anu" not in node.attributes and not self.fast:
            node.attributes["8anu"] = find_route_url(
                self.url_8anu, node.attributes["name"]
            )

    def depart_RouteNode(self, node):
        pass

    def visit_ApartmentNode(self, node):
        self.add_image(node.attributes["title-img"], thumnail=True)

    def depart_ApartmentNode(self, node):
        pass

    def visit_ApartmentsNode(self, node):
        pass

    def depart_ApartmentsNode(self, node):
        pass

    def visit_MenuNode(self, node):
        pass

    def depart_MenuNode(self, node):
        pass

    def visit_section(self, node):
        self.section_level += 1
        id_ = node.get("ids", [""])[0]
        if id_:
            self.last_section_id = id_
            if not self.first_section:
                self.first_section = id_
            
        self.section_ids.append(id_)
        self.route_number = 0

    def depart_section(self, node):
        self.section_level -= 1

        self.active_topo = None

        self.active_statistics = [
            c for c in self.active_statistics if c.start_level <= self.section_level
        ]
        self.active_geomaps = [
            c for c in self.active_geomaps if c.start_level <= self.section_level
        ]

        self.section_ids.pop()
        self.last_section_id = ""
        for n in reversed(self.section_ids):
            if n:
                self.last_section_id = n
                break


class MyHTMLWriter(Writer):
    def __init__(self, destination_path, fast=False):
        super().__init__()
        self.translator_class = MyHTMLTranslator
        self.destination_path = destination_path
        self.fast = fast

    def get_transforms(self):
        super_transforms = super().get_transforms()
        return super_transforms + [
            CollectorTransform.factory(self.destination_path, self.fast)
        ]

    def assemble_parts(self):
        super().assemble_parts()
        self.parts["first_section"] = self.document.first_section
        self.parts["json_output"] = self.document.json_output
        self.parts["images"] = self.document.images


class MyHTMLTranslator(MImageHTMLTranslator, HTMLTranslator):
    overview_container_done = False

    def insert_overview_container(self):
        if self.overview_container_done:
            return False
        self.overview_container_done = True
        self.body.append(
            """
            <div id="overview-container" class="w-full sticky top-0 bg-surface-50">
                <div id="overview">
                    <div id="map" class="show zoom-able"></div>"""
        )

        for k, v in self.document.topos.items():
            self.body.append(
                f"""<div id="{k}" class="topo bg-surface-50 zoom-able">{v}{orientation}
                </div>"""
            )

        self.body.append(
            """</div>
            <ol id="breadcrump" class="variant-glass-surface"></ol></div>"""
        )
        return True

    def visit_RouteStatisticsNode(self, node):
        svg = node.attributes["collector"].draw()
        self.body.append(
            f"""<div class="routestatisics zoom-able">{svg}</div>""")

    def depart_RouteStatisticsNode(self, node):
        pass

    def visit_GeoLocationNode(self, node):
        pass

    def depart_GeoLocationNode(self, node):
        pass

    def visit_GeoMapNode(self, node):
        pass

    def depart_GeoMapNode(self, node):
        pass

    def visit_TopoNode(self, node):
        pass

    def depart_TopoNode(self, node):
        pass

    def visit_AttributesNode(self, node):
        self.body.extend(
            (self.starttag(node, "div", CLASS="attributes"), "<ul>"))
        # all is limestone
        if 0 and "rock" in node.attributes:
            self.body.append("<li>Rock: " + node.attributes["rock"] + "</li>")

        try:
            coords = node.attributes["coords"]
            self.body.append(
                f"""<li>Location: {coords[0]:.4f}, {
                    coords[1]:.4f}</li>"""
            )
        except KeyError:
            pass

        if "sun" in node.attributes:
            self.body.append("<li>Sun: " + node.attributes["sun"] + "</li>")
        if "children" in node.attributes:
            self.body.append("<li>Children: " +
                             node.attributes["children"] + "</li>")
        if "altitude" in node.attributes:
            self.body.append(
                "<li>Altitude: " + str(node.attributes["altitude"]) + "m</li>"
            )
        if "approach" in node.attributes:
            self.body.append(
                "<li>Approach: " +
                str(node.attributes["approach"]) + "min</li>"
            )
        if "driesafterrain" in node.attributes:
            self.body.append(
                "<li>Dries after rain: "
                + str(node.attributes["driesafterrain"])
                + "</li>"
            )

        self.body.append("</ul>")
        if "orientation" in node.attributes:
            self.body.append(
                f"""<div class="orientation zoom-able {" ".join(node.attributes["orientation"])}">
                {KOMPASS}</div>"""
            )

        if "season" in node.attributes:
            months = [
                "jan",
                "feb",
                "mar",
                "apr",
                "may",
                "jun",
                "jul",
                "aug",
                "sep",
                "oct",
                "nov",
                "dec",
            ]
            klasses = " ".join("s-" + months[m - 1]
                               for m in node.attributes["season"])
            self.body.append(
                f"""<div class="season zoom-able {klasses}">{SEASON}</div>"""
            )

        self.body.append("</div>")

    def depart_AttributesNode(self, node):
        pass

    def visit_RouteNode(self, node):
        try:
            id_ = node.attributes["html_id"]
        except KeyError:
            id_ = "route-" + name_to_id(node.attributes["name"])

        props = node.attributes
        props["ids"] = [id_]
        self.body.append(self.starttag(node, "div", CLASS="route"))

        rgrade = props.get("grade", "").strip()
        gclass = "grade-" + rgrade.replace("+", "p")
        self.body.append(
            f"""<a href="#{id_}"><h4>
            <span class="route-number">{props["number"]}</span>
            {props["name"]}
            <span class="route-grade {gclass}">{rgrade}
            </span></h4></a>"""
        )
        self.body.append(self.starttag(node, "ul", CLASS="route-props"))
        if props.get("length"):
            self.body.append(f"<li>{props['length']}m</li>")

        if int(props.get("stars", 0) or 0):
            alt = CEVAPI_RATING.get(props["stars"], "")
            self.body.append(
                f"""<li><a href="javascript:route_rating()">
                <img alt="{alt}" src="cevapi-{props['stars']}.svg"/></a></li>"""
            )

        if props.get("bolts"):
            self.body.append(f"<li>Bolts: {props['bolts']}</li>")

        if props.get("style"):
            self.body.append(f"<li>Style: {', '.join(props['style'])}</li>")

        if props.get("steepness"):
            self.body.append(f"<li>Steepness: {
                             ', '.join(props['steepness'])}</li>")

        if props.get("other"):
            self.body.append(f"<li>Other: {', '.join(props['other'])}</li>")

        if props.get("created"):
            self.body.append(f"<li>Created: {props['created']}</li>")

        if props.get("creator"):
            self.body.append(f"<li>Creator: {props['creator']}</li>")

        if props.get("first-ascent"):
            self.body.append(f"<li>FA: {props['first-ascent']}</li>")

        if props.get("8anu"):
            self.body.append(
                f"""<li><a href="{props['8anu']}
                    " target="_blank">&#x261B 8a.nu</a></li>"""
            )

        self.body.append("</ul>")

    def depart_RouteNode(self, node):
        self.body.append("</div>")

    def visit_paragraph(self, node):
        if node.children or True:
            super().visit_paragraph(node)

    def depart_paragraph(self, node):
        if node.children or True:
            super().depart_paragraph(node)

    def visit_section(self, node):
        try:
            id_ = node.get("ids", [""])[0]
        except IndexError:
            return

        props = self.document.json_output.get(id_, {})
        klasses = node.get("classes", [])

        try:
            bgimage = self.document.background_images[id_]
        except KeyError:
            pass
        else:
            self.body.append(
                f'<div class="background" style="background-image: url({
                    bgimage})">'
            )
            klasses.append("has-background")
            node["classes"] = klasses

        klass = "section"
        if "geomap" in props or "topo" in props:
             if self.insert_overview_container():
                h3klass = "h-3"
                if "has-background" in klasses:
                    h3klass += " has-background"
                self.body.append(f"""<div class="{h3klass}"></div>""")
                klass += " after-overview-container"

        elif not self.overview_container_done:
            klass += " before-overview-container"
                
        # the next is a modified super().visit_section(node)
        self.section_level += 1
        self.body.append(self.starttag(node, "div", CLASS=klass))

    def depart_section(self, node):
        super().depart_section(node)
        try:
            id_ = node.get("ids", [""])[0]
        except IndexError:
            return

        if id_ in self.document.background_images:
            self.body.append("</div>")

    def section_title_tags(self, node):
        try:
            id_ = node.parent.get("ids", [""])[0]
            if id_:
                node.attributes["refid"] = id_
        except Exception:
            pass
        return super().section_title_tags(node)
    

def order_coords(coords):
    return [[c[1], c[0]] for c in coords]


def read_geo_data():
    geo_file = __DIR__.parent / "docutil/Climbersheaven.kml"

    with open(geo_file, "rb") as file:
        k = kml.KML()
        k.from_string(file.read().decode("utf-8"))

    geo_data = {}
    document = list(k.features())[0]
    for folder in document.features():
        geo_data[folder.name] = placemarks = []
        # print("Folder:", folder.name)
        for placemark in folder.features():
            if not placemark.visibility:
                continue

            parts = placemark.name.split("/")
            type_ = parts.pop(0)
            name = parts[-1] if parts else ""
            # print("Placemark:", placemark.name)

            data = {
                "type": type_,
                "name": name,
                "path": placemark.name,
            }

            if placemark.geometry.geom_type == "Point":
                data["coords"] = order_coords(placemark.geometry.coords)[0]
                # print("Coordinates:", placemark.geometry.coords)
            elif placemark.geometry.geom_type == "LineString":
                data["coords"] = order_coords(placemark.geometry.coords)
                # print("Path:", placemark.geometry.coords)

            placemarks.append(data)

    return geo_data


def serialize(obj):
    return obj.to_json()


geo_data = None
version = 0


def transform(fast=False):
    global tempdir
    tempdir = tempfile.TemporaryDirectory()
    with tempdir:
        _transform(fast)


def _transform(fast=False):
    global geo_data
    global version

    geo_data = read_geo_data()

    guide_file = __DIR__.parent / "docutil" / "guide.rst"
    with open(guide_file, "r", encoding="utf-8") as file:
        input_string = file.read()

    dest_dir = __DIR__.parent / "html" / "static" / "data"
    dest_dir.mkdir(exist_ok=True, parents=True)

    dest = dest_dir / "guide.txt"
    output = my_html_parts(
        input_string, source_path=str(guide_file), destination_path=dest, fast=fast
    )
    with open(dest, "w", encoding="utf-8") as file:
        file.write(htmlmin.minify(output["html_body"]))

    write_images(dest_dir, output["images"])

    # if called in guide.py
    if version:
        print("version", repr(version))
        output["json_output"]["__version__"] = version
    version += 1

    # If the display is above the overview =>
    # fill the overview with the first data
    first_value = next(iter(output["json_output"].values()))
    output["json_output"][output["first_section"]] = first_value

    with open(dest.with_suffix(".json"), "w", encoding="utf-8") as file:
        file.write(json.dumps(output["json_output"], default=serialize))


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    file_handler = logging.FileHandler('errors.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    transform()
    if 0:
        try:
            transform()
        except Exception as e:
            logger.exception(e)
