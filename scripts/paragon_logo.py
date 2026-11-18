#!/usr/bin/env python3
"""Paragon Photo app icon generator.

Draws the Paragon family app icon for Paragon Photo, in the style of the PR7 plugins' icon
(Paragon-PR7-S `source/ui/Logo.cpp`, `Logo::drawAppIcon`):

- a pearl onyx rounded tile (#1d171c at the top to #070508 at the foot) with the family's red
  glow edge (#ff4a3a) and a fainter inner glow ring;
- a "PP" monogram in heavy, wide, forward-slanted block letters with two "speed cuts" through
  their lower half: the first P in the family gradient (pink #de0639 at the top to orange
  #cd6619 at the foot), the second in pearl white (#f4eeea);
- the family's neon stripe (pink -> red -> orange at 75% strength) and the full
  "PARAGON PHOTO" mark under it, PARAGON in pearl white and PHOTO in the accent red (#e0103c),
  as the PR7 mark draws its 7. Small sizes (16 and 32 px) leave the name out, where it can't
  be read.

The letters are built from vector outlines on the same grid as the PR7 mark (1 unit tall,
stems 0.24 wide, bars 0.2 tall, bevelled corners), not from a font, so they are the same shape
everywhere. Run from the repository root:

    python3 scripts/paragon_logo.py

It rewrites the icon files the build already references (file names kept so no Rust or
packaging code changes): assets/app-icon/photocraft{.svg,-small.svg,-1024.png,.ico,.icns} and
the Linux hicolor theme icons. Needs Pillow only.
"""

from __future__ import annotations

import argparse
import pathlib

from PIL import Image, ImageChops, ImageDraw

# ---- Palette (Paragon family, from PR7-S Logo.cpp / Finish.cpp / Project.h) -------------------

TILE_TOP = (0x1D, 0x17, 0x1C)
TILE_BOTTOM = (0x07, 0x05, 0x08)
GLOW = (0xFF, 0x4A, 0x3A)
PINK = (0xDE, 0x06, 0x39)
RED = (0xD4, 0x2E, 0x2A)
ORANGE = (0xCD, 0x66, 0x19)
PEARL = (0xF4, 0xEE, 0xEA)
ACCENT = (0xE0, 0x10, 0x3C)

# Finish::neonGradient: the swatch's colours at 75%, with stops at 0, .25, .5, .75, 1.
NEON_STOPS = [
    (0.0, PINK),
    (0.25, (0xD9, 0x07, 0x38)),
    (0.5, RED),
    (0.75, (0xCF, 0x5C, 0x1C)),
    (1.0, ORANGE),
]
NEON_STOPS = [(t, tuple(round(c * 0.75) for c in rgb)) for t, rgb in NEON_STOPS]

# ---- Letter geometry ------------------------------------------------------------------------

SLANT = 0.3  # how far the top leans right, per unit of height
SPACING = 0.1
WORD_SPACE = 0.45
CUTS = [(0.63, 0.68), (0.79, 0.83)]  # speed cuts, as fractions of the height from the top

# Each letter: (width, [polygons]). Polygons after the first that lie inside it are counters
# (holes, even-odd fill). Coordinates are upright, y down, 1 unit tall.
LETTERS: dict[str, tuple[float, list[list[tuple[float, float]]]]] = {
    "P": (0.8, [
        [(0, 0), (0.64, 0), (0.8, 0.15), (0.8, 0.45), (0.64, 0.6), (0.24, 0.6), (0.24, 1), (0, 1)],
        [(0.24, 0.2), (0.56, 0.2), (0.56, 0.4), (0.24, 0.4)],
    ]),
    "R": (0.84, [
        [(0, 0), (0.64, 0), (0.8, 0.15), (0.8, 0.45), (0.64, 0.6), (0.24, 0.6), (0.24, 1), (0, 1)],
        [(0.24, 0.2), (0.56, 0.2), (0.56, 0.4), (0.24, 0.4)],
        [(0.4, 0.6), (0.64, 0.6), (0.84, 1), (0.6, 1)],  # the leg (a separate solid piece)
    ]),
    "A": (0.8, [
        [(0, 1), (0, 0.15), (0.16, 0), (0.64, 0), (0.8, 0.15), (0.8, 1), (0.56, 1), (0.56, 0.62),
         (0.24, 0.62), (0.24, 1)],
        [(0.24, 0.2), (0.56, 0.2), (0.56, 0.42), (0.24, 0.42)],
    ]),
    "G": (0.8, [
        [(0.16, 0), (0.8, 0), (0.8, 0.2), (0.24, 0.2), (0.24, 0.8), (0.56, 0.8), (0.56, 0.62),
         (0.4, 0.62), (0.4, 0.42), (0.8, 0.42), (0.8, 0.85), (0.64, 1), (0.16, 1), (0, 0.85), (0, 0.15)],
    ]),
    "O": (0.8, [
        [(0.16, 0), (0.64, 0), (0.8, 0.15), (0.8, 0.85), (0.64, 1), (0.16, 1), (0, 0.85), (0, 0.15)],
        [(0.24, 0.2), (0.56, 0.2), (0.56, 0.8), (0.24, 0.8)],
    ]),
    "N": (0.8, [
        [(0, 0), (0.24, 0), (0.56, 0.55), (0.56, 0), (0.8, 0), (0.8, 1), (0.56, 1), (0.24, 0.45),
         (0.24, 1), (0, 1)],
    ]),
    "H": (0.8, [
        [(0, 0), (0.24, 0), (0.24, 0.4), (0.56, 0.4), (0.56, 0), (0.8, 0), (0.8, 1), (0.56, 1),
         (0.56, 0.6), (0.24, 0.6), (0.24, 1), (0, 1)],
    ]),
    "T": (0.8, [
        [(0, 0), (0.8, 0), (0.8, 0.2), (0.52, 0.2), (0.52, 1), (0.28, 1), (0.28, 0.2), (0, 0.2)],
    ]),
}
# Which polygons of a letter are holes (index > 0 and not listed here are holes).
SOLID_EXTRA = {"R": {2}}


def lean(points, dx=0.0):
    """Shift by dx, then slant: the top moves right, the baseline stays put (x += SLANT*(1-y))."""
    return [(x + dx + SLANT * (1.0 - y), y) for x, y in points]


def layout(text: str):
    """Pieces of `text` laid out on one line: list of (char, solids, holes), and total width."""
    pieces, x = [], 0.0
    for i, ch in enumerate(text):
        if ch == " ":
            x += WORD_SPACE
            continue
        width, polys = LETTERS[ch]
        solids = [lean(polys[0], x)]
        holes = []
        for j, poly in enumerate(polys[1:], start=1):
            (solids if j in SOLID_EXTRA.get(ch, set()) else holes).append(lean(poly, x))
        pieces.append((ch, solids, holes))
        x += width + (SPACING if i + 1 < len(text) else 0.0)
    return pieces, x + SLANT


# ---- Raster rendering (Pillow, supersampled) --------------------------------------------------

SS = 4  # supersampling factor


def vertical_gradient(size, top, bottom, box=None):
    """An RGB image of `size`, `top` colour at box[1] to `bottom` at box[3]."""
    w, h = size
    y0, y1 = (0, h) if box is None else (box[1], box[3])
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = min(1.0, max(0.0, (y - y0) / max(1.0, (y1 - y0))))
        col.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return col.resize((w, h))


def horizontal_stops(size, stops, x0, x1):
    w, h = size
    row = Image.new("RGB", (w, 1))
    for x in range(w):
        t = min(1.0, max(0.0, (x - x0) / max(1.0, (x1 - x0))))
        for (ta, ca), (tb, cb) in zip(stops, stops[1:]):
            if ta <= t <= tb:
                u = (t - ta) / (tb - ta) if tb > ta else 0.0
                row.putpixel((x, 0), tuple(round(a + (b - a) * u) for a, b in zip(ca, cb)))
                break
    return row.resize((w, h))


def rounded_mask(size, box, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=radius, fill=255)
    return m


def ring_mask(size, box, radius, width):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=radius, outline=255, width=max(1, round(width)))
    return m


def letters_mask(size, pieces, place, which=None):
    """Mask of the letters (even-odd counters), placed by `place(x, y) -> (px, py)`."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for idx, (_, solids, holes) in enumerate(pieces):
        if which is not None and idx not in which:
            continue
        for poly in solids:
            d.polygon([place(x, y) for x, y in poly], fill=255)
        for poly in holes:
            d.polygon([place(x, y) for x, y in poly], fill=0)
    return m


def cut_bands(mask, top, height, full_width):
    """Clear the speed cuts from a letters mask whose letters span [top, top+height]."""
    d = ImageDraw.Draw(mask)
    for a, b in CUTS:
        d.rectangle([0, top + height * a, full_width, top + height * b], fill=0)
    return mask


def fill(base, colour_or_image, mask):
    layer = colour_or_image if isinstance(colour_or_image, Image.Image) else Image.new("RGB", base.size, colour_or_image)
    base.paste(layer, (0, 0), mask)


def render_icon(px: int, with_name: bool, margin: float = 0.0) -> Image.Image:
    """The app icon as an RGBA image px x px (Logo::drawAppIcon). `margin` insets the tile by that fraction of
    the size: PR7-S's own icon uses 0.02; Windows and Linux icons are full bleed (0), only their round corners
    transparent, or the shells crop them (PhotoCraft #4478, guarded by `app_icon.rs`'s tests)."""
    S = px * SS
    size = (S, S)
    img = Image.new("RGBA", size, (0, 0, 0, 0))

    m = S * margin
    tile = (m, m, S - m, S - m)
    corner = S * 0.2
    tile_mask = rounded_mask(size, tile, corner)

    rgb = vertical_gradient(size, TILE_TOP, TILE_BOTTOM, tile).convert("RGBA")
    img.paste(rgb, (0, 0), tile_mask)

    if px >= 24:  # the soft inner glow ring
        r = S * 0.025
        glow = ring_mask(size, (tile[0] + r, tile[1] + r, tile[2] - r, tile[3] - r), corner * 0.9, S * 0.035)
        glow = glow.point(lambda v: round(v * 0.28))
        glow = ImageChops.multiply(glow, tile_mask)
        img.paste(Image.new("RGBA", size, GLOW + (255,)), (0, 0), glow)
    r = S * 0.008
    edge = ring_mask(size, (tile[0] + r, tile[1] + r, tile[2] - r, tile[3] - r), corner, max(SS, S * 0.012))
    img.paste(Image.new("RGBA", size, GLOW + (255,)), (0, 0), edge)

    # Inner area, name area at its foot.
    inset = (tile[2] - tile[0]) * 0.13
    inner = [tile[0] + inset, tile[1] + inset, tile[2] - inset, tile[3] - inset]
    name_area = None
    if with_name:
        name_h = (inner[3] - inner[1]) * 0.24
        name_area = [inner[0], inner[3] - name_h, inner[2], inner[3]]
        inner[3] -= name_h

    # Monogram "PP": the second P a touch apart, as the 7S monogram spaces its letters.
    p_w = LETTERS["P"][0]
    pieces = [("P", [lean(LETTERS["P"][1][0])], [lean(LETTERS["P"][1][1])]),
              ("P", [lean(LETTERS["P"][1][0], p_w + SPACING * 1.5)], [lean(LETTERS["P"][1][1], p_w + SPACING * 1.5)])]
    xs = [x for _, sol, _ in pieces for poly in sol for x, _ in poly]
    shape_w, shape_h = max(xs) - min(xs), 1.0
    iw, ih = inner[2] - inner[0], inner[3] - inner[1]
    fit = min(iw * 0.9 / shape_w, ih * (0.86 if with_name else 0.78) / shape_h)
    cx, cy = (inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2
    sx0 = (min(xs) + max(xs)) / 2

    def place(x, y):
        return (cx + (x - sx0) * fit, cy + (y - 0.5) * fit)

    top = cy - 0.5 * fit
    first = letters_mask(size, pieces, place, {0})
    second = letters_mask(size, pieces, place, {1})
    if px >= 48:
        cut_bands(first, top, fit, S)
        cut_bands(second, top, fit, S)
    grad = vertical_gradient(size, PINK, ORANGE, (0, top, 0, top + fit)).convert("RGBA")
    img.paste(grad, (0, 0), first)
    img.paste(Image.new("RGBA", size, PEARL + (255,)), (0, 0), second)

    if with_name and name_area:
        nh = name_area[3] - name_area[1]
        stripe_h = max(SS, S * 0.012)
        stripe_cy = name_area[1] + nh * 0.11
        sw = iw * 0.82
        sx = (inner[0] + inner[2]) / 2 - sw / 2
        stripe = Image.new("L", size, 0)
        ImageDraw.Draw(stripe).rectangle([sx, stripe_cy - stripe_h / 2, sx + sw, stripe_cy + stripe_h / 2], fill=255)
        neon = horizontal_stops(size, NEON_STOPS, sx, sx + sw).convert("RGBA")
        img.paste(neon, (0, 0), stripe)

        mark_area = [name_area[0], name_area[1] + nh * 0.22, name_area[2], name_area[3]]
        mh = (mark_area[3] - mark_area[1]) * 0.84
        word_pieces, total_w = layout("PARAGON PHOTO")
        h = min(mh, (mark_area[2] - mark_area[0]) / total_w)
        mx = (mark_area[0] + mark_area[2]) / 2 - total_w * h / 2
        my = (mark_area[1] + mark_area[3]) / 2 - h / 2

        def place_mark(x, y):
            return (mx + x * h, my + y * h)

        paragon = letters_mask(size, word_pieces, place_mark, set(range(7)))
        photo = letters_mask(size, word_pieces, place_mark, set(range(7, 12)))
        if px >= 256:  # the cuts only read on the large renders
            cut_bands(paragon, my, h, S)
            cut_bands(photo, my, h, S)
        img.paste(Image.new("RGBA", size, PEARL + (255,)), (0, 0), paragon)
        img.paste(Image.new("RGBA", size, ACCENT + (255,)), (0, 0), photo)

    return img.resize((px, px), Image.LANCZOS)


# ---- SVG (vector master) ----------------------------------------------------------------------

def svg_icon(with_name: bool = True, margin: float = 0.0) -> str:
    S = 1024.0
    m = S * margin
    t0, t1 = m, S - m
    corner = S * 0.2
    inset = (t1 - t0) * 0.13
    inner = [t0 + inset, t0 + inset, t1 - inset, t1 - inset]
    name_area = None
    if with_name:
        name_h = (inner[3] - inner[1]) * 0.24
        name_area = [inner[0], inner[3] - name_h, inner[2], inner[3]]
        inner[3] -= name_h

    def path(polys, place):
        return " ".join("M" + " L".join(f"{place(x, y)[0]:.2f},{place(x, y)[1]:.2f}" for x, y in poly) + " Z" for poly in polys)

    p_w = LETTERS["P"][0]
    pp = [(lean(LETTERS["P"][1][0]), lean(LETTERS["P"][1][1])),
          (lean(LETTERS["P"][1][0], p_w + SPACING * 1.5), lean(LETTERS["P"][1][1], p_w + SPACING * 1.5))]
    xs = [x for a, _ in pp for x, _ in a]
    iw, ih = inner[2] - inner[0], inner[3] - inner[1]
    fit = min(iw * 0.9 / (max(xs) - min(xs)), ih * (0.86 if with_name else 0.78))
    cx, cy = (inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2
    sx0 = (min(xs) + max(xs)) / 2

    def place(x, y):
        return (cx + (x - sx0) * fit, cy + (y - 0.5) * fit)

    top = cy - 0.5 * fit
    cuts = "".join(
        f'<rect x="0" y="{top + fit * a:.2f}" width="{S}" height="{fit * (b - a):.2f}" fill="black"/>' for a, b in CUTS)
    hexc = lambda c: "#%02x%02x%02x" % c  # noqa: E731
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S:.0f} {S:.0f}" width="{S:.0f}" height="{S:.0f}">',
        "<title>Paragon Photo</title>",
        "<defs>",
        f'<linearGradient id="tile" x1="0" y1="{t0}" x2="0" y2="{t1}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{hexc(TILE_TOP)}"/><stop offset="1" stop-color="{hexc(TILE_BOTTOM)}"/></linearGradient>',
        f'<linearGradient id="seven" x1="0" y1="{top:.2f}" x2="0" y2="{top + fit:.2f}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{hexc(PINK)}"/><stop offset="1" stop-color="{hexc(ORANGE)}"/></linearGradient>',
        f'<mask id="cuts"><rect width="{S}" height="{S}" fill="white"/>{cuts}</mask>',
    ]
    if with_name:
        sw = iw * 0.82
        sx = cx - sw / 2
        stops = "".join(f'<stop offset="{t}" stop-color="{hexc(c)}"/>' for t, c in NEON_STOPS)
        out.append(f'<linearGradient id="neon" x1="{sx:.2f}" y1="0" x2="{sx + sw:.2f}" y2="0" gradientUnits="userSpaceOnUse">{stops}</linearGradient>')
    out.append("</defs>")
    out.append(f'<rect x="{t0}" y="{t0}" width="{t1 - t0}" height="{t1 - t0}" rx="{corner}" fill="url(#tile)"/>')
    r = S * 0.025
    out.append(f'<rect x="{t0 + r}" y="{t0 + r}" width="{t1 - t0 - 2 * r}" height="{t1 - t0 - 2 * r}" rx="{corner * 0.9}" '
               f'fill="none" stroke="{hexc(GLOW)}" stroke-opacity="0.28" stroke-width="{S * 0.035}"/>')
    r = S * 0.008
    out.append(f'<rect x="{t0 + r}" y="{t0 + r}" width="{t1 - t0 - 2 * r}" height="{t1 - t0 - 2 * r}" rx="{corner}" '
               f'fill="none" stroke="{hexc(GLOW)}" stroke-width="{S * 0.012}"/>')
    out.append('<g mask="url(#cuts)" fill-rule="evenodd">')
    out.append(f'<path fill="url(#seven)" d="{path(pp[0], place)}"/>')
    out.append(f'<path fill="{hexc(PEARL)}" d="{path(pp[1], place)}"/>')
    out.append("</g>")
    if with_name and name_area:
        nh = name_area[3] - name_area[1]
        sh = S * 0.012
        scy = name_area[1] + nh * 0.11
        sw = iw * 0.82
        out.append(f'<rect x="{cx - sw / 2:.2f}" y="{scy - sh / 2:.2f}" width="{sw:.2f}" height="{sh:.2f}" fill="url(#neon)"/>')
        ma = [name_area[0], name_area[1] + nh * 0.22, name_area[2], name_area[3]]
        mh = (ma[3] - ma[1]) * 0.84
        pieces, total_w = layout("PARAGON PHOTO")
        h = min(mh, (ma[2] - ma[0]) / total_w)
        mx = cx - total_w * h / 2
        my = (ma[1] + ma[3]) / 2 - h / 2

        def pm(x, y):
            return (mx + x * h, my + y * h)

        word_cuts = "".join(
            f'<rect x="0" y="{my + h * a:.2f}" width="{S}" height="{h * (b - a):.2f}" fill="black"/>' for a, b in CUTS)
        out.insert(-1 - 0, "")  # keep list shape; masks are defined inline below
        out.append(f'<mask id="wordcuts"><rect width="{S}" height="{S}" fill="white"/>{word_cuts}</mask>')
        for idx, (_, solids, holes) in enumerate(pieces):
            colour = PEARL if idx < 7 else ACCENT
            out.append(f'<path mask="url(#wordcuts)" fill-rule="evenodd" fill="{hexc(colour)}" d="{path(solids + holes, pm)}"/>')
    out.append("</svg>")
    return "\n".join(line for line in out if line) + "\n"


# ---- Outputs ------------------------------------------------------------------------------------

APP_ID = "io.github.aryez.paragonphoto"
HICOLOR = [16, 24, 32, 48, 64, 128, 256, 512]


def write_all(root: pathlib.Path, app_id: str) -> list[pathlib.Path]:
    icons = root / "assets" / "app-icon"
    written = []

    def save(img, path, **kw):
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path, **kw)
        written.append(path)

    (icons / "photocraft.svg").write_text(svg_icon(True))
    (icons / "photocraft-small.svg").write_text(svg_icon(True))
    written += [icons / "photocraft.svg", icons / "photocraft-small.svg"]
    scal = icons / "hicolor" / "scalable" / "apps" / f"{app_id}.svg"
    scal.parent.mkdir(parents=True, exist_ok=True)
    scal.write_text(svg_icon(True))
    written.append(scal)

    cache: dict[int, Image.Image] = {}

    def icon(px):
        if px not in cache:
            cache[px] = render_icon(px, with_name=px > 32)
        return cache[px]

    for px in HICOLOR:
        save(icon(px), icons / "hicolor" / f"{px}x{px}" / "apps" / f"{app_id}.png")

    # macOS: the tile on Apple's 824/1024 grid.
    mac = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    mac.paste(render_icon(824, True, margin=0.02), (100, 100))
    save(mac, icons / "photocraft-1024.png")
    save(mac, icons / "photocraft.icns")
    save(icon(256), icons / "photocraft.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=".", help="repository root (default: current directory)")
    ap.add_argument("--app-id", default=APP_ID, help=f"reverse-DNS app id for the hicolor files (default {APP_ID})")
    ap.add_argument("--preview", help="only write a 1024 px preview PNG to this path")
    args = ap.parse_args()
    if args.preview:
        render_icon(1024, True).save(args.preview)
        print(args.preview)
        return
    for p in write_all(pathlib.Path(args.root), args.app_id):
        print(p)


if __name__ == "__main__":
    main()
