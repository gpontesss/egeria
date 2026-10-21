"""The papyrus textures in assets/css/style.css, as data URIs: the sheet
itself, and the torn strips along the header's foot and the left menu's inner
edge.

They are SVG encoded into the stylesheet rather than files under assets/, so a
theme is still one request and Hugo has nothing extra to fingerprint. Nothing
reads this at build time -- it exists so the encoding is never hand-typed and
the awkward constraints below are written down. Run it to print the
declarations, and paste them over the ones in style.css:

    python3 tools/textures.py
"""
from urllib.parse import quote


def uri(svg):
    return 'url("data:image/svg+xml,%s")' % quote(svg, safe="")


# Papyrus, as one tile: two long-wavelength turbulences (one streaked
# horizontally, one vertically) that read together as woven fibre, and a fine
# isotropic grain over them.
#
# TILE is 256 and every baseFrequency below is an exact multiple of 1/256.
# stitchTiles only produces a seamless tile when it does not have to round the
# frequency to fit -- at 300px with 0.014 the seam was a hard line every 300px
# in both themes. Do not change TILE and the frequencies independently.
TILE = 256
LAYERS = [
    ("0.015625 0.75", "11"),   # fibres running across
    ("0.75 0.015625", "19"),   # fibres running down
    ("0.9375", "7"),           # grain
]
IDS = "abc"


def _filters(region):
    """The turbulence definitions, shared by the sheet and the torn strips so
    a strip is made of exactly the same fibre as the page it lies on."""
    return "".join(
        "<filter id='" + IDS[i] + "' x='0' y='0' width='" + region +
        "' height='" + region + "'>"
        "<feTurbulence type='fractalNoise' baseFrequency='" + bf + "'"
        " numOctaves='2' seed='" + seed + "' stitchTiles='stitch'/>"
        "<feColorMatrix type='saturate' values='0'/>"
        "</filter>" for i, (bf, seed) in enumerate(LAYERS))


def _noise(w, h, opacities):
    return "".join(
        "<rect width='%d' height='%d' filter='url(#%s)' opacity='%s'/>"
        % (w, h, IDS[i], op) for i, op in enumerate(opacities))


def paper(*opacities):
    """One data URI for the whole sheet. Opacities are per layer, in the
    order of LAYERS; the dark theme passes weaker ones."""
    assert len(opacities) == len(LAYERS)
    return uri(
        "<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d'>"
        "%s%s</svg>"
        % (TILE, TILE, _filters("100%"), _noise(TILE, TILE, opacities)))


# The torn contour, tiling along its long axis. The spacing between points is
# as irregular as the depth of them: with an even step this came out as a
# pinking-shears zigzag rather than a tear. The first and last point must
# share a depth or the tear shows a seam at every tile boundary.
PTS = [
    (7.0, 0), (5.8, 7), (6.4, 15), (3.9, 22), (4.6, 31), (8.1, 38),
    (7.2, 44), (7.6, 56), (5.0, 63), (3.2, 69), (4.1, 78), (6.9, 85),
    (8.4, 93), (6.2, 99), (6.6, 112), (4.4, 118), (2.9, 125), (5.1, 133),
    (7.8, 140), (6.4, 147), (7.1, 158), (4.8, 164), (3.6, 172), (5.4, 179),
    (8.0, 186), (6.3, 193), (7.0, 200),
]
W = 9
H = PTS[-1][1]


def torn(bg, edge, opacities, across=False):
    """A torn edge as a tiling strip.

    `bg` and `edge` are plain #rrggbb -- quote() encodes the hash once.
    Passing an already-encoded %23 double-encodes it and the fill silently
    falls back to black.

    THE STRIP IS MADE OF THE SAME PAPER AS THE PAGE: the same --bg underneath
    and the same turbulence over it, at the same per-theme strength. An
    earlier version filled it with a flat colour a shade deeper than the page,
    and it read as a band of different stock laid over woven paper rather than
    as a tear in one sheet. For the same reason the contour is drawn faintly:
    what should be visible is the shadow of a tear, not a line ruled down the
    page.

    across=False gives a vertical strip whose RIGHT edge is torn (the left
    menu); across=True transposes the same points into a horizontal strip
    whose BOTTOM edge is torn (the header).
    """
    pts = [(y, x) for x, y in PTS] if across else list(PTS)
    w, h = (H, W) if across else (W, H)

    def line(d):
        if across:
            return " ".join("L%d,%g" % (a, b - d) for a, b in pts)
        return " ".join("L%g,%d" % (a - d, b) for a, b in pts)

    close = "L%d,0" % w if across else "L0,%d" % h
    stroke = ("<path d='M%s' fill='none' stroke='%s' stroke-width='%s'"
              " stroke-linejoin='round' opacity='%s'/>")
    return uri(
        "<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d'>"
        "%s"
        "<clipPath id='t'><path d='M0,0 %s %s Z'/></clipPath>"
        "<g clip-path='url(#t)'>"
        "<rect width='%d' height='%d' fill='%s'/>%s"
        "</g>"
        # Wide and nearly transparent: the shadow the sheet casts where it is
        # torn. Then the fibrous thickness of the tear, then the contour.
        "%s%s%s</svg>"
        % (w, h, _filters("1000%"), line(0), close, w, h, bg,
           _noise(w, h, opacities),
           stroke % (line(3.2)[1:], edge, "3.5", "0.13"),
           stroke % (line(1.6)[1:], edge, "0.7", "0.18"),
           stroke % (line(0)[1:], edge, "0.8", "0.4")))


# The palette each theme is baked for: the page colour the strips are filled
# with, the ink their contour is drawn in, and how strong the fibre is. Noise
# over near-black reads stronger than the same noise over papyrus, hence the
# lower dark figures.
THEMES = {
    "light": {"bg": "#f2e6d0", "edge": "#8a6e50",
              "paper": (".42", ".26", ".26")},
    "dark": {"bg": "#19140f", "edge": "#c7ae8a",
             "paper": (".20", ".13", ".12")},
}

if __name__ == "__main__":
    for name, t in THEMES.items():
        print("/* %s */" % name)
        print("  --paper: %s;" % paper(*t["paper"]))
        print("  --torn-edge: %s;" % torn(t["bg"], t["edge"], t["paper"]))
        print("  --torn-head: %s;"
              % torn(t["bg"], t["edge"], t["paper"], across=True))
        print()
