"""
Extracts the data of a 27crags site that was saved offline

To run that script you need to install the following packages:

    - pip install drawsvg
    - pip install pillow
    - pip install beautifulsoup4


call it with:
    
    python crags-scraper.py input.html output-dir
"""

import sys
import json
import requests
import textwrap
import unicodedata
import drawsvg as dw
from pathlib import Path
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image


def name_to_id(name):
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ", "-")


def orientation(node, props):
    props["orientation"] = node.text.strip().lower()


def season(node, props):
    #print("season: ", node.text.strip())
    props["season"] = node.text.strip()


def approach(node, props):
    #print("approach: ", node.text.strip().strip("min"))
    props["approach"] = node.text.strip().strip("min").strip()


def altitude(node, props):
    # print("altitude: ", node.text.strip())
    props["altitude"] = node.text.strip().strip("m").strip()


def children(node, props):
    props["children"] = "yes"


attr_translate = {
    "Orientation": orientation,
    "Best season": season,
    "Approach time": approach,
    "Altitude": altitude,
    "Child friendly": children
}


def sprop(name, value):
    def f(props):
        props[name].append(value)
    return f


rprop_translate = {
    'slab': sprop("steepness", "slab"),
    'vertical': sprop("steepness", "vertical"),
    'overhang': sprop("steepness", "overhang"),
    'roof': sprop("steepness", "roof"),
    'powerful': sprop("style", "powerful"),
    'endurance': sprop("style", "endurance"),
    'technical': sprop("style", "technical"),
    'fingery': sprop("style", "fingery"),
    'tufas': sprop("style", "tufa"),
    'pockets': sprop("style", "pockets"),
    'dangerous': sprop("other", "dangerous"),
    'runout': sprop("other", "runout")}


def read_stars(node):
    return len(node.find_all("div", class_="glyphicon-star"))


def read_info(node, route):
    info_nodes = node.find_all("div", class_="route-info")

    desc = []
    lcy = ""
    for inf in  info_nodes:
        if len(inf.text.split(",")) < 2:
            desc.append(inf.text.strip())
        else:
            lcy = inf.text.strip()

    if desc:
        route["description"] = "\n".join(desc)

    lcy = [p.strip() for p in lcy.split(",")]
    try:
        route["length"] = lcy.pop(0).strip("m").strip()
    except IndexError:
        pass

    try:
        route["created"] = lcy.pop().strip()
    except IndexError:
        pass

    try:
        route["creator"] = lcy.pop(0).strip()
    except IndexError:
        pass
    
    try:
        route["first-ascent"] = lcy.pop(0).strip().strip("FA:").strip()
    except IndexError:
        pass


def write_sector(dest, sector, attrs, routes, topo_url):
    with open(dest, "w") as f:
        print(sector, file=f)
        print("-"*len(sector), file=f)
        print("", file=f)
        print(".. geolocation::", file=f)
        print("    :marker:", sector.replace(" ", "/").lower(), file=f)
        print("    :show-title: yes", file=f)
        print("", file=f)
        print(".. routestatistics::", file=f)
        print("", file=f)
        print(".. attributes::", file=f)
        print("    :rock: limestone", file=f)
        
        if "orientation" in attrs:
            print("    :orientation:", attrs["orientation"], file=f)
        
        if "season" in attrs:
            print("    :season:", attrs["season"], file=f)
        
        if "approach" in attrs:
            print("    :approach:", attrs["approach"], file=f)
        
        if "altitude" in attrs:
            print("    :altitude:", attrs["altitude"], file=f)

        print("    :children:", attrs.get("children", "no"), file=f)
        print("", file=f)
        print("Routes", file=f)
        print("......", file=f)
        print("", file=f)
        print(".. topo::", topo_url, file=f)
        print("", file=f)
        for r in routes:
            print(".. route::", r["name"], file=f)
            print("    :grade: ", r["grade"], file=f)
            print("    :length: ", r.get("length", ""), file=f)
            print("    :stars: ", r["stars"], file=f)
            print("    :created: ", r.get("created", ""), file=f)
            print("    :creator: ", r.get("creator", ""), file=f)
            print("    :first-ascent: ", r.get("first-ascent", ""), file=f)
            print("    :style: ", ", ".join(r["style"]), file=f)
            print("    :steepness: ", ", ".join(r["steepness"]), file=f)
            print("    :other: ", ", ".join(r["other"]), file=f)
            desc = r.get("description", "")
            if desc:
                print("", file=f)
                print(textwrap.indent(desc, "    "), file=f)

            print("", file=f)



def create_svg(routes, image_url, dest):
    response = requests.get(image_url)
    if response.status_code == 200:
        image_raw = response.content
        image = Image.open(BytesIO(image_raw))
    else:
        raise Exception("Could not download image")

    width = image.width
    height = image.height

    # print("width: ", width, file=sys.stderr)
    # print("height: ", height, file=sys.stderr)

    d = dw.Drawing(width, height, origin=(0, 0))
    d.append(dw.Image(0, 0, width, height, image_url, image_raw, embed=True))

    for r in routes:
        points = []
        for p in r["line"]:
            points.append(float(p['x'])*width)
            points.append(float(p['y'])*height)
        d.append(dw.Lines(*points,
                          id=r["id"],
                          style="fill: none; stroke: rgb(255, 0, 0); vector-effect: non-scaling-stroke; stroke-width: 2px;"))

    with open(dest, 'w') as f:
        f.write(d.as_svg())


def main(html, dest):
    with open(html) as fp:
        soup = BeautifulSoup(fp, features="html.parser")

    if 0:
        props = set()
        tags = soup.find_all("span", class_="tag")

        for t in tags:
            props.add(t["class"][1])

        return props

    sector = soup.find(id='sectors-dropdown').find(class_="name").text
    properties = soup.find(class_='sector-properties')

    attrs = {}
    for p in properties.find_all(string=False):
        if p.has_attr('data-href'):
            attrs["location"] = p['data-href']
            continue

        if p.has_attr('data-original-title'):
            attr_translate[p['data-original-title']](p, attrs)

    topos = soup.find_all(class_="topo")

    for i, t in enumerate(topos):
        lines = t.find("script", class_="js-data")
        topos_routes = lines.parent.find_all("div", class_="nbr")
        topos_routes = [t["id"] for t in topos_routes]
        # print("topos_routes", topos_routes)

        img = lines.previous_element['src']
        lines = json.loads(lines.text)["lines"]

        route_container = t.find("ul", class_="route-list")
        routes = []
        for r in route_container.find_all("li", recursive=False):
            line_id = "line-tag-" + r["data-image"] + '-' + r["data-route"]
            rhc = r.find("div", class_="header-container")
            name_grade = rhc.find("div", class_="route-name").text
            name_grade = [c.strip() for c in name_grade.split(",")]
            name = name_grade[0]
            try:
                grade = name_grade[1]
            except IndexError:
                grade = ""

            id_ = name_to_id(name)
            route = {
                "id": id_,
                "name": name,
                "grade": grade,
                "line": lines[topos_routes.index(line_id)],
                'style': [],
                'steepness': [],
                'other': [],
                'stars': read_stars(rhc)
            }
            read_info(r, route)

            tags = r.find("div", class_="tags")
            for t in tags.find_all("span"):
                for k, f in rprop_translate.items():
                    if k in t["class"]:
                        f(route)

            routes.append(route)

        topo_url = Path(html).stem + f"-{i}.svg"
        create_svg(routes, img, Path(dest) / (Path(html).stem + f"-{i}.svg"))
        # print(routes)
        dpath = Path(dest) / (Path(html).stem + f"-{i}.rst")
        write_sector(dpath, sector, attrs, routes, topo_url)


if __name__ == '__main__':
    try:
        main(sys.argv[1], sys.argv[2])
    except IndexError:
        sources = Path(__file__).parents[1] / "sources"
        guide = Path(__file__).parents[1] / "guide" / "podgorica"
        smo = sources / "cievna"
        smo_dest = guide / "cievna"
        args = [
            (smo/"dark-side.html", smo_dest),
            (smo/"Disco.html", smo_dest),
            (smo/"Grey left.html", smo_dest),
            (smo/"Left Wall.html", smo_dest),
            (smo/"Right Wall.html", smo_dest)
        ]

        for a in args:
            main(*a)
