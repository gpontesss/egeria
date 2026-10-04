# log.md

Decisions worth not re-litigating. Newest last.

## 2026-10-03 — The project, and why Hugo rather than Typst

Egeria is a list of Orthodox pilgrimage sites for one journey: Athens and
Attica, Aegina, Patmos, and a single 23-hour layover in Istanbul.

The sibling project `../materia-medica` is **book-first**: entries are
Typst, the artefact is a print-ready PDF, and the website is generated from
the same sources as a secondary output. Egeria is deliberately the other
way round. A pilgrimage list is consulted on a phone, in a street, next to
a locked church door — it wants deep links, per-place pages, a saints
index, map links and search far more than it wants a justified 5×8in page.
There is no PDF target and no plan for one.

**Decision: Hugo** (0.167.0, extended, via Homebrew), with a small
hand-rolled theme in `layouts/` rather than any external theme.

Alternatives considered:

- *Typst with the HTML backend*, as Materia Medica does it. Rejected: the
  HTML backend is still experimental, and Materia Medica only tolerates it
  because the PDF is the real artefact and the site is a bonus. Here the
  site **is** the artefact, so betting it on an experimental backend is the
  wrong way round.
- *A hand-written static site*, as `materia-medica/site/build.py` is. The
  Python generator there is ~450 lines and reimplements taxonomies, nav,
  search and a TOC. Hugo has all of it, and the entry count here will be
  larger and churn more.
- *An off-the-shelf Hugo theme*. Rejected: the styling requirement is to
  match the Materia Medica PDF exactly, so every theme would be fought
  rather than used. The hand-rolled theme is five templates and three
  partials.

## 2026-10-03 — Styling inherited from the Materia Medica PDF

The brief was to match the compiled Materia Medica PDF's typography. Taken
from `../materia-medica/materia-medica.typ` and
`../materia-medica/site/assets/style.css`:

- **EB Garamond** as the only typeface, from Google Fonts with the Greek
  subsets loaded (entry prose carries Greek names and the odd polytonic
  quotation — Materia Medica needed Devanagari fallback, this project does
  not).
- Headings at Typst's own default ratios, **1.4em / 1.2em / 1.1em**, all
  bold, sized in em so they track the base size.
- **Justified paragraphs with `hyphens: auto`**, matching the PDF's
  `#set par(justify: true)`.
- **Base size 15pt**, dropping to 14pt under 30rem, and
  `--max-measure: min(38rem, 92vw)`. These two were tuned together in
  Materia Medica and are carried over as a pair.
- **Pure black on white, no accent colour anywhere.** Dark mode is a true
  monochrome inversion, not a second palette. Jurisdiction and verification
  status are therefore conveyed in words, never in coloured badges — which
  is also the honest way to do it.
- The floating side TOC's `left` is computed from the viewport centre and
  `--max-measure` so it never shares a layout track with the article. This
  is a fix carried over from Materia Medica, where an earlier shared-grid
  version visibly squeezed the article at medium widths. Do not reintroduce
  that.

Not carried over: the PDF's fixed 5in page width (this is web-first, the
measure adapts), the two-column outline front page, and the Devanagari
fallback.

## 2026-10-03 — `.Fragments.Identifiers`, not `.Fragments.Headings`

The sidebar TOC should appear only on entries with more than one section.
`len .Fragments.Headings` returns **1** on a page whose headings are all
sibling `h2`s, because that collection is nested — so the condition was
false everywhere and no entry ever got a sidebar.
`.Fragments.Identifiers` is the flat list of every heading id and is what
to count. Fixed in `layouts/page.html`.

## 2026-10-03 — Verification is a first-class field

Every entry carries `verified: false` until it has been checked on the
ground or against a printed source, and the page then prints a plain-text
caveat. This was a deliberate choice over writing confident prose: much of
what this site needs — opening hours, which reliquaries are currently
displayed, whether a converted church is open this month — changes faster
than any list can track, and three entries (Chora, the GOC parishes in
Athens, Daphni's hours) are actively volatile.

Two entries are **pointers rather than lists on purpose**: the GOC presence
in Athens, and the Patmos hermitages. In both cases a plausible-looking
wrong address would be worse than no address, so the entry says where to
get the real one.

## 2026-10-03 — Generic gazetteer, not one person's trip

The first draft was written around a specific journey: a 23-hour Istanbul
layover, ferries from Piraeus on particular dates, and a calendar page
addressed to an Old Calendarist reader. All of it is gone.

Deleted outright: the layover itinerary, the ferries-and-transport page, and
the entry on the Genuine Orthodox Church in Athens. Rewritten generically:
the home page, all four region introductions, *Calendars and jurisdictions*
(now an explainer of what the calendar difference does to a feast date, for
a reader of any jurisdiction), and *Dress, veneration and what to carry*.
Several dozen sentences across the entries that said "on this route", "the
layover" or "you will pass it" were rewritten.

**The jurisdiction field stayed, and so did the rule about it.** Every entry
names whose church or state a place belongs to, because that changes what a
visit is — a functioning church, a state museum, a working mosque, an open
ruin. The site states that as fact and goes no further: whether a visitor of
one jurisdiction should venerate in the church of another is a question for a
priest. That was true when the site was written for one reader and is more
obviously true now.

`practicalities/` became `visiting/`, and gained *How to read an entry*.

## 2026-10-03 — The left menu, and `summary` as a first-class field

The menu lists regions as `<details>` disclosures, each place inside it with
a one-line summary of what is there. That summary is a new front-matter
field on every entry, and it is used in four places: the menu, the region
listings, the map popups, and the `<meta name="description">`. It falls back
to `relics`, then to the first `kinds` value, so an entry without one still
renders.

The menu is a grid column at >=60rem and an off-canvas drawer below it.
The drawer slides with `transform`, not `display`, so the scroll position
nav.js sets (centring the current entry) survives opening and closing.

The entry contents nav moved from the left to the right, since the left is
now the menu's, and only appears as a floating panel at >=88rem; below that
it is an ordinary block in the article. It is still positioned from the
centre of the content column and `--max-measure`, never from a shared grid
track.

## 2026-10-03 — Maps: three tile providers before one worked

Every entry with `coords` gets its own map; the home page and each region
page get an overview built from `/sites.json`, which the home page emits as
a custom Hugo output format from the content itself — so a new entry with
coordinates appears on the map with no registration anywhere.

Leaflet is **vendored into `assets/vendor/`** rather than loaded from a CDN,
so the only third-party request a page makes is for the tiles.

Tile providers, in the order they were tried:

1. **Carto light_all/dark_all** — the obvious choice for a black-and-white
   site. Now stamps "API KEY REQUIRED" across every tile.
2. **openstreetmap.org**, desaturated with a CSS filter. Fine from curl, but
   returns **503 to browser embeds** often enough to leave the map half
   blank. OSM's tile policy does not cover this use anyway.
3. **Esri World Light Gray Canvas** (+ its Reference labels overlay) —
   keyless, and grey by design rather than a colour map pushed through a
   filter. This is what is in use. Max zoom 16, which `tilesMaxZoom` feeds
   to both the layers and every `fitBounds`.

Dark mode inverts the tile pane — and **only** the tile pane, never
`.leaflet-container`, so markers, popups and controls keep their own
colours. Markers are `circleMarker`s rather than pin images: monochrome, and
no marker PNGs needed from the vendored Leaflet.

## 2026-10-03 — Load Leaflet's stylesheet before style.css

Leaflet styles its own links (`#0078A8`), controls and popups with
single-class selectors. With `leaflet.css` loading last, every override in
`style.css` lost the specificity tie on source order and silently did
nothing — the popup link stayed blue and the focus ring stayed blue, while
the rules were visibly present in the built CSS.

The fix is ordering, not a specificity arms race: `layouts/_partials/needs-map.html`
decides up front whether a page will render a map, `baseof.html` computes it
before calling `head.html`, and the head emits `leaflet.css` *before*
`style.css`. Leaflet's JS still loads at the end of the body.

Two related traps found at the same time:

- **`.map` IS the Leaflet container**, not its ancestor — `L.map(el)` adds
  its classes to that same div. `.map .leaflet-container` matched nothing;
  the selector has to be compound, `.map.leaflet-container`.
- **Chrome rings a clicked SVG path on plain `:focus`**, not only
  `:focus-visible`, so the focus-ring override has to cover both.

## 2026-10-03 — A marker's tooltip and its popup both opened at once

Clicking a pin left the hover tooltip open behind the popup, showing as a
stray bordered box. The tooltip pane comes *before* the popup pane in the
DOM, so no sibling combinator can reach it from the popup. Fixed in CSS with
`:has()` on their common parent:
`.map .leaflet-map-pane:has(.leaflet-popup) .leaflet-tooltip-pane { display: none }`.

## 2026-10-03 — An explicit theme toggle, not only the system preference

The site already had light and dark palettes keyed to `prefers-color-scheme`.
It now also has a toggle, and the two coexist by one rule: **the system
decides until the reader chooses, and then the choice wins and is
remembered.** In CSS that is the existing three-block shape —

```
:root                                       { light }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"])           { dark }
}
:root[data-theme="dark"]                    { dark }
```

— so no attribute means "follow the system", and `data-theme` is set only by
an explicit choice. `color-scheme` is set per theme too, so the browser's own
surfaces (scrollbars, form controls) follow rather than keeping the other one.

**`theme.js` is inlined in `<head>`, not linked.** A deferred script would
apply the stored theme after first paint, and the reader would see a flash of
the other theme on every page load. That is the only reason it is inline, and
the reason it has to stay small.

Two things the toggle has to reach that CSS cannot:

- **The map markers**, which are drawn in JS. `map.js` now reads the
  `data-theme` attribute first and the media query only as a fallback — never
  the media query alone, or a toggled page gets markers in the wrong colour —
  and restyles every marker on an `egeria:theme` event.
- **The button itself**, which ships with `hidden` and is revealed by the
  script, so a reader with JS off gets no inert control.

## 2026-10-03 — The portrait: frontispiece, header mark, favicon

One image, `assets/images/egeria.png`, used at three sizes through a single
`portrait.html` partial, with Hugo generating every derivative — the 694 KB
source is never served. Frontispiece beside the home-page intro, a 1.65rem
mark beside the wordmark in the header, and the 32px/180px favicons.

**The caption says what the picture actually is.** No likeness of Egeria
survives; this is a Romano-Egyptian funerary portrait of the Fayum type, of
an unrelated woman, painted somewhat before her time. Captioning it as her
would be the one dishonest thing on a site whose whole discipline is not
claiming more than is known. The text lives in `params.portraitCaption`.

**Outstanding:** the provenance of this particular reproduction and its
licence are unconfirmed. The painting is ancient and long out of copyright,
but a specific photograph of it may not be. Worth settling before the site is
published.

It is also the only colour on the site, and deliberately so: a painted panel
reads as a plate, the way a frontispiece does in a book, not as an accent in
the interface. The no-accent-colour rule still governs everything that is
chrome.

## 2026-10-03 — One column width per page, not two

Adding the frontispiece exposed an older shortcut. Listing pages gave their
`<h1>` the class `.entry`, which carries not only the heading size but
`.entry`'s own `max-width: var(--max-measure)` and auto margins. That was
invisible while every column was exactly the measure.

The home page now needs to be wider than the measure — it carries the
frontispiece and the overview map — and the borrowed class pinned the heading
to a narrower centred box, so the page had two different left edges. Fixed by
giving listings a `.page-title` class that is the size and weight alone, and
by widening the whole home column (`.listing-wide`) rather than letting
individual blocks break out of a narrow one. Prose inside it is still capped
at the measure by `.lead` and `.region-blurb`: **the column got wider, the
reading line did not.**

`--breakout` moved to `:root` so the frontispiece and the maps share one
definition. Section pages keep the measure, so `.map-region` still breaks out
with symmetric negative margins.

## 2026-10-03 — Photographs from Wikimedia Commons, and the three guards

Every place now carries a gallery on its entry page, a thumbnail in every
listing, and a photograph in its map popup. The photographs come from
Wikimedia Commons via `tools/fetch_photos.py`, and are **committed** rather
than fetched at build time: the site then builds in CI with no network, and
nothing on the page depends on a third party staying up.

The script went through four rounds before it was trustworthy, and each
round was a real wrong answer, not a hypothetical:

1. **A plain name search returns the wrong country.** "Metropolitan Cathedral
   of the Annunciation" came back with Annunciation cathedrals in Atlanta,
   Boston and New England. Fixed with a locality check against the file's own
   coordinates (2.5 km, or 6 km for a site that is an area).
2. **The first locality check passed everything**, because the haystack it
   searched for a region name included the *entry's* `place` field — which
   naturally names its own city. Atlanta sailed through again. The haystack
   has to be the file's own words only.
3. **Good files are often unlocated and unnamed.** "File:Cave of the
   Apocalypse.jpg" has no coordinates and does not say Patmos, so the
   locality check rejected it and that entry got nothing. Added a category
   stage: a Commons category can be *shown* to be the right place — by its
   name, or by where its other members are — and its files inherit that.
   Category matching turned out to be by far the most precise source
   ("Category:Church of Agioi Theodoroi (Omorfi Ekklisia), Aegina").
4. **Category membership is not enough on its own.** Commons files a scale
   replica of Hagia Sophia in a Chinese theme park under
   `Category:Hagia Sophia`. A category file still has to pass the distance
   check when it carries coordinates; it only inherits the category's
   locality when it has none.

And one more after the first real run: a Flickr photograph about **sky
colour**, taken 2 km from a monastery, was accepted because it cleared the
distance check and nothing required it to match the name. A candidate that
matches no word of the place's name and is not in its category is now
dropped outright.

Other decisions:

- **Variety over score.** Six slots filled by the six highest-scoring files
  gave six frames of the same object, because Flickr batches upload as
  "Foo (8695837448).jpg", "Foo (8695838298).jpg"... Candidates are grouped by
  a series key with the digits stripped, and at most two per series are taken
  before moving on.
- **Attribution is carried, not assumed.** CC BY and CC BY-SA require author
  and licence wherever the image appears, so the fetcher refuses to record a
  file without them and the gallery renders them in the lightbox and in a
  credits list.
- **Archival scans are demoted, not excluded** — a 1900 photochrom is a real
  photograph of the place, but it is not what "show me what this is" means.
  Same for manuscripts, plans and models, which are penalised by title.
- **Rate limiting.** Commons returns 429 readily. One request at a time,
  spaced, with a long backoff; the whole corpus is fetched once and there is
  a block to lose by going faster.

### The fetcher audits the entries

`--report` flags two things. Photographs matched by proximity alone, which
may be of the building next door. And entries whose matched photographs
cluster *away* from the pin — where the likelier explanation is that the
**pin** is wrong. That is how the Cave of the Apocalypse turned out to be
pinned 1.5 km from the cave.

### Repository size

Commons serves thumbnails in the original format, so a PNG original arrives
as a 1.3 MB PNG. `--optimise` re-encodes everything to 1200 px progressive
JPEG, which is ample: these are sources that Hugo resizes again at build
time, and the published derivatives are much smaller.

## 2026-10-03 — Pin labels, and why they are conditional

Pins now carry the place's name beneath them, so a point is identifiable
without clicking it. Two things make that work rather than turn the map into
noise:

**They are permanent only above zoom 11.** The overview map opens on the
whole Aegean, where forty-odd permanent labels overlap into an unreadable
mat; below the threshold they revert to hover tooltips. Region maps open
above it, so they are labelled by default, which is where the labels earn
their keep. Leaflet fixes `permanent` at bind time, so crossing the threshold
unbinds and rebinds every tooltip -- done on `zoomend`, and only when the
threshold is actually crossed, not on every wheel notch.

**The label is the short form of the title.** Parentheses carry the
alternative name and are what make these titles long, so they are stripped,
and anything still over 34 characters is truncated: "The Little Metropolis
(Panagia Gorgoepikoos)" becomes "The Little Metropolis".

Styling is a halo rather than a box -- forty bordered boxes would read as
clutter. The halo is painted in `var(--bg)` and the text in `var(--text)`,
so it works in both themes without a second rule. `pointer-events: none`
keeps a label from swallowing a click meant for the pin under it.

## 2026-10-03 — Wheel zoom, and giving the page back

The wheel now zooms every map (`scrollWheelZoom` was off). Two things had to
come with it, or it would have made the pages worse rather than better.

**A map must be able to hand the wheel back.** A map that captures the wheel
unconditionally is a dead spot in the middle of a long page: the reader
scrolls, the map zooms, and the page never moves. `releaseAtBounds` watches
for the map being stuck at its zoom limit in the direction being scrolled,
disables wheel zoom, and re-arms it half a second after the wheel goes quiet
-- so the page scrolls past, and the map still works when the reader comes
back to it.

**That needs a floor to be stuck against.** Leaflet's default `minZoom` is 0,
so "stuck zoomed out" meant the whole world, and a reader scrolling down the
page would have zoomed a map through eleven levels before it released.
`MIN_ZOOM_SINGLE = 11` and `MIN_ZOOM_OVERVIEW = 5` put the release somewhere
sensible, and there was never a reason to let the map of one church show the
Atlantic.

`wheelPxPerZoomLevel` is also raised from Leaflet's default of 60 to 160: at
60 one trackpad flick crosses three or four zoom levels.

## 2026-10-04 — Hover opens a pin's popup

Pins open their popup on hover now, not only on click, so the map can be
read by moving across it.

**The delay is the whole mechanism.** Closing on `mouseout` alone makes the
popup unusable: it vanishes the instant the pointer leaves the pin, so the
"Read the entry" link inside it can never be reached, and the popup becomes a
thing you can see but not use. Instead a close is *scheduled* (280 ms) and
cancelled if the pointer arrives in the popup, which is what makes the gap
between pin and popup crossable. The popup element gets its own
`mouseenter`/`mouseleave` pair on `popupopen` to do the cancelling.

Click still works and now means something distinct: it **pins** the popup
open, so one reached deliberately does not evaporate while it is being read.
`popupclose` clears that state.

The hover tooltip and the popup cannot both appear, because the `:has()` rule
added earlier already hides the tooltip pane whenever a popup is open.

## 2026-10-04 — Popups never move the map

Leaflet's `autoPan` is on by default: opening a popup pans the view so the
popup fits. That was tolerable while popups opened on click, and became bad
the moment they opened on hover -- merely passing the pointer across a pin
near an edge dragged the map out from under the reader.

`autoPan: false` and `keepInView: false`. A popup that does not fit is
clipped by the Leaflet container's own `overflow: hidden`, which is the
lesser surprise: the map stays exactly where it was put, and the reader can
pan or zoom to see the rest.

The cost, accepted deliberately: for a pin close to the top edge the popup's
photograph and title are cropped away and only the tail of it shows. Leaflet
does not flip a popup to the other side of its marker when there is no room;
doing that would keep both the still map and the whole popup, and is the
obvious next move if the cropping proves annoying in use.

## 2026-10-04 — The popup photograph moved beside the text

It was a banner across the top of the popup; it is now a column down the
left, with the name and summary beside it, so the picture and the name are
read together rather than one after the other.

Three things that layout needed:

- **Image and body as siblings, not a stack.** The body is wrapped in its own
  element so it can be padded while the image runs flush to the popup's
  border; `.leaflet-popup-content` therefore carries no padding of its own.
- **`align-self: stretch` with `object-fit: cover`**, so the image takes
  whatever height the text next to it ends up being and crops to fill rather
  than distorting. The popup's height is set by the text, which varies.
- **A portrait crop.** The thumbnail in `sites.json` was 320x200, a banner
  shape, and is now 260x330. It is generated only for popups, so changing it
  affects nothing else -- the listing thumbnails have their own square crop.

`min-width: 0` on the body is what lets a long place name wrap instead of
widening the flex row past the popup's maximum.
