from html import escape
from pathlib import Path
import ast
import json
import re
import shutil
import sys

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "contribution-guide" / "site"
DATA_OUTPUT = OUTPUT / "data"
DOCUTIL = ROOT / "docutil"
GUIDE = DOCUTIL / "guide.rst"
SCRIPTS = ROOT / "scripts"
DIRECTIVE_README = DOCUTIL / "README.md"
SVGEDIT_PATCH = ROOT / "contribution-guide" / "svgedit-patch.js"
CONTRIBUTION_ASSETS = ROOT / "contribution-guide" / "assets"
SVGEDIT_CDN_EDITOR = "https://cdn.jsdelivr.net/npm/svgedit@7.4.2/dist/editor"
GITHUB_REPOSITORY_URL = "https://github.com/kochelmonster/climbers-heaven-guide"
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/kochelmonster/climbers-heaven-guide/develop/docutil"
)

INCLUDE_RE = re.compile(r"^\.\.\s+include::\s*(\S+)\s*$")
TOPO_RE = re.compile(r"^\.\.\s+topo::\s*(\S+)\s*$")
ROUTE_RE = re.compile(r"^\.\.\s+route::")
UNDERLINE_RE = re.compile(r"^([=\-~*^\"'`#+_:.])\1{1,}\s*$")

# Enum values that docutil/README.md does not spell out.
EXTRA_OPTION_VALUES = {
    "geolocation": {
        "direction": ["n", "ne", "e", "se", "s", "sw", "w", "nw"],
        "show-title": ["yes", "no"],
    },
    "geomap": {"style": ["map", "satellite"]},
    "routestatistics": {"summary": ["e", "w", "n"]},
    "attributes": {"children": ["yes", "no"]},
}


def inline_markup(text):
    text = escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render_markdown(markdown):
    output = []
    in_code = False
    code_lines = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for line in markdown.splitlines():
        if line.startswith("```"):
            if in_code:
                output.append("<pre><code>" + escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
            else:
                close_list()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        image = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image:
            close_list()
            alt, source = image.groups()
            output.append(f'<figure><img src="{source}" alt="{escape(alt, quote=True)}"></figure>')
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline_markup(heading.group(2))}</h{level}>")
            continue
        item = re.match(r"^[-*]\s+(.+)$", line)
        if item:
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline_markup(item.group(1))}</li>")
            continue
        if not line.strip():
            close_list()
            continue
        close_list()
        output.append(f"<p>{inline_markup(line)}</p>")

    close_list()
    return "\n".join(output)


def iter_included_rst(path, seen=None):
    """Walk the ``.. include::`` tree in document order."""
    seen = set() if seen is None else seen
    resolved = path.resolve()
    if resolved in seen or not path.is_file():
        return []
    seen.add(resolved)
    result = [path]
    for line in path.read_text(encoding="utf-8").splitlines():
        match = INCLUDE_RE.match(line)
        if match:
            result.extend(iter_included_rst(path.parent / match.group(1), seen))
    return result


def section_title(lines):
    for index, line in enumerate(lines):
        text = line.strip()
        if not text or UNDERLINE_RE.match(line):
            continue
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if UNDERLINE_RE.match(following) and len(following.strip()) >= len(text):
            return text
    return ""


def describe_rst(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    topos = []
    for line in lines:
        match = TOPO_RE.match(line)
        if not match:
            continue
        topo = path.parent / match.group(1)
        if topo.is_file():
            topos.append(topo)
        else:
            print(f"warning: {path.name} references missing topo {match.group(1)}")

    relative = path.relative_to(DOCUTIL)
    return {
        "rst": relative.as_posix(),
        "area": relative.parent.as_posix().replace("/", " / "),
        "title": section_title(lines) or path.stem,
        "routes": sum(1 for line in lines if ROUTE_RE.match(line)),
        "topos": [topo.relative_to(DOCUTIL).as_posix() for topo in topos],
    }


def collect_sectors():
    sectors = []
    for path in iter_included_rst(GUIDE):
        entry = describe_rst(path)
        if entry["routes"] or entry["topos"]:
            sectors.append(entry)
    return sectors


def import_directive_specs():
    sys.path.insert(0, str(SCRIPTS))
    try:
        import compile_guide  # noqa: F401  importing registers the directives
        from docutils.parsers.rst import directives
    finally:
        sys.path.remove(str(SCRIPTS))

    return {
        name: {
            "arguments": cls.required_arguments,
            "content": bool(cls.has_content),
            "options": sorted(cls.option_spec or {}),
        }
        for name, cls in directives._directives.items()
    }


def scan_directive_specs():
    """Static fallback for environments without the compiler dependencies."""
    specs = {}
    for module in (SCRIPTS / "compile_guide.py", SCRIPTS / "images.py"):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        classes = {}
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            spec = {"arguments": 0, "content": False, "options": []}
            for statement in node.body:
                if not isinstance(statement, ast.Assign):
                    continue
                target = statement.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                try:
                    value = ast.literal_eval(statement.value)
                except ValueError:
                    value = None
                if target.id == "required_arguments":
                    spec["arguments"] = value or 0
                elif target.id == "has_content":
                    spec["content"] = bool(value)
                elif target.id == "option_spec" and isinstance(statement.value, ast.Dict):
                    spec["options"] = sorted(
                        key.value
                        for key in statement.value.keys
                        if isinstance(key, ast.Constant)
                    )
            classes[node.name] = spec

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "register_directive"
                and len(node.args) == 2
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[1], ast.Name)
            ):
                specs[node.args[0].value] = classes[node.args[1].id]
    return specs


def load_directive_specs():
    try:
        return import_directive_specs()
    except Exception as error:
        print(f"warning: reading directives statically ({error})")
        return scan_directive_specs()


def load_directive_docs():
    """Read directive and option descriptions from docutil/README.md."""
    lines = DIRECTIVE_README.read_text(encoding="utf-8").splitlines()
    docs = {}
    current = None
    in_fence = False
    for index, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = re.match(r"^##\s+(\S+)", line)
        if heading:
            current = docs.setdefault(heading.group(1), {"doc": "", "options": {}})
            continue
        if current is None or not line.strip():
            continue

        following = lines[index + 1] if index + 1 < len(lines) else ""
        if following.startswith(":") and not line.startswith((" ", "#", ":")):
            text = following[1:].strip()
            values = re.search(r"Possible values:\s*([^.]+)", text)
            current["options"][line.strip()] = {
                "doc": text,
                "values": [v.strip() for v in values.group(1).split(",")] if values else [],
            }
        elif not current["doc"] and not line.startswith(":"):
            current["doc"] = line.strip()
    return docs


def directive_metadata():
    docs = load_directive_docs()
    metadata = {}
    for name, spec in sorted(load_directive_specs().items()):
        described = docs.get(name, {"doc": "", "options": {}})
        options = {}
        for option in spec["options"]:
            info = described["options"].get(option, {"doc": "", "values": []})
            values = info["values"] or EXTRA_OPTION_VALUES.get(name, {}).get(option, [])
            options[option] = {"doc": info["doc"], "values": values}
        metadata[name] = {
            "doc": described["doc"],
            "arguments": spec["arguments"],
            "content": spec["content"],
            "options": options,
        }
    return metadata


def topo_link(topo):
    source = GITHUB_RAW_BASE + "/" + topo
    return f"svg-edit/index.html?url={source}&noStorageOnLoad=1&storagePrompt=false"


def render_svg_editor_wrapper():
    return '''<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge, chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="icon" href="{editor}/images/logo.svg">
    <style id="styleoverrides" media="screen"></style>
    <link href="{editor}/svgedit.css" rel="stylesheet" media="all">
    <script type="module" src="{editor}/browser-not-supported.js"></script>
    <title>SVG-edit</title>
</head>
<body style="margin:0">
    <div id="container" style="width:100%;height:100vh"></div>
    <noscript>SVG-Edit requires JavaScript.</noscript>
    <script type="module">
        import Editor from '{editor}/Editor.js'
        import {{ applySvgEditPatch }} from './svgedit-patch.js'

        const svgEditor = new Editor(document.getElementById('container'))
        svgEditor.setConfig({{
            initFill: {{ color: 'none', opacity: 1 }},
            initStroke: {{ color: 'FF0000', opacity: 1, width: 2 }},
            imgPath: '{editor}/images',
            extPath: '{editor}/extensions',
            allowInitialUserOverride: true,
            extensions: [],
            noDefaultExtensions: false,
            userExtensions: []
        }})
        applySvgEditPatch(svgEditor)
    </script>
</body>
</html>
'''.format(editor=SVGEDIT_CDN_EDITOR)


def render_index(sectors):
    output = [
        "<h1>Climbers Heaven Contribution Guide</h1>",
        "<h2>Add a route</h2>",
        "<ol class=\"contribution-steps\">",
        "<li>Choose a sector below and click its name to open the sector RST file. "
        "Add the route in the correct position: routes are listed from left to right, "
        "matching their positions on the topo. Tip: Copy an existing route entry and update "
        "it with the new route's details. Download the edited RST file.</li>",
        "<li>Click the sector's topo SVG file. It opens in SVG-Edit with the topo already loaded. "
        "Use the Path tool to draw the new route line.",
        '<figure><img src="assets/step10.svg" alt="Path tool"></figure>',
        "Select the new path and set its ID to the route name in lowercase, with spaces "
        "replaced by hyphens. For example, the ID for \"The last rope jump\" is "
        "<code>the-last-rope-jump</code>.",
        '<figure><img src="assets/step11.svg" alt="Set path ID"></figure>',
        "Download the edited topo SVG file and keep its original filename.</li>",
        "<li>Send the downloaded RST description file and SVG topo file to the guide maintainer.</li>",
        "</ol>",
    ]
    areas = {}
    for entry in sectors:
        areas.setdefault(entry["area"], []).append(entry)

    for area, entries in areas.items():
        output.append(f"<h2>{escape(area)}</h2>")
        output.append('<ul class="file-index">')
        for entry in entries:
            links = [
                f'<a href="edit/?file={escape(entry["rst"], quote=True)}" target="_blank" rel="noopener">'
                f'{escape(entry["title"])}</a>'
            ]
            if entry["routes"]:
                links.append(f'<span class="routes">{entry["routes"]} routes</span>')
            for topo in entry["topos"]:
                name = topo.rsplit("/", 1)[-1]
                links.append(
                    f'<a class="topo" target="_blank" rel="noopener" '
                    f'href="{escape(topo_link(topo), quote=True)}">{escape(name)}</a>'
                )
            output.append("<li>" + "".join(links) + "</li>")
        output.append("</ul>")
    return "\n".join(output)


IMPORT_MAP = {
    "@codemirror/autocomplete": "https://esm.sh/*@codemirror/autocomplete@6.18.6",
    "@codemirror/commands": "https://esm.sh/*@codemirror/commands@6.8.0",
    "@codemirror/language": "https://esm.sh/*@codemirror/language@6.10.8",
    "@codemirror/lint": "https://esm.sh/*@codemirror/lint@6.8.4",
    "@codemirror/search": "https://esm.sh/*@codemirror/search@6.5.8",
    "@codemirror/state": "https://esm.sh/*@codemirror/state@6.5.2",
    "@codemirror/view": "https://esm.sh/*@codemirror/view@6.36.2",
    "@lezer/common": "https://esm.sh/*@lezer/common@1.2.3",
    "@lezer/highlight": "https://esm.sh/*@lezer/highlight@1.2.1",
    "@lezer/lr": "https://esm.sh/*@lezer/lr@1.4.2",
    "@marijn/find-cluster-break": "https://esm.sh/*@marijn/find-cluster-break@1.0.2",
    "codemirror": "https://esm.sh/*codemirror@6.0.1",
    "crelt": "https://esm.sh/*crelt@1.0.6",
    "style-mod": "https://esm.sh/*style-mod@4.1.2",
    "w3c-keyname": "https://esm.sh/*w3c-keyname@2.2.8",
}


def render_editor():
    body = """<h1 id="filename">Sector description</h1>
<div id="editor"><textarea id="fallback" spellcheck="false"></textarea></div>
<div class="toolbar">
<button id="download" type="button">Download</button>
<button id="copy" type="button">Copy to clipboard</button>
<span id="status"></span>
</div>
<p>Edit the file, download it and send it to the guide maintainer.</p>"""
    head = (
        '<script type="importmap">'
        + json.dumps({"imports": IMPORT_MAP})
        + '</script>\n<script type="module" src="../rst-editor.js"></script>'
    )
    return page("Edit sector description", body, root="../", head=head)


def page(title, body, root="../", head=""):
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{root}style.css">
{head}
</head>
<body>
<header><a href="{repository_url}">Climbers Heaven Contribution Guide</a></header>
<main>{body}</main>
</body>
</html>
'''.format(
        title=escape(title),
        root=root,
        head=head,
        repository_url=escape(GITHUB_REPOSITORY_URL, quote=True),
        body=body,
    )


def build():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    DATA_OUTPUT.mkdir(parents=True)
    shutil.copy(ROOT / "contribution-guide" / "style.css", OUTPUT / "style.css")
    shutil.copy(ROOT / "contribution-guide" / "rst-editor.js", OUTPUT / "rst-editor.js")
    assets_output = OUTPUT / "assets"
    assets_output.mkdir()
    for name in ("step10.svg", "step11.svg"):
        shutil.copy(CONTRIBUTION_ASSETS / name, assets_output / name)
    editor_dir = OUTPUT / "svg-edit"
    editor_dir.mkdir()
    (editor_dir / "index.html").write_text(render_svg_editor_wrapper(), encoding="utf-8")
    shutil.copy(SVGEDIT_PATCH, editor_dir / "svgedit-patch.js")

    sectors = collect_sectors()
    (DATA_OUTPUT / "files.json").write_text(json.dumps(sectors, indent=1), encoding="utf-8")
    (DATA_OUTPUT / "directives.json").write_text(
        json.dumps(directive_metadata(), indent=1), encoding="utf-8"
    )
    (OUTPUT / "edit").mkdir()
    (OUTPUT / "edit" / "index.html").write_text(render_editor(), encoding="utf-8")
    (OUTPUT / "index.html").write_text(
        page("Climbers Heaven Contribution Guide", render_index(sectors), root=""), encoding="utf-8"
    )
    print(f"Built {OUTPUT} with {len(sectors)} sectors.")


if __name__ == "__main__":
    build()

