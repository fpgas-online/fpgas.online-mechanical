#!/usr/bin/env python3
"""Check that the camera position sheets say what they can be shown to say.

Four things, from the data modules rather than from the drawings:

* every figure quoted in :mod:`raspberry_pi_camera.optics` is really in the
  vendor page cached under ``tmp/src/rpi-camera-optics/``;
* the pinhole model reproduces Raspberry Pi's own declared field of view from
  their own focal length and sensor size, which is what makes it the right
  model rather than a convenient one;
* every frame is the smallest rectangle of the sensor's aspect ratio holding
  its target plus the stated margin, and the camera sits over its centre at a
  height where both declared angles reach it;
* every height is compared against the lens's published near limit, and the
  answer the sheet prints is the answer the arithmetic gives.

That last one passes while reporting TOO CLOSE on every row.  It has to: a
stock Camera Module OV5647 is fixed at "Approx 1 m to infinity" and every
board here wants the camera a tenth of that away.  What is being checked is
that the sheet says so, not that the problem has gone away.

Run: uv run --no-project --with pillow python raspberry_pi_camera/verify.py
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
from raspberry_pi_camera.optics import (ASPECT, FOV_CHECK,  # noqa: E402
                                        FOV_CHECK_TOL, FRAME_MARGIN, LENSES,
                                        place, subjects)

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
        "53.50 +/- 0.13 degrees",
        "41.41 +/- 0.11 degrees",
        "F2.9",
        "Focus Fixed Adjustable Motorized Motorized",
        "Depth of field Approx 1 m to ∞ Approx 10 cm to ∞",
        "Approx 5 cm to ∞",
    ],
    "arducam-5mp-ov5647.html": [
        "Field of View(H x V) Focus Type",
        "Stock Lens 54° (H) x 41° (V) Fixed Focus",
        "B0176 15/Bottom Mini Size 54°(H)x44° (V) Auto Focus",
        "B006604 120°(H) x 90°(V)",
    ],
    "arducam-motorized-focus-camera.html": [
        "you can understand it the same as autofocus",
    ],
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

            for lens in LENSES.values():
                p = place(frame, lens)
                # 3. The camera is over the frame's centre.
                centred = (abs(p.x - frame.cx) < EPS
                           and abs(p.y - frame.cy) < EPS)
                # 4. At that height both declared angles reach the frame.
                reaches = (p.covers_x >= frame.width - 1e-6
                           and p.covers_y >= frame.height - 1e-6)
                bad += not (centred and reaches)
                print(f"   {'ok  ' if centred and reaches else 'FAIL'} "
                      f"  {lens.key:>3} deg: X {p.x:7.2f} Y {p.y:6.2f} "
                      f"Z {p.z:6.1f}  covers {p.covers_x:7.2f} x "
                      f"{p.covers_y:6.2f}")

                # 5. The focus verdict the sheet prints is the arithmetic.
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
        print()
    return bad


def main() -> None:
    problems = 0
    bad, _ = check_quotes()
    problems += bad
    problems += check_model()
    problems += check_frames()

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
