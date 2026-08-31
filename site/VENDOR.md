# Vendored assets

Third-party files copied into this repo rather than installed. Each row records
where it came from and the commit it was taken at, so a refresh is a copy from a
checkout at a known point and never a guess.

| File | Source | Commit | Why vendored |
|---|---|---|---|
| `public/vendor/concept-tree-3d.bundle.js` | github.com/mithudso/json-3d-renderer | `d78ec82` | the 3D view must load offline and from our own origin; the upstream repo ships the bundle, not a package |

Refresh: copy the file again from a checkout at the commit you want and update
this row. The bundle is three.js + three-spritetext + 3d-force-graph in one
file; it sets `window.ForceGraph3D` and `window.SpriteText` and takes no data
of its own — `src/components/Tree3D.astro` feeds it the graph.
