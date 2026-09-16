#!/usr/bin/env python3
"""Check that the light pipe adapter really does what its sheet claims.

Three claims, and nothing else about the part matters:

* the cable still goes in.  Nothing of the adapter, and nothing of either
  light pipe, is inside the opening a plug goes through or the keyway its
  latch enters;
* the LEDs get into the pipes.  Each pipe's tip, seen from its LED window
  along the direction the light leaves it, lands inside that window, and no
  part of the adapter touches the window;
* the pipes fit, and so does the adapter.  The bore is what Bivar's drawing
  asks for, the press fit is inside the panel thickness that pipe is made
  for, the skirts pass the shield at maximum material while the jack's own
  side EMI springs still bear on them, and the roof clears the shield and its
  springs.

Proved from ``adapter.py`` and ``fpga/boards.py`` rather than from the
drawing, so it is the data the drawing is made from that is being checked.

Run: uv run --no-project python fpga/light_pipe/verify.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from fpga.boards import BOARDS  # noqa: E402
from fpga.light_pipe import adapter as A  # noqa: E402

H = math.sqrt(0.5)          # cos 45, sin 45: the bore's axis is at 45 degrees

results: list[tuple[bool, str, str]] = []


def check(ok: bool, what: str, detail: str) -> None:
    results.append((bool(ok), what, detail))


#: A micron.  Every figure in ``adapter.py`` is rounded to a thousandth of a
#: millimetre on the way out, so a clearance derived from two of them can miss
#: its own target by the last digit; nothing here is drawn or made to better
#: than a hundredth.
EPS = 1e-3


def clearance(value: float, want: float, what: str, detail: str) -> None:
    check(value >= want - EPS, what,
          f"{detail}: {value:+.3f} mm against {want:.2f} mm wanted")


# -- the pipe in its bore ----------------------------------------------------

def pipe_and_bore() -> None:
    """The bore is the pipe's own drawing turned into a hole."""
    axis_len = (A.FACET_K - A.ENTRY_K) * H
    check(abs(axis_len - A.PIPE_LEN) < 5e-3,
          "bore length equals the pipe's body length",
          f"{axis_len:.3f} mm of bore for a {A.PIPE_LEN:.2f} mm body, so the "
          "flange seats on the facet as the tip reaches the entry plane")
    check(A.PRESS_DIA == A.PIPE_HOLE,
          "press-fit bore is Bivar's recommended mounting hole",
          f"Ø{A.PRESS_DIA} against Ø{A.PIPE_HOLE} "
          f"+{A.PIPE_HOLE_PLUS}/-{A.PIPE_HOLE_MINUS}")
    check(A.PANEL_MIN <= A.PRESS_LEN <= A.PANEL_MAX,
          "press-fit length is inside Bivar's panel thickness",
          f"{A.PRESS_LEN:.2f} mm, between {A.PANEL_MIN} and {A.PANEL_MAX} mm")
    clearance(A.BORE_DIA - A.PIPE_RIB_DIA, 0.05,
              "clearance bore passes the pipe's press-fit ribs",
              f"Ø{A.BORE_DIA} bore over Ø{A.PIPE_RIB_DIA} ribs")

    # The flange sits on the facet, which is cut off at the cheek's front
    # face at one end and its top face at the other.
    # Both ends of the facet are a step in X and the same step in Z away
    # from the flange's centre, so the distance along the facet is that step
    # times root two.
    lower = (A.FACET_X - A.CHEEK_X0) * math.sqrt(2)
    upper = ((A.CHEEK_Z1 - A.FACET_K) - A.FACET_X) * math.sqrt(2)
    want = A.FLANGE_DIA / 2 + A.CLEARANCES["flange rim to the edge of its seat"]
    clearance(lower, want, "flange seat reaches the facet's lower edge",
              "flange centre to where the facet meets the cheek's front face")
    clearance(upper, want, "flange seat reaches the facet's upper edge",
              "flange centre to where the facet meets the cheek's top face")


# -- the light path ----------------------------------------------------------

def tip_disc() -> tuple[float, float, float, float]:
    """The pipe's tip, projected onto the jack's front face.

    The tip is a circle of the pipe's diameter lying at 45 degrees to that
    face, so what the LED window sees of it is an ellipse: the pipe's full
    diameter across, and that diameter foreshortened up the face.
    """
    r = A.PIPE_DIA / 2
    return (A.BORE_Y - r, A.BORE_Y + r, A.BORE_Z - r * H, A.BORE_Z + r * H)


def light_path() -> None:
    y0, y1, z0, z1 = tip_disc()
    inside = (y0 >= A.WINDOW_Y0 and y1 <= A.WINDOW_Y1
              and z0 >= A.WINDOW_Z0 and z1 <= A.WINDOW_Z1)
    check(inside, "the pipe's tip lands inside the LED window",
          f"tip covers y {y0:.2f}..{y1:.2f}, z {z0:.2f}..{z1:.2f} of a window "
          f"at y {A.WINDOW_Y0}..{A.WINDOW_Y1}, z {A.WINDOW_Z0}..{A.WINDOW_Z1}")

    # The tip is a disc at 45 degrees, so it reaches PIPE_DIA / 2 * cos 45
    # either side of its centre along X; the nearest point to the jack is
    # what has to clear the front face.
    nearest = A.BORE_X + A.PIPE_DIA / 2 * H
    clearance(-nearest, A.CLEARANCES["pipe tip to jack face"],
              "the pipe stands off the jack's front face",
              "nearest point of the tip to the face")

    # The pocket has to clear both the window and the bore's mouth, and it
    # must not shrink onto either.
    check(A.POCKET_Y0 <= A.WINDOW_Y0 and A.POCKET_Y1 >= A.WINDOW_Y1
          and A.POCKET_Z1 >= A.WINDOW_Z1,
          "the pocket clears the whole LED window",
          f"pocket y {A.POCKET_Y0}..{A.POCKET_Y1}, z {A.POCKET_Z0}.."
          f"{A.POCKET_Z1} over a window y {A.WINDOW_Y0}..{A.WINDOW_Y1}, "
          f"z {A.WINDOW_Z0}..{A.WINDOW_Z1}")
    # The bore's mouth is an ellipse in the cheek's back face region; the
    # pocket has to be cut deeper than its furthest point or the bore opens
    # into solid material and the light stops there.
    mouth = A.BORE_X - A.BORE_DIA / 2 * H
    clearance(mouth - A.POCKET_X0, 0.0,
              "the pocket is cut past the bore's mouth",
              f"pocket floor at x {A.POCKET_X0:.3f}, mouth at {mouth:.3f}")
    # Nothing of the adapter may land on the window itself: the cheek's back
    # face is the only part of it in that plane.
    check(A.CHEEK_Y0 <= A.POCKET_Y0 and A.WINDOW_Y0 >= A.POCKET_Y0,
          "no adapter material lands on the LED window",
          f"the cheek's back face stops at y {A.POCKET_Y0} and the window "
          f"starts at {A.WINDOW_Y0}")


# -- the cable ---------------------------------------------------------------

def cable() -> None:
    """The plug, its latch, and the space in front of the jack they need."""
    clearance(A.CHEEK_Z0 - A.APERTURE_Z1, A.CLEARANCES["plug aperture"],
              "the cheeks are above the plug aperture",
              f"cheek underside at z {A.CHEEK_Z0}, aperture top at "
              f"{A.APERTURE_Z1}")
    _, _, tip_z0, _ = tip_disc()
    clearance(tip_z0 - A.APERTURE_Z1, A.CLEARANCES["plug aperture"],
              "the pipes are above the plug aperture",
              f"lowest point of a tip at z {tip_z0:.3f}")
    clearance(A.CHEEK_Y0 - A.KEYWAY_Y, 0.30,
              "the channel between the cheeks clears the latch keyway",
              f"channel {2 * A.CHEEK_Y0:.2f} mm wide over a keyway "
              f"{2 * A.KEYWAY_Y:.2f} mm wide")
    # Everything the adapter puts in front of the jack is above the plug, and
    # the channel over the latch is open to the sky: nothing of the part
    # bridges it forward of the front face.
    check(A.ROOF_X0 >= 0.0, "nothing bridges the latch channel in front of "
          "the jack", f"the roof starts at the front face, x = {A.ROOF_X0}, "
          "so a finger reaches the latch from above and in front")


# -- the adapter on the jack -------------------------------------------------

def on_the_jack() -> None:
    half_max = A.SHIELD_W / 2 + A.BEL_TOL / 2
    half_min = A.SHIELD_W / 2 - A.BEL_TOL / 2
    top_max = A.SHIELD_H + A.BEL_TOL / 2
    top_min = A.SHIELD_H - A.BEL_TOL / 2

    clearance(A.SKIRT_Y0 - half_max, A.CLEARANCES["skirt to shield"],
              "the skirts pass the shield at maximum material",
              f"skirt inner face at y {A.SKIRT_Y0}, shield at {half_max:.3f}")
    grip_min = (half_min + A.SPRING_PROUD - A.SPRING_PROUD_TOL) - A.SKIRT_Y0
    grip_max = (half_max + A.SPRING_PROUD + A.SPRING_PROUD_TOL) - A.SKIRT_Y0
    check(grip_min > 0, "the side EMI spring bears on the skirt at minimum "
          "material", f"deflection {grip_min:+.3f} mm at the least and "
          f"{grip_max:+.3f} mm at the most, per side; that spring is all that "
          "holds the adapter on")
    check(A.SKIRT_Z0 <= A.SIDE_SPRING_Z0 and A.SKIRT_Z1 >= A.SIDE_SPRING_Z1,
          "the skirt covers the side EMI spring",
          f"skirt z {A.SKIRT_Z0}..{A.SKIRT_Z1} over a spring at "
          f"{A.SIDE_SPRING_Z0}..{A.SIDE_SPRING_Z1}")
    check(A.SKIRT_X1 >= A.SPRING_TOP_LEN,
          "the skirt reaches past the sprung part of the shield",
          f"skirt runs back {A.SKIRT_X1} mm, springs {A.SPRING_TOP_LEN} mm")

    clearance(A.ROOF_Z0 - top_max, A.CLEARANCES["roof to shield"],
              "the roof clears the top of the shield at maximum material",
              f"roof underside at z {A.ROOF_Z0}, shield top at {top_max:.3f}")
    check(A.SLOT_Y0 <= A.TOP_SPRING_Y0 - A.CLEARANCES[
              "roof slot to top EMI spring"] + 1e-9
          and A.SLOT_Y1 >= A.TOP_SPRING_Y1 + A.CLEARANCES[
              "roof slot to top EMI spring"] - 1e-9,
          "the roof's slots clear the top EMI springs",
          f"slot y {A.SLOT_Y0}..{A.SLOT_Y1} over a spring at "
          f"{A.TOP_SPRING_Y0}..{A.TOP_SPRING_Y1}")
    check(A.SLOT_X1 >= A.SPRING_TOP_LEN,
          "the roof's slots are as long as the top EMI springs",
          f"slot runs back {A.SLOT_X1} mm, spring {A.SPRING_TOP_LEN} mm")
    check(A.ROOF_X1 <= A.BODY_D,
          "the roof stays on the jack",
          f"it reaches x {A.ROOF_X1} of a {A.BODY_D} mm body")
    # The cheeks' back faces are the only stop; they have to land on the
    # front face and not on the wrapped-forward side springs.
    check(A.CHEEK_Y1 > half_max and A.SIDE_SPRING_Z1 < A.CHEEK_Z0,
          "the back faces miss the forward-wrapped side springs",
          f"those springs stop at z {A.SIDE_SPRING_Z1}, the cheeks start at "
          f"{A.CHEEK_Z0}")


# -- the part itself ---------------------------------------------------------

def the_part() -> None:
    inner = A.CHEEK_Y0 - (A.BORE_Y - A.BORE_DIA / 2)
    outer = A.CHEEK_Y1 - (A.BORE_Y + A.BORE_DIA / 2)
    clearance(-inner, A.CLEARANCES["bore to cheek inner face"],
              "wall inboard of the bore", "cheek inner face to bore")
    clearance(outer, A.CLEARANCES["bore to cheek inner face"],
              "wall outboard of the bore", "bore to cheek outer face")
    clearance(A.ROOF_Z1 - A.ROOF_Z0, 1.2, "roof thickness", "roof")
    clearance(A.SKIRT_Y1 - A.SKIRT_Y0, 1.2, "skirt thickness", "skirt")
    check(A.CHEEK_Z1 == A.ROOF_Z1,
          "the cheeks and the roof share a top face",
          f"both at z {A.ROOF_Z1}")


# -- the adapter on the board ------------------------------------------------

def on_the_board() -> None:
    board = BOARDS[A.BOARD_KEY]
    x0 = A.JACK_FACE_X + A.CHEEK_X0
    x1 = A.JACK_FACE_X + A.SKIRT_X1
    y0 = A.JACK_CENTRE_Y - A.WIDTH / 2
    y1 = A.JACK_CENTRE_Y + A.WIDTH / 2
    for f in board.features:
        if f.key == "ethernet":
            continue
        hit = not (f.x1 <= x0 or f.x0 >= x1 or f.y1 <= y0 or f.y0 >= y1)
        check(not hit, f"clear of {f.designator} on the board",
              f"{f.label} at x {f.x0:.2f}..{f.x1:.2f}, y {f.y0:.2f}.."
              f"{f.y1:.2f}")
    for p in board.pmods:
        hit = not (p.body_x1 <= x0 or p.body_x0 >= x1
                   or p.body_y1 <= y0 or p.body_y0 >= y1)
        check(not hit, f"clear of Pmod host {p.label}",
              f"body x {p.body_x0:.2f}..{p.body_x1:.2f}, y "
              f"{p.body_y0:.2f}..{p.body_y1:.2f}")
    eth = next(f for f in board.features if f.key == "ethernet")
    check(y0 >= eth.y0 - 2.0 and y1 <= eth.y1 + 2.0,
          "the adapter stays within two millimetres of the jack's own width",
          f"adapter y {y0:.2f}..{y1:.2f}, jack drawn at {eth.y0:.2f}.."
          f"{eth.y1:.2f}")
    check(x0 < 0, "the adapter overhangs the board's front edge",
          f"by {-x0:.2f} mm, which a plate or a box has to leave clear")


def main() -> None:
    print(f"{A.ADAPTER.title}: {A.WIDTH} x {A.DEPTH} x {A.HEIGHT} mm over "
          f"the jack {A.JACK_PART} ({A.JACK_DESIGNATOR}) on the "
          f"{BOARDS[A.BOARD_KEY].title}\n")
    pipe_and_bore()
    light_path()
    cable()
    on_the_jack()
    the_part()
    on_the_board()

    bad = 0
    for ok, what, detail in results:
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {what}\n        {detail}")
    print()
    print(f"PASS: {len(results)} checks" if not bad
          else f"FAIL: {bad} of {len(results)} checks")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
