import pathlib
import glob
import shutil
import pillow_avif
from PIL import Image
from docutils import nodes
from docutils.parsers.rst import Directive, directives


def directive_source_file(directive):
    doc_source = directive.state.document.get("source")
    candidates = [
        getattr(directive.state.document, "current_source", None),
        directive.state_machine.input_lines.source(0),
        doc_source,
    ]

    for source in candidates:
        if not source:
            continue

        path = pathlib.Path(source)
        if path.is_absolute() and path.exists():
            return path

        cwd_path = (pathlib.Path.cwd() / path).resolve()
        if cwd_path.exists():
            return cwd_path

        if doc_source:
            doc_parent = pathlib.Path(doc_source).resolve().parent
            doc_relative_path = (doc_parent / path).resolve()
            if doc_relative_path.exists():
                return doc_relative_path

        return path.resolve()

    return pathlib.Path(".").resolve()


class ImageListNode(nodes.Element):
    pass


class ImageList(Directive):
    required_arguments = 1
    optional_arguments = 20
    has_content = False
    option_spec = {
        "path": directives.unchanged
    }

    def run(self):
        source_path = directive_source_file(self).parent
        paths = " ".join(self.arguments)
        paths = [source_path/p.strip() for p in paths.split(",")]
        matched_paths = []
        for pattern in paths:
            matched_paths.extend(glob.glob(str(pattern), recursive=True))
        paths = [pathlib.Path(path) for path in dict.fromkeys(matched_paths)]

        # sort for image height
        landscape = []
        portrait = []
        for p in sorted(paths):
            img = Image.open(p)
            if img.size[0] > img.size[-1]:
                landscape.append(p)
            else:
                portrait.append(p)

        return [ImageListNode(self.block_text, landscape=landscape, portrait=portrait)]


directives.register_directive('imagelist', ImageList)


class ImgNode(nodes.Element):
    pass


def yesno(argument):
    return directives.choice(argument, ("yes", "no"))


class Img(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False
    option_spec = {
        "zoomable": yesno,
        "class": directives.unchanged,
    }

    def run(self):
        source_path = directive_source_file(self).parent
        path = source_path/self.arguments[0]
        return [ImgNode(self.block_text, path=path, **self.options)]


directives.register_directive('img', Img)


class BackgroundNode(nodes.Element):
    pass


class Background(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False
    option_spec = {}

    def run(self):
        source_path = directive_source_file(self)
        path = source_path.parent / directives.path(self.arguments[0])
        return [BackgroundNode(self.block_text, path=path)]


directives.register_directive('background', Background)


class MImageCollector:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_images = {}
        self.images = {}
        self.image_titles = {}
        self.image_list_nodes = []

    def image_path_to_url(self, path):
        return path

    def add_image(self, path, comment=False, **options):
        if path not in self.images:
            image_id = f"data/img/image-{str(len(self.images))}{path.suffix}"
            self.images[path] = (image_id, options)
        else:
            image_id = self.images[path][0]

        if comment:
            img = Image.open(path)
            try:
                desc = img.getxmp().get('xmpmeta', {}).get(
                    "RDF", {}).get("Description", [])
            except:
                desc = []

            text = None
            if isinstance(desc, dict):
                try:
                    text = desc["description"]["Alt"].get("li", {}).get("text")
                except KeyError:
                    pass
            else:
                for d in desc:
                    if "description" in d:
                        text = d["description"]["Alt"].get("li", {}).get("text")
                        break
        
            if text:
                self.image_titles[image_id] = text

        return image_id

    def visit_ImageListNode(self, node):
        node.attributes["ls_images"] = [
            self.add_image(p, reduce=True, comment=True)
            for p in node.attributes["landscape"]]
        node.attributes["pt_images"] = [
            self.add_image(p, reduce=True, comment=True)
            for p in node.attributes["portrait"]]
        self.image_list_nodes.append(node)

    def depart_ImageListNode(self, node):
        pass

    def visit_ImgNode(self, node):
        node.attributes["image_id"] = self.add_image(
            node.attributes["path"], reduce=True, comment=True)

    def depart_ImgNode(self, node):
        pass

    def visit_BackgroundNode(self, node):
        self.background_images[self.last_section_id] = self.image_path_to_url(
            self.add_image(node.attributes["path"], background=True))

    def depart_BackgroundNode(self, node):
        pass


class MImageHTMLTranslator:
    def image_path_to_url(self, path):
        return path

    def visit_ImageListNode(self, node):
        html = render_image_list_html(
            node.attributes.get("ls_images", ()),
            node.attributes.get("pt_images", ()),
            self.document.image_titles,
            self.image_path_to_url,
        )
        if html:
            self.body.append(html)

    def depart_ImageListNode(self, node):
        pass

    def visit_ImgNode(self, node):
        img = node.attributes["image_id"]
        url = self.image_path_to_url(img)

        klass = node.attributes.get("class")
        if klass:
            self.body.append(f'<div class="{klass}">')

        title = self.document.image_titles.get(img, "")
        if node.attributes.get("zoomable", False):
            self.body.append(
                f"""<div class="zoom-able">
                    <img src="{url}" alt="{title}"/>""")

            if title:
                self.body.append(f"""<div class="image-title">{title}</div>""")

            self.body.append('</div>')
        else:
            self.body.append(f'<div class="pic"><img src="{
                             url}" alt="{title}"/></div>')

        if klass:
            self.body.append(f'</div>')

    def depart_ImgNode(self, node):
        pass

    def visit_BackgroundNode(self, node):
        pass

    def depart_BackgroundNode(self, node):
        pass


def render_image_list_html(landscape, portrait, image_titles, image_path_to_url=lambda path: path):
    parts = []
    for images in (landscape, portrait):
        if not images:
            continue

        parts.append('<div class="image-list"><div class="text">double click to zoom</div>')

        for img in images:
            url = image_path_to_url(img)
            title = image_titles.get(img, "")
            parts.append(
                f"""<div class="zoom-able">
                        <img src="{url}" alt="{title}"/>"""
            )
            if title:
                parts.append(f"""<div class="image-title">{title}</div>""")
            parts.append('</div>')

        parts.append('</div>')

    return "".join(parts)


def write_images(dest_dir, images):
    img_dir = dest_dir / "img"
    img_dir.mkdir(exist_ok=True)
    for path, (id_, options) in images.items():
        if path.suffix == ".svg":
            shutil.copyfile(path, img_dir.parent / id_.replace("data/", ""))
            continue

        img = Image.open(path)

        if options.get("background"):
            img = img.resize(
                (1024, int(img.size[1] * (1024 / img.size[0]))), resample=Image.LANCZOS)

        if options.get("reduce"):
            if img.size[0] > 3500:
                img = img.resize(
                    (3500, int(img.size[1] * (3500 / img.size[0]))), resample=Image.LANCZOS)

            if img.size[1] > 3500:
                img = img.resize(
                    (int(img.size[0] * (3500 / img.size[1])), 3500), resample=Image.LANCZOS)


        quality = options.get("quality", 90)
        dest_path = (img_dir.parent / id_.replace("data/", ""))
        while True:
            img.save(dest_path, optimize=True, quality=quality)
            file_size = dest_path.stat().st_size
            if file_size < 2 * 1024 * 1024:
                break
            quality -= 5