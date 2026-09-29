#!/usr/bin/env python3
"""Generate ``raspberry_pi_camera/boards.py`` from Raspberry Pi Ltd drawings.

Sources, all from Raspberry Pi Ltd and downloaded into ``tmp/rpi`` by
``tools/fetch_raspberry_pi_camera.sh``:

====================  ====================================================
Camera Module 2       vector PDF, plotted at 1.5:1, every letter outlined
Camera Module 3       vector PDF, true 1:1, with a live text layer
Camera Module 3 Wide  the same drawing again for the wide lens
====================  ====================================================

Neither is a 1:1 plot by assumption.  The scale is *recovered* from the
mounting-hole rectangle, which every camera module shares, and then checked
against the two overall dimensions the drawing prints; the Camera Module 3
drawings come out at 1.0000 and the Camera Module 2 drawing at 1.5055, so a
sheet that trusted the page would have been half again too big.

What can be machine-read differs between them, and the sheets say which is
which.  The Camera Module 3 drawings carry their dimension text as text, so
the figures this script quotes are checked against the file.  The Camera
Module 2 drawing carries none: ``page.chars`` is empty, every digit on it is
a filled path, so its printed figures are transcribed by eye and only its
*geometry* is machine-read.

Run: uv run --no-project --with pdfplumber python \\
         raspberry_pi_camera/extract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.dump_rpi_pdf import points_mm, rectangles  # noqa: E402

RPI = ROOT / "tmp" / "rpi"

DOC = "https://datasheets.raspberrypi.com/camera"
PIP = "https://pip.raspberrypi.com/documents"

#: The mounting-hole rectangle every Raspberry Pi camera module is built on,
#: in board coordinates: 21 mm apart across the 25 mm width and 12.5 mm apart
#: up the 23.862 mm height, the lower pair 2 mm in from two edges.  Read
#: exactly off the Camera Module 3 drawing, which is a true 1:1 plot, and
#: used to recover the scale of any camera drawing the same way
#: ``tools/dump_rpi_pdf.py`` recovers a Raspberry Pi board's from its own
#: 58 x 49 mm pattern.
HOLE_PITCH_X = 21.0
HOLE_PITCH_Y = 12.5
HOLE_INSET = 2.0

#: Raspberry Pi Ltd state that the two boards share these.  The claim is not
#: taken on trust: each drawing is read on its own and the readings compared,
#: and they have to agree within SHARED_TOL before one figure is used for
#: both.  "Board dimensions and mounting-hole positions for Camera Module 3
#: are identical to Camera Module 2" --
#: raspberrypi.com/documentation/accessories/camera.html, Advanced
#: information.
SHARED_TOL = 0.05

#: How far a recovered plot scale may sit from 1.0 and still be called a
#: true 1:1 plot.  The Camera Module 3 drawings measure 1.0000 and are; the
#: Camera Module 2 drawing measures 1.5055 and is described by that figure,
#: not rounded to the 1.5:1 it was presumably plotted at, because the number
#: on the sheet is the one the extraction actually used.
SCALE_TOLERANCE = 0.01

#: Feature numbers, fixed across the family: a number means the same part on
#: every camera sheet, whether or not that board carries it.
FEATURE_ORDER = ["lens", "ffc"]
FEATURE_NAMES = {
    "lens": "Lens and sensor module",
    "ffc": "Camera FFC connector, on the underside",
}

MODELS = [
    dict(
        key="cm2",
        title="Raspberry Pi Camera Module 2",
        subtitle="25 x 23.862 mm, Sony IMX219",
        file="camera-module-2-mechanical-drawing.pdf",
        drawing=f"{DOC}/camera-module-2-mechanical-drawing.pdf",
        drawing_note="Raspberry Pi Ltd, RPI-CAM-V2_1, 12/11/2015",
        width=25.0, height=23.862, corner_radius=2.0, thickness=None,
        # The drawing is plotted with the 25 mm width running up the page.
        # Stated rather than guessed, and checked: the hole rectangle's 21 mm
        # side has to come out on the axis this says it does.
        plan_rotation=90,
        hole_dia=2.2, hole_keepout=None,
        hole_note="Drawing note, quoted: 4x 2.2mm diameter holes. No "
                  "land or keep-out is shown.",
        # Geometry only.  Every figure printed on this drawing is an outlined
        # path, so nothing on it can be quoted back from the file.
        text_is_outlined=True,
        printed=(), printed_own=(),
        parts=[
            ("lens", "Lens and sensor module", "lens",
             (12.49, 14.40), (8.49, 8.49)),
        ],
        # Drawn as two boxes, the body and the wider latch ears that reach
        # the board edge, so the connector is the envelope of both.  Each is
        # selected in its own right; a selector for the union would match
        # nothing, because the union is never drawn.
        ffc_union=[((12.49, 20.49), (19.61, 4.30)),
                   ((12.49, 23.24), (20.88, 1.20))],
        ffc_side="bottom",
        # No elevation and no height anywhere on the sheet.
        height_note="The source drawing is a plan view only and gives no "
                    "height.",
        lens_note="Feature 1 is dimensioned 8.5 square. Its lower body, "
                  "stepped, reaches to 2.76 from the lower edge across 6.72 "
                  "to 16.14.",
    ),
    dict(
        key="cm3",
        title="Raspberry Pi Camera Module 3",
        subtitle="25 x 23.862 mm, standard and wide, Sony IMX708",
        file="camera-module-3-standard-mechanical-drawing.pdf",
        drawing=f"{DOC}/camera-module-3-standard-mechanical-drawing.pdf",
        drawing_note="Raspberry Pi Ltd, RP-008153-DS-1",
        # The wide drawing is the same sheet redrawn for the other lens, so
        # it carries its own five figures where the standard carries five
        # others.  Each drawing is checked against its own set; a set shared
        # between them would have to leave out exactly the figures this
        # sheet quotes for the wide lens.
        also=[("Camera Module 3 Wide",
               "camera-module-3-wide-mechanical-drawing.pdf",
               f"{DOC}/camera-module-3-wide-mechanical-drawing.pdf",
               "Raspberry Pi Ltd, RP-008155-DS-1",
               ("o6.95", "12", "8.3", "102", "67"), 6.95)],
        width=25.0, height=23.862, corner_radius=2.0, thickness=1.12,
        plan_rotation=0,
        hole_dia=2.2, hole_keepout=4.75,
        hole_note="o2.2, with an o4.75 land round each one.",
        text_is_outlined=False,
        # Quoted from the drawing's own text layer, and checked to be
        # there.  `printed` is what both Camera Module 3 drawings carry,
        # `printed_own` what only the standard one does.
        printed=("25", "23.862", "12.5", "14.5", "14.4", "10.8", "8.9",
                 "o2.2", "o4.75", "1.12", "2.75", "5.71", "19.61"),
        printed_own=("o5.75", "11.3", "6.98", "66", "41"),
        parts=[
            ("lens", "Lens and sensor module", "lens",
             (12.50, 14.40), (10.80, 10.80)),
        ],
        #: What the drawing prints beside the aperture circle.  Measured as
        #: well, and the two are required to stay close: the standard draws
        #: its o5.75 exactly and the wide draws o7.00 against a printed
        #: o6.95, which is the same disagreement the heights have.
        aperture_printed=5.75,
        ffc_side="bottom",
        # Not in the plan view: the connector is on the underside and the
        # drawing draws it only in the two elevations, so its width comes
        # from one and its depth from the other.
        ffc_from_elevations=True,
        height_note="Overall thickness printed 11.3 standard, 12 wide, "
                    "lens tip to connector back; lens assembly 6.98 and 8.3 "
                    "above the board. The source's own elevations scale 1.2 "
                    "short, so no height is drawn here.",
        lens_note="Clear aperture printed o5.75 standard, o6.95 wide; the "
                  "wide drawing draws o7.00. Feature 1's lower body, 8.9 "
                  "across, reaches to 1.70 from the lower edge.",
    ),
]


def is_scale(scale: float, ratio: float) -> bool:
    return abs(scale - ratio) <= SCALE_TOLERANCE


def describe_scale(scale: float) -> str:
    """How a sheet should describe the plot it was extracted from."""
    if is_scale(scale, 1.0):
        return "a true 1:1 plot"
    return f"a {scale:.4f}:1 plot"


def _closed(pts) -> bool:
    return len(pts) >= 5 and abs(pts[0][0] - pts[-1][0]) < 0.01 \
        and abs(pts[0][1] - pts[-1][1]) < 0.01


def circles(page) -> list[tuple[float, float, float]]:
    """(cx, cy, dia) for every circle, whole or drawn as quarter arcs.

    Raspberry Pi's two camera drawings draw the same hole two ways: the
    Camera Module 3 plot emits a closed path per circle, the Camera Module 2
    plot emits four separate quarter arcs.  A quarter arc's bounding box is a
    square with the circle's centre at one of its corners, so the four
    quarters of one circle all name that centre and nothing else names it
    more than twice -- the other three corners of a quarter's box lie on the
    circle and are shared by at most one neighbouring quarter.  A circle is
    a corner three or more quarters of the same size agree on.

    Merging boxes by proximity will not do it.  A mounting hole sits 2 mm in
    from two edges of a board whose corner radius is 2 mm, so the hole and
    the corner arc are *concentric*: merged, they give one blob half again
    the size of either.  Told apart by radius they are two circles, which is
    what they are.
    """
    found: list[tuple[float, float, float]] = []
    votes: dict[tuple[int, int, int], list[tuple[float, float, float]]] = {}
    for obj in page.curves:
        pts = points_mm(page, obj)
        if len(pts) < 2:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if w < 0.2 or h < 0.2 or abs(w - h) > 0.05 * max(w, h):
            continue
        if _closed(pts):
            found.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
                          (w + h) / 2))
            continue
        r = (w + h) / 2
        for cx in (min(xs), max(xs)):
            for cy in (min(ys), max(ys)):
                # Every point of the arc, control points included, sits
                # between one and about 1.15 radii from the true centre.
                if not all(0.97 * r <= ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
                           <= 1.20 * r for px, py in pts):
                    continue
                key = (round(cx / 0.05), round(cy / 0.05), round(r / 0.05))
                votes.setdefault(key, []).append((cx, cy, r))
    for group in votes.values():
        if len(group) < 3:
            continue
        n = len(group)
        found.append((sum(g[0] for g in group) / n,
                      sum(g[1] for g in group) / n,
                      2 * sum(g[2] for g in group) / n))
    return found


def boxes(page) -> list[tuple[float, float, float, float]]:
    """Every axis-aligned rectangle the page draws, however it draws it.

    Three ways, because these two drawings use all three: a PDF rectangle
    operator, a closed path of four corners, and four separate straight
    segments that have to be paired up again.
    """
    out = []
    for r in page.rects:
        out.append((r["x0"] / 72 * 25.4, (page.height - r["bottom"]) / 72 * 25.4,
                    r["x1"] / 72 * 25.4, (page.height - r["top"]) / 72 * 25.4))
    segs = []
    for obj in page.lines + page.curves:
        pts = points_mm(page, obj)
        if _closed(pts) and len(pts) <= 6:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            segs.append((ax, ay, bx, by))
    out += list(rectangles(segs))
    return out


def find_frame(page, model: dict):
    """Recover origin, scale and orientation from the mounting-hole rectangle.

    Returns ``(to_board, board_mm_per_page_mm, hole_dia)``.  *to_board* maps
    a page point in millimetres to board coordinates.  The middle value is
    how many board millimetres one page millimetre stands for, which is the
    reciprocal of the plot scale a sheet quotes: a 1.5055:1 plot gives
    0.6642.  *hole_dia* is the mounting holes' own diameter in board
    millimetres, measured here rather than taken from the drawing's text,
    which the Camera Module 2 plot does not have.

    The four smallest equal circles that sit on a rectangle of the right
    proportions are the mounting holes; their spacing gives the scale on each
    axis separately, and the two have to agree or the drawing is not a
    uniform plot of this board.
    """
    cands = circles(page)
    by_dia: dict[int, list] = {}
    for cx, cy, dia in cands:
        by_dia.setdefault(round(dia / 0.05), []).append((cx, cy, dia))
    best = None
    for group in by_dia.values():
        if len(group) < 4:
            continue
        xs = sorted({round(c[0], 2) for c in group})
        ys = sorted({round(c[1], 2) for c in group})
        if len(xs) != 2 or len(ys) != 2:
            continue
        dx, dy = xs[1] - xs[0], ys[1] - ys[0]
        long_on_x = dx > dy
        sx = (HOLE_PITCH_X if long_on_x else HOLE_PITCH_Y) / dx
        sy = (HOLE_PITCH_Y if long_on_x else HOLE_PITCH_X) / dy
        if abs(sx - sy) > 0.01 * sx:
            continue
        dia = sum(c[2] for c in group) / len(group) * (sx + sy) / 2
        if best is None or dia < best[0]:
            best = (dia, xs, ys, long_on_x, (sx + sy) / 2)
    if best is None:
        raise SystemExit(
            f"{model['key']}: no {HOLE_PITCH_X} x {HOLE_PITCH_Y} mm mounting "
            "hole rectangle in this drawing")
    dia, xs, ys, long_on_x, s = best
    rot = model["plan_rotation"]
    if long_on_x != (rot == 0):
        raise SystemExit(
            f"{model['key']}: plan_rotation says {rot} degrees but the "
            f"{HOLE_PITCH_X} mm hole pitch runs "
            f"{'across' if long_on_x else 'up'} the page")
    if rot == 0:
        def to_board(px, py):
            return ((px - xs[0]) * s + HOLE_INSET,
                    (py - ys[0]) * s + HOLE_INSET)
    else:
        # A quarter turn, not a transpose: swapping the axes would mirror the
        # board, which is easy to miss because the hole pattern is symmetric
        # across the 25 mm width.
        def to_board(px, py):
            return ((ys[1] - py) * s + HOLE_INSET,
                    (px - xs[0]) * s + HOLE_INSET)
    return to_board, s, dia


def pick(rects, key, centre, size, tol_pos=0.35, tol_size=0.35):
    """Choose the one outline matching a selector, as the Pi extractor does.

    The same rectangle turns up several times over -- as a path, as a merge
    of collinear segments, as a PDF rectangle -- so the tightest fit is taken
    and a disagreement wider than a tenth of a millimetre is printed, because
    that means the selector is not pinning down one feature.
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
    if spread > 0.1:
        print(f"    note: {key} matched {len(hits)} outlines spanning "
              f"{spread:.3f} mm; took the tightest")
    return tuple(round(v, 3) for v in best)


def measure_outline(segs, model: dict):
    """The board profile, from the four straight runs between its corners.

    Not from a rectangle: the outline is a rounded rectangle whose sides stop
    2 mm short of each corner, so no pair of its edges shares a span and the
    rectangle recovery cannot close it.  The four full-length straight runs
    are unambiguous on their own, and finding them where the recovered frame
    says they should be is what tests the frame.
    """
    r = model["corner_radius"]
    w, h = model["width"], model["height"]
    edges = {}
    for x0, y0, x1, y1 in segs:
        if abs(y1 - y0) < 0.02 and abs(x1 - x0) > w - 2 * r - 0.5:
            for name, at in (("bottom", 0.0), ("top", h)):
                if abs((y0 + y1) / 2 - at) < 0.5:
                    edges.setdefault(name, []).append((y0 + y1) / 2)
        elif abs(x1 - x0) < 0.02 and abs(y1 - y0) > h - 2 * r - 0.5:
            for name, at in (("left", 0.0), ("right", w)):
                if abs((x0 + x1) / 2 - at) < 0.5:
                    edges.setdefault(name, []).append((x0 + x1) / 2)
    missing = [k for k in ("left", "right", "bottom", "top") if k not in edges]
    if missing:
        raise SystemExit(
            f"{model['key']}: no board edge found where the recovered frame "
            f"puts the {', '.join(missing)}; the drawing has changed")
    return tuple(round(sum(edges[k]) / len(edges[k]), 3)
                 for k in ("left", "bottom", "right", "top"))


def ffc_from_elevations(page, model: dict):
    """The Camera Module 3 connector, built from the two elevations.

    It is on the underside, so the plan view does not draw it at all; the
    side elevation gives how far it reaches down the board and the front
    elevation how wide it is.  Both also draw the board's own section, which
    is what puts each measurement back in board coordinates, and both give
    its height, which is required to agree.
    """
    t = model["thickness"]
    h, w = model["height"], model["width"]
    found = {}
    for x0, y0, x1, y1 in boxes(page):
        bw, bh = x1 - x0, y1 - y0
        if abs(bw - w) < 0.05 and abs(bh - t) < 0.05:
            found["front"] = (x0, y0, x1, y1)
        if abs(bw - t) < 0.05 and abs(bh - h) < 0.05:
            found["side"] = (x0, y0, x1, y1)
    for want in ("front", "side"):
        if want not in found:
            raise SystemExit(
                f"{model['key']}: no {want} elevation section of the board "
                f"({w} x {t} / {t} x {h} mm) in this drawing")
    fx0, fy0, fx1, fy1 = found["front"]
    sx0, sy0, sx1, sy1 = found["side"]
    # The connector is the block sitting against the back face of the board
    # in each elevation: the far side from the lens in both.
    front = [b for b in boxes(page)
             if abs(b[1] - fy1) < 0.05 and b[0] > fx0 - 0.05
             and b[2] < fx1 + 0.05 and 1.0 < b[3] - b[1] < 4.0]
    side = [b for b in boxes(page)
            if abs(b[0] - sx1) < 0.05 and b[1] > sy0 - 0.05
            and b[3] < sy1 + 0.05 and 1.0 < b[2] - b[0] < 4.0]
    if not front or not side:
        raise SystemExit(f"{model['key']}: the connector is not on the back "
                         "face in both elevations")
    front = max(front, key=lambda b: b[2] - b[0])
    side = max(side, key=lambda b: b[3] - b[1])
    z_front = front[3] - front[1]
    z_side = side[2] - side[0]
    if abs(z_front - z_side) > 0.05:
        raise SystemExit(
            f"{model['key']}: the elevations disagree about the connector "
            f"height, {z_front:.3f} against {z_side:.3f}")
    x0 = front[0] - fx0
    x1 = front[2] - fx0
    y0 = side[1] - sy0
    y1 = side[3] - sy0
    return (round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)), z_front


def extract(model: dict) -> dict:
    path = RPI / model["file"]
    if not path.exists():
        raise SystemExit(f"missing source {path}; run "
                         "tools/fetch_raspberry_pi_camera.sh")
    page = pdfplumber.open(str(path)).pages[0]

    outlined = not page.chars
    if outlined != model["text_is_outlined"]:
        raise SystemExit(
            f"{model['key']}: the drawing's text layer "
            f"{'went away' if outlined else 'came back'}; the sheet says the "
            "opposite about what can be quoted from it")
    # Whole words, not a substring search over the page: "12" is a figure the
    # wide drawing prints on its own and also the first half of the "12.5"
    # both drawings print, so a substring test would pass on the wrong one.
    words = {w["text"].replace("ø", "o").rstrip("°")
             for w in page.extract_words()} if page.chars else set()
    for want in tuple(model["printed"]) + tuple(model["printed_own"]):
        if want not in words:
            raise SystemExit(
                f"{model['key']}: this sheet quotes {want!r} from the "
                "drawing and the drawing no longer prints it")

    to_board, s, hole_dia = find_frame(page, model)
    scale = 1.0 / s

    rects = []
    for x0, y0, x1, y1 in boxes(page):
        a = to_board(x0, y0)
        b = to_board(x1, y1)
        lo = (min(a[0], b[0]), min(a[1], b[1]))
        hi = (max(a[0], b[0]), max(a[1], b[1]))
        rects.append((lo[0], lo[1], hi[0], hi[1]))
    segs = []
    for obj in page.lines + page.curves:
        pts = points_mm(page, obj)
        for p, q in zip(pts, pts[1:]):
            a, b = to_board(*p), to_board(*q)
            segs.append((a[0], a[1], b[0], b[1]))

    # What the recovered plot scale is worth, checked rather than asserted:
    # the two overall dimensions the drawing prints have to come back out of
    # it, and the board's own edges have to land on the frame's axes.
    outline = measure_outline(segs, model)
    residual = max(abs(outline[0]), abs(outline[1]),
                   abs((outline[2] - outline[0]) - model["width"]),
                   abs((outline[3] - outline[1]) - model["height"]))

    features = []
    for key, label, kind, centre, size in model["parts"]:
        x0, y0, x1, y1 = pick(rects, key, centre, size)
        features.append(dict(key=key, label=label, kind=kind,
                             x0=x0, y0=y0, x1=x1, y1=y1, side="top"))
    ffc_z = None
    if model.get("ffc_union"):
        parts = [pick(rects, "ffc", centre, size)
                 for centre, size in model["ffc_union"]]
        features.append(dict(
            key="ffc", label="Camera FFC connector, 15-way", kind="connector",
            x0=round(min(p[0] for p in parts), 3),
            y0=round(min(p[1] for p in parts), 3),
            x1=round(max(p[2] for p in parts), 3),
            y1=round(max(p[3] for p in parts), 3), side="bottom"))
    if model.get("ffc_from_elevations"):
        (x0, y0, x1, y1), ffc_z = ffc_from_elevations(page, model)
        features.append(dict(key="ffc", label="Camera FFC connector, 15-way",
                             kind="connector", x0=x0, y0=y0, x1=x1, y1=y1,
                             side="bottom"))
    for f in features:
        if f["key"] == "ffc":
            f["side"] = model["ffc_side"]

    unknown = [f["key"] for f in features if f["key"] not in FEATURE_ORDER]
    if unknown:
        raise SystemExit(
            f"{model['key']}: {', '.join(unknown)} not in FEATURE_ORDER; "
            "decide where they belong in the schedule")
    features.sort(key=lambda f: FEATURE_ORDER.index(f["key"]))
    for f in features:
        f["number"] = FEATURE_ORDER.index(f["key"]) + 1

    # The clear aperture, measured rather than taken from the print.  It is
    # the largest circle drawn concentric with the lens module and smaller
    # than it: the aperture on both Camera Module 3 drawings, and nothing at
    # all on the Camera Module 2 drawing, which dimensions none.
    aperture = None
    if model.get("aperture_printed"):
        lens = next(f for f in features if f["kind"] == "lens")
        lcx, lcy = (lens["x0"] + lens["x1"]) / 2, (lens["y0"] + lens["y1"]) / 2
        span = min(lens["x1"] - lens["x0"], lens["y1"] - lens["y0"])
        inner = [dia * s for cx, cy, dia in circles(page)
                 for bx, by in [to_board(cx, cy)]
                 if abs(bx - lcx) < 0.1 and abs(by - lcy) < 0.1
                 and 0.5 < dia * s < span]
        if not inner:
            raise SystemExit(f"{model['key']}: no aperture circle on the lens")
        aperture = round(max(inner), 3)
        if abs(aperture - model["aperture_printed"]) > 0.2:
            raise SystemExit(
                f"{model['key']}: the aperture measures {aperture:.3f} "
                f"against a printed {model['aperture_printed']}; the sheet "
                "quotes the printed figure and would now be wrong")

    holes = []
    for cx, cy, dia in circles(page):
        bx, by = to_board(cx, cy)
        if abs(dia * s - model["hole_dia"]) > 0.2:
            continue
        if not (0 < bx < model["width"] and 0 < by < model["height"]):
            continue
        holes.append(dict(x=round(bx, 3), y=round(by, 3),
                          dia=model["hole_dia"],
                          keepout_dia=model["hole_keepout"], kind="mount"))
    if len(holes) != 4:
        raise SystemExit(f"{model['key']}: expected 4 mounting holes, got "
                         f"{len(holes)}")
    holes.sort(key=lambda h: (h["y"], h["x"]))
    for i, h in enumerate(holes, 1):
        h["label"] = f"MT{i}"

    return dict(model=model, features=features, holes=holes, scale=scale,
                hole_dia=hole_dia, outline=outline, residual=residual,
                ffc_z=ffc_z, aperture=aperture)


def cross_check(model: dict, rec: dict) -> None:
    """Read the other lens's drawing and require identical board geometry.

    One sheet covers the standard and the wide Camera Module 3 only for as
    long as the two drawings agree about the board.  Raspberry Pi say they
    do; this is what entitles the sheet to repeat it.
    """
    for name, filename, _, _, printed_own, aperture in model.get("also", ()):
        other = extract(dict(model, file=filename, also=(),
                             printed_own=printed_own,
                             aperture_printed=aperture))
        rec.setdefault("apertures", []).append((name, other["aperture"]))
        mine = sorted((h["x"], h["y"], h["dia"]) for h in rec["holes"])
        theirs = sorted((h["x"], h["y"], h["dia"]) for h in other["holes"])
        if max(abs(a - b) for m, t in zip(mine, theirs)
               for a, b in zip(m, t)) > SHARED_TOL:
            raise SystemExit(
                f"{model['key']}: {name} has a different hole pattern. "
                "It needs its own sheet.")
        for f, g in zip(rec["features"], other["features"]):
            if f["key"] != g["key"] or max(
                    abs(f[k] - g[k]) for k in ("x0", "y0", "x1", "y1")
                    ) > SHARED_TOL:
                raise SystemExit(
                    f"{model['key']}: {name} differs at {f['key']}. "
                    "It needs its own sheet.")


HEADER = '''"""Raspberry Pi camera module mechanical data, from Raspberry Pi Ltd drawings.

GENERATED FILE -- do not edit by hand.
Regenerate with::

    uv run --no-project --with pdfplumber python \\\\
        raspberry_pi_camera/extract.py

Coordinates follow :mod:`tools.schema`: origin at the lower-left corner of the
board, X right, Y up, top view, millimetres.  Top view means the lens side,
which is how Raspberry Pi draw the Camera Module 3 plan; the Camera Module 2
drawing is the same view turned a quarter turn on the page, and the extractor
turns it back.

The board is 25 mm across and 23.862 mm up.  The camera FFC connector is on
the underside, against the upper edge; the lens is near that same edge, at
14.4 mm up; the four mounting holes are 21 mm apart across and 12.5 mm apart
up, the lower pair 2 mm in from the lower and side edges.
"""

from __future__ import annotations

from tools.schema import BoardSpec, Feature, Hole, Outline, Source

BOARDS: dict[str, BoardSpec] = {}

#: Feature numbers are fixed across the family: a number means the same part
#: on every sheet.
FEATURE_NUMBERS = __NUMBERS__

'''


def render(rec: dict) -> str:
    m = rec["model"]
    # The optical axis is the one number a camera mount is designed around,
    # and it is not in either ordinate chain: on both boards it sits 0.1 mm
    # from a mounting hole's Y, so its witness line would print over the
    # hole's and neither label could be tied to a line.  It is stated here
    # instead, from the measured box rather than typed in.
    lens = next(f for f in rec["features"] if f["kind"] == "lens")
    lens = dict(lens, cx=(lens["x0"] + lens["x1"]) / 2,
                cy=(lens["y0"] + lens["y1"]) / 2)

    holes = ",\n".join(
        f"        Hole(x={h['x']}, y={h['y']}, dia={h['dia']}, "
        f"label={h['label']!r}, kind={h['kind']!r}, "
        f"keepout_dia={h['keepout_dia']})"
        for h in rec["holes"])
    feats = ",\n".join(
        f"        Feature(key={f['key']!r}, label={f['label']!r}, "
        f"kind={f['kind']!r},\n"
        f"                x0={f['x0']}, y0={f['y0']}, x1={f['x1']}, "
        f"y1={f['y1']},\n"
        f"                side={f['side']!r}, number={f['number']})"
        for f in rec["features"])

    also = "".join(
        f'        Source(label="Mechanical drawing", ref={ref!r},\n'
        f'               note={note!r}),\n'
        for _, _, ref, note, _, _ in m.get("also", ()))

    notes = [
        repr("Hole IDs are this drawing's, the same hole on every camera "
             "sheet. The two drawings are read separately and their hole "
             f"patterns agree to {rec['family_spread']:.3f}, which is why one "
             "sheet prints 22.98 where the other prints 23.00."),
        repr(f"Optical axis at X {lens['cx']:.2f}, Y {lens['cy']:.2f}, the "
             f"centre of feature {lens['number']}. " + m["lens_note"]),
        repr(m["height_note"]),
        repr(f"Source read as {describe_scale(rec['scale'])}: scale from "
             f"the {HOLE_PITCH_X} x {HOLE_PITCH_Y} hole rectangle, overall "
             f"dimensions then back within {rec['residual']:.3f}."),
    ]
    if m["text_is_outlined"]:
        notes.append(repr(
            "Every figure printed on the source is an outlined path, not "
            "text: its geometry is machine-read, its printed dimensions are "
            "transcribed by eye."))
    for name, _, _, _, _, _ in m.get("also", ()):
        notes.append(repr(
            f"The standard and wide drawings agree on the outline, holes and "
            f"lens module within {SHARED_TOL}, so one sheet covers both."))
    # No note saying the connector is on the underside: the legend already
    # carries "On the underside, seen through the board", and a sheet that
    # says a thing twice is a sheet with a line less of view.

    thickness = (f", thickness={m['thickness']}" if m["thickness"] else "")
    return f'''
BOARDS[{m["key"]!r}] = BoardSpec(
    key={m["key"]!r},
    title={m["title"]!r},
    subtitle={m["subtitle"]!r},
    family="raspberrypicamera",
    front_edge="top",
    outline=Outline(width={m["width"]}, height={m["height"]},
                    corner_radius={m["corner_radius"]}{thickness}),
    holes=(
{holes},
    ),
    features=(
{feats},
    ),
    sources=(
        Source(label="Mechanical drawing", ref={m["drawing"]!r},
               note={m["drawing_note"]!r}),
{also}        Source(label="Mounting holes", ref={m["drawing"]!r},
               note={m["hole_note"]!r}),
    ),
    notes=(
        {",\n        ".join(notes)},
    ),
)
'''


def main() -> None:
    records = []
    for model in MODELS:
        rec = extract(model)
        cross_check(model, rec)
        records.append(rec)

    # Raspberry Pi say the two boards share an outline and a hole pattern.
    # Read separately they do, to a hundredth of a millimetre; said rather
    # than snapped, so each sheet still carries what its own drawing gave.
    ref = records[0]
    for rec in records[1:]:
        spread = max(abs(a[k] - b[k])
                     for a, b in zip(sorted(ref["holes"],
                                            key=lambda h: (h["y"], h["x"])),
                                     sorted(rec["holes"],
                                            key=lambda h: (h["y"], h["x"])))
                     for k in ("x", "y"))
        if spread > SHARED_TOL:
            raise SystemExit(
                "Raspberry Pi state the Camera Module 2 and 3 hole patterns "
                f"are identical, but the drawings disagree by {spread:.3f} "
                f"mm, over the {SHARED_TOL} mm allowed. Check the sources.")
        print(f"  {ref['model']['key']} against {rec['model']['key']}: "
              f"hole patterns agree to {spread:.3f} mm")
        # Both sheets say it, because a reader comparing them sees MT2 and
        # MT4 at 22.98 on one and 23.00 on the other and is owed the reason.
        # Each record carries its own figure, and the reference carries the
        # widest of the disagreements it is the reference for, so a third
        # camera joining the family cannot overwrite the second's.
        rec["family_spread"] = spread
        ref["family_spread"] = max(ref.get("family_spread", 0.0), spread)

    numbers = "{\n" + "".join(
        f"    {i}: {FEATURE_NAMES[key]!r},\n"
        for i, key in enumerate(FEATURE_ORDER, 1)) + "}"
    chunks = [HEADER.replace("__NUMBERS__", numbers)]
    for rec in records:
        m = rec["model"]
        chunks.append(render(rec))
        print(f"{m['key']:5s} {m['width']:5.1f} x {m['height']:6.3f} mm  "
              f"{len(rec['holes'])} holes  {len(rec['features'])} features  "
              f"plot={rec['scale']:.4f}  hole dia read {rec['hole_dia']:.3f}  "
              f"outline residual {rec['residual']:.3f} mm")
        for name, dia in ([(m["title"], rec["aperture"])] if rec["aperture"]
                          else []) + rec.get("apertures", []):
            printed = (m["aperture_printed"] if name == m["title"]
                       else next(a for n, _, _, _, _, a in m["also"]
                                 if n == name))
            print(f"  {name}: aperture printed {printed}, drawn {dia:.3f}"
                  + ("" if abs(dia - printed) < 0.005 else "  <- differ"))
    out = ROOT / "raspberry_pi_camera" / "boards.py"
    out.write_text("".join(chunks))
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
