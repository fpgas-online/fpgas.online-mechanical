#!/usr/bin/env python3
"""Check that the light pipe adapter really does what its sheet claims.

Three claims, and nothing else about the part matters:

* the cable still goes in.  Nothing of the adapter, and nothing of either
  light pipe, is inside the opening a plug goes through or the keyway its
  latch enters;
* the LEDs get into the pipes.  Each pipe's tip, seen from its LED window
  along the direction the light leaves it, lands on that window, and neither
  the adapter nor the pipe touches the window -- which on this jack stands
  proud of the face the adapter lands on;
* the pipes fit, and so does the adapter.  The press fit is inside the panel
  thickness Bivar make that pipe for, the skirts pass the shield at maximum
  material while the jack's own side EMI springs still bear on them at
  minimum, and the roof clears the shield and its springs.

Proved from ``adapter.py`` and ``fpga/boards.py`` rather than from the
drawing, so it is the data the drawing is made from that is being checked.

Every check here compares two things that were arrived at separately: the
part's geometry against the jack's, the jack's against the board's, or either
against a figure from Bivar.  Checks that would only restate how
``design.py`` built a number -- that the bore is as long as the pipe, that
the press-fit diameter is the one it was set from -- are not checks and are
not here; where a figure is true by construction and still worth printing,
the line says so.

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

results: list[tuple[bool, str, str, bool]] = []


def check(ok: bool, what: str, detail: str, *, report: bool = False) -> None:
    """Record a check, or -- with *report* -- a figure that is only printed.

    A line that cannot fail is not a check and is not counted as one; two of
    them are here because the number they print is worth having beside the
    checks it bears on.
    """
    results.append((bool(ok), what, detail, report))


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
    """The bore against Bivar's drawing, and the flange against its seat."""
    check(A.PANEL_MIN <= A.PRESS_LEN <= A.PANEL_MAX,
          "press-fit length is inside Bivar's panel thickness",
          f"{A.PRESS_LEN:.2f} mm of Ø{A.PRESS_DIA} bore, between Bivar's "
          f"{A.PANEL_MIN} and {A.PANEL_MAX} mm")
    clearance(A.BORE_DIA - A.PIPE_RIB_DIA, 0.05,
              "the clearance bore passes the pipe's press-fit ribs",
              f"Ø{A.BORE_DIA} bore over Ø{A.PIPE_RIB_DIA} ribs")

    # The flange seats on the facet, which is cut off at the cheek's front
    # face at one end and its top face at the other.  Both ends are a step in
    # X and the same step in Z from the flange's centre, so the distance
    # along the facet is that step times root two.
    lower = (A.FACET_X - A.CHEEK_X0) * math.sqrt(2)
    upper = ((A.CHEEK_Z1 - A.FACET_K) - A.FACET_X) * math.sqrt(2)
    want = A.FLANGE_DIA / 2 + A.CLEARANCES["flange rim to the edge of its seat"]
    clearance(lower, want, "the flange's seat reaches the facet's lower edge",
              "flange centre to where the facet meets the cheek's front face")
    clearance(upper, want, "the flange's seat reaches the facet's upper edge",
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
    win_y = (A.WINDOW_Y0 + A.WINDOW_Y1) / 2
    win_z = (A.WINDOW_Z0 + A.WINDOW_Z1) / 2
    off_y = abs((y0 + y1) / 2 - win_y)
    off_z = abs((z0 + z1) / 2 - win_z)
    # What can be established: that the tip is aimed at the window, to better
    # than the window's own measurement uncertainty.  Whether every last
    # fraction of its rim falls inside the window cannot be, because the
    # window's edges are only known to READ_TOL -- and it does not matter:
    # light that lands on the shield beside the window is light not
    # collected, not a part that does not fit.
    clearance(A.READ_TOL - max(off_y, off_z), 0.0,
              "the pipe's tip is centred on the LED window",
              f"off centre by {off_y:.3f} mm across and {off_z:.3f} mm up, "
              f"against the +/-{A.READ_TOL} the window itself is read to")
    margin_y = min(y0 - A.WINDOW_Y0, A.WINDOW_Y1 - y1)
    margin_z = min(z0 - A.WINDOW_Z0, A.WINDOW_Z1 - z1)
    check(True, "how much of the tip the window covers, nominally",
          f"tip {y0:.2f}..{y1:.2f} across and {z0:.2f}..{z1:.2f} up, inside a "
          f"window {A.WINDOW_Y0}..{A.WINDOW_Y1} and {A.WINDOW_Z0}.."
          f"{A.WINDOW_Z1} by {margin_y:+.3f} and {margin_z:+.3f} mm -- the "
          f"first of those is well inside the +/-{A.READ_TOL} the window is "
          "read to, so it is a nominal figure, not a fit", report=True)

    # The window stands proud of the face the cheeks land on, so the tip has
    # to clear the window rather than the face.  At maximum material: the
    # 0.025 that dimensions it carries Bel's +/-0.254.
    nearest = A.BORE_X + A.PIPE_DIA / 2 * H
    clearance(A.WINDOW_FACE_X - nearest,
              A.CLEARANCES["pipe tip to the LED window at maximum material"],
              "the pipe stands off the LED window",
              f"nearest point of the tip at x {nearest:.3f}, window face at "
              f"{A.WINDOW_FACE_X:.3f} at maximum material")
    clearance(-nearest - A.WINDOW_PROUD, 0.0,
              "and off it as the drawing draws it",
              f"window face at {-A.WINDOW_PROUD:.3f} as dimensioned")

    # The pocket has to clear the window, and the window has to fit into it.
    check(A.POCKET_Y0 <= A.WINDOW_Y0 and A.POCKET_Y1 >= A.WINDOW_Y1
          and A.POCKET_Z1 >= A.WINDOW_Z1,
          "the pocket clears the whole LED window",
          f"pocket y {A.POCKET_Y0}..{A.POCKET_Y1}, z {A.POCKET_Z0}.."
          f"{A.POCKET_Z1} over a window y {A.WINDOW_Y0}..{A.WINDOW_Y1}, "
          f"z {A.WINDOW_Z0}..{A.WINDOW_Z1}")
    check(A.CHEEK_Y0 <= A.POCKET_Y0 and A.WINDOW_Y0 >= A.POCKET_Y0,
          "and nothing of the adapter lands on the window",
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
              "and so are the pipes",
              f"lowest point of a tip at z {tip_z0:.3f}")
    clearance(A.CHEEK_Y0 - A.KEYWAY_Y, 0.30,
              "the channel between the cheeks clears the latch keyway",
              f"channel {2 * A.CHEEK_Y0:.2f} mm wide over a keyway "
              f"{2 * A.KEYWAY_Y:.2f} mm wide")
    # Everything the adapter puts in front of the jack is above the plug, and
    # the channel over the latch is open to the sky: the roof, which is the
    # only thing that spans the two cheeks, starts at the jack's front face
    # and goes backwards from there.
    check(A.ROOF_X0 >= A.CHEEK_X1, "nothing bridges the latch channel in "
          "front of the jack",
          f"the roof spans x {A.ROOF_X0}..{A.ROOF_X1}, all of it behind the "
          f"cheeks' back faces at {A.CHEEK_X1}, so a finger reaches the latch")


# -- the adapter on the jack -------------------------------------------------

def on_the_jack() -> None:
    half_max = A.SHIELD_W / 2 + A.BEL_TOL / 2
    half_min = A.SHIELD_W / 2 - A.BEL_TOL / 2
    top_max = A.SHIELD_H + A.BEL_TOL / 2

    clearance(A.SKIRT_Y0 - half_max, A.CLEARANCES["skirt to shield"],
              "the skirts pass the shield at maximum material",
              f"skirt inner face at y {A.SKIRT_Y0}, shield at {half_max:.3f}")
    grip_min = (half_min + A.SPRING_PROUD - A.SPRING_PROUD_TOL) - A.SKIRT_Y0
    grip_max = (half_max + A.SPRING_PROUD + A.SPRING_PROUD_TOL) - A.SKIRT_Y0
    grip_drawn = A.SIDE_SPRING_Y - A.SKIRT_Y0
    clearance(grip_min, A.CLEARANCES["side EMI spring deflection"],
              "the side EMI spring bears on the skirt at minimum material",
              f"deflection {grip_min:.3f} mm at the least, {grip_max:.3f} at "
              f"the most and {grip_drawn:.3f} at the figures Bel draws; that "
              "spring is all that holds the adapter on")
    # The spring Bel draws and the spring Bel dimensions are two different
    # statements about the same part, and the drawn one has to be inside the
    # dimensioned band or one of the two readings is wrong.
    drawn_proud = A.SIDE_SPRING_Y - A.SHIELD_W / 2
    check(abs(drawn_proud - A.SPRING_PROUD) <= A.SPRING_PROUD_TOL,
          "the spring as drawn is inside the spring as dimensioned",
          f"drawn {drawn_proud:.3f} mm proud of the shield against "
          f"{A.SPRING_PROUD} +/-{A.SPRING_PROUD_TOL}")
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
              "roof slot to top EMI spring"] + EPS
          and A.SLOT_Y1 >= A.TOP_SPRING_Y1 + A.CLEARANCES[
              "roof slot to top EMI spring"] - EPS,
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
    # front face and not on the side springs where those wrap round it.
    check(A.CHEEK_Y1 > half_max and A.SIDE_SPRING_Z1 < A.CHEEK_Z0,
          "the back faces miss the side springs",
          f"those springs stop at z {A.SIDE_SPRING_Z1}, the cheeks start at "
          f"{A.CHEEK_Z0}")


# -- the part itself ---------------------------------------------------------

def the_part() -> None:
    inner = (A.BORE_Y - A.BORE_DIA / 2) - A.CHEEK_Y0
    outer = A.CHEEK_Y1 - (A.BORE_Y + A.BORE_DIA / 2)
    clearance(inner, A.CLEARANCES["bore to cheek inner face"],
              "wall inboard of the bore", "cheek inner face to bore")
    clearance(outer, A.CLEARANCES["bore to cheek inner face"],
              "wall outboard of the bore", "bore to cheek outer face")
    clearance(A.ROOF_Z1 - A.ROOF_Z0, 1.2, "roof thickness", "roof")
    clearance(A.SKIRT_Y1 - A.SKIRT_Y0, 1.2, "skirt thickness", "skirt")
    check(A.CHEEK_Z1 == A.ROOF_Z1 and A.CHEEK_Y1 == A.SKIRT_Y1,
          "the cheeks, the roof and the skirts share their outer faces",
          f"top at z {A.ROOF_Z1}, sides at y +/-{A.SKIRT_Y1}")


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
          f"by {-x0:.2f} mm, +/-{A.JACK_FACE_TOL} because that is how well "
          "the jack's own position on the board is known; a plate or a box "
          "has to leave it clear")


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
    for ok, what, detail, report in results:
        bad += not ok
        mark = "--  " if report else ("ok  " if ok else "FAIL")
        print(f"   {mark} {what}\n        {detail}")
    tested = sum(1 for r in results if not r[3])
    noted = len(results) - tested
    print()
    figures = "figure" if noted == 1 else "figures"
    print(f"PASS: {tested} checks, {noted} {figures} reported" if not bad
          else f"FAIL: {bad} of {tested} checks")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
