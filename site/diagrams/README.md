# Diagram sources (d2)

Diagrams on this site are drawn with [d2](https://d2lang.com) and committed as static SVG assets
under `site/public/diagrams/`, the same way `Anth.us/diagrams/` commits its `.d2` sources
alongside the images they render. There is no build-time dependency on the `d2` binary: the
rendered SVGs are what the site actually serves, so `make site` and CI need nothing extra
installed.

To re-render a diagram after editing its source:

```bash
d2 site/diagrams/<name>.d2 site/public/diagrams/<name>.svg
```

Palette matches `site/src/styles/site.css`: background `#f1f9fe`, ink `#0c1e2b`, rule `#cfdfea`,
alarm red `#c8102e`. Keep new diagrams to that palette so they sit naturally on the page.
