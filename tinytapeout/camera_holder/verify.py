#!/usr/bin/env python3
"""Check that the camera holder does what its sheet claims.

Four claims, for the holder built for each lens, and nothing else about it
matters:

* the camera is where ``RPICAM-OVER-PLATE`` says it has to be: over the
  centre of frame A, lens down, at least as high as the lens needs --
  and at that height every revision's whole board is in the picture, at its
  own board plane, with the holder hiding none of it;
* nothing of the holder is where a board, a standoff or a connector is, or
  where a cable has to come in: every revision's envelope, its standoffs,
  its USB-C plug, its Pmod peripherals front and side;
* every fastener fits: the holes line up through the parts they join, the
  screws are long enough, the heads and nuts land on material and clear
  what is next to them, and the camera's own screws and bosses miss its
  lens and its connector;
* the plate needs no new hole: the feet sit over fixings it already has.

And one about the two holders together: the beam and the carrier are the
same parts in both, only moved in Z, so one file of each serves both.

Proved from ``holder.py`` against the data modules it is built from --
``tinytapeout/boards.py``, the plate, the camera, the optics -- and wherever
a figure can be reached two ways it is reached the way ``holder.py`` did not:
the picture is worked from the declared angles rather than through
``optics.place``.  The lens height is summed back up the parts as built,
which checks the stack's arithmetic rather than offering a second design.

Run: uv run --no-project python tinytapeout/camera_holder/verify.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from raspberry_pi_camera import optics  # noqa: E402
from tinytapeout.boards import BOARDS as TT  # noqa: E402
from tinytapeout.camera_holder import holder  # noqa: E402
from tinytapeout.mounting_plate.plate import (PLACEMENTS, PLATE,  # noqa: E402
                                              STANDOFF_HEIGHT)

results: list[tuple[bool, str, str, bool]] = []

#: The holder being checked: each of ``holder.VARIANTS`` in turn, set by
#: ``main``.  Every check reads it as it used to read the module.
H = holder.VARIANTS[next(iter(holder.VARIANTS))]


def check(ok: bool, what: str, detail: str, *, report: bool = False) -> None:
    """Record a check, or -- with *report* -- a figure that is only printed."""
    results.append((bool(ok), what, detail, report))


#: Floating point, and the thousandth every plate figure is rounded to.
EPS = 1e-6

#: The largest an M2 thread can be: ISO 965-2 tolerance class 6g puts the
#: major diameter 0.019 under the 2.000 basic size for a 0.4 mm pitch.
M2_MAX_MAJOR = 1.981

#: The least air left between the holder and anything it must not touch.
CLEAR = 0.5

#: An M3 hex standoff, 5.5 mm across flats, as the circle it sweeps.
STANDOFF_R = 5.5 / math.sqrt(3)

#: What a cable needs in front of a connector.  Not a published figure: a
#: USB-C plug's overmould and the start of its cable's bend, and the body of
#: a Pmod peripheral, each taken generously, since the holder stands well
#: clear of all of them and a tight figure would prove nothing extra.
USB_REACH, USB_SIDE, USB_TALL = 40.0, 3.0, 10.0
PMOD_REACH, PMOD_TALL = 30.0, 25.0
#: ASSUMED: how far a Pmod peripheral's board stands past its connector's
#: body on each side.  A peripheral is wider than the 2x6 header it plugs
#: into, and nothing here gives a figure for how much.
PMOD_SIDE = 2.0


def boxes(parts=None):
    """Every box of every printed part, and the round bosses as boxes."""
    for p in parts or H.ASSEMBLY:
        for b in p.boxes:
            yield p, (b.x0, b.x1, b.y0, b.y1, b.z0, b.z1)
        for c in p.bosses:
            r = c.dia / 2
            yield p, (c.x - r, c.x + r, c.y - r, c.y + r, c.z0, c.z1)


def gap_1d(a0, a1, b0, b1) -> float:
    """Signed gap between two intervals: negative where they overlap."""
    return max(b0 - a1, a0 - b1)


def box_gap(a, b) -> float:
    """Clear distance between two 3D boxes, negative if they overlap.

    Axis-aligned, so the boxes are apart by the largest of the three
    one-dimensional gaps; where that is negative they intersect.
    """
    return max(gap_1d(a[0], a[1], b[0], b[1]), gap_1d(a[2], a[3], b[2], b[3]),
               gap_1d(a[4], a[5], b[4], b[5]))


def circle_box_gap(cx, cy, r, z0, z1, b) -> float:
    """Clear distance from a vertical cylinder to a box."""
    dz = gap_1d(z0, z1, b[4], b[5])
    dx = max(b[0] - cx, 0.0, cx - b[1])
    dy = max(b[2] - cy, 0.0, cy - b[3])
    d = math.hypot(dx, dy) - r if (dx or dy) else -r
    return max(d, dz)


# -- where the camera is ----------------------------------------------------

def the_camera() -> None:
    lens = H.LENS
    frame = H.FRAME
    # The height the stock lens needs over frame A, straight from the
    # declared angles and the frame's own rectangle.
    along_x = lens.fov_h if frame.long_axis == "X" else lens.fov_v
    along_y = lens.fov_v if frame.long_axis == "X" else lens.fov_h
    z_need = max(frame.width / 2 / math.tan(math.radians(along_x / 2)),
                 frame.height / 2 / math.tan(math.radians(along_y / 2)))
    # The lens face, summed up the parts: the rail's top, less the carrier,
    # the bosses, the camera's board and its lens.
    rail_top = max(b.z1 for b in H.SIDE_LEFT.boxes)
    carrier = H.CARRIER.boxes[0]
    boss = H.CARRIER.bosses[0]
    face = (rail_top - (carrier.z1 - carrier.z0) - (boss.z1 - boss.z0)
            - H.CAMERA.thickness - H.CAMERA.lens_height)
    thick = [TT[r].outline.thickness for pl in PLACEMENTS.values()
             for r in pl["revisions"]]
    plane_hi = STANDOFF_HEIGHT + max(thick)
    check(face - plane_hi >= z_need - EPS,
          "the lens is high enough over the highest board",
          f"lens face {face:.2f} above the plate, board face {plane_hi:.2f}: "
          f"{face - plane_hi:.2f} against the {z_need:.2f} the {lens.short} "
          f"deg lens needs over frame A, {face - plane_hi - z_need:+.2f} "
          "spare")
    check(abs(face - H.LENS_FACE_Z) < EPS,
          "the parts stack to the height the sheet prints",
          f"{face:.2f} summed, {H.LENS_FACE_Z:.2f} printed")
    # The lens axis over frame A's centre, through the camera's own data.
    ax, ay = H.camera_to_plate(*H.CAMERA.lens_axis)
    check(abs(ax - frame.cx) < EPS and abs(ay - frame.cy) < EPS,
          "the lens axis is over frame A's centre",
          f"({ax:.2f}, {ay:.2f}) against ({frame.cx:.2f}, {frame.cy:.2f})")
    # The carrier's fixings are square about that axis, so a quarter turn
    # of the carrier turns the camera without moving the axis.
    fix = [(h.x - ax, h.y - ay) for h in H.CARRIER.holes
           if "carrier fixing" in h.what]
    turned = {(round(-y, 6), round(x, 6)) for x, y in fix}
    check(turned == {(round(x, 6), round(y, 6)) for x, y in fix},
          "a quarter turn of the carrier lands on the same four fixings",
          f"{len(fix)} fixings at +/-{H.CARRIER_FIX:.2f} about the lens axis")
    # Turned the wrong way, the short side of the picture lies along frame
    # A's long side: how much of it that loses, off each end.
    long_side = max(frame.width, frame.height)
    wrong = 2 * (face - (STANDOFF_HEIGHT + max(thick))) * math.tan(
        math.radians(lens.fov_v / 2))
    check(True, "which way the camera is turned",
          f"{H.QUARTER_TURNS} quarter turns, ASSUMING the long image axis "
          "lies along the camera board's 25 mm width; nobody publishes it. "
          f"Frame A's long side is along {frame.long_axis}. Turned wrong, "
          f"the picture covers {wrong:.1f} of its {long_side:.1f}, "
          f"{(long_side - wrong) / 2:.1f} short at each end: turn the "
          "carrier", report=True)
    check(abs((long_side - wrong) / 2 - H.turned_wrong()) < EPS,
          "and the sheet prints that shortfall",
          f"{H.turned_wrong():.2f} printed, {(long_side - wrong) / 2:.2f} "
          "worked here")

    spare_by_rev: dict[str, float] = {}
    # Every revision, whole, at its own board face.  A thinner board is
    # lower, so it is further from the lens and more of it is covered.
    for name, pl in PLACEMENTS.items():
        for rev in pl["revisions"]:
            spec = TT[rev]
            plane = STANDOFF_HEIGHT + spec.outline.thickness
            z = face - plane
            half_x = z * math.tan(math.radians(along_x / 2))
            half_y = z * math.tan(math.radians(along_y / 2))
            e = optics._envelope(spec, pl["dx"], pl["dy"])
            spare = min(e[0] - (ax - half_x), (ax + half_x) - e[2],
                        e[1] - (ay - half_y), (ay + half_y) - e[3])
            spare_by_rev[rev] = spare
            check(spare >= -EPS, f"all of {rev} is in the picture",
                  f"its envelope {e[2] - e[0]:.2f} x {e[3] - e[1]:.2f} at "
                  f"its face {plane:.2f} up, {spare:+.2f} mm to the "
                  "nearest edge of the picture, the frame's "
                  f"{optics.FRAME_MARGIN:.2f} margin included")

    from raspberry_pi_camera import v1
    worst = min(spare_by_rev.values())
    check(worst >= v1.LENS_TOL + v1.HOLE_TOL - EPS,
          "and with room for where the lens really is",
          f"{worst:.2f} mm to spare at the tightest, the margin and "
          f"{worst - optics.FRAME_MARGIN:.2f} over it, against the "
          f"{v1.LENS_TOL:.2f} v1.py gives the glued-on lens module and the "
          f"{v1.HOLE_TOL:.1f} it gives the holes it is located by")

    # Nothing of the holder between the lens and any board.  The picture of
    # a revision's envelope is a pyramid from the lens; its section shrinks
    # towards the lens, so a box misses it if it misses the section at the
    # box's lowest height inside it.  The apex is taken at the lens FACE,
    # the lowest the entrance pupil can be.  A pupil higher up makes the
    # pyramid slimmer at every height below the face, so it can only miss
    # more -- and nothing of the holder is below the face but the side
    # frames, which stand outside every envelope's section at every height.
    hit = []
    visible = []
    for p, b in boxes():
        for name, pl in PLACEMENTS.items():
            for rev in pl["revisions"]:
                plane = STANDOFF_HEIGHT + TT[rev].outline.thickness
                e = optics._envelope(TT[rev], pl["dx"], pl["dy"])
                for target, into in ((e, hit), (
                        (frame.x0, frame.y0, frame.x1, frame.y1), visible)):
                    z0 = max(b[4], plane)
                    if z0 >= min(b[5], face):
                        continue
                    k = (face - z0) / (face - plane)
                    sx0, sx1 = ax + (target[0] - ax) * k, ax + (target[2] - ax) * k
                    sy0, sy1 = ay + (target[1] - ay) * k, ay + (target[3] - ay) * k
                    if gap_1d(b[0], b[1], sx0, sx1) < 0 and \
                            gap_1d(b[2], b[3], sy0, sy1) < 0:
                        into.append((p.name, rev))
    check(not hit, "no part of the holder hides any of any board",
          "the sight lines from the lens to every point of every revision's "
          "envelope are clear" if not hit else
          f"blocked: {sorted(set(hit))}")
    names = sorted({n for n, _ in visible})
    check(True, "what of the holder is in the picture",
          ("the " + " and the ".join(names) + " show in frame A's margin, "
           "outside every board; how far outside is the clearance to the "
           "boards below") if names else "nothing", report=True)


# -- what it must not touch -------------------------------------------------

def keep_outs():
    """Every revision's board, standoffs and cable space, as boxes."""
    out = []
    for name, pl in PLACEMENTS.items():
        dx, dy = pl["dx"], pl["dy"]
        for rev in pl["revisions"]:
            spec = TT[rev]
            plane = STANDOFF_HEIGHT + spec.outline.thickness
            e = optics._envelope(spec, dx, dy)
            # The board and everything on it, from its underside up to the
            # lens: nothing on it has a published height.
            out.append((f"{rev} board and parts", "box",
                        (e[0], e[2], e[1], e[3], STANDOFF_HEIGHT,
                         H.LENS_FACE_Z)))
            for h in spec.holes:
                out.append((f"{rev} {h.label} standoff", "cyl",
                            (h.x + dx, h.y + dy, STANDOFF_R, 0.0,
                             STANDOFF_HEIGHT)))
            for f in spec.features:
                if f.kind != "usb_power":
                    continue
                x0, x1 = f.x0 + dx - USB_SIDE, f.x1 + dx + USB_SIDE
                back = (f.y1 + dy) > (dy + spec.outline.height / 2)
                y0, y1 = ((f.y1 + dy, f.y1 + dy + USB_REACH) if back
                          else (f.y0 + dy - USB_REACH, f.y0 + dy))
                out.append((f"{rev} USB-C plug", "box",
                            (x0, x1, y0, y1, plane - 2.0, plane + USB_TALL)))
            for p in spec.pmods:
                if p.body_x1 <= p.body_x0:
                    continue
                out.append((f"{rev} Pmod {p.label} peripheral", "box",
                            (p.body_x0 + dx - PMOD_SIDE,
                             p.body_x1 + dx + PMOD_SIDE,
                             p.body_y0 + dy - PMOD_REACH, p.body_y0 + dy,
                             -PMOD_TALL, plane + PMOD_TALL)))
            # The side positions, not fitted: a header there takes a
            # peripheral out through the left edge.
            for f in spec.features:
                if f.kind == "header" and f.x0 < 1.0:
                    out.append((f"{rev} {f.label.split(' (')[0]} peripheral",
                                "box",
                                (f.x0 + dx - PMOD_REACH, f.x0 + dx,
                                 f.y0 + dy - PMOD_SIDE,
                                 f.y1 + dy + PMOD_SIDE, plane - 2.0,
                                 plane + PMOD_TALL)))
    return out


def clear_of_everything() -> None:
    worst: dict[str, tuple[float, str]] = {}
    for label, kind, k in keep_outs():
        for p, b in boxes():
            if kind == "box":
                g = box_gap(b, k)
            else:
                g = circle_box_gap(k[0], k[1], k[2], k[3], k[4], b)
            group = label.split(" ", 1)[1]
            if group not in worst or g < worst[group][0]:
                worst[group] = (g, f"{p.name} to {label}")
    for group, (g, who) in sorted(worst.items()):
        check(g >= CLEAR - EPS, f"clear of every {group}",
              f"{g:+.2f} mm at the closest, {who}")


# -- the fasteners ----------------------------------------------------------

def fasteners() -> None:
    # The feet over the plate's own fixings, both sides: the right foot's
    # holes are the mirror of the left's, and the plate has to have a
    # fixing there too.
    plate_fix = [(h.x, h.y, h.dia) for h in PLATE.holes if h.kind == "plate"]
    for part in (H.SIDE_LEFT, H.SIDE_RIGHT):
        for h in part.holes:
            if "plate fixing" not in h.what:
                continue
            near = min(plate_fix, key=lambda f: math.dist(f[:2], (h.x, h.y)))
            off = math.dist(near[:2], (h.x, h.y))
            check(off < 0.01, f"{part.name}: foot hole on a plate fixing",
                  f"({h.x:.3f}, {h.y:.3f}) against the plate's "
                  f"({near[0]:.3f}, {near[1]:.3f}), {off:.3f} apart")
            check(min(near[2], h.dia) > 4.0 + 0.1,
                  f"{part.name}: an M4 passes both",
                  f"plate {near[2]:.2f}, foot {h.dia:.2f}")
            foot = next(b for b in part.boxes if b.what == "foot")
            edge = min(h.x - foot.x0, foot.x1 - h.x, h.y - foot.y0,
                       foot.y1 - h.y)
            check(edge >= H.M4_HEAD_DIA / 2 - EPS,
                  f"{part.name}: the M4 head lands on the foot",
                  f"head radius {H.M4_HEAD_DIA / 2:.2f}, foot edge "
                  f"{edge:.2f} from the hole")
            # The head stands on the foot, under whatever overhangs it.
            head = (h.x, h.y, H.M4_HEAD_DIA / 2, H.FOOT_T,
                    H.FOOT_T + H.M4_HEAD_H)
            g = min(circle_box_gap(*head, k) for label, kind, k in
                    keep_outs() if kind == "box" and "board" in label)
            clear = min(circle_box_gap(*head, b) for p, b in boxes()
                        if p is not part)
            check(g >= CLEAR - EPS and clear >= CLEAR - EPS,
                  f"{part.name}: the M4 head clears the boards over it",
                  f"{g:+.2f} mm to the nearest board or part standing on "
                  f"one, {clear:+.2f} to the other parts of the holder")
    # Every other screw: its holes line up through both parts it joins, and
    # its length passes the grip and a whole nut.
    def holes(part, what):
        return sorted((round(h.x, 6), round(h.y, 6)) for h in part.holes
                      if what in h.what)
    rails = holes(H.SIDE_LEFT, "beam fixing") + \
        holes(H.SIDE_RIGHT, "beam fixing")
    check(sorted(rails) == holes(H.BEAM, "beam fixing"),
          "the beam's fixings are over the rails'",
          f"{len(rails)} M3 holes, each through both")
    check(holes(H.BEAM, "carrier fixing") == holes(H.CARRIER,
                                                   "carrier fixing"),
          "the carrier's fixings are under the pad's",
          f"{len(holes(H.CARRIER, 'carrier fixing'))} M3 holes")
    for key, (thread, grip, washer) in H.GRIPS.items():
        n = H._screw(key)
        need = grip + washer + H.NUT_H[thread] + 2 * H.PITCH[thread]
        check(need <= n, f"the {thread} x {n} is long enough ({key})",
              f"grip {grip:.2f}{' + washer' if washer else ''} + nut "
              f"{H.NUT_H[thread]:.1f} + two threads past it = {need:.2f}")
    # Where the ends of the screws go.  The camera's M2s come up through
    # the carrier into nut pockets in its top face; nut and tip have to stay
    # below the face the beam's pad bears on.
    pocket = next(h for h in H.CARRIER.holes if h.hex)
    tip = H.PCB_FRONT + H._screw("camera")
    nut_top = pocket.z0 + H.NUT_H["M2"]
    check(pocket.dia > H.M2_NUT_AF and nut_top <= H.CARRIER_Z1 - EPS
          and tip <= H.CARRIER_Z1 - 0.2,
          "the camera's M2 nuts and screw ends stay in the carrier",
          f"pocket {pocket.dia:.2f} across flats for a {H.M2_NUT_AF:.1f} "
          f"nut; nut top {H.CARRIER_Z1 - nut_top:.2f} and screw end "
          f"{H.CARRIER_Z1 - tip:.2f} below the pad")
    # Screw heads on the beam land on it, clear of its edges and of each
    # other.
    bar = next(b for b in H.BEAM.boxes if b.what == "beam")
    pad = next(b for b in H.BEAM.boxes if b.what == "pad")
    worst = min(min(h.x - b.x0, b.x1 - h.x, h.y - b.y0, b.y1 - h.y)
                for h in H.BEAM.holes
                for b in (pad if "carrier" in h.what else bar,))
    beam_holes = [(h.x, h.y) for h in H.BEAM.holes]
    apart = min(math.dist(a, b) for i, a in enumerate(beam_holes)
                for b in beam_holes[i + 1:])
    check(worst >= H.M3_HEAD_DIA / 2 and apart >= H.M3_HEAD_DIA + 0.5,
          "the M3 heads sit on the beam",
          f"{worst:.2f} from the nearest edge for a {H.M3_HEAD_DIA / 2:.2f} "
          f"head radius, {apart:.2f} between the closest pair")
    # The carrier's nuts, under it, miss the camera however it is turned.
    for turns in range(4):
        corners = [H.camera_to_plate(u, v, turns) for u, v in
                   ((0, 0), (H.CAMERA.width, 0), (0, H.CAMERA.height),
                    (H.CAMERA.width, H.CAMERA.height))]
        cam = (min(x for x, _ in corners), max(x for x, _ in corners),
               min(y for _, y in corners), max(y for _, y in corners),
               H.PCB_FRONT, H.PCB_BACK)
        tip = H.BEAM_Z1 - H._screw("carrier")
        g = min(circle_box_gap(h.x, h.y, H.M3_NUT_AF / math.sqrt(3),
                               tip, H.CARRIER_Z0, cam)
                for h in H.CARRIER.holes if "carrier fixing" in h.what)
        check(g >= CLEAR - EPS,
              f"the carrier's nuts and screw ends miss the camera, {turns} "
              "quarter turns",
              f"{g:+.2f} mm")
    # The camera's own screws: through its holes, heads clear of its lens
    # and of what is beside it, bosses clear of what is on its far face.
    # An M2's thread is at most 1.981 across (ISO 965-2, 6g: 19 um under
    # the 2.000 basic size).  v1.py's holes are 2.0 as both measurements
    # give them, which passes it; but v1.py carries them +/-0.2, because no
    # source reads them finer, and at the bottom of that an M2 does not go.
    cam_holes = [(u, v, d) for u, v, d in H.CAMERA.holes]
    check(all(d > M2_MAX_MAJOR for _, _, d in cam_holes),
          "an M2 passes the camera's holes, as measured",
          f"holes {', '.join(f'{d:.2f}' for *_, d in cam_holes)} against an "
          f"M2 thread at most {M2_MAX_MAJOR:.3f}")
    low = min(d for *_, d in cam_holes) - H.CAMERA.hole_dia_tol
    check(True, "and at the bottom of their tolerance",
          f"{low:.2f}, which an M2 does not pass: a board whose holes are "
          "that small wants them opened with a 2.0 drill", report=True)
    au, av = H.CAMERA.lens_axis
    size = H.CAMERA.lens_profile[0][1]
    beside = [("lens module", au - size / 2, av - size / 2, au + size / 2,
               av + size / 2)] + [(label, x0, y0, x1, y1) for
                                  label, x0, y0, x1, y1, _h in
                                  H.CAMERA.front_parts]
    head, who = min((math.hypot(max(x0 - u, 0.0, u - x1),
                                max(y0 - v, 0.0, v - y1))
                     - H.M2_HEAD_DIA / 2, label)
                    for u, v, _ in cam_holes
                    for label, x0, y0, x1, y1 in beside)
    check(head >= 0.2 - EPS, "the M2 heads clear the lens and the flex",
          f"{head:+.2f} mm at the closest, to the {who}")
    check(True, "what the M2 heads are not checked against",
          "the small parts on the lens side besides the module and its flex "
          "-- LED D1 and R9 by MT1 in Raspberry Pi Spy's photograph -- which "
          "no source dimensions", report=True)
    worst = min(math.hypot(max(x0 - u, 0.0, u - x1), max(y0 - v, 0.0, v - y1))
                - H.BOSS_DIA / 2
                for u, v, _ in cam_holes
                for _, x0, y0, x1, y1, _h in H.CAMERA.back_parts)
    check(worst >= 0.2 - EPS, "the bosses clear the camera's far face parts",
          f"{worst:+.2f} mm at the closest")
    tallest = max(h for *_, h in H.CAMERA.back_parts)
    check(H.BOSS_H >= tallest + 0.5 - EPS,
          "and stand the carrier clear of the tallest of them",
          f"bosses {H.BOSS_H:.2f}, tallest part {tallest:.2f}")


# -- the cable --------------------------------------------------------------

def the_cable() -> None:
    """The FFC leaves its connector and out from under the carrier clear."""
    name, x0, y0, x1, y1, h = next(p for p in H.CAMERA.back_parts
                                   if "FFC" in p[0])
    edge = H.CAMERA.ffc_edge
    corners = [H.camera_to_plate(u, v) for u, v in
               ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
    cx0, cx1 = min(x for x, _ in corners), max(x for x, _ in corners)
    cy0, cy1 = min(y for _, y in corners), max(y for _, y in corners)
    out_u, out_v = {"top": (0, 1), "bottom": (0, -1), "left": (-1, 0),
                    "right": (1, 0)}[edge]
    tip = H.camera_to_plate(H.CAMERA.lens_axis[0] + out_u,
                            H.CAMERA.lens_axis[1] + out_v)
    dx, dy = tip[0] - H.AXIS_X, tip[1] - H.AXIS_Y
    # The cable, where v1.py says it crosses the board's edge, from the
    # connector out past the carrier's edge, at the height v1.py says it
    # leaves the connector: a strip, and the gap it runs in.
    reach = H.CARRIER_HALF + 5.0
    u0, u1 = H.CAMERA.ffc_cable
    ends = [H.camera_to_plate(u, y1 if edge == "top" else y0)
            for u in (u0, u1)] if edge in ("top", "bottom") else \
        [H.camera_to_plate(x1 if edge == "right" else x0, u)
         for u in (u0, u1)]
    if abs(dy) > abs(dx):
        a, b = sorted(p[0] for p in ends)
        strip = (a, b, cy1 if dy > 0 else H.AXIS_Y - reach,
                 H.AXIS_Y + reach if dy > 0 else cy0)
    else:
        a, b = sorted(p[1] for p in ends)
        strip = (cx1 if dx > 0 else H.AXIS_X - reach,
                 H.AXIS_X + reach if dx > 0 else cx0, a, b)
    z = H.PCB_BACK + H.CAMERA.ffc_cable_z
    box = (*strip, z - 0.3, z + 0.3)
    check(z + 0.3 <= H.CARRIER_Z0 - EPS,
          "the cable leaves the connector under the carrier",
          f"at {H.CAMERA.ffc_cable_z:.2f} below the camera's far face, in a "
          f"{H.CARRIER_Z0 - H.PCB_BACK:.2f} mm gap")
    g = min([circle_box_gap(c.x, c.y, c.dia / 2, c.z0, c.z1, box)
             for c in H.CARRIER.bosses]
            + [circle_box_gap(h.x, h.y, H.M3_NUT_AF / math.sqrt(3),
                              H.CARRIER_Z0 - H.NUT_H["M3"], H.CARRIER_Z0,
                              box)
               for h in H.CARRIER.holes if "carrier fixing" in h.what])
    toward = {(0, 1): "the back", (0, -1): "the front", (1, 0): "the right",
              (-1, 0): "the left"}[(round(dx), round(dy))]
    check(g >= CLEAR - EPS, "and runs out from under it unobstructed",
          f"towards {toward}, {strip[1] - strip[0] if abs(dy) > abs(dx) else strip[3] - strip[2]:.2f} wide "
          f"(v1.py prints {H.CAMERA.ffc_cable_width:.1f}); "
          f"{g:+.2f} mm to the nearest boss or nut")


def the_plate_is_unchanged() -> None:
    check(all(any(math.dist((h.x, h.y), (p.x, p.y)) < 0.01
                  for p in PLATE.holes if p.kind == "plate")
              for part in (H.SIDE_LEFT, H.SIDE_RIGHT)
              for h in part.holes if "plate fixing" in h.what),
          "the plate needs no new hole",
          "all four feet's screws go through fixings the plate already has")


def the_variants_share_parts() -> None:
    """The beam and the carrier are the same parts in every holder.

    Only moved in Z: the design says the side frames are the one part that
    changes with the lens, and that is what lets one beam and one carrier
    file serve both.  Checked box by box and hole by hole.
    """
    first, *rest = holder.VARIANTS.values()

    def shape(part):
        z = part.bbox.z0
        return ([(b.x0, b.x1, b.y0, b.y1, b.z0 - z, b.z1 - z)
                 for b in part.boxes],
                [(h.x, h.y, h.dia, h.z0 - z, h.z1 - z, h.hex)
                 for h in part.holes],
                [(c.x, c.y, c.dia, c.z0 - z, c.z1 - z) for c in part.bosses])
    for other in rest:
        for key in ("BEAM", "CARRIER"):
            a, b = getattr(first, key), getattr(other, key)
            same = all(
                len(x) == len(y) and all(
                    all(abs(u - v) < EPS for u, v in zip(p, q))
                    for p, q in zip(x, y))
                for x, y in zip(shape(a), shape(b)))
            check(same, f"the {a.name.lower()} is one part for both lenses",
                  f"{first.LENS.short} and {other.LENS.short} deg: the same "
                  f"boxes and holes, {a.bbox.z0 - b.bbox.z0:.2f} mm apart "
                  "in Z")


def main() -> None:
    global H
    bad = tested = noted = 0
    for key, variant in holder.VARIANTS.items():
        H = variant
        results.clear()
        print(f"Camera holder over the {PLATE.title}, carrying the "
              f"{H.CAMERA.name}, for the {H.LENS.name} lens\n")
        the_camera()
        clear_of_everything()
        fasteners()
        the_cable()
        the_plate_is_unchanged()
        bad, tested, noted = _report(bad, tested, noted)
    results.clear()
    print("Both holders\n")
    the_variants_share_parts()
    bad, tested, noted = _report(bad, tested, noted)
    print(f"PASS: {tested} checks, {noted} figures reported" if not bad
          else f"FAIL: {bad} of {tested} checks")
    sys.exit(1 if bad else 0)


def _report(bad: int, tested: int, noted: int) -> tuple[int, int, int]:
    for ok, what, detail, report in results:
        bad += not ok
        mark = "--  " if report else ("ok  " if ok else "FAIL")
        print(f"   {mark} {what}\n        {detail}")
    print()
    tested += sum(1 for r in results if not r[3])
    noted += sum(1 for r in results if r[3])
    return bad, tested, noted


if __name__ == "__main__":
    main()
