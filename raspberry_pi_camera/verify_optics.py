#!/usr/bin/env python3
"""Check that the camera position sheets say what they can be shown to say.

Four things, from the data modules rather than from the drawings:

* every figure quoted in :mod:`raspberry_pi_camera.optics` is really in the
  vendor page cached under ``tmp/src/rpi-camera-optics/``;
* the pinhole model reproduces Raspberry Pi's own declared field of view from
  their own focal length and sensor size, which is what makes it the right
  model rather than a convenient one;
* every lens's declared pair is tested against the sensor's own shape, so
  that ``Lens.consistent`` means what the sheets say it means;
* every frame is the smallest rectangle of the sensor's aspect ratio holding
  its target plus the stated margin, and the camera sits over its centre at a
  height where both declared angles reach it;
* every target whose plane is not the subject's own top face says so, because
  a height set at the wrong plane covers less at the right one;
* every height is compared against the lens's published near limit, and the
  answer the sheet prints is the answer the arithmetic gives;
* what the elevations draw and print: that the declared angle each one
  shows is the one lying along its axis, that it reaches the frame's edge
  from the lens, that the camera is turned the way that needs the lower
  camera, the height above the plate face on the mounting plate sheet, and
  the figures the notes derive -- the diagonal's mistake, how far the stand
  may lean, how soft a stock lens is at these heights, and which published
  close limits each height is inside.

That last one passes while reporting TOO CLOSE on every row.  It has to: a
stock Camera Module OV5647 is fixed at "Approx 1 m to infinity" and every
board here wants the camera a tenth of that away.  What is being checked is
that the sheet says so, not that the problem has gone away.

Run: uv run --no-project python raspberry_pi_camera/verify_optics.py
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
        "F2.9",
        "53.50 +/- 0.13 degrees",
        "41.41 +/- 0.11 degrees",
        "Focus Fixed Adjustable Motorized Motorized",
        "Depth of field Approx 1 m to ∞ Approx 10 cm to ∞",
        "Approx 5 cm to ∞",
    ],
    "arducam-5mp-ov5647.html": [
        "Stock Lens 54° (H) x 41° (V) Fixed Focus",
        "B0176 15/Bottom Mini Size 54°(H)x44° (V) Auto Focus",
        "B006604 120°(H) x 90°(V)",
    ],
    "arducam-motorized-focus-camera.html": [
        "you can understand it the same as autofocus",
    ],
    # The OV5647 guide the AUTOFOCUS note sends a reader to.  The sheets no
    # longer print these two strings -- they are what the words look like
    # after the spacing in the rendered page is flattened, and anyone
    # copying them would get a config.txt that does nothing -- but the note
    # still says that guide adds a voice-coil device tree line and a close
    # focus range, and this is the page that has to go on saying it.
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
    spaces.  Tags out, entities resolved, whitespace collapsed.
    """
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
    """Each lens's declared pair, against the shape of the sensor behind it.

    ``Lens.consistent`` is what the sheets branch on when they decide whether
    to warn that the picture runs over the rectangle drawn, so the rule it
    encodes is checked here rather than trusted: on a 4:3 sensor a
    rectilinear lens has tan(V/2) = tan(H/2) x 3/4.
    """
    bad = 0
    for lens in list(LENSES.values()) + [optics.AUTOFOCUS]:
        off = abs(lens.consistent_v - lens.fov_v)
        agrees = off <= CONSISTENCY_TOL
        ok = agrees == lens.consistent
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {lens.name:<22} declared "
              f"{lens.fov_h:6.2f} x {lens.fov_v:5.2f}; {lens.fov_h:.2f} on a "
              f"4:3 sensor implies {lens.consistent_v:6.2f}, off by {off:5.2f}"
              f" -> {'consistent' if lens.consistent else 'INCONSISTENT'}")
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

            for lens in LENSES.values():
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
                      f"  {lens.key:>3} deg: X {p.x:7.2f} Y {p.y:6.2f} "
                      f"Z {p.z:6.1f} (H wants {p.z_from_h:6.1f}, V "
                      f"{p.z_from_v:6.1f}, {p.governed_by} governs); covers "
                      f"{p.covers_x:7.2f} x {p.covers_y:6.2f}, over by "
                      f"{dx:5.2f} x {dy:5.2f}")

                # 6. The focus verdict the sheet prints is the arithmetic.
                if lens.min_object_distance is None:
                    print(f"        -- {lens.key:>3} deg: no near limit is "
                          "published, so the sheet prints UNKNOWN")
                    continue
                printed = p.too_close
                truth = p.z < lens.min_object_distance
                bad += printed is not truth
                mark = "TOO CLOSE" if truth else "ok"
                print(f"   {'ok  ' if printed is truth else 'FAIL'} "
                      f"  {lens.key:>3} deg: Z {p.z:.1f} against a near "
                      f"limit of {lens.min_object_distance:.0f} -> {mark} "
                      f"({p.z / lens.min_object_distance:.2f} x the limit)")
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
                      f"{p.headroom(box):5.1f} mm above the plate at "
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
        tilt = math.degrees(math.atan(FRAME_MARGIN / p.z))
        ok = abs(tilt - p.aim_tilt) < 1e-9
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {'':<20} a lean of {tilt:.2f} "
              f"deg moves the picture {FRAME_MARGIN:.2f} mm at Z")
        # 5. How soft a stock lens is at Z: the depth of field formula,
        #    f^2 |s - u| / (N u (s - f)), against the thin lens optics.blur
        #    works the other way round, and against a lens set at infinity,
        #    which is the other reading of "1 m to infinity".
        f, n = optics.FOCAL_LENGTH, float(optics.FOCAL_RATIO.lstrip("F"))
        s, u = optics.FIXED_FOCUS_DISTANCE, p.z
        b = f * f * abs(s - u) / (n * u * (s - f))
        b_inf = f * f / (n * u)
        on_sensor, on_subject = optics.blur(u)
        ok = abs(b - on_sensor) < 1e-12 and n == optics.F_NUMBER
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
    problems += check_frames()
    problems += check_elevations()

    close = sum(1 for s in subjects().values() for f in s.frames()
                for ln in LENSES.values() if place(f, ln).too_close)
    print(f"all {close} heights with a published near limit are nearer "
          f"than the stock lens's {LENSES['65'].min_object_distance:.0f} mm, "
          "and every sheet says so.")
    print("PASS: the frames hold their targets and the heights reach them"
          if not problems else f"FAIL: {problems} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
