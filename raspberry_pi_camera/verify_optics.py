#!/usr/bin/env python3
"""Check that the camera position sheets say what they can be shown to say.

From the data modules rather than from the drawings:

* every figure quoted in :mod:`raspberry_pi_camera.optics` is really in the
  vendor page cached under ``tmp/src/rpi-camera-optics/``;
* the rectilinear model reproduces Raspberry Pi's own declared field of view
  from their own focal length and sensor size, which is what makes it the
  right model for the stock lens rather than a convenient one;
* every lens's figures are tested against the sensor's own shape under the
  lens's projection and the other one, the one declared pair that cannot be
  right under any projection is named, and the wide lens's pair is the
  split of its declared diagonal it is said to be, between the rectilinear
  and equisolid splits of it;
* the frame margin absorbs every alternative pair the evidence allows, at
  the height the sheet prints, and the wide lens's barrel distortion puts
  the frame's corners inside the picture rather than outside it;
* every frame is the smallest rectangle of the sensor's aspect ratio holding
  its target plus the stated margin, and the camera sits over its centre at a
  height where both angles reach it, for every lens;
* every target whose plane is not the subject's own top face says so, because
  a height set at the wrong plane covers less at the right one;
* the hyperfocal distance and depth of field of every lens, and every
  height against every lens's declared focus range, with how soft a fixed
  lens is there and how deep the field is once a motorised one has focused;
* what the elevations draw and print: that the declared angle each one
  shows is the one lying along its axis, that it reaches the frame's edge
  from the lens, that the camera is turned the way that needs the lower
  camera, the height above the plate face on the mounting plate sheet, and
  the figures the notes derive.

The focus check passes while reporting every fixed-focus height as out of
range.  It has to: both fixed lenses are declared "1 m to infinity" and
every board here wants the camera a tenth of that away.  What is being
checked is that the sheet says so, not that the problem has gone away.

Run: uv run --no-project --with pypdf \\
         python raspberry_pi_camera/verify_optics.py
"""

from __future__ import annotations

import html
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from raspberry_pi_camera import optics  # noqa: E402
from raspberry_pi_camera.optics import (ASPECT, CONSISTENCY_TOL,  # noqa: E402
                                        FOV_CHECK, FOV_CHECK_TOL,
                                        FRAME_MARGIN, LENSES,
                                        coincident_edges, place, subjects)

#: Where the fetch script leaves the pages the optics module quotes.
CACHE = ROOT / "tmp" / "src" / "rpi-camera-optics"

#: Every figure the optics module takes from a vendor, as the vendor's own
#: words, and the cached file it has to appear in.  Written out here rather
#: than parsed out of the module's ``Source`` notes: this file has to be able
#: to disagree with that one, which it cannot do if it reads its expectations
#: from it.
QUOTES = {
    "raspberry-pi-camera-documentation.html": [
        "OmniVision OV5647",
        "2592 × 1944 pixels",
        "3.76 × 2.74 mm",
        "1.4 µm × 1.4 µm",
        "3.60 mm +/- 0.01",
        "Focal ratio (F-Stop) F2.9",
        "53.50 +/- 0.13 degrees",
        "41.41 +/- 0.11 degrees",
        "Focus Fixed Adjustable Motorized Motorized",
        "Depth of field Approx 1 m to ∞ Approx 10 cm to ∞",
        "Approx 5 cm to ∞",
    ],
    # OmniVision's own datasheet: the active array the declared angles are
    # measured to, and the larger "image area" round it that Raspberry Pi's
    # 3.76 x 2.74 looks like a transposition of.
    "ov5647-datasheet.pdf": [
        "active array size: 2592 x 1944",
        "pixel size: 1.4 µm x 1.4 µm",
        "image area: 3673.6 µm x 2738.4 µm",
        "lens chief ray angle: 24°",
    ],
    "arducam-5mp-ov5647.html": [
        "Stock Lens 54° (H) x 41° (V) Fixed Focus",
        "B0176 15/Bottom Mini Size 54°(H)x44° (V) Auto Focus",
        "B006604 120°(H) x 90°(V)",
        # The no-IR-filter rows: B006603N is a different, narrower SKU,
        # quoted for the IR column it carries, which the B006604N row below
        # shares; B006604N is the 120 degree camera without its filter.
        "B006603N 64°(H) x 48°(V) without IR-cut filter",
        "B006604N 96°(H) x 72°(V)",
        "B0370 Wide Angle M12 155°(H) x 116°(V) Auto Focus",
    ],
    # The B006604's own product page: the 120 is a DIAGONAL.
    "arducam-b006604.html": [
        "SKU B006604",
        "Dimension: 60mm × 11.5mm × 5.5mm",
        "angle of view: 120° diagonal",
        "Diagnoal Field of View (DFOV) 120°",
        "Focus Distance 1 m to infinity",
        "Focus Type Fixed",
    ],
    "arducam-motorized-focus-camera.html": [
        "you can understand it the same as autofocus",
    ],
    # The motorised-focus OV5647 twice over: the discontinued B0121, whose
    # page names the B0176 as its successor, and the B0176 itself.
    "arducam-b0121-motorized-focus.html": [
        "SKU: B0121",
        "Please check the new version- SKU: B0176",
        "Angle of View: 54 x 41 degrees",
        "Field of View: 2.0 x 1.33 m at 2 m",
        "Full-frame SLR lens equivalent: 35 mm",
        "Focus distance: 4 cm to infinity",
    ],
    "uctronics-arducam-b0176.html": [
        "SKU B0176",
        "Focus Distance 80mm to infinity",
        "Field of View(FOV) 54°(H), 44°(V)",
        "Focus Type Motorized Focus",
        "Full-frame SLR lens equivalent 35mm",
        "Camera Board Size 24mm x 25mm",
    ],
    # Two lens makers' figures for a real lens of about 120 degrees diagonal
    # on this sensor, distortion included.
    "commonlands-ov5647.html": [
        "Active area 3.63 × 2.72 mm",
        "real distortion rather than a focal-length-only estimate",
        "Fisheye 2.2mm M12 Lens (CIL282) 2.2 mm M12 f/1.8 96° 72° 122°",
    ],
    "yxf-m6-lens.html": [
        "1/4 inch OV5647",
        "Focal Length [mm] 1.79mm",
        "Aperture F.no 2.4 ± 5%",
        "Field of View Diagonal [°] 73.9°",
        "Field of View Horizontal [°] 119.9°",
        "Field of View Vertical [°] 92.4°",
        "Distortion [%] -11.5%",
    ],
    # Waveshare's Camera Module v1 sized fisheye, and The Pi Hut's listing of
    # it, the one place its horizontal angle is printed.
    "waveshare-rpi-camera-g.html": [
        "Aperture (F) : 2.35",
        "Focal Length : 3.15mm",
        "Angle of View (diagonal) : 160 degree",
    ],
    "waveshare-rpi-camera-g-wiki.html": [
        "Approximately 10cm to infinity",
    ],
    "pihut-fisheye-160.html": [
        "Aperture (F): 2.35",
        "Diagonal angle: 160 degree Horizontal angle: 120 degree",
    ],
    # Arducam's OV5647 motorized focus guide.  The sheets do not print these
    # two strings -- they are what the words look like after the spacing in
    # the rendered page is flattened, and anyone copying them would get a
    # config.txt that does nothing -- but this family's README says that
    # guide adds a voice-coil device tree line and a close focus range, and
    # this is the page that has to go on saying it.
    "arducam-ov5647-motorized-focus-camera.html": [
        "dtoverlay = ov5647 , vcm",
        "autofocus - range macro",
    ],
}

#: How far a frame edge may sit inside where the margin puts it.  Floating
#: point only: the frame is built from the target by addition.
EPS = 1e-6


def _plain(path: Path) -> str:
    """A cached page as running text, the way a reader sees it.

    The quotes in the optics module are sentences and table rows, and in the
    HTML the words of a table row are separated by markup rather than by
    spaces.  Tags out, entities resolved, whitespace collapsed.  A PDF --
    only OmniVision's datasheet -- is read by its text layer, the first
    pages, which is where its key specifications are.
    """
    if path.suffix == ".pdf":
        from pypdf import PdfReader
        pages = PdfReader(path).pages[:8]
        return re.sub(r"\s+", " ", " ".join(p.extract_text() or ""
                                            for p in pages))
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text))


def check_quotes() -> tuple[int, int]:
    """Every quoted figure is in the page it is credited to."""
    if not CACHE.is_dir():
        print(f"quotes: {CACHE.relative_to(ROOT)} is not there; run "
              "`make fetch` to check the quotes against the sources\n")
        return 0, 0
    bad = total = 0
    for name, quotes in QUOTES.items():
        path = CACHE / name
        if not path.exists():
            print(f"   FAIL {name}: not fetched")
            bad += len(quotes)
            total += len(quotes)
            continue
        text = _plain(path)
        for quote in quotes:
            total += 1
            ok = quote in text
            bad += not ok
            print(f"   {'ok  ' if ok else 'FAIL'} {name[:34]:<36} "
                  f"{quote!r}")
    print(f"quotes: {total - bad} of {total} found in the cached pages\n")
    return bad, total


def check_lenses() -> int:
    """Each lens's figures, against the shape of the sensor behind it.

    Four things.  The pair a sheet computes with agrees with the 4:3 sensor
    under the lens's own projection -- tan(V/2) = tan(H/2) x 3/4 for a
    rectilinear lens, V = H x 3/4 for an equidistant one -- or the lens says
    it does not, which is what the sheets branch on.  Every declared pair is
    tried both ways, so that a pair called inconsistent is inconsistent under
    either projection and not just the convenient one.  No figure may have a
    horizontal as wide as its own diagonal, which no projection can give:
    the array's corner is further from the axis than its side, and every
    lens maps further to wider.  And the wide lens's pair is what its
    declared diagonal splits into under the projection it is said to have.
    """
    bad = 0
    lenses = list(optics.ALL_LENSES.values())
    for lens in lenses:
        off = abs(lens.consistent_v - lens.fov_v)
        agrees = off <= CONSISTENCY_TOL
        ok = agrees == lens.consistent
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {lens.name:<22} uses "
              f"{lens.fov_h:6.2f} x {lens.fov_v:5.2f}, {lens.projection}: "
              f"{lens.fov_h:.2f} across implies {lens.consistent_v:6.2f} "
              f"down, off by {off:5.2f} -> "
              f"{'consistent' if lens.consistent else 'INCONSISTENT'}")
        for fg in lens.figures:
            if fg.h is None:
                print(f"   --     {fg.what:<34} {fg.kind:<8} diagonal "
                      f"{fg.d:.1f} only")
                continue
            if fg.d is not None and fg.h >= fg.d - 1e-9:
                # The one conclusion no choice of lens model can rescue.
                print(f"   --     {fg.what:<34} {fg.kind:<8} {fg.h:6.2f} "
                      f"across against {fg.d:.1f} diagonal: IMPOSSIBLE, H "
                      "cannot reach the diagonal")
                continue
            if fg.v is None:
                continue
            rect = abs(optics.implied_v(fg.h, "rectilinear") - fg.v)
            equi = abs(optics.implied_v(fg.h, "equidistant") - fg.v)
            print(f"   --     {fg.what:<34} {fg.kind:<8} {fg.h:6.2f} x "
                  f"{fg.v:5.2f}: off the 4:3 by {rect:5.2f} rectilinear, "
                  f"{equi:5.2f} equidistant")
    # The catalogue's 120 x 90 is the one declared pair the sheets reject,
    # so the reason is checked: it is the product page's 120 diagonal, which
    # the same camera's H cannot equal.
    wide = optics.LENS_120
    page = next(f for f in wide.figures if f.h is None)
    cat = next(f for f in wide.figures if f.rejected)
    ok = cat.h >= page.d and cat.v is not None
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} {cat.what} gives {cat.h:.0f} across"
          f" where the product page gives {page.d:.0f} diagonal: rejected")
    h, v = optics.split_diagonal(page.d, wide.projection)
    ok = abs(h - wide.fov_h) < 0.01 and abs(v - wide.fov_v) < 0.01
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} {page.d:.0f} diagonal, "
          f"{wide.projection}, splits to {h:.2f} x {v:.2f}; the sheets use "
          f"{wide.fov_h:.2f} x {wide.fov_v:.2f}")
    # The splits either side: for one diagonal, rectilinear is the widest a
    # lens without pincushion distortion can be, and equisolid is narrower
    # than equidistant; the pair used has to lie between.
    r = optics.split_diagonal(page.d, "rectilinear")
    q = optics.split_diagonal(page.d, "equisolid")
    ok = q[0] < wide.fov_h < r[0] and q[1] < wide.fov_v < r[1]
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} between equisolid {q[0]:.2f} x "
          f"{q[1]:.2f} and rectilinear {r[0]:.2f} x {r[1]:.2f}")
    # Its focal length, from the same diagonal, beside the two real lenses'.
    f = optics.focal_from_diagonal(page.d, wide.projection)
    ok = abs(f - wide.focal_length) < 1e-9
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} its focal length, DERIVED: "
          f"{optics.ARRAY_DIAGONAL / 2:.3f} / {math.radians(page.d / 2):.4f}"
          f" rad = {f:.3f} mm (rectilinear would be "
          f"{optics.focal_from_diagonal(page.d, 'rectilinear'):.3f})")
    # The autofocus lens's, from its 35 mm equivalent.
    af = optics.AUTOFOCUS
    f = 35.0 * optics.ARRAY_DIAGONAL / math.hypot(36.0, 24.0)
    ok = abs(f - af.focal_length) < 1e-9
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} {af.name}'s focal length, DERIVED:"
          f" 35 x {optics.ARRAY_DIAGONAL:.3f} / 43.27 = {f:.3f} mm")
    # The datasheet's image area, whose diagonal is the 65.
    d = optics.full_angle(math.hypot(*optics.DATASHEET_IMAGE_AREA))
    ok = abs(d - optics.DIAGONAL_FROM_DATASHEET) < 1e-9 and round(d) == 65
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} OmniVision's image area, "
          f"{optics.DATASHEET_IMAGE_AREA[0]:.4f} x "
          f"{optics.DATASHEET_IMAGE_AREA[1]:.4f}, diagonal {d:.2f} deg at "
          f"{optics.FOCAL_LENGTH:.2f} mm")
    print()
    return bad


def check_bounds() -> int:
    """The frame margin absorbs what is not known about each lens.

    For every lens, frame and alternative pair: at the height the sheet
    prints, a lens with the alternative angles still has the TARGET in its
    picture.  The frame is the target plus the margin; the margin is what
    is spent.  A pair wider than the one used only overshoots, and is
    checked all the same.
    """
    bad = 0
    print("What the margin absorbs")
    for subject in subjects().values():
        for letter, frame in zip("AB", subject.frames()):
            t = frame.target
            for lens in optics.ALL_LENSES.values():
                p = place(frame, lens)
                for alt in lens.alternatives:
                    ax = alt.h if frame.long_axis == "X" else alt.v
                    ay = alt.v if frame.long_axis == "X" else alt.h
                    hx = p.z * math.tan(math.radians(ax / 2))
                    hy = p.z * math.tan(math.radians(ay / 2))
                    spare = min(t.x0 - (p.x - hx), (p.x + hx) - t.x1,
                                t.y0 - (p.y - hy), (p.y + hy) - t.y1)
                    ok = spare >= -EPS
                    bad += not ok
                    print(f"   {'ok  ' if ok else 'FAIL'} {subject.key:<20} "
                          f"{letter} {lens.short:>3}, as {alt.what:<34} "
                          f"{spare:+6.2f} mm to spare of "
                          f"{optics.FRAME_MARGIN:.2f}")
    print()
    return bad


def _edge_on_plane(z: float, projection: str, focal: float, n=64):
    """The picture's edge, walked onto a plane *z* below the lens.

    Image points round the array's edge, each turned back into its field
    angle by *projection* and sent down to the plane.  Returned as the
    greatest |x| along the long edges and |y| along the short ones, with
    the least of each, so a caller can see whether the edge bows in or out.
    """
    w, h = optics.ARRAY_WIDTH / 2, optics.ARRAY_HEIGHT / 2
    xs, ys = [], []
    for i in range(n + 1):
        for (u, v, into) in ((w, -h + 2 * h * i / n, xs),
                             (-w + 2 * w * i / n, h, ys)):
            r = math.hypot(u, v)
            if projection == "equidistant":
                theta = r / focal
            else:
                theta = 2 * math.asin(r / (2 * focal))
            out = z * math.tan(theta)
            into.append(abs(out * (u if into is xs else v) / r))
    return min(xs), max(xs), min(ys), max(ys)


def check_distortion() -> int:
    """Under barrel distortion the frame's corners are inside the picture.

    The heights are set so that the picture's edge reaches the frame at the
    MIDDLE of each side, where the declared angles are measured.  A
    rectilinear lens's edges are straight, so its corners are then exactly
    the frame's.  A barrel-distorted lens's are not: walked down onto the
    board, each straight edge of the sensor lands as a curve, and this
    checks it bows outwards -- the least distance out along an edge is at
    its middle -- for the wide lens's projection and for the equisolid one
    it is bounded by, so that the frame's corners are covered with room to
    spare rather than cut off.
    """
    bad = 0
    wide = optics.LENS_120
    print("Distortion: the picture's edges on the board, at the wide lens")
    for projection in ("equidistant", "equisolid"):
        f = optics.focal_from_diagonal(120.0, projection)
        # Any height will do: the shape scales with it.
        z = 100.0
        x_lo, x_hi, y_lo, y_hi = _edge_on_plane(z, projection, f)
        mid_x = z * math.tan(w_half(projection, f, "x"))
        mid_y = z * math.tan(w_half(projection, f, "y"))
        ok = (abs(x_lo - mid_x) < 1e-6 and abs(y_lo - mid_y) < 1e-6
              and x_hi > x_lo and y_hi > y_lo)
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {projection:<11} f {f:.3f}: at"
              f" Z {z:.0f} the side edges run {x_lo:.1f} to {x_hi:.1f} out, "
              f"the top and bottom {y_lo:.1f} to {y_hi:.1f}: least at the "
              "middle, so they bow outwards")
    # How coarse the board comes out at the edge against the middle, on
    # the wide lens: d(Z tan theta)/d theta over f.
    for axis, a in (("H", wide.fov_h), ("V", wide.fov_v),
                    ("D", wide.fov_d)):
        k = 1 / math.cos(math.radians(a / 2)) ** 2
        print(f"   --   at the {axis} edge, {a / 2:.1f} deg out, a pixel "
              f"covers {k:.2f} x the board it does on the axis (radially)")
    print()
    return bad


def w_half(projection: str, f: float, axis: str) -> float:
    """The field half-angle, in radians, at the middle of an array edge."""
    r = (optics.ARRAY_WIDTH if axis == "x" else optics.ARRAY_HEIGHT) / 2
    if projection == "equidistant":
        return r / f
    return 2 * math.asin(r / (2 * f))


def check_focus() -> int:
    """The depth of field figures the sheets print, and every verdict.

    Worked by the formulae directly rather than through optics' helpers
    where there is a second way: the hyperfocal distance as f^2 / (N c) + f,
    and the circle of confusion Raspberry Pi's own "1 m to infinity" implies.
    """
    bad = 0
    print(f"Focus, at a circle of confusion of {optics.COC_PIXELS} pixels, "
          f"{optics.COC * 1000:.1f} um")
    for lens in optics.ALL_LENSES.values():
        f, n = lens.focal_length, lens.f_number
        h1 = f * f / (n * optics.PIXEL_PITCH) + f
        h2 = f * f / (n * optics.COC) + f
        ok = abs(h2 - lens.hyperfocal) < 1e-9
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {lens.name:<20} f {f:.3f} "
              f"({lens.focal_basis}), F{n:g} ({lens.f_basis}): hyperfocal "
              f"{h2:.0f} mm at 2 px, near limit {h2 / 2:.0f}; {h1:.0f} and "
              f"{h1 / 2:.0f} at 1 px; declared \"{lens.near_quote}\"")
    c = optics.LENS_65.focal_length ** 2 / (
        optics.LENS_65.f_number * (2 * 1000.0 - optics.LENS_65.focal_length))
    ok = abs(c - optics.IMPLIED_COC) < 1e-12
    bad += not ok
    print(f"   {'ok  ' if ok else 'FAIL'} \"Approx 1 m to infinity\" at the "
          f"hyperfocal distance implies a circle of {c * 1000:.2f} um, "
          f"{c / optics.PIXEL_PITCH:.1f} px")
    # Every height against every lens's declared near limit, and what a
    # motorised lens's depth of field is once it has focused there.
    af = optics.AUTOFOCUS
    for subject in subjects().values():
        for letter, frame in zip("AB", subject.frames()):
            for lens in optics.ALL_LENSES.values():
                p = place(frame, lens)
                truth = p.z < lens.near
                ok = p.too_close is truth
                bad += not ok
                extra = ""
                if lens.focus_at is None:
                    near, far = optics.dof(p.z, lens.focal_length,
                                           lens.f_number)
                    extra = (f"; focused there, sharp from {near:.1f} to "
                             f"{far:.1f}")
                else:
                    on_sensor, on_subject = lens.blur(p.z)
                    extra = (f"; a point spreads {on_sensor * 1000:.1f} um,"
                             f" {on_sensor / optics.PIXEL_PITCH:.0f} px, "
                             f"{on_subject:.2f} mm on the board")
                print(f"   {'ok  ' if ok else 'FAIL'} {subject.key:<20} "
                      f"{letter} {lens.short:>3} Z {p.z:6.1f} against "
                      f"{lens.near:5.0f}: "
                      f"{'OUT OF RANGE' if truth else 'in range'}{extra}")
    print()
    return bad


def check_model() -> int:
    """The declared field of view comes back out of the pinhole model.

    Raspberry Pi publish a focal length, a sensor size and a field of view,
    and any two of those predict the third.  They agree to a hundredth of a
    degree on both axes -- but only against the ACTIVE PIXEL ARRAY, not
    against the "sensor image area" printed one row above it in the same
    table.  That is the whole justification for the arithmetic on these
    sheets, so it is checked rather than asserted in a comment.
    """
    bad = 0
    print(f"Sensor: {optics.SENSOR_COLUMNS} x {optics.SENSOR_ROWS} at "
          f"{optics.PIXEL_PITCH * 1000:.1f} um = "
          f"{optics.ARRAY_WIDTH:.4f} x {optics.ARRAY_HEIGHT:.4f} mm, "
          f"aspect {ASPECT:.6f}, f = {optics.FOCAL_LENGTH:.2f} mm")
    for what, derived, declared in FOV_CHECK:
        if declared is None:
            print(f"   --   {what:<38} {derived:7.3f} deg  (nothing "
                  "declared to compare)")
            continue
        off = abs(derived - declared)
        # The image area rows are expected to MISS: they are there to show
        # which rectangle the vendor measured to.
        expect = "array" in what
        ok = (off <= FOV_CHECK_TOL) == expect
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {what:<38} {derived:7.3f} deg "
              f"vs declared {declared:6.2f}, off by {off:.3f} "
              f"({'must match' if expect else 'must not match'})")
    print()
    return bad


def check_frames() -> int:
    """Every frame holds its target, and every height reaches every frame."""
    bad = 0
    for subject in subjects().values():
        print(f"{subject.title}  ({subject.key})")
        for letter, frame in zip("AB", subject.frames()):
            t = frame.target
            # 1. The frame holds the target plus the margin, on all four
            #    sides.  This is the claim the phantom rectangle makes.
            want = (t.x0 - FRAME_MARGIN, t.y0 - FRAME_MARGIN,
                    t.x1 + FRAME_MARGIN, t.y1 + FRAME_MARGIN)
            holds = (frame.x0 <= want[0] + EPS and frame.y0 <= want[1] + EPS
                     and frame.x1 >= want[2] - EPS
                     and frame.y1 >= want[3] - EPS)
            bad += not holds
            print(f"   {'ok  ' if holds else 'FAIL'} frame {letter} "
                  f"{frame.width:7.2f} x {frame.height:6.2f} holds "
                  f"{t.label} + {FRAME_MARGIN:.2f} all round "
                  f"({t.width:.2f} x {t.height:.2f})")

            # 2. It is the sensor's own shape, and the SMALLEST such
            #    rectangle: one of its two sides is exactly what the margin
            #    asked for, or the frame is bigger than it needs to be.
            ratio = (frame.width / frame.height if frame.long_axis == "X"
                     else frame.height / frame.width)
            shape = abs(ratio - ASPECT) < 1e-9
            tight = (abs(frame.width - (want[2] - want[0])) < 1e-9
                     or abs(frame.height - (want[3] - want[1])) < 1e-9)
            bad += not (shape and tight)
            print(f"   {'ok  ' if shape and tight else 'FAIL'} frame "
                  f"{letter} is {ASPECT:.4f}:1 with its long axis along "
                  f"{frame.long_axis}, and touches the target on "
                  f"{'one' if tight else 'NEITHER'} axis")

            # 3. Z is quoted above the target's own plane, and where that is
            #    not the subject's face the sheet has to say so: a height set
            #    at the subject's face covers (Z - h) / Z of the frame at the
            #    target's, and nothing on the drawing would show it.
            said = (t.plane_above_subject == 0.0
                    or (t.plane_name and t.plane_note))
            bad += not said
            print(f"   {'ok  ' if said else 'FAIL'} frame {letter} is set "
                  f"from {t.plane_name}"
                  + ("" if t.plane_above_subject == 0.0
                     else ", and says where that is"))

            for lens in optics.ALL_LENSES.values():
                p = place(frame, lens)
                # 4. The camera is over the frame's centre.
                centred = (abs(p.x - frame.cx) < EPS
                           and abs(p.y - frame.cy) < EPS)
                # 5. At that height both declared angles reach the frame.
                reaches = (p.covers_x >= frame.width - 1e-6
                           and p.covers_y >= frame.height - 1e-6)
                bad += not (centred and reaches)
                dx, dy = p.excess
                print(f"   {'ok  ' if centred and reaches else 'FAIL'} "
                      f"  {lens.short:>3}: X {p.x:7.2f} Y {p.y:6.2f} "
                      f"Z {p.z:6.1f} (H wants {p.z_from_h:6.1f}, V "
                      f"{p.z_from_v:6.1f}, {p.governed_by} governs); covers "
                      f"{p.covers_x:7.2f} x {p.covers_y:6.2f}, over by "
                      f"{dx:5.2f} x {dy:5.2f}")

        # 7. Frame edges too close together to be drawn as two lines.  Not
        #    a failure -- the frames are what the targets make them -- but
        #    the sheet has to point at each one, so they are listed here and
        #    the drawing carries a leader for every one of them.
        for axis, ia, ib, pos, lo, hi, gap in coincident_edges(
                subject.frames()):
            print(f"   --   frames {'AB'[ia]} and {'AB'[ib]} have {axis} "
                  f"edges {gap:.2f} mm apart over {hi - lo:.1f} mm; the "
                  "sheet calls it out")

        # 8. What stands above the plane the first frame was set from, and
        #    how far it may stand before it leaves the picture.  Reported
        #    rather than asserted: there is no figure to fail against, and
        #    the number is what the sheet's own note prints.
        for label, box in subject.standing:
            for lens in LENSES.values():
                p = place(subject.frames()[0], lens)
                print(f"   --   {label} stays in frame A up to "
                      f"{p.headroom(box):5.1f} mm above the board face at "
                      f"{lens.key} deg")
        print()
    return bad


def _z_turned(frame, lens, long_axis: str) -> float:
    """The height *frame*'s rectangle needs with the sensor's long side
    along *long_axis*, worked from the declared angles directly."""
    along_x = lens.fov_h if long_axis == "X" else lens.fov_v
    along_y = lens.fov_v if long_axis == "X" else lens.fov_h
    return max(frame.width / 2 / math.tan(math.radians(along_x / 2)),
               frame.height / 2 / math.tan(math.radians(along_y / 2)))


def check_elevations() -> int:
    """The figures the elevations and the notes under them print.

    Worked from the declared angles and the vendor's own lens figures, not
    through the properties that print them, so that a wrong property is a
    disagreement here rather than two copies of one mistake.
    """
    bad = 0
    stock = LENSES["65"]
    print("Elevations, at the stock lens")
    for subject in subjects().values():
        frame = subject.frames()[0]
        p = place(frame, stock)
        # 1. The angle each elevation labels is the one along its axis, and
        #    from the lens at Z it reaches frame A's edge on that axis.
        want_x = stock.fov_h if frame.long_axis == "X" else stock.fov_v
        want_y = stock.fov_v if frame.long_axis == "X" else stock.fov_h
        reach_x = 2 * p.z * math.tan(math.radians(want_x / 2))
        reach_y = 2 * p.z * math.tan(math.radians(want_y / 2))
        ok = (p.angle_x == want_x and p.angle_y == want_y
              and reach_x >= frame.width - 1e-6
              and reach_y >= frame.height - 1e-6)
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {subject.key:<20} front "
              f"{p.angle_x:.2f}, end {p.angle_y:.2f}: from Z {p.z:.1f} they "
              f"reach {reach_x:.2f} x {reach_y:.2f} over a frame "
              f"{frame.width:.2f} x {frame.height:.2f}")
        # 2. Turned the other way the camera would have to go higher: the
        #    sheet says the frame is turned whichever way needs the lower
        #    camera.
        other = "Y" if frame.long_axis == "X" else "X"
        # The frame for the other turn is the target plus the margin made
        # 4:3 the other way up, which is a different rectangle.
        t = frame.target
        m = FRAME_MARGIN
        w0, h0 = t.width + 2 * m, t.height + 2 * m
        ratio = ASPECT if other == "X" else 1 / ASPECT
        w = max(w0, h0 * ratio)
        h = max(h0, w / ratio)
        z_other = _z_turned(type("F", (), {"width": w, "height": h})(),
                            stock, other)
        ok = z_other >= p.z - 1e-6
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {'':<20} long side along "
              f"{frame.long_axis} needs Z {p.z:.1f}; along {other} it would "
              f"need {z_other:.1f}")
        # 3. The diagonal read as the angle across the long side.
        long_side = max(frame.width, frame.height)
        naive = long_side / 2 / math.tan(math.radians(65.0 / 2))
        short = (long_side - 2 * naive * math.tan(
            math.radians(stock.fov_h / 2))) / 2
        ok = (abs(naive - p.naive_z) < 1e-9
              and abs(short - p.naive_shortfall) < 1e-9 and short > 0)
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {'':<20} 65 deg across the "
              f"long side: Z {naive:.1f}, {short:.1f} mm lost off each end")
        # 4. How far the stand may lean before the margin is used up.
        # Solved the other way: bisect for the lean at which the governing
        # edge has come in by the margin.
        a = stock.fov_h if p.governed_by == "H" else stock.fov_v
        th = math.radians(a / 2)
        lo, hi = 0.0, th
        for _ in range(200):
            mid = (lo + hi) / 2
            lost = p.z * (math.tan(th) - math.tan(th - mid))
            lo, hi = (mid, hi) if lost < FRAME_MARGIN else (lo, mid)
        tilt = math.degrees(lo)
        ok = abs(tilt - p.aim_tilt) < 1e-6
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {'':<20} a lean of {tilt:.2f} "
              f"deg moves the picture's edge {FRAME_MARGIN:.2f} mm at Z")
        # 5. How soft a stock lens is at Z: the depth of field formula,
        #    f^2 |s - u| / (N u (s - f)), against the thin lens Lens.blur
        #    works the other way round, and against a lens set at infinity,
        #    which is the other reading of "1 m to infinity".
        f, n = stock.focal_length, float(optics.FOCAL_RATIO.lstrip("F"))
        s, u = stock.focus_at, p.z
        b = f * f * abs(s - u) / (n * u * (s - f))
        b_inf = f * f / (n * u)
        on_sensor, on_subject = stock.blur(u)
        ok = abs(b - on_sensor) < 1e-12 and n == stock.f_number
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {'':<20} stock lens at Z: a "
              f"point spreads to {b * 1000:.1f} um, {b / optics.PIXEL_PITCH:.0f}"
              f" px, {on_subject:.2f} mm on the board")
        print(f"   --   {'':<20} set at infinity instead: {b_inf * 1000:.1f} "
              f"um, {b_inf / optics.PIXEL_PITCH:.0f} px, "
              f"{b_inf * (u - f) / f:.2f} mm on the board")
        # 6. Which published close limits each frame's height is inside.
        for quote, mm in optics.near_limits():
            cm = float(re.search(r"(\d+) cm", quote).group(1))
            ins = [f"{letter} {place(fr, stock).z:.1f}"
                   for letter, fr in zip("AB", subject.frames())
                   if place(fr, stock).z >= cm * 10]
            ok = abs(mm - cm * 10) < 1e-9
            bad += not ok
            print(f"   {'ok  ' if ok else 'FAIL'} {'':<20} inside {quote!r}, "
                  f"{cm * 10:.0f} mm: {', '.join(ins) or 'none'}")
        # 7. The plate's second height: the plate face to the lens, which
        #    is Z plus the standoff and the thickest board.
        if subject.key == "tt-mounting-plate":
            from tinytapeout.boards import BOARDS as TT
            from tinytapeout.mounting_plate.plate import (PLACEMENTS,
                                                          STANDOFF_HEIGHT)
            thick = max(TT[r].outline.thickness for pl in PLACEMENTS.values()
                        for r in pl["revisions"])
            plane = STANDOFF_HEIGHT + thick
            ok = abs(frame.target.plane_above_subject - plane) < 1e-9
            bad += not ok
            print(f"   {'ok  ' if ok else 'FAIL'} {'':<20} board face "
                  f"{STANDOFF_HEIGHT:g} + {thick:.2f} = {plane:.2f} above the "
                  f"plate, so the lens is {p.z + plane:.1f} above the plate "
                  "face")
    print()
    return bad


def main() -> None:
    problems = 0
    bad, _ = check_quotes()
    problems += bad
    problems += check_model()
    problems += check_lenses()
    problems += check_bounds()
    problems += check_distortion()
    problems += check_frames()
    problems += check_focus()
    problems += check_elevations()

    fixed = [ln for ln in optics.ALL_LENSES.values() if ln.focus_at]
    close = sum(1 for s in subjects().values() for f in s.frames()
                for ln in fixed if place(f, ln).too_close)
    total = sum(1 for s in subjects().values() for f in s.frames()
                for ln in fixed)
    print(f"{close} of {total} fixed-focus heights are nearer than the lens's "
          "declared near limit, and every sheet says so.")
    print("PASS: the frames hold their targets and the heights reach them"
          if not problems else f"FAIL: {problems} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
