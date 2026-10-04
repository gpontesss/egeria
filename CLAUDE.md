# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

**Egeria** — a generic gazetteer of Orthodox holy places, currently covering
Athens and Attica, Aegina, Patmos and Constantinople. Each entry records what
is physically there to venerate, what happened there, whose church or state
the place belongs to, and what it takes to get in, and is pinned on a map.

It is **for any reader**, not for one person's trip. The project began as a
single itinerary and was deliberately generalised; see `log.md`. Do not
reintroduce route-specific framing — "on this route", "the layover", a named
traveller's dates or jurisdiction. New regions are added as new content
folders, and the site is built to expect that.

It is a **web-first** project, built with [Hugo](https://gohugo.io/). This
is the deliberate contrast with its sibling `../materia-medica`, which is
book-first (Typst → PDF, with a website as a secondary output). **There is
no PDF target here and no plan for one.** See `log.md` for that decision
and the alternatives rejected.

## Build commands

```sh
make serve    # live-reloading preview at localhost:1313
make site     # build to out/site/
make check    # build with path warnings fatal
make new REGION=athens SLUG=agia-eirini
make clean
```

Hugo **0.167.0 extended** (`brew install hugo`). The version is pinned in
`.github/workflows/pages.yml` — **bump both together**, since template
lookup rules and config deprecations move between Hugo minors.

`out/` is gitignored and never committed; CI rebuilds it on every push to
`main` and deploys to GitHub Pages. Pages must have its source set to
"GitHub Actions" in the repo's Settings → Pages — a one-time manual step
the workflow cannot do for itself.

## Architecture

```
config/
  _default/hugo.toml             ← all config; production baseURL
  development/hugo.toml          ← localhost baseURL for `hugo server`
content/
  _index.md                      ← home page prose
  athens/ aegina/ patmos/ constantinople/
                                 ← one file per place; _index.md per region
  visiting/                      ← guidance that applies to every place
  saints/_index.md kinds/_index.md
                                 ← taxonomy landing pages (prose only)
layouts/
  baseof.html page.html section.html home.html taxonomy.html term.html
  home.sitesjson.json            ← emits /sites.json, the maps' only data source
  _partials/
    head.html header.html footer.html sidebar.html
    facts.html site-list.html map.html needs-map.html
assets/
  css/style.css                  ← all styling, one file
  js/nav.js js/map.js            ← left menu; Leaflet maps
  js/gallery.js                  ← lightbox, loaded only where photos exist
  js/theme.js                    ← light/dark; INLINED in <head>, see Gotchas
  images/egeria.png              ← the one image: frontispiece, mark, favicon
  photos/<section>/<slug>/       ← Commons photographs (see Photographs)
  vendor/leaflet/                ← Leaflet 1.9.4, vendored not CDN-loaded
data/photos/<section>/<slug>.yaml ← author, licence, source per photograph
tools/fetch_photos.py            ← fetches and audits them
archetypes/default.md            ← the entry template `make new` uses
```

**Adding a region** is a new folder under `content/` with an `_index.md`
carrying `region: true`, a `weight`, a `title` and a `blurb`. That flag is
what separates a geographic region (left menu, home page, map filter) from
`visiting/`, which is guidance. Nothing else needs touching.

**Regions are ordered by `weight` in their `_index.md`** (Athens 10, Aegina
20, Patmos 30, Constantinople 40, Visiting 90), so the left menu and home
page follow geography rather than the alphabet.

**Entries within a region are ordered by `weight` too, and the weight is
meaningful**: it ranks a place by what a first-time visitor would give up
last. Weighted entries appear first, in weight order; unweighted ones fall
into an
"Also in the area" tail, alphabetised. Adding a place therefore needs no
registration anywhere — drop the file in the region folder and it appears.

**Taxonomies**: `saints` and `kinds`. `saints` is the one that earns its
keep — it answers the question the site exists for, *whose relics can I
venerate and where* — and a saint is listed on an entry if their relics are
there, they lived or died there, or the church is dedicated to them. The
entry prose must say which of those it is; the taxonomy does not
distinguish.

**`relics` is a separate front-matter field from `saints`**, and means only
what is *physically present and offered for veneration*. Never infer one
from the other: a church dedicated to St George does not have St George's
relics.

**`summary` is a first-class field and every entry has one** — one line on
what is there to see. It drives the left menu, the region listings, the map
popups and the page's `<meta name="description">`, falling back to `relics`
and then to the first `kinds` value. Write it as the answer to "why would I
click this?", not as a restatement of the title.

## Entry front matter

```yaml
title: "Holy Trinity Monastery of St Nektarios"
native: "Ιερά Μονή Αγίας Τριάδος"    # local-language name, shown under the title
summary: "The relics, the tomb and the cell of St Nektarios of Aegina."
place: "Kontos, ~6 km from Aegina town"
kinds: ["monastery"]                  # taxonomy: monastery, church, cathedral,
                                      #   chapel, cave, holy spring, museum,
                                      #   ruin, monument, open site, mosque,
                                      #   ancient site, logistics
saints: ["Nektarios of Aegina"]       # taxonomy
relics: ["Relics of St Nektarios"]    # only what is physically there
feast: "9 November — St Nektarios"
jurisdiction: "Church of Greece (New Calendar) — a working convent"
status: "active"                      # active | museum | mosque | ruin
                                      #   | open site | restricted
access: "Open daily, free. Strict modest dress."
coords: [37.7336, 23.4836]            # → the entry's own map, a pin on the
                                      #   overview maps, and an OSM link
verified: false
weight: 10                            # omit to fall into "Also in the area"
```

Every field is optional and the facts block emits only the rows that are
set, so a stub entry renders cleanly rather than showing a grid of blanks.

Body sections, in this order, and only the ones that have something to say:
`## Why go` → `## What is there to venerate` → `## History` →
`## Practical notes`. Short entries are usually just *Why go* and
*Practical notes*, and that is correct — do not pad an entry to fill the
template.

## Content standards

These matter more than anything in the templates.

- **Never invent a relic, a dedication, or a tradition.** If it is not
  known, the entry says so or omits the claim. A plausible-sounding wrong
  relic is the single worst failure this project can have, because someone
  will travel on it.
- **`verified: false` until checked on the ground or against a printed
  source.** The page then prints a plain-text caveat. Clear the flag only
  when it has actually been verified, not when the prose merely feels
  confident.
- **Volatile facts get a hedge in the prose, not just the flag.** Opening
  hours, ferry timetables, which reliquaries are displayed, and the status
  of the reconverted Istanbul churches (Hagia Sophia 2020, Chora 2024) all
  change faster than this list can track. Say so in the entry.
- **Some entries are pointers on purpose** — the Patmos hermitages are the
  clearest case. Which cells can be visited depends on who is living in them
  and is not anyone's to publish; a plausible-looking wrong address is worse
  than no address, so the entry names the monastery to ask instead. **Do not
  "helpfully" fill these in from memory.**
- **State jurisdiction as fact and stop there.** The site records whose
  church a place is — Church of Greece, Ecumenical Patriarchate, a Slavic
  church, an Old Calendar synod, the Turkish state — so the reader knows what
  they are walking into. Whether and how a visitor of one jurisdiction should
  venerate in the church of another is a question for a priest, and this site
  does not answer it. Do not add pastoral advice, approval, or disapproval
  anywhere.
- **British spelling**, serial commas off, em dashes for parenthesis.
  Greek and Turkish names in the `native` field in their own script, with a
  transliteration or the Turkish name alongside where it helps.

## Styling

Typography is **inherited from the compiled Materia Medica PDF** and should
not drift from it. The full rationale is in `log.md`; the rules:

- **EB Garamond only**, Google Fonts, with the Greek subsets.
- Headings **1.4em / 1.2em / 1.1em**, all bold, sized in em.
- Justified paragraphs with `hyphens: auto`.
- Base **15pt**, 14pt under 30rem; `--max-measure: min(38rem, 92vw)`.
  **These two were tuned as a pair — move them together.**
- **No accent colour anywhere.** Dark mode is a monochrome inversion.
  Jurisdiction and verification status are conveyed in words, never in
  coloured badges — which is also the honest way to do it.
- The floating side TOC's `left` is computed from the viewport centre and
  `--max-measure`, never from a shared layout track. An earlier
  shared-grid version in Materia Medica visibly squeezed the article at
  medium widths. **Do not reintroduce a layout where the TOC and the
  article compete for width.**
- `--header-h` is a shared constant: the header's fixed height, what the
  sticky menu hangs from, and what `[id] { scroll-margin-top }` clears for
  every anchor target. Nothing in the header may wrap, or it stops being
  true.
- **Maps are monochrome too.** A grey basemap (not a colour one pushed
  through a filter), `circleMarker`s rather than pin images, and Leaflet's
  own blue links and focus rings overridden to the text colour. Dark mode
  inverts the tile pane and **only** the tile pane.

## Themes

Light and dark, by one rule: **the system preference decides until the reader
chooses, and then the choice wins and is remembered.** No `data-theme`
attribute means "follow the system"; `theme.js` sets it only on an explicit
choice. The CSS shape that makes this work is three blocks and must stay
intact:

```css
:root                              { light }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"])  { dark }   /* the :not() is load-bearing */
}
:root[data-theme="dark"]           { dark }
```

`color-scheme` is set per theme as well, so scrollbars and form controls
follow.

Anything drawn in JS has to be told about a change, because CSS variables
cannot reach it: `map.js` reads `data-theme` first (media query only as a
fallback) and restyles its markers on the `egeria:theme` event. If you add
another JS-drawn surface, listen for that event too.

## The portrait

One image, `assets/images/egeria.png`, rendered at three sizes through
`layouts/_partials/portrait.html`, which generates every derivative with Hugo
— **never reference the source file directly**, it is 694 KB. It is the
frontispiece on the home page, the mark beside the wordmark in the header,
and the favicon.

**It is not a portrait of Egeria, and the caption must keep saying so.** No
likeness of her survives; this is a Romano-Egyptian funerary portrait of the
Fayum type. The caption is `params.portraitCaption`. Do not "improve" it into
claiming it depicts her.

It is also the only colour on the site — a painted panel, the way a
frontispiece is in a book. That is not licence to introduce accent colour
into the interface; see Styling.

## URLs

Published at **https://gpontesss.github.io/egeria/** — a GitHub Pages
*project* site, so every internal link must carry the `/egeria/` path.

- **`relURL` is a no-op on input that starts with `/`.** `"saints/" | relURL`
  → `/egeria/saints/`; `"/saints/" | relURL` → `/saints/`. Always pass a
  relative path, or use `.RelPermalink` / `site.Home.RelPermalink`.
- Markdown content may write root-absolute links; `layouts/_markup/render-link.html`
  rewrites them (stripping the slash first, for the reason above).
- **The baseURL is per-environment, and must stay that way.**
  `config/_default/hugo.toml` holds the published URL;
  `config/development/hugo.toml` overrides it with `http://localhost:1313/`.
  `hugo server` runs in *development* automatically, so plain `hugo server`
  works with no flags; `hugo` builds *production*. Do not move the published
  baseURL back into the default config alone — the dev server would then
  serve pages at `/` with assets pointing at `/egeria/`, and the site renders
  as unstyled markup.
- `make preview` serves the built output at `localhost:8080`, rebuilding it
  against a root baseURL first, since the production build hardcodes
  `/egeria/` into every link.

After changing anything about linking, audit with:
`grep -rEo '(href|src)=/(?!egeria/)[^ >]*' out/site` — it should be empty.

## Photographs

Every place that has them shows a gallery on its entry page, a thumbnail in
every listing, and a photograph in its map popup. They come from **Wikimedia
Commons**, fetched by `tools/fetch_photos.py`:

```sh
python3 tools/fetch_photos.py --all              # fetch everything missing
python3 tools/fetch_photos.py --only athens/kapnikarea --dry-run
python3 tools/fetch_photos.py --all --force      # redo entries that have photos
python3 tools/fetch_photos.py --optimise         # re-encode to 1200px JPEG
python3 tools/fetch_photos.py --report           # audit matches and coordinates
```

Files land in `assets/photos/<section>/<slug>/`, metadata in
`data/photos/<section>/<slug>.yaml`. Both are committed; Hugo generates every
derivative at build time, so the site is self-contained and CI needs no
network.

### The lead photograph is not the first one

`photo-lead.html` picks the picture that stands for a place — the entry
hero, the listing thumbnail, the map popup — and all three use that one
partial so they cannot disagree. It skips files whose Commons title looks
like a print or carries an early date, because an old engraving often
matches a church's name better than a modern photograph does and the fetcher
ranks by match confidence. `lead: N` in front matter overrides it.

### Attribution is not optional

Most of these images are CC BY or CC BY-SA, which **require** the author and
licence to be shown wherever the image appears. The manifest carries
`author`, `licence`, `licenceUrl` and `source` for every file, and
`gallery.html` renders them in the lightbox and in the credits list. **Never
add a photograph without its manifest entry, and never strip those fields.**

### How a photograph is matched, and why it can be wrong

Three sources, best first:

1. **`category`** — the file is in a Commons category that was shown to be
   this place, either because the category name says so or because its other
   members are located at the right spot. Highest precision by far.
2. **`name`** — full-text search, *and* the file passed the locality check.
3. **`geo`** — Commons geosearch around the entry's coordinates.

Two guards do the real work, and both exist because they caught real
failures:

- **Locality.** A file with coordinates must be within 2.5 km (6 km for sites
  that are an area). A file without coordinates must name the region, or be
  in the category. Without this, "Metropolitan Cathedral of the Annunciation"
  returned Annunciation cathedrals in **Atlanta and Boston**.
- **Name.** A candidate that matches no word of the place's name and is not
  in its category is dropped outright, whatever the distance. Without this, a
  Flickr photograph about sky colour taken 2 km away was accepted as a
  monastery.

Category membership does **not** excuse a file from the distance check when
the file has its own coordinates — Commons files a scale replica of Hagia
Sophia in a Chinese theme park under `Category:Hagia Sophia`.

`found:` in the manifest records which source matched and how far away the
file was. **`(no name match)` means the image has not been confirmed to show
this place.** `--report` lists them.

### Fixing a bad match

Add `commons: "<search string or category>"` to the entry's front matter and
re-run with `--force`. That overrides every query the script would build.

### `--report` also audits the coordinates

When matched photographs cluster away from an entry's pin, the likelier
explanation is that **the pin is wrong**, not the photographs — this is how
the Patmos cave turned out to be pinned 1.5 km from the cave. Treat anything
over ~0.4 km as a coordinate to re-check.

## Maps

Every entry with `coords` renders its own map; the home page and each region
page render an overview. All of them read `/sites.json`, emitted by
`layouts/home.sitesjson.json` from the content itself — **so a new entry with
coordinates appears on the map with no registration anywhere.** The map
partial takes everything from data attributes; no page carries an inline
script.

Leaflet 1.9.4 is **vendored in `assets/vendor/`**, not loaded from a CDN, so
the only third-party request a page makes is for the tiles.

**Popups never pan the map** (`autoPan: false`, `keepInView: false`). With
hover-to-open, panning meant a pointer passing over an edge pin dragged the
view; a popup that does not fit is clipped by the container instead. Do not
re-enable autoPan to "fix" a cropped popup -- flip it below its marker
instead.

**Hovering a pin opens its popup; clicking pins it open.** The close is
delayed and cancellable rather than immediate -- on `mouseout` alone the
popup disappears before the pointer can reach the link inside it. If you
touch `hoverPopups` in `map.js`, keep the scheduled close and the popup's own
`mouseenter` cancel together; either one without the other breaks it.

**The wheel zooms the maps**, which means each map must also be able to give
the wheel back to the page: `releaseAtBounds` in `map.js` disables wheel zoom
once the map is stuck at its zoom limit in the direction being scrolled, and
re-arms it when the wheel goes quiet. That only works because each map has a
`minZoom` floor (`MIN_ZOOM_SINGLE`, `MIN_ZOOM_OVERVIEW`) -- with Leaflet's
default of 0, "stuck" meant the whole world and the page would never scroll
past. Do not remove either half.

**Pins are labelled with the place's name below them**, but only as permanent
labels above zoom 11 (`LABEL_ZOOM` in `map.js`) -- the overview opens on the
whole Aegean, where forty permanent labels overlap into noise, and reverts to
hover tooltips there. Leaflet fixes a tooltip's `permanent` flag at bind time,
so crossing the threshold rebinds them all; that happens on `zoomend` and only
on an actual crossing. Label text is the title with parentheses stripped and
truncated, and is styled with a `var(--bg)` halo rather than a box so it works
in both themes.

**Tiles are Esri's World Light Gray Canvas** plus its Reference labels
overlay: keyless, and grey by design. Swapping provider is the `tiles`,
`tilesLabels`, `tilesMaxZoom` and `tileAttribution` params in `hugo.toml` and
nothing else — but check `log.md` first, because Carto (now key-walled) and
openstreetmap.org (503s to browser embeds) were both tried and rejected.

## Gotchas

- **`.Fragments.Headings` nests**, so its top-level length is 1 on a page
  whose headings are all sibling `h2`s. Count `.Fragments.Identifiers` —
  the flat list — when deciding whether an entry gets a sidebar TOC.
  `layouts/page.html` does this; it was a real bug, not a theoretical one.
- **`theme.js` is inlined in `<head>` on purpose.** Linked or deferred, the
  stored theme would be applied after first paint and every page load would
  flash the other theme. Keep it small; do not move it to a `<script src>`.
- **Listing headings use `.page-title`, not `.entry`.** `.entry` carries
  `max-width: var(--max-measure)` and auto margins along with the heading
  size, which silently indents a heading on any column wider than the
  measure — it is what gave the home page two different left edges.
- **Widen a column, not the blocks inside it.** The home page is
  `.listing-wide`; prose within it stays at the measure via `.lead` and
  `.region-blurb`. Only a block on a measure-width page (`.map-region`)
  should break out with negative margins.
- **Nothing in the header may wrap.** Its height is `--header-h`, which the
  sticky sidebar and every anchor's `scroll-margin-top` depend on. The index
  links are hidden below 30rem for exactly this reason; add header content
  with that budget in mind.
- **Leaflet's stylesheet must load before `style.css`.** It styles its links,
  controls and popups with single-class selectors; if it loads last it wins
  every specificity tie on source order and the site's overrides silently do
  nothing while appearing fine in the built CSS. `needs-map.html` decides up
  front whether a page has a map so that `head.html` can emit `leaflet.css`
  early. Do not "fix" an override by inflating its selector instead.
- **`.map` IS the Leaflet container**, not its ancestor — `L.map(el)` adds
  Leaflet's classes to that same div. Container-level rules must be compound
  (`.map.leaflet-container`), not descendant.
- **Chrome rings a clicked SVG path on plain `:focus`**, not only
  `:focus-visible`; a focus-ring override has to cover both.
- A marker's tooltip and its popup open at once, and the tooltip pane comes
  *before* the popup pane in the DOM, so no sibling combinator reaches it.
  Suppressed with `:has()` on their common parent.
- Hugo 0.146+ wants partials in **`layouts/_partials/`**, and templates at
  `layouts/page.html` rather than `layouts/_default/single.html`. The legacy
  paths still resolve but are deprecated.
- Config uses **`locale`**, not `languageCode` (deprecated in 0.158).
- `baseURL` in `hugo.toml` is a placeholder; CI overrides it from the Pages
  deployment, so the committed config does not need the real URL.

## Maintenance rules

- **Update `log.md`** on any non-trivial decision (tooling, content model,
  typography, a new region). Record the problem, the decision, the
  reasoning, and what was rejected.
- **Update this file** when commands, architecture, or conventions change.
- **Do not commit.** Leave git staging and committing to the user.
