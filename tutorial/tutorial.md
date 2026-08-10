# Tutorial: Add Climbing Content (No Programming Needed)

This guide shows how to add content to the climbing guide without writing code.

You will learn how to:

1. Add a new route to an existing sector (example: Rainbow Warriors in Smokovac).

## Before You Start

For this tutorial, you only edit files in `docutil/`:

1. the sector `.rst` file,
2. the matching topo `.svg` file.


For each change, work in this order:

1. Update the relevant `.rst` document.
2. If needed, update the matching `.svg` topo file.
3. Make sure route names and topo IDs match exactly.

## 1) Add a New Route to an Existing Sector

Example: add `Rainbow Warriors` in Smokovac.

### Files to edit (Route)

- `docutil/podgorica/smokovac/sector-d.rst` (route list)
- `docutil/podgorica/smokovac/sector-d.svg` (route line in topo)

### Steps (Route)

1. Open `docutil/podgorica/smokovac/sector-d.rst`.
2. Find a place where routes are listed (`.. route:: ...`).
3. Copy an existing route block and paste it where your new route should appear.
4. Update the fields.
5. Save the file.

Use this template:

```rst
.. route:: Rainbow Warriors
    :grade:  7a
    :length:  22
    :stars:  2
    :created:  2026
    :creator:  Your Name
    :first-ascent:
    :style:  technical
    :steepness:  vertical
    :other:

    Short comment about the route.
```

### Add the route line in the topo ([SVG-Edit](https://svgedit.netlify.app/index.html))

1. Open [SVG-Edit](https://svg-edit.github.io/svgedit/) and load `docutil/podgorica/smokovac/sector-d.svg`.
2. Draw the new route line as a path.
3. Select the new path and set its element `id`.
4. Use an ID that matches the route name format used by the compiler:
   - lowercase,
   - spaces become `-`,
   - `:` becomes `-`,
   - accented letters are converted to plain ASCII.
5. Example ID conversions:
   - `Rainbow Warriors` -> `rainbow-warriors`
   - `Ogi I Matija` -> `ogi-i-matija`
   - `Čista Petica` -> `cista-petica`
6. Save the SVG file.

If you need a custom ID (for duplicate names or special cases), set the same value in both places:

```rst
.. route:: Rainbow Warriors
    :topo-id: rainbow-warriors-2
```

And in SVG set the path `id` to `rainbow-warriors-2`.

### Notes

- Keep the same indentation as other routes (4 spaces before `:grade:` etc.).
- If you have two routes with exactly the same name, add `:topo-id:`.
- Valid `:style:` examples: `technical`, `endurance`, `pockets`, `tufa`.
- Valid `:steepness:` examples: `slab`, `vertical`, `overhang`, `roof`.

## Notice

If you want to add a new sector or area call us.

## Common Mistakes (And How to Avoid Them)

1. **Sector or area does not appear**
    - Cause: this tutorial does not cover sector/area creation.
    - Fix: contact us.

2. **Map marker does not show**
    - Cause: this tutorial is route-only and does not include marker editing.
    - Fix: contact us.

3. **Compile errors after editing**
   - Cause: wrong indentation or broken directive syntax.
   - Fix: compare your block with a nearby working block.

4. **Wrong file name case**
   - Cause: Linux is case-sensitive (`Disco.rst` is different from `disco.rst`).
   - Fix: match file names exactly in `.. include::`.

## Document Checklist

Before you finish, verify these document links and names:

1. The route exists in the correct sector `.rst` file.
2. The topo file named in `.. topo:: ...` exists in the same folder.
3. Route path `id` values in the topo SVG match route names (or `:topo-id:` values).

## Helpful References

- Directive reference: `docutil/README.md`
- Smokovac route example: `docutil/podgorica/smokovac/sector-d.rst`
