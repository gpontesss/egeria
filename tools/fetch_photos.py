#!/usr/bin/env python3
"""Fetch freely-licensed photographs of each place from Wikimedia Commons.

Every image on Commons carries a licence and an author, and most of the
licences in use (CC BY, CC BY-SA) REQUIRE both to be shown wherever the image
is. So this script never downloads a file without also recording who made it,
under what licence, and where it came from -- that metadata is written to
data/photos/<slug>.yaml beside the files and is what the gallery renders.

Candidates come from two independent searches, and which one found an image is
recorded as `found` so a human can audit the weak ones:

  name   -- full-text search on the place's name. Strong signal.
  geo    -- Commons geosearch around the entry's own coordinates. Weaker: it
            returns whatever is NEAR the point, which on a crowded site like
            Sultanahmet or the Athens Agora is often a different building.

Nothing here is authoritative. Run `--report` to see what was matched weakly.

Usage:
  python3 tools/fetch_photos.py --only aegina/agios-nektarios   # one entry
  python3 tools/fetch_photos.py --all                           # everything
  python3 tools/fetch_photos.py --all --dry-run                 # pick, don't download
  python3 tools/fetch_photos.py --report                        # audit what exists
"""

import argparse, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
PHOTOS = ROOT / "assets" / "photos"
DATA = ROOT / "data" / "photos"

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia throttles clients whose User-Agent does not identify them.
UA = ("Egeria-gazetteer/0.1 photo-fetch "
      "(static site build script; one-off corpus fetch; contact via repository)")

MAX_PER_SITE = 6
DOWNLOAD_WIDTH = 1200
# Below this, a candidate is more likely to be the wrong building than the
# right one -- an entry with no photographs is better than an entry with
# somebody else's. Proximity alone scores under it by construction.
MIN_SCORE = 4
# Commons answers 429 readily. One request at a time, spaced, with a long
# backoff: the whole corpus is ~50 entries and is fetched once, so there is
# nothing to gain by going faster and a block to lose.
REQUEST_SPACING = 1.0

# Commons is full of things that are not photographs of the place.
TITLE_PENALTY = re.compile(
    r"\b(map|plan|plans|diagram|section|elevation|drawing|engraving|lithograph|"
    r"gravure|stamp|coin|banknote|logo|coat of arms|flag|chart|graph|"
    r"inscription rubbing|facsimile|screenshot|poster|"
    r"fol\.?\s*\d|folio|manuscript|codex|miniature|replica|model of|"
    r"scale model|reconstruction drawing)\b", re.I)
TITLE_BONUS = re.compile(
    r"\b(exterior|interior|facade|fa[cç]ade|nave|dome|apse|mosaic|fresco|"
    r"iconostasis|katholikon|courtyard|narthex|view|panorama)\b", re.I)
# Archival scans are legitimate but are not what "a photo of this place today"
# means; demoted rather than excluded, so they can still fill a thin gallery.
TITLE_ARCHIVAL = re.compile(
    r"\b(dpla|postcard|stereo(graph|scopic)?|lantern slide|glass negative|"
    r"18\d\d|19[0-5]\d|lithographie|photochrom)\b", re.I)
STOPWORDS = {
    "the", "of", "and", "in", "at", "on", "a", "saint", "st", "holy", "church",
    "monastery", "convent", "chapel", "museum", "great", "new", "old", "and",
    "its", "churches", "town", "mount", "panagia",
}
GOOD_MIME = {"image/jpeg", "image/png"}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


_last_call = [0.0]


def api(params):
    params = dict(params, format="json", action="query")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        gap = time.monotonic() - _last_call[0]
        if gap < REQUEST_SPACING:
            time.sleep(REQUEST_SPACING - gap)
        _last_call[0] = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            wait = 5 * (attempt + 1)
            log(f"    rate limited, waiting {wait}s")
            time.sleep(wait)
        except Exception as e:                       # noqa: BLE001
            if attempt == 4:
                raise
            log(f"    retry {attempt + 1} after {e}")
            time.sleep(2 * (attempt + 1))
    return {}


# ---------------------------------------------------------------- front matter

def front_matter(path):
    """Minimal YAML front-matter reader -- enough for the flat fields used here."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.index("\n---", 3)
    fm = {}
    for line in text[3:end].split("\n"):
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            fm[k] = json.loads(v) if inner else []
        elif v.startswith('"') and v.endswith('"'):
            fm[k] = json.loads(v)
        elif v in ("true", "false"):
            fm[k] = v == "true"
        else:
            fm[k] = v
    return fm


def entries(only=None):
    out = []
    for md in sorted(CONTENT.rglob("*.md")):
        if md.name == "_index.md":
            continue
        slug = str(md.relative_to(CONTENT)).removesuffix(".md")
        if only and slug not in only:
            continue
        fm = front_matter(md)
        if not fm.get("coords"):          # guidance pages have no place to photograph
            continue
        out.append((slug, fm))
    return out


# ------------------------------------------------------------------- searching

def tokens(fm):
    """Distinctive words from the title and native name, for scoring matches."""
    raw = f"{fm.get('title', '')} {fm.get('native', '')}"
    raw = re.sub(r"\(.*?\)", " ", raw)
    words = re.findall(r"[\w'’Ͱ-Ͽἀ-῿]+", raw.lower())
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]


def queries(fm):
    """Search strings, best first. `commons` in front matter overrides."""
    if fm.get("commons"):
        return [fm["commons"]]
    qs = []
    title = re.sub(r"\(.*?\)", "", fm.get("title", "")).strip()
    if title:
        qs.append(title)
    # Categories are named plainly: "Cave of the Apocalypse", not "The Holy
    # Cave of the Apocalypse", so a query of the distinctive words alone finds
    # them where the full title does not. It comes SECOND, ahead of the
    # native-script name: callers take queries()[:2] to keep the request count
    # down, and having this one third silently broke the category stage for
    # every entry whose title carries an article or an epithet.
    core = " ".join(tokens({"title": title})[:4])
    if core and core.lower() != title.lower():
        qs.append(core)
    native = fm.get("native", "")
    # The native field is "Greek name — English gloss"; the Greek half searches best.
    native = native.split("\u2014")[0].strip()
    if native and native != title:
        qs.append(native)
    return qs


def search_by_name(fm, limit=25):
    found = {}
    for q in queries(fm)[:2]:
        d = api({"list": "search", "srsearch": q, "srnamespace": 6, "srlimit": limit})
        for hit in d.get("query", {}).get("search", []):
            found.setdefault(hit["title"], "name")
    return found


def search_by_category(slug, fm, limit=30):
    """Files from a Commons category that is itself anchored to this place.

    This is the highest-precision source, and it exists because the other two
    are not enough on their own. Many good files carry no coordinates and do
    not name their region ("File:Cave of the Apocalypse.jpg"), so the locality
    check rejects them -- but the CATEGORY they sit in can be shown to be the
    right one, either because its name says so or because its other members
    are located at the right spot. Files then inherit that verdict."""
    cats = []
    for q in queries(fm)[:2]:
        d = api({"list": "search", "srsearch": q, "srnamespace": 14, "srlimit": 5})
        for h in d.get("query", {}).get("search", []):
            if h["title"] not in cats:
                cats.append(h["title"])
    if not cats:
        return {}, None

    words = REGION_WORDS.get(slug.split("/")[0], [])
    toks = tokens(fm)
    lat, lon = fm["coords"][0], fm["coords"][1]

    for cat in cats[:6]:
        low = cat.lower()
        if sum(1 for tk in toks if tk in low) < 1:
            continue
        named = any(w in low for w in words)

        d = api({
            "generator": "categorymembers", "gcmtitle": cat, "gcmtype": "file",
            "gcmlimit": limit, "prop": "coordinates", "colimit": "max",
        })
        pages = d.get("query", {}).get("pages", {})
        if not pages:
            continue

        if not named:
            # No region in the name: make its members prove where it is.
            near = far = 0
            for pg in pages.values():
                co = (pg.get("coordinates") or [{}])[0]
                if co.get("lat") is None:
                    continue
                if km_apart(lat, lon, co["lat"], co["lon"]) <= 6.0:
                    near += 1
                else:
                    far += 1
            if near == 0 or far > near:
                continue

        return {pg["title"]: "category" for pg in pages.values()}, cat
    return {}, None


def search_by_geo(fm, limit=25):
    lat, lon = fm["coords"][0], fm["coords"][1]
    # A tight radius for a single building, wider for a site that IS an area.
    kinds = fm.get("kinds") or []
    radius = 600 if {"ruin", "open site", "monument", "ancient site"} & set(kinds) else 250
    d = api({
        "generator": "geosearch", "ggscoord": f"{lat}|{lon}", "ggsradius": radius,
        "ggslimit": limit, "ggsnamespace": 6,
    })
    return {p["title"]: "geo" for p in d.get("query", {}).get("pages", {}).values()}


def imageinfo(titles):
    """Image metadata AND the file's own coordinates, in one request each.

    The coordinates are the whole reason this is not just a name search: a
    search for "Cathedral of the Annunciation" returns cathedrals of that
    dedication in Atlanta and Boston, and nothing in the file's title or
    licence distinguishes them from the one in Athens."""
    out = {}
    titles = list(titles)
    for i in range(0, len(titles), 25):              # API caps titles per request
        batch = titles[i:i + 25]
        d = api({
            "titles": "|".join(batch), "prop": "imageinfo|coordinates",
            "iiprop": "url|extmetadata|size|mime", "iiurlwidth": DOWNLOAD_WIDTH,
            "coprop": "type|name", "colimit": "max",
        })
        for p in d.get("query", {}).get("pages", {}).values():
            if "imageinfo" not in p:
                continue
            info = p["imageinfo"][0]
            co = (p.get("coordinates") or [{}])[0]
            info["_lat"] = co.get("lat")
            info["_lon"] = co.get("lon")
            out[p["title"]] = info
    return out


def km_apart(lat1, lon1, lat2, lon2):
    import math
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Where each region is, in words, for files that carry no coordinates.
REGION_WORDS = {
    "athens": ["athens", "attica", "\u03b1\u03b8\u03ae\u03bd", "\u03b1\u03b8\u03b7\u03bd", "attika", "piraeus", "hymettus", "penteli", "pendeli"],
    "aegina": ["aegina", "egina", "aigina", "\u03b1\u03af\u03b3\u03b9\u03bd", "\u03b1\u03b9\u03b3\u03b9\u03bd"],
    "patmos": ["patmos", "\u03c0\u03ac\u03c4\u03bc", "\u03c0\u03b1\u03c4\u03bc", "chora", "skala"],
    "constantinople": ["istanbul", "constantinople", "\u0130stanbul", "konstantin", "fener", "balat",
                       "sultanahmet", "zeyrek", "edirnekap", "ayvansaray", "\u03ba\u03c9\u03bd\u03c3\u03c4\u03b1\u03bd\u03c4\u03b9\u03bd"],
}


def locality_ok(slug, fm, title, info, em):
    """Is this file plausibly OF this place, rather than merely named like it?

    Coordinates decide when the file has them. When it does not, the file has
    to name the region somewhere in its title or description, or it is
    rejected -- an unlocated "Annunciation Cathedral" is not evidence."""
    lat, lon = fm["coords"][0], fm["coords"][1]
    kinds = set(fm.get("kinds") or [])
    limit = 6.0 if {"ruin", "open site", "monument", "ancient site"} & kinds else 2.5

    if info.get("_lat") is not None:
        d = km_apart(lat, lon, info["_lat"], info["_lon"])
        return (d <= limit, f"{d:.1f} km")

    region = slug.split("/")[0]
    # The haystack is the FILE's own words only. Including the entry's `place`
    # here made every unlocated candidate pass, because the entry naturally
    # names its own city -- which is how Atlanta and Boston got through.
    hay = (title + " " + plain(em.get("ImageDescription", {}).get("value", ""))).lower()
    for w in REGION_WORDS.get(region, []):
        if w in hay:
            return (True, "no coords; region named")
    return (False, "no coords; region not named")


def plain(html):
    if not html:
        return ""
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = (txt.replace("&amp;", "&").replace("&quot;", '"')
              .replace("&#039;", "'").replace("&lt;", "<").replace("&gt;", ">")
              .replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", txt).strip()


def score(title, info, how, toks):
    name = title[5:]                                  # strip "File:"
    s = 0
    low = name.lower()
    hits = sum(1 for t in toks if t in low)
    s += 4 * hits
    s += {"category": 5, "name": 3}.get(how, 0)
    if TITLE_BONUS.search(name):
        s += 2
    if TITLE_PENALTY.search(name):
        s -= 10
    if TITLE_ARCHIVAL.search(name):
        s -= 5
    w, h = info.get("width", 0), info.get("height", 0)
    if w >= 1600:
        s += 2
    elif w >= 1000:
        s += 1
    elif w < 640:
        s -= 4
    if h and w and (w / h > 3 or h / w > 3):          # banners and scroll crops
        s -= 3
    return s, hits


def series_key(title):
    """A key shared by consecutive frames of one upload batch.

    Flickr and camera dumps arrive as "Foo (8695837448).jpg",
    "Foo (8695838298).jpg", ... -- all of the same object from one visit.
    Stripping the digits collapses them so the gallery can cap how many of
    any one series it takes."""
    base = title[5:].rsplit(".", 1)[0].lower()
    base = re.sub(r"[\d_()\[\]-]+", " ", base)
    return " ".join(base.split()[:5])


def diversify(scored, per_series=2):
    """Keep the best few of each series, so six slots are six subjects."""
    seen, out, overflow = {}, [], []
    for r in scored:
        k = series_key(r[2])
        seen[k] = seen.get(k, 0) + 1
        (out if seen[k] <= per_series else overflow).append(r)
    return out + overflow          # overflow still available if nothing else is


def pick(slug, fm, dry=False):
    toks = tokens(fm)
    cat_files, cat = search_by_category(slug, fm)
    if cat:
        log(f"    category: {cat}")
    cands = dict(cat_files)
    for _t, _h in search_by_name(fm).items():
        cands.setdefault(_t, _h)
    # Geosearch is the weakest signal and costs a round trip on every entry,
    # so it only runs when the category and name searches came up short.
    if len(cands) < 12:
        for t, how in search_by_geo(fm).items():
            cands.setdefault(t, how)
    if not cands:
        return []

    infos = imageinfo(cands)
    scored = []
    rejected = 0
    for title, how in cands.items():
        info = infos.get(title)
        if not info or info.get("mime") not in GOOD_MIME:
            continue
        em = info.get("extmetadata", {})
        if how == "category" and info.get("_lat") is None:
            ok, why = True, "in the place's Commons category"   # settled above
        else:
            ok, why = locality_ok(slug, fm, title, info, em)
        if not ok:
            rejected += 1
            continue
        lic = plain(em.get("LicenseShortName", {}).get("value"))
        # Commons should be free throughout, but never assume it.
        if not lic or "fair use" in lic.lower() or "non-free" in lic.lower():
            continue
        sc, hits = score(title, info, how, toks)
        # A candidate that matches nothing in the name and is not in the
        # place's own category is not evidence of anything: a free-text
        # search for a monastery returned a Flickr photograph about sky
        # colour, taken 2 km away, which cleared the distance check on its
        # own. Membership of the category is the only thing that substitutes
        # for the name.
        if hits == 0 and how != "category":
            continue
        scored.append((sc, hits, title, info, how, lic, em, why))

    scored.sort(key=lambda r: (-r[0], r[2]))
    scored = [r for r in scored if r[0] >= MIN_SCORE]
    scored = diversify(scored)
    if rejected:
        log(f"    ({rejected} candidates rejected as the wrong location)")
    out = []
    for sc, hits, title, info, how, lic, em, why in scored[:MAX_PER_SITE]:
        out.append({
            "title": title,
            "score": sc,
            "found": (how if hits else f"{how} (no name match)") + f"; {why}",
            "url": info.get("thumburl") or info.get("url"),
            "descriptionurl": info.get("descriptionurl"),
            "width": info.get("thumbwidth") or info.get("width"),
            "height": info.get("thumbheight") or info.get("height"),
            "licence": lic,
            "licenceUrl": plain(em.get("LicenseUrl", {}).get("value")),
            "author": plain(em.get("Artist", {}).get("value")) or "Unknown",
            "caption": plain(em.get("ImageDescription", {}).get("value"))[:300],
        })
    return out


# ----------------------------------------------------------------- downloading

GREEK = str.maketrans({
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i", "θ": "th",
    "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p",
    "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "f", "χ": "ch", "ψ": "ps",
    "ω": "o", "ά": "a", "έ": "e", "ή": "i", "ί": "i", "ό": "o", "ύ": "y", "ώ": "o",
    "ϊ": "i", "ϋ": "y", "ΐ": "i", "ΰ": "y",
})


def safe_name(title, n):
    """A readable ASCII filename. Greek titles are transliterated rather than
    stripped, or every Greek-named file would collapse to the same name."""
    base = title[5:].rsplit(".", 1)[0].lower().translate(GREEK)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:60]
    if not base:
        import hashlib
        base = hashlib.sha1(title.encode("utf-8")).hexdigest()[:10]
    return f"{n:02d}-{base}.jpg"


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data)


def yaml_quote(s):
    return json.dumps(s if s is not None else "", ensure_ascii=False)


def write_manifest(slug, records):
    path = DATA / (slug + ".yaml")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Generated by tools/fetch_photos.py from Wikimedia Commons.",
        "# Attribution and licence are REQUIRED on display -- the gallery",
        "# partial renders them. Do not strip these fields.",
        "#",
        "# `found: geo (no name match)` means the image was picked only because",
        "# it is near the coordinates, not because anything identified it as",
        "# this place. Check those before trusting them.",
        "photos:",
    ]
    for r in records:
        lines += [
            f"  - file: {yaml_quote(r['file'])}",
            f"    commons: {yaml_quote(r['title'])}",
            f"    source: {yaml_quote(r['descriptionurl'])}",
            f"    author: {yaml_quote(r['author'])}",
            f"    licence: {yaml_quote(r['licence'])}",
            f"    licenceUrl: {yaml_quote(r['licenceUrl'])}",
            f"    caption: {yaml_quote(r['caption'])}",
            f"    found: {yaml_quote(r['found'])}",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def optimise(max_width=1200, quality=82):
    """Re-encode everything under assets/photos to a sane size and format.

    Commons serves its thumbnails in the original format, so a PNG original
    comes back as a 1.3 MB PNG. These files are repository sources that Hugo
    resizes again at build time, so there is nothing to gain from keeping them
    large -- and a gazetteer of fifty places at six photographs each turns
    that waste into tens of megabytes of git history."""
    from PIL import Image
    before = after = 0
    for f in sorted(PHOTOS.rglob("*.jpg")):
        start = f.stat().st_size
        before += start
        try:
            with Image.open(f) as im:
                im = im.convert("RGB")
                if im.width > max_width:
                    h = round(im.height * max_width / im.width)
                    im = im.resize((max_width, h), Image.LANCZOS)
                im.save(f, "JPEG", quality=quality, optimize=True, progressive=True)
        except Exception as e:                          # noqa: BLE001
            log(f"  ! {f.relative_to(ROOT)}: {e}")
            continue
        end = f.stat().st_size
        after += end
        if start - end > 50_000:
            log(f"  {f.relative_to(PHOTOS)}: {start // 1024} -> {end // 1024} KB")
    log(f"\n{before // 1_048_576} MB -> {after // 1_048_576} MB")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--optimise", action="store_true",
                    help="re-encode downloaded files to 1200px JPEG")
    ap.add_argument("--force", action="store_true", help="refetch entries that already have photos")
    args = ap.parse_args()

    if args.report:
        return report()
    if args.optimise:
        return optimise()
    if not args.all and not args.only:
        ap.error("pass --all or --only <slug>")

    todo = entries(set(args.only) if args.only else None)
    log(f"{len(todo)} entries with coordinates")

    for slug, fm in todo:
        manifest = DATA / (slug + ".yaml")
        if manifest.exists() and not args.force:
            log(f"  = {slug} (already has photos; --force to redo)")
            continue
        log(f"  · {slug}")
        try:
            picks = pick(slug, fm)
        except Exception as e:                         # noqa: BLE001
            log(f"    FAILED: {e}")
            continue
        if not picks:
            log("    no candidates")
            continue

        records = []
        for n, p in enumerate(picks, 1):
            fname = safe_name(p["title"], n)
            dest = PHOTOS / slug / fname
            if not args.dry_run:
                try:
                    size = download(p["url"], dest)
                except Exception as e:                 # noqa: BLE001
                    log(f"    skip {p['title']}: {e}")
                    continue
                log(f"    + {fname} ({size // 1024} KB, {p['found']}, {p['licence']})")
            else:
                log(f"    ? {fname} ({p['found']}, score {p['score']}, {p['licence']})")
            records.append(dict(p, file=fname))

        if records and not args.dry_run:
            write_manifest(slug, records)
    return 0


def report():
    """What was found, and what should be looked at by a human.

    Two kinds of doubt are worth separating. A photograph matched only by
    proximity may be of the building next door. And a photograph matched
    confidently but sitting far from the entry's own coordinates is evidence
    that THE ENTRY is wrong, not the photograph -- which is how the Patmos
    cave turned out to be pinned 1.5 km from the cave."""
    import re as _re
    total = weak = 0
    missing = []
    far = []
    for slug, fm in entries():
        path = DATA / (slug + ".yaml")
        if not path.exists():
            missing.append(slug)
            continue
        text = path.read_text(encoding="utf-8")
        n = text.count("  - file:")
        w = text.count("no name match")
        total += n
        weak += w
        dists = [float(d) for d in _re.findall(r"; ([\d.]+) km\"", text)]
        flag = f"   <-- {w} matched by proximity only" if w else ""
        if dists:
            med = sorted(dists)[len(dists) // 2]
            if med > 0.4:
                far.append((med, slug, len(dists)))
                flag += f"   <-- photos sit {med:.1f} km from this entry's coords"
        print(f"{n:2d} photos  {slug}{flag}")
    print(f"\n{total} photos across {len(entries()) - len(missing)} entries; "
          f"{weak} matched by proximity only")
    if far:
        print("\ncoordinates to re-check (photos cluster away from the pin):")
        for med, slug, n in sorted(far, reverse=True):
            print(f"  {med:5.1f} km  {slug}  ({n} located photos)")
    if missing:
        print(f"\nno photos yet ({len(missing)}):")
        for m in missing:
            print("  ", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
