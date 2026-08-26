# Contribution guide

Run `python contribution-guide/build.py` from the repository root to generate the static site in
`contribution-guide/site/`.

The generated site contains:

- an index of every sector `.rst` file reachable from `docutil/guide.rst` that has routes or a topo,
- integrated instructions for adding a route before the sector index, including the path-drawing and
  path-ID screenshots (copied from `contribution-guide/assets/` into `contribution-guide/site/assets/`),
- a local wrapper page for SVG-Edit; it loads editor assets from jsDelivr (`svgedit@7.4.2`) and topo links open it with the topo already loaded via `?url=`,
- an in-browser reStructuredText editor at `edit/?file=<path>` with highlighting and
  autocompletion for the custom docutils directives.

Contributors download the edited file and send it to the guide maintainer; the site is static and
writes nothing back.

The contribution guide links to the [Climbers Heaven GitHub repository](https://github.com/kochelmonster/climbers-heaven-guide).
RST and topo files are loaded directly from its `develop` branch under `docutil/`. The build does not
generate a local `source/` directory, so the guide needs internet access for contributor files as well
as for the SVG-Edit CDN.

The editor loads CodeMirror 6 from `esm.sh` through an import map, so it needs internet access.
Without it the page falls back to a plain text area.

Autocompletion data is generated from `scripts/compile_guide.py` (the directives' `option_spec`)
and `docutil/README.md` (descriptions and allowed values). If the compiler dependencies are not
installed, the build reads the directives statically instead and prints a warning.

New route paths use fill `none`, stroke `red`, and stroke width `2`.
