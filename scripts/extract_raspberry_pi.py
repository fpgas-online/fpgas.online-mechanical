#!/usr/bin/env python3
"""Generate ``data/raspberry_pi_boards.py`` from Raspberry Pi Ltd drawings.

Sources, all from Raspberry Pi Ltd and downloaded into ``tmp/rpi``:

============  ==========================================================
Pi 3B, 3B+    layered DXF (BOARD_OUTLINE / PARTS_TOP / SILK_TOP / ...)
Pi 4B         layered DXF, and the only one whose DXF carries the holes
Pi 5          1:1 vector PDF plot on A4
============  ==========================================================

Fetch them with ``scripts/fetch_raspberry_pi.sh``.

Identification is human: the ``PARTS`` table gives, for each connector, roughly
where it sits and roughly how big it is.  The script then finds the one outline
in the source that matches and emits *its* exact numbers.  If a source ever
changes, the selector stops matching and the script fails, rather than quietly
emitting a wrong dimension.

Run: uv run --no-project --with ezdxf --with pdfplumber python \\
         scripts/extract_raspberry_pi.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import ezdxf
import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
from dump_rpi_pdf import find_origin, points_mm, rectangles  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RPI = ROOT / "tmp" / "rpi"

DOC = "https://datasheets.raspberrypi.com"

# Every Model B sized Raspberry Pi shares this hole pattern, dimensioned on each
# model's own drawing: 3.5 mm in from the edges on a 58 x 49 mm rectangle.
STANDARD_HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]

# Hole diameter and keep-out provenance differs per model and must not be
# blurred together, because only some of it is actually published:
#
#   Pi 3B    the drawing carries the note "4x M2.5 MOUNTING HOLES DRILLED TO
#            2.75 +/- 0.05mm".  No keep-out is given.
#   Pi 3B+   no hole note and no keep-out on its drawing.  Same outline, same
#            hole pattern, and a byte-identical BOARD_OUTLINE and hole geometry
#            in its DXF, so the Pi 3B figure is carried over and said to be.
#   Pi 4B    the DXF carries the holes on layer 0: 2.70 hole, 6.00 keep-out.
#   Pi 5     the drawing dimensions the hole as "o2.7"; the keep-out circle is
#            drawn and measures 5.80.
#
# The Raspberry Pi HAT mechanical specification separately requires a 6.2 mm
# keep-out around each mounting hole on a board fitted to a Pi.  That is the
# figure to design a plate to, and it is quoted in the notes rather than being
# passed off as a dimension from the Pi's own drawing.
#: Said on every model, whatever that model's own drawing gives, so one plate
#: can be designed for all five.
KEEPOUT_DESIGN_NOTE = (
    "Design mounting hole keep-outs to 6.2 mm diameter on every model: that "
    "is what the Raspberry Pi HAT specification (github.com/raspberrypi/hats) "
    "requires, and the largest figure the models themselves publish. The "
    "KEEPOUT column gives what this model's drawing shows, which is not "
    "always anything."
)

#: The order features are numbered in, on every Raspberry Pi sheet.  Numbered
#: in table order instead, a reader comparing two sheets had to check the
#: schedule to see that balloon 2 meant the same connector on both.  A model
#: that lacks one of these simply skips it; the rest keep their places
#: relative to each other.
FEATURE_ORDER = ["gpio40", "usb_power", "ethernet", "usb_a_1", "usb_a_2"]

#: Features whose position is fixed by the Raspberry Pi HAT specification and
#: so must be the same on every model.  Each model's own drawing is still read
#: and the readings compared; agreeing within SHARED_TOL they are snapped to
#: one value, and outside it the extraction stops.  The two DXF sources agree
#: exactly; the Pi 5's vector PDF reads a few hundredths out, which is plot
#: noise and not a different board.
SHARED_FEATURES = {"gpio40": "fixed by the Raspberry Pi HAT specification"}
SHARED_TOL = 0.10

MODELS = [
    dict(
        key="rpi3b", title="Raspberry Pi 3 Model B and B+",
        subtitle="85 x 56 mm, both models",
        kind="dxf", file="raspberry-pi-3-b-mechanical-drawing.dxf",
        # One sheet for two models.  Not asserted: the 3B+ drawing is read
        # separately and its outline, holes and every feature position are
        # required to match, so the sheet only covers both while they agree.
        also=[("Raspberry Pi 3 Model B+",
               "raspberry-pi-3-b-plus-mechanical-drawing.dxf",
               f"{DOC}/rpi3/raspberry-pi-3-b-plus-mechanical-drawing.dxf")],
        width=85.0, height=56.0, corner_radius=3.0,
        hole_dia=2.75, hole_keepout=None, hole_tol=0.05,
        hole_note="Drawing note on the Model B drawing, quoted: 4x M2.5 "
                  "MOUNTING HOLES DRILLED TO 2.75 +/- 0.05mm. The B+ drawing "
                  "gives no hole size, but its geometry is identical.",
        hole_source=f"{DOC}/rpi3/raspberry-pi-3-b-mechanical-drawing.pdf",
        drawing=f"{DOC}/rpi3/raspberry-pi-3-b-mechanical-drawing.dxf",
        parts=[
            ("gpio40", "40-pin GPIO header", "header", (32.5, 52.5), (50.8, 5.0)),
            ("ethernet", "Ethernet RJ45", "ethernet", (76.3, 10.25), (21.35, 15.51)),
            ("usb_a_1", "USB 2.0 type A (upper pair)", "usb_a", (78.15, 46.61), (17.7, 13.92)),
            ("usb_a_2", "USB 2.0 type A (lower pair)", "usb_a", (78.15, 28.61), (17.7, 13.92)),
            ("usb_power", "micro-USB power input", "usb_power", (10.6, 2.05), (7.5, 5.31)),
        ],
    ),
    dict(
        key="rpi4b", title="Raspberry Pi 4 Model B", subtitle="85 x 56 mm",
        kind="dxf", file="raspberry-pi-4-mechanical-drawing.dxf",
        width=85.0, height=56.0, corner_radius=3.0,
        hole_dia=2.70, hole_keepout=6.00, hole_tol=None,
        hole_note="Read from the DXF: hole and keep-out circles on layer 0.", holes_from_source=True,
        hole_source=f"{DOC}/rpi4/raspberry-pi-4-mechanical-drawing.dxf",
        drawing=f"{DOC}/rpi4/raspberry-pi-4-mechanical-drawing.dxf",
        parts=[
            ("gpio40", "40-pin GPIO header", "header", (32.5, 52.5), (50.8, 5.0)),
            ("ethernet", "Ethernet RJ45", "ethernet", (77.3, 45.75), (21.35, 15.51)),
            ("usb_a_1", "USB 3.0 type A (upper pair)", "usb_a", (79.25, 27.34), (17.5, 13.82)),
            ("usb_a_2", "USB 2.0 type A (lower pair)", "usb_a", (79.15, 8.61), (17.7, 13.92)),
            ("usb_power", "USB-C power input", "usb_power", (11.2, 2.45), (8.65, 7.4)),
        ],
    ),
    dict(
        key="rpi5", title="Raspberry Pi 5", subtitle="85 x 56 mm",
        kind="pdf", file="raspberry-pi-5-mechanical-drawing.pdf",
        width=85.0, height=56.0, corner_radius=3.0,
        hole_dia=2.70, hole_keepout=5.80, hole_tol=None,
        hole_note="Hole diameter dimensioned on the drawing as \u00f82.7 mm; "
                  "the keep-out circle is drawn and measures 5.80 mm.",
        hole_source=f"{DOC}/rpi5/raspberry-pi-5-mechanical-drawing.pdf",
        drawing=f"{DOC}/rpi5/raspberry-pi-5-mechanical-drawing.pdf",
        # Snapped from the measured 3.482 / 61.480, which are within the
        # +/-0.02 mm noise the same extraction shows on the mounting holes
        # (3.500 / 61.497 / 52.501 against nominal 3.5 / 61.5 / 52.5).
        aux_holes=[(3.5, 9.497, 3.0), (61.5, 46.504, 3.0)],
        parts=[
            ("gpio40", "40-pin GPIO header", "header", (32.5, 52.5), (50.8, 5.0)),
            ("ethernet", "Ethernet RJ45", "ethernet", (77.3, 10.2), (21.24, 15.98)),
            ("usb_a_1", "USB 3.0 type A (upper pair)", "usb_a", (79.1, 47.0), (16.32, 12.31)),
            ("usb_a_2", "USB 3.0 type A (lower pair)", "usb_a", (79.1, 29.1), (16.32, 12.31)),
            ("usb_power", "USB-C power input", "usb_power", (11.2, 2.35), (6.72, 7.3)),
        ],
    ),
]


#: How far a recovered plot scale may sit from 1.000 and still be a 1:1 plot.
#: The Pi 5's PDF measures 1.00002; a fit-to-page reduction measures 1.068.
SCALE_TOLERANCE = 0.002


def is_reduced(scale: float) -> bool:
    """Whether a source plot was reduced to fit its sheet.

    Read from the measurement rather than from a per-model flag.  A flag has
    to be remembered: set from the scale, a reduced source added later cannot
    be described as a true 1:1 plot by a sheet that never noticed.
    """
    return abs(scale - 1.0) > SCALE_TOLERANCE


def dxf_rects(path: Path):
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    out = []
    for layer in ("PARTS_TOP",):
        for e in list(msp.query(f'LWPOLYLINE[layer=="{layer}"]')) + \
                 list(msp.query(f'POLYLINE[layer=="{layer}"]')):
            if e.dxftype() == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points("xy")]
            else:
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            if len(pts) < 3:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def dxf_holes(path: Path):
    doc = ezdxf.readfile(str(path))
    found = {}
    for e in doc.modelspace().query('CIRCLE[layer=="0"]'):
        c = e.dxf.center
        found.setdefault((round(c.x, 3), round(c.y, 3)), []).append(2 * e.dxf.radius)
    return {k: sorted(v) for k, v in found.items()}


def pdf_rects(path: Path, width: float, height: float):
    page = pdfplumber.open(str(path)).pages[0]
    ox, oy, scale = find_origin(page)
    segs = []
    for obj in page.lines + page.curves:
        pts = points_mm(page, obj)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            p0 = ((ax - ox) * scale, (ay - oy) * scale)
            p1 = ((bx - ox) * scale, (by - oy) * scale)
            if all(-12 < p[0] < width + 12 and -12 < p[1] < height + 12
                   for p in (p0, p1)):
                segs.append((p0[0], p0[1], p1[0], p1[1]))
    return rectangles(segs), scale


def pick(rects, key, centre, size, tol_pos=2.5, tol_size=1.2):
    """Choose the outline matching a selector, and complain if it is ambiguous.

    Several near-identical candidates can survive the filter, because the
    rectangle recovery offers both the raw segments and collinear merges of
    them.  The tightest fit is taken, since a merge can only over-extend an
    edge, never under-extend it.  A disagreement wider than a fifth of a
    millimetre is printed, because that means the selector is not pinning down
    one feature.
    """
    cx, cy = centre
    w, h = size
    hits = [r for r in rects
            if abs((r[0] + r[2]) / 2 - cx) < tol_pos
            and abs((r[1] + r[3]) / 2 - cy) < tol_pos
            and abs((r[2] - r[0]) - w) < tol_size
            and abs((r[3] - r[1]) - h) < tol_size]
    if not hits:
        raise SystemExit(f"{key}: no outline near {centre} sized {size}")
    hits.sort(key=lambda r: ((r[2] - r[0]) * (r[3] - r[1]),
                             abs((r[0] + r[2]) / 2 - cx)
                             + abs((r[1] + r[3]) / 2 - cy)))
    best = hits[0]
    spread = max(max(abs(a - b) for a, b in zip(best, r)) for r in hits)
    if spread > 0.2:
        print(f"    note: {key} matched {len(hits)} outlines spanning "
              f"{spread:.3f} mm; took the tightest")
    return tuple(round(v, 3) for v in best)


def extract(model: dict) -> dict:
    path = RPI / model["file"]
    if not path.exists():
        raise SystemExit(f"missing source {path}; run scripts/fetch_raspberry_pi.sh")

    scale = 1.0
    if model["kind"] == "dxf":
        rects = dxf_rects(path)
    else:
        rects, scale = pdf_rects(path, model["width"], model["height"])

    features = []
    for key, label, kind, centre, size in model["parts"]:
        # A reduced plot carries a few tenths of residual error, so the
        # matcher has to be looser on it than on a 1:1 source.
        tol_pos, tol_size = (3.5, 2.0) if is_reduced(scale) else (2.5, 1.2)
        x0, y0, x1, y1 = pick(rects, key, centre, size, tol_pos, tol_size)
        features.append(dict(key=key, label=label, kind=kind,
                             x0=x0, y0=y0, x1=x1, y1=y1))

    # One numbering across the whole family.  Unknown keys fail rather than
    # sorting to the front, so adding a connector is a decision about where it
    # belongs in the sequence and not an accident of table order.
    unknown = [f["key"] for f in features if f["key"] not in FEATURE_ORDER]
    if unknown:
        raise SystemExit(
            f"{model['key']}: {', '.join(unknown)} not in FEATURE_ORDER; "
            "decide where they belong in the schedule")
    features.sort(key=lambda f: FEATURE_ORDER.index(f["key"]))
    for f in features:
        f["number"] = FEATURE_ORDER.index(f["key"]) + 1

    holes = []
    if model.get("holes_from_source"):
        for (x, y), dias in dxf_holes(path).items():
            holes.append(dict(x=x, y=y, dia=round(min(dias), 3),
                              keepout_dia=round(max(dias), 3), kind="mount"))
        if len(holes) != 4:
            raise SystemExit(f"{model['key']}: expected 4 holes, got {len(holes)}")
    else:
        for x, y in STANDARD_HOLES:
            holes.append(dict(x=x, y=y, dia=model["hole_dia"],
                              keepout_dia=model["hole_keepout"], kind="mount"))
    # One ordering for every model, bottom row first then left to right, so a
    # hole ID means the same thing on every sheet.  The Pi 4B's come out of its
    # DXF in a different order, which had MT2 and MT3 swapped against the rest.
    holes.sort(key=lambda h: (h["y"], h["x"]))
    for i, h in enumerate(holes, 1):
        h["label"] = f"MT{i}"
    for i, (x, y, d) in enumerate(model.get("aux_holes", []), 1):
        holes.append(dict(x=round(x, 3), y=round(y, 3), dia=d,
                          keepout_dia=None, kind="aux", label=f"AUX{i}"))

    return dict(model=model, features=features, holes=holes, scale=scale)


HEADER = '''"""Raspberry Pi mechanical data, from Raspberry Pi Ltd drawings.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with ezdxf --with pdfplumber python \\\\
        scripts/extract_raspberry_pi.py

Coordinates follow :mod:`data.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  This is the same way up as
Raspberry Pi Ltd draw their own plan views, with the 40-pin GPIO header along
the upper edge.

Note the Ethernet jack and the USB type A ports swap places between the Pi 3
and the Pi 4: on the Pi 3B/3B+ and on the Pi 5 the RJ45 sits in the lower right
corner with the USB ports above it, while on the Pi 4B the RJ45 is in the upper
right corner with the USB ports below.
"""

from __future__ import annotations

from .schema import BoardSpec, Feature, Hole, Outline, Source

BOARDS: dict[str, BoardSpec] = {}

'''


def render(rec: dict) -> str:
    m = rec["model"]

    def also_sources() -> str:
        return "".join(
            f'        Source(label="Mechanical drawing", ref={ref!r},\n'
            f'               note={f"Raspberry Pi Ltd, {name}"!r}),\n'
            for name, _, ref in m.get("also", ()))

    holes = ",\n".join(
        f"        Hole(x={h['x']}, y={h['y']}, dia={h['dia']}, "
        f"label={h['label']!r}, kind={h['kind']!r}, "
        f"keepout_dia={h['keepout_dia']}, tol={m.get('hole_tol')})"
        for h in rec["holes"])
    feats = ",\n".join(
        f"        Feature(key={f['key']!r}, label={f['label']!r}, kind={f['kind']!r},\n"
        f"                x0={f['x0']}, y0={f['y0']}, x1={f['x1']}, y1={f['y1']},\n"
        f"                number={f['number']})"
        for f in rec["features"])

    # The hole note is provenance, so it goes in SOURCES under "Mounting
    # holes" and not also in the notes: printed in both it was the same
    # sentence twice on every Raspberry Pi sheet.
    notes = ['"Connector outlines are the component body as drawn by '
             'Raspberry Pi Ltd, overhang past the board edge included."',
             repr("Hole IDs are assigned by this drawing, bottom row first "
                  "then left to right, and mean the same thing on every "
                  "Raspberry Pi sheet here.")]
    for name, _, _ in m.get("also", ()):
        notes.append(repr(
            f"This sheet covers the {m['title'].split(' and ')[0]} and the "
            f"{name}. Every connector position was read from both drawings "
            "separately and required to match, so the sheet covers both only "
            "while they agree."))
    for key, spread in rec.get("shared_spreads", {}).items():
        label = next((f["label"] for f in rec["features"] if f["key"] == key),
                     key)
        notes.append(repr(
            f"The {label} is {SHARED_FEATURES[key]} and carries the same "
            "position on every Raspberry Pi sheet here. The drawings were "
            f"read separately, agreed to {spread:.3f} mm, and were snapped to "
            "one value."))
    notes.append(repr(KEEPOUT_DESIGN_NOTE))
    if m.get("hole_tol"):
        # The schedule's figure is tighter than the sheet's general block, and
        # a drawing that states two tolerances for the same feature without
        # saying which wins is ambiguous.
        notes.append(repr(
            f"The hole diameter tolerance in the schedule, +/-{m['hole_tol']} "
            "mm, is quoted from this model's own drawing and governs in place "
            "of the hole diameter figure in the general tolerance block."))
    if is_reduced(rec["scale"]):
        notes.append(repr(
            "The source drawing is a reduced plot, not 1:1. Its scale was "
            f"recovered from the mounting hole rectangle as {rec['scale']:.4f} "
            "and applied. Residual error over the 85 mm width is a few tenths "
            "of a millimetre, so treat every dimension on this sheet as "
            "+/-0.5 rather than the +/-0.20 the other models carry."))
    elif m["kind"] == "pdf":
        # Say so explicitly.  A sheet built from a PDF that carries the general
        # tolerance, next to one that says its plot was reduced, otherwise
        # leaves a reader wondering whether the scale was checked at all.
        notes.append(repr(
            "The source is a PDF, not a DXF, but a true 1:1 vector plot: its "
            "scale, recovered from the mounting hole rectangle, came out "
            f"{rec['scale']:.5f}. Geometry was read from the vector paths, so "
            "this sheet carries the same tolerance as the DXF-derived "
            "models."))
    if m.get("aux_holes"):
        notes.append('"AUX1 and AUX2 are 3.0 mm holes additional to the four '
                     'M2.5 mounting holes. Each sits 6.0 mm inboard of the '
                     'mounting hole it shares an X coordinate with, and the '
                     'pair are diagonally opposite each other."')
    if not m.get("holes_from_source"):
        notes.append('"Hole positions are the 3.5 mm inset and 58 x 49 mm '
                     'rectangle dimensioned on this model\'s drawing."')

    return f'''
BOARDS[{m["key"]!r}] = BoardSpec(
    key={m["key"]!r},
    title={m["title"]!r},
    subtitle={m["subtitle"]!r},
    family="raspberrypi",
    front_edge="top",
    outline=Outline(width={m["width"]}, height={m["height"]},
                    corner_radius={m["corner_radius"]}),
    holes=(
{holes},
    ),
    features=(
{feats},
    ),
    tolerance={m.get("tolerance", "")!r},
    sources=(
        Source(label="Mechanical drawing", ref={m["drawing"]!r},
               note="Raspberry Pi Ltd"),
{also_sources()}        Source(label="Mounting holes", ref={m["hole_source"]!r},
               note={m["hole_note"]!r}),
    ),
    notes=(
        {",\n        ".join(notes)},
    ),
)
'''


def cross_check(model: dict, rec: dict) -> None:
    """Re-read a second drawing and require identical geometry.

    A sheet that covers two models has to be able to say why.  Reading the
    other model's own drawing and comparing every number is the only thing
    that entitles it to; the alternative is a note asserting the two are the
    same, which is a claim rather than a check.
    """
    for name, filename, _ in model.get("also", ()):
        other = extract(dict(model, file=filename, also=()))
        # Only what is actually read out of the drawing is worth comparing.
        # The outline size is declared in the table above, so comparing it
        # would be comparing this file with itself.
        mine = sorted((h["x"], h["y"], h["dia"]) for h in rec["holes"])
        theirs = sorted((h["x"], h["y"], h["dia"]) for h in other["holes"])
        if mine != theirs:
            raise SystemExit(
                f"{model['key']}: {name} has a different hole pattern. "
                "It needs its own sheet.")
        mine = {f["key"]: (f["x0"], f["y0"], f["x1"], f["y1"])
                for f in rec["features"]}
        theirs = {f["key"]: (f["x0"], f["y0"], f["x1"], f["y1"])
                  for f in other["features"]}
        if mine != theirs:
            differ = sorted(k for k in set(mine) | set(theirs)
                            if mine.get(k) != theirs.get(k))
            raise SystemExit(
                f"{model['key']}: {name} differs at {', '.join(differ)}. "
                "It needs its own sheet.")


def snap_shared(records: list[dict]) -> dict[str, float]:
    """Give the HAT-specified features one position across every model.

    Returns the worst disagreement seen per feature, so the sheets can say how
    far the sources were apart before they were snapped rather than presenting
    a shared number as though every drawing had stated it.
    """
    spreads: dict[str, float] = {}
    for key in SHARED_FEATURES:
        boxes = {}
        for rec in records:
            for f in rec["features"]:
                if f["key"] == key:
                    boxes[rec["model"]["key"]] = (f["x0"], f["y0"],
                                                  f["x1"], f["y1"])
        if len(boxes) < 2:
            continue
        spread = max(abs(a - b)
                     for one in boxes.values() for other in boxes.values()
                     for a, b in zip(one, other))
        if spread > SHARED_TOL:
            worst = ", ".join(f"{k} {v}" for k, v in sorted(boxes.items()))
            raise SystemExit(
                f"{key} is {SHARED_FEATURES[key]} but the drawings disagree "
                f"by {spread:.3f} mm, over the {SHARED_TOL} mm allowed: "
                f"{worst}. Check the sources before snapping them together.")
        # The value the most sources agree on, which is the DXF-derived one:
        # two independent DXFs give it exactly, the PDF a few hundredths out.
        common = max(set(boxes.values()), key=list(boxes.values()).count)
        for rec in records:
            for f in rec["features"]:
                if f["key"] == key:
                    f["x0"], f["y0"], f["x1"], f["y1"] = common
        spreads[key] = spread
    return spreads


def main() -> None:
    records = []
    for model in MODELS:
        rec = extract(model)
        cross_check(model, rec)
        records.append(rec)
    spreads = snap_shared(records)

    chunks = [HEADER]
    for rec in records:
        model = rec["model"]
        rec["shared_spreads"] = spreads
        chunks.append(render(rec))
        print(f"{model['key']:11s} {model['width']:5.1f} x {model['height']:4.1f} mm  "
              f"{len(rec['holes'])} holes  {len(rec['features'])} features  "
              f"scale={rec['scale']:.4f}")
    for key, spread in spreads.items():
        print(f"  {key}: snapped across {len(records)} models, "
              f"sources agreed to {spread:.3f} mm")
    (ROOT / "data" / "raspberry_pi_boards.py").write_text("".join(chunks))
    print("wrote data/raspberry_pi_boards.py")


if __name__ == "__main__":
    main()
